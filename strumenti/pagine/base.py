"""Pezzi comuni delle pagine di ricerca della landing di Arturo: head, testata, piede, CSS.

Le pagine sorelle (installa/, organizzazioni/, privacy/) tengono il loro <style> dentro la pagina:
queste fanno lo stesso, così ogni pagina regge da sola e non tocca file esistenti.
"""
import html
import json
import re

SITO = "https://arturo.stellakamikaze.org"
OG_IMG = SITO + "/img/og.png"

FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' "
           "height='32' fill='%230b0d10'/%3E%3Cpath d='M5 25 13 11l6 8 8-11' fill='none' stroke='%23d7ebff' "
           "stroke-width='1.6'/%3E%3Ccircle cx='13' cy='11' r='3.2' fill='%23f2a24a'/%3E%3C/svg%3E")

MARCHIO = ('<svg viewBox="0 0 28 28" fill="none" aria-hidden="true"><path d="M3 24 11.5 9.5 17 17l8-11" '
           'stroke="#0b0d10" stroke-width="1.5"/><circle cx="11.5" cy="9.5" r="3.2" fill="#f2a24a"/>'
           '<circle cx="17" cy="17" r="1.6" fill="#0b0d10"/><circle cx="25" cy="6" r="1.6" fill="#0b0d10"/></svg>')

PIU = ('<svg viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M8 2v12M2 8h12" stroke="currentColor" '
       'stroke-width="1.3"/></svg>')

CSS = r"""
@font-face{font-family:"Archivo";src:url(../font/archivo.woff2) format("woff2");font-weight:100 900;font-stretch:62% 125%;font-display:swap}
@font-face{font-family:"Atkinson Next";src:url(../font/atkinson-next.woff2) format("woff2");font-weight:200 800;font-style:normal;font-display:swap}
@font-face{font-family:"Atkinson Mono";src:url(../font/atkinson-mono.woff2) format("woff2");font-weight:200 800;font-display:swap}

*,*::before,*::after{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;scroll-behavior:smooth;scroll-padding-top:24px;scrollbar-color:var(--scorrimento) var(--carta)}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
body{margin:0;background:var(--carta);color:var(--grafite);font:400 clamp(16.5px, .98rem + .15vw, 18px)/1.55 var(--testo);letter-spacing:-.005em;-webkit-font-smoothing:antialiased}
::selection{background:var(--azione);color:var(--bianco)}
:focus-visible{outline:2px solid var(--azione);outline-offset:3px}
img,svg{display:block;max-width:100%}
a{color:inherit;text-underline-offset:.2em;text-decoration-thickness:1px}
p,li,figcaption,summary{text-wrap:pretty}
p{margin:0 0 1em}
ul,ol{margin:0;padding:0;list-style:none}
h1,h2,h3{margin:0;color:var(--inchiostro);font-family:var(--titolo);font-weight:400;text-wrap:balance;overflow-wrap:break-word;min-width:0}
code,pre{font-family:var(--mono)}
code{font-size:.9em;padding:.05em .3em;background:var(--carta-2);color:var(--inchiostro);overflow-wrap:anywhere}
kbd{display:inline-block;min-width:1.7em;padding:.05em .4em;border:1px solid var(--scorrimento);border-bottom-width:2px;background:var(--bianco);font:.82em var(--mono);text-align:center;color:var(--inchiostro)}
.dentro{max-width:var(--colonna);margin:0 auto;padding:0 var(--gutter)}
.salta{position:absolute;left:12px;top:8px;z-index:20;padding:10px 14px;background:var(--inchiostro);color:var(--bianco);transform:translateY(-150%)}
.salta:focus{transform:none}
/* voce stretta e maiuscola: solo sui pulsanti, a 0,04em */
.stretta{font-family:var(--titolo);font-stretch:75%;font-weight:560;text-transform:uppercase;letter-spacing:.04em}

.azione{display:inline-flex;align-items:center;justify-content:center;gap:10px;min-height:48px;padding:0 22px;border:1px solid var(--azione);background:var(--azione);color:var(--bianco);text-decoration:none;font:560 .98rem/1 var(--titolo);font-stretch:75%;letter-spacing:.04em;text-transform:uppercase;cursor:pointer;transition:background-color .18s,border-color .18s,color .18s}
.azione:hover{background:var(--azione-giu);border-color:var(--azione-giu)}
.azione:active{transform:translateY(1px);transition:none}
.azione--bordo{background:transparent;color:var(--inchiostro);border-color:var(--inchiostro)}
.azione--bordo:hover{background:var(--inchiostro);border-color:var(--inchiostro);color:var(--bianco)}

/* ---------- testata unica delle pagine interne ---------- */
.menu{position:relative;z-index:3}
.menu .dentro{display:flex;align-items:center;gap:28px;min-height:68px}
.marchio{display:inline-flex;align-items:center;gap:10px;min-height:44px;text-decoration:none;color:var(--inchiostro);font:500 1.2rem/1 var(--titolo);font-stretch:108%;letter-spacing:-.01em}
.marchio svg{width:28px;height:28px;flex:none}
.menu__fine{margin-left:auto;display:flex;align-items:center;gap:24px}
.menu__voce{display:inline-flex;align-items:center;min-height:44px;color:var(--grafite);text-decoration:none;font-size:.9rem;white-space:nowrap}
a.menu__voce:hover{color:var(--inchiostro);text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:.3em}
.menu .azione--scura{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:0 18px;border:1px solid var(--inchiostro);background:var(--inchiostro);color:var(--bianco);text-decoration:none;font-size:.9rem;white-space:nowrap;transition:background-color .18s,border-color .18s}
.menu .azione--scura:hover{background:var(--inchiostro-su);border-color:var(--inchiostro-su);color:var(--bianco)}
.menu a:active{transform:translateY(1px);transition:none}
@media (max-width:480px){.menu .dentro,.menu__fine{gap:16px}}
/* sotto 360 px il marchio basta per tornare alla home */
@media (max-width:360px){a.menu__voce{display:none}}

.testata{position:relative;background:var(--cielo);overflow:hidden;isolation:isolate}
.testata__volta{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:right top;z-index:-1;-webkit-mask-image:linear-gradient(90deg,var(--maschera-lieve) 0,var(--maschera-media) 45%,var(--maschera) 85%);mask-image:linear-gradient(90deg,var(--maschera-lieve) 0,var(--maschera-media) 45%,var(--maschera) 85%)}
.testata__corpo{padding:clamp(24px,5vw,72px) 0 clamp(44px,6vw,80px);max-width:940px}
.testata h1{font-weight:250;font-size:clamp(2.4rem, 1.2rem + 4.2vw, 5.2rem);line-height:.98;letter-spacing:-.025em;font-stretch:114%}
.testata__lead{margin:22px 0 0;max-width:50ch;font-size:1.1rem;color:var(--grafite)}
@media (max-width:760px){.testata__volta{opacity:.35}}

/* il percorso, sopra il titolo */
.briciole{margin:0 0 14px}
.briciole ol{display:flex;flex-wrap:wrap;align-items:center;gap:0 10px;font-size:.88rem;color:var(--cenere)}
.briciole li{display:inline-flex;align-items:center;gap:10px}
.briciole li + li::before{content:"/";color:var(--scorrimento)}
.briciole a{display:inline-flex;align-items:center;min-height:44px;color:var(--grafite)}
.briciole a:hover{color:var(--inchiostro)}

/* ---------- l'indice in cima ---------- */
.indice{padding:clamp(40px,5vw,64px) 0 0}
.indice__corpo{display:grid;grid-template-columns:minmax(0,3fr) minmax(0,9fr);gap:8px 48px;padding-top:16px;border-top:1px solid var(--inchiostro)}
.indice h2{font:600 .9rem/1.3 var(--testo);color:var(--cenere);padding-top:12px}
.indice ol{counter-reset:voce;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0 32px}
.indice li{counter-increment:voce;border-bottom:1px solid var(--filetto)}
.indice a{display:grid;grid-template-columns:28px minmax(0,1fr);align-items:center;min-height:48px;padding:6px 0;color:var(--inchiostro);text-decoration:none}
.indice a::before{content:counter(voce);font:500 .82rem/1 var(--mono);color:var(--cenere)}
.indice a:hover{color:var(--azione)}
.indice a:hover span{text-decoration:underline;text-underline-offset:.2em}

/* ---------- le voci: titolo a sinistra, testo a destra ---------- */
.sezione{padding:clamp(56px,7vw,104px) 0}
.voci{display:grid;gap:clamp(48px,6vw,88px)}
.voce{display:grid;grid-template-columns:minmax(0,3fr) minmax(0,9fr);gap:12px 48px;padding-top:18px;border-top:1px solid var(--inchiostro);scroll-margin-top:24px}
.voce > h2{font-weight:350;font-size:clamp(1.5rem, 1.2rem + .9vw, 2rem);line-height:1.15;letter-spacing:-.015em;font-stretch:108%}
.voce__corpo{min-width:0;max-width:52ch}
.voce__corpo > :last-child{margin-bottom:0}
.voce__attacco{font-size:1.18rem;line-height:1.45;color:var(--inchiostro)}
.voce h3{margin:1.6em 0 .5em;font:400 1.25rem/1.25 var(--titolo);letter-spacing:-.015em}
.voce strong{color:var(--inchiostro);font-weight:600}
.voce a{font-weight:600}
.puntata{margin:0 0 1.2em;border-top:1px solid var(--filetto)}
.puntata li{padding:12px 0;border-bottom:1px solid var(--filetto)}
.puntata strong{color:var(--inchiostro)}
.fonte{font-size:.88rem;color:var(--cenere)}
.fonte a{font-weight:400}

/* i passi del primo giorno: boa quadrata blu, come nella guida */
.giorno{counter-reset:passo;display:grid;gap:0;margin:0 0 1.2em;border-top:1px solid var(--filetto)}
.giorno li{counter-increment:passo;display:grid;grid-template-columns:28px minmax(0,1fr);gap:14px;padding:14px 0;border-bottom:1px solid var(--filetto)}
.giorno li::before{content:counter(passo);display:grid;place-items:center;width:28px;height:28px;background:var(--azione);color:var(--bianco);font:500 .9rem/1 var(--mono)}
.giorno p{margin:0}

/* il messaggio di una guardia, com'è scritto nel codice */
.messaggio{margin:.4em 0 1.4em;max-width:100%}
.messaggio__finestra{background:var(--term);border-radius:4px;padding:14px 16px 16px}
.messaggio__barra{margin:0 0 10px;font:400 .8rem/1.2 var(--mono);color:var(--term-cenere)}
.messaggio__esito{border:1px solid var(--term-guardia);padding:12px 14px}
.messaggio__esito b{display:block;margin:0 0 6px;font:600 .78rem/1.2 var(--mono);color:var(--term-tu)}
.messaggio__esito p{margin:0;font:400 .86rem/1.6 var(--mono);color:var(--term-guardia-testo);overflow-wrap:anywhere}
.messaggio--blocca .messaggio__esito{border-color:var(--term-blocca-bordo)}
.messaggio--blocca .messaggio__esito b{color:var(--term-blocca)}
.messaggio figcaption{margin-top:8px;font-size:.86rem;color:var(--cenere)}
.messaggio figcaption a{font-weight:400}

/* ---------- la tabella del confronto ---------- */
.confronto{width:100%;table-layout:fixed;border-collapse:collapse;font-size:.96rem;line-height:1.5}
.confronto caption{text-align:left;margin:0 0 14px;font-size:.9rem;color:var(--cenere)}
.confronto th,.confronto td{text-align:left;vertical-align:top;padding:14px 18px 14px 0;border-bottom:1px solid var(--filetto)}
.confronto thead th{padding-top:0;font:600 .92rem/1.3 var(--titolo);font-stretch:75%;color:var(--cenere);border-bottom:1px solid var(--inchiostro)}
.confronto thead th:last-child{color:var(--inchiostro)}
.confronto tbody th{font:600 .96rem/1.4 var(--testo);color:var(--inchiostro)}
.confronto td:last-child{color:var(--inchiostro)}
.confronto code{font-size:.86em}

/* ---------- domande ---------- */
.dentro--lato{display:grid;grid-template-columns:minmax(0,3fr) minmax(0,9fr);gap:0 48px;align-items:start}
.testa-lato{position:sticky;top:32px}
.testa-lato h2{font-weight:300;font-size:clamp(2.1rem, 1.3rem + 2.6vw, 3.6rem);line-height:1.02;letter-spacing:-.02em;font-stretch:112%}
.testa-lato h2 span{display:block;color:var(--cenere)}
.domande{border-top:1px solid var(--inchiostro)}
.domande details{border-bottom:1px solid var(--filetto)}
.domande summary{display:flex;align-items:center;justify-content:space-between;gap:24px;min-height:44px;padding:20px 0;cursor:pointer;list-style:none;font:400 clamp(1.08rem, 1rem + .3vw, 1.25rem)/1.3 var(--titolo);letter-spacing:-.01em;color:var(--inchiostro)}
.domande summary::-webkit-details-marker{display:none}
.domande summary svg{width:16px;height:16px;flex:none;transition:transform .25s cubic-bezier(.16,1,.3,1)}
.domande details[open] summary svg{transform:rotate(45deg)}
.domande summary:hover{color:var(--azione)}
.domande .risposta{padding:0 0 24px;max-width:66ch;color:var(--grafite)}
.domande .risposta p:last-child{margin:0}
@media (prefers-reduced-motion:reduce){.domande summary svg{transition:none}}

/* ---------- chiusura ---------- */
.vuoto{position:relative;background:var(--vuoto);color:var(--vuoto-testo);isolation:isolate}
.vuoto::before{content:"";position:absolute;inset:0;z-index:-1;opacity:.13;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='g'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 .55 0'/%3E%3C/filter%3E%3Crect width='180' height='180' filter='url(%23g)'/%3E%3C/svg%3E")}
.vuoto ::selection{background:var(--bianco);color:var(--vuoto)}
.vuoto :focus-visible{outline-color:var(--term-tu)}
.chiusura .dentro{display:grid;grid-template-columns:minmax(0,1fr);gap:24px;justify-items:start}
.chiusura .dentro > *{max-width:760px}
.chiusura h2{color:var(--bianco);font-weight:300;font-size:clamp(2.1rem, 1.3rem + 2.6vw, 3.6rem);line-height:1.02;letter-spacing:-.02em;font-stretch:112%}
.chiusura p{margin:16px 0 0;color:var(--vuoto-cenere);max-width:56ch}
.chiusura code{background:var(--vuoto-2);color:var(--bianco)}
.frase{width:100%;margin:0;padding:12px 14px;border:1px solid var(--vuoto-filetto);background:var(--vuoto-2);color:var(--bianco);font:400 .92rem/1.6 var(--mono);white-space:pre-wrap;overflow-wrap:break-word}
.chiusura__vie{display:flex;flex-wrap:wrap;gap:12px}
.chiusura .azione--chiara{background:var(--bianco);border-color:var(--bianco);color:var(--inchiostro)}
.chiusura .azione--chiara:hover{background:var(--cielo);border-color:var(--cielo)}
.chiusura .azione--bordo{color:var(--bianco);border-color:var(--bianco)}
.chiusura .azione--bordo:hover{background:var(--bianco);color:var(--inchiostro)}

/* un blocco a tutta larghezza, col titolo sopra un filetto */
.blocco{padding-top:18px;border-top:1px solid var(--inchiostro)}
.blocco > h2{margin-bottom:clamp(20px,3vw,32px);font-weight:350;font-size:clamp(1.5rem, 1.2rem + .9vw, 2rem);line-height:1.15;letter-spacing:-.015em;font-stretch:108%}
.blocco + .voci{margin-top:clamp(56px,7vw,104px)}
/* la frase da incollare in Claude Code, su fondo chiaro */
.frase--chiara{margin:.4em 0 1.2em;border:0;background:var(--bianco);color:var(--inchiostro);box-shadow:inset 0 0 0 1px var(--inchiostro)}

/* un comando da incollare nel terminale: una riga sola, che scorre se non ci sta */
.riga{margin:0 0 4px;padding:10px 12px;background:var(--term);color:var(--term-testo);border-radius:4px;font:400 .86rem/1.5 var(--mono);white-space:pre;overflow-x:auto}
.giorno .riga__nome{margin:12px 0 6px;font-size:.86rem;color:var(--cenere)}
.giorno .frase{margin:10px 0 0}

.piede{padding:32px 0 44px;font-size:.9rem;color:var(--cenere);border-top:1px solid var(--filetto)}
.piede .dentro{display:flex;flex-wrap:wrap;gap:8px 24px;justify-content:space-between}
.piede strong{color:var(--inchiostro)}
.piede p{margin:0}
.piede a{display:inline-block;padding:10px 0}

@media (max-width:860px){
  .indice ol{grid-template-columns:minmax(0,1fr)}
}
@media (max-width:760px){
  .indice__corpo,.voce,.dentro--lato{grid-template-columns:minmax(0,1fr)}
  .indice h2{padding-top:0}
  .testa-lato{position:static;margin-bottom:24px}
  .confronto caption{display:block}
  .confronto thead{display:none}
  .confronto,.confronto tbody,.confronto tr,.confronto th,.confronto td{display:block;width:100%}
  .confronto tr{padding:14px 0 6px;border-top:1px solid var(--inchiostro)}
  .confronto tbody th{padding:0 0 8px;border:0;font-size:1.05rem}
  .confronto td{padding:8px 0;border:0;border-top:1px solid var(--filetto)}
  .confronto td::before{content:attr(data-colonna);display:block;margin-bottom:2px;font:600 .82rem/1.3 var(--titolo);font-stretch:75%;color:var(--cenere)}
}
"""


def testo_puro(frammento: str) -> str:
    """Il testo visibile di un frammento HTML, per il JSON-LD e il conteggio delle parole."""
    t = re.sub(r"<[^>]+>", "", frammento)
    t = html.unescape(t)
    return re.sub(r"\s+", " ", t).strip()


def jsonld(oggetto) -> str:
    # ensure_ascii=False tiene gli accenti leggibili; "</" non compare mai nei testi.
    testo = json.dumps(oggetto, ensure_ascii=False, indent=1)
    assert "</" not in testo
    return '<script type="application/ld+json">\n' + testo + "\n</script>"


def grafo(p) -> dict:
    url = SITO + "/" + p["slug"] + "/"
    domande = [{
        "@type": "Question",
        "name": testo_puro(q),
        "acceptedAnswer": {"@type": "Answer", "text": testo_puro(r)},
    } for q, r in p["faq"]]
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "@id": url + "#pagina",
                "url": url,
                "name": p["title"],
                "description": p["desc"],
                "inLanguage": p["lang"],
                "dateModified": "2026-11-04",
                "isPartOf": {"@id": SITO + "/#sito"},
                "about": {"@id": SITO + "/#arturo"},
                "author": {"@id": SITO + "/#autore"},
                "breadcrumb": {"@id": url + "#percorso"},
            },
            {
                "@type": "BreadcrumbList",
                "@id": url + "#percorso",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Arturo", "item": SITO + "/"},
                    {"@type": "ListItem", "position": 2, "name": p["briciola"], "item": url},
                ],
            },
            {
                "@type": "FAQPage",
                "@id": url + "#domande",
                "inLanguage": p["lang"],
                "mainEntity": domande,
            },
        ],
    }


def head(p) -> str:
    url = SITO + "/" + p["slug"] + "/"
    t = html.escape(p["title"], quote=True)
    d = html.escape(p["desc"], quote=True)
    locale = "it_IT" if p["lang"] == "it" else "en_US"
    alterne = ""
    if p["lang"] == "en":
        alterne = ('<link rel="alternate" hreflang="it" href="' + SITO + '/">\n'
                   '<link rel="alternate" hreflang="en" href="' + url + '">\n'
                   '<link rel="alternate" hreflang="x-default" href="' + SITO + '/">\n')
    og_alt = ("Arturo, la stella sopra il reticolo blu della volta celeste" if p["lang"] == "it"
              else "Arturo, the star above the blue grid of the celestial vault")
    return f"""<!doctype html>
<html lang="{p['lang']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t}</title>
<meta name="description" content="{d}">
<link rel="canonical" href="{url}">
{alterne}<meta property="og:type" content="article">
<meta property="og:site_name" content="Arturo">
<meta property="og:locale" content="{locale}">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{d}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{OG_IMG}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{og_alt}">
<meta property="article:modified_time" content="2026-11-04">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{t}">
<meta name="twitter:description" content="{d}">
<meta name="twitter:image" content="{OG_IMG}">
{jsonld(grafo(p))}
<meta name="theme-color" content="#d7ebff">
<link rel="icon" href="{FAVICON}">
<link rel="preload" href="../font/archivo.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="../font/atkinson-next.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="../stile/colori.css">
<script defer data-domain="arturo.stellakamikaze.org" data-api="/api/e" src="/js/a.js"></script>
<script defer src="../traccia.js"></script>
<style>{CSS}</style>
</head>
"""


def testata(p) -> str:
    if p["lang"] == "it":
        menu = ('<a class="menu__voce" href="../">Cos\'è Arturo</a>\n'
                '        <a class="azione azione--scura stretta" href="../installa/">Installa</a>')
        marchio_label = "Arturo, pagina principale"
        percorso = "Percorso"
        salta = "Vai al contenuto"
    else:
        menu = ('<a class="menu__voce" href="../" hreflang="it">Arturo in Italian</a>\n'
                '        <a class="azione azione--scura stretta" href="../installa/" hreflang="it">Install</a>')
        marchio_label = "Arturo, home page (in Italian)"
        percorso = "Breadcrumb"
        salta = "Skip to content"
    return f"""<body>
<a class="salta" href="#contenuto">{salta}</a>

<header class="testata">
  <img class="testata__volta" src="../img/volta.svg" alt="" width="1600" height="1000">
  <nav class="menu" aria-label="{'Principale' if p['lang'] == 'it' else 'Main'}">
    <div class="dentro">
      <a class="marchio" href="../" aria-label="{marchio_label}">
        {MARCHIO}
        Arturo
      </a>
      <div class="menu__fine">
        {menu}
      </div>
    </div>
  </nav>
  <div class="dentro">
    <div class="testata__corpo">
      <nav class="briciole" aria-label="{percorso}">
        <ol>
          <li><a href="../">Arturo</a></li>
          <li aria-current="page">{p['briciola']}</li>
        </ol>
      </nav>
      <h1 id="titolo">{p['h1']}</h1>
      <p class="testata__lead">{p['lead']}</p>
    </div>
  </div>
</header>
"""


def indice(p) -> str:
    voci = "\n".join(f'        <li><a href="#{i}"><span>{t}</span></a></li>' for i, t in p["indice"])
    return f"""
<section class="indice" aria-labelledby="t-indice">
  <div class="dentro">
    <div class="indice__corpo">
      <h2 id="t-indice">In questa pagina</h2>
      <ol>
{voci}
      </ol>
    </div>
  </div>
</section>
"""


def faq(p) -> str:
    righe = []
    for q, r in p["faq"]:
        righe.append(f"""        <details>
          <summary>{q}{PIU}</summary>
          <div class="risposta"><p>{r}</p></div>
        </details>""")
    titolo = p.get("faq_titolo", "Domande.")
    return f"""
<section class="sezione" id="domande" aria-labelledby="t-domande" style="padding-top:0">
  <div class="dentro dentro--lato">
    <div class="testa-lato">
      <h2 id="t-domande">{titolo}</h2>
    </div>
    <div class="domande">
{chr(10).join(righe)}
    </div>
  </div>
</section>
"""


def chiusura_it() -> str:
    return """
<section class="sezione vuoto chiusura" aria-labelledby="t-comincia">
  <div class="dentro">
    <div>
      <h2 id="t-comincia">Per cominciare</h2>
      <p>Installa Claude Code, aprilo e incolla questa frase. Claude legge la pagina del link, scarica Arturo e ti chiede un sì prima di ogni passo. Alla fine scrivi <code>/exit</code>, poi <code>claude</code>, poi <code>/setup</code>.</p>
    </div>
    <pre class="frase">Installa Arturo: https://<wbr>arturo.stellakamikaze.org/<wbr>inizia/</pre>
    <div class="chiusura__vie">
      <a class="azione azione--chiara" href="../installa/">Guida passo per passo</a>
      <a class="azione azione--bordo" href="../">Cos'è Arturo</a>
    </div>
  </div>
</section>
"""


def piede(p) -> str:
    if p["lang"] == "it":
        riga = ('<p>Niente cookie, nessun tracker di terzi, nessun font da server esterni. '
                '<a href="../privacy/">Privacy</a> · <a href="../feedback/">Dimmi com\'è andata</a></p>')
        firma = "<p><strong>Progetto di Federico Nejrotti.</strong> Licenza MIT. "
    else:
        riga = ('<p>No cookies, no third-party trackers, no fonts from external servers. '
                '<a href="../privacy/" hreflang="it">Privacy (in Italian)</a></p>')
        firma = "<p><strong>A project by Federico Nejrotti.</strong> MIT license. "
    return f"""
<footer class="piede">
  <div class="dentro">
    {firma}<a href="https://github.com/stellakamikaze/arturo">github.com/stellakamikaze/arturo</a></p>
    {riga}
  </div>
</footer>

<script type="module" src="../note.js"></script>
</body>
</html>
"""


def voce(ident, titolo, corpo) -> str:
    return f"""
      <article class="voce" id="{ident}" aria-labelledby="t-{ident}">
        <h2 id="t-{ident}">{titolo}</h2>
        <div class="voce__corpo">
{corpo}
        </div>
      </article>
"""


def pagina(p) -> str:
    corpo = head(p) + testata(p) + '\n<main id="contenuto">\n'
    if p.get("indice"):
        corpo += indice(p)
    corpo += p["main"]
    corpo += faq(p)
    if p["lang"] == "it":
        corpo += chiusura_it()
    else:
        corpo += p.get("chiusura", "")
    corpo += "\n</main>\n" + piede(p)
    return corpo
