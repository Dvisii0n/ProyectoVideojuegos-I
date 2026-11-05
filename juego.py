import os
import pygame
from nivelUno import NivelUno
from jugador import Jugador
from camara import Camara


class Juego:
    def __init__(self, ancho=1280, alto=720, fps=60):
        pygame.init()
        pygame.display.set_caption("Walter Cam")
        self.ANCHO = ancho
        self.ALTO = alto
        self.ejecutando = True
        self.reloj = pygame.time.Clock()
        self.FPS = fps
        self.pantalla = pygame.display.set_mode((self.ANCHO, self.ALTO))

        # la fisica avanza en pasos fijos (independiente de los FPS reales)
        self.PASO_FISICA = 1 / 120
        self.SUBPASOS = 2

        self.TIPO_COLISIONES = {"PISO": 1, "JUGADOR": 2, "ENEMIGO": 3, "PARED": 4}

        self.fuente = pygame.font.Font(None, 30)
        self.fuente_grande = pygame.font.Font(None, 80)
        self.sombra = pygame.Surface((self.ANCHO, self.ALTO), pygame.SRCALPHA)
        self.destello = pygame.Surface((self.ANCHO, self.ALTO), pygame.SRCALPHA)

        self.iniciar_musica()
        self.iniciar_nivel()

    def alternar_musica(self):
        self.musica_muteada = not self.musica_muteada
        pygame.mixer.music.set_volume(0.0 if self.musica_muteada else self.VOLUMEN_MUSICA)

    def iniciar_musica(self):
        self.VOLUMEN_MUSICA = 0.5
        self.musica_muteada = False
        # musica de fondo en loop infinito (-1)
        ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Pou Game BGM Morning.mp3")
        try:
            pygame.mixer.music.load(ruta)
            pygame.mixer.music.set_volume(self.VOLUMEN_MUSICA)
            pygame.mixer.music.play(-1)
        except pygame.error as e:
            print(f"No se pudo cargar la musica: {e}")

    def iniciar_nivel(self):
        self.jugador = Jugador(colision_tipo=self.TIPO_COLISIONES["JUGADOR"])

        # cambiar esta propiedad por otro objeto de nivel si se quiere cambiar de nivel
        self.camara = Camara(jugador=self.jugador, ancho=self.ANCHO, alto=self.ALTO)
        self.nivel = NivelUno(
            pantalla=self.pantalla,
            camara=self.camara,
            tipo_colisiones=self.TIPO_COLISIONES,
        )
        self.camara.piso_y = self.nivel.piso_y

        self.jugador.set_posicion_inicial(self.nivel.inicio)
        self.nivel.agregar_a_space(self.jugador.cuerpo, self.jugador.forma)
        self.punto_reaparicion = self.nivel.inicio
        self.camara.centrar()

        self.acumulador = 0.0
        self.tiempo = 0.0
        self.muertes = 0
        self.completado = False
        self.tiempo_destello = 0.0

    # ------------------------------------------------------------ entrada
    def manejar_eventos(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.ejecutando = False

            # teclas que se presionan una sola vez
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.ejecutando = False
                if event.key == pygame.K_m:
                    self.alternar_musica()
                if self.completado:
                    if event.key in (pygame.K_r, pygame.K_RETURN):
                        self.iniciar_nivel()
                    continue
                if event.key == pygame.K_e:
                    self.jugador.activar_walter_cam()
                if event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                    self.jugador.pedir_salto()
                if event.key == pygame.K_r:
                    self.reaparecer(contar_muerte=False)

            if event.type == pygame.KEYUP:
                if event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                    self.jugador.soltar_salto()

    def direccion_input(self):
        if self.completado:
            return 0
        teclas = pygame.key.get_pressed()
        der = teclas[pygame.K_d] or teclas[pygame.K_RIGHT]
        izq = teclas[pygame.K_a] or teclas[pygame.K_LEFT]
        return int(der) - int(izq)

    # ------------------------------------------------------------ logica
    def reaparecer(self, contar_muerte=True):
        if contar_muerte:
            self.muertes += 1
            self.tiempo_destello = 0.35
        self.jugador.reaparecer(self.punto_reaparicion)
        self.nivel.reiniciar_objetos()
        self.camara.centrar()

    def paso_fisica(self, dt, direccion):
        self.jugador.actualizar(dt, direccion)
        self.nivel.actualizar(dt)

        for _ in range(self.SUBPASOS):
            self.nivel.space.step(dt / self.SUBPASOS)

        self.jugador.detectar_piso()
        self.jugador.aplicar_walter_cam(self.nivel.space)

        if self.completado:
            return

        x, y = self.jugador.cuerpo.position
        w, h = self.jugador.dimension
        rect = pygame.Rect(0, 0, w, h)
        rect.center = (round(x), round(y))

        if (
            self.nivel.toca_pinchos(rect)
            or self.nivel.toca_sierras(rect)
            or y > self.nivel.limite_caida
        ):
            self.reaparecer()
            return

        nuevo = self.nivel.actualizar_checkpoint(x, self.jugador.en_piso)
        if nuevo:
            self.punto_reaparicion = nuevo

        # basta con cruzar la bandera (aunque sea saltando por encima)
        if rect.right >= self.nivel.meta.centerx:
            self.completado = True
            self.jugador.walter_cam = False

    # ------------------------------------------------------------ dibujo
    def texto(self, texto, pos, fuente=None, color=(240, 240, 240), centro=False):
        fuente = fuente or self.fuente
        sup = fuente.render(texto, True, color)
        r = sup.get_rect()
        if centro:
            r.center = pos
        else:
            r.topleft = pos
        self.pantalla.blit(sup, r)

    def renderizar(self):
        ox, oy = self.camara.offset()
        self.nivel.dibujar(ox, oy, self.tiempo)
        self.jugador.dibujar_walter_cam(self.pantalla, ox, oy, self.sombra, self.tiempo)
        self.jugador.dibujar(self.pantalla, ox, oy)

        # HUD
        minutos, segundos = divmod(self.tiempo, 60)
        self.texto(f"Tiempo {int(minutos):02d}:{segundos:05.2f}", (20, 16))
        self.texto(f"Caidas {self.muertes}", (20, 44))
        estado = "ON" if self.jugador.walter_cam else "OFF"
        color = (255, 90, 90) if self.jugador.walter_cam else (180, 180, 190)
        self.texto(f"[E] Walter Cam: {estado}", (self.ANCHO - 260, 16), color=color)
        self.texto("[R] Checkpoint   [ESC] Salir", (self.ANCHO - 300, 44), color=(150, 150, 160))
        musica = "OFF" if self.musica_muteada else "ON"
        self.texto(f"[M] Musica: {musica}", (self.ANCHO - 260, 72), color=(150, 150, 160))
        if self.jugador.walter_cam:
            self.texto(
                "Sal por cualquier borde del recuadro para aparecer del lado contrario",
                (self.ANCHO // 2, self.ALTO - 30),
                color=(255, 140, 140),
                centro=True,
            )

        if self.tiempo_destello > 0:
            self.destello.fill((255, 255, 255, int(200 * self.tiempo_destello / 0.35)))
            self.pantalla.blit(self.destello, (0, 0))

        if self.completado:
            self.sombra.fill((0, 0, 0, 170))
            self.pantalla.blit(self.sombra, (0, 0))
            cx, cy = self.ANCHO // 2, self.ALTO // 2
            self.texto("NIVEL COMPLETADO", (cx, cy - 60), self.fuente_grande, (120, 240, 140), True)
            self.texto(
                f"Tiempo {int(minutos):02d}:{segundos:05.2f}   Caidas {self.muertes}",
                (cx, cy + 10),
                centro=True,
            )
            self.texto("R / ENTER: jugar otra vez    ESC: salir", (cx, cy + 50), centro=True)

    # ------------------------------------------------------------ bucle
    def ejecutar(self):
        while self.ejecutando:
            dt = min(self.reloj.tick(self.FPS) / 1000, 0.1)
            self.manejar_eventos()
            if not self.ejecutando:
                break

            direccion = self.direccion_input()
            self.acumulador += dt
            while self.acumulador >= self.PASO_FISICA:
                self.paso_fisica(self.PASO_FISICA, direccion)
                self.acumulador -= self.PASO_FISICA

            if not self.completado:
                self.tiempo += dt
            self.tiempo_destello = max(0.0, self.tiempo_destello - dt)
            self.camara.actualizar(dt)

            self.renderizar()
            pygame.display.flip()

        pygame.quit()


if __name__ == "__main__":
    juego = Juego()
    juego.ejecutar()
