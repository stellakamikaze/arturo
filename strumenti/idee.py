#!/usr/bin/env python3
"""Scrive i position paper del sito (/idee/) dai file markdown in strumenti/idee/ (16/11/2026, #4537).

Ogni paper è un passo del racconto della landing. Il primo passo, "Per chi è", è la pagina /mestieri/ (la
scrive strumenti/mestieri.py); gli altri stanno in strumenti/idee/<n>-<slug>.md con un'intestazione
(slug, passo, titolo, sottotitolo, descrizione, prossima facoltativa), poi "---" e il testo. Nel testo:
  ## titolo               un titolo di sezione
  - **Etichetta** — testo un elenco
  {prossima}              l'etichetta "Nella prossima versione"
  {figura:nome}           la figura strumenti/idee/figure/<nome>.html
  Fonti:                  la riga che apre l'elenco delle fonti, in fondo
uso: python3 strumenti/idee.py
"""
import html
import re
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
SORGENTI = RADICE / "strumenti" / "idee"
SITO = RADICE / "sito"
MODELLO = SITO / "organizzazioni" / "index.html"
PRIMO = {"slug": "mestieri", "passo": "1", "titolo": "I mestieri della conoscenza", "url": "../../mestieri/",
         "sottotitolo": "Sei famiglie di mestieri, e per ognuna cosa fa Arturo."}
ETICHETTA = '<span class="in-arrivo">Nella prossima versione</span>'


def inline(t: str) -> str:
    t = html.escape(t, quote=False)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', t)
    return t.replace("{prossima}", ETICHETTA)


def leggi(percorso: Path) -> dict:
    testa, _, corpo = percorso.read_text(encoding="utf-8").partition("\n---\n")
    dati = dict(re.findall(r"(?m)^([a-z]+): (.+)$", testa))
    dati["corpo"] = corpo.strip()
    return dati


def corpo_html(testo: str) -> str:
    fuori, fonti = [], []
    in_fonti = False
    for blocco in re.split(r"\n\s*\n", testo):
        righe = blocco.strip().splitlines()
        if not righe:
            continue
        if righe[0].strip() == "Fonti:":
            in_fonti = True
            righe = righe[1:]
        if in_fonti:
            fonti += [inline(r[2:].strip()) for r in righe if r.startswith("- ")]
            continue
        m = re.fullmatch(r"\{figura:([a-z]+)\}", righe[0].strip())
        if m:
            figura = (SORGENTI / "figure" / f"{m.group(1)}.html").read_text(encoding="utf-8")
            fuori.append(f'<div class="paper__figura">\n{figura}</div>')
        elif righe[0].startswith("## "):
            titolo = righe[0][3:].strip()
            ident = re.sub(r"[^a-z0-9]+", "-", titolo.lower().replace("à", "a").replace("è", "e").replace("é", "e")
                           .replace("ì", "i").replace("ò", "o").replace("ù", "u")).strip("-")
            fuori.append(f'<h2 id="{ident}">{inline(titolo)}</h2>')
            if len(righe) > 1:
                fuori.append(f"<p>{inline(' '.join(righe[1:]))}</p>")
        elif all(r.startswith("- ") for r in righe):
            voci = "".join(f"<li>{inline(r[2:].strip())}</li>" for r in righe)
            fuori.append(f'<ul class="paper__voci">{voci}</ul>')
        else:
            fuori.append(f"<p>{inline(' '.join(r.strip() for r in righe))}</p>")
    if fonti:
        fuori.append('<section class="paper__fonti" aria-labelledby="t-fonti"><h2 id="t-fonti">Fonti</h2><ul>'
                     + "".join(f"<li>{f}</li>" for f in fonti) + "</ul></section>")
    return "\n".join(fuori)


def testa_pagina(titolo: str, descrizione: str, url: str, profondita: int, figure: bool) -> str:
    modello = MODELLO.read_text(encoding="utf-8")
    testa = modello[: modello.index("</style>")]
    vecchio_titolo = re.search(r"<title>(.*?)</title>", testa).group(1)
    vecchia_desc = re.search(r'<meta name="description" content="([^"]*)"', testa).group(1)
    testa = testa.replace(vecchio_titolo, html.escape(titolo, quote=False))
    testa = testa.replace(vecchia_desc, html.escape(descrizione))
    testa = testa.replace("https://arturo.stellakamikaze.org/organizzazioni/", url)
    su = "../" * profondita
    testa = testa.replace('href="../', f'href="{su}').replace("url(../", f"url({su}")
    collegamenti = f'<link rel="stylesheet" href="{su}stile/componenti.css?v=2026-11-16">\n'
    if figure:
        collegamenti += f'<link rel="stylesheet" href="{su}stile/figure.css?v=2026-11-04">\n'
    testa = testa.replace("<style>", collegamenti + "<style>", 1)
    return testa + STILE + "</style>\n"


STILE = """
/* ---------- i position paper ---------- */
.testata__corpo h1{font-weight:250;font-size:clamp(2.4rem, 1.3rem + 4vw, 4.8rem);line-height:.98;letter-spacing:-.025em;font-stretch:114%}
.testata__corpo .paper__sotto{margin:18px 0 0;max-width:40ch;font:300 clamp(1.3rem, 1rem + 1vw, 1.8rem)/1.2 var(--titolo);font-stretch:108%;color:var(--cenere)}
.paper__dove{display:flex;flex-wrap:wrap;gap:8px 20px;margin:24px 0 0;font-size:.95rem;color:var(--grafite)}
.paper__dove a{color:var(--inchiostro)}
.paper{padding:clamp(40px,6vw,80px) 0 clamp(48px,7vw,96px)}
.paper .dentro > *{max-width:68ch}
.paper .dentro > .paper__figura{max-width:none;margin:clamp(28px,4vw,48px) 0}
.paper p{color:var(--grafite)}
.paper h2{margin:clamp(36px,5vw,56px) 0 12px;font-weight:300;font-size:clamp(1.6rem, 1.2rem + 1.4vw, 2.3rem);line-height:1.1;letter-spacing:-.02em;font-stretch:110%}
.paper__voci{margin:0 0 1em;padding:0;list-style:none;border-top:1px solid var(--inchiostro)}
.paper__voci li{padding:12px 0;border-bottom:1px solid var(--filetto);color:var(--grafite)}
.paper__voci strong{color:var(--inchiostro)}
.paper__fonti{margin-top:clamp(40px,6vw,64px);padding-top:20px;border-top:1px solid var(--inchiostro)}
.paper__fonti h2{margin:0 0 12px;font-size:1.3rem;font-weight:400}
.paper__fonti li{padding:6px 0;font-size:.95rem}
.paper .in-arrivo{margin:0 4px 0 0}
.seguito{padding:clamp(36px,5vw,56px) 0;background:var(--carta-2);border-top:1px solid var(--filetto)}
.seguito .dentro{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px var(--fra-lati, 48px)}
.seguito a{display:block;padding:16px 0;border-top:1px solid var(--inchiostro);text-decoration:none;color:var(--inchiostro)}
.seguito a span{display:block;font:600 .85rem/1.3 var(--testo);color:var(--grafite)}
.seguito a strong{display:block;margin-top:4px;font:400 1.3rem/1.2 var(--titolo);letter-spacing:-.02em}
.seguito a:hover strong{text-decoration:underline;text-underline-offset:4px;text-decoration-thickness:1px}
.elenco-paper{margin:0;padding:0;list-style:none;border-top:1px solid var(--inchiostro)}
.elenco-paper a{display:grid;grid-template-columns:3rem minmax(0,1fr);gap:4px 16px;padding:20px 0;border-bottom:1px solid var(--filetto);text-decoration:none;color:var(--inchiostro)}
.elenco-paper b{font:300 1.6rem/1 var(--titolo);color:var(--cenere)}
.elenco-paper strong{font:400 1.4rem/1.2 var(--titolo);letter-spacing:-.02em}
.elenco-paper span{grid-column:2;color:var(--grafite)}
.elenco-paper a:hover strong{text-decoration:underline;text-underline-offset:4px;text-decoration-thickness:1px}
@media (max-width:760px){.seguito .dentro{grid-template-columns:minmax(0,1fr)}}
"""


def corpo_pagina(modello: str, profondita: int, testata: str, principale: str, script: str = "") -> str:
    su = "../" * profondita
    inizio = modello.index('<header class="testata">')
    menu = modello[inizio: modello.index('<div class="dentro">\n    <div class="testata__corpo">')]
    menu = menu.replace('href="../', f'href="{su}').replace('src="../', f'src="{su}')
    piede = modello[modello.index('<footer class="piede">'): modello.index("</footer>") + len("</footer>")]
    piede = piede.replace('href="../', f'href="{su}')
    return (f'<script defer data-domain="arturo.stellakamikaze.org" data-api="/api/e" src="/js/a.js"></script>\n'
            f'<script defer src="{su}traccia.js"></script>\n</head>\n<body>\n<a class="salta" href="#testo">Vai al testo</a>\n'
            f"{menu}<div class=\"dentro\">\n    <div class=\"testata__corpo\">\n{testata}\n    </div>\n  </div>\n</header>\n\n"
            f"<main id=\"testo\">\n{principale}\n</main>\n\n{piede}\n{script}"
            f'<script type="module" src="{su}note.js"></script>\n</body>\n</html>\n')


def main() -> None:
    modello = MODELLO.read_text(encoding="utf-8")
    paper = [leggi(p) for p in sorted(SORGENTI.glob("[0-9]-*.md"))]
    tutti = [PRIMO] + [dict(p, url=f"../{p['slug']}/") for p in paper]
    for i, p in enumerate(paper, start=1):
        prima, dopo = tutti[i - 1], tutti[i + 1] if i + 1 < len(tutti) else None
        figure = "{figura:" in p["corpo"]
        script = '<script defer src="../../js/figura-cassettiera.js"></script>\n' if "{figura:cassettiera}" in p["corpo"] else ""
        url = f"https://arturo.stellakamikaze.org/idee/{p['slug']}/"
        stato = f"\n      <p class=\"paper__dove\">{ETICHETTA}</p>" if p.get("prossima") else ""
        testata = (f'      <h1 id="titolo">{inline(p["titolo"])}</h1>\n      <p class="paper__sotto">{inline(p["sottotitolo"])}</p>{stato}\n'
                   f'      <p class="paper__dove"><span>Passo {p["passo"]} di 7</span><a href="../../#passo-{p["passo"]}">Torna al racconto</a>'
                   f'<a href="../">Tutte le idee</a></p>')
        seguito = ['<nav class="seguito" aria-label="Gli altri paper"><div class="dentro">',
                   f'<a href="{prima["url"] if prima is PRIMO else "../" + prima["slug"] + "/"}"><span>Passo {prima["passo"]}, prima</span><strong>{inline(prima["titolo"])}</strong></a>']
        if dopo:
            seguito.append(f'<a href="../{dopo["slug"]}/"><span>Passo {dopo["passo"]}, dopo</span><strong>{inline(dopo["titolo"])}</strong></a>')
        else:
            seguito.append('<a href="../../installa/"><span>E adesso</span><strong>Installa Arturo</strong></a>')
        seguito.append("</div></nav>")
        principale = (f'<article class="paper" aria-labelledby="titolo"><div class="dentro">\n{corpo_html(p["corpo"])}\n</div></article>\n'
                      + "\n".join(seguito))
        pagina = testa_pagina(f"{p['titolo']} · Arturo", p["descrizione"], url, 2, figure) + corpo_pagina(modello, 2, testata, principale, script)
        uscita = SITO / "idee" / p["slug"] / "index.html"
        uscita.parent.mkdir(parents=True, exist_ok=True)
        uscita.write_text(pagina, encoding="utf-8")
        print(f"scritta {uscita.relative_to(RADICE)}")

    voci = []
    for p in tutti:
        href = "../mestieri/" if p is PRIMO else f"{p['slug']}/"
        voci.append(f'<li><a href="{href}"><b>{p["passo"]}</b><strong>{inline(p["titolo"])}</strong><span>{inline(p["sottotitolo"])}</span></a></li>')
    testata = ('      <h1 id="titolo">Le idee dietro Arturo</h1>\n'
               '      <p class="paper__sotto">Sette paper brevi, uno per passo del racconto.</p>\n'
               '      <p class="paper__dove"><a href="../#racconto">Torna al racconto</a></p>')
    principale = ('<article class="paper" aria-labelledby="titolo"><div class="dentro">\n'
                  '<p>Ogni paper allarga un passo della pagina principale: per chi è Arturo, perché il terminale, di chi è '
                  "il contesto, cos'è un harness, da dove parte, cosa ti propone e come cresce senza rompersi.</p>\n"
                  f'<ol class="elenco-paper">{"".join(voci)}</ol>\n</div></article>')
    pagina = (testa_pagina("Le idee dietro Arturo · sette paper brevi", "Sette paper brevi che allargano il racconto di "
                           "Arturo: mestieri, terminale, strati, harness, storico, proposte, Orsa.",
                           "https://arturo.stellakamikaze.org/idee/", 1, False)
              + corpo_pagina(modello, 1, testata, principale))
    (SITO / "idee" / "index.html").write_text(pagina, encoding="utf-8")
    print("scritta sito/idee/index.html")


if __name__ == "__main__":
    main()
