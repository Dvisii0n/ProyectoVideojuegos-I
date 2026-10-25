# uso exclusivo dentro del metodo dibujar_walter_cam del jugador
def debugWalterCam(self, limites):
    lim_str = ""
    for key, val in limites.items():
        lim_str += f"{key} pos: {val}\n"
    print(
        f"Posicion walter_cam: {self.walter_cam_posicion}\nPosicion jugador: {self.cuerpo.position}\n{lim_str}"
    )
