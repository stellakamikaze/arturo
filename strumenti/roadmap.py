#!/usr/bin/env python3
"""Scrive le due pagine della roadmap di Arturo da ROADMAP.md.

ROADMAP.md vive nel repo di Arturo, ramo dev. Ha una riga "Aggiornata il AAAA-MM-GG", qualche
paragrafo d'apertura, poi sezioni "## Nome". Dentro una sezione una voce è "### Titolo {#ancora}",
seguita da "Stato: ..." e dai suoi paragrafi. I commenti HTML (i numeri dei task) non escono mai.

Le uscite sono due:
- sito/roadmap/index.html: la pagina pubblica, sola lettura, con "Commenta" su ogni voce;
- <sviluppo>/pagine/roadmap/: la pagina dietro Access di arturo-sviluppo (repo arturo-admin),
  dove ogni voce ha il suo filo di commenti, visibile a tutte le persone invitate.

  git -C ../arturo show origin/dev:ROADMAP.md | python3 strumenti/roadmap.py --da -
  python3 strumenti/roadmap.py --da PERCORSO [--sviluppo CARTELLA] [--prova]

Solo libreria standard, Python 3.8 o successivo.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import novita  # noqa: E402  stesso markdown in linea, stessi blocchi, stesso stile della pagina Novità

RADICE = Path(__file__).resolve().parent.parent
PAGINA = RADICE / "sito" / "roadmap" / "index.html"
DEFAULT = RADICE.parent / "arturo" / "ROADMAP.md"
SVILUPPO = RADICE.parent / "arturo-admin" / "sviluppo"
SITO = novita.SITO
URL = SITO + "/roadmap/"
COMMENTI = "/sviluppo/roadmap/"
GITHUB = "https://github.com/stellakamikaze/arturo/blob/dev/ROADMAP.md"

DATA = re.compile(r"^Aggiornata il (\d{4}-\d{2}-\d{2})\s*$")
VOCE = re.compile(r"^### (.+?)\s*\{#([a-z0-9-]+)\}\s*$")
STATO = re.compile(r"^Stato:\s*(.+)$")
SEZIONE = re.compile(r"^## (.+?)(?:\s+\(versione ([^)]+)\))?\s*$")
COMMENTO = re.compile(r"<!--.*?-->", re.S)

# La seconda riga, in cenere, dei titoli di sezione. Una sezione nuova senza voce qui esce senza.
SOTTOTITOLI = {
    "Adesso": "Il lavoro in corso.",
    "Prossimo": "Parte quando finisce quello di adesso.",
    "Dopo": "In fila, senza una data.",
    "Da decidere": "Aspettano una scelta di chi mantiene Arturo.",
    "Uscito di recente": "Le ultime versioni, raccontate in Novità.",
}

DESCRIZIONE = ("La roadmap di Arturo, l'harness in italiano per Claude Code: su cosa si lavora adesso, "
               "cosa viene dopo e cosa aspetta una decisione. Ogni voce si commenta.")


class Fuori(Exception):
    """ROADMAP.md non ha la forma attesa: il messaggio dice dove."""


def leggi(testo: str) -> dict:
    """ROADMAP.md diviso in data, apertura e sezioni con le loro voci."""
    righe = COMMENTO.sub("", testo).splitlines()
    data = None
    apertura: list = []
    sezioni: list = []
    voce = None
    ancore = set()
    for riga in righe:
        if data is None and DATA.match(riga):
            data = DATA.match(riga).group(1)
            continue
        if riga.startswith("# "):
            continue
        if riga.startswith("## "):
            # "## Adesso (versione 0.3)": il numero con cui esce il blocco (3/11/2026). Il nome resta la chiave.
            n = SEZIONE.match(riga)
            sezioni.append({"nome": n.group(1).strip(), "versione": n.group(2), "righe": [], "voci": []})
            voce = None
            continue
        m = VOCE.match(riga)
        if m:
            if not sezioni:
                raise Fuori("voce prima di ogni sezione: " + riga)
            if m.group(2) in ancore:
                raise Fuori("ancora ripetuta: " + m.group(2))
            ancore.add(m.group(2))
            voce = {"titolo": m.group(1), "ancora": m.group(2), "stato": None, "righe": []}
            sezioni[-1]["voci"].append(voce)
            continue
        if riga.startswith("### "):
            raise Fuori("voce senza {#ancora}: " + riga)
        if voce is not None:
            s = STATO.match(riga)
            if voce["stato"] is None and s:
                voce["stato"] = s.group(1).strip()
            else:
                voce["righe"].append(riga)
        elif sezioni:
            sezioni[-1]["righe"].append(riga)
        else:
            apertura.append(riga)
    if data is None:
        raise Fuori('manca la riga "Aggiornata il AAAA-MM-GG"')
    for s in sezioni:
        for v in s["voci"]:
            if not v["stato"]:
                raise Fuori("voce senza Stato: " + v["ancora"])
    return {"data": data, "apertura": apertura, "sezioni": sezioni}


def etichetta(stato: str) -> tuple:
    """"in corso. Il pacchetto..." -> ("In corso", "Il pacchetto..."): la prima frase fa da etichetta."""
    prima, _, resto = stato.partition(". ")
    prima = prima.rstrip(".")
    return prima[:1].upper() + prima[1:], resto.strip()


def primo_paragrafo(righe: list) -> str:
    paragrafo = []
    for r in righe:
        if r.strip():
            paragrafo.append(r.strip())
        elif paragrafo:
            break
    return " ".join(paragrafo)


# ---------- pagina pubblica ----------

def voce_pubblica(v: dict) -> str:
    nome, resto = etichetta(v["stato"])
    corpo = ("<p class=\"voce__stato\">" + novita.in_linea(resto) + "</p>\n" if resto else "") + novita.blocchi(v["righe"])
    return (
        '      <article class="voce" id="' + v["ancora"] + '" aria-labelledby="t-' + v["ancora"] + '">\n'
        '        <p class="voce__data">' + html.escape(nome) + "</p>\n"
        '        <div class="voce__corpo">\n'
        '          <h3 id="t-' + v["ancora"] + '"><a href="#' + v["ancora"] + '">' + novita.in_linea(v["titolo"]) + "</a></h3>\n"
        + "\n".join("          " + r for r in corpo.splitlines()) + "\n"
        '          <p class="voce__vie"><a class="azione azione--bordo" href="' + COMMENTI + "#" + v["ancora"]
        + '">Commenta questa voce</a></p>\n'
        "        </div>\n"
        "      </article>"
    )


def sezione_pubblica(s: dict, n: int) -> str:
    sid = "s-" + novita.slug(s["nome"])
    sotto = SOTTOTITOLI.get(s["nome"])
    if s.get("versione"):
        sotto = "Versione " + s["versione"] + "." + (" " + sotto if sotto else "")
    testa = ('    <h2 class="sezione__titolo" id="' + sid + '">' + novita.in_linea(s["nome"])
             + ("<span>" + html.escape(sotto) + "</span>" if sotto else "") + "</h2>\n")
    if s["voci"]:
        dentro = '    <div class="voci">\n\n' + "\n\n".join(voce_pubblica(v) for v in s["voci"]) + "\n\n    </div>\n"
    else:
        dentro = ('    <div class="elenco">\n'
                  + "\n".join("      " + r for r in novita.blocchi(s["righe"]).splitlines()) + "\n    </div>\n")
    return ('<section class="sezione' + (" sezione--carta" if n % 2 else "") + '" aria-labelledby="' + sid + '">\n'
            '  <div class="dentro">\n' + testa + dentro + "  </div>\n</section>")


def json_ld(r: dict) -> str:
    dati = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "@id": URL + "#roadmap",
        "name": "La strada di Arturo",
        "description": DESCRIZIONE,
        "url": URL,
        "inLanguage": "it",
        "dateModified": r["data"],
        "publisher": {"@type": "Person", "name": "Federico Nejrotti"},
        "about": {"@type": "SoftwareApplication", "name": "Arturo", "url": SITO + "/"},
    }
    return json.dumps(dati, ensure_ascii=False, indent=1).replace("</", "<\\/")


def stile_novita() -> str:
    """Il <style> della pagina Novità, senza le graffe raddoppiate del suo modello."""
    m = novita.MODELLO
    s = m[m.index("<style>") + len("<style>"):m.index("</style>")]
    return s.replace("{{", "{").replace("}}", "}")


STILE_ROADMAP = """
/* ---------- roadmap ---------- */
.sezione--carta{background:var(--carta-2)}
.sezione__titolo{font-weight:300;font-size:clamp(2.1rem, 1.3rem + 2.6vw, 3.6rem);line-height:1.02;letter-spacing:-.02em;font-stretch:112%;margin-bottom:clamp(36px,5vw,64px);scroll-margin-top:24px}
.sezione__titolo span{display:block;color:var(--cenere)}
.voce h3{font-weight:350;font-size:clamp(1.5rem, 1.2rem + .9vw, 2rem);line-height:1.15;letter-spacing:-.015em;font-stretch:108%;margin:0 0 18px;overflow-wrap:break-word}
.voce h3 a{text-decoration:none}
.voce h3 a:hover{text-decoration:underline}
.voce__stato{color:var(--inchiostro)}
.voce__vie{margin:24px 0 0}
.elenco{max-width:62ch}
.elenco ul{list-style:none;border-top:1px solid var(--inchiostro)}
.elenco li{padding:14px 0;border-bottom:1px solid var(--filetto)}
.testata__data{font:600 .9rem/1.3 var(--titolo);font-stretch:75%;color:var(--cenere);font-variant-numeric:tabular-nums}
"""


def pagina_pubblica(r: dict) -> str:
    sezioni = "\n\n".join(sezione_pubblica(s, i) for i, s in enumerate(r["sezioni"]))
    testo = MODELLO
    for chiave, valore in (
        ("@@STILE@@", stile_novita() + STILE_ROADMAP),
        ("@@DESCRIZIONE@@", html.escape(DESCRIZIONE)),
        ("@@URL@@", URL),
        ("@@SITO@@", SITO),
        ("@@JSONLD@@", json_ld(r)),
        ("@@APERTURA@@", novita.in_linea(primo_paragrafo(r["apertura"]))),
        ("@@DATAISO@@", r["data"]),
        ("@@DATA@@", novita.data_lunga(r["data"])),
        ("@@COMMENTI@@", COMMENTI),
        ("@@GITHUB@@", GITHUB),
        ("@@SEZIONI@@", sezioni),
    ):
        testo = testo.replace(chiave, valore)
    return testo


MODELLO = """<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>La strada di Arturo · cosa viene adesso e dopo</title>
<meta name="description" content="@@DESCRIZIONE@@">
<link rel="canonical" href="@@URL@@">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Arturo">
<meta property="og:locale" content="it_IT">
<meta property="og:title" content="La strada di Arturo · cosa viene adesso e dopo">
<meta property="og:description" content="@@DESCRIZIONE@@">
<meta property="og:url" content="@@URL@@">
<meta property="og:image" content="@@SITO@@/img/anteprima-github.png">
<meta property="og:image:width" content="1280">
<meta property="og:image:height" content="640">
<meta property="og:image:alt" content="Arturo, un harness per il lavoro della conoscenza: la stella sopra il reticolo blu della volta celeste">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="La strada di Arturo · cosa viene adesso e dopo">
<meta name="twitter:description" content="@@DESCRIZIONE@@">
<meta name="twitter:image" content="@@SITO@@/img/anteprima-github.png">
<link rel="alternate" type="text/markdown" title="ROADMAP.md su GitHub" href="@@GITHUB@@">
<meta name="theme-color" content="#d7ebff">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' fill='%230b0d10'/%3E%3Cpath d='M5 25 13 11l6 8 8-11' fill='none' stroke='%23d7ebff' stroke-width='1.6'/%3E%3Ccircle cx='13' cy='11' r='3.2' fill='%23f2a24a'/%3E%3C/svg%3E">
<link rel="preload" href="../font/archivo.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="../font/atkinson-next.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="../stile/colori.css">
<script type="application/ld+json">
@@JSONLD@@
</script>
<style>@@STILE@@</style>
<script defer data-domain="arturo.stellakamikaze.org" data-api="/api/e" src="/js/a.js"></script>
<script defer src="../traccia.js"></script>
</head>
<body>
<a class="salta" href="#s-adesso">Vai al contenuto</a>

<header class="testata">
  <img class="testata__volta" src="../img/volta.svg" alt="" width="1600" height="1000">
  <nav class="menu" aria-label="Principale">
    <div class="dentro">
      <a class="marchio" href="../" aria-label="Arturo, pagina principale">
        <svg viewBox="0 0 28 28" fill="none" aria-hidden="true"><path d="M3 24 11.5 9.5 17 17l8-11" stroke="#0b0d10" stroke-width="1.5"/><circle cx="11.5" cy="9.5" r="3.2" fill="#f2a24a"/><circle cx="17" cy="17" r="1.6" fill="#0b0d10"/><circle cx="25" cy="6" r="1.6" fill="#0b0d10"/></svg>
        Arturo
      </a>
      <div class="menu__fine">
        <a class="menu__voce" href="../">Cos'è Arturo</a>
        <a class="azione azione--scura stretta" href="../installa/">Installa</a>
      </div>
    </div>
  </nav>
  <div class="dentro">
    <div class="testata__corpo">
      <h1 id="titolo">La strada di Arturo</h1>
      <p>@@APERTURA@@ Ogni voce si commenta nella pagina delle persone che usano Arturo: si entra con l'email dell'invito, e ognuno legge i commenti degli altri.</p>
      <p class="testata__data">Aggiornata il <time datetime="@@DATAISO@@">@@DATA@@</time></p>
      <div class="testata__vie">
        <a class="azione" href="@@COMMENTI@@">Commenta la roadmap</a>
        <a class="azione azione--bordo" href="@@GITHUB@@">ROADMAP.md su GitHub</a>
      </div>
    </div>
  </div>
</header>

<main>

@@SEZIONI@@

<section class="sezione vuoto chiusura" aria-labelledby="t-invito">
  <div class="dentro">
    <div>
      <h2 id="t-invito">Non hai l'invito?</h2>
      <p>I commenti sono per chi usa Arturo. Se lo usi e non riesci a entrare, o se vuoi dire qualcosa senza invito, scrivimi dal modulo.</p>
    </div>
    <div class="chiusura__vie">
      <a class="azione azione--chiara" href="../feedback/">Scrivimi</a>
      <a class="azione azione--bordo" href="../novita/">Le novità</a>
    </div>
  </div>
</section>

</main>

<footer class="piede">
  <div class="dentro">
    <p><strong>Progetto di Federico Nejrotti.</strong> Licenza MIT. <a href="https://github.com/stellakamikaze/arturo">github.com/stellakamikaze/arturo</a></p>
    <p>Niente cookie, nessun tracker di terzi, nessun font da server esterni. <a href="../privacy/">Privacy</a> · <a href="../feedback/">Dimmi com'è andata</a></p>
  </div>
</footer>

<script type="module" src="../note.js"></script>
</body>
</html>
"""


# ---------- pagina con i commenti (arturo-sviluppo) ----------

def voce_sviluppo(v: dict, rovescio: bool) -> str:
    nome, resto = etichetta(v["stato"])
    corpo = ("<p><strong>" + html.escape(nome) + ".</strong> " + novita.in_linea(resto) + "</p>\n" if resto
             else "<p><strong>" + html.escape(nome) + ".</strong></p>\n") + novita.blocchi(v["righe"])
    return (
        '<section class="giro" id="' + v["ancora"] + '" data-sezione="' + v["ancora"]
        + '" aria-labelledby="t-' + v["ancora"] + '">\n'
        '  <div class="dentro">\n'
        '    <div class="giro__testo">\n'
        '      <h2 id="t-' + v["ancora"] + '">' + novita.in_linea(v["titolo"]) + "</h2>\n"
        + "\n".join("      " + r for r in corpo.splitlines()) + "\n"
        "    </div>\n"
        "  </div>\n"
        '  <div class="dentro filo" data-filo></div>\n'
        "</section>"
    )


def pagina_sviluppo(r: dict) -> tuple:
    blocchi = []
    for s in r["sezioni"]:
        if s["voci"]:
            tappa = s["nome"] + (" · versione " + s["versione"] if s.get("versione") else "")
            blocchi.append('<div class="dentro"><p class="tappa">' + html.escape(tappa) + "</p></div>")
            blocchi.extend(voce_sviluppo(v, i % 2 == 1) for i, v in enumerate(s["voci"]))
    decidere = next((s for s in r["sezioni"] if s["nome"] == "Da decidere" and not s["voci"]), None)
    sezioni = [v["ancora"] for s in r["sezioni"] for v in s["voci"]]
    if decidere is not None:
        sezioni.append("decidere")
        blocchi.append(
            '<section class="giro" id="decidere" data-sezione="decidere" aria-labelledby="t-decidere">\n'
            '  <div class="dentro">\n    <div class="giro__testo">\n'
            '      <h2 id="t-decidere">Da decidere<span>Aspettano una scelta di chi mantiene Arturo.</span></h2>\n'
            + "\n".join("      " + x for x in novita.blocchi(decidere["righe"]).splitlines())
            + "\n    </div>\n  </div>\n  <div class=\"dentro filo\" data-filo></div>\n</section>")
    sezioni.append("generale")
    pagina = SVILUPPO_MODELLO
    for chiave, valore in (
        ("@@APERTURA@@", novita.in_linea(primo_paragrafo(r["apertura"]))),
        ("@@DATA@@", novita.data_lunga(r["data"])),
        ("@@SEZIONI@@", "\n\n".join(blocchi)),
    ):
        pagina = pagina.replace(chiave, valore)
    meta = {
        "titolo": "La strada di Arturo",
        "attacco": "Su cosa lavoro adesso, cosa viene dopo e cosa aspetta una decisione. Ogni voce ha i suoi commenti.",
        "data": novita.data_lunga(r["data"]),
        "sezioni": sezioni,
    }
    return pagina, json.dumps(meta, ensure_ascii=False, indent=2) + "\n"


SVILUPPO_MODELLO = """<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>La strada di Arturo · Sviluppo di Arturo</title>
<meta name="theme-color" content="#d7ebff">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' fill='%230b0d10'/%3E%3Cpath d='M5 25 13 11l6 8 8-11' fill='none' stroke='%23d7ebff' stroke-width='1.6'/%3E%3Ccircle cx='13' cy='11' r='3.2' fill='%23f2a24a'/%3E%3C/svg%3E">
<link rel="preload" href="../static/archivo.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="../static/atkinson-next.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="../static/colori.css">
<link rel="stylesheet" href="../static/sviluppo.css">
<script defer src="../static/commenti.js"></script>
</head>
<body data-pagina="roadmap">
<a class="salta" href="#voci">Vai alle voci</a>
<header class="testata">
  <img class="testata__volta" src="../static/volta.svg" alt="" width="1600" height="1000">
  <nav class="menu" aria-label="Principale">
    <div class="dentro">
      <a class="marchio" href="../" aria-label="Sviluppo di Arturo, tutte le pagine">
        <svg viewBox="0 0 28 28" fill="none" aria-hidden="true"><path d="M3 24 11.5 9.5 17 17l8-11" stroke="#0b0d10" stroke-width="1.5"/><circle cx="11.5" cy="9.5" r="3.2" fill="#f2a24a"/><circle cx="17" cy="17" r="1.6" fill="#0b0d10"/><circle cx="25" cy="6" r="1.6" fill="#0b0d10"/></svg>
        Arturo
      </a>
      <div class="menu__fine stretta"><a href="../">Tutte le pagine</a><span class="menu__io" id="io" hidden></span></div>
    </div>
  </nav>
  <div class="dentro">
    <div class="testata__corpo">
      <h1>La strada di Arturo</h1>
      <p>@@APERTURA@@ Aggiornata il @@DATA@@.</p>
    </div>
    <ul class="patti">
      <li><strong>I commenti si vedono.</strong> Li leggono tutte le persone invitate, col tuo nome. Puoi togliere i tuoi.</li>
      <li><strong>Una riga basta.</strong> Dimmi cosa ti serve, cosa ti manca o cosa faresti prima.</li>
      <li><strong>Leggo prima di aggiornare.</strong> Ogni volta che aggiorno una voce, leggo i commenti su quella voce.</li>
    </ul>
  </div>
</header>

<main id="voci">

@@SEZIONI@@

<section class="giro giro--chiusura" data-sezione="generale" aria-labelledby="t-generale">
  <div class="dentro">
    <h2 id="t-generale">Cosa manca?<span>Una cosa che ti serve e che in questa strada non vedi.</span></h2>
  </div>
  <div class="dentro filo" data-filo></div>
</section>

</main>

<footer class="piede">
  <div class="dentro">
    <p>Pagina privata dello sviluppo di Arturo. La vedono solo le persone invitate.</p>
    <p><strong>Arturo</strong> · progetto di Federico Nejrotti</p>
  </div>
</footer>
</body>
</html>
"""


def main(argomenti: list) -> int:
    parser = argparse.ArgumentParser(description="Scrive le pagine della roadmap da ROADMAP.md.")
    parser.add_argument("--da", default=str(DEFAULT), help="percorso di ROADMAP.md, oppure - per stdin")
    parser.add_argument("--sviluppo", default=str(SVILUPPO), help="cartella sviluppo/ del repo arturo-admin")
    parser.add_argument("--prova", action="store_true", help="controlla e stampa i conteggi senza scrivere")
    o = parser.parse_args(argomenti)
    if o.da == "-":
        testo = sys.stdin.buffer.read().decode("utf-8")
    else:
        sorgente = Path(o.da)
        if not sorgente.is_file():
            print("Non trovo " + str(sorgente) + ": passa il percorso con --da", file=sys.stderr)
            return 1
        testo = sorgente.read_text(encoding="utf-8")
    try:
        r = leggi(testo)
    except Fuori as e:
        print("ROADMAP.md fuori forma: " + str(e), file=sys.stderr)
        return 1
    voci = sum(len(s["voci"]) for s in r["sezioni"])
    pubblica = pagina_pubblica(r)
    sviluppo, meta = pagina_sviluppo(r)
    if o.prova:
        print("roadmap del " + r["data"] + ": " + str(len(r["sezioni"])) + " sezioni, " + str(voci) + " voci")
        return 0
    PAGINA.parent.mkdir(parents=True, exist_ok=True)
    PAGINA.write_text(pubblica, encoding="utf-8")
    print("Scritta " + str(PAGINA.relative_to(RADICE)) + ": " + str(voci) + " voci, aggiornata il " + r["data"])
    cartella = Path(o.sviluppo)
    if cartella.is_dir():
        dest = cartella / "pagine" / "roadmap"
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "index.html").write_text(sviluppo, encoding="utf-8")
        (dest / "pagina.json").write_text(meta, encoding="utf-8")
        print("Scritta " + str(dest) + ": index.html e pagina.json")
    else:
        print("Cartella di sviluppo assente (" + str(cartella) + "): pagina con i commenti non scritta", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
