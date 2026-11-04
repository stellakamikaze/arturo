import os, re, sys, html
sys.path.insert(0, os.path.dirname(__file__))
from base import pagina, testo_puro
from pagine import PAGINE
RADICE = "/Users/federico/Documents/ClaudeCode/arturo-landing/sito"
for p in PAGINE:
    assert len(p["desc"]) <= 155, (p["slug"], len(p["desc"]))
    out = pagina(p)
    cartella = os.path.join(RADICE, p["slug"])
    os.makedirs(cartella, exist_ok=True)
    with open(os.path.join(cartella, "index.html"), "w", encoding="utf-8") as f:
        f.write(out)
    m = re.search(r'<main id="contenuto">(.*)</main>', out, re.S).group(1)
    m = re.sub(r'<section class="sezione vuoto chiusura".*?</section>', '', m, flags=re.S)
    parole = len(testo_puro(m).split())
    print(f'{p["slug"]:32} desc={len(p["desc"]):3} parole_main={parole}')
