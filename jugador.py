import pymunk


class Jugador:
    def __init__(
        self,
        colision_tipo,
        dimension=(100, 100),
        masa=1,
        posicion_inicial=(0, 0),
        velocidad=500,
        impulso_saltar=600,
    ):
        self.dimension = dimension
        self.masa = masa
        self.momento = pymunk.moment_for_box(masa, self.dimension)
        self.cuerpo = pymunk.Body(masa, self.momento)
        self.velocidad = velocidad
        self.impulso_saltar = impulso_saltar
        self.posicion_inicial = posicion_inicial
        self.forma = pymunk.Poly.create_box(self.cuerpo, self.dimension)
        self.estado = "IDLE"
        self.en_piso = True

        self.forma.collision_type = colision_tipo

    def set_posicion_inicial(self, posicion):
        self.posicion_inicial = posicion
        self.cuerpo.position = posicion

    def set_esta_en_piso(self, arbiter, space, data):
        self.en_piso = True

    def mover(self, direccion):
        if self.en_piso:
            self.estado = "CAMINANDO"
        match direccion:
            case "DER":
                self.cuerpo.velocity = (self.velocidad, self.cuerpo.velocity.y)
            case "IZQ":
                self.cuerpo.velocity = (-self.velocidad, self.cuerpo.velocity.y)

    def saltar(self):
        self.estado = "SALTANDO"
        self.cuerpo.apply_impulse_at_local_point((0, -self.impulso_saltar))
        self.en_piso = False

    def parar(self):
        self.cuerpo.velocity = (0, self.cuerpo.velocity.y)
        if self.en_piso:
            self.estado = "IDLE"
