import math

import pygame
import pymunk


def _ajustar_color(color, delta):
    return tuple(max(0, min(255, c + delta)) for c in color[:3])


class Obstaculo:
    """Bloque rectangular del nivel.

    - estatico=True   -> piso, paredes, plataformas fijas.
    - cinematico=True -> plataforma movil (se mueve entre su posicion inicial
                         y posicion inicial + recorrido, con movimiento suave).
    - ninguno         -> objeto dinamico que se puede empujar (sin rotacion).
    """

    def __init__(
        self,
        space,
        posicion,
        colision_tipo,
        estatico=False,
        dimension=(100, 100),
        masa=10,
        color=(200, 80, 60),
        friccion=0.0,
        cinematico=False,
        recorrido=(0, 0),
        periodo=4.0,
        muro_camara=False,
    ):
        self.dimension = dimension
        self.color = color
        self.posicion_inicial = pymunk.Vec2d(*posicion)
        self.cinematico = cinematico
        self.estatico = estatico and not cinematico
        self.recorrido = pymunk.Vec2d(*recorrido)
        self.periodo = periodo
        self.tiempo = 0.0
        # los muros de camara se dibujan distinto para que el jugador sepa
        # que debe usar la Walter Cam (tecla E) para pasarlos
        self.muro_camara = muro_camara

        if cinematico:
            self.cuerpo = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        elif estatico:
            self.cuerpo = pymunk.Body(body_type=pymunk.Body.STATIC)
        else:
            self.masa = masa
            # momento infinito = no rota, se comporta como una caja estable
            self.cuerpo = pymunk.Body(masa, float("inf"))

        self.cuerpo.position = posicion

        self.forma = pymunk.Poly.create_box(self.cuerpo, self.dimension)
        self.forma.elasticity = 0
        self.forma.friction = friccion
        self.forma.collision_type = colision_tipo

        space.add(self.cuerpo, self.forma)

    def actualizar(self, dt):
        """Mueve las plataformas moviles. Se fija la velocidad (en lugar de la
        posicion) para que la fisica arrastre al jugador de forma suave."""
        if not self.cinematico or dt <= 0:
            return
        self.tiempo += dt
        fase = (1 - math.cos(2 * math.pi * self.tiempo / self.periodo)) / 2
        objetivo = self.posicion_inicial + self.recorrido * fase
        self.cuerpo.velocity = (objetivo - self.cuerpo.position) / dt

    def reiniciar(self):
        if self.estatico:
            return
        self.tiempo = 0.0
        self.cuerpo.position = self.posicion_inicial
        self.cuerpo.velocity = (0, 0)

    def rect_mundo(self):
        bb = self.forma.bb
        return pygame.Rect(
            round(bb.left), round(bb.bottom), round(bb.right - bb.left), round(bb.top - bb.bottom)
        )

    def dibujar(self, pantalla, ox, oy):
        rect = self.rect_mundo().move(ox, oy)
        if not rect.colliderect(pantalla.get_rect()):
            return

        pygame.draw.rect(pantalla, self.color, rect)

        if self.muro_camara:
            # franjas diagonales para distinguir los muros de la Walter Cam
            franja = _ajustar_color(self.color, 25)
            visible = rect.clip(pantalla.get_rect())
            pantalla.set_clip(visible)
            inicio = visible.top - (visible.top - rect.top) % 40 - rect.width
            for y in range(inicio, visible.bottom + 40, 40):
                pygame.draw.line(
                    pantalla, franja, (rect.left, y), (rect.right, y + rect.width), 6
                )
            pantalla.set_clip(None)
            pygame.draw.rect(pantalla, (255, 70, 70), rect, 2)
        else:
            # borde superior claro para dar volumen
            pygame.draw.rect(
                pantalla, _ajustar_color(self.color, 40), (rect.x, rect.y, rect.w, 5)
            )
            pygame.draw.rect(pantalla, _ajustar_color(self.color, -40), rect, 2)
