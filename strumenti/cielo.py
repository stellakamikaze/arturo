"""Genera il reticolo della volta celeste con Boote e l'arco dell'Orsa, come SVG.
Uso: python3 cielo.py W H R CX CY RA0 DEC0 > out.svg (gradi per RA0 e DEC0).
La landing del 15/10/2026 usa: 1600 1000 700 1452 223 210 50. Nella home lo SVG è in linea
(senza la scritta ORSA MAGGIORE), in sito/img/volta.svg è senza scritte e con lo stile dentro."""
import math, sys

W, H, R, CX, CY, RA0, DEC0 = (float(x) for x in sys.argv[1:8])
ID = sys.argv[8] if len(sys.argv) > 8 else "cielo"

def vec(ra, dec):
    a, d = math.radians(ra), math.radians(dec)
    return (math.cos(d)*math.cos(a), math.cos(d)*math.sin(a), math.sin(d))

def dot(p, q): return sum(x*y for x, y in zip(p, q))

f = vec(RA0, DEC0)
a0 = math.radians(RA0)
e = (-math.sin(a0), math.cos(a0), 0.0)                 # est al centro
u = (f[1]*e[2]-f[2]*e[1], f[2]*e[0]-f[0]*e[2], f[0]*e[1]-f[1]*e[0])  # nord = f x e

def proj(p):
    z = dot(p, f)
    if z <= 0.12: return None
    x, y = CX - R*dot(p, e)/z, CY - R*dot(p, u)/z
    if not (-900 < x < W+900 and -900 < y < H+900): return None
    return (x, y)

def polilinea(punti, dritta=False):
    seg, cur = [], []
    for p in punti:
        q = proj(p)
        if q is None:
            if len(cur) > 1: seg.append(cur)
            cur = []
        else:
            cur.append(q)
    if len(cur) > 1: seg.append(cur)
    out = []
    for s in seg:
        dentro = [q for q in s if 0 <= q[0] <= W and 0 <= q[1] <= H]
        if len(dentro) < 2: continue
        if dritta: s = [s[0], s[-1]]           # in gnomonica un cerchio massimo è una retta
        pts = []
        for x, y in s:
            q = (round(x), round(y))
            if not pts or pts[-1] != q: pts.append(q)
        out.append("M" + " L".join(f"{x} {y}" for x, y in pts))
    return out

righe = []
for ra in [x/2 for x in range(0, 720, 15)]:      # meridiani, ogni mezz'ora
    righe += polilinea([vec(ra, d/4) for d in range(-356, 357, 1)], dritta=True)
for dec in range(-80, 90, 5):                    # paralleli
    righe += polilinea([vec(r/2, dec) for r in range(0, 721, 1)])

def slerp(p, q, t):
    om = math.acos(max(-1, min(1, dot(p, q))))
    s = math.sin(om)
    return tuple((math.sin((1-t)*om)*a + math.sin(t*om)*b)/s for a, b in zip(p, q))

STELLE = {  # J2000, gradi
    "arturo": (213.915, 19.182), "izar": (221.247, 27.074), "delta": (228.876, 33.315),
    "nekkar": (225.487, 40.390), "seginus": (218.019, 38.308), "rho": (217.957, 30.371),
    "muphrid": (208.671, 18.398), "zeta": (220.287, 13.728),
    "alkaid": (206.885, 49.313), "mizar": (200.981, 54.925), "alioth": (193.507, 55.960),
    "megrez": (183.856, 57.033), "phecda": (178.458, 53.695), "merak": (165.460, 56.382),
    "dubhe": (165.932, 61.751),
}
BOOTE = [("arturo", "izar"), ("izar", "delta"), ("delta", "nekkar"), ("nekkar", "seginus"),
         ("seginus", "rho"), ("rho", "arturo"), ("arturo", "muphrid"), ("arturo", "zeta")]
ORSA = [("dubhe", "merak"), ("merak", "phecda"), ("phecda", "megrez"), ("megrez", "dubhe"),
        ("megrez", "alioth"), ("alioth", "mizar"), ("mizar", "alkaid")]

def linea(a, b):
    p, q = vec(*STELLE[a]), vec(*STELLE[b])
    return polilinea([slerp(p, q, t/20) for t in range(21)])

boote = sum((linea(a, b) for a, b in BOOTE), [])
orsa = sum((linea(a, b) for a, b in ORSA), [])
arco = linea("alkaid", "arturo")
pt = {k: proj(vec(*v)) for k, v in STELLE.items()}

o = [f'<svg class="volta" viewBox="0 0 {W:.0f} {H:.0f}" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">']
o.append(f'<path class="volta__griglia" d="{" ".join(righe)}"/>')
o.append(f'<path class="volta__orsa" d="{" ".join(orsa)}"/>')
o.append(f'<path class="volta__arco" d="{" ".join(arco)}"/>')
o.append(f'<path class="volta__boote" d="{" ".join(boote)}"/>')
for k, q in pt.items():
    if q is None or k == "arturo": continue
    o.append(f'<circle class="volta__stella" cx="{q[0]:.1f}" cy="{q[1]:.1f}" r="2.6"/>')
a = pt["arturo"]
o.append(f'<circle class="volta__alone" cx="{a[0]:.1f}" cy="{a[1]:.1f}" r="15"/>')
o.append(f'<circle class="volta__arturo" cx="{a[0]:.1f}" cy="{a[1]:.1f}" r="6"/>')
o.append(f'<text class="volta__nome" x="{a[0]+16:.1f}" y="{a[1]+30:.1f}">ARTURO</text>')
b = pt["nekkar"]
if b: o.append(f'<text class="volta__nome volta__nome--quieto" x="{b[0]+12:.1f}" y="{b[1]-10:.1f}">BOOTE</text>')
c = pt["megrez"]
if c: o.append(f'<text class="volta__nome volta__nome--quieto" x="{c[0]+12:.1f}" y="{c[1]-12:.1f}">ORSA MAGGIORE</text>')
o.append('</svg>')
print("\n".join(o))
print(f"<!-- arturo {a[0]:.0f},{a[1]:.0f} -->", file=sys.stderr)
