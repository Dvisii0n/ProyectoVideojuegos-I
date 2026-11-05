import math
import random

import pygame
import pymunk

from obstaculo import Obstaculo

PISO_Y = 620  # altura (y) de la superficie del piso
ALTURA_MURO = 2200  # los muros de camara son tan altos que no se pueden saltar
# altura de la parte de arriba del suelo de camara sobre el piso del tunel.
# Al aparecer abajo, el jugador queda 121 px bajo sus pies anteriores y el borde
# inferior del recuadro esta a 125 px: 123 deja el piso del tunel entre ambos.
ALTO_SUELO = 123

COLOR_PISO = (138, 138, 138)
COLOR_PLATAFORMA = (110, 120, 150)
COLOR_MURO_CAMARA = (70, 60, 95)
COLOR_CAJA = (200, 80, 60)
COLOR_MOVIL = (90, 170, 120)
COLOR_SIERRA = (205, 210, 220)
COLOR_SIERRA_BORDE = (110, 110, 125)
COLOR_RIEL = (45, 45, 60)


class NivelUno:
    def __init__(self, pantalla, camara, tipo_colisiones):
        self.camara = camara
        self.pantalla = pantalla
        self.tipo = tipo_colisiones
        self.space = pymunk.Space()
        self.space.gravity = (0, 900)
        self.space.iterations = 20
        self.color_fondo = (10, 10, 22)
        self.piso_y = PISO_Y

        self.obstaculos = []
        self.pinchos = []  # pygame.Rect en coordenadas del mundo
        self.carteles = []  # (texto, x, y)
        self.checkpoints = []  # dict(x, activo)
        self.sierras = []  # dict con posicion, radio, recorrido y giro (ver _sierra)

        self.inicio = (150, PISO_Y - 25)
        self.limite_caida = PISO_Y + 700

        self._construir()
        self._crear_fondo()

        self.fuente = pygame.font.Font(None, 26)
        self.textos = [
            (self.fuente.render(t, True, (230, 230, 240)), x, y) for t, x, y in self.carteles
        ]

    # ------------------------------------------------------------ construccion
    def _bloque(self, x, y_arriba, ancho, alto, color=COLOR_PISO, tipo="PISO", **kw):
        """Crea un bloque estatico a partir de su esquina superior izquierda."""
        ob = Obstaculo(
            space=self.space,
            posicion=(x + ancho / 2, y_arriba + alto / 2),
            colision_tipo=self.tipo[tipo],
            dimension=(ancho, alto),
            estatico=True,
            color=color,
            friccion=1.0,
            **kw,
        )
        self.obstaculos.append(ob)
        return ob

    def _piso(self, x_ini, x_fin):
        return self._bloque(x_ini, PISO_Y, x_fin - x_ini, 500)

    def _muro_camara(self, x, ancho=70):
        """Muro imposible de saltar: solo se pasa con la Walter Cam (E)."""
        return self._bloque(
            x, PISO_Y - ALTURA_MURO, ancho, ALTURA_MURO, COLOR_MURO_CAMARA, "PARED",
            muro_camara=True,
        )

    def _suelo_camara(self, x, y_arriba, ancho, alto=40):
        """Suelo delgado que solo se atraviesa con la Walter Cam (E) saltando:
        al salir por arriba del recuadro se aparece por debajo del suelo."""
        return self._bloque(
            x, y_arriba, ancho, alto, COLOR_MURO_CAMARA, "PISO", muro_camara=True
        )

    def _plataforma(self, x, y_arriba, ancho, alto=24):
        return self._bloque(x, y_arriba, ancho, alto, COLOR_PLATAFORMA)

    def _pinchos(self, x_ini, x_fin):
        self.pinchos.append(pygame.Rect(x_ini, PISO_Y - 24, x_fin - x_ini, 24))

    def _sierra(self, x, y, radio=40, recorrido=(0, 0), periodo=3.0, giro=10.0):
        """Sierra giratoria que mata al jugador al tocarla.
        (x, y) es su centro en el mundo. Si tiene recorrido va y viene entre
        su posicion inicial y posicion inicial + recorrido (igual que las
        plataformas moviles). giro = velocidad de rotacion en radianes/seg."""
        self.sierras.append(
            {
                "inicio": pygame.Vector2(x, y),
                "recorrido": pygame.Vector2(recorrido),
                "periodo": periodo,
                "radio": radio,
                "giro": giro,
                "pos": pygame.Vector2(x, y),
                "angulo": 0.0,
                "tiempo": 0.0,
            }
        )

    def _caja(self, x, lado=70, masa=4):
        ob = Obstaculo(
            space=self.space,
            posicion=(x, PISO_Y - lado / 2),
            colision_tipo=self.tipo["ENEMIGO"],
            dimension=(lado, lado),
            masa=masa,
            color=COLOR_CAJA,
            friccion=0.8,
        )
        self.obstaculos.append(ob)

    def _plataforma_movil(self, x, y, recorrido, periodo, ancho=170):
        ob = Obstaculo(
            space=self.space,
            posicion=(x + ancho / 2, y + 11),
            colision_tipo=self.tipo["PISO"],
            dimension=(ancho, 22),
            cinematico=True,
            recorrido=recorrido,
            periodo=periodo,
            color=COLOR_MOVIL,
            friccion=1.0,
        )
        self.obstaculos.append(ob)

    def _construir(self):
        # pared invisible del inicio
        self._bloque(-460, PISO_Y - ALTURA_MURO, 60, ALTURA_MURO, (60, 60, 70), "PARED")

        # ---------------- Zona 1: calentamiento
        self._piso(-460, 900)
        self.carteles.append(("A / D: moverse    ESPACIO: saltar", -50, PISO_Y - 200))
        self._bloque(480, PISO_Y - 60, 60, 60)
        self._bloque(700, PISO_Y - 110, 70, 110)
        # sierra fija medio enterrada en el piso entre los dos bloques
        self.carteles.append(("Cuidado con las sierras!", 470, PISO_Y - 230))
        self._sierra(620, PISO_Y, radio=32)
        # hueco 900 - 1100

        # ---------------- Zona 2: plataformas y primer muro de camara
        self._piso(1100, 2600)
        self._plataforma(1250, PISO_Y - 130, 140)
        self._plataforma(1460, PISO_Y - 240, 140)
        # sierra que recorre el piso debajo de las plataformas
        self._sierra(1230, PISO_Y, radio=38, recorrido=(330, 0), periodo=4.0)
        self._bloque(1600, PISO_Y - 90, 100, 90)
        self.carteles.append(("Muro demasiado alto...", 1720, PISO_Y - 300))
        self.carteles.append(("Pegate al muro, presiona E", 1720, PISO_Y - 270))
        self.carteles.append(("y camina hacia ATRAS", 1720, PISO_Y - 240))
        self._muro_camara(2000)
        self.checkpoints.append({"x": 2200, "activo": False})
        self._pinchos(2350, 2550)

        # ---------------- Zona 3: hueco grande con plataforma movil
        # hueco 2600 - 3500
        self.carteles.append(("Sube a la plataforma", 2420, PISO_Y - 220))
        self._plataforma_movil(2615, PISO_Y - 20, recorrido=(700, 0), periodo=5.0)
        self._plataforma(3020, PISO_Y - 260, 90)  # descanso opcional

        # ---------------- Zona 4: muro con pinchos delante
        self._piso(3500, 5700)
        self.checkpoints.append({"x": 3600, "activo": False})
        self.carteles.append(("Acercate lo mas posible", 3640, PISO_Y - 260))
        self.carteles.append(("antes de usar E", 3640, PISO_Y - 230))
        self._pinchos(3860, 3900)
        self._muro_camara(3900, ancho=50)
        self._pinchos(4150, 4330)
        self._plataforma(4180, PISO_Y - 150, 120)

        # ---------------- Zona 5: doble muro
        self.carteles.append(("Dos muros: usa E dos veces", 4420, PISO_Y - 260))
        self.carteles.append(("(E otra vez para apagarla)", 4420, PISO_Y - 230))
        self._muro_camara(4700, ancho=60)
        self._muro_camara(5060, ancho=60)
        self.checkpoints.append({"x": 5250, "activo": False})

        # ---------------- Zona 6: caja para alcanzar la cornisa
        self.carteles.append(("Empuja la caja hasta la cornisa", 5180, PISO_Y - 260))
        self.carteles.append(("R: volver al checkpoint", 5180, PISO_Y - 230))
        self._caja(5420)
        self._bloque(5700, PISO_Y - 340, 420, 840)  # cornisa (no se alcanza saltando)

        # ---------------- Zona 7: recta final
        self._piso(6120, 8700)
        self.checkpoints.append({"x": 6200, "activo": False})
        self._pinchos(6300, 6460)
        # sierra que sube y baja sobre los pinchos: hay que medir el salto
        self._sierra(6380, PISO_Y - 260, radio=34, recorrido=(0, 180), periodo=2.4)
        self._plataforma(6520, PISO_Y - 150, 110)
        self._muro_camara(6760, ancho=80)
        self._pinchos(6960, 7000)

        # ---------------- Zona 8: suelo de camara (Walter Cam hacia abajo)
        # Un muro demasiado grueso para cruzarlo por los lados del recuadro.
        # Debajo del suelo rayado hay un tunel: con la Walter Cam activa,
        # al saltar y salir por ARRIBA del recuadro se aparece ABAJO (en el tunel).
        # El recuadro mide 300 de alto y se centra en el jugador, asi que su
        # borde inferior queda 125 px debajo de los pies: el piso del tunel
        # debe quedar justo dentro de ese limite (ver ALTO_SUELO).
        self.checkpoints.append({"x": 7100, "activo": False})
        self.carteles.append(("Este muro es demasiado grueso...", 6980, PISO_Y - 330))
        self.carteles.append(("Sube al suelo rayado, presiona E", 6980, PISO_Y - 300))
        self.carteles.append(("y SALTA para aparecer abajo", 6980, PISO_Y - 270))
        self._bloque(7260, PISO_Y - ALTO_SUELO, 60, ALTO_SUELO)  # escalon / pared del tunel
        self._suelo_camara(7320, PISO_Y - ALTO_SUELO, 430)
        self._bloque(  # muro grueso que llega hasta el techo del tunel
            7750, PISO_Y - ALTURA_MURO, 300, ALTURA_MURO - ALTO_SUELO + 40, (60, 60, 70), "PARED"
        )
        self.carteles.append(("E: apagar la camara", 7400, PISO_Y - 290))

        self.meta = pygame.Rect(8350, PISO_Y - 170, 60, 170)
        self._bloque(8700, PISO_Y - ALTURA_MURO, 60, ALTURA_MURO + 500, (60, 60, 70), "PARED")

    def _crear_fondo(self):
        rng = random.Random(7)
        self.fondo_capas = []
        for factor, color, alto_max in ((0.15, (18, 18, 36), 380), (0.35, (28, 28, 52), 260)):
            edificios = []
            x = -1500
            while x < 9000:
                ancho = rng.randint(80, 220)
                alto = rng.randint(80, alto_max)
                edificios.append((x, ancho, alto))
                x += ancho + rng.randint(10, 80)
            self.fondo_capas.append((factor, color, edificios))
        self.estrellas = [(rng.randint(0, 9000), rng.randint(0, 400)) for _ in range(160)]

    # ------------------------------------------------------------ logica
    def agregar_a_space(self, *cuerpos):
        for c in cuerpos:
            self.space.add(c)

    def actualizar(self, dt):
        for ob in self.obstaculos:
            ob.actualizar(dt)

        for s in self.sierras:
            s["tiempo"] += dt
            s["angulo"] = (s["angulo"] + s["giro"] * dt) % (2 * math.pi)
            # mismo movimiento suave de ida y vuelta que las plataformas moviles
            fase = (1 - math.cos(2 * math.pi * s["tiempo"] / s["periodo"])) / 2
            s["pos"] = s["inicio"] + s["recorrido"] * fase

    def reiniciar_objetos(self):
        for ob in self.obstaculos:
            ob.reiniciar()
        for s in self.sierras:
            s["tiempo"] = 0.0
            s["pos"] = pygame.Vector2(s["inicio"])

    def toca_pinchos(self, rect_jugador):
        hitbox = rect_jugador.inflate(-10, -6)
        return any(hitbox.colliderect(p.inflate(-8, -6)) for p in self.pinchos)

    def toca_sierras(self, rect_jugador):
        """Colision circulo vs rectangulo: se busca el punto del rectangulo
        mas cercano al centro de la sierra y se mide su distancia."""
        hitbox = rect_jugador.inflate(-8, -8)
        for s in self.sierras:
            cx, cy = s["pos"]
            px = max(hitbox.left, min(cx, hitbox.right))
            py = max(hitbox.top, min(cy, hitbox.bottom))
            radio = s["radio"] * 0.85  # un poco de tolerancia en los dientes
            if (cx - px) ** 2 + (cy - py) ** 2 < radio * radio:
                return True
        return False

    def actualizar_checkpoint(self, x_jugador, en_piso):
        """Devuelve la nueva posicion de reaparicion si se activo un checkpoint."""
        for cp in self.checkpoints:
            if not cp["activo"] and en_piso and x_jugador >= cp["x"]:
                cp["activo"] = True
                return (cp["x"], PISO_Y - 25)
        return None

    # ------------------------------------------------------------ dibujo
    def dibujar(self, ox, oy, tiempo):
        pantalla = self.pantalla
        ancho, alto = pantalla.get_size()
        pantalla.fill(self.color_fondo)

        # estrellas y edificios con parallax para dar sensacion de profundidad
        for sx, sy in self.estrellas:
            x = (sx + ox * 0.05) % ancho
            pygame.draw.circle(pantalla, (70, 70, 110), (x, sy + oy * 0.05), 1)
        for factor, color, edificios in self.fondo_capas:
            base = PISO_Y + oy * factor + (1 - factor) * 120
            for x, w, h in edificios:
                sx = x + ox * factor
                if sx + w < 0 or sx > ancho:
                    continue
                pygame.draw.rect(pantalla, color, (sx, base - h, w, h + alto))

        # las sierras van antes que los bloques para que las del piso
        # se vean medio enterradas
        for s in self.sierras:
            self._dibujar_sierra(pantalla, s, ox, oy, ancho)

        for ob in self.obstaculos:
            ob.dibujar(pantalla, ox, oy)

        for p in self.pinchos:
            r = p.move(ox, oy)
            if r.right < 0 or r.left > ancho:
                continue
            n = max(1, r.width // 20)
            paso = r.width / n
            for i in range(n):
                x0 = r.left + i * paso
                pygame.draw.polygon(
                    pantalla,
                    (230, 230, 240),
                    [(x0, r.bottom), (x0 + paso / 2, r.top), (x0 + paso, r.bottom)],
                )
                pygame.draw.polygon(
                    pantalla,
                    (150, 150, 170),
                    [(x0, r.bottom), (x0 + paso / 2, r.top), (x0 + paso, r.bottom)],
                    1,
                )

        for cp in self.checkpoints:
            x, y = cp["x"] + ox, PISO_Y + oy
            color = (90, 230, 120) if cp["activo"] else (120, 120, 130)
            pygame.draw.line(pantalla, (200, 200, 210), (x, y), (x, y - 80), 4)
            pygame.draw.polygon(pantalla, color, [(x, y - 80), (x + 36, y - 68), (x, y - 56)])

        # meta: bandera a cuadros
        m = self.meta.move(ox, oy)
        pygame.draw.line(pantalla, (230, 230, 230), (m.left, m.bottom), (m.left, m.top), 5)
        ondear = int(tiempo * 6) % 2
        for fila in range(3):
            for col in range(4):
                color = (240, 240, 240) if (fila + col + ondear) % 2 == 0 else (20, 20, 20)
                pygame.draw.rect(pantalla, color, (m.left + 3 + col * 14, m.top + fila * 14, 14, 14))

        for superficie, x, y in self.textos:
            sx = x + ox
            if -superficie.get_width() < sx < ancho:
                pantalla.blit(superficie, (sx, y + oy))

    def _dibujar_sierra(self, pantalla, s, ox, oy, ancho):
        r = s["radio"]
        cx, cy = s["pos"].x + ox, s["pos"].y + oy

        # riel por donde se mueve (solo si tiene recorrido)
        if s["recorrido"].length() > 0:
            a = s["inicio"] + (ox, oy)
            b = a + s["recorrido"]
            pygame.draw.line(pantalla, COLOR_RIEL, a, b, 6)
            pygame.draw.circle(pantalla, COLOR_RIEL, a, 7)
            pygame.draw.circle(pantalla, COLOR_RIEL, b, 7)

        if cx + r < 0 or cx - r > ancho:
            return

        # dientes en forma de serrucho: cada diente sube en diagonal hasta la
        # punta y cae recto, asi se nota hacia donde gira
        dientes = 12
        paso = 2 * math.pi / dientes
        puntos = []
        for i in range(dientes):
            ang = s["angulo"] + i * paso
            puntos.append((cx + math.cos(ang) * r * 0.75, cy + math.sin(ang) * r * 0.75))
            ang_punta = ang + paso * 0.8
            puntos.append((cx + math.cos(ang_punta) * r, cy + math.sin(ang_punta) * r))
        pygame.draw.polygon(pantalla, COLOR_SIERRA, puntos)
        pygame.draw.polygon(pantalla, COLOR_SIERRA_BORDE, puntos, 2)

        # disco interior con agujeros que giran
        pygame.draw.circle(pantalla, (160, 165, 180), (cx, cy), r * 0.58)
        for i in range(3):
            ang = s["angulo"] + i * 2 * math.pi / 3
            hx = cx + math.cos(ang) * r * 0.33
            hy = cy + math.sin(ang) * r * 0.33
            pygame.draw.circle(pantalla, (90, 90, 105), (hx, hy), max(2, r * 0.1))
        pygame.draw.circle(pantalla, (60, 60, 72), (cx, cy), max(3, r * 0.15))
