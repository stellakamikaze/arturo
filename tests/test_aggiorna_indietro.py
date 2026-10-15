#!/usr/bin/env python3
"""C07-C09: la copia di prova resta e /aggiorna indietro gira nella copia di prova (15/10/2026).

C07 la copia di prova in attesa sta dentro la cartella .git, non nella cartella temporanea che il
sistema svuota da solo. C08 /aggiorna indietro con un commit suo successivo che tocca la stessa riga
dell'aggiornamento: nessun marcatore nei file in uso, ~/.claude com'era, l'esito lo dice. C09
/aggiorna indietro con un commit suo su un altro file: si torna alla versione di prima, il suo commit
resta, la riga del registro sparisce, la copia di prova non resta.

Riusa il laboratorio di test_aggiorna_copia.py. Sulla base 4515e63 ogni controllo deve fallire con un
AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
from typing import Callable, Dict

_spec = importlib.util.spec_from_file_location("aggiorna_copia", Path(__file__).with_name("test_aggiorna_copia.py"))
assert _spec and _spec.loader
_copia = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_copia)
Lab, blocco, read, SECONDA = _copia.Lab, _copia.blocco, _copia.read, _copia.SECONDA
_sicuro, aggiorna, per_shell = _copia._sicuro, _copia.aggiorna, _copia.per_shell
conflitto_sulla_deny, passo3_in_conflitto, spia = _copia.conflitto_sulla_deny, _copia.passo3_in_conflitto, _copia.spia


def test_c07(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        conflitto_sulla_deny(lab)
        passo3_in_conflitto(lab, repo, "C07")
        copia = Path(read(lab.utente / ".git" / "arturo-aggiorna-copia").split()[0]).resolve()
        dentro = (lab.utente / ".git").resolve()
        assert dentro in copia.parents, f"C07 con {lab.shell} la copia di prova sta fuori da .git: {copia}"
        assert not lab.git(lab.utente, "status", "--porcelain"), f"C07 con {lab.shell} git status vede la copia di prova"
    per_shell(prova, repo)


def applicato_poi_commit(lab: Lab, repo: Path, codice: str, file: str, fare: Callable[[str], str]) -> str:
    """Un aggiornamento applicato dal Passo 3, poi un commit suo: torna l'HEAD prima dell'aggiornamento."""
    prima = lab.head()
    lab.pubblica(lab.autore, {"settings.json": lambda t: t.replace('"B": "2"', '"B": "autore"'),
                              "NOVITA.md": lambda t: SECONDA}, "v1")
    testo = aggiorna(repo)
    lab.lancia(blocco(testo, "## Passo 1", codice))
    uscita = lab.lancia(blocco(testo, "## Passo 3", codice))
    assert "APPLICATO" in uscita and lab.registro(), f"{codice} prova: l'aggiornamento non e' applicato: {uscita[-300:]!r}"
    (lab.utente / file).write_text(fare(read(lab.utente / file)) if (lab.utente / file).exists() else fare(""))
    lab.git(lab.utente, "add", file)
    lab.git(lab.utente, "commit", "-q", "-m", "suo")
    return prima


def indietro(lab: Lab, repo: Path, codice: str) -> str:
    testo = aggiorna(repo)
    blocchi = _sicuro.blocchi(testo, "## Tornare indietro", codice)
    return lab.lancia(blocchi[1])


def test_c08(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        applicato_poi_commit(lab, repo, "C08", "settings.json", lambda t: t.replace('"B": "autore"', '"B": "suo"'))
        adesso, registro = lab.head(), lab.registro()
        log = spia(lab)
        uscita = indietro(lab, repo, "C08")
        visti = read(log) if log.exists() else ""
        assert not visti, f"C08 con {lab.shell} settings.json in uso ha avuto i marcatori di conflitto dopo: {visti.strip()!r}"
        assert lab.head() == adesso and lab.config_integra() and lab.registro() == registro, \
            f"C08 con {lab.shell} un ritorno in conflitto ha cambiato ~/.claude: {uscita[-300:]!r}"
        assert "RITORNO ANNULLATO" in uscita, f"C08 con {lab.shell} l'esito non dice che il ritorno e' annullato: {uscita[-300:]!r}"
        assert len(lab.git(lab.utente, "worktree", "list").splitlines()) == 1, f"C08 con {lab.shell} resta un worktree"
    per_shell(prova, repo)


def test_c09(repo: Path) -> None:
    def prova(lab: Lab) -> None:
        prima = applicato_poi_commit(lab, repo, "C09", "mio.md", lambda t: "mio\n")
        uscita = indietro(lab, repo, "C09")
        assert "TORNATO INDIETRO" in uscita, f"C09 con {lab.shell} l'esito non dice TORNATO INDIETRO: {uscita[-300:]!r}"
        assert "Seconda" not in read(lab.utente / "NOVITA.md") and (lab.utente / "mio.md").exists(), \
            f"C09 con {lab.shell} non torna alla versione di prima o perde il suo commit: {uscita[-300:]!r}"
        assert lab.git(lab.utente, "rev-parse", "HEAD~1") == prima and not lab.registro().strip(), \
            f"C09 con {lab.shell} storia o registro sbagliati dopo il ritorno: {uscita[-300:]!r}"
        assert lab.config_integra() and len(lab.git(lab.utente, "worktree", "list").splitlines()) == 1, \
            f"C09 con {lab.shell} config rotta o worktree rimasto"
    per_shell(prova, repo)


TESTS: Dict[str, Callable[[Path], None]] = {"C07": test_c07, "C08": test_c08, "C09": test_c09}


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
    print(f"PASS {','.join(scelti)} controlli={len(scelti)} shell={','.join(_copia.SHELL)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
