#!/usr/bin/env python3
"""CT01: un aggiornamento in conflitto dice alla telemetria quale file lo blocca (20/10/2026, #3589).

Il caso vero: il riepilogo del 19/10 mostrava un'installazione con un aggiornamento in conflitto e
nessun file nell'elenco della deriva, quindi la causa non si leggeva. settings.json, il file più
conteso, non entra nella deriva.

CT01 dopo un conflitto vero su settings.json la coda della telemetria ha l'evento `aggiorna
conflitto` e, dopo, la riga `deriva file:settings.json`. Solo il percorso dentro Arturo, mai il
contenuto: nessuna riga della coda contiene le voci della lista deny.

Sulla base 3184831 il controllo deve fallire con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
from pathlib import Path

_spec = importlib.util.spec_from_file_location("aggiorna_copia", Path(__file__).with_name("test_aggiorna_copia.py"))
assert _spec and _spec.loader
_copia = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_copia)
_sicuro = _copia._sicuro


def test_ct01(repo: Path) -> None:
    def prova(lab) -> None:
        _copia.conflitto_sulla_deny(lab)
        # Il banco gira con la telemetria spenta: qui serve accesa. Dalla HOME temporanea non parte
        # niente verso il server vero, e registra scrive solo la coda.
        lab.env.update(ARTURO_TELEMETRIA="1")
        lab.env.pop("DO_NOT_TRACK", None)
        # La config del laboratorio ha solo lo script degli aggiornamenti: la telemetria si copia accanto,
        # fuori da git (pulita() guarda solo i file tracciati).
        for nome in ("telemetria.py", "todo_store.py"):
            shutil.copy(str(repo / "bin" / nome), str(lab.utente / "bin" / nome))
        uscita = _copia.passo3_in_conflitto(lab, repo, "CT01")
        assert "CONFLITTO" in uscita, f"CT01 con {lab.shell} prova: niente conflitto: {uscita[-300:]!r}"
        coda = lab.utente / "data" / "telemetria" / "coda.jsonl"
        righe = [json.loads(r) for r in coda.read_text(encoding="utf-8").splitlines()] if coda.exists() else []
        eventi = [(r["evento"], r["valore"]) for r in righe]
        assert ("aggiorna", "conflitto") in eventi, f"CT01 con {lab.shell} prova: niente aggiorna conflitto: {eventi}"
        dopo = eventi[eventi.index(("aggiorna", "conflitto")):]
        assert ("deriva", "file:settings.json") in dopo, \
            f"CT01 con {lab.shell} la telemetria non dice quale file blocca l'aggiornamento: {eventi}"
        testo = coda.read_text(encoding="utf-8")
        assert "zshenv" not in testo and "profile" not in testo, f"CT01 con {lab.shell} esce il contenuto del file: {testo!r}"
    _copia.per_shell(prova, repo)


TESTS = {"CT01": test_ct01}


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
