#!/usr/bin/env python3
"""C01-C03: /aggiorna fa il merge in una copia di prova, mai nei file in uso (12/10/2026).

Il caso vero: il 12/10 un utente con un repository suo come origin ha lanciato /aggiorna. Lui e Arturo
avevano aggiunto righe diverse alla lista deny di settings.json, il merge e' andato in conflitto e ha
lasciato i marcatori nei file che Claude Code legge, con le guardie spente. In piu', la procedura che
girava era quella installata, vecchia: la correzione del 9/10 arrivava con lo stesso merge.

C01 durante un conflitto vero settings.json di ~/.claude non contiene mai un marcatore, in nessun
momento, e l'esito nomina il conflitto e il file. C02 risolto il conflitto nella copia di prova, il
blocco di «Risolvere un conflitto» porta dentro il risultato: la config e' integra, l'aggiornamento
registrato, la copia di prova tolta. C03 il Passo 3 lancia la procedura della versione in arrivo, non
quella installata.

Il «in nessun momento» di C01 lo guarda un git finto in testa al PATH: dopo ogni comando git vero
controlla settings.json di ~/.claude e annota ogni marcatore che trova.

Sulla base 0aee68c ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, Dict

_spec = importlib.util.spec_from_file_location("aggiorna_sicuro", Path(__file__).with_name("test_aggiorna_sicuro.py"))
assert _spec and _spec.loader
_sicuro = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_sicuro)
Lab, blocco, read, SHELL, SECONDA = _sicuro.Lab, _sicuro.blocco, _sicuro.read, _sicuro.SHELL, _sicuro.SECONDA

SPIA_GIT = r'''#!/bin/bash
# Il git vero, poi un'occhiata a settings.json della config in uso.
"@VERO@" "$@"; rc=$?
if grep -qE '^(<<<<<<<|>>>>>>>)' "$SPIA_VIVA/settings.json" 2>/dev/null; then
  echo "git $*" >> "$SPIA_LOG"
fi
exit $rc
'''

TUO = '"Edit(~/.zshenv)"'
LORO = '"Edit(~/.profile)"'


def con_deny(voce: str) -> Callable[[str], str]:
    def fare(testo: str) -> str:
        dati = json.loads(testo)
        dati["permissions"]["deny"].append(json.loads(voce))
        return json.dumps(dati, indent=2) + "\n"
    return fare


def conflitto_sulla_deny(lab: Lab) -> None:
    """Lui aggiunge una riga alla lista deny e la pubblica sul suo repository, Arturo ne aggiunge
    un'altra nello stesso punto: il merge va in conflitto davvero."""
    lab.pubblica(lab.autore, {"settings.json": lambda t: json.dumps(
        {**json.loads(t), "permissions": {"deny": ["Edit(~/.bash_profile)"]}}, indent=2) + "\n"}, "deny")
    lab.git(lab.utente, "pull", "-q", "origin", "main")
    lab.personale()
    (lab.utente / "settings.json").write_text(con_deny(TUO)(read(lab.utente / "settings.json")))
    lab.git(lab.utente, "commit", "-q", "-am", "chore: session sync")
    lab.git(lab.utente, "push", "-q", "origin", "main")
    lab.pubblica(lab.autore, {"settings.json": con_deny(LORO), "NOVITA.md": lambda t: SECONDA}, "v1")


def spia(lab: Lab) -> Path:
    finti = lab.base / "spia"
    finti.mkdir()
    vero = shutil.which("git", path=os.environ.get("PATH"))
    assert vero, "prova: git mancante"
    (finti / "git").write_text(SPIA_GIT.replace("@VERO@", vero))
    (finti / "git").chmod(0o755)
    log = lab.base / "marcatori-visti"
    lab.env.update(PATH=f"{finti}{os.pathsep}{os.environ.get('PATH', '')}", SPIA_VIVA=str(lab.utente),
                   SPIA_LOG=str(log))
    return log


def aggiorna(repo: Path) -> str:
    return read(repo / "commands" / "aggiorna.md")


def per_shell(prova: Callable[[Lab], None], repo: Path) -> None:
    assert SHELL, "bash mancante: i blocchi non si provano"
    for shell in SHELL:
        with tempfile.TemporaryDirectory() as tmp:
            prova(Lab(repo, Path(tmp), shell))


def passo3_in_conflitto(lab: Lab, repo: Path, codice: str) -> str:
    testo = aggiorna(repo)
    lab.lancia(blocco(testo, "## Passo 1", codice))
    return lab.lancia(blocco(testo, "## Passo 3", codice))


def test_c01(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        conflitto_sulla_deny(lab)
        prima = lab.head()
        log = spia(lab)
        uscita = passo3_in_conflitto(lab, repo, "C01")
        visti = read(log) if log.exists() else ""
        assert not visti, \
            f"C01 con {lab.shell} settings.json in uso ha avuto i marcatori di conflitto dopo: {visti.strip()!r}"
        assert lab.head() == prima and lab.config_integra(), f"C01 con {lab.shell} la copia e' cambiata: {uscita[-300:]!r}"
        assert "CONFLITTO" in uscita and "settings.json" in uscita, \
            f"C01 con {lab.shell} l'esito non nomina il conflitto e il file: {uscita[-400:]!r}"
    per_shell(prova, repo)


def test_c02(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        conflitto_sulla_deny(lab)
        uscita = passo3_in_conflitto(lab, repo, "C02")
        stato = lab.utente / ".git" / "arturo-aggiorna-copia"
        assert stato.exists(), f"C02 con {lab.shell} nessuna copia di prova in attesa: {uscita[-300:]!r}"
        copia = Path(read(stato).split()[0])
        risolto = {"env": {"A": "1", "B": "2", "C": "3"},
                   "permissions": {"deny": ["Edit(~/.bash_profile)", "Edit(~/.zshenv)", "Edit(~/.profile)"]}}
        (copia / "settings.json").write_text(json.dumps(risolto, indent=2) + "\n")
        lab.git(copia, "add", "settings.json")
        lab.git(copia, "commit", "-q", "--no-edit")
        fine = lab.lancia(blocco(aggiorna(repo), "### Risolvere un conflitto", "C02"))
        impostazioni = json.loads(read(lab.utente / "settings.json"))
        assert "APPLICATO" in fine and impostazioni["permissions"]["deny"] == risolto["permissions"]["deny"], \
            f"C02 con {lab.shell} il risultato risolto non arriva in ~/.claude: {fine[-400:]!r}"
        assert "Seconda" in read(lab.utente / "NOVITA.md") and lab.config_integra() and lab.registro(), \
            f"C02 con {lab.shell} aggiornamento incompleto, config rotta o non registrato: {fine[-300:]!r}"
        copie = lab.git(lab.utente, "worktree", "list")
        assert len(copie.splitlines()) == 1 and not copia.exists() and not stato.exists(), \
            f"C02 con {lab.shell} la copia di prova resta dopo l'applicazione: {copie!r}"
    per_shell(prova, repo)


def test_c03(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        applica = lab.autore / "bin" / "aggiorna-applica.sh"
        if applica.exists():
            testo = read(applica)
            primo_a_capo = testo.index("\n") + 1
            lab.pubblica(lab.autore, {"bin/aggiorna-applica.sh":
                                      lambda t: t[:primo_a_capo] + 'echo "PROCEDURA_IN_ARRIVO"\n' + t[primo_a_capo:],
                                      "NOVITA.md": lambda t: SECONDA}, "v1")
        else:
            lab.pubblica(lab.autore, {"NOVITA.md": lambda t: SECONDA}, "v1")
        testo = aggiorna(repo)
        lab.lancia(blocco(testo, "## Passo 1", "C03"))
        uscita = lab.lancia(blocco(testo, "## Passo 3", "C03"))
        assert "PROCEDURA_IN_ARRIVO" in uscita, \
            f"C03 con {lab.shell} il Passo 3 non usa la procedura della versione in arrivo: {uscita[-300:]!r}"
        assert "Seconda" in read(lab.utente / "NOVITA.md"), f"C03 con {lab.shell} l'aggiornamento non e' applicato"
    per_shell(prova, repo)


TESTS: Dict[str, Callable[[Path], None]] = {"C01": test_c01, "C02": test_c02, "C03": test_c03}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    parser.add_argument("--solo", help="codici separati da virgola, per i veleni")
    args = parser.parse_args()
    repo = args.repo.resolve()
    scelti = {k: v for k, v in TESTS.items() if not args.solo or k in args.solo.split(",")}
    if args.baseline_ref:
        rossi, altro = _sicuro.baseline(scelti, repo)
        assert not altro and rossi == list(scelti), \
            "baseline non discriminante: ogni controllo deve fallire col suo codice.\n" + "\n".join(altro)
        print(f"BASELINE_DISCRIMINANTE={','.join(rossi)}")
        return 0
    for test in scelti.values():
        test(repo)
    print(f"PASS {','.join(scelti)} controlli={len(scelti)} shell={','.join(SHELL)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
