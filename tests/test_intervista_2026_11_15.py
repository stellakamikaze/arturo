#!/usr/bin/env python3
"""IV01-IV12: bin/intervista.py, l'intervista che continua dopo /setup (15/11/2026, Fase C, #5709).

La voce "L'intervista che continua" (ROADMAP.md) e la sezione omonima di docs/privacy.md promettono: al
massimo una domanda al giorno, solo nelle prime sei settimane dopo /setup, mai in rotazione, domande per
famiglia di mestiere da docs/mestieri.md, la risposta nella memoria solo col sì e senza testo nello stato,
un comando che la spegne. Qui si provano su una HOME finta.

IV01 docs/mestieri.md dà quattro domande per tutti e sei famiglie, ognuna con due domande e le sue parole.
IV02 la famiglia viene dal "Chi sono" del CLAUDE.md, poi dai temi dello storico; un pareggio non sceglie.
IV03 una domanda coperta dal CLAUDE.md non esce: con "Chi sono" la prima è committenti, senza è mestiere.
IV04 una domanda al giorno: la seconda proposta dello stesso giorno tace, e una domanda proposta due volte
     senza risposta non torna il terzo giorno.
IV05 risposta salva la nota persona-ID di tipo user, annunciata da /fine, e lo stato non ha il testo.
IV06 una risposta con un segreto non si salva e non segna la domanda come fatta.
IV07 tace senza /setup, dopo 42 giorni, spenta, con ARTURO_INTERVISTA=0 e a memoria spenta.
IV08 arturo contesto stampa INTERVISTA, ma in rotazione non la stampa e non scrive lo stato.
IV09 salta toglie la domanda per sempre, e una nota persona-ID già in memoria la copre.
IV10 arturo intervista passa da bin/arturo; /inizio e la privacy raccontano l'intervista.
IV11 lo script non importa rete né telemetria.
IV12 dopo la risposta a ricorrente esce la riga SKILL, che propone /creaskill: una volta sola, mai per
     un'altra domanda. `skill no` e `skill si` restano nello stato, senza testo; /inizio dice cosa fare
     della riga (21/11/2026, #6277).

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

OGGI = "2026-11-15"
RISPOSTA = "Lavoro per due redazioni online e per un'agenzia di Torino."
CHI_SONO = "# Le mie istruzioni\n\n## Chi sono\nSono una giornalista e scrivo una newsletter di cinema.\n\n## Regole\n- niente emoji\n"


class Banco:
    def __init__(self, repo: Path) -> None:
        self.repo = repo
        self.home = Path(tempfile.mkdtemp(prefix="arturo-intervista."))
        self.claude = self.home / ".claude"
        (self.claude / "data").mkdir(parents=True)
        (self.claude / "data" / "setup-fatto").write_text("2026-11-10\n", encoding="utf-8")
        (self.claude / "CLAUDE.md").write_text(CHI_SONO, encoding="utf-8")
        (self.home / "Documents" / "ClaudeCode" / "libro").mkdir(parents=True)

    def lancia(self, *argomenti: str, script: str = "intervista.py", oggi: str = OGGI, stdin: str = "",
               **env_extra: str) -> subprocess.CompletedProcess:
        env = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home), PYTHONDONTWRITEBYTECODE="1",
                   ARTURO_OGGI=oggi)
        for chiave in ("ARTURO_TELEMETRIA", "ARTURO_MEMORIA", "ARTURO_INTERVISTA", "CLAUDE_CONFIG_DIR"):
            env.pop(chiave, None)
        env.update(env_extra)
        return subprocess.run([sys.executable, str(self.repo / "bin" / script), *argomenti], env=env, input=stdin,
                              capture_output=True, text=True, timeout=120)

    def stato(self) -> dict:
        try:
            return json.loads((self.claude / "data" / "intervista" / "stato.json").read_text(encoding="utf-8"))
        except OSError:
            return {}

    def prossima(self, **kw: str) -> str:
        r = self.lancia("stato", "--json", **kw)
        assert r.returncode == 0, f"stato --json: {r.stderr[-200:]}"
        return json.loads(r.stdout)

    def chiudi(self) -> None:
        shutil.rmtree(self.home, ignore_errors=True)


def _domanda(uscita: str) -> str:
    m = re.search(r"domanda: ([a-z0-9-]+) ·", uscita)
    return m.group(1) if m else ""


def test_iv01(b: Banco) -> None:
    sys.path.insert(0, str(b.repo / "bin"))
    sys.path.insert(0, str(b.repo / "hooks"))
    try:
        import importlib
        import intervista
        intervista = importlib.reload(intervista)
        m = intervista.leggi_mestieri(b.repo / "docs" / "mestieri.md")
    finally:
        sys.path.pop(0)
        sys.path.pop(0)
        sys.modules.pop("intervista", None)
    ids = [d["id"] for d in m["generali"]]
    assert ids == ["mestiere", "committenti", "ricorrente", "consegna"], f"IV01 domande per tutti: {ids}"
    assert len(m["famiglie"]) == 6, f"IV01 famiglie lette: {sorted(m['famiglie'])}"
    for chiave, f in m["famiglie"].items():
        assert len(f["domande"]) == 2 and len(f["parole"]) >= 5, \
            f"IV01 la famiglia {chiave} ha {len(f['domande'])} domande e {len(f['parole'])} parole"
        assert all(d["id"].startswith(chiave + "-") for d in f["domande"]), f"IV01 id fuori famiglia in {chiave}"


def test_iv02(b: Banco) -> None:
    s = b.prossima()
    assert s["famiglia"] == "parola" and "CLAUDE.md" in s["fonte_famiglia"], f"IV02 dal CLAUDE.md: {s}"
    (b.claude / "CLAUDE.md").write_text("# Io\n\n## Regole\n- niente emoji\n", encoding="utf-8")
    storico = b.claude / "data" / "storico"
    storico.mkdir(parents=True)
    (storico / "indice.json").write_text(json.dumps({"lavori": [
        {"titolo": "Mostra di fotografia", "temi": ["curatela", "catalogo", "museo"]}]}), encoding="utf-8")
    s = b.prossima()
    assert s["famiglia"] == "archivio" and "storico" in s["fonte_famiglia"], f"IV02 dallo storico: {s}"
    (b.claude / "CLAUDE.md").write_text("# Io\n\n## Chi sono\nFotografa e curatrice.\n", encoding="utf-8")
    (storico / "indice.json").unlink()
    s = b.prossima()
    assert s["famiglia"] is None, f"IV02 un pareggio fra immagine e archivio ha scelto: {s}"


def test_iv03(b: Banco) -> None:
    r = b.lancia("proponi")
    assert _domanda(r.stdout) == "committenti", f"IV03 con Chi sono la prima domanda è: {r.stdout[-200:]}"
    b.chiudi()
    b.__init__(b.repo)
    (b.claude / "CLAUDE.md").write_text("# Io\n\n## Regole\n- niente emoji\n", encoding="utf-8")
    r = b.lancia("proponi")
    assert _domanda(r.stdout) == "mestiere", f"IV03 senza Chi sono la prima domanda è: {r.stdout[-200:]}"


def test_iv04(b: Banco) -> None:
    primo = _domanda(b.lancia("proponi").stdout)
    secondo = b.lancia("proponi")
    assert primo and not _domanda(secondo.stdout) and "oggi" in secondo.stdout, \
        f"IV04 due domande lo stesso giorno: {primo} poi {secondo.stdout[-160:]}"
    domani = _domanda(b.lancia("proponi", oggi="2026-11-16").stdout)
    dopo = _domanda(b.lancia("proponi", oggi="2026-11-17").stdout)
    assert domani == primo and dopo and dopo != primo, \
        f"IV04 una domanda ignorata due volte torna: {primo} {domani} {dopo}"


def test_iv05(b: Banco) -> None:
    r = b.lancia("risposta", "committenti", "--testo", RISPOSTA)
    nota = b.claude / "data" / "memory" / "profilo" / "persona-committenti.md"
    assert r.returncode == 0 and nota.is_file(), f"IV05 la nota non c'è: {r.returncode} {r.stderr[-200:]}"
    testo = nota.read_text(encoding="utf-8")
    assert "type: user" in testo and RISPOSTA in testo, f"IV05 nota senza tipo o senza risposta: {testo[:200]}"
    registro = (b.claude / "data" / "memoria" / "ricordate.json").read_text(encoding="utf-8")
    assert "persona-committenti" in registro, "IV05 la nota non è fra quelle che /fine annuncia"
    grezzo = (b.claude / "data" / "intervista" / "stato.json").read_text(encoding="utf-8")
    assert "committenti" in b.stato()["risposte"] and "redazioni" not in grezzo, \
        f"IV05 lo stato non segna la risposta o ne tiene il testo: {grezzo[:200]}"
    assert b.prossima()["prossima"] != "committenti", "IV05 la domanda con risposta torna"


def test_iv06(b: Banco) -> None:
    r = b.lancia("risposta", "committenti", "--testo", "La mia password è Rosso!Tramonto9 e la chiave sk-ant-api03-"
                 + "A" * 60)
    nota = b.claude / "data" / "memory" / "profilo" / "persona-committenti.md"
    assert not nota.exists(), f"IV06 una risposta con un segreto è salvata: {r.stdout[-160:]}"
    assert r.returncode != 0 and "committenti" not in b.stato().get("risposte", {}), \
        f"IV06 la domanda risulta fatta senza nota: rc {r.returncode}"


def test_iv07(b: Banco) -> None:
    casi = {}
    casi["oltre 42 giorni"] = b.lancia("proponi", oggi="2026-12-23")
    casi["ARTURO_INTERVISTA=0"] = b.lancia("proponi", ARTURO_INTERVISTA="0")
    casi["memoria spenta"] = b.lancia("proponi", ARTURO_MEMORIA="0")
    (b.claude / "data" / "setup-fatto").unlink()
    casi["senza /setup"] = b.lancia("proponi")
    (b.claude / "data" / "setup-fatto").write_text("2026-11-10\n", encoding="utf-8")
    b.lancia("spegni")
    casi["spenta"] = b.lancia("proponi")
    parlano = [k for k, r in casi.items() if _domanda(r.stdout)]
    assert not parlano, f"IV07 l'intervista parla quando deve tacere: {parlano}"
    b.lancia("accendi")
    assert _domanda(b.lancia("proponi").stdout), "IV07 accendi non la riprende"


def test_iv08(b: Banco) -> None:
    r = b.lancia("--stdin", script="contesto.py", stdin="libro -- --rotazione scrivere il capitolo\n")
    assert r.returncode == 0 and "INTERVISTA" not in r.stdout and not b.stato(), \
        f"IV08 in rotazione la domanda esce o lo stato si scrive: {r.returncode} {r.stdout[-200:]}"
    r = b.lancia("libro", script="contesto.py")
    assert r.returncode == 0 and "INTERVISTA" in r.stdout and _domanda(r.stdout) == "committenti", \
        f"IV08 arturo contesto non stampa la domanda: {r.returncode} {r.stdout[-300:]}"


def test_iv09(b: Banco) -> None:
    assert b.lancia("salta", "committenti").returncode == 0, "IV09 salta non va"
    assert _domanda(b.lancia("proponi").stdout) == "parola-voce", "IV09 la domanda saltata torna"
    profilo = b.claude / "data" / "memory" / "profilo"
    profilo.mkdir(parents=True, exist_ok=True)
    (profilo / "persona-parola-fonti.md").write_text(
        "---\nname: persona-parola-fonti\ndescription: x\ntype: user\n---\nfonti in Dropbox\n", encoding="utf-8")
    domani = _domanda(b.lancia("proponi", oggi="2026-11-16").stdout)
    assert domani == "parola-voce", f"IV09 dopo parola-voce: {domani}"
    b.lancia("salta", "parola-voce")
    dopo = _domanda(b.lancia("proponi", oggi="2026-11-17").stdout)
    assert dopo == "ricorrente", f"IV09 una nota persona-ID già in memoria non copre la domanda: {dopo}"


def test_iv10(b: Banco) -> None:
    r = b.lancia("intervista", "stato", script="arturo")
    assert r.returncode == 0 and "intervista:" in r.stdout, f"IV10 arturo intervista non arriva: {r.stderr[-200:]}"
    inizio = (b.repo / "commands" / "inizio.md").read_text(encoding="utf-8")
    assert "`INTERVISTA`" in inizio and "arturo intervista risposta <id>" in inizio, \
        "IV10 /inizio non racconta l'intervista"
    privacy = (b.repo / "docs" / "privacy.md").read_text(encoding="utf-8")
    assert "## L'intervista che continua" in privacy, "IV10 la privacy non racconta l'intervista"


def test_iv11(b: Banco) -> None:
    sorgente = (b.repo / "bin" / "intervista.py").read_text(encoding="utf-8")
    vietati = re.findall(r"(?m)^\s*(?:import|from)\s+(socket|urllib|http|telemetria|ssl)\b", sorgente)
    assert not vietati, f"IV11 intervista.py importa rete o telemetria: {vietati}"


def test_iv12(b: Banco) -> None:
    altra = b.lancia("risposta", "committenti", "--testo", RISPOSTA)
    assert altra.returncode == 0 and "SKILL:" not in altra.stdout, \
        f"IV12 la proposta di una skill esce per un'altra domanda: {altra.stdout[-200:]}"
    lavoro = "Ogni lunedì scrivo il riepilogo della settimana per la redazione."
    prima = b.lancia("risposta", "ricorrente", "--testo", lavoro)
    assert prima.returncode == 0 and "SKILL:" in prima.stdout and "/creaskill" in prima.stdout, \
        f"IV12 dopo ricorrente non esce la proposta di /creaskill: {prima.returncode} {prima.stdout[-200:]}"
    assert "proposta" in b.stato().get("skill", {}), f"IV12 lo stato non segna la proposta: {b.stato()}"
    # La persona toglie la nota dalla memoria e risponde di nuovo: la proposta non torna.
    (b.claude / "data" / "memory" / "profilo" / "persona-ricorrente.md").unlink()
    seconda = b.lancia("risposta", "ricorrente", "--testo", lavoro + " Anche il venerdì.")
    assert seconda.returncode == 0 and "SKILL:" not in seconda.stdout, \
        f"IV12 la proposta torna una seconda volta: {seconda.returncode} {seconda.stdout[-200:]} {seconda.stderr[-200:]}"
    no = b.lancia("skill", "no")
    assert no.returncode == 0 and b.stato()["skill"].get("esito") == "no", \
        f"IV12 il no non resta nello stato: {no.returncode} {b.stato().get('skill')}"
    assert b.prossima()["skill"]["esito"] == "no", "IV12 stato --json non dice il no"
    grezzo = (b.claude / "data" / "intervista" / "stato.json").read_text(encoding="utf-8")
    assert "riepilogo" not in grezzo, f"IV12 lo stato tiene il testo della risposta: {grezzo[:200]}"
    assert b.lancia("skill", "forse").returncode == 3, "IV12 skill accetta un valore che non è sì o no"
    inizio = (b.repo / "commands" / "inizio.md").read_text(encoding="utf-8")
    assert "stampa la riga `SKILL`" in inizio and "arturo intervista skill no" in inizio \
        and "commands/creaskill.md" in inizio, "IV12 /inizio non dice cosa fare della riga SKILL"


CASI = [(f"IV{n:02d}", f) for n, f in enumerate(
    (test_iv01, test_iv02, test_iv03, test_iv04, test_iv05, test_iv06, test_iv07, test_iv08, test_iv09,
     test_iv10, test_iv11, test_iv12), start=1)]

VELENI = (
    ("IV01", [("docs/mestieri.md", "- `consegna`:", "- consegna:")], "domande per tutti"),
    ("IV02", [("bin/intervista.py", "(len(punti) > 1 and punti[1][0] == punti[0][0])", "False")], "pareggio"),
    ("IV03", [("bin/intervista.py", "if copre and any(", "if False and any(")], "Chi sono"),
    ("IV04", [("bin/intervista.py", 'if stato.get("ultima") == oggi().isoformat():', "if False:")], "stesso giorno"),
    ("IV05", [("bin/intervista.py", '"--tipo", "user"', '"--tipo", "project"')], "la nota non c'è"),
    ("IV06", [("bin/intervista.py", "    if rc != 0:\n        return rc\n", "")], "risulta fatta"),
    ("IV07", [("bin/intervista.py", "    if passati > GIORNI:", "    if False:")], "deve tacere"),
    ("IV08", [("bin/contesto.py", "    if not rotazione:\n        domanda = sezione_intervista()",
               "    if True:\n        domanda = sezione_intervista()")], "rotazione"),
    ("IV09", [("bin/intervista.py", "or PREFISSO_NOTA + i in gia:", ":")], "già in memoria"),
    ("IV10", [("bin/arturo", '    "intervista": ("intervista",', '    "intervista-vecchia": ("intervista",')],
     "non arriva"),
    ("IV11", [("bin/intervista.py", "import argparse\n", "import argparse\nimport urllib\n")], "rete o telemetria"),
    ("IV12", [("bin/intervista.py", 'not isinstance(stato.get("skill"), dict)', "True")], "seconda volta"),
)


def avvelena(repo: Path) -> int:
    assert len(VELENI) == len(CASI), f"veleni {len(VELENI)} per {len(CASI)} controlli"
    casi = dict(CASI)
    inerti = []
    for codice, modifiche, motivo in VELENI:
        copia = Path(tempfile.mkdtemp(prefix="arturo-veleno-intervista."))
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
