"""Una volta sola (16/11/2026): porta dalla home a capitoli le figure e lo stile dei componenti nei paper.

Scrive strumenti/idee/figure/<nome>.html e sito/stile/componenti.css. Dopo, la home diventa la landing a passi
e queste figure vivono solo nei paper (strumenti/idee.py le include con {figura:nome}).
uso: python3 strumenti/idee/estrai_figure.py sito/index.html
"""
import re
import sys
from pathlib import Path

QUI = Path(__file__).parent
home = Path(sys.argv[1]).read_text(encoding="utf-8")


def blocco(testo: str, inizio: str) -> str:
    """Dall'apertura `inizio` al tag che la chiude, contando i tag dello stesso nome annidati."""
    pos = testo.index(inizio)
    nome = re.match(r"<([a-z]+)", inizio).group(1)
    apre, chiude = re.compile(rf"<{nome}[\s>]"), f"</{nome}>"
    profondita, i = 0, pos
    while True:
        m_apre = apre.search(testo, i)
        m_chiude = testo.index(chiude, i)
        if m_apre and m_apre.start() < m_chiude:
            profondita += 1
            i = m_apre.end()
        else:
            profondita -= 1
            i = m_chiude + len(chiude)
            if profondita == 0:
                return testo[pos:i]


def sezione(ident: str) -> str:
    return blocco(home, re.search(rf'<section [^>]*id="{ident}"[^>]*>', home).group(0))


figure = {
    "guardie": blocco(home, '<figure class="figura figura--diagramma figura--guardie">'),
    "anelli": blocco(home, '<figure class="anelli">'),
    "cassettiera": blocco(home, '<figure class="figura figura--cassettiera"'),
    "strati": blocco(home, '<figure class="strati__figura">'),
}
ritmo = sezione("ritmo")
testa_ritmo = blocco(ritmo, '<div class="testa testa--riga">')
interno = blocco(ritmo, '<div class="dentro">')
figure["ritmo"] = interno[len('<div class="dentro">'):-len("</div>")].replace(testa_ritmo, "").strip()
uso = sezione("uso")
figure["uso"] = blocco(uso, '<ul class="uso__elenco">')
figure["proposte"] = blocco(home, '<div class="risultati proposte__esempi">')
orsa = sezione("orsa")
figure["orsa"] = blocco(orsa, '<figure class="riga__lastra">')

# La cassettiera contava ancora 23 guardie: il README di main (16/11/2026) dice 32.
figure["cassettiera"] = figure["cassettiera"].replace("23 guardie", "32 guardie")

cartella = QUI / "figure"
cartella.mkdir(exist_ok=True)
for nome, html in figure.items():
    (cartella / f"{nome}.html").write_text(html.strip() + "\n", encoding="utf-8")
    print(f"figura {nome}: {len(html)} caratteri")

# Lo stile dei componenti: le regole della home i cui selettori sono tutti di un componente dei paper.
stile = home[home.index("<style>") + 7: home.index("</style>")]
NOMI = ("finestra", "t", "risultato", "risultati", "foglio", "pagina", "tabella-mock", "settimana", "progetti",
        "stato", "regolo", "pila", "in-arrivo", "giorni", "appunto", "anelli", "uso__elenco", "uso__voce",
        "uso__quando", "uso__nota", "uso__prima", "uso__ora", "quattro", "lastra", "strati", "cursore", "albero",
        "figura", "giorno")
COMPONENTE = re.compile(r"^\.(?:" + "|".join(re.escape(n) for n in NOMI) + r")(?![a-z0-9])")


def del_componente(selettore: str) -> bool:
    parti = [p.strip() for p in selettore.split(",") if p.strip()]
    return bool(parti) and all(COMPONENTE.match(p) for p in parti)


def regole(testo: str):
    """(selettore o at-rule, corpo) al primo livello."""
    i, n = 0, len(testo)
    while i < n:
        a = testo.find("{", i)
        if a < 0:
            return
        testa = testo[i:a].strip()
        profondita, j = 1, a + 1
        while profondita:
            if testo[j] == "{":
                profondita += 1
            elif testo[j] == "}":
                profondita -= 1
            j += 1
        yield testa, testo[a + 1: j - 1]
        i = j


uscita = ["/* Componenti condivisi fra la landing e i paper (/idee/): finestre del terminale, fogli d'esempio, pila degli\n"
          "   strati, figure. Estratti dalla home il 16/11/2026 da strumenti/idee/estrai_figure.py. */\n"]
for testa, corpo in regole(stile):
    testa_pulita = re.sub(r"/\*.*?\*/", "", testa, flags=re.S).strip()
    if testa_pulita.startswith("@media"):
        dentro = [f"  {s}{{{c}}}" for s, c in regole(corpo) if del_componente(re.sub(r"/\*.*?\*/", "", s, flags=re.S).strip())]
        if dentro:
            uscita.append(testa_pulita + "{\n" + "\n".join(dentro) + "\n}")
    elif del_componente(testa_pulita):
        uscita.append(f"{testa_pulita}{{{corpo}}}")
css = "\n".join(uscita).replace("url(img/", "url(../img/") + "\n"
(QUI.parent.parent / "sito" / "stile" / "componenti.css").write_text(css, encoding="utf-8")
print(f"componenti.css: {len(uscita) - 1} regole o blocchi")
