"""
Vista grafica del Tower Defense con Pygame (Semanas 2 y 3).

Dibuja el estado del modelo sobre el mapa de Tiled:

    - capas del mapa (Terreno, Camino, Decoracion) pre-renderizadas
    - torres colocadas por el jugador con su alcance (circulo translucido)
      y sus frames de animacion PNG (Semana 4 - 12 variantes en
      View.tower_animations): quietas en reposo y reproduciendo la
      animacion de lanzamiento al disparar, recortada antes de que el
      proyectil de los PNG salga del encuadre para no duplicar el
      proyectil visual del juego. Sin animacion cables, se dibuja el
      sprite compuesto de la Semana 3 (sombra + cuerpo, munición
      flotante y rebote de disparo)
    - proyectiles en vuelo desde la torre hasta el enemigo objetivo
      (basica, fuego o roca) y efectos de impacto animados por frames
    - enemigos con barra de vida
    - torres y enemigos ordenados con Y-sorting: cada entidad se
      ordena por su punto de contacto con el suelo (base de la torre,
      pies del enemigo) y la situada mas abajo en pantalla se dibuja
      encima, de modo que un enemigo que pasa delante de una torre la
      tapa y uno que pasa detras queda cubierto por ella
    - Decoraciones_superiores por encima de enemigos y torres
    - resumen del estado (HUD)

Permite colocar torres haciendo click izquierdo en el mapa, validando
que la posicion no este en zona bloqueada, fuera del mapa ni encima de
otra torre. Las teclas 1, 2 y 3 seleccionan el tipo de torre (basica,
fuego o pesada) antes de colocarla. El modo de colocacion se cancela
con clic derecho; ESC primero cancela la colocacion/venta y despues
abre el menu de pausa (menu.md). La tecla Q sale siempre; el juego
solo se cierra con Exit, el boton X de la ventana o Q.

La tienda emergente (View.shop_panel.ShopPanel) se abre con el boton
«Tienda» de la esquina inferior derecha: mientras esta abierta se
oscurece el mapa, la simulacion queda en pausa (window.paused, que
main.py consulta antes de actualizar el controlador) y los clicks no
colocan torres. El menu de pausa (View.pause_menu.PauseMenu) funciona
igual: ESC lo abre y lo cierra, y mientras esta abierto main.py omite
el update del controlador. Cada tarjeta de la tienda muestra su
precio en estrellas (fuente
de sprites de View.sprite_font) tomado de la configuracion unica del
modelo; elegir una torre asequible cierra la tienda y arma su
colocacion, mientras que una torre sin fondos no inicia la compra y
las nueve restantes se muestran bloqueadas. Al colocar una torre se
vuelve a comprobar el saldo y su precio se descuenta (model.buy_tower):
nunca se cobra sin colocar ni se coloca sin pagar. Mientras dura el
modo de colocacion se dibuja una vista previa fantasma de la torre
seleccionada en la posicion del cursor.

Los proyectiles son puramente visuales: el danio se aplica una sola
vez, en el momento del ataque (modelo/controlador). El modelo expone
model.shots (eventos de disparo) que esta vista consume al dibujar
para animar proyectil -> impacto sin duplicar el danio.

La barra de acciones junto al boton «Tienda» en la esquina inferior
derecha (undoredo.md) muestra tres botones con los iconos de
assets/ui/tienda/iconos: Undo (deshace la ultima colocacion y devuelve
el 100% pagado), Redo (restaura la torre desecha cobrando su precio de
nuevo) y el Martillo (activa o cancela el modo venta: un click sobre
una torre la vende por el 50% de su precio y desactiva el modo). Undo y
Redo se atenuan cuando no hay accion disponible, el Martillo se
resalta mientras el modo venta esta activo y, en ese modo, el cursor
lleva el icono del martillo. Los clics sobre estos botones no colocan
torres ni abren la tienda.

La ventana solo dibuja el modelo; el ciclo del juego se ejecuta en
main.py.
"""

import math
import os

import pygame

from Model.game_model import TOWER_KINDS, TOWER_RANGE
from View.pause_menu import PauseMenu
from View.shop_panel import ShopPanel
from View.sprite_font import SpriteFont
from View.tiled_map import TiledMapRenderer
from View.tower_animations import TowerAnimations
from View.tower_assets import TowerAssets


class GameWindow:
    """Ventana de Pygame que dibuja el estado del modelo sobre el mapa."""

    FPS = 60
    MAX_FRAME_TIME = 0.1

    WIDTH = 1280
    HEIGHT = 720

    ENEMY_RADIUS = 8
    TOWER_FOOTPRINT = 40.0
    # Alcance y huella en pixeles del mapa de Tiled (misma unidad que
    # Enemy.progress y Tower.position); el dibujo aplica el escalado.
    # El combate mide la distancia sobre el camino (progress), no en
    # linea recta: la torre llega un poco mas alla del circulo dibujado,
    # por lo que este valor va algo por debajo del radio visual para
    # que ambas cosas coincidan en pantalla. El valor proviene del
    # modelo (TOWER_RANGE, datos.md: alcance unico de las 12 torres).
    TOWER_RANGE_PX = TOWER_RANGE
    # Segundos entre ataques de la torre basica colocada por el jugador
    # (los demas tipos usan su cadencia en Model.game_model.TOWER_KINDS).
    TOWER_ATTACK_INTERVAL = TOWER_KINDS["basica"]["attack_interval"]

    # Orden de seleccion con las teclas 1, 2 y 3.
    TOWER_KIND_ORDER = ("basica", "fuego", "pesada")
    KIND_KEYS = (pygame.K_1, pygame.K_2, pygame.K_3)
    # Giro del proyectil pesado (grados por segundo).
    HEAVY_SPIN_RATE = 200.0
    # 35.png esta dibujado en orientacion de caida: giro progresivo
    # del sprite hacia 0 grados (hacia abajo) durante el vuelo.
    FALL_PITCH_RATE = 150.0

    # Animacion de torre sin frames PNG: rebote al disparar y flote de
    # la munición. Las torres con animacion cables (Semana 4) usan la
    # duracion de View.tower_animations en su lugar.
    FIRE_ANIM_TIME = 0.12
    BOUNCE_PX = 7.0
    HOVER_BOB_PX = 9.0
    HOVER_BOB_SPEED = 3.2

    RANGE_FILL = (90, 150, 255, 45)
    PREVIEW_VALID_FILL = (90, 205, 90, 70)
    PREVIEW_INVALID_FILL = (200, 60, 60, 70)
    TOWER_COLOR = (180, 140, 80)
    TOWER_BORDER = (100, 80, 40)
    TOWER_INVALID = (200, 60, 60)
    ENEMY_COLOR = (205, 70, 70)
    ENEMY_BORDER = (95, 25, 25)
    HP_BG = (70, 70, 70)
    HP_FILL = (90, 205, 90)
    TEXT_COLOR = (240, 240, 240)
    TEXT_DIM = (200, 200, 200)
    HUD_BG = (12, 18, 14, 170)
    BACKGROUND = (34, 60, 30)

    # Contador de monedas con sprites (estrella dorada + digitos).
    COIN_HUD_PAD = 12
    COIN_GLYPH_H = 28
    COIN_DIGIT_SPACING = 2

    # Vista previa fantasma de la torre en colocacion.
    PREVIEW_ALPHA = 150

    # Barra de acciones Undo/Redo/Martillo (undoredo.md): iconos PNG de
    # assets/ui/tienda/iconos, escalados y alineados en una fila a la
    # izquierda del boton «Tienda» de la esquina inferior derecha.
    ACTION_ICON_DIR = os.path.join("assets", "ui", "tienda", "iconos")
    ACTION_BTN_SIZE = 58
    ACTION_ICON_SIZE = 36
    ACTION_BTN_GAP = 10
    ACTION_SELL_CURSOR_SIZE = 32
    ACTION_BORDER = (140, 110, 70)
    ACTION_HOVER_BORDER = (198, 150, 58)
    ACTION_ACTIVE_BORDER = (214, 122, 48)
    ACTION_DISABLED_BORDER = (70, 70, 70)
    ACTION_DISABLED_ALPHA = 110
    # Margenes de tolerancia (px de pantalla) de la hitbox de venta
    # sobre el CONTENIDO VISIBLE del sprite (no sobre su lienzo). El
    # izquierdo es el mas estrecho para no clicar el pasto de al lado;
    # el inferior es un poco mayor porque la base se toca el suelo.
    SELL_HITBOX_PAD_LEFT = 2
    SELL_HITBOX_PAD_RIGHT = 4
    SELL_HITBOX_PAD_TOP = 4
    SELL_HITBOX_PAD_BOTTOM = 4
    # Depuracion temporal: dibuja la hitbox de venta de cada torre
    # mientras el modo martillo este activo (hitbox.md).
    DEBUG_SELL_HITBOX = False

    def __init__(self, model, tiled_map=None):
        self.model = model
        self.tiled_map = tiled_map
        pygame.init()
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Tower Defense - Semana 2")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 26)

        self.renderer = None
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0

        if tiled_map is not None:
            self.renderer = TiledMapRenderer(tiled_map)
            map_w = tiled_map.pixel_width
            map_h = tiled_map.pixel_height
            self.scale = min(self.WIDTH / map_w, self.HEIGHT / map_h)
            scaled_w = int(map_w * self.scale)
            scaled_h = int(map_h * self.scale)
            self.offset_x = (self.WIDTH - scaled_w) // 2
            self.offset_y = (self.HEIGHT - scaled_h) // 2

        self.assets = TowerAssets(self.scale)
        self.animations = TowerAnimations(self.scale)
        self.sprite_font = SpriteFont()
        # Sin torre seleccionada al iniciar la partida (torreta.md): no
        # hay previsualizacion ni colocacion hasta que el jugador elija
        # una torre en la tienda (o con las teclas 1/2/3). Cancelar con
        # ESC/clic derecho o entrar en modo venta vuelve a este estado.
        self.selected_kind = None
        # Modo de colocacion: apagado por defecto; la tienda y las
        # teclas de tipo lo rearman al seleccionar una torre.
        self.placing = False
        # Menu de pausa (menu.md): ESC lo abre/cierra; el juego solo
        # sale con Exit, el boton X de la ventana o la tecla Q.
        self.pause_menu = PauseMenu(self.WIDTH, self.HEIGHT)
        # La tienda consulta el saldo del modelo (model.stars) para
        # marcar las torres que aun no se pueden pagar.
        self.shop = ShopPanel(self.WIDTH, self.HEIGHT, self.model)
        # Modo venta del martillo (undoredo.md): activo mientras el
        # jugador pueda vender una torre con un click sobre el mapa.
        self.selling = False
        self.undo_icon = self._load_action_icon("icono_undo.png")
        self.redo_icon = self._load_action_icon("icono_redo.png")
        self.hammer_icon = self._load_action_icon("icono_martillo.png")
        self.sell_cursor_icon = pygame.transform.smoothscale(
            self.hammer_icon,
            (self.ACTION_SELL_CURSOR_SIZE, self.ACTION_SELL_CURSOR_SIZE),
        )
        # Fila de botones a la izquierda del boton «Tienda» (esquina
        # inferior derecha), centrada verticalmente con el opener.
        row_width = (
            3 * self.ACTION_BTN_SIZE + 2 * self.ACTION_BTN_GAP
        )
        action_y = self.shop.opener_rect.centery - self.ACTION_BTN_SIZE // 2
        action_x = self.shop.opener_rect.left - self.ACTION_BTN_GAP - row_width
        self.undo_button_rect = pygame.Rect(
            action_x, action_y, self.ACTION_BTN_SIZE, self.ACTION_BTN_SIZE
        )
        self.redo_button_rect = self.undo_button_rect.move(
            self.ACTION_BTN_SIZE + self.ACTION_BTN_GAP, 0
        )
        self.hammer_button_rect = self.undo_button_rect.move(
            2 * (self.ACTION_BTN_SIZE + self.ACTION_BTN_GAP), 0
        )
        self.projectiles = []   # proyectiles en vuelo (pos. en mapa)
        self.impacts = []       # impactos en animacion (pos. en mapa)
        self._anim_time = 0.0   # reloj acumulado para flote de munición
        self._fire_timers = {}  # tid -> segundos restantes de anim. de disparo

        self.hud_background = self._build_hud_background()
        self._pending_click = None
        self._dt = 0.0
        # Modo debug de alcance (fixed.md): F3 activa/desactiva el
        # circulo de radio real y el punto rojo del centro de calculo.
        self.debug_range = False

    # ------------------------------------------------------------------
    # Ciclo (usado por main.py)
    # ------------------------------------------------------------------
    @property
    def paused(self):
        """True mientras la tienda o el menu de pausa esten abiertos. O(1).

        main.py omite controller.update(dt) cuando esto es True, de
        modo que enemigos, torres, proyectiles y oleadas no avanzan.
        """
        return self.shop.is_open or self.pause_menu.is_open

    def tick(self):
        """Limita la velocidad del ciclo y devuelve el tiempo del frame. O(1)."""
        self._dt = min(self.clock.tick(self.FPS) / 1000.0, self.MAX_FRAME_TIME)
        return self._dt

    def process_events(self):
        """Procesa eventos de Pygame. Devuelve False si hay que salir. O(e).

        Con el menu de pausa abierto solo se atienden Resume, Exit y
        ESC (que reanuda, igual que Resume); el resto de teclas y los
        clicks del mapa quedan bloqueados. Con la tienda abierta solo
        se atiende su cierre (ESC, su boton o un click dentro del
        panel). Con ambos cerrados, ESC abre la pausa y Q sale
        siempre. Los clics en la barra Undo/Redo/Martillo se atienden
        antes que el mapa: nunca colocan torres ni abren la tienda.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if self.pause_menu.is_open:
                if not self._process_pause_event(event):
                    return False
                continue
            if self.shop.is_open:
                self._process_shop_event(event)
                continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    return False
                if event.key == pygame.K_F3:
                    self.debug_range = not self.debug_range
                    continue
                if event.key == pygame.K_ESCAPE:
                    if self.placing:
                        self.placing = False
                        self.selected_kind = None
                        continue
                    if self.selling:
                        self.selling = False
                        continue
                    self.pause_menu.open()
                    continue
                if event.key in self.KIND_KEYS:
                    index = self.KIND_KEYS.index(event.key)
                    if index < len(self.TOWER_KIND_ORDER):
                        self.selected_kind = self.TOWER_KIND_ORDER[index]
                        self.placing = True
                        self.selling = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.shop.hits_opener(event.pos):
                    self.shop.open()
                elif self.undo_button_rect.collidepoint(event.pos):
                    if self.model.can_undo():
                        self.model.undo_last_placement()
                elif self.redo_button_rect.collidepoint(event.pos):
                    if self.model.can_redo():
                        self.model.redo_last_placement(self.tiled_map)
                elif self.hammer_button_rect.collidepoint(event.pos):
                    self.selling = not self.selling
                    if self.selling:
                        self.placing = False
                        self.selected_kind = None
                elif self.selling:
                    self._try_sell_tower(*event.pos)
                else:
                    self._pending_click = event.pos
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                self.placing = False
                self.selected_kind = None
                self.selling = False
        return True

    def _process_pause_event(self, event):
        """Eventos atendidos mientras el menu de pausa esta abierto. O(1).

        ESC y el boton Resume cierran el menu y reanudan; Exit cierra
        Pygame (devuelve False para que main.py salga del bucle). El
        resto de teclas y clicks quedan bloqueados. Devuelve False
        solo cuando hay que salir del juego.
        """
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                self.pause_menu.close()
                return True
            if event.key == pygame.K_q:
                return False
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            result = self.pause_menu.handle_click(event.pos)
            if result is not None and result[0] == "exit":
                return False
        return True

    def _process_shop_event(self, event):
        """Eventos atendidos mientras la tienda esta abierta. O(1).

        ESC y el clic derecho cierran el panel; el click izquierdo se
        reparte entre el boton de cierre y las tarjetas del catalogo.
        Elegir una torre asequible arma su colocacion; una torre sin
        fondos no inicia la compra y el panel sigue abierto.
        """
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.shop.close()
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            self.shop.close()
            return
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        result = self.shop.handle_click(event.pos)
        if result is None:
            return
        if result[0] == "select":
            self.selected_kind = result[1]
            self.placing = True
            self.selling = False
        # ("insufficient", kind): saldo insuficiente; no se arma la
        # colocacion y la tienda permanece abierta.

    def close(self):
        """Cierra la ventana y finaliza Pygame. O(1)."""
        pygame.quit()

    # ------------------------------------------------------------------
    # Conversion de coordenadas
    # ------------------------------------------------------------------
    def screen_to_map(self, screen_x, screen_y):
        """Convierte coordenadas de ventana a pixeles del mapa Tiled. O(1)."""
        if self.scale <= 0:
            return 0.0, 0.0
        mx = (screen_x - self.offset_x) / self.scale
        my = (screen_y - self.offset_y) / self.scale
        return mx, my

    def map_to_screen(self, map_x, map_y):
        """Convierte pixeles del mapa Tiled a coordenadas de ventana. O(1)."""
        return (
            self.offset_x + map_x * self.scale,
            self.offset_y + map_y * self.scale,
        )

    def _point_map_at(self, progress):
        """Punto en pixeles de mapa para un progreso del modelo. O(p).

        Sin mapa de Tiled se usa la misma parametrizacion lineal que
        _point_at (en ese caso las coordenadas de mapa y de ventana
        coinciden porque scale=1 y el offset es cero).
        """
        path_length = max(1e-9, self.model.path_length)
        fraction = min(1.0, max(0.0, progress / path_length))
        if self.tiled_map is None:
            return 40 + fraction * (self.WIDTH - 80), float(self.HEIGHT // 2)
        return self.tiled_map.point_at_fraction(fraction)

    def _point_at(self, progress):
        """Punto en pantalla para un progreso del modelo. O(p)."""
        if self.tiled_map is None:
            return self._point_map_at(progress)
        map_x, map_y = self._point_map_at(progress)
        return self.map_to_screen(map_x, map_y)

    def _tower_screen_point(self, tower):
        """Base de la torre en pixeles de pantalla. O(1).

        Usa la posicion en el mapa (map_x, map_y) cuando existe y, si
        no, su progreso sobre el camino. Es el punto que la torre
        toca en el suelo y el ancla de su sprite.
        """
        if tower.map_x is not None and tower.map_y is not None:
            return self.map_to_screen(tower.map_x, tower.map_y)
        return self._point_at(tower.position)

    # ------------------------------------------------------------------
    # Colocacion de torres
    # ------------------------------------------------------------------
    def _try_place_tower(self, screen_x, screen_y):
        """Valida, compra y coloca la torre seleccionada en el click.

        El tipo seleccionado (selected_kind) aporta nombre, danio,
        cadencia, alcance y precio desde Model.game_model.TOWER_KINDS
        (datos.md). La colocacion usa model.buy_tower, que vuelve a
        comprobar el saldo y descuenta el precio solo si la torre se
        crea: si el saldo no alcanza en el momento de colocar no se
        crea nada ni se cobra. No hace nada si no hay torre
        seleccionada (estado inicial de partida), si el modo de
        colocacion esta cancelado o si la tienda esta abierta. O(z+t).
        """
        if (
            self.tiled_map is None
            or not self.placing
            or self.selected_kind is None
            or self.shop.is_open
        ):
            return
        map_x, map_y = self.screen_to_map(screen_x, screen_y)
        valid, _ = self.model.can_place_tower_at(
            map_x, map_y, self.TOWER_FOOTPRINT, self.tiled_map
        )
        if not valid:
            return
        progress = self.tiled_map.closest_progress_on_path(map_x, map_y)
        self.model.buy_tower(
            kind=self.selected_kind,
            position=progress,
            map_x=map_x, map_y=map_y,
            footprint=self.TOWER_FOOTPRINT,
        )

    def _draw_placement_preview(self):
        """Vista previa fantasma de la torre en colocacion. O(1).

        Mientras dura el modo de colocacion (con una torre seleccionada
        y la tienda cerrada) dibuja el sprite del tipo seleccionado
        semitransparente en la posicion del cursor, junto al circulo de
        su huella en verde si la posicion es valida o en rojo si no lo
        es, y el circulo semitransparente de alcance (circulo.md). Sin
        seleccion (inicio de partida) no dibuja nada. Es solo visual:
        no toca el modelo ni cobra nada.
        """
        if (
            not self.placing
            or self.selected_kind is None
            or self.shop.is_open
            or self.tiled_map is None
        ):
            return
        mouse_x, mouse_y = pygame.mouse.get_pos()
        map_x, map_y = self.screen_to_map(mouse_x, mouse_y)
        valid, _ = self.model.can_place_tower_at(
            map_x, map_y, self.TOWER_FOOTPRINT, self.tiled_map
        )
        center = (int(mouse_x), int(mouse_y))

        # Circulo de alcance semitransparente centrado en el punto de
        # anclaje de la torre (la base del sprite), usando el radio
        # real TOWER_RANGE_PX escalado a pantalla. Circulo.md: solo
        # visible mientras placing esta activo.
        range_radius = int(self.TOWER_RANGE_PX * self.scale)
        if range_radius > 0:
            range_surface = pygame.Surface(
                (range_radius * 2, range_radius * 2), pygame.SRCALPHA
            )
            pygame.draw.circle(
                range_surface,
                self.RANGE_FILL,
                (range_radius, range_radius),
                range_radius,
            )
            self.screen.blit(
                range_surface,
                (center[0] - range_radius, center[1] - range_radius),
            )

        radius_px = max(4, int(self.TOWER_FOOTPRINT * self.scale))
        fill = self.PREVIEW_VALID_FILL if valid else self.PREVIEW_INVALID_FILL
        preview_surface = pygame.Surface(
            (radius_px * 2, radius_px * 2), pygame.SRCALPHA
        )
        pygame.draw.circle(
            preview_surface, fill, (radius_px, radius_px), radius_px
        )
        self.screen.blit(
            preview_surface, (center[0] - radius_px, center[1] - radius_px)
        )

        ghost = None
        anchor_x = anchor_y = 0
        if self.animations.has(self.selected_kind):
            ghost = self.animations.idle(self.selected_kind).copy()
            anchor_x, anchor_y = self.animations.anchor(self.selected_kind)
        else:
            source = self.assets.tower(self.selected_kind, firing=False)
            if source is not None:
                ghost = source.copy()
                anchor_x, anchor_y = self.assets.tower_anchor(self.selected_kind)
        if ghost is not None:
            ghost.set_alpha(self.PREVIEW_ALPHA)
            self.screen.blit(
                ghost, (center[0] - anchor_x, center[1] - anchor_y)
            )

    # ------------------------------------------------------------------
    # Barra de acciones: Undo, Redo y modo venta del martillo
    # ------------------------------------------------------------------
    def _load_action_icon(self, filename):
        """Icono PNG de la barra de acciones, escalado al boton. O(1).

        Usa exactamente los archivos preparados en
        assets/ui/tienda/iconos (undoredo.md); no se generan iconos.
        """
        path = os.path.join(self.ACTION_ICON_DIR, filename)
        image = pygame.image.load(path).convert_alpha()
        return pygame.transform.smoothscale(
            image, (self.ACTION_ICON_SIZE, self.ACTION_ICON_SIZE)
        )

    def _tower_hitbox(self, tower):
        """Caja clicable del sprite de la torre, para el modo venta. O(1).

        Calculo en dos pasos (fix.md), usando siempre las mismas
        coordenadas que _draw_tower al pintarla (sin repetir escalados
        ni offsets: el frame ya viene escalado de TowerAnimations y el
        anchor esta en esa misma escala):

        1. Rect dibujado: topleft = centro - anchor, identico al blit.
        2. Recorte al contenido visible: los PNG de animacion tienen el
           lienzo de 165x349 con la mitad superior TRANSPARENTE (la torre
           real solo ocupa la banda inferior), por lo que el rect del
           lienzo entero salia ~74 px por encima de la torre («altura de
           dos torres») y su izquierda quedaba por el pasto de al lado.
           get_bounding_rect() devuelve exactamente el area no
           transparente del frame, ya en pixeles de pantalla, y se
           adapta al tamano real de cada variante.

        Solo se anade un margen de tolerancia pequeno y asimetrico
        (SELL_HITBOX_PAD_*), el mas estrecho por la izquierda. Sin
        sprite visible se recurre a la caja de la huella dibujada en
        circulo. La hitbox NO modifica el dibujo de la torre; se usa
        unicamente para la seleccion del modo venta.
        """
        x, y = self._tower_screen_point(tower)
        center = (int(x), int(y))
        frame = None
        anchor = None
        if self.animations.has(tower.kind):
            frame = self.animations.idle(tower.kind)
            anchor = self.animations.anchor(tower.kind)
        else:
            frame = self.assets.tower(tower.kind, firing=False)
            if frame is not None:
                anchor = self.assets.tower_anchor(tower.kind)
        if frame is None or anchor is None:
            radius = max(
                4, int((tower.footprint or self.TOWER_FOOTPRINT) * self.scale)
            )
            return pygame.Rect(
                center[0] - radius, center[1] - radius, radius * 2, radius * 2
            )
        # 1. Rect exacto del blit (mismas coordenadas que _draw_tower).
        drawn = frame.get_rect(
            topleft=(center[0] - anchor[0], center[1] - anchor[1])
        )
        # 2. Solo el contenido visible del frame, trasladado a pantalla.
        visible = frame.get_bounding_rect().move(drawn.x, drawn.y)
        # 3. Tolerancia de click, asimetrica (izquierda la mas estrecha).
        #    Se recalcula x/y + tamano: asignar .right/.bottom en un Rect
        #    de Pygame solo mueve la posicion, no ensancha el rectangulo.
        return pygame.Rect(
            visible.x - self.SELL_HITBOX_PAD_LEFT,
            visible.y - self.SELL_HITBOX_PAD_TOP,
            visible.w + self.SELL_HITBOX_PAD_LEFT + self.SELL_HITBOX_PAD_RIGHT,
            visible.h + self.SELL_HITBOX_PAD_TOP + self.SELL_HITBOX_PAD_BOTTOM,
        )

    def _tower_at_screen(self, screen_x, screen_y):
        """Torre cuyo sprite esta bajo el punto de pantalla, o None. O(t).

        Hit-testing exclusivo de la venta (undoredo.md / hitbox.md):
        comprueba la hitbox visual de cada torre (_tower_hitbox) en vez
        de un radio alrededor de su base, para poder vender tambien por
        la parte central y superior de sprites altos. Si dos hitboxes se
        superponen gana la torre visualmente delante, es decir, la que
        se dibuja mas tarde en el orden de renderizado (mayor
        _tower_sort_y, el mismo eje que usa _draw_entities_y_sorted).
        """
        point = (int(screen_x), int(screen_y))
        best = None
        best_sort_y = None
        for tower in self.model.towers:
            if not self._tower_hitbox(tower).collidepoint(point):
                continue
            sort_y = self._tower_sort_y(tower)
            if best_sort_y is None or sort_y > best_sort_y:
                best = tower
                best_sort_y = sort_y
        return best

    def _try_sell_tower(self, screen_x, screen_y):
        """Vende la torre bajo el click si el modo venta esta activo. O(t).

        Un click en zona vacia no hace nada (el modo sigue activo para
        reintentar). Tras vender, el modo venta se desactiva solo; la
        venta la valida y reembolsa el modelo (sell_tower), que ademas
        descarta las acciones de Undo/Redo que referenciaran la torre.
        """
        if not self.selling or self.shop.is_open:
            return None
        tower = self._tower_at_screen(screen_x, screen_y)
        if tower is None:
            return None
        refund = self.model.sell_tower(tower)
        if refund:
            self.selling = False
        return refund

    def _draw_action_buttons(self):
        """Dibuja los botones Undo, Redo y Martillo. O(1).

        Mismo lenguaje visual que el resto de la UI medieval: panel
        semitransparente redondeado (HUD_BG), borde dorado al pasar el
        raton, borde naranja mientras el modo venta esta activo y el
        icono atenuado cuando la accion no esta disponible.
        """
        mouse_pos = pygame.mouse.get_pos()
        buttons = (
            (
                self.undo_button_rect,
                self.undo_icon,
                self.model.can_undo(),
                False,
            ),
            (
                self.redo_button_rect,
                self.redo_icon,
                self.model.can_redo(),
                False,
            ),
            (
                self.hammer_button_rect,
                self.hammer_icon,
                True,
                self.selling,
            ),
        )
        for rect, icon, enabled, active in buttons:
            panel = rect.inflate(6, 6)
            pygame.draw.rect(self.screen, self.HUD_BG, panel, border_radius=6)
            if active:
                border_color = self.ACTION_ACTIVE_BORDER
                width = 3
            elif not enabled:
                border_color = self.ACTION_DISABLED_BORDER
                width = 2
            elif rect.collidepoint(mouse_pos):
                border_color = self.ACTION_HOVER_BORDER
                width = 3
            else:
                border_color = self.ACTION_BORDER
                width = 2
            pygame.draw.rect(
                self.screen, border_color, panel, width=width, border_radius=6
            )
            if enabled:
                self.screen.blit(icon, icon.get_rect(center=rect.center))
            else:
                dimmed = icon.copy()
                dimmed.set_alpha(self.ACTION_DISABLED_ALPHA)
                self.screen.blit(dimmed, dimmed.get_rect(center=rect.center))

    def _draw_sell_cursor(self):
        """Icono del martillo siguiendo al cursor en modo venta. O(1).

        Senal visual de que el modo venta esta activo (undoredo.md); se
        oculta mientras la tienda tapa el mapa.
        """
        if not self.selling or self.shop.is_open:
            return
        mouse_x, mouse_y = pygame.mouse.get_pos()
        self.screen.blit(
            self.sell_cursor_icon,
            self.sell_cursor_icon.get_rect(center=(mouse_x, mouse_y)),
        )

    def _draw_sell_hitboxes(self):
        """Depuracion temporal: dibuja la hitbox de venta de cada torre. O(t).

        Solo con DEBUG_SELL_HITBOX = True y el modo martillo activo:
        pinta un rectangulo por encima de cada torre para comprobar
        visualmente que la clicable coincide con su sprite visible.
        """
        if not (self.DEBUG_SELL_HITBOX and self.selling):
            return
        for tower in self.model.towers:
            pygame.draw.rect(
                self.screen, (255, 0, 255), self._tower_hitbox(tower), 1
            )

    # ------------------------------------------------------------------
    # Dibujo
    # ------------------------------------------------------------------
    def draw(self):
        """Dibuja el estado completo del modelo. O(n + p + i).

        Convierte los disparos pendientes del modelo en proyectiles,
        avanza proyectiles e impactos con el tiempo del frame (tick).

        El orden de dibujo sobre el mapa es: circulos de alcance,
        torres y enemigos con Y-sorting (de menor a mayor Y de
        contacto con el suelo), proyectiles e impactos por encima de
        las entidades y, por ultimo, las Decoraciones_superiores del
        mapa de Tiled.
        """
        if self._pending_click is not None and not self.paused:
            self._try_place_tower(*self._pending_click)
            self._pending_click = None

        self._consume_shots()
        self._advance_effects()

        self.screen.fill(self.BACKGROUND)

        if self.renderer is not None:
            scaled = pygame.transform.smoothscale(
                self.renderer.base_surface,
                (
                    int(self.tiled_map.pixel_width * self.scale),
                    int(self.tiled_map.pixel_height * self.scale),
                ),
            )
            self.screen.blit(scaled, (self.offset_x, self.offset_y))

        self._draw_entities_y_sorted()
        self._draw_debug_range()
        self._draw_projectiles()
        self._draw_impacts()
        self._draw_placement_preview()

        if self.renderer is not None:
            scaled_upper = pygame.transform.smoothscale(
                self.renderer.upper_surface,
                (
                    int(self.tiled_map.pixel_width * self.scale),
                    int(self.tiled_map.pixel_height * self.scale),
                ),
            )
            self.screen.blit(scaled_upper, (self.offset_x, self.offset_y))

        self._draw_hud()
        self._draw_coin_counter()
        self._draw_action_buttons()

        if self.shop.is_open:
            self.shop.draw(self.screen)
        else:
            self.shop.draw_opener(self.screen)
        self._draw_sell_cursor()
        self._draw_sell_hitboxes()
        self.pause_menu.draw(self.screen)
        pygame.display.flip()

    def _build_hud_background(self):
        """Panel semitransparento detras del HUD. O(1)."""
        surface = pygame.Surface((self.WIDTH, 56), pygame.SRCALPHA)
        pygame.draw.rect(surface, self.HUD_BG, surface.get_rect(), border_radius=6)
        return surface

    def _range_radius_px(self, tower):
        """Radio del circulo de alcance en pixeles de pantalla. O(1).

        tower.range esta expresado en pixeles del mapa (misma unidad que
        Enemy.progress), por lo que el radio en pantalla se calcula
        aplicando el escalado del mapa de Tiled. Sin mapa, el progreso
        se dibuja de forma lineal sobre la ventana.
        """
        if self.tiled_map is not None:
            return int(tower.range * self.scale)
        path_length = max(1e-9, self.model.path_length)
        return int(tower.range / path_length * (self.WIDTH - 80))

    def _tower_anim_duration(self, tower):
        """Segundos que dura la animacion de disparo de la torre. O(1).

        Las torres con frames PNG usan la duracion de su animacion de
        ataque (View.tower_animations); las demas, FIRE_ANIM_TIME.
        """
        if self.animations.has(tower.kind):
            return self.animations.duration(tower.kind)
        return self.FIRE_ANIM_TIME

    def _tower_fire_progress(self, tower):
        """Progreso 0..1 de la animacion de disparo de la torre. O(1).

        Usa el temporizador local que se arma al consumir un disparo
        (sin estado extra en el modelo): 0 en el instante del disparo
        y crece hasta 1 al terminar la animacion del tipo.
        """
        remaining = self._fire_timers.get(tower.tower_id, 0.0)
        if remaining <= 0.0:
            return 0.0
        duration = self._tower_anim_duration(tower)
        if duration <= 0.0:
            return 0.0
        return 1.0 - remaining / duration

    def _tower_has_projectile_in_flight(self, tower):
        """True si aun vuela un proyectil lanzado por esa torre. O(p)."""
        for projectile in self.projectiles:
            if projectile.get("tower") is tower:
                return True
        return False

    def _tower_hover_position(self, tower, fire_progress):
        """Posicion de pantalla de la munición flotante. O(1).

        Flota sobre la torre con un seno (fase por torre) y se
        esconde mientras hay un proyectil en vuelo o durante el
        rebote de disparo.
        """
        if fire_progress > 0.0 or self._tower_has_projectile_in_flight(tower):
            return None
        base_x, base_y = self._tower_screen_point(tower)
        bob = (
            math.sin(self._anim_time * self.HOVER_BOB_SPEED + tower.tower_id * 0.9)
            * self.HOVER_BOB_PX
            * self.scale
        )
        return base_x, base_y - self.assets.hover_height(tower.kind) + bob

    # ------------------------------------------------------------------
    # Torres y enemigos (orden de profundidad por la coordenada Y)
    # ------------------------------------------------------------------
    def _tower_sort_y(self, tower):
        """Y de pantalla de la base de la torre, para ordenar. O(1)."""
        return self._tower_screen_point(tower)[1]

    def _enemy_sort_y(self, enemy):
        """Y de pantalla de los pies del enemigo, para ordenar. O(1).

        El enemigo se dibuja como un circulo cuyo borde inferior es su
        punto de contacto con el suelo; ordenar por el centro
        descolocaria su profundidad respecto a la base de las torres.
        """
        return self._point_at(enemy.progress)[1] + self.ENEMY_RADIUS

    def _draw_entities_y_sorted(self):
        """Dibuja torres y enemigos ordenados por su Y de contacto. O((t+n)log(t+n)).

        Y-sorting: se dibuja primero la entidad con menor Y (mas arriba
        en pantalla, visualmente detras) y encima la de mayor Y (mas
        abajo, visualmente delante). Asi un enemigo que pasa por
        delante de una torre alta la tapa y uno que pasa detras queda
        cubierto por la torre. Si dos entidades coinciden en Y gana el
        enemigo, como en el orden anterior.
        """
        entries = []
        for tower in self.model.towers:
            entries.append(
                (self._tower_sort_y(tower), 0, self._draw_tower, tower)
            )
        for enemy in self.model.active_enemies:
            entries.append(
                (self._enemy_sort_y(enemy), 1, self._draw_enemy, enemy)
            )
        entries.sort(key=lambda entry: (entry[0], entry[1]))
        for _, _, draw, entity in entries:
            draw(entity)

    def _draw_debug_range(self):
        """Dibuja la visualizacion de depuracion del alcance (fixed.md).

        Con debug_range activo (tecla F3), para cada torre colocada
        dibuja:
          - Circulo de radio 210 px (TOWER_RANGE_PX) centrado en el
            punto exacto que usa la logica de combate (is_in_range).
          - Punto rojo en el centro del calculo de distancia.
        El centro coincide con el empleado en la deteccion de enemigos,
        no uno aproximado para dibujar. O(t).
        """
        if not self.debug_range:
            return
        for tower in self.model.towers:
            # Centro real del calculo de ataque: Tower.position (en
            # pixeles de mapa a lo largo del camino), convertido a
            # pantalla con _point_at que usa la misma parametrizacion
            # que Enemy.progress.
            center_x, center_y = self._point_at(tower.position)
            radius_px = self._range_radius_px(tower)
            # Circulo de radio exacto
            pygame.draw.circle(
                self.screen,
                (0, 255, 0, 80),
                (int(center_x), int(center_y)),
                radius_px,
                2,
            )
            # Punto rojo en el centro del calculo
            pygame.draw.circle(
                self.screen,
                (255, 0, 0),
                (int(center_x), int(center_y)),
                4,
            )

    def _draw_tower(self, tower):
        """Dibuja una torre animada (o su sprite) en su posicion. O(1).

        Con frames PNG cables (Semana 4) usa el frame de reposo o el
        de ataque segun _tower_fire_progress; sin animacion aplica el
        sprite compuesto con rebote y munición flotante de la Semana 3.
        """
        x, y = self._tower_screen_point(tower)
        fire_progress = self._tower_fire_progress(tower)
        center = (int(x), int(y))

        if self.animations.has(tower.kind):
            # Frames PNG (Semana 4): quietas en reposo y con la
            # animacion de lanzamiento durante el temporizador de
            # disparo. Sin rebote ni munición flotante: el frame de
            # reposo ya muestra la munición asentada en la torre.
            frame = self.animations.frame(tower.kind, fire_progress)
            anchor_x, anchor_y = self.animations.anchor(tower.kind)
            self.screen.blit(
                frame,
                (center[0] - anchor_x, center[1] - anchor_y),
            )
            return

        sprite = self.assets.tower(tower.kind, firing=fire_progress > 0.0)
        if sprite is not None:
            anchor_x, anchor_y = self.assets.tower_anchor(tower.kind)
            bounce = 0.0
            if fire_progress > 0.0:
                bounce = (
                    math.sin(fire_progress * math.pi)
                    * self.BOUNCE_PX
                    * self.scale
                )
            self.screen.blit(
                sprite,
                (center[0] - anchor_x, center[1] - anchor_y - int(bounce)),
            )
            hover_pos = self._tower_hover_position(tower, fire_progress)
            if hover_pos is not None:
                hover_image = self.assets.hover(tower.kind)
                hx, hy = hover_pos
                self.screen.blit(
                    hover_image,
                    (
                        int(hx) - hover_image.get_width() // 2,
                        int(hy) - hover_image.get_height() // 2,
                    ),
                )
        else:
            footprint_px = max(4, int(tower.footprint * self.scale)) \
                if tower.footprint else self.TOWER_FOOTPRINT
            pygame.draw.circle(self.screen, self.TOWER_COLOR, center, footprint_px)
            pygame.draw.circle(
                self.screen, self.TOWER_BORDER, center, footprint_px, 2
            )

    # ------------------------------------------------------------------
    # Proyectiles e impactos (visuales; el danio ya se aplico al disparar)
    # ------------------------------------------------------------------
    def _consume_shots(self):
        """Convierte los disparos del modelo en proyectiles en vuelo. O(s).

        model.shots son eventos del ultimo update(); cada uno se
        convierte en un proyectil que vuela desde su torre hasta la
        posicion actual del enemigo objetivo (misma conversion
        progress -> mapa que usan los enemigos).
        """
        for shot in self.model.shots:
            tower = shot["tower"]
            if tower.map_x is not None and tower.map_y is not None:
                origin_x, origin_y = tower.map_x, tower.map_y
            else:
                origin_x, origin_y = self._point_map_at(tower.position)
            self._fire_timers[tower.tower_id] = self._tower_anim_duration(tower)
            self.projectiles.append({
                "kind": shot["kind"],
                "x": origin_x,
                "y": origin_y,
                "target": shot["enemy"],
                "tower": tower,
                "angle": 0.0,
                "age": 0.0,
            })
        self.model.shots.clear()

    def _target_point(self, enemy):
        """Posicion en pixeles de mapa del enemigo (por su progreso). O(p)."""
        return self._point_map_at(enemy.progress)

    def _advance_effects(self):
        """Mueve proyectiles y avanza los frames de impacto. O(p + i).

        Con la tienda abierta el tiempo efectivo es cero: los
        proyectiles y los impactos se congelan igual que la simulacion.
        """
        dt = 0.0 if self.paused else self._dt
        self._anim_time += max(0.0, dt)
        if dt > 0.0 and self._fire_timers:
            for tower_id in list(self._fire_timers):
                self._fire_timers[tower_id] -= dt
                if self._fire_timers[tower_id] <= 0.0:
                    del self._fire_timers[tower_id]
        if dt <= 0.0 and not self.impacts:
            return

        still_flying = []
        for projectile in self.projectiles:
            spec = self.assets.spec(projectile["kind"])
            target_x, target_y = self._target_point(projectile["target"])
            dx = target_x - projectile["x"]
            dy = target_y - projectile["y"]
            distance = (dx * dx + dy * dy) ** 0.5

            self._update_projectile_rotation(projectile, spec, dx, dy, distance, dt)

            step = spec["projectile_speed"] * dt
            if distance <= step or distance < 1.0:
                self._spawn_impact(projectile["kind"], target_x, target_y)
            else:
                projectile["x"] += dx / distance * step
                projectile["y"] += dy / distance * step
                still_flying.append(projectile)
        self.projectiles = still_flying

        still_active = []
        for impact in self.impacts:
            impact["time"] += dt
            spec = self.assets.spec(impact["kind"])
            index = int(impact["time"] / max(1e-9, spec["impact_frame_time"]))
            if index >= len(self.assets.impact_frames(impact["kind"])):
                continue
            impact["index"] = index
            still_active.append(impact)
        self.impacts = still_active

    def _update_projectile_rotation(self, projectile, spec, dx, dy, distance, dt):
        """Orienta el proyectil segun el modo de rotacion de su spec. O(1).

        - "aim": sprite dibujado apuntando arriba; se gira hacia el
          objetivo.
        - "fall": 35.png esta dibujado en orientacion de caida (la
          llama apunta hacia abajo); se alinea con la direccion real
          del movimiento y va girando hacia 0 grados (hacia abajo)
          durante el vuelo, por el camino mas corto.
        - "spin": gira sobre si mismo mientras vuela.
        """
        age = projectile.get("age", 0.0)
        rotate = spec.get("rotate")
        if rotate == "aim":
            if distance > 1e-6:
                projectile["angle"] = math.degrees(math.atan2(-dx, -dy))
        elif rotate == "fall":
            if age <= 0.0 and distance > 1e-6:
                # Un sprite dibujado apuntando hacia abajo se orienta
                # hacia (dx, dy) con atan2(dx, dy).
                projectile["angle"] = math.degrees(math.atan2(dx, dy)) % 360.0
            delta = (projectile["angle"] + 180.0) % 360.0 - 180.0
            pitch = self.FALL_PITCH_RATE * max(0.0, dt)
            if abs(delta) <= pitch:
                projectile["angle"] = 0.0
            elif delta > 0.0:
                projectile["angle"] = (delta - pitch) % 360.0
            else:
                projectile["angle"] = (delta + pitch) % 360.0
        elif rotate == "spin":
            projectile["angle"] = (
                projectile["angle"] + self.HEAVY_SPIN_RATE * dt
            ) % 360.0
        projectile["age"] = age + max(0.0, dt)

    def _spawn_impact(self, kind, x, y):
        """Registra un impacto nuevo en la posicion (x, y) de mapa. O(1)."""
        self.impacts.append({"kind": kind, "x": x, "y": y, "time": 0.0, "index": 0})

    def _blit_centered(self, image, map_x, map_y):
        """Dibuja image centrado en una posicion de mapa. O(1)."""
        x, y = self.map_to_screen(map_x, map_y)
        self.screen.blit(
            image,
            (
                int(x) - image.get_width() // 2,
                int(y) - image.get_height() // 2,
            ),
        )

    def _draw_projectiles(self):
        """Dibuja los proyectiles en vuelo, girados segun su tipo. O(p)."""
        for projectile in self.projectiles:
            image = self.assets.projectile(projectile["kind"])
            angle = projectile.get("angle", 0.0)
            if angle:
                image = pygame.transform.rotate(image, angle)
            self._blit_centered(image, projectile["x"], projectile["y"])

    def _draw_impacts(self):
        """Dibuja el frame actual de cada impacto activo. O(i)."""
        for impact in self.impacts:
            frames = self.assets.impact_frames(impact["kind"])
            if not frames:
                continue
            image = frames[min(impact["index"], len(frames) - 1)]
            self._blit_centered(image, impact["x"], impact["y"])

    def _draw_enemies(self):
        """Dibuja los enemigos activos con barra de vida. O(n)."""
        for enemy in self.model.active_enemies:
            self._draw_enemy(enemy)

    def _draw_enemy(self, enemy):
        """Dibuja un enemigo y su barra de vida en su posicion. O(1)."""
        x, y = self._point_at(enemy.progress)
        x, y = int(x), int(y)
        center = (x, y)

        pygame.draw.circle(self.screen, self.ENEMY_COLOR, center, self.ENEMY_RADIUS)
        pygame.draw.circle(
            self.screen, self.ENEMY_BORDER, center, self.ENEMY_RADIUS, 2
        )

        bar_width = 22
        ratio = 0.0
        if enemy.max_hp > 0:
            ratio = max(0.0, min(1.0, enemy.hp / enemy.max_hp))
        bar = pygame.Rect(x - bar_width // 2, y - 20, bar_width, 4)
        pygame.draw.rect(self.screen, self.HP_BG, bar)
        fill = bar.copy()
        fill.width = int(bar_width * ratio)
        if fill.width > 0:
            pygame.draw.rect(self.screen, self.HP_FILL, fill)

    def _draw_hud(self):
        """Dibuja el resumen del estado y la ayuda de controles."""
        self.screen.blit(self.hud_background, (6, 6))
        state_text = (
            f"Pendientes: {self.model.pending_count}   "
            f"Activos: {self.model.active_count}   "
            f"Torres: {len(self.model.towers)}   "
            f"Historial: {self.model.history_count}"
        )
        self.screen.blit(
            self.font.render(state_text, True, self.TEXT_COLOR), (14, 12)
        )
        kinds_text = "  ".join(
            f"{index + 1}:{kind}"
            for index, kind in enumerate(self.TOWER_KIND_ORDER)
        )
        placement_text = (
            f"Sel: {self.selected_kind}"
            if self.placing and self.selected_kind is not None
            else "Sel: --"
        )
        help_text = (
            f"{kinds_text}   {placement_text}   "
            f"Clic izq: colocar   Clic der/ESC: cancelar   "
            f"Martillo: vender   ESC: salir   Tienda: boton inferior derecho"
        )
        self.screen.blit(
            self.font.render(help_text, True, self.TEXT_DIM), (14, 32)
        )

    def _draw_coin_counter(self):
        """Contador de estrellas en la esquina superior derecha. O(d).

        Lee el saldo real del modelo (model.stars, actualizacion.md) y
        lo dibuja con la estrella dorada (SpriteFont.STAR_GOLD) y los
        digitos del spritesheet de madera, no con la fuente
        convencional. Se repinta en cada frame, por lo que refleja al
        instante las compras y las recompensas por enemigos.
        """
        stars = max(0, int(self.model.stars))
        star = self.sprite_font.star(self.COIN_GLYPH_H)
        digits = str(stars)
        text_w, _ = self.sprite_font.measure(
            digits, self.COIN_GLYPH_H, self.COIN_DIGIT_SPACING
        )

        gap = self.COIN_GLYPH_H // 4
        total_w = star.get_width() + gap + text_w
        x = self.WIDTH - total_w - self.COIN_HUD_PAD
        y = self.COIN_HUD_PAD

        pad = self.COIN_GLYPH_H // 3
        panel = pygame.Rect(
            x - pad, y - pad, total_w + pad * 2, self.COIN_GLYPH_H + pad * 2
        )
        pygame.draw.rect(self.screen, self.HUD_BG, panel, border_radius=6)

        self.screen.blit(star, (x, y))
        self.sprite_font.render(
            self.screen,
            digits,
            (x + star.get_width() + gap, y),
            self.COIN_GLYPH_H,
            self.COIN_DIGIT_SPACING,
        )
