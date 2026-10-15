import pymunk


class NivelUno:
    def __init__(self, pantalla):
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
        self.color_fondo = (0, 0, 0)

        self.space.add(self.piso)

    def dibujar(self):
        self.pantalla.fill(self.color_fondo)
        self.space.debug_draw(self.draw_options)
