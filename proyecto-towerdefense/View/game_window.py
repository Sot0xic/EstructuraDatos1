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
    - Decoraciones_superiores por encima de enemigos y torres
    - resumen del estado (HUD)

Permite colocar torres haciendo click izquierdo en el mapa, validando
que la posicion no este en zona bloqueada, fuera del mapa ni encima de
otra torre. Las teclas 1, 2 y 3 seleccionan el tipo de torre (basica,
fuego o pesada) antes de colocarla. Las torres se dibujan en su
posicion del mapa y su alcance se calcula sobre el camino (progreso
mas cercano).

Los proyectiles son puramente visuales: el danio se aplica una sola
vez, en el momento del ataque (modelo/controlador). El modelo expone
model.shots (eventos de disparo) que esta vista consume al dibujar
para animar proyectil -> impacto sin duplicar el danio.

La ventana solo dibuja el modelo; el ciclo del juego se ejecuta en
main.py.
"""

import math

import pygame

from Model.game_model import TOWER_KINDS
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
    # que ambas cosas coincidan en pantalla.
    TOWER_RANGE_PX = 210.0
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
        self.selected_kind = "basica"
        self.projectiles = []   # proyectiles en vuelo (pos. en mapa)
        self.impacts = []       # impactos en animacion (pos. en mapa)
        self._anim_time = 0.0   # reloj acumulado para flote de munición
        self._fire_timers = {}  # tid -> segundos restantes de anim. de disparo

        self.hud_background = self._build_hud_background()
        self._pending_click = None
        self._dt = 0.0

    # ------------------------------------------------------------------
    # Ciclo (usado por main.py)
    # ------------------------------------------------------------------
    def tick(self):
        """Limita la velocidad del ciclo y devuelve el tiempo del frame. O(1)."""
        self._dt = min(self.clock.tick(self.FPS) / 1000.0, self.MAX_FRAME_TIME)
        return self._dt

    def process_events(self):
        """Procesa eventos de Pygame. Devuelve False si hay que salir. O(e)."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_ESCAPE,
                pygame.K_q,
            ):
                return False
            if (
                event.type == pygame.KEYDOWN
                and event.key in self.KIND_KEYS
            ):
                index = self.KIND_KEYS.index(event.key)
                if index < len(self.TOWER_KIND_ORDER):
                    self.selected_kind = self.TOWER_KIND_ORDER[index]
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._pending_click = event.pos
        return True

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

    # ------------------------------------------------------------------
    # Colocacion de torres
    # ------------------------------------------------------------------
    def _try_place_tower(self, screen_x, screen_y):
        """Valida y coloca la torre seleccionada en la posicion del click.

        El tipo seleccionado (selected_kind) aporta nombre, danio y
        cadencia desde Model.game_model.TOWER_KINDS. O(z + t).
        """
        if self.tiled_map is None:
            return
        map_x, map_y = self.screen_to_map(screen_x, screen_y)
        valid, _ = self.model.can_place_tower_at(
            map_x, map_y, self.TOWER_FOOTPRINT, self.tiled_map
        )
        if not valid:
            return
        progress = self.tiled_map.closest_progress_on_path(map_x, map_y)
        self.model.create_tower(
            kind=self.selected_kind,
            range=self.TOWER_RANGE_PX,
            position=progress,
            map_x=map_x, map_y=map_y,
            footprint=self.TOWER_FOOTPRINT,
        )

    # ------------------------------------------------------------------
    # Dibujo
    # ------------------------------------------------------------------
    def draw(self):
        """Dibuja el estado completo del modelo. O(n + p + i).

        Convierte los disparos pendientes del modelo en proyectiles,
        avanza proyectiles e impactos con el tiempo del frame (tick)
        y los dibuja por encima de las torres y de los enemigos.
        """
        if self._pending_click is not None:
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

        self._draw_towers()
        self._draw_projectiles()
        self._draw_enemies()
        self._draw_impacts()

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
        if tower.map_x is not None and tower.map_y is not None:
            base_x, base_y = self.map_to_screen(tower.map_x, tower.map_y)
        else:
            base_x, base_y = self._point_at(tower.position)
        bob = (
            math.sin(self._anim_time * self.HOVER_BOB_SPEED + tower.tower_id * 0.9)
            * self.HOVER_BOB_PX
            * self.scale
        )
        return base_x, base_y - self.assets.hover_height(tower.kind) + bob

    def _draw_towers(self):
        """Dibuja cada torre animada (o su sprite) y su alcance. O(t).

        Con frames PNG cables (Semana 4) usa el frame de reposo o el
        de ataque segun _tower_fire_progress; sin animacion aplica el
        sprite compuesto con rebote y munición flotante de la Semana 3.
        """
        for tower in self.model.towers:
            if tower.map_x is not None and tower.map_y is not None:
                x, y = self.map_to_screen(tower.map_x, tower.map_y)
            else:
                x, y = self._point_at(tower.position)

            radius_px = self._range_radius_px(tower)
            if radius_px > 0:
                range_surface = pygame.Surface(
                    (radius_px * 2, radius_px * 2), pygame.SRCALPHA
                )
                pygame.draw.circle(
                    range_surface, self.RANGE_FILL, (radius_px, radius_px), radius_px
                )
                self.screen.blit(
                    range_surface, (int(x) - radius_px, int(y) - radius_px)
                )

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
                continue

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
        """Mueve proyectiles y avanza los frames de impacto. O(p + i)."""
        dt = self._dt
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
        """Dibuja los enemigos activos con barra de vida."""
        for enemy in self.model.active_enemies:
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
        help_text = (
            f"{kinds_text}   Sel: {self.selected_kind}   "
            f"Click izq: colocar   ESC: salir"
        )
        self.screen.blit(
            self.font.render(help_text, True, self.TEXT_DIM), (14, 32)
        )
