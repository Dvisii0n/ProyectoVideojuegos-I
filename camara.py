class Camara:
    def __init__(self, jugador):
        self.jugador = jugador
        self.posicion = {"x": 0, "y": 0}

    def actualizar(self):
        self.posicion["x"] = (
            self.jugador.posicion_inicial[0] - self.jugador.cuerpo.position.x
        )
