#!/usr/bin/env python3
"""SA01-SA09: le segnalazioni partono da sole (11/11/2026).

Decisione di chi mantiene Arturo: la segnalazione parte senza la domanda "La mando?", per tutti, con un
interruttore e un avviso al primo avvio. `arturo segnala manda` prepara e invia in un passo sul canale arturo.
Il server finto risponde come server/logica.js.

SA01 manda parte senza domanda: il server la riceve con l'origine, la riga finale dice numero e ritiro, lo
     stato ricorda l'invio.
SA02 l'interruttore: arturo segnalazioni manuali e ARTURO_SEGNALAZIONI=manuali riportano la domanda (uscita 4,
     anteprima, niente al server); automatiche riaccende.
SA03 il tetto: dopo dieci automatiche in 24 ore torna la domanda; le voci più vecchie di 24 ore non contano.
SA04 la stessa segnalazione non parte due volte in 24 ore.
SA05 un segreto non parte, e la riga dice perché.
SA06 l'avviso esce una volta sola; prima dell'avviso niente parte da solo; in modo manuale l'avviso non si consuma.
SA07 torna la domanda anche con: telemetria spenta, arturo segnala basta, un altro canale scelto, un nome di
     documento da controllare. manda rifiuta --tieni.
SA08 con la rete giù la segnalazione va in coda, e la riga lo dice.
SA09 i testi: l'avvio ha la riga dei due modi, /segnala usa manda, privacy, README e NOVITA dicono
     l'interruttore, /proponi resta col sì.

Sulla base ogni controllo deve fallire con un AssertionError che comincia con il suo codice. --avvelena: ogni
copia rotta fa rosso il caso suo.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_sportello_2026_11_04 import Lab  # noqa: E402
from test_contatto_2026_11_10 import Server, NUMERO  # noqa: E402

TITOLO = "La sessione si ferma"


def lab_con_avviso(repo: Path, server=None, **env) -> Lab:
    """Un laboratorio dove la persona ha già letto l'avviso: il caso comune dopo la prima sessione."""
    lab = Lab(repo, server, **env)
    lab.env.pop("ARTURO_SEGNALAZIONI", None)
    (lab.claude / "session-env").mkdir(parents=True, exist_ok=True)
    (lab.claude / "session-env" / "segnalazioni-annuncio").write_text("2026-11-11", encoding="utf-8")
    return lab


def manda(lab: Lab, testo: str = "Non parte.", *extra: str, **env):
    return lab.arturo("segnala", "manda", "--tipo", "problema", "--titolo", TITOLO,
                      "--file", str(lab.bozza(testo)), *extra, **env)


def stato(lab: Lab) -> dict:
    f = lab.claude / "session-env" / "segnala.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def scrivi_stato(lab: Lab, **campi) -> None:
    f = lab.claude / "session-env" / "segnala.json"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({"versione": 2, "domanda": None, "inviata": None, "canale": None, "pausa": None,
                             "modo": None, "auto": [], **campi}), encoding="utf-8")


def test_sa01(repo: Path) -> None:
    server = Server()
    lab = lab_con_avviso(repo, server)
    r = manda(lab, "Non parte.", "--origine", "avvio")
    assert r.returncode == 0, f"SA01 manda non parte: {r.returncode} {r.stderr[-300:]!r}"
    arrivate = server.segnalazioni()
    assert len(arrivate) == 1 and arrivate[0].get("origine") == "avvio" and "Non parte." in arrivate[0].get("testo", ""), \
        f"SA01 al server non arriva la segnalazione con l'origine: {arrivate}"
    assert r.stdout.startswith(f"Segnalato n. {NUMERO}: ") and f"arturo segnala ritira {NUMERO}" in r.stdout, \
        f"SA01 la riga finale non dice numero e ritiro: {r.stdout!r}"
    assert "La mando?" in r.stdout and "segnalazioni manuali" in r.stdout, "SA01 la riga finale non dice come tornare alla domanda"
    assert "PRONTA:" not in r.stdout, "SA01 manda stampa l'anteprima intera anche quando parte da sola"
    auto = stato(lab).get("auto") or []
    assert len(auto) == 1 and auto[0].get("numero") == NUMERO, f"SA01 lo stato non ricorda l'invio: {auto}"
    assert list((lab.claude / "data" / "segnalazioni").glob("*.md")), "SA01 manca la copia locale"


def test_sa02(repo: Path) -> None:
    server = Server()
    lab = lab_con_avviso(repo, server)
    r = lab.arturo("segnalazioni", "manuali")
    assert r.returncode == 0 and "La mando?" in r.stdout, f"SA02 arturo segnalazioni manuali non c'è: {r.stderr[-200:]!r}"
    assert '"modo": "manuali"' in (lab.claude / "session-env" / "segnala.json").read_text(encoding="utf-8"), \
        "SA02 lo stato non porta la forma che l'avvio cerca col grep"
    r = manda(lab)
    assert r.returncode == 4 and not server.segnalazioni(), f"SA02 in modo manuale manda parte lo stesso: {r.returncode}"
    assert "PRONTA: " in r.stdout and "DOMANDA: " in r.stdout and "segnala invia --canale arturo --file" in r.stdout, \
        f"SA02 in modo manuale mancano anteprima e domanda: {r.stdout[-300:]!r}"
    r = lab.arturo("segnalazioni", "automatiche")
    assert r.returncode == 0 and "ritirarla" in r.stdout, f"SA02 automatiche non riaccende: {r.stdout!r}"
    assert manda(lab).returncode == 0 and len(server.segnalazioni()) == 1, "SA02 dopo automatiche manda non parte"
    r = manda(lab, "Un altro fatto.", ARTURO_SEGNALAZIONI="Manuali")
    assert r.returncode == 4 and len(server.segnalazioni()) == 1, "SA02 la variabile ARTURO_SEGNALAZIONI non riporta la domanda"
    assert lab.arturo("segnalazioni", "boh").returncode == 2, "SA02 un modo sconosciuto non è un errore"


def test_sa03(repo: Path) -> None:
    server = Server()
    lab = lab_con_avviso(repo, server)
    adesso = dt.datetime.now()
    recenti = [{"quando": (adesso - dt.timedelta(hours=1, minutes=i)).isoformat(timespec="seconds"),
                "impronta": f"x{i}", "numero": i + 1} for i in range(10)]
    scrivi_stato(lab, auto=recenti)
    r = manda(lab)
    assert r.returncode == 4 and not server.segnalazioni(), f"SA03 oltre il tetto manda parte lo stesso: {r.returncode}"
    assert "DOMANDA: " in r.stdout and "tetto" in r.stdout, f"SA03 la domanda non dice il tetto: {r.stdout[-300:]!r}"
    vecchie = [dict(v, quando=(adesso - dt.timedelta(hours=25)).isoformat(timespec="seconds")) for v in recenti]
    scrivi_stato(lab, auto=vecchie)
    r = manda(lab)
    assert r.returncode == 0 and len(server.segnalazioni()) == 1, f"SA03 le voci di ieri contano ancora: {r.returncode}"
    assert len(stato(lab).get("auto") or []) == 1, "SA03 le voci di ieri restano nello stato"


def test_sa04(repo: Path) -> None:
    server = Server()
    lab = lab_con_avviso(repo, server)
    assert manda(lab).returncode == 0, "SA04 la prima non parte"
    r = manda(lab)
    assert r.returncode == 0 and len(server.segnalazioni()) == 1, f"SA04 la stessa segnalazione parte due volte: {len(server.segnalazioni())}"
    assert r.stdout.startswith("Già segnalata") and f"n. {NUMERO}" in r.stdout, f"SA04 la riga non dice che è già partita: {r.stdout!r}"
    assert manda(lab, "Un fatto diverso.").returncode == 0 and len(server.segnalazioni()) == 2, "SA04 un fatto diverso non parte"


def test_sa05(repo: Path) -> None:
    server = Server()
    lab = lab_con_avviso(repo, server)
    finto = "ghp_" + "a1B2c3D4e5" * 4
    r = manda(lab, f"Il token è {finto}.")
    assert r.returncode == 3 and not server.segnalazioni(), f"SA05 un segreto parte da solo: {r.returncode}"
    assert "segreto" in r.stderr and "Non è partita" in r.stderr and finto not in r.stdout + r.stderr, \
        f"SA05 la riga non dice perché, o stampa il segreto: {r.stderr!r}"


def test_sa06(repo: Path) -> None:
    server = Server()
    lab = Lab(repo, server)
    segno = lab.claude / "session-env" / "segnalazioni-annuncio"
    r = manda(lab)
    assert r.returncode == 4 and not server.segnalazioni(), f"SA06 prima dell'avviso manda parte da solo: {r.returncode}"
    assert "SEGNALAZIONI: " in r.stdout and "segnalazioni manuali" in r.stdout, "SA06 la domanda non porta l'avviso"
    assert segno.exists(), "SA06 dopo l'avviso detto con la domanda il segno manca"
    assert manda(lab, "Un altro fatto.").returncode == 0, "SA06 dopo l'avviso manda non parte"
    altro = Lab(repo, None)
    altro.arturo("segnalazioni", "manuali")
    r = altro.arturo("segnala", "avviso")
    assert r.returncode == 0 and not r.stdout.strip() and not (altro.claude / "session-env" / "segnalazioni-annuncio").exists(), \
        "SA06 in modo manuale l'avviso esce o si consuma"
    altro.arturo("segnalazioni", "automatiche")
    prima = altro.arturo("segnala", "avviso").stdout
    assert prima.startswith("SEGNALAZIONI: ") and "senza chiedere" in prima and "segnalazioni manuali" in prima, \
        f"SA06 l'avviso non dice cosa cambia e come spegnerlo: {prima!r}"
    assert not altro.arturo("segnala", "avviso").stdout.strip(), "SA06 l'avviso esce due volte"


def test_sa07(repo: Path) -> None:
    server = Server()
    for nome, prepara_lab in (
            ("telemetria spenta", lambda l: l.env.update(ARTURO_TELEMETRIA="0")),
            ("basta", lambda l: l.arturo("segnala", "basta")),
            ("canale gh", lambda l: l.arturo("segnala", "canale", "gh"))):
        lab = lab_con_avviso(repo, server)
        prepara_lab(lab)
        r = manda(lab)
        assert r.returncode == 4 and "DOMANDA: " in r.stdout and not server.segnalazioni(), \
            f"SA07 con {nome} manda parte da solo: {r.returncode} {r.stdout[-200:]!r}"
    lab = lab_con_avviso(repo, server)
    r = manda(lab, "Si rompe aprendo contratto rossi.zip dal menu.")
    assert r.returncode == 4 and "Da controllare" in r.stdout and not server.segnalazioni(), \
        f"SA07 un nome di documento da controllare parte da solo: {r.returncode}"
    r = manda(lab, "Non parte.", "--tieni", "web")
    assert r.returncode == 2 and "Errore: manda non accetta --tieni" in r.stderr and not server.segnalazioni(), \
        f"SA07 manda accetta --tieni o non dice perché lo rifiuta: {r.returncode} {r.stderr[:160]!r}"


def test_sa08(repo: Path) -> None:
    lab = lab_con_avviso(repo, None)
    r = manda(lab)
    assert r.returncode == 0 and r.stdout.startswith("Segnalato, in coda"), f"SA08 con la rete giù la riga non dice la coda: {r.stdout!r} {r.stderr[-200:]!r}"
    assert list((lab.claude / "data" / "segnalazioni").glob("*.attesa.json")), "SA08 la segnalazione non resta in attesa"
    auto = stato(lab).get("auto") or []
    assert len(auto) == 1 and auto[0].get("numero") is None, f"SA08 l'invio in coda non conta per il tetto: {auto}"


def test_sa09(repo: Path) -> None:
    leggi = lambda nome: (repo / nome).read_text(encoding="utf-8")  # noqa: E731
    avvio = leggi("hooks/session-start.sh")
    assert '"modo": "manuali"' in avvio and "ARTURO_SEGNALAZIONI" in avvio and "segnala avviso" in avvio, \
        "SA09 l'avvio non distingue i due modi o non lancia l'avviso"
    assert "proponi una volta /segnala" in avvio and "mandala con manda" in avvio, "SA09 l'avvio non ha le due righe SEGNALA"
    comando = leggi("commands/segnala.md")
    assert "segnala manda --tipo" in comando and "Uscita 4" in comando and "segnalazioni manuali" in comando, \
        "SA09 /segnala non usa manda o non dice l'interruttore"
    assert "parte solo dopo il tuo sì" not in comando, "SA09 /segnala promette ancora il sì per ogni segnalazione"
    assert "manda --tipo" not in leggi("commands/proponi.md") and "mai `manda`" in leggi("commands/proponi.md"), \
        "SA09 /proponi non tiene il sì"
    assert "`manda`" in leggi("commands/fine.md"), "SA09 la FASE 10 di /fine propone ancora invece di mandare"
    for nome in ("docs/privacy.md", "README.md", "NOVITA.md", "commands/setup.md"):
        assert "arturo segnalazioni manuali" in leggi(nome), f"SA09 {nome} non dice come tornare alla domanda"
    assert "Solo dopo il tuo sì | 12 mesi" not in leggi("docs/privacy.md"), "SA09 la privacy promette ancora il sì per ogni segnalazione"
    assert '"segnalazioni": (segnalazioni' in leggi("bin/arturo"), "SA09 arturo non ha il comando segnalazioni"


# Il veleno (caso, file, testo giusto, testo rotto): la copia rotta deve far rosso il suo caso.
VELENI = [
    ("SA02", "bin/segnala.py", '    if stato.get("modo") == "manuali":\n        return "manuali", "hai scelto', '    if False:\n        return "manuali", "hai scelto'),
    ("SA02", "bin/segnala.py", 'if os.environ.get(VARIABILE_MODO, "").strip().lower() == "manuali":', "if False:"),
    ("SA03", "bin/segnala.py", "        elif len(recenti) >= AUTO_AL_GIORNO:", "        elif False:"),
    ("SA03", "bin/segnala.py", "(adesso - _quando(v[\"quando\"])) < dt.timedelta(hours=AUTO_ORE)]", "True]"),
    ("SA04", "bin/segnala.py", '    gia = next((v for v in recenti if v["impronta"] == impronta), None)', "    gia = None"),
    ("SA05", "bin/segnala.py", "    if esito != 0:\n        if esito == 3:", "    if esito not in (0, 3):\n        if esito == 3:"),
    ("SA06", "bin/segnala.py", "        elif not file_annuncio().exists():", "        elif False:"),
    ("SA06", "bin/segnala.py", '    if file_annuncio().exists() or modo_segnalazioni()[0] == "manuali":', "    if file_annuncio().exists():"),
    ("SA07", "bin/segnala.py", "    spenta = telemetria.perche_spenta()\n    if spenta:\n        return \"manuali\"", "    spenta = telemetria.perche_spenta()\n    if False:\n        return \"manuali\""),
    ("SA07", "bin/segnala.py", '    if stato.get("pausa") == "sempre":\n        return "manuali"', '    if False:\n        return "manuali"'),
    ("SA07", "bin/segnala.py", '        if stato.get("canale") not in (None, "arturo"):', "        if False:"),
    ("SA07", "bin/segnala.py", '        elif "\\nDa controllare: " in "\\n" + anteprima.getvalue():', "        elif False:"),
    ("SA07", "bin/segnala.py", '            if any(x == "--tieni" or x.startswith("--tieni=") for x in resto):', "            if False:"),
    ("SA08", "bin/segnala.py", '                                             "numero": numero}]))', '                                             "numero": numero}][:0]))'),
]


def avvelena(repo: Path) -> int:
    esiti = []
    for caso, rel, giusto, rotto in VELENI:
        with tempfile.TemporaryDirectory() as tmp:
            copia = Path(tmp) / "repo"
            shutil.copytree(repo, copia, ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules"))
            testo = (copia / rel).read_text(encoding="utf-8")
            assert testo.count(giusto) == 1, f"veleno {caso}: il testo da rompere non c'è più in {rel}: {giusto[:50]!r}"
            (copia / rel).write_text(testo.replace(giusto, rotto), encoding="utf-8")
            try:
                TESTS[caso](copia)
            except AssertionError as e:
                if str(e).startswith(caso):
                    print(f"VELENO {caso} ROSSO: {str(e)[:120]}")
                    esiti.append(caso)
                    continue
                print(f"VELENO {caso} NON ATTACCA ({rel}): {e}")
                return 1
            print(f"VELENO {caso} NON ATTACCA ({rel}): il caso resta verde con {rotto[:50]!r}")
            return 1
    print(f"VELENI_ROSSI={','.join(esiti)} veleni={len(VELENI)}")
    return 0 if len(esiti) == len(VELENI) else 1


TESTS = {"SA01": test_sa01, "SA02": test_sa02, "SA03": test_sa03, "SA04": test_sa04, "SA05": test_sa05,
         "SA06": test_sa06, "SA07": test_sa07, "SA08": test_sa08, "SA09": test_sa09}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    parser.add_argument("--avvelena", action="store_true")
    parser.add_argument("casi", nargs="*")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.avvelena:
        return avvelena(repo)
    scelti = {k: v for k, v in TESTS.items() if not args.casi or k in args.casi}
    if args.baseline_ref:
        rossi, altro = [], []
        for nome, test in scelti.items():
            try:
                test(repo)
            except AssertionError as e:
                (rossi if str(e).startswith(nome) else altro).append(f"{nome}: {e}")
            except Exception as e:  # noqa: BLE001
                altro.append(f"{nome}: {type(e).__name__} {e}")
        assert not altro and len(rossi) == len(scelti), \
            "baseline non discriminante: ogni controllo deve fallire col suo codice.\n" + "\n".join(altro + rossi)
        print(f"BASELINE_DISCRIMINANTE={','.join(r.split(':')[0] for r in rossi)}")
        return 0
    for test in scelti.values():
        test(repo)
    print(f"PASS {','.join(scelti)} controlli={len(scelti)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
