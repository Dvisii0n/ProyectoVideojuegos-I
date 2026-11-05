import pygame
import pymunk


def _acercar(valor, objetivo, paso):
    """Mueve `valor` hacia `objetivo` como maximo `paso` unidades."""
    if valor < objetivo:
        return min(valor + paso, objetivo)
    return max(valor - paso, objetivo)


class Jugador:
    def __init__(
        self,
        colision_tipo,
        dimension=(50, 50),
        masa=1,
        posicion_inicial=(0, 0),
        velocidad=450,
        velocidad_salto=740,
    ):
        self.dimension = dimension
        self.masa = masa
        # momento infinito: el jugador nunca rota
        self.cuerpo = pymunk.Body(masa, float("inf"))
        # caja con esquinas redondeadas para no atorarse en las uniones de bloques
        radio = 3
        self.forma = pymunk.Poly.create_box(
            self.cuerpo, (dimension[0] - 2 * radio, dimension[1] - 2 * radio), radio
        )
        self.forma.friction = 0
        self.forma.elasticity = 0
        self.forma.collision_type = colision_tipo

        self.velocidad = velocidad
        self.velocidad_salto = velocidad_salto
        self.posicion_inicial = posicion_inicial

        # movimiento fluido
        self.aceleracion_piso = 3800
        self.frenado_piso = 4200
        self.aceleracion_aire = 2400
        self.frenado_aire = 1400
        self.gravedad_extra_caida = 700  # cae mas rapido de lo que sube
        self.velocidad_caida_max = 1100
        self.tiempo_coyote = 0.10  # puede saltar poco despues de dejar el piso
        self.tiempo_buffer = 0.12  # recuerda el salto si se presiono antes de tocar piso
        self.coyote = 0.0
        self.buffer_salto = 0.0
        self.plataforma_vel = pymunk.Vec2d(0, 0)

        self.estado = "IDLE"
        self.en_piso = False
        self.mirando = 1

        # efecto visual de estirar / aplastar
        self.escala = [1.0, 1.0]

        # Walter Cam: congela la camara y crea un recuadro; al salir por un lado
        # del recuadro el jugador aparece por el lado contrario
        self.walter_cam = False
        self.walter_rect = pygame.Rect(0, 0, 400, 300)
        self.walter_cam_posicion = pymunk.Vec2d(0, 0)
        self.estelas = []  # posiciones de teletransporte para dibujar un destello
        self.bloqueado = 0.0  # destello cuando el destino esta ocupado

    # ------------------------------------------------------------------ estado
    def set_posicion_inicial(self, posicion):
        self.posicion_inicial = posicion
        self.reaparecer(posicion)

    def reaparecer(self, posicion):
        self.cuerpo.position = posicion
        self.cuerpo.velocity = (0, 0)
        self.walter_cam = False
        self.coyote = 0.0
        self.buffer_salto = 0.0
        self.estelas.clear()
        self.escala = [1.0, 1.0]

    def activar_walter_cam(self):
        self.walter_cam = not self.walter_cam
        if self.walter_cam:
            self.walter_cam_posicion = pymunk.Vec2d(*self.cuerpo.position)

    # ------------------------------------------------------------ controles
    def pedir_salto(self):
        self.buffer_salto = self.tiempo_buffer

    def soltar_salto(self):
        # salto variable: soltar la tecla antes corta el salto
        vx, vy = self.cuerpo.velocity
        if vy < -200:
            self.cuerpo.velocity = (vx, vy * 0.45)

    def actualizar(self, dt, direccion):
        """direccion: -1 izquierda, 0 nada, 1 derecha."""
        vx, vy = self.cuerpo.velocity

        if direccion != 0:
            self.mirando = direccion

        # --- horizontal con aceleracion (no cambia de golpe)
        objetivo = direccion * self.velocidad + self.plataforma_vel.x
        if direccion != 0:
            acel = self.aceleracion_piso if self.en_piso else self.aceleracion_aire
        else:
            acel = self.frenado_piso if self.en_piso else self.frenado_aire
        vx = _acercar(vx, objetivo, acel * dt)

        # --- timers de coyote y buffer
        if self.en_piso:
            self.coyote = self.tiempo_coyote
        else:
            self.coyote = max(0.0, self.coyote - dt)
        self.buffer_salto = max(0.0, self.buffer_salto - dt)

        # --- salto
        if self.buffer_salto > 0 and self.coyote > 0:
            vy = -self.velocidad_salto + min(0, self.plataforma_vel.y)
            self.buffer_salto = 0
            self.coyote = 0
            self.en_piso = False
            self.escala = [0.78, 1.25]

        # --- caida mas pesada y con limite
        if vy > 0:
            vy += self.gravedad_extra_caida * dt
        vy = min(vy, self.velocidad_caida_max)

        self.cuerpo.velocity = (vx, vy)

        # estado (por si se usan animaciones despues)
        if not self.en_piso:
            self.estado = "SALTANDO"
        elif direccion != 0:
            self.estado = "CAMINANDO"
        else:
            self.estado = "IDLE"

        # efectos visuales
        suav = min(1.0, dt * 12)
        self.escala[0] += (1 - self.escala[0]) * suav
        self.escala[1] += (1 - self.escala[1]) * suav
        self.estelas = [(p, t - dt) for p, t in self.estelas if t - dt > 0]
        self.bloqueado = max(0.0, self.bloqueado - dt)

    def detectar_piso(self):
        """Revisa los contactos actuales: si algo esta debajo del jugador, esta en piso.
        Funciona con piso, cajas, plataformas y cualquier obstaculo."""
        estaba_en_piso = self.en_piso
        self.en_piso = False
        self.plataforma_vel = pymunk.Vec2d(0, 0)

        def revisar(arbiter):
            a, b = arbiter.shapes
            normal = arbiter.normal if a is self.forma else -arbiter.normal
            otra = b if a is self.forma else a
            if otra.sensor:
                return
            if normal.y > 0.6:  # el contacto esta debajo
                self.en_piso = True
                if otra.body.body_type == pymunk.Body.KINEMATIC:
                    self.plataforma_vel = otra.body.velocity

        self.cuerpo.each_arbiter(revisar)

        if self.en_piso and not estaba_en_piso:
            self.escala = [1.22, 0.8]  # aterrizaje

    # ------------------------------------------------------------ walter cam
    def _espacio_libre(self, space, x, y):
        mitad_w = self.dimension[0] / 2 - 1
        mitad_h = self.dimension[1] / 2 - 1
        bb = pymunk.BB(x - mitad_w, y - mitad_h, x + mitad_w, y + mitad_h)
        for forma in space.bb_query(bb, pymunk.ShapeFilter()):
            if forma is not self.forma and not forma.sensor:
                return False
        return True

    def _teletransportar(self, space, x, y):
        self.estelas.append((pymunk.Vec2d(*self.cuerpo.position), 0.25))
        self.cuerpo.position = (x, y)
        space.reindex_shapes_for_body(self.cuerpo)
        self.estelas.append((pymunk.Vec2d(x, y), 0.25))

    def aplicar_walter_cam(self, space):
        """Si el jugador toca un borde del recuadro, aparece por el borde contrario.
        - Lados: se atraviesan muros que estan dentro del recuadro.
        - Arriba/abajo: se atraviesan suelos y techos delgados (saltando por
          arriba se aparece abajo, cayendo por abajo se aparece arriba)."""
        if not self.walter_cam:
            return

        centro_x, centro_y = self.walter_cam_posicion
        mitad_w = self.walter_rect.width / 2
        mitad_h = self.walter_rect.height / 2
        mitad_jw = self.dimension[0] / 2
        mitad_jh = self.dimension[1] / 2
        x, y = self.cuerpo.position
        vx, vy = self.cuerpo.velocity

        # ---- horizontal
        lim_der = centro_x + mitad_w
        lim_izq = centro_x - mitad_w
        margen_x = mitad_jw + 4

        destino = None
        if x + mitad_jw >= lim_der and vx >= 0:
            destino, borde = lim_izq + margen_x, lim_der - mitad_jw
        elif x - mitad_jw <= lim_izq and vx <= 0:
            destino, borde = lim_der - margen_x, lim_izq + mitad_jw

        if destino is not None:
            if self._espacio_libre(space, destino, y):
                self._teletransportar(space, destino, y)
            else:
                # el otro lado esta ocupado: el borde del recuadro funciona como pared
                self.cuerpo.position = (borde, y)
                self.cuerpo.velocity = (0, vy)
                self.bloqueado = 0.2
            return

        # ---- vertical (solo justo cuando el jugador cruza el borde)
        lim_arr = centro_y - mitad_h
        lim_aba = centro_y + mitad_h
        margen_y = mitad_jh + 4

        if vy < 0 and y - mitad_jh <= lim_arr <= y:
            destino_y = lim_aba - margen_y  # sale por arriba -> aparece abajo
        elif vy > 0 and y <= lim_aba <= y + mitad_jh:
            destino_y = lim_arr + margen_y  # sale por abajo -> aparece arriba
        else:
            return

        if self._espacio_libre(space, x, destino_y):
            self._teletransportar(space, x, destino_y)
        # si el destino esta ocupado (por ejemplo dentro del piso) no pasa nada:
        # el jugador sale del recuadro normalmente y puede seguir saltando

    # ------------------------------------------------------------ dibujo
    def dibujar(self, pantalla, ox, oy):
        w = self.dimension[0] * self.escala[0]
        h = self.dimension[1] * self.escala[1]
        x, y = self.cuerpo.position
        # se aplasta hacia el piso (la base queda en su lugar)
        base = y + self.dimension[1] / 2
        rect = pygame.Rect(0, 0, round(w), round(h))
        rect.midbottom = (round(x + ox), round(base + oy))

        for pos, t in self.estelas:
            alpha = int(255 * t / 0.25)
            s = pygame.Surface(self.dimension, pygame.SRCALPHA)
            s.fill((255, 120, 120, alpha // 2))
            pantalla.blit(
                s, (pos.x + ox - self.dimension[0] / 2, pos.y + oy - self.dimension[1] / 2)
            )

        pygame.draw.rect(pantalla, (80, 200, 255), rect, border_radius=8)
        pygame.draw.rect(pantalla, (30, 110, 170), rect, 3, border_radius=8)
        # ojos que miran hacia donde se mueve
        ojo_y = rect.top + rect.h * 0.38
        for dx in (-0.12, 0.18):
            ojo_x = rect.centerx + rect.w * (dx + 0.1 * self.mirando)
            pygame.draw.circle(pantalla, (255, 255, 255), (ojo_x, ojo_y), 6)
            pygame.draw.circle(pantalla, (20, 20, 40), (ojo_x + 2 * self.mirando, ojo_y), 3)

    def dibujar_walter_cam(self, pantalla, ox, oy, sombra, tiempo):
        cx, cy = self.walter_cam_posicion
        self.walter_rect.center = (round(cx + ox), round(cy + oy))
        if not self.walter_cam:
            return

        # oscurecer todo lo que esta fuera del recuadro
        sombra.fill((0, 0, 0, 120))
        sombra.fill((0, 0, 0, 0), self.walter_rect)
        pantalla.blit(sombra, (0, 0))

        color = (255, 60, 60) if self.bloqueado <= 0 else (255, 220, 60)
        r = self.walter_rect
        pygame.draw.rect(pantalla, color, r, width=2)
        # esquinas
        largo = 22
        for (px, py), (dx, dy) in (
            (r.topleft, (1, 1)),
            (r.topright, (-1, 1)),
            (r.bottomleft, (1, -1)),
            (r.bottomright, (-1, -1)),
        ):
            pygame.draw.line(pantalla, color, (px, py), (px + dx * largo, py), 5)
            pygame.draw.line(pantalla, color, (px, py), (px, py + dy * largo), 5)
        # punto REC parpadeando
        if int(tiempo * 2) % 2 == 0:
            pygame.draw.circle(pantalla, (255, 40, 40), (r.left + 18, r.top + 18), 7)
