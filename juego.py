import pygame
import pymunk
import pymunk.pygame_util
from nivelUno import NivelUno


class Juego:
    def __init__(self, ancho=1280, alto=720, fps=60):
        pygame.init()
        self.ANCHO = ancho
        self.ALTO = alto
        self.ejecutando = True
        self.reloj = pygame.time.Clock()
        self.FPS = fps
        self.pantalla = pygame.display.set_mode((self.ANCHO, self.ALTO))
        # cambiar estar propiedad por otro objeto de nivel si se quiere cambiar de nivel
        self.nivel = NivelUno(self.pantalla)

    def renderizar(self):
        self.nivel.dibujar()

    def manejar_eventos(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.ejecutando = False

    def ejecutar(self):

        while self.ejecutando:
            self.manejar_eventos()
            self.renderizar()

            self.nivel.space.step(1 / self.FPS)
            pygame.display.flip()
            self.reloj.tick(self.FPS)

        pygame.quit()


if __name__ == "__main__":
    juego = Juego()
    juego.ejecutar()
