"""Costruisce sito/mestieri/index.html da docs/mestieri.md di dev (16/11/2026, #4537).
uso: python3 genera_mestieri.py MESTIERI_MD MODELLO_ORGANIZZAZIONI USCITA"""
import html
import re
import sys
from pathlib import Path

md = Path(sys.argv[1]).read_text(encoding="utf-8")
modello = Path(sys.argv[2]).read_text(encoding="utf-8")
uscita = Path(sys.argv[3])

# Le parole che dicono che una voce "(Scoperta)" è una forma nuova (sintesi o pagina), non ancora rilasciata.
FORME = ("pagina", "sintesi", "calendario editoriale", "galleria", "lezione interattiva", "simulatore", "cruscotto",
         "linea del tempo")


def maiuscola(t: str) -> str:
    return t[:1].upper() + t[1:] if t and t[0].islower() else t


def inline(t: str) -> str:
    t = html.escape(maiuscola(t), quote=False)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', t)
    return t


def stato(voce: str):
    """(testo senza la marca, etichetta, classe)."""
    voce = voce.rstrip(";.").strip()
    m = re.search(r"\s*\(([^)]*)\)$", voce)
    marca = m.group(1) if m else ""
    testo = voce[: m.start()] if m else voce
    if marca.startswith("oggi"):
        return testo + ".", "Oggi", "stato--oggi"
    if marca == "Scoperta":
        if any(p in testo.lower() for p in FORME):
            return testo + ".", "Nella prossima versione", "in-arrivo"
        return testo + ".", "Scoperta", "stato--scoperta"
    return testo + ".", "", ""


famiglie = []
for blocco in re.split(r"(?m)^## ", md)[1:]:
    titolo, _, corpo = blocco.partition("\n")
    m = re.match(r"(\d)\. (.+)", titolo.strip())
    if not m:
        continue
    fam = {"titolo": m.group(2), "campi": [], "voci": []}
    in_cosa = False
    for riga in corpo.splitlines():
        c = re.match(r"\*\*(Chi|Materiali|In chat|Lavori che tornano):\*\* (.+)", riga)
        if c:
            fam["campi"].append((c.group(1), c.group(2)))
            in_cosa = False
            continue
        if riga.startswith("**Cosa può fare Arturo:**"):
            in_cosa = True
            continue
        if riga.startswith("**Le domande"):
            in_cosa = False
            continue
        if in_cosa and riga.startswith("- "):
            voce = riga[2:].strip()
            # Una voce con "(oggi). " a metà porta due stati: diventa due voci.
            for pezzo in re.split(r"(?<=\(oggi\))\.\s+", voce):
                fam["voci"].append(stato(pezzo))
    famiglie.append(fam)
assert len(famiglie) == 6, f"famiglie lette: {len(famiglie)}"

testa = modello[: modello.index("</style>")]
DESCRIZIONE = ("Sei famiglie di mestieri della conoscenza, dalla parola all'archivio: per ognuna i materiali, i "
               "lavori che tornano e cosa fa Arturo, oggi e nella prossima versione.")
testa = re.sub(r"<title>.*?</title>", "<title>I mestieri della conoscenza · Arturo</title>", testa)
testa = testa.replace("Arturo per organizzazioni · cosa vale già oggi", "I mestieri della conoscenza · Arturo")
testa = re.sub(r'(content=")Arturo in uno studio[^"]*(")', lambda m: m.group(1) + DESCRIZIONE + m.group(2), testa)
testa = testa.replace("/organizzazioni/", "/mestieri/")

STILE = """
/* ---------- i mestieri ---------- */
.famiglia{padding:clamp(48px,7vw,96px) 0;border-top:1px solid var(--filetto)}
.famiglia:nth-of-type(even){background:var(--carta-2)}
.famiglia .dentro{display:grid;grid-template-columns:minmax(0,4fr) minmax(0,8fr);gap:24px var(--fra-lati, 48px)}
.famiglia h2{font-weight:300;font-size:clamp(1.9rem, 1.2rem + 2.2vw, 3rem);line-height:1.05;letter-spacing:-.02em;font-stretch:112%}
.campi{display:grid;grid-template-columns:minmax(0,10rem) minmax(0,1fr);gap:12px 24px;margin:0 0 28px}
.campi dt{font:600 .9rem/1.5 var(--testo);color:var(--inchiostro)}
.campi dd{margin:0;color:var(--grafite)}
.famiglia h3{margin:0 0 4px;padding-top:20px;border-top:1px solid var(--inchiostro);font-size:1.2rem;font-weight:400;letter-spacing:-.015em}
.voci li{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:4px 20px;align-items:baseline;padding:14px 0;border-bottom:1px solid var(--filetto)}
.voci li p{margin:0;color:var(--grafite)}
.voci li > span{justify-self:start}
.stato{font:600 .8rem/1.2 var(--testo);white-space:nowrap;color:var(--inchiostro)}
.stato--oggi{color:var(--grafite)}
.stato--scoperta{color:var(--azione-giu)}
.in-arrivo{display:inline-block;padding:4px 8px;background:var(--bianco);box-shadow:inset 0 0 0 1px var(--inchiostro);font:600 .78rem/1.2 var(--testo);color:var(--inchiostro);white-space:nowrap}
.legenda{display:flex;flex-wrap:wrap;gap:12px 24px;margin:28px 0 0;align-items:center;font-size:.92rem;color:var(--grafite)}
.legenda li{display:flex;gap:8px;align-items:center}
.controllo{padding:clamp(48px,7vw,96px) 0;border-top:1px solid var(--filetto)}
.controllo p{max-width:62ch;margin-top:20px}
.controllo h2{font-weight:300;font-size:clamp(1.9rem, 1.2rem + 2.2vw, 3rem);line-height:1.05;letter-spacing:-.02em;font-stretch:112%}
@media (max-width:760px){
  .famiglia .dentro,.campi,.voci li{grid-template-columns:minmax(0,1fr)}
  .campi{gap:4px}
  .campi dd{margin-bottom:12px}
}
"""

corpo = ['</style>\n<script defer data-domain="arturo.stellakamikaze.org" data-api="/api/e" src="/js/a.js"></script>',
         '<script defer src="../traccia.js"></script>\n</head>\n<body>\n<a class="salta" href="#famiglie">Vai al contenuto</a>\n']
corpo.append(modello[modello.index('<header class="testata">'): modello.index('<div class="dentro">\n    <div class="testata__corpo">')])
corpo.append("""<div class="dentro">
    <div class="testata__corpo">
      <h1 id="titolo">I mestieri della conoscenza</h1>
      <p>Arturo è pensato per chi raccoglie materiali e ne ricava un lavoro da consegnare a qualcun altro. Questa pagina divide quel lavoro in sei famiglie. Per ognuna dice che materiali usa, cosa si chiede di solito all'IA in chat, quali lavori tornano e cosa può fare Arturo. Una persona può stare in più famiglie: chi insegna spesso scrive anche, chi produce eventi spesso cura.</p>
      <ul class="legenda" aria-label="Gli stati delle voci">
        <li><span class="stato stato--oggi">Oggi</span> Claude lo fa già, se glielo chiedi</li>
        <li><span class="stato stato--scoperta">Scoperta</span> Arturo te lo propone da solo, quando vede il lavoro tornare</li>
        <li><span class="in-arrivo">Nella prossima versione</span> è pronto e arriva col prossimo rilascio</li>
      </ul>
    </div>
  </div>
</header>

<main id="famiglie">
""")
for fam in famiglie:
    ident = re.sub(r"[^a-z]+", "-", fam["titolo"].lower().replace("'", " ").replace("à", "a")).strip("-")
    corpo.append(f'<section class="famiglia" id="{ident}" aria-labelledby="t-{ident}">\n  <div class="dentro">\n'
                 f'    <h2 id="t-{ident}">{inline(fam["titolo"])}</h2>\n    <div>\n      <dl class="campi">\n')
    for nome, valore in fam["campi"]:
        corpo.append(f"        <dt>{nome}</dt><dd>{inline(valore)}</dd>\n")
    corpo.append('      </dl>\n      <h3>Cosa fa Arturo</h3>\n      <ul class="voci">\n')
    for testo, etichetta, classe in fam["voci"]:
        segno = (f'<span class="{classe}">{etichetta}</span>' if classe == "in-arrivo"
                 else f'<span class="stato {classe}">{etichetta}</span>' if etichetta else "")
        corpo.append(f"        <li><p>{inline(testo)}</p>{segno}</li>\n")
    corpo.append("      </ul>\n    </div>\n  </div>\n</section>\n\n")

corpo.append("""<section class="controllo" aria-labelledby="t-controllo">
  <div class="dentro">
    <h2 id="t-controllo">Chi controlla il risultato</h2>
    <p>Claude fa la raccolta e il primo ordine, ma il controllo del risultato resta a chi conosce il mestiere. Anche la ricerca di Anthropic sulle sessioni di Claude Code dice che conta più conoscere il proprio mestiere che saper programmare (<a href="https://www.anthropic.com/research/claude-code-expertise">Agentic coding and persistent returns to expertise</a>, giugno 2026).</p>
  </div>
</section>

<section class="sezione vuoto chiusura" aria-labelledby="t-comincia">
  <div class="dentro">
    <div>
      <h2 id="t-comincia">Il tuo mestiere non c'è?</h2>
      <p>Scrivimi cosa fai e quale lavoro ti torna ogni settimana: le famiglie crescono con le risposte di chi usa Arturo.</p>
    </div>
    <div class="chiusura__vie">
      <a class="azione azione--chiara" href="../feedback/">Scrivimelo</a>
      <a class="azione azione--bordo" href="../installa/">Installa Arturo</a>
    </div>
  </div>
</section>

</main>
""")
corpo.append(modello[modello.index('<footer class="piede">'): modello.index("</footer>") + len("</footer>")])
corpo.append('\n\n<script type="module" src="../note.js"></script>\n</body>\n</html>\n')

testo = testa + STILE + "".join(corpo)
testo = testo.replace('<a class="menu__voce" href="../">Cos\'è Arturo</a>', '<a class="menu__voce" href="../">Cos\'è Arturo</a>')
uscita.parent.mkdir(parents=True, exist_ok=True)
uscita.write_text(testo, encoding="utf-8")
print(f"{uscita}: {len(famiglie)} famiglie, {sum(len(f['voci']) for f in famiglie)} voci")
for f in famiglie:
    print(" ", f["titolo"], [e for _, e, _ in f["voci"]])
