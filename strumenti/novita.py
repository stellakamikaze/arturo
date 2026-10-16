#!/usr/bin/env python3
"""Scrive sito/novita/index.html dalle voci di NOVITA.md di Arturo.

Ogni voce di NOVITA.md comincia con «## AAAA-MM-GG — Titolo» e diventa un <article> con un'ancora
(data più titolo) e un <time datetime>. Il resto del markdown che NOVITA.md usa (paragrafi, liste,
**grassetto**, *corsivo*, `codice`, link, citazioni, blocchi di codice) diventa HTML semplice ed
escapato. Testata, menu, stile e piede riprendono la pagina per le organizzazioni.

  python3 strumenti/novita.py                       legge ../arturo/NOVITA.md accanto al worktree
  python3 strumenti/novita.py --da PERCORSO         legge un altro NOVITA.md
  git -C ../arturo show origin/main:NOVITA.md | python3 strumenti/novita.py --da -
                                                    legge la versione rilasciata da stdin
  python3 strumenti/novita.py --prova               stampa la pagina senza scrivere

Solo libreria standard, Python 3.8 o successivo.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import unicodedata
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
PAGINA = RADICE / "sito" / "novita" / "index.html"
DEFAULT = RADICE.parent / "arturo" / "NOVITA.md"
SITO = "https://arturo.stellakamikaze.org"
URL = SITO + "/novita/"
REPO = "https://github.com/stellakamikaze/arturo"
MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre",
        "ottobre", "novembre", "dicembre"]
TESTA_VOCE = re.compile(r"^## (\d{4}-\d{2}-\d{2}) — (.+?)\s*$")
VOCE_LISTA = re.compile(r"^(\s*)([-*]|\d+\.)\s+(.*)$")

DESCRIZIONE = ("Le novità di Arturo, l'harness in italiano per Claude Code: cosa cambia a ogni "
               "aggiornamento, il principio dietro e cosa fare tu. La più recente in cima.")


# ---------- markdown in linea ----------

def in_linea(testo: str) -> str:
    """Escapa il testo e converte `codice`, link, **grassetto** e *corsivo*."""
    # Il codice esce per primo e torna alla fine: un ** o un * dentro `...` resta testo.
    codici = []

    def metti_da_parte(m):
        codici.append("<code>" + html.escape(m.group(1), quote=False) + "</code>")
        return "\x00" + str(len(codici) - 1) + "\x00"

    s = re.sub(r"`([^`]+)`", metti_da_parte, testo)
    s = html.escape(s, quote=False)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: _link(m.group(1), m.group(2)), s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)([^*]+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", s)
    return re.sub(r"\x00(\d+)\x00", lambda m: codici[int(m.group(1))], s)


def _link(testo: str, destinazione: str) -> str:
    dest = html.unescape(destinazione)
    if not re.match(r"^(https?:|mailto:|#)", dest):
        dest = REPO + "/blob/main/" + dest.lstrip("./")
    return '<a href="' + html.escape(dest) + '">' + testo + "</a>"


# ---------- blocchi ----------

def blocchi(righe: list) -> str:
    """Converte il corpo di una voce in HTML, riga per riga."""
    fuori = []
    paragrafo = []
    i = 0

    def chiudi_paragrafo():
        if paragrafo:
            fuori.append("<p>" + in_linea(" ".join(r.strip() for r in paragrafo)) + "</p>")
            paragrafo.clear()

    while i < len(righe):
        riga = righe[i]
        nuda = riga.strip()
        if not nuda or re.fullmatch(r"-{3,}|\*{3,}", nuda):
            chiudi_paragrafo()
            i += 1
            continue
        if nuda.startswith("```"):
            chiudi_paragrafo()
            codice = []
            i += 1
            while i < len(righe) and not righe[i].strip().startswith("```"):
                codice.append(righe[i])
                i += 1
            i += 1
            fuori.append("<pre><code>" + html.escape("\n".join(codice), quote=False) + "</code></pre>")
            continue
        titolo = re.match(r"^(#{3,6})\s+(.*)$", nuda)
        if titolo:
            chiudi_paragrafo()
            fuori.append("<h3>" + in_linea(titolo.group(2)) + "</h3>")
            i += 1
            continue
        if nuda.startswith(">"):
            chiudi_paragrafo()
            citazione = []
            while i < len(righe) and righe[i].strip().startswith(">"):
                citazione.append(righe[i].strip()[1:].strip())
                i += 1
            fuori.append("<blockquote><p>" + in_linea(" ".join(citazione)) + "</p></blockquote>")
            continue
        voce = VOCE_LISTA.match(riga)
        if voce and len(voce.group(1)) < 2:
            chiudi_paragrafo()
            ordinata = voce.group(2)[0].isdigit()
            elementi = []
            while i < len(righe):
                m = VOCE_LISTA.match(righe[i])
                if m and len(m.group(1)) < 2:
                    elementi.append([m.group(3)])
                elif righe[i].strip() and righe[i][:1] in (" ", "\t") and elementi:
                    elementi[-1].append(righe[i].strip())
                else:
                    break
                i += 1
            tag = "ol" if ordinata else "ul"
            fuori.append("<" + tag + ">" + "".join(
                "<li>" + in_linea(" ".join(e)) + "</li>" for e in elementi) + "</" + tag + ">")
            continue
        paragrafo.append(riga)
        i += 1
    chiudi_paragrafo()
    return "\n".join(fuori)


def slug(testo: str) -> str:
    s = unicodedata.normalize("NFKD", testo).encode("ascii", "ignore").decode("ascii").lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:60].rstrip("-") or "voce"


def voci(testo: str) -> list:
    """Divide NOVITA.md nelle sue voci, nell'ordine del file (la più recente in cima)."""
    elenco = []
    corrente = None
    for riga in testo.splitlines():
        m = TESTA_VOCE.match(riga)
        if m:
            corrente = {"data": m.group(1), "titolo": m.group(2), "righe": []}
            elenco.append(corrente)
        elif riga.startswith("## "):
            print("Intestazione fuori formato, la salto: " + riga, file=sys.stderr)
            corrente = None
        elif corrente is not None:
            corrente["righe"].append(riga)
    visti = set()
    for v in elenco:
        base = v["data"] + "-" + slug(v["titolo"])
        ancora, n = base, 2
        while ancora in visti:
            ancora, n = base + "-" + str(n), n + 1
        visti.add(ancora)
        v["id"] = ancora
    return elenco


def data_lunga(iso: str) -> str:
    anno, mese, giorno = iso.split("-")
    return str(int(giorno)) + " " + MESI[int(mese) - 1] + " " + anno


def titolo_semplice(titolo: str) -> str:
    """Il titolo senza i segni del markdown, per il JSON-LD."""
    return re.sub(r"\*\*|`|(?<!\w)\*|\*(?!\w)", "", titolo)


# ---------- pagina ----------

def json_ld(elenco: list) -> str:
    dati = {
        "@context": "https://schema.org",
        "@type": "Blog",
        "@id": URL + "#novita",
        "name": "Novità di Arturo",
        "description": DESCRIZIONE,
        "url": URL,
        "inLanguage": "it",
        "publisher": {"@type": "Person", "name": "Federico Nejrotti"},
        "about": {"@type": "SoftwareApplication", "name": "Arturo", "url": SITO + "/"},
        "blogPost": [{
            "@type": "BlogPosting",
            "headline": titolo_semplice(v["titolo"]),
            "datePublished": v["data"],
            "author": {"@type": "Person", "name": "Federico Nejrotti"},
            "url": URL + "#" + v["id"],
            "inLanguage": "it",
        } for v in elenco],
    }
    testo = json.dumps(dati, ensure_ascii=False, indent=1)
    return testo.replace("</", "<\\/")


def articolo(v: dict) -> str:
    return (
        '      <article class="voce" id="' + v["id"] + '" aria-labelledby="t-' + v["id"] + '">\n'
        '        <p class="voce__data stretta"><time datetime="' + v["data"] + '">'
        + data_lunga(v["data"]) + "</time></p>\n"
        '        <div class="voce__corpo">\n'
        '          <h2 id="t-' + v["id"] + '"><a href="#' + v["id"] + '">' + in_linea(v["titolo"]) + "</a></h2>\n"
        + "\n".join("          " + r for r in blocchi(v["righe"]).splitlines()) + "\n"
        "        </div>\n"
        "      </article>"
    )


def pagina(elenco: list) -> str:
    ultima = data_lunga(elenco[0]["data"]) if elenco else ""
    return MODELLO.format(
        descrizione=html.escape(DESCRIZIONE),
        url=URL,
        sito=SITO,
        json_ld=json_ld(elenco),
        ultima=ultima,
        conteggio=len(elenco),
        voci="\n\n".join(articolo(v) for v in elenco),
    )


MODELLO = """<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Novità di Arturo · cosa cambia e perché</title>
<meta name="description" content="{descrizione}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Arturo">
<meta property="og:locale" content="it_IT">
<meta property="og:title" content="Novità di Arturo · cosa cambia e perché">
<meta property="og:description" content="{descrizione}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{sito}/img/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Arturo, la stella sopra il reticolo blu della volta celeste">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Novità di Arturo · cosa cambia e perché">
<meta name="twitter:description" content="{descrizione}">
<meta name="twitter:image" content="{sito}/img/og.png">
<link rel="alternate" type="text/markdown" title="NOVITA.md su GitHub" href="https://github.com/stellakamikaze/arturo/blob/main/NOVITA.md">
<meta name="theme-color" content="#d7ebff">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' fill='%230b0d10'/%3E%3Cpath d='M5 25 13 11l6 8 8-11' fill='none' stroke='%23d7ebff' stroke-width='1.6'/%3E%3Ccircle cx='13' cy='11' r='3.2' fill='%23f2a24a'/%3E%3C/svg%3E">
<link rel="preload" href="../font/archivo.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="../font/atkinson-next.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="../stile/colori.css">
<script type="application/ld+json">
{json_ld}
</script>
<style>
@font-face{{font-family:"Archivo";src:url(../font/archivo.woff2) format("woff2");font-weight:100 900;font-stretch:62% 125%;font-display:swap}}
@font-face{{font-family:"Atkinson Next";src:url(../font/atkinson-next.woff2) format("woff2");font-weight:200 800;font-style:normal;font-display:swap}}
@font-face{{font-family:"Atkinson Mono";src:url(../font/atkinson-mono.woff2) format("woff2");font-weight:200 800;font-display:swap}}

*,*::before,*::after{{box-sizing:border-box}}
html{{-webkit-text-size-adjust:100%;scroll-behavior:smooth;scrollbar-color:#a3abb5 var(--carta)}}
@media (prefers-reduced-motion:reduce){{html{{scroll-behavior:auto}}}}
body{{margin:0;background:var(--carta);color:var(--grafite);font:400 clamp(16.5px, .98rem + .15vw, 18px)/1.55 var(--testo);letter-spacing:-.005em;-webkit-font-smoothing:antialiased}}
::selection{{background:var(--azione);color:#fff}}
:focus-visible{{outline:2px solid var(--azione);outline-offset:3px}}
img,svg{{display:block;max-width:100%}}
a{{color:inherit;text-underline-offset:.2em;text-decoration-thickness:1px}}
p{{margin:0 0 1em;text-wrap:pretty}}
ul,ol{{margin:0;padding:0}}
h1,h2,h3{{margin:0;color:var(--inchiostro);font-family:var(--titolo);font-weight:400;text-wrap:balance}}
code,pre{{font-family:var(--mono)}}
code{{font-size:.9em;padding:.05em .3em;background:var(--carta-2);color:var(--inchiostro);overflow-wrap:anywhere}}
.dentro{{max-width:var(--colonna);margin:0 auto;padding:0 var(--gutter)}}
.salta{{position:absolute;left:-9999px;top:8px;z-index:20;padding:10px 14px;background:var(--inchiostro);color:#fff}}
.salta:focus{{left:12px}}
.stretta{{font-family:var(--titolo);font-stretch:75%;font-weight:560;text-transform:uppercase;letter-spacing:.04em}}

.azione{{display:inline-flex;align-items:center;justify-content:center;gap:10px;min-height:48px;padding:0 22px;border:1px solid var(--azione);background:var(--azione);color:#fff;text-decoration:none;font:560 .98rem/1 var(--titolo);font-stretch:75%;letter-spacing:.06em;text-transform:uppercase;transition:background-color .18s,border-color .18s,color .18s}}
.azione:hover{{background:var(--azione-giu);border-color:var(--azione-giu)}}
.azione--bordo{{background:transparent;color:var(--inchiostro);border-color:var(--inchiostro)}}
.azione--bordo:hover{{background:var(--inchiostro);border-color:var(--inchiostro);color:#fff}}

/* ---------- testata ---------- */
.testata{{position:relative;background:var(--cielo);overflow:hidden;isolation:isolate}}
.testata__volta{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:right top;z-index:-1;-webkit-mask-image:linear-gradient(90deg,rgba(0,0,0,.15) 0,rgba(0,0,0,.3) 45%,#000 85%);mask-image:linear-gradient(90deg,rgba(0,0,0,.15) 0,rgba(0,0,0,.3) 45%,#000 85%)}}
.menu .dentro{{display:flex;align-items:center;gap:28px;min-height:68px}}
.marchio{{display:inline-flex;align-items:center;gap:10px;text-decoration:none;color:var(--inchiostro);font:500 1.2rem/1 var(--titolo);font-stretch:108%;letter-spacing:-.01em}}
.marchio svg{{width:28px;height:28px}}
.menu__fine{{margin-left:auto;display:flex;gap:24px;font-size:.86rem}}
.menu__fine a{{text-decoration:none;padding:6px 0;border-bottom:1px solid currentColor}}
.testata__corpo{{padding:clamp(40px,7vw,104px) 0 clamp(48px,6vw,88px);max-width:900px}}
.testata h1{{font-weight:250;font-size:clamp(2.6rem, 1.2rem + 5vw, 5.8rem);line-height:.95;letter-spacing:-.025em;font-stretch:114%}}
.testata p{{margin:22px 0 28px;max-width:56ch;font-size:1.1rem;color:var(--grafite)}}
.testata__vie{{display:flex;flex-wrap:wrap;gap:12px}}

/* ---------- le voci ---------- */
.sezione{{padding:var(--ritmo) 0}}
.voci{{display:grid;gap:clamp(44px,6vw,80px)}}
.voce{{display:grid;grid-template-columns:minmax(0,3fr) minmax(0,9fr);gap:12px 48px;padding-top:18px;border-top:1px solid var(--inchiostro);scroll-margin-top:24px}}
.voce__data{{margin:0;font-size:.82rem;font-weight:600;letter-spacing:.07em;color:var(--cenere);font-variant-numeric:tabular-nums}}
.voce__corpo{{min-width:0;max-width:70ch}}
.voce h2{{font-weight:350;font-size:clamp(1.5rem, 1.2rem + .9vw, 2rem);line-height:1.15;letter-spacing:-.015em;font-stretch:108%;margin-bottom:18px}}
.voce h2 a{{text-decoration:none}}
.voce h2 a:hover{{text-decoration:underline}}
.voce h3{{font-size:1.15rem;margin:1.4em 0 .5em}}
.voce strong{{color:var(--inchiostro);font-weight:600}}
.voce ul,.voce ol{{margin:0 0 1em;padding-left:1.3em}}
.voce li{{margin:0 0 .45em;padding-left:.2em}}
.voce ul li::marker{{color:var(--cenere)}}
.voce blockquote{{margin:0 0 1em;padding-left:18px;border-left:1px solid var(--azione)}}
.voce pre{{margin:0 0 1em;padding:14px 16px;background:var(--term);color:var(--term-testo);border-radius:4px;font-size:.8rem;line-height:1.6;white-space:pre-wrap;overflow-wrap:anywhere}}
.voce pre code{{background:none;padding:0;color:inherit;font-size:inherit}}

/* chiusura */
.vuoto{{position:relative;background:var(--vuoto);color:var(--vuoto-testo);isolation:isolate}}
.vuoto::before{{content:"";position:absolute;inset:0;z-index:-1;opacity:.13;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='g'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 .55 0'/%3E%3C/filter%3E%3Crect width='180' height='180' filter='url(%23g)'/%3E%3C/svg%3E")}}
.vuoto ::selection{{background:#fff;color:var(--vuoto)}}
.vuoto :focus-visible{{outline-color:var(--term-tu)}}
.chiusura .dentro{{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(0,1fr);gap:32px;align-items:end}}
.chiusura h2{{color:#fff;font-weight:300;font-size:clamp(2.2rem, 1.4rem + 2.6vw, 3.8rem);line-height:1;letter-spacing:-.02em;font-stretch:112%}}
.chiusura p{{margin:18px 0 0;color:var(--vuoto-cenere);max-width:52ch}}
.chiusura code{{background:var(--vuoto-2);color:#fff}}
.chiusura__vie{{justify-self:end;display:flex;flex-wrap:wrap;gap:12px;justify-content:flex-end}}
.chiusura .azione--chiara{{background:#fff;border-color:#fff;color:var(--inchiostro)}}
.chiusura .azione--chiara:hover{{background:var(--cielo);border-color:var(--cielo)}}
.chiusura .azione--bordo{{color:#fff;border-color:#fff}}
.chiusura .azione--bordo:hover{{background:#fff;color:var(--inchiostro)}}

.piede{{padding:32px 0 44px;font-size:.86rem;color:var(--cenere)}}
.piede .dentro{{display:flex;flex-wrap:wrap;gap:8px 24px;justify-content:space-between}}
.piede strong{{color:var(--inchiostro)}}
.piede p{{margin:0}}

@media (max-width:760px){{
  .voce,.chiusura .dentro{{grid-template-columns:minmax(0,1fr)}}
  .chiusura__vie{{justify-self:stretch;justify-content:flex-start}}
  .menu__fine a:first-child{{display:none}}
  .testata__volta{{opacity:.35}}
}}
</style>
<script defer data-domain="arturo.stellakamikaze.org" data-api="/api/e" src="/js/a.js"></script>
</head>
<body>
<a class="salta" href="#voci">Vai al contenuto</a>

<header class="testata">
  <img class="testata__volta" src="../img/volta.svg" alt="" width="1600" height="1000">
  <nav class="menu" aria-label="Principale">
    <div class="dentro">
      <a class="marchio" href="../" aria-label="Arturo, pagina principale">
        <svg viewBox="0 0 28 28" fill="none" aria-hidden="true"><path d="M3 24 11.5 9.5 17 17l8-11" stroke="#0b0d10" stroke-width="1.5"/><circle cx="11.5" cy="9.5" r="3.2" fill="#f2a24a"/><circle cx="17" cy="17" r="1.6" fill="#0b0d10"/><circle cx="25" cy="6" r="1.6" fill="#0b0d10"/></svg>
        Arturo
      </a>
      <div class="menu__fine stretta"><a href="../">Cos'è Arturo</a><a href="../installa/">Installa</a></div>
    </div>
  </nav>
  <div class="dentro">
    <div class="testata__corpo">
      <h1 id="titolo">Novità di Arturo</h1>
      <p>Cosa cambia a ogni aggiornamento, il principio dietro e cosa devi fare tu. La voce più recente sta in cima: l'ultima è del {ultima}. Dentro Claude Code le stesse voci te le racconta <code>/novita</code>.</p>
      <div class="testata__vie">
        <a class="azione" href="#voci">Leggi le novità</a>
        <a class="azione azione--bordo" href="https://github.com/stellakamikaze/arturo/blob/main/NOVITA.md">NOVITA.md su GitHub</a>
      </div>
    </div>
  </div>
</header>

<main>

<section class="sezione" aria-labelledby="titolo">
  <div class="dentro">
    <div class="voci" id="voci">

{voci}

    </div>
  </div>
</section>

<section class="sezione vuoto chiusura" aria-labelledby="t-comincia">
  <div class="dentro">
    <div>
      <h2 id="t-comincia">Per cominciare</h2>
      <p>Installa Arturo sul tuo computer, con la guida passo per passo.</p>
    </div>
    <div class="chiusura__vie">
      <a class="azione azione--chiara" href="../installa/">Installa Arturo</a>
      <a class="azione azione--bordo" href="../">Cos'è Arturo</a>
    </div>
  </div>
</section>

</main>

<footer class="piede">
  <div class="dentro">
    <p><strong>Progetto di Federico Nejrotti.</strong> Licenza MIT. <a href="https://github.com/stellakamikaze/arturo">github.com/stellakamikaze/arturo</a></p>
    <p>Questa pagina non usa cookie di tracciamento, tracker né font da server esterni.</p>
  </div>
</footer>

<script type="module" src="../note.js"></script>
</body>
</html>
"""


def main(argomenti: list) -> int:
    parser = argparse.ArgumentParser(description="Scrive sito/novita/index.html da NOVITA.md.")
    parser.add_argument("--da", default=str(DEFAULT), help="percorso di NOVITA.md, oppure - per stdin")
    parser.add_argument("--prova", action="store_true", help="stampa la pagina senza scriverla")
    opzioni = parser.parse_args(argomenti)
    if opzioni.da == "-":
        testo = sys.stdin.buffer.read().decode("utf-8")
    else:
        sorgente = Path(opzioni.da)
        if not sorgente.is_file():
            print("Non trovo " + str(sorgente) + ": passa il percorso con --da", file=sys.stderr)
            return 1
        testo = sorgente.read_text(encoding="utf-8")
    elenco = voci(testo)
    if not elenco:
        print("Nessuna voce «## AAAA-MM-GG — Titolo» trovata: non scrivo niente", file=sys.stderr)
        return 1
    risultato = pagina(elenco)
    if opzioni.prova:
        sys.stdout.buffer.write(risultato.encode("utf-8"))
        return 0
    PAGINA.parent.mkdir(parents=True, exist_ok=True)
    PAGINA.write_text(risultato, encoding="utf-8", newline="\n")
    print("Scritte " + str(len(elenco)) + " voci in " + str(PAGINA.relative_to(RADICE)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
