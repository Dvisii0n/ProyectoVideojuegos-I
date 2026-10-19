import pygame
import pymunk


class Obstaculo:
    def __init__(
        self,
        space,
        posicion,
        colision_tipo,
        dimension=(100, 100),
        color=(200, 80, 60),
    ):
        self.dimension = dimension
        self.color = color

        
        self.cuerpo = pymunk.Body(body_type=pymunk.Body.STATIC)
        self.cuerpo.position = posicion

        self.forma = pymunk.Poly.create_box(self.cuerpo, self.dimension)
        self.forma.elasticity = 0
        self.forma.friction = 0
        
        self.forma.collision_type = colision_tipo

        space.add(self.cuerpo, self.forma)

    def dibujar(self, pantalla, camara):
        
        puntos = []
        for v in self.forma.get_vertices():
            mundo = self.cuerpo.local_to_world(v)
            puntos.append(
                (mundo.x + camara.posicion["x"], mundo.y + camara.posicion["y"])
            )
        pygame.draw.polygon(pantalla, self.color, puntos)