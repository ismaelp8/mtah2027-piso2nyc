"""K8: la pérdida por secuencia, un CRF lineal de dos estados (`H` y `A`) con la energía del decodificador.

No se ejecuta solo. Lo usa `entrenar_k8.py` (torch). La comprobación contra la enumeración de todos los caminos está en
`comprobar_k8.py crf`.

**La energía** de un camino y (docs/decisiones.md, 17/11, K8): por cada grupo vivo, +w·z/2 si dice `H` y −w·z/2 si
dice `A` (la diferencia, w·z, es la del decodificador: −α|z| al equipo que pierde, por frame, y 5 frames por grupo,
así que w = 5·α); y −c por cada cambio entre dos grupos vivos seguidos (el coste de cambio de `main`). En un grupo
que no está vivo (`D`, `X` o fuera del centro del trozo) la cadena se corta sin coste, como un `H → D → A` del
decodificador, que cuesta lo mismo que `H → D → H`.

La pérdida es −log p(camino de la etiqueta) = log Z − energía del camino de la etiqueta, sumada sobre el lote y
dividida por los grupos vivos. En un grupo vivo aislado es la entropía cruzada de σ(w·z).
"""

import torch


def nll(z, gt, vivo, w, c):
    """(suma de −log p del camino de la etiqueta, grupos vivos).

    z     (B, G) el logit de `H` frente a `A`, por grupo.
    gt    (B, G) la etiqueta por grupo: 0 `H`, 1 `A` (lo demás solo cuenta si `vivo` lo dice, y no debería).
    vivo  (B, G) bool: los grupos que entran en la cadena.
    """
    lote, grupos = z.shape
    e = torch.stack((0.5 * w * z, -0.5 * w * z), dim=-1)  # (B, G, 2): la emisión de H y de A
    coste = torch.tensor([[0.0, -c], [-c, 0.0]], dtype=z.dtype, device=z.device)  # (de, a)
    cero = torch.zeros(lote, dtype=z.dtype, device=z.device)
    a = torch.zeros(lote, 2, dtype=z.dtype, device=z.device)
    k = cero  # log Z de los tramos ya cerrados
    antes = torch.zeros(lote, dtype=torch.bool, device=z.device)
    for t in range(grupos):
        ahora = vivo[:, t]
        seguir = torch.logsumexp(a[:, :, None] + coste[None], dim=1)  # (B, 2)
        nuevo = e[:, t] + torch.where(antes[:, None], seguir, k[:, None])
        cerrar = antes & ~ahora
        k = torch.where(cerrar, torch.logsumexp(a, dim=1), k)
        a = torch.where(ahora[:, None], nuevo, a)
        antes = ahora
    log_z = torch.where(antes, torch.logsumexp(a, dim=1), k)

    y = gt.clamp(0, 1)
    emision = torch.where(y == 0, e[..., 0], e[..., 1])
    oro = (emision * vivo).sum(1)
    seguidos = vivo[:, 1:] & vivo[:, :-1]
    oro = oro - c * (seguidos & (y[:, 1:] != y[:, :-1])).to(z.dtype).sum(1)
    return (log_z - oro).sum(), int(vivo.sum())
