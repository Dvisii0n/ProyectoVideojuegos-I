import math


class Camara:
    """Camara que sigue al jugador suavemente.

    `posicion` es el desplazamiento que se suma a las coordenadas del mundo
    para obtener coordenadas de pantalla.
    """

    def __init__(self, jugador, ancho=1280, alto=720, piso_y=620):
        self.jugador = jugador
        self.ancho = ancho
        self.alto = alto
        self.piso_y = piso_y
        self.posicion = {"x": 0.0, "y": 0.0}
        # donde queda el jugador en la pantalla (un poco a la izquierda para ver hacia adelante)
        self.ancla = (ancho * 0.42, alto * 0.6)
        self.suavizado_x = 7.0
        self.suavizado_y = 4.0
        self.adelanto = 0.0

    def _objetivo(self):
        if self.jugador.walter_cam:
            # con la Walter Cam activa la camara se queda fija en el recuadro
            px, py = self.jugador.walter_cam_posicion
            adelanto = 0.0
        else:
            px, py = self.jugador.cuerpo.position
            adelanto = self.adelanto

        tx = self.ancla[0] - px - adelanto
        ty = self.ancla[1] - py
        # no mostrar demasiado por debajo del piso
        ty = max(ty, self.alto - (self.piso_y + 100))
        return tx, ty

    def actualizar(self, dt):
        # mira un poco hacia donde camina el jugador
        objetivo_adelanto = 110 * self.jugador.mirando
        self.adelanto += (objetivo_adelanto - self.adelanto) * (1 - math.exp(-2.5 * dt))

        tx, ty = self._objetivo()
        # suavizado exponencial: independiente de los FPS
        self.posicion["x"] += (tx - self.posicion["x"]) * (1 - math.exp(-self.suavizado_x * dt))
        self.posicion["y"] += (ty - self.posicion["y"]) * (1 - math.exp(-self.suavizado_y * dt))

    def centrar(self):
        """Coloca la camara de golpe (al iniciar o reaparecer)."""
        self.adelanto = 110 * self.jugador.mirando
        tx, ty = self._objetivo()
        self.posicion["x"] = tx
        self.posicion["y"] = ty

    def offset(self):
        # redondear una sola vez por cuadro evita temblores entre objetos
        return round(self.posicion["x"]), round(self.posicion["y"])
