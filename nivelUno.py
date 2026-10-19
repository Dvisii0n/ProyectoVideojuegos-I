import pymunk
from obstaculo import Obstaculo


class NivelUno:
    def __init__(self, pantalla, camara, piso_colision_tipo):
        self.camara = camara
        self.space = pymunk.Space()
        self.space.gravity = (0, 900)
        self.pantalla = pantalla
        self.draw_options = pymunk.pygame_util.DrawOptions(self.pantalla)
        self.piso = pymunk.Segment(
            self.space.static_body,
            (0, self.pantalla.height),
            (self.pantalla.width, self.pantalla.height),
            100,
        )
        self.piso.color = (138, 138, 138, 255)
        self.piso.elasticity = 0
        self.piso.friction = 0
        self.color_fondo = (0, 0, 0)
        self.piso.collision_type = piso_colision_tipo

        self.space.add(self.piso)

        
        self.obstaculos = [
            Obstaculo(
                space=self.space,
                posicion=(
                    self.pantalla.width // 2 + 400,
                    self.pantalla.height - 100 - 50,
                ),
                colision_tipo=piso_colision_tipo,
                dimension=(100, 100),
            )
        ]

    def agregar_a_space(self, *cuerpos):
        for c in cuerpos:
            self.space.add(c)

    def dibujar(self):
        self.pantalla.fill(self.color_fondo)
        self.draw_options.transform = pymunk.Transform.translation(
            self.camara.posicion["x"], self.camara.posicion["y"]
        )
        self.space.debug_draw(self.draw_options)
        for obstaculo in self.obstaculos:
            obstaculo.dibujar(self.pantalla, self.camara)