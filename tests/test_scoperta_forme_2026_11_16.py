#!/usr/bin/env python3
"""SF01-SF11: le forme della Scoperta e i lavori dello storico (16/11/2026, Fase D, #5702).

La voce "Arturo ti propone cosa automatizzare" (ROADMAP.md) e docs/mestieri.md promettono: un lavoro dello
storico delle chat che torna da mesi diventa una proposta dal primo giorno; una proposta è un'automazione,
una sintesi o una pagina web locale dal modello della famiglia di mestiere; `arturo scoperta mappa` dice per
ogni progetto cosa si può proporre. Restano i limiti della Scoperta v1. Qui si provano su una HOME finta.

SF01 un lavoro dello storico con 6 conversazioni in 4 mesi è un candidato "storico" in forma di sintesi;
     uno con 3 conversazioni, o tutto in un mese, no.
SF02 un lavoro con "corso" e "lezioni" nei temi è una pagina sul modello "lezione interattiva".
SF03 la famiglia decide un pareggio: "budget" e "report" insieme senza famiglia danno una sintesi, con la
     famiglia della produzione (dal "Chi sono" del CLAUDE.md) il simulatore di spesa.
SF04 proponi: il blocco ha la bozza della sintesi, la riga Forma e la risposta giusta; proposte.json ha la
     forma; una seconda proposta nella stessa sessione esce con 3.
SF05 rispondi si dice di scrivere la sintesi; creata e annulla spostano il file in data/scoperta/annullate/.
SF06 un foglio .csv che torna è una pagina se il nome o i campi chiamano un modello (spese: simulatore,
     report: cruscotto del report); un foglio dei solleciti, un .md e un gruppo di file restano automazioni.
SF07 mappa: il lavoro dello storico con la sua forma, poi "proposta" dopo proponi; senza lavori, una riga.
SF08 un indice dello storico rotto non ferma analizza.
SF09 ogni famiglia di docs/mestieri.md ha un modello di pagina, e la pagina nomina ogni modello.
SF10 /fine racconta le forme e bin/arturo ha la mappa nell'aiuto della Scoperta.
SF11 scoperta_forme.py non importa rete né telemetria.

Con --avvelena ogni controllo riceve una copia del repository rotta nel punto che sorveglia, e deve
fallire col suo codice e il motivo atteso (VELENI).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SESSIONE = "sessione-prova-forme-0001"


def lavoro(ident: str, titolo: str, conversazioni: int, da: str, a: str, temi=None, file=None) -> dict:
    return {"id": ident, "titolo": titolo, "titoli": [titolo], "temi": temi or [], "da": da, "a": a,
            "conversazioni": conversazioni, "fonte": ["chatgpt"], "file": file or [], "approvato": "2026-11-16"}


class Banco:
    def __init__(self, repo: Path) -> None:
        self.repo = repo
        self.home = Path(tempfile.mkdtemp(prefix="arturo-forme."))
        self.claude = self.home / ".claude"
        (self.claude / "data").mkdir(parents=True)
        (self.claude / "CLAUDE.md").write_text("# Io\n\n## Regole\n- niente emoji\n", encoding="utf-8")

    def storico(self, *lavori: dict) -> None:
        d = self.claude / "data" / "storico"
        d.mkdir(parents=True, exist_ok=True)
        (d / "indice.json").write_text(json.dumps({"lavori": list(lavori)}), encoding="utf-8")

    def scoperta(self, *argomenti: str) -> subprocess.CompletedProcess:
        env = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home), PYTHONDONTWRITEBYTECODE="1",
                   ARTURO_TELEMETRIA="0", CLAUDE_CODE_SESSION_ID=SESSIONE)
        for chiave in ("CLAUDE_CONFIG_DIR", "ARTURO_INTERVISTA", "ARTURO_MEMORIA"):
            env.pop(chiave, None)
        return subprocess.run([sys.executable, str(self.repo / "bin" / "scoperta.py"), *argomenti], env=env,
                              capture_output=True, text=True, encoding="utf-8", timeout=120)

    def analizza(self) -> list:
        r = self.scoperta("analizza", "--json")
        assert r.returncode == 0, f"analizza: {r.stderr[-300:]}"
        return json.loads(r.stdout)

    def forme(self):
        """Il modulo delle forme, caricato dalla copia del repository sotto prova."""
        sys.path.insert(0, str(self.repo / "bin"))
        sys.path.insert(0, str(self.repo / "hooks"))
        try:
            import importlib
            for nome in ("scoperta_forme", "radici"):
                sys.modules.pop(nome, None)
            return importlib.import_module("scoperta_forme")
        finally:
            sys.path.pop(0)
            sys.path.pop(0)

    def chiudi(self) -> None:
        shutil.rmtree(self.home, ignore_errors=True)
        sys.modules.pop("scoperta_forme", None)


LUNGO = lavoro("L1", "Ricerca sulla mobilità a Torino", 6, "2026-06", "2026-09", temi=["interviste", "trasporti"])


def _storici(trovati: list) -> list:
    return [c for c in trovati if c.get("segnale") == "storico"]


def test_sf01(b: Banco) -> None:
    b.storico(LUNGO, lavoro("L2", "Domanda veloce", 3, "2026-06", "2026-09"),
              lavoro("L3", "Trasloco", 9, "2026-07", "2026-07"))
    s = _storici(b.analizza())
    assert [c["lavoro"]["titolo"] for c in s] == ["Ricerca sulla mobilità a Torino"], \
        f"SF01 i lavori dello storico che tornano non sono quelli giusti: {[c['lavoro'] for c in s]}"
    assert s[0]["forma"] == "sintesi" and s[0]["volte"] == 6, f"SF01 forma o volte sbagliate: {s[0]}"


def test_sf02(b: Banco) -> None:
    b.storico(lavoro("L4", "Corso di fotografia per ragazzi", 8, "2026-03", "2026-10", temi=["lezioni", "esercizi"]))
    s = _storici(b.analizza())
    assert s and s[0]["forma"] == "pagina" and s[0]["modello"] == "insegnamento", \
        f"SF02 un corso non diventa una lezione interattiva: {s}"
    r = b.scoperta("proponi")
    assert "lezione interattiva" in r.stdout and "Forma: pagina" in r.stdout, \
        f"SF02 la proposta non nomina il modello: {r.stdout[-300:]}"


def test_sf03(b: Banco) -> None:
    pari = lavoro("L5", "Budget e report", 7, "2026-01", "2026-05", temi=["budget", "report"])
    b.storico(pari)
    s = _storici(b.analizza())
    assert s and s[0]["forma"] == "sintesi", f"SF03 un pareggio senza famiglia sceglie un modello: {s}"
    (b.claude / "CLAUDE.md").write_text("# Io\n\n## Chi sono\nSono producer di eventi e festival.\n",
                                        encoding="utf-8")
    s = _storici(b.analizza())
    assert s and s[0]["forma"] == "pagina" and s[0]["modello"] == "produzione", \
        f"SF03 la famiglia della produzione non sceglie il simulatore di spesa: {s}"


def test_sf04(b: Banco) -> None:
    b.storico(LUNGO)
    r = b.scoperta("proponi")
    assert r.returncode == 0 and "Bozza della sintesi" in r.stdout and "Forma: sintesi" in r.stdout \
        and "Claude scrive la sintesi" in r.stdout, f"SF04 il blocco della sintesi non torna: {r.stdout[-400:]}"
    proposte = json.loads((b.claude / "data" / "scoperta" / "proposte.json").read_text(encoding="utf-8"))
    assert any(p.get("forma") == "sintesi" for p in proposte.values()), f"SF04 proposte.json senza forma: {proposte}"
    b.storico(LUNGO, lavoro("L6", "Rubrica di cinema", 9, "2026-02", "2026-08"))
    assert b.scoperta("proponi").returncode == 3, "SF04 due proposte nella stessa sessione"


def test_sf05(b: Banco) -> None:
    b.storico(LUNGO)
    ident = re.search(r"SCOPERTA ([0-9a-f]{10}):", b.scoperta("proponi").stdout).group(1)
    si = b.scoperta("rispondi", ident, "si")
    assert si.returncode == 0 and "scrivi la sintesi" in si.stdout and "/creaskill" not in si.stdout, \
        f"SF05 il sì di una sintesi manda a /creaskill: {si.stdout[-200:]}"
    file = b.home / "Documents" / "newsletter" / "sintesi-newsletter.md"
    file.parent.mkdir(parents=True)
    file.write_text("# Sintesi\n", encoding="utf-8")
    assert b.scoperta("creata", ident, str(file)).returncode == 0, "SF05 creata rifiuta la sintesi"
    assert b.scoperta("annulla", ident).returncode == 0 and not file.exists(), "SF05 annulla non toglie la sintesi"
    annullate = list((b.claude / "data" / "scoperta" / "annullate").rglob("sintesi-newsletter.md"))
    assert annullate, "SF05 la sintesi annullata non è tenuta da parte"


def test_sf06(b: Banco) -> None:
    f = b.forme()
    base = {"segnale": "cadenza", "campi": ["totale"], "file": [], "famiglia": ""}
    spese = f.con_forma(dict(base, famiglia="/x/spese-#.csv", file=["/x/spese-1.csv"]), None)
    assert spese["forma"] == "pagina" and f.descrizione_modello(spese)["nome"] == "simulatore di spesa", \
        f"SF06 il foglio delle spese non è un simulatore: {spese}"
    report = f.con_forma(dict(base, famiglia="/x/dati-report.tsv", file=["/x/dati-report.tsv"]), None)
    assert f.descrizione_modello(report)["nome"] == "cruscotto del report", f"SF06 i dati del report: {report}"
    solleciti = f.con_forma(dict(base, famiglia="/x/solleciti.csv", file=["/x/solleciti.csv"]), "produzione")
    assert solleciti["forma"] == "automazione", f"SF06 il foglio dei solleciti diventa una pagina: {solleciti}"
    md = f.con_forma(dict(base, famiglia="/x/report.md", file=["/x/report.md"]), "produzione")
    insieme = f.con_forma(dict(base, segnale="insieme", file=["/x/a.csv", "/x/b.md"]), None)
    assert md["forma"] == "automazione" and insieme["forma"] == "automazione", \
        f"SF06 un .md o un gruppo diventano pagine: {md['forma']} {insieme['forma']}"


def test_sf07(b: Banco) -> None:
    vuota = b.scoperta("mappa")
    assert vuota.returncode == 0 and "Nessun lavoro" in vuota.stdout, f"SF07 la mappa vuota: {vuota.stdout[-200:]}"
    b.storico(LUNGO)
    r = b.scoperta("mappa")
    assert "storico · Ricerca sulla mobilità a Torino" in r.stdout and "sintesi · 6 volte" in r.stdout, \
        f"SF07 la mappa non ha il lavoro: {r.stdout[-300:]}"
    b.scoperta("proponi")
    assert "proposta" in b.scoperta("mappa").stdout.splitlines()[-1], "SF07 la mappa non dice che è proposta"


def test_sf08(b: Banco) -> None:
    d = b.claude / "data" / "storico"
    d.mkdir(parents=True)
    (d / "indice.json").write_text("{rotto", encoding="utf-8")
    r = b.scoperta("analizza", "--json")
    assert r.returncode == 0 and json.loads(r.stdout) == [], f"SF08 un indice rotto ferma analizza: {r.stderr[-200:]}"
    (d / "indice.json").write_text(json.dumps({"lavori": [{"titolo": 3, "conversazioni": "x", "temi": "no"}]}),
                                   encoding="utf-8")
    r = b.scoperta("analizza", "--json")
    assert r.returncode == 0, f"SF08 un lavoro con campi strani ferma analizza: {r.stderr[-200:]}"


def test_sf09(b: Banco) -> None:
    f = b.forme()
    mestieri = (b.repo / "docs" / "mestieri.md").read_text(encoding="utf-8")
    famiglie = ("parola", "immagine", "insegnamento", "produzione", "consulenza", "archivio")
    mancano = [k for k in famiglie if k not in f.MODELLI]
    assert not mancano, f"SF09 famiglie senza modello di pagina: {mancano}"
    non_nominati = [m["nome"] for m in f.MODELLI.values() if m["nome"] not in mestieri]
    assert not non_nominati, f"SF09 docs/mestieri.md non nomina i modelli: {non_nominati}"


def test_sf10(b: Banco) -> None:
    fine = (b.repo / "commands" / "fine.md").read_text(encoding="utf-8")
    assert "riga `Forma:`" in fine and "arturo scoperta\ncreata <ID> <file>" in fine.replace("arturo scoperta creata", "arturo scoperta\ncreata"), \
        "SF10 /fine non racconta la sintesi e la pagina"
    aiuto = b.scoperta("aiuto")
    assert "mappa" in aiuto.stdout, "SF10 l'aiuto della Scoperta non ha la mappa"


def test_sf11(b: Banco) -> None:
    sorgente = (b.repo / "bin" / "scoperta_forme.py").read_text(encoding="utf-8")
    vietati = re.findall(r"(?m)^\s*(?:import|from)\s+(socket|urllib|http|telemetria|ssl)\b", sorgente)
    assert not vietati, f"SF11 scoperta_forme.py importa rete o telemetria: {vietati}"


CASI = [(f"SF{n:02d}", f) for n, f in enumerate(
    (test_sf01, test_sf02, test_sf03, test_sf04, test_sf05, test_sf06, test_sf07, test_sf08, test_sf09,
     test_sf10, test_sf11), start=1)]

VELENI = (
    ("SF01", [("bin/scoperta_forme.py", "if n < MIN_CONVERSAZIONI or mesi < MIN_MESI:", "if n < MIN_CONVERSAZIONI:")],
     "non sono quelli giusti"),
    ("SF02", [("bin/scoperta_forme.py", '"parole": ["lezion", "corso", "lezione", "classe", "studenti", "workshop", '
               '"seminari", "esercizi"]', '"parole": ["xyz"]')], "lezione interattiva"),
    ("SF03", [("bin/scoperta_forme.py", "(len(punti) < 2 or punti[1][0] < punti[0][0])", "True")], "pareggio"),
    ("SF04", [("bin/scoperta.py", '"forma": c.get("forma", "automazione"),\n', "")], "senza forma"),
    ("SF05", [("bin/scoperta.py", "print(forme.dopo_il_si(voce, ident))",
               'print(f"Ora: /creaskill con la bozza {ident}")')], "/creaskill"),
    ("SF06", [("bin/scoperta_forme.py", 'if c.get("segnale") != "insieme" and ext in DATI:', "if ext in DATI or True:")],
     "diventano pagine"),
    ("SF07", [("bin/scoperta.py", '    if verbo == "mappa":\n', '    if verbo == "mappa-vecchia":\n')], "mappa vuota"),
    ("SF08", [("bin/scoperta_forme.py", "    except (OSError, ValueError):\n        return []\n    lavori",
               "    except OSError:\n        return []\n    lavori")], "indice rotto"),
    ("SF09", [("bin/scoperta_forme.py", '"archivio": {"nome": "linea del tempo",', '"archivi": {"nome": "linea del tempo",')],
     "senza modello"),
    ("SF10", [("commands/fine.md", "riga `Forma:`", "riga Forma")], "non racconta"),
    ("SF11", [("bin/scoperta_forme.py", "import hashlib\n", "import hashlib\nimport socket\n")], "rete o telemetria"),
)


def avvelena(repo: Path) -> int:
    assert len(VELENI) == len(CASI), f"veleni {len(VELENI)} per {len(CASI)} controlli"
    casi = dict(CASI)
    inerti = []
    for codice, modifiche, motivo in VELENI:
        copia = Path(tempfile.mkdtemp(prefix="arturo-veleno-forme."))
        b = None
        try:
            for cartella in ("bin", "hooks", "docs", "shared", "commands", "scripts"):
                if (repo / cartella).is_dir():
                    shutil.copytree(repo / cartella, copia / cartella)
            for file, vecchio, nuovo in modifiche:
                bersaglio = copia / file
                testo = bersaglio.read_text(encoding="utf-8").replace("\r\n", "\n")
                assert testo.count(vecchio) == 1, f"veleno {codice}: il punto da rompere non c'è più in {file}"
                bersaglio.write_bytes(testo.replace(vecchio, nuovo).encode("utf-8"))
            b = Banco(copia)
            try:
                casi[codice](b)
                inerti.append(f"{codice}: verde con il veleno")
            except AssertionError as e:
                if not (str(e).startswith(codice) and motivo in str(e)):
                    inerti.append(f"{codice}: rosso col motivo sbagliato: {e}")
                else:
                    print(f"VELENO {codice} ROSSO: {str(e)[:120]}")
            except Exception as e:  # un veleno che fa cadere il codice prima dell'assert
                inerti.append(f"{codice}: eccezione invece del rosso: {type(e).__name__}: {e}")
        finally:
            if b is not None:
                b.chiudi()
            shutil.rmtree(copia, ignore_errors=True)
    assert not inerti, "veleni che non attaccano:\n" + "\n".join(inerti)
    print(f"VELENI_ROSSI={','.join(v[0] for v in VELENI)} veleni={len(VELENI)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    parser.add_argument("--avvelena", action="store_true")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.avvelena:
        return avvelena(repo)
    errori = []
    for codice, caso in CASI:
        b = Banco(repo)
        try:
            caso(b)
        except AssertionError as e:
            errori.append(str(e))
        except Exception as e:
            errori.append(f"{codice} eccezione: {type(e).__name__}: {e}")
        finally:
            b.chiudi()
    for e in errori:
        print("KO", e)
    if errori:
        return 1
    print(f"PASS {','.join(c for c, _ in CASI)} controlli={len(CASI)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
