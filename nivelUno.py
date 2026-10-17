import pymunk


class NivelUno:
    def __init__(self, pantalla, piso_colision_tipo):
        self.space = pymunk.Space()
        self.space.gravity = (0, 900)
        self.draw_options = pymunk.pygame_util.DrawOptions(pantalla)
        self.pantalla = pantalla
        self.piso = pymunk.Segment(
            self.space.static_body,
            (0, pantalla.height),
            (pantalla.width, pantalla.height),
            100,
        )
        self.piso.color = (255, 255, 255, 255)
        self.piso.elasticity = 0
        self.piso.friction = 0
        self.color_fondo = (0, 0, 0)
        self.piso.collision_type = piso_colision_tipo

        self.space.add(self.piso)

    def agregar_a_space(self, *cuerpos):
        for c in cuerpos:
            self.space.add(c)

    def dibujar(self):
        self.pantalla.fill(self.color_fondo)
        self.space.debug_draw(self.draw_options)
