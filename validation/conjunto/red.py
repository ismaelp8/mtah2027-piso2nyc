"""El modelo conjunto en torch: las entradas por jugador y la red (docs/decisiones.md, 17/11).

No se ejecuta solo. Lo usa `entrenar.py`, en el entorno `mtah2027-conjunto` (torch con CUDA). No importa nada del
pipeline: trabaja con los arrays crudos de `exportar.py`.

Todo lo que calcula se puede repetir en numpy bit a bit: las entradas usan sumas, productos, divisiones, raíces,
máximos y comparaciones, y la red solo tiene ReLU. La predicción en numpy se escribe solo si un candidato pasa los
puntos 1 y 3 de su regla.
"""

import torch
import torch.nn as nn

GRUPO = 5  # frames por grupo (5 Hz)
PASO_VEL = 2  # frames: la velocidad es la diferencia entre t+2 y t−2
VEL_MAX = 12.0  # m/s: por encima es un cambio de slot (aprendida.VEL_MAX)
VEL_BALON_MAX = 40.0  # m/s: tope de la velocidad del balón
N_SLOT = 14  # entradas por jugador y grupo
N_IMPAR, N_PAR = 4, 3  # entradas por grupo que cambian de signo, o no, al cambiar los equipos
RADIOS2 = (1.0, 6.25, 36.0)  # m²: 1, 2,5 y 6 m, los radios de B1 (aprendida.SIGMAS)
TOPE = 15.0  # m: tope de la distancia al balón (aprendida.TOPE)


def entradas(px, py, bx, by, signo, direccion, largo, ancho, fps=25.0):
    """Las entradas a 5 Hz de un lote de trozos.

    px, py      (B, T + 4, S): slots en metros, con NaN donde faltan. T es múltiplo de 5; los 2 frames de más a cada
                lado son solo para la velocidad (NaN si caen fuera del tramo).
    bx, by      (B, T + 4): balón en metros, con NaN donde no se ve.
    signo       (B, S): +1 si el slot ataca hacia x creciente, −1 si hacia x decreciente, 0 si la columna está vacía.
    direccion   (B,): +1 si el local ataca hacia x creciente, −1 si no.
    largo, ancho (B,): el campo, en metros.

    Devuelve (por_slot (B, G, S, 14), hay (B, G, S) bool, impares (B, G, 4), pares (B, G, 3)).
    """
    p = PASO_VEL
    presente_t = torch.isfinite(px) & torch.isfinite(py)
    x_t, y_t = torch.nan_to_num(px), torch.nan_to_num(py)
    visible_t = torch.isfinite(bx) & torch.isfinite(by)
    bx_t, by_t = torch.nan_to_num(bx), torch.nan_to_num(by)
    centro = slice(p, -p)
    presente, visible = presente_t[:, centro], visible_t[:, centro]
    x, y, bxc, byc = x_t[:, centro], y_t[:, centro], bx_t[:, centro], by_t[:, centro]
    k = fps / (2.0 * p)

    vx, vy = (x_t[:, 2 * p:] - x_t[:, :-2 * p]) * k, (y_t[:, 2 * p:] - y_t[:, :-2 * p]) * k
    v_ok = presente_t[:, 2 * p:] & presente_t[:, :-2 * p] & presente & (vx * vx + vy * vy <= VEL_MAX * VEL_MAX)
    vx, vy = torch.where(v_ok, vx, 0.0), torch.where(v_ok, vy, 0.0)
    vbx, vby = (bx_t[:, 2 * p:] - bx_t[:, :-2 * p]) * k, (by_t[:, 2 * p:] - by_t[:, :-2 * p]) * k
    b_ok = visible_t[:, 2 * p:] & visible_t[:, :-2 * p] & visible
    rapidez = torch.sqrt(vbx * vbx + vby * vby)
    escala = torch.where(rapidez > VEL_BALON_MAX, VEL_BALON_MAX / rapidez.clamp(min=1.0), 1.0)
    vbx, vby = torch.where(b_ok, vbx * escala, 0.0), torch.where(b_ok, vby * escala, 0.0)
    rapidez = torch.where(b_ok, torch.clamp(rapidez, max=VEL_BALON_MAX), 0.0)

    o = signo[:, None, :]
    medio_l, medio_a = (largo / 2.0)[:, None, None], (ancho / 2.0)[:, None, None]
    dx, dy = x - bxc[:, :, None], y - byc[:, :, None]
    con_balon = presente & visible[:, :, None]
    d2 = dx * dx + dy * dy
    d = torch.sqrt(d2)
    rvx, rvy = vx - vbx[:, :, None], vy - vby[:, :, None]
    rel_ok = con_balon & v_ok & b_ok[:, :, None]
    cero = torch.zeros((), dtype=px.dtype, device=px.device)
    por_slot = torch.stack([
        torch.where(con_balon, torch.clamp(o * dx / 10.0, -6.0, 6.0), cero),
        torch.where(con_balon, torch.clamp(o * dy / 10.0, -6.0, 6.0), cero),
        torch.where(con_balon, 1.0 / (1.0 + d2 / RADIOS2[0]), cero),
        torch.where(con_balon, 1.0 / (1.0 + d2 / RADIOS2[1]), cero),
        torch.where(con_balon, 1.0 / (1.0 + d2 / RADIOS2[2]), cero),
        torch.where(con_balon, torch.clamp(d, max=TOPE) / TOPE, cero + 1.0),
        o * vx / 5.0,
        o * vy / 5.0,
        torch.where(rel_ok, o * rvx / 5.0, cero),
        torch.where(rel_ok, o * rvy / 5.0, cero),
        o * (x - medio_l) / medio_l,
        o * (y - medio_a) / medio_a,
        torch.where(rel_ok, torch.clamp(-(dx * rvx + dy * rvy) / torch.clamp(d, min=0.5) / 5.0, -4.0, 4.0), cero),
    ], dim=-1) * presente[..., None]

    lote, frames, slots = presente.shape
    grupos = frames // GRUPO
    cuenta = presente.view(lote, grupos, GRUPO, slots).sum(2)
    media = por_slot.view(lote, grupos, GRUPO, slots, -1).sum(2) / cuenta.clamp(min=1)[..., None]
    por_slot = torch.cat([media, (cuenta / float(GRUPO))[..., None]], dim=-1)

    sentido = direccion[:, None]
    ml, ma = (largo / 2.0)[:, None], (ancho / 2.0)[:, None]
    impares = torch.stack([
        torch.where(visible, sentido * (bxc - ml) / ml, cero),
        sentido * vbx / 10.0,
        torch.where(visible, sentido * (byc - ma) / ma, cero),
        sentido * vby / 10.0,
    ], dim=-1).view(lote, grupos, GRUPO, N_IMPAR).mean(2)
    pares = torch.stack([
        visible.to(px.dtype),
        rapidez / 10.0,
        torch.where(visible, torch.abs(byc - ma) / ma, cero),
    ], dim=-1).view(lote, grupos, GRUPO, N_PAR).mean(2)
    return por_slot, cuenta > 0, impares, pares


class Conjunto(nn.Module):
    """Red por jugador (compartida), suma y máximo por equipo, y convolucional temporal residual. Solo ReLU.

    Salidas por grupo: z (`H` frente a `A`, impar), el logit de cambio hacia `H` y hacia `A` (se intercambian al
    cambiar los equipos) y el logit auxiliar del flag (impar).
    """

    def __init__(self, oculto=32, canales=40, dilaciones=(1, 2, 4, 8, 16, 32), abandono=0.1):
        super().__init__()
        self.config = {"oculto": oculto, "canales": canales, "dilaciones": list(dilaciones), "abandono": abandono}
        self.jugador = nn.Sequential(nn.Linear(N_SLOT, oculto), nn.ReLU(), nn.Linear(oculto, oculto), nn.ReLU())
        equipo = 2 * oculto + 1
        self.entrada = nn.Conv1d(2 * equipo + N_IMPAR + N_PAR, canales, 1)
        self.bloques = nn.ModuleList([nn.Conv1d(canales, canales, 3, padding=d, dilation=d) for d in dilaciones])
        self.abandono = nn.Dropout(abandono)
        self.salida = nn.Conv1d(canales, 4, 1)

    def equipos(self, por_slot, hay, team):
        """(u_local, u_visitante): por equipo, la suma (entre 11) y el máximo de sus jugadores, y cuántos hay."""
        h = self.jugador(por_slot)
        salida = []
        for equipo in (0, 1):
            mio = (hay & (team[:, None, :] == equipo)).to(h.dtype)
            hm = h * mio[..., None]  # h ≥ 0 tras la ReLU: el máximo de lo enmascarado es el de los presentes, o 0
            salida.append(torch.cat([hm.sum(2) / 11.0, hm.max(2).values, mio.sum(2, keepdim=True) / 11.0], dim=-1))
        return salida

    def g(self, u_a, u_b, impares, pares):
        h = self.entrada(torch.cat([u_a, u_b, impares, pares], dim=-1).transpose(1, 2))
        for bloque in self.bloques:
            h = h + self.abandono(bloque(torch.relu(h)))
        return self.salida(torch.relu(h))

    def forward(self, por_slot, hay, team, impares, pares):
        u_h, u_a = self.equipos(por_slot, hay, team)
        directa = self.g(u_h, u_a, impares, pares)
        cambiada = self.g(u_a, u_h, -impares, pares)
        z = 0.5 * (directa[:, 0] - cambiada[:, 0])
        par = 0.5 * (directa[:, 1] + cambiada[:, 1])
        impar = 0.5 * (directa[:, 2] - cambiada[:, 2])
        flag = 0.5 * (directa[:, 3] - cambiada[:, 3])
        return z, par + impar, par - impar, flag
