#!/usr/bin/env python3
"""Banco della pagina-link /inizia/ e delle pagine che la nominano (1/11/2026).

La persona incolla in Claude Code "Installa Arturo: https://arturo.stellakamikaze.org/inizia/".
Claude legge la pagina con WebFetch, che la passa a un modello piccolo: per questo la pagina ha
pochi comandi, ognuno su una riga, niente script e niente testo nascosto. Il banco controlla la
pagina, la frase uguale nelle altre copie del sito, la guida in cinque passi con la strada a mano,
le FAQ della home uguali al JSON-LD, il server e il controllo di pubblica.sh.

Il README di origin/main di arturo non si confronta qui: al 1/11/2026 non ha ancora la frase.
Al suo posto la sezione "Dopo" deve nominare Anthropic, telemetria, .ssh, .env e password manager.

Le frasi comuni (review dell'ingresso, 1/11/2026) devono coincidere alla lettera con quelle di
arturo: CRONOLOGIA nella sezione "Dopo", IMPOSTAZIONI_PRIMA in "Per te", nella home e in llms.txt.
I 90 giorni sono cleanupPeriodDays del settings.json di arturo: se cambia lì, cambia qui.

--avvelena il banco lo prova da solo: per ogni veleno copia i file letti dai casi in una cartella
temporanea, rompe un file (spesso rimettendo il testo di prima della review) e vuole il caso rosso
col suo motivo. Esce 1 solo se tutti i veleni sono rossi col motivo giusto. Un veleno verde, o
rosso per un altro motivo, fa uscire 0: così il gate lo legge come "veleno verde".
"""
import argparse
import html
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

FRASE = "Installa Arturo: https://arturo.stellakamikaze.org/inizia/"
# I comandi della pagina, alla lettera: uno per <pre>, ognuno su una riga.
COMANDI = {
    "winget install --id Git.Git -e --source winget",
    'curl -fsSL https://arturo.stellakamikaze.org/installa.sh -o "$HOME/.arturo-installa.sh"',
    'curl -fsSL https://raw.githubusercontent.com/stellakamikaze/arturo/landing-v2/sito/installa.sh | cmp - "$HOME/.arturo-installa.sh" && echo UGUALE',
    'bash "$HOME/.arturo-installa.sh"',
    "! bash ~/.arturo-installa.sh",
}
MAX_PAROLE = 650
CRONOLOGIA = ("Quello che leggo resta nella cronologia di questa conversazione, che Claude Code tiene sul tuo "
              "computer e cancella da sola dopo 90 giorni. Arturo non ne fa altre copie.")
IMPOSTAZIONI_PRIMA = ("Il tuo accesso e le tue conversazioni restano dove sono, e i plugin restano installati. "
                      "Il settings.json che avevi va nella copia con la data: /setup ti propone di riportare "
                      "hook, plugin e preferenze.")
RIGA_GUIDA = "Non hai ancora Claude Code? Parti dalla guida: installa/"
# I file del sito toccati dall'ingresso col link: qui niente virgolette basse o curve. Il resto di
# sito/ (novità, privacy, feedback) ne ha ancora, e una voce delle novità cita una virgoletta curva
# come fatto: si sistemano a parte.
SENZA_VIRGOLETTE = ("sito/index.html", "sito/inizia/index.html", "sito/installa/index.html", "sito/llms.txt",
                    "sito/setup/index.html", "sito/js/home.js", "sito/js/installa-1.js", "sito/js/installa-2.js",
                    "PRODUCT.md", "DESIGN.md", "strumenti/pubblica.sh")
# I file che i casi leggono: --avvelena li copia, poi ne rompe uno.
LETTI = SENZA_VIRGOLETTE + ("sito/sitemap.xml", "server/arturo-sito.conf")
VIRGOLETTE = re.compile("[«»“”„‘’]")


def leggi(repo, percorso):
    f = repo / percorso
    assert f.is_file(), f"manca {percorso}"
    return f.read_text(encoding="utf-8")


def testo(frammento, fra=" "):
    """Il testo visibile di un frammento HTML, con gli spazi ridotti. fra: cosa prende il posto dei tag."""
    senza = re.sub(r"<[^>]+>", fra, frammento)
    return re.sub(r"\s+", " ", html.unescape(senza)).strip()


def sezione(pagina, titolo):
    m = re.search(r"<h2>" + re.escape(titolo) + r"</h2>(.*?)(?=<h2>|</main>)", pagina, re.S)
    assert m, f"manca la sezione {titolo}"
    return testo(m.group(1))


# ---------- la pagina /inizia/ ----------

def caso_niente_nascosto(repo):
    p = leggi(repo, "sito/inizia/index.html")
    for vietato in ("<script", "display:none", "display: none", "aria-hidden", "<!--", "visibility:hidden"):
        assert vietato not in p, f"la pagina contiene {vietato}"
    assert not re.search(r"<[^>]+\shidden[\s>=]", p), "la pagina ha un elemento hidden"


def caso_comandi_pagina(repo):
    p = leggi(repo, "sito/inizia/index.html")
    pre = [html.unescape(x) for x in re.findall(r"<pre>(.*?)</pre>", p, re.S)]
    a_capo = [x for x in pre if "\n" in x]
    assert not a_capo, f"comandi su più righe: {a_capo}"
    assert set(pre) == COMANDI and len(pre) == len(COMANDI), \
        f"comandi diversi: in più {sorted(set(pre) - COMANDI)}, mancano {sorted(COMANDI - set(pre))}"


def caso_niente_scorciatoie(repo):
    grezza = leggi(repo, "sito/inizia/index.html")
    p = testo(grezza)
    assert "| bash" not in p, "la pagina contiene | bash"
    for parola in ("ignora", "bypass"):
        assert parola not in p.lower(), f"la pagina contiene {parola}"
    # sudo compare solo nel divieto: ogni voce o paragrafo che lo nomina comincia con "Non usare sudo"
    for blocco in re.findall(r"<(?:li|p|pre)>(.*?)</(?:li|p|pre)>", grezza, re.S):
        frase = testo(blocco)
        if re.search(r"\bsudo\b", frase):
            assert frase.startswith("Non usare sudo"), f"sudo come istruzione: {frase}"


def caso_parole(repo):
    p = leggi(repo, "sito/inizia/index.html")
    corpo = re.search(r"<body>(.*)</body>", p, re.S).group(1)
    n = len(testo(corpo).split())
    assert n < MAX_PAROLE, f"{n} parole, il tetto è {MAX_PAROLE}"


def passo(pagina, parola):
    """Il testo della voce <li> della pagina che contiene parola."""
    voci = [testo(v) for v in re.findall(r"<li>(.*?)</li>", pagina, re.S) if parola in v]
    assert len(voci) == 1, f"voci con {parola}: {len(voci)}, attesa 1"
    return voci[0]


def caso_dopo(repo):
    dopo = sezione(leggi(repo, "sito/inizia/index.html"), "Dopo")
    for parola in ("Anthropic", "telemetria", ".ssh", ".env", "password manager"):
        assert parola in dopo, f'la sezione "Dopo" non nomina {parola}'
    # R4: la conversazione di /setup resta nella cronologia di Claude Code, non "solo il CLAUDE.md".
    assert "resta solo" not in dopo, 'la sezione "Dopo" promette che resta solo il CLAUDE.md'
    assert CRONOLOGIA in dopo, 'la sezione "Dopo" non ha la frase comune sulla cronologia'


def caso_impostazioni_prima(repo):
    """I3: il settings.json di prima va nella copia, e le pagine lo dicono con la stessa frase."""
    assert IMPOSTAZIONI_PRIMA in sezione(leggi(repo, "sito/inizia/index.html"), "Per te"), \
        'la sezione "Per te" non ha la frase comune sulle impostazioni di prima'
    assert IMPOSTAZIONI_PRIMA in testo(leggi(repo, "sito/index.html"), ""), \
        "la home non ha la frase sulle impostazioni di prima"
    assert IMPOSTAZIONI_PRIMA in leggi(repo, "sito/llms.txt"), "llms.txt non ha la frase sulle impostazioni di prima"
    for percorso in ("sito/inizia/index.html", "sito/index.html", "sito/llms.txt"):
        t = testo(leggi(repo, percorso))
        for vecchia in ("plugin restano dove sono", "e i plugin. I file", "plugin di Claude Code, che non tocca"):
            assert vecchia not in t, f"{percorso} promette ancora: {vecchia}"


def caso_ingresso_persone(repo):
    """F1: chi arriva dal browser va alla guida; /inizia/ è scritta per Claude e lo dice in apertura."""
    h = leggi(repo, "sito/index.html")
    m = re.search(r'<div class="promessa__via">.*?<a class="azione azione--grande[^"]*" href="([^"]+)"', h, re.S)
    assert m, "manca il pulsante principale della home"
    assert m.group(1) == "installa/", f"il pulsante principale della home non porta alla guida: {m.group(1)}"
    assert 'href="inizia/"' not in h, "la home ha ancora un link a inizia/"
    p = leggi(repo, "sito/inizia/index.html")
    m = re.search(r"</h1>\s*<p>(.*?)</p>", p, re.S)
    assert m and testo(m.group(1)).startswith(RIGA_GUIDA), "manca la riga per chi non ha Claude Code"
    assert 'href="https://arturo.stellakamikaze.org/installa/"' in m.group(1), \
        "la riga per chi non ha Claude Code non porta alla guida"


def caso_attesa_cache(repo):
    """F7: raw.githubusercontent.com tiene una cache di circa 5 minuti: si aspetta e si riprova una volta."""
    v = passo(leggi(repo, "sito/inizia/index.html"), "echo UGUALE")
    i, j = v.find("aspetta 5 minuti"), v.find("fermati")
    assert i >= 0 and "una volta sola" in v, "il confronto non fa aspettare 5 minuti e riprovare una volta"
    assert i < j, "il confronto fa fermare Claude prima di aspettare e riprovare"
    s = leggi(repo, "strumenti/pubblica.sh")
    k = s.index("  applica)")
    assert "5 minuti" in s[k:] and "cmp -s" in s[k:], \
        "pubblica.sh applica non rifà il confronto e non ricorda i 5 minuti"


def caso_windows(repo):
    """F2: su Windows la pagina non dà istruzioni su python, segue le righe MANCA dello script."""
    p = leggi(repo, "sito/inizia/index.html")
    assert "python" not in testo(p).lower(), "la pagina dà istruzioni su python"
    manca = passo(p, "MANCA")
    assert "segui quelle righe" in manca and "riaprire Claude Code" in manca, \
        "il passo MANCA non dice di seguire le righe dello script"
    git = passo(p, "Git.Git")
    assert "PowerShell" in git and "finestra nuova" in git, \
        "dopo winget il riavvio non chiede una finestra nuova di PowerShell"


# ---------- la frase nelle altre copie ----------

def caso_frase_ovunque(repo):
    for percorso in ("sito/index.html", "sito/installa/index.html", "sito/llms.txt", "sito/setup/index.html"):
        assert FRASE in html.unescape(leggi(repo, percorso)), f"{percorso} non cita la frase con /inizia/"


def caso_virgolette(repo):
    for percorso in SENZA_VIRGOLETTE:
        for i, riga in enumerate(leggi(repo, percorso).splitlines(), 1):
            m = VIRGOLETTE.search(riga)
            assert not m, f"{percorso}:{i} virgoletta {m.group(0)!r}"


# ---------- la guida in cinque passi ----------

def caso_guida_cinque(repo):
    g = leggi(repo, "sito/installa/index.html")
    tappe = re.findall(r'<li class="tappa" id="tappa-(\d+)"', g)
    assert tappe == ["1", "2", "3", "4", "5"], f"tappe {tappe}, attese 1-5"
    assert "dieci passi" not in g.lower() and "un'ora" not in g, "la guida dice ancora dieci passi o un'ora"
    for js in ("sito/js/installa-1.js", "sito/js/home.js"):
        s = leggi(repo, js)
        assert "'arturo-setup-2'" in s and "TOTALE=5" in s, f"{js}: chiave o totale vecchi"
        assert "arturo-setup-1" not in s, f"{js}: chiave vecchia"
    s = leggi(repo, "sito/js/installa-1.js")
    assert "'#tappa-5'" in s and "a-mano" in s, "manca l'alias #tappa-5 verso #a-mano"


def caso_a_mano(repo):
    g = leggi(repo, "sito/installa/index.html")
    m = re.search(r'<section class="a-mano" id="a-mano".*?</section>', g, re.S)
    assert m, 'manca <section id="a-mano">'
    mano = html.unescape(m.group(0))
    assert "for x in" in mano and "CLAUDE.md" in mano, "il blocco for x in non sta in #a-mano"
    assert "Self-Modification" in mano, "la nota Self-Modification non sta in #a-mano"
    fuori = g[:m.start()] + g[m.end():]
    assert "Git Bash" not in fuori, "Git Bash fuori da #a-mano nella guida"
    for percorso in ("sito/index.html", "sito/inizia/index.html"):
        assert "Git Bash" not in leggi(repo, percorso), f"{percorso} nomina Git Bash"
    llms = leggi(repo, "sito/llms.txt")
    i = llms.find("### A mano")
    assert i >= 0, "llms.txt: manca la sezione A mano"
    assert "Git Bash" not in llms[:i], "llms.txt nomina Git Bash prima della strada a mano"
    assert "tappa-5" not in llms and "dieci passi" not in llms, "llms.txt: #tappa-5 o dieci passi"


# ---------- la home ----------

def caso_faq_uguali(repo):
    h = leggi(repo, "sito/index.html")
    j = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', h, re.S).group(1))
    nodi = {n["@type"]: n for n in j["@graph"]}
    app = nodi["SoftwareApplication"]
    assert app["installUrl"] == "https://arturo.stellakamikaze.org/inizia/", "installUrl non è /inizia/"
    assert app["softwareRequirements"] == "Claude Code", "softwareRequirements diverso da Claude Code"
    assert app["operatingSystem"] == "macOS, Windows, Linux", "operatingSystem diverso"
    json_ld = [(q["name"], q["acceptedAnswer"]["text"]) for q in nodi["FAQPage"]["mainEntity"]]
    visibili = [(testo(s, ""), testo(r, "")) for s, r in re.findall(
        r'<details>\s*<summary>(.*?)</summary>\s*<div class="risposta">(.*?)</div>\s*</details>', h, re.S)]
    assert visibili == json_ld, f"FAQ diverse: visibili {visibili} JSON-LD {json_ld}"
    domande = [d for d, _ in json_ld]
    for d in ("Serve saper programmare?", "Cosa legge Claude sul mio computer?", "Posso farlo a mano?"):
        assert d in domande, f"manca la domanda {d}"
    assert "un'ora" not in h.lower(), "la home dice ancora un'ora"


def caso_carte(repo):
    h = leggi(repo, "sito/index.html")
    carte = re.search(r'<ol class="carte" id="carte">(.*?)</ol>', h, re.S).group(1)
    assert carte.count('<li class="carta"') == 3, "le carte di Installalo non sono tre"
    assert f'<pre id="c-frase">{FRASE}</pre>' in carte and 'data-copia="c-frase"' in carte, "manca la frase da copiare"
    assert "installa.sh" not in carte, "le carte danno ancora la riga di installa.sh"


# ---------- server, sitemap, rimandi, pubblicazione ----------

def caso_server(repo):
    c = leggi(repo, "server/arturo-sito.conf")
    assert re.search(r"location = /inizia \{[^}]*try_files /inizia/index\.html =404;", c), "manca location = /inizia"
    assert "charset utf-8;" in c and "charset_types text/plain text/html;" in c, "manca il charset"
    assert re.search(r"location = /installa\.sh \{(?:[^{}]|\{\s*\})*?default_type text/plain;", c), "installa.sh non è text/plain"


def caso_rimandi(repo):
    s = leggi(repo, "sito/setup/index.html")
    assert 'url=../installa/' in s and 'canonical" href="https://arturo.stellakamikaze.org/installa/"' in s, \
        "setup/ non porta alla guida installa/"
    assert "<loc>https://arturo.stellakamikaze.org/inizia/</loc>" in leggi(repo, "sito/sitemap.xml"), "la sitemap non ha /inizia/"


def caso_pubblica_punta(repo):
    p = leggi(repo, "strumenti/pubblica.sh")
    i = p.index("  prepara)")
    j = p.index("git -C \"$RADICE\" -c core.autocrlf=false archive", i)
    assert "origin/landing-v2" in p[i:j], "prepara non controlla la punta di origin/landing-v2 prima di caricare"


CASI = [caso_niente_nascosto, caso_comandi_pagina, caso_niente_scorciatoie, caso_parole, caso_dopo,
        caso_impostazioni_prima, caso_ingresso_persone, caso_attesa_cache, caso_windows,
        caso_frase_ovunque, caso_virgolette, caso_guida_cinque, caso_a_mano, caso_faq_uguali, caso_carte,
        caso_server, caso_rimandi, caso_pubblica_punta]

INIZIA = "sito/inizia/index.html"


def togli(da, a):
    """Un veleno che taglia il testo da `da` ad `a` compreso."""
    return lambda s: re.sub(re.escape(da) + ".*?" + re.escape(a), "", s, count=1, flags=re.S)


def sostituisci(vecchio, nuovo):
    return lambda s: s.replace(vecchio, nuovo)


# (nome, file rotto, come si rompe, caso, motivo atteso del rosso). I veleni F/R/I rimettono il testo
# di prima della review dell'ingresso (1/11/2026).
VELENI = [
    ("un comando in più", INIZIA, sostituisci(
        "<pre>! bash ~/.arturo-installa.sh</pre>", "<pre>! bash ~/.arturo-installa.sh</pre>\n<pre>sh ~/.arturo-installa.sh</pre>"),
     caso_comandi_pagina, "comandi diversi"),
    ("un URL diverso", INIZIA, sostituisci(
        "https://arturo.stellakamikaze.org/installa.sh -o", "https://arturo.example.org/installa.sh -o"),
     caso_comandi_pagina, "comandi diversi"),
    ("R4 resta solo il CLAUDE.md", INIZIA, lambda p: re.sub(
        r"Claude te lo dice così: .*? prima che venga salvato\.",
        "Sul computer resta solo il tuo CLAUDE.md, e lo approvi tu prima che venga salvato.", p, flags=re.S),
     caso_dopo, "resta solo il CLAUDE.md"),
    ("I3 plugin restano dove sono", INIZIA, sostituisci(
        IMPOSTAZIONI_PRIMA, "Restano dove sono il tuo accesso, le tue conversazioni e i plugin."),
     caso_impostazioni_prima, "frase comune sulle impostazioni di prima"),
    ("I3 la home dice che non tocca", "sito/index.html", sostituisci(
        "Il tuo accesso e le tue conversazioni restano dove sono, e i plugin restano installati.", "che non tocca."),
     caso_impostazioni_prima, "la home non ha la frase"),
    ("F1 pulsante della home su inizia/", "sito/index.html", sostituisci(
        '<a class="azione azione--grande stretta" href="installa/">', '<a class="azione azione--grande stretta" href="inizia/">'),
     caso_ingresso_persone, "il pulsante principale della home non porta alla guida"),
    ("F1 senza la riga per chi non ha Claude Code", INIZIA, togli("<p>Non hai ancora Claude Code?", "</p>\n"),
     caso_ingresso_persone, "manca la riga per chi non ha Claude Code"),
    ("F1 setup/ rimanda a inizia/", "sito/setup/index.html", sostituisci("installa/", "inizia/"),
     caso_rimandi, "setup/ non porta alla guida"),
    ("F7 si ferma subito", INIZIA, sostituisci(
        "aspetta 5 minuti per la cache di GitHub e rilancia i due comandi, una volta sola. Se ancora no, fermati", "fermati"),
     caso_attesa_cache, "non fa aspettare 5 minuti"),
    ("F7 pubblica.sh senza confronto", "strumenti/pubblica.sh", togli("    # Il confronto di /inizia/", "    fi\n"),
     caso_attesa_cache, "pubblica.sh applica non rifà il confronto"),
    ("F2 istruzione python su Windows", INIZIA, sostituisci(
        "<li>Se lo script stampa righe", "<li>Su Windows installa python3 da python.org.</li>\n<li>Se lo script stampa righe"),
     caso_windows, "istruzioni su python"),
    ("F2 riavvio nella stessa finestra", INIZIA, sostituisci(
        "di chiudere PowerShell, aprire una finestra nuova, scrivere <code>claude</code> e",
        "di chiudere Claude Code, riaprirlo e"),
     caso_windows, "finestra nuova"),
    ("F8 virgolette basse in PRODUCT.md", "PRODUCT.md", sostituisci(
        '"update automatico è acceso di default"', "\u00abupdate automatico è acceso di default\u00bb"),
     caso_virgolette, "PRODUCT.md:"),
    ("F8 virgolette basse in DESIGN.md", "DESIGN.md", sostituisci(
        '"Sessione di esempio"', "\u00abSessione di esempio\u00bb"),
     caso_virgolette, "DESIGN.md:"),
]


def main():
    for flusso in (sys.stdout, sys.stderr):
        try:
            flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument("--avvelena", action="store_true",
                    help="prova i casi su copie rotte dei file: ogni veleno deve dare rosso col suo motivo")
    a = ap.parse_args()
    repo = Path(a.repo)
    if a.avvelena:
        return avvelena(repo)
    passati = 0
    for caso in CASI:
        try:
            caso(repo)
            passati += 1
            print(f"PASS {caso.__name__}")
        except AssertionError as e:
            print(f"FAIL {caso.__name__}: {e}")
    print(f"inizia: {passati}/{len(CASI)}")
    return 0 if passati == len(CASI) else 1


def avvelena(repo):
    rossi = 0
    with tempfile.TemporaryDirectory() as t:
        for n, (nome, percorso, guasta, caso, motivo) in enumerate(VELENI):
            copia = Path(t) / str(n)
            for f in LETTI:
                (copia / f).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(repo / f, copia / f)
            prima = leggi(copia, percorso)
            rotta = guasta(prima)
            if rotta == prima:
                print(f"GUASTO {caso.__name__} ({nome}): il veleno non cambia {percorso}")
                continue
            (copia / percorso).write_text(rotta, encoding="utf-8", newline="\n")
            try:
                caso(copia)
                print(f"VELENO VERDE {caso.__name__} ({nome})")
            except AssertionError as e:
                if motivo in str(e):
                    rossi += 1
                    print(f"FAIL {caso.__name__} ({nome}): {e}")
                else:
                    print(f"VELENO ROSSO PER UN ALTRO MOTIVO {caso.__name__} ({nome}): {e}; atteso {motivo!r}")
    print(f"inizia: {rossi}/{len(VELENI)} veleni rossi col motivo atteso (veleno)")
    return 1 if rossi == len(VELENI) else 0


if __name__ == "__main__":
    sys.exit(main())
