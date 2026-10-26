#!/usr/bin/env python3
"""AP01: gli archivi della persona non fermano l'aggiornamento (26/10/2026, segnalazione n. 14).

Il caso vero: su una config con Arturo come origin alcuni handoff erano tracciati da git. La retention
di /fine ne cancella uno e riscrive INDEX.md, e il sync della FASE 9 non li salva, perché il remote è
pubblico. L'aggiornamento automatico non partiva più, a ogni sessione: "APPLICAZIONE NON PARTITA:
questi file hanno modifiche tue non ancora salvate con un commit".

AP01 con un handoff tracciato cancellato e INDEX.md riscritto, la procedura della versione in arrivo
applica l'aggiornamento e lascia gli archivi come la persona li ha lasciati. Un file di Arturo
cambiato e non salvato ferma ancora l'applicazione, e lo nomina.

Sulla base 7337350 il controllo deve fallire con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("aggiorna_copia", Path(__file__).with_name("test_aggiorna_copia.py"))
assert _spec and _spec.loader
_copia = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_copia)
_sicuro = _copia._sicuro
read, SECONDA, BASH = _copia.read, _copia.SECONDA, _copia.BASH


def applica(lab) -> str:
    """Come bin/aggiornamenti.py: la procedura della versione in arrivo, in modo rebase con Arturo come origin."""
    lab.git(lab.utente, "fetch", "-q", "origin")
    procedura = lab.base / "procedura-in-arrivo.sh"
    procedura.write_text(lab.git(lab.utente, "show", "origin/main:bin/aggiorna-applica.sh") + "\n", encoding="utf-8")
    return lab.lancia(f'"{BASH}" "{procedura}" "{lab.utente}" rebase origin/main')


def test_ap01(repo: Path) -> None:
    def prova(lab) -> None:
        cartella = lab.utente / "data" / "handoffs"
        vecchio = cartella / "libro" / "HANDOFF_2026-10-01_10-00.md"
        vecchio.parent.mkdir(parents=True)
        vecchio.write_text("# vecchio\n", encoding="utf-8")
        (cartella / "INDEX.md").write_text("# Indice\n- libro 1/10\n", encoding="utf-8")
        lab.git(lab.utente, "add", "data/handoffs")
        lab.git(lab.utente, "commit", "-q", "-m", "chore: session sync")
        vecchio.unlink()
        (cartella / "INDEX.md").write_text("# Indice\n- libro 26/10\n", encoding="utf-8")
        lab.pubblica(lab.autore, {"NOVITA.md": lambda t: SECONDA}, "v1")
        uscita = applica(lab)
        assert "APPLICATO" in uscita and "Seconda" in read(lab.utente / "NOVITA.md"), \
            f"AP01 con {lab.shell} gli handoff non salvati fermano l'aggiornamento: {uscita[-400:]!r}"
        assert not vecchio.exists() and "26/10" in read(cartella / "INDEX.md") and lab.config_integra(), \
            f"AP01 con {lab.shell} l'aggiornamento ha cambiato gli archivi della persona: {uscita[-400:]!r}"
        lab.pubblica(lab.autore, {"NOVITA.md": lambda t: t + "\n## 2026-10-27 — Terza\n"}, "v2")
        lab.cambia(lab.utente, "hooks/guardia.py", "True", "False")
        prima = lab.head()
        uscita = applica(lab)
        assert "APPLICAZIONE NON PARTITA" in uscita and "hooks/guardia.py" in uscita and lab.head() == prima, \
            f"AP01 con {lab.shell} un file di Arturo cambiato non ferma più l'aggiornamento: {uscita[-400:]!r}"
    _copia.per_shell(prova, repo)


TESTS = {"AP01": test_ap01}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.baseline_ref:
        rossi, altro = _sicuro.baseline(TESTS, repo)
        assert not altro and rossi == list(TESTS), \
            "baseline non discriminante: ogni controllo deve fallire col suo codice.\n" + "\n".join(altro)
        print(f"BASELINE_DISCRIMINANTE={','.join(rossi)}")
        return 0
    for test in TESTS.values():
        test(repo)
    print(f"PASS {','.join(TESTS)} controlli={len(TESTS)} shell={','.join(_copia.SHELL)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
