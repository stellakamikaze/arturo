#!/usr/bin/env python3
"""Banco della roadmap (3/11/2026): strumenti/roadmap.py e la pagina sito/roadmap/.

ROADMAP.md vive nel repo di Arturo; qui il banco usa una roadmap di prova scritta sotto, così non
dipende da un clone accanto. Controlla:
  RM01 i commenti HTML con i numeri dei task non arrivano in nessuna delle due pagine;
  RM02 ogni voce ha "Commenta" verso la sua sezione, e pagina.json elenca le stesse sezioni;
  RM03 una roadmap fuori forma (ancora ripetuta, voce senza Stato, data mancante) si ferma;
  RM04 la pagina pubblicata è collegata da menu e piede della home, sitemap e llms.txt;
  RM05 "## Adesso (versione 0.3)" resta la sezione Adesso, e le due pagine dicono la versione.

--avvelena rompe il filtro dei commenti e vuole RM01 rosso col suo motivo. Esce 1 solo se il
veleno è rosso col motivo giusto: un veleno verde fa uscire 0, e il gate lo legge come tale.
"""
import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

PROVA = """# La strada di Arturo

Aggiornata il 2026-11-03

Apertura della prova.

<!--
nota per le sessioni
-->

## Adesso

### Prima voce {#prima}

Stato: in corso. Manca una cosa.

Testo della prima voce.

<!-- task: #4531 #4532 -->

### Seconda voce {#seconda}

Stato: da fare.

Testo della seconda.

<!-- task: #4566 -->

## Da decidere

- Una scelta. <!-- task: #4565 -->

## Uscito di recente

- 3 novembre 2026: una novità.
"""


def carica(repo: Path):
    spec = importlib.util.spec_from_file_location("roadmap", repo / "strumenti" / "roadmap.py")
    m = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(repo / "strumenti"))
    spec.loader.exec_module(m)
    return m


def rm01(rm) -> None:
    r = rm.leggi(PROVA)
    pubblica = rm.pagina_pubblica(r)
    sviluppo, meta = rm.pagina_sviluppo(r)
    for nome, testo in (("pubblica", pubblica), ("sviluppo", sviluppo), ("pagina.json", meta)):
        assert "task:" not in testo and not re.search(r"#45\d\d", testo), \
            "RM01 commento dei task in pagina " + nome


def rm02(rm) -> None:
    r = rm.leggi(PROVA)
    pubblica = rm.pagina_pubblica(r)
    sviluppo, meta = rm.pagina_sviluppo(r)
    for ancora in ("prima", "seconda"):
        assert 'href="/sviluppo/roadmap/#' + ancora + '"' in pubblica, "RM02 manca Commenta per " + ancora
        assert 'data-sezione="' + ancora + '"' in sviluppo, "RM02 manca il filo per " + ancora
    assert json.loads(meta)["sezioni"] == ["prima", "seconda", "decidere", "generale"], "RM02 sezioni di pagina.json"
    assert "In corso" in pubblica and "Manca una cosa." in pubblica, "RM02 stato della voce"


def rm03(rm) -> None:
    rotte = {
        "ancora ripetuta": PROVA.replace("{#seconda}", "{#prima}"),
        "voce senza Stato": PROVA.replace("Stato: da fare.\n", ""),
        "Aggiornata il": PROVA.replace("Aggiornata il 2026-11-03\n", ""),
        "voce senza {#ancora}": PROVA.replace(" {#seconda}", ""),
    }
    for motivo, testo in rotte.items():
        try:
            rm.leggi(testo)
        except rm.Fuori as e:
            assert motivo in str(e), "RM03 fermata per un altro motivo: " + str(e)
        else:
            raise AssertionError("RM03 roadmap fuori forma accettata: " + motivo)


def rm04(repo: Path) -> None:
    pagina = (repo / "sito" / "roadmap" / "index.html").read_text(encoding="utf-8")
    assert '<link rel="canonical" href="https://arturo.stellakamikaze.org/roadmap/">' in pagina, "RM04 canonical"
    assert "task:" not in pagina, "RM04 commento dei task nella pagina pubblicata"
    assert "Commenta questa voce" in pagina, "RM04 pagina senza Commenta"
    home = (repo / "sito" / "index.html").read_text(encoding="utf-8")
    assert home.count('href="roadmap/"') >= 2, "RM04 la home non porta alla roadmap da menu e piede"
    assert "<loc>https://arturo.stellakamikaze.org/roadmap/</loc>" in (repo / "sito" / "sitemap.xml").read_text(encoding="utf-8"), "RM04 sitemap"
    assert "https://arturo.stellakamikaze.org/roadmap/" in (repo / "sito" / "llms.txt").read_text(encoding="utf-8"), "RM04 llms.txt"


def rm05(rm) -> None:
    # Il numero di un blocco (3/11/2026): "## Adesso (versione 0.3)" resta la sezione Adesso, col suo sottotitolo.
    r = rm.leggi(PROVA.replace("## Adesso\n", "## Adesso (versione 0.3)\n"))
    assert [s["nome"] for s in r["sezioni"]][0] == "Adesso", "RM05 il numero entra nel nome della sezione"
    pubblica = rm.pagina_pubblica(r)
    assert 'id="s-adesso"' in pubblica and "<span>Versione 0.3. Il lavoro in corso.</span>" in pubblica, \
        "RM05 la pagina pubblica non dice la versione del blocco"
    sviluppo, _ = rm.pagina_sviluppo(r)
    assert "Adesso · versione 0.3" in sviluppo, "RM05 la pagina di sviluppo non dice la versione del blocco"


def esegui(repo: Path, rm) -> int:
    casi = [("RM01", lambda: rm01(rm)), ("RM02", lambda: rm02(rm)), ("RM03", lambda: rm03(rm)), ("RM04", lambda: rm04(repo)),
            ("RM05", lambda: rm05(rm))]
    rossi = 0
    for nome, caso in casi:
        try:
            caso()
            print("PASS " + nome)
        except AssertionError as e:
            rossi += 1
            print("FAIL " + nome + ": " + str(e))
    print("roadmap: " + str(len(casi) - rossi) + "/" + str(len(casi)))
    return 1 if rossi else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument("--avvelena", action="store_true", help="filtro dei commenti rotto: RM01 deve diventare rosso")
    a = ap.parse_args()
    repo = Path(a.repo)
    rm = carica(repo)
    if a.avvelena:
        rm.COMMENTO = re.compile(r"(?!)")
        return esegui(repo, rm)
    return esegui(repo, rm)


if __name__ == "__main__":
    sys.exit(main())
