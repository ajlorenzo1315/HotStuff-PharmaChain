"""Produce nine conceptual teaching GIFs (not measured simulator traffic)."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent / "static" / "gifs"
ROOT.mkdir(parents=True, exist_ok=True)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def f(sz, b=False):
    return ImageFont.truetype(BOLD if b else FONT, sz)


SCENARIOS = {
    "offline_leader": ("LIDER DESCONECTADO", "El lider no propone", "Timeout y cambio de vista", "Recuperacion posible"),
    "quorum_loss": ("PERDIDA DE QUORUM", "Dos nodos no participan", "Solo 2 votos disponibles", "No se forma QC"),
    "forged_qc": ("QC FALSIFICADO", "Llega evidencia manipulada", "Se comprueba la firma", "Rechazar evidencia falsa"),
    "duplicate_qc": ("QC DUPLICADO", "Se repite un certificado", "Validacion de estructura", "No contar evidencia dos veces"),
    "unsolicited_sync": (
        "SYNC NO SOLICITADO",
        "Respuesta sin solicitud",
        "Comprobar origen esperado",
        "Rechazar respuesta ajena",
    ),
    "valid_sync": ("SYNC LEGITIMO", "Un nodo pide bloques", "Validar cadena y QC", "Actualizar estado"),
    "equivocation": (
        "LIDER EQUIVOCO",
        "Dos propuestas incompatibles",
        "Un voto honesto por vista",
        "Sin doble commit observado",
    ),
    "omit": ("OMISION DE VOTOS", "Un validador no vota", "Comprobar votos restantes", "Con 3 honestos: QC posible"),
    "invalid_signature": ("FIRMA INVALIDA", "Un voto se manipula", "Verificar firma antes de QC", "No contar voto invalido"),
}
XY = [(155, 142), (640, 142), (155, 312), (640, 312)]
for key, (title, *steps) in SCENARIOS.items():
    frames = []
    for i in range(4):
        im = Image.new("RGB", (800, 450), "#081626")
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((15, 15, 785, 435), radius=20, outline="#3b5872", width=2)
        d.text((34, 28), title, font=f(25, True), fill="#a4f0e3")
        d.text((35, 69), "GIF CONCEPTUAL - NO ES UNA TRAZA MEDIDA", font=f(14), fill="#f8cb80")
        for a in range(4):
            for b in range(a + 1, 4):
                d.line((*XY[a], *XY[b]), fill="#25465e", width=3)
        bad = [0] if key == "offline_leader" else [2, 3] if key == "quorum_loss" else [3] if key in ("omit", "invalid_signature") else [0] if key == "equivocation" else []
        active = i % 4
        for n, (x, y) in enumerate(XY):
            fill = "#713746" if n in bad else "#236b68" if n == active else "#18354d"
            d.rounded_rectangle((x - 68, y - 32, x + 68, y + 32), radius=13, fill=fill, outline="#f08a9c" if n in bad else "#6ee5d1", width=3)
            d.text((x - 25, y - 12), f"V{n}", font=f(21, True), fill="white")
        if i > 0:
            a = XY[(i - 1) % 4]
            b = XY[i % 4]
            d.line((*a, *b), fill="#f8cb80", width=7)
            mx = (a[0] + b[0]) // 2
            my = (a[1] + b[1]) // 2
            d.ellipse((mx - 11, my - 11, mx + 11, my + 11), fill="#fff0a4")
        text = "Preparacion del escenario" if i == 0 else steps[i - 1]
        d.rounded_rectangle((55, 355, 745, 418), radius=12, fill="#123048", outline="#4b7a91", width=2)
        d.text((75, 369), f"{i + 1}/4  {text}", font=f(20, True), fill="#e7f9ff")
        frames.append(im)
    frames[0].save(ROOT / f"{key}.gif", save_all=True, append_images=frames[1:], duration=[1000, 1300, 1300, 2200], loop=0, optimize=True)
print("Generated", len(SCENARIOS), "GIFs")
