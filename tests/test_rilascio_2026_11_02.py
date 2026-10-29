#!/usr/bin/env python3
"""RL01-RL04: i ritocchi prima del rilascio del 2/11/2026.

RL01 /setup sta sotto il tetto di 30 KB dell'audit: la FASE 8d (Lancillotto, solo Mac) vive in
     shared/setup-lancillotto.md, che /setup nomina e che ha ancora il comando d'installazione (#4104).
RL02 i testi seguono i comandi nuovi del 28/10 (#4105): il README conta i comandi come i file di
     commands/ e la rotta come quelli in vetrina, dice l'avviso prima di un ultracode; il pannello
     /dafare non promette che ogni tasto si annulla; segnala.py racconta stato; sessione.py non rimanda
     alla pagina personale e non usa una funzione privata di segnala.
RL03 il tasto o del pannello passa il titolo atteso, e arturo sessione si ferma se il todo con quel
     numero ha un altro titolo (#4106): dopo un merge la sessione partirebbe sul lavoro sbagliato.
RL04 /segnala non vede un segreto nel base64 di un'immagine in linea, come la guardia credenziali
     (#4078); una chiave nel testo la trova ancora.

Sulla base 60b7d8d ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

PAROLE = {9: "Nove", 10: "Dieci", 11: "Undici", 12: "Dodici"}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def test_rl01(repo: Path) -> None:
    setup = repo / "commands" / "setup.md"
    peso = setup.stat().st_size
    assert peso <= 30000, f"RL01 /setup pesa {peso} byte, oltre il tetto di 30000 dell'audit"
    testo = read(setup)
    fase = testo[testo.index("## FASE 8d"):testo.index("## FASE 9")]
    assert "~/.claude/shared/setup-lancillotto.md" in fase, "RL01 la FASE 8d non dice dove leggere la sua procedura"
    parte = read(repo / "shared" / "setup-lancillotto.md")
    assert "gh repo clone stellakamikaze/lancillotto" in parte and "installa.sh" in parte and "Accessibilità" in parte, \
        "RL01 shared/setup-lancillotto.md non ha domanda, controlli e installazione"


def test_rl02(repo: Path) -> None:
    readme = read(repo / "README.md")
    comandi = len(list((repo / "commands").glob("*.md")))
    assert f"**{comandi} slash command**" in readme and f"{comandi} slash command (" in readme, \
        f"RL02 il README non conta {comandi} slash command"
    rotta = readme[readme.index("### La rotta"):]
    rotta = rotta[:rotta.index("\n## ")] if "\n## " in rotta else rotta
    vetrina = len(re.findall(r"^- \*\*`/", rotta, re.MULTILINE))
    assert f"{PAROLE.get(vetrina, vetrina)} comandi, e Arturo" in rotta, \
        f"RL02 la rotta mostra {vetrina} comandi ma il testo ne conta un altro numero"
    riga = next((r for r in readme.splitlines() if r.startswith("- `inject-now.sh`")), "")
    blocco = readme[readme.index(riga):readme.index("- `input-notifier-start.sh`")] if riga else ""
    assert "ultracode" in blocco, "RL02 il README non dice che inject-now avvisa prima di un ultracode"
    pannello = read(repo / "skills" / "dafare" / "hooks" / "register.tsx")
    assert 'Ogni tasto si annulla con "u"' not in pannello, "RL02 il pannello promette che ogni tasto si annulla"
    assert "La CLI dei todo si è fermata" not in pannello, "RL02 un errore di arturo sessione parla della CLI dei todo"
    segnala = read(repo / "bin" / "segnala.py")
    assert "- stato:" in segnala.split('"""', 2)[1], "RL02 la docstring di segnala.py non racconta stato"
    sessione = read(repo / "bin" / "sessione.py")
    assert "dafare personale" not in sessione and "segnala._copia" not in sessione, \
        "RL02 sessione.py rimanda alla pagina personale o usa una funzione privata di segnala"


def test_rl03(repo: Path) -> None:
    pannello = read(repo / "skills" / "dafare" / "hooks" / "register.tsx")
    verbi = read(repo / "skills" / "dafare" / "hooks" / "verbi.mjs")
    # Il parametro lo costruisce solo titolo() di verbi.mjs, come per gli altri tasti (#4175).
    assert "'sessione'" in pannello and "titolo(t)" in pannello.split("async function apriSessione")[-1][:900] \
        and "export function titolo(t)" in verbi and "--titolo-atteso=${t.titolo}" in verbi, \
        "RL03 il tasto o non passa il titolo atteso"
    spec = importlib.util.spec_from_file_location("telemetria_banco", Path(__file__).with_name("test_telemetria.py"))
    assert spec and spec.loader
    banco = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(banco)
    lab = banco.Lab(repo)
    lab.env.update(ARTURO_SISTEMA="linux")
    r = lab.arturo("todo", "aggiungi", "Montare il mixer", "--progetto", "libro")
    assert r.returncode == 0, f"RL03 todo di prova non creato: {r.stderr!r}"
    r = lab.arturo("sessione", "--todo", "1", "--titolo-atteso=Montare il mixer", "--stampa")
    assert r.returncode == 0 and "Montare il mixer" in r.stdout, f"RL03 col titolo giusto non apre: {r.returncode} {r.stderr!r}"
    r = lab.arturo("sessione", "--todo", "1", "--titolo-atteso=Scrivere il capitolo", "--stampa")
    assert r.returncode == 1 and "non è più come" in r.stderr and "/inizio" not in r.stdout, \
        f"RL03 con un altro titolo la sessione parte lo stesso: {r.returncode} {r.stdout!r} {r.stderr!r}"


def test_rl04(repo: Path) -> None:
    chiave = "AKIA" + "ABCDEFGHIJKLMNOP"
    prova = ("import json, sys; sys.path.insert(0, sys.argv[1]); import segnala; "
             "print(json.dumps([segnala.segreti_trovati(t) for t in json.loads(sys.argv[2])]))")
    testi = ["schermata ![x](data:image/png;base64,iVBORw0KGgo" + chiave + "AAAA==) fine", "chiave " + chiave]
    r = subprocess.run([sys.executable, "-B", "-c", prova, str(repo / "bin"), json.dumps(testi)],
                       capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, f"RL04 segnala non si importa: {r.stderr[-300:]}"
    immagine, testo = json.loads(r.stdout.strip().splitlines()[-1])
    assert not immagine, f"RL04 /segnala vede {immagine} nel base64 di un'immagine in linea"
    assert testo, "RL04 /segnala non trova più una chiave scritta nel testo"


TESTS = {"RL01": test_rl01, "RL02": test_rl02, "RL03": test_rl03, "RL04": test_rl04}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.baseline_ref:
        rossi, altro = [], []
        for nome, test in TESTS.items():
            try:
                test(repo)
            except AssertionError as e:
                (rossi if str(e).startswith(nome) else altro).append(f"{nome}: {e}")
            except Exception as e:  # noqa: BLE001
                altro.append(f"{nome}: {type(e).__name__} {e}")
        assert not altro and len(rossi) == len(TESTS), \
            "baseline non discriminante: ogni controllo deve fallire col suo codice.\n" + "\n".join(altro + rossi)
        print(f"BASELINE_DISCRIMINANTE={','.join(r.split(':')[0] for r in rossi)}")
        return 0
    for test in TESTS.values():
        test(repo)
    print(f"PASS {','.join(TESTS)} controlli={len(TESTS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
