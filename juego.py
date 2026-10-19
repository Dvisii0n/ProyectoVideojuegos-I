import pygame
import pymunk
import pymunk.pygame_util
from nivelUno import NivelUno
from jugador import Jugador
from camara import Camara

#si usas IA eres joto


class Juego:
    def __init__(self, ancho=1280, alto=720, fps=60):
        pygame.init()
        self.ANCHO = ancho
        self.ALTO = alto
        self.ejecutando = True
        self.reloj = pygame.time.Clock()
        self.FPS = fps
        self.pantalla = pygame.display.set_mode((self.ANCHO, self.ALTO))

        self.PISO_COLISION = 1
        self.JUGADOR_COLISION = 2

        self.jugador = Jugador(
            colision_tipo=self.JUGADOR_COLISION,
        )

        self.camara = Camara(jugador=self.jugador)

        # cambiar esta propiedad por otro objeto de nivel si se quiere cambiar de nivel
        self.nivel = NivelUno(
            pantalla=self.pantalla,
            camara=self.camara,
            piso_colision_tipo=self.PISO_COLISION,
        )

    def renderizar(self):
        self.nivel.dibujar()

    def manejar_eventos(self):

        self.nivel.space.on_collision(
            self.JUGADOR_COLISION,
            self.PISO_COLISION,
            begin=self.jugador.set_esta_en_piso,
        )

        teclas_presionadas = pygame.key.get_pressed()
        if teclas_presionadas[pygame.K_SPACE] and self.jugador.en_piso:
            self.jugador.saltar()

        if teclas_presionadas[pygame.K_d]:
            self.jugador.mover("DER")
        elif teclas_presionadas[pygame.K_a]:
            self.jugador.mover("IZQ")

        else:
            self.jugador.parar()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.ejecutando = False

    def ejecutar(self):

        jugador_posicion_inicial = (
            self.ANCHO // 2,
            self.ALTO - (self.nivel.piso.radius + 50),
        )
        self.jugador.set_posicion_inicial(jugador_posicion_inicial)
        self.nivel.agregar_a_space(self.jugador.cuerpo, self.jugador.forma)

        while self.ejecutando:
            self.manejar_eventos()
            self.renderizar()

            substeps = 4
            for _ in range(substeps):
                self.nivel.space.step(1 / self.FPS / substeps)

            self.camara.actualizar()
            pygame.display.flip()
            self.reloj.tick(self.FPS)

        pygame.quit()


if __name__ == "__main__":
    juego = Juego()
    juego.ejecutar()
