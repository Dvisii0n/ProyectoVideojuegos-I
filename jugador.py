import pygame
import pymunk
from utils import debugWalterCam


class Jugador:
    def __init__(
        self,
        colision_tipo,
        dimension=(50, 50),
        masa=1,
        posicion_inicial=(0, 0),
        velocidad=500,
        impulso_saltar=700,
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
        self.walter_cam = False
        self.walter_rect = pygame.Rect(0, 0, 400, 300)
        self.walter_cam_posicion = (0, 0)

        self.forma.collision_type = colision_tipo

    def set_posicion_inicial(self, posicion):
        self.posicion_inicial = posicion
        self.cuerpo.position = posicion

    def activar_walter_cam(self):
        self.walter_cam = not self.walter_cam
        if self.walter_cam:
            self.walter_cam_posicion = self.cuerpo.position

    def set_esta_en_piso(self, arbiter, space, data):
        self.en_piso = True

    def bloquear_rotacion(self):
        self.cuerpo.moment = float("inf")
        self.cuerpo.angular_velocity = 0

    def dibujar_walter_cam(self, pantalla, camara):
        # centro de la walter cam y el jugador
        walter_x, walter_y = self.walter_cam_posicion
        jugador_x, jugador_y = self.cuerpo.position
        self.walter_rect.center = (
            round(walter_x + camara.posicion["x"]),
            round(walter_y + camara.posicion["y"]),
        )

        if self.walter_cam:
            # posicionar walter cam de acuerdo al centro del jugador y la camara
            pygame.draw.rect(pantalla, (255, 0, 0), self.walter_rect, width=2)

            diferencia_x = self.walter_rect.width / 2
            limites = {
                "lim_der": walter_x + diferencia_x,
                "lim_izq": walter_x - diferencia_x,
            }
            debugWalterCam(self, limites)
            if jugador_x >= limites["lim_der"]:
                self.cuerpo.position = (walter_x - diferencia_x, jugador_y)
            elif jugador_x <= limites["lim_izq"]:
                self.cuerpo.position = (walter_x + diferencia_x, jugador_y)

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
