#!/usr/bin/env python3
"""SN01-SN03: le segnalazioni n. 15 e n. 16 arrivate con /segnala il 26/10/2026, e il messaggio di
/segnala quando il server non accetta.

SN01 nel worktree aperto da /inizio la guardia di Claude Code rifiuta anche un heredoc
     (`python3 - <<'E'`: "too complex to verify that it stays inside the worktree"). La voce del
     worktree di /inizio nomina cicli, variabili e $(...), ma non l'heredoc: Claude lo tentava, e la
     persona vedeva il rifiuto (segnalazione n. 15). Gli altri punti della n. 15 ("$HOME" in /fine,
     il merge da dentro il worktree, i file ignorati) sono già corretti e sorvegliati da F13, F14 e F16.
SN02 un comando che la persona lancia col prefisso `!` gira senza un terminale vero: sudo si ferma con
     "a terminal is required to read the password". Lo stile Conciso, sempre caricato, dice che un
     comando con sudo o con una password non passa dal `!`: prima una via senza sudo, poi il
     Terminale (segnalazione n. 16).
SN03 il 27/10/2026 una /segnala di Liliana ha risposto "il server non risponde" e in D1 non è arrivato
     niente. Il client trattava ogni codice fuori da 2xx, 400 e 413 come "non risponde", senza dire
     quale. Ora il messaggio porta "(risposta N)", o "(nessuna risposta dalla rete)" se la rete tace.

Sulla base 32a574e ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_sn01(repo: Path) -> None:
    inizio = read(repo / "commands" / "inizio.md")
    voce = "**Worktree, solo se c'è quella sessione.**"
    assert voce in inizio and "## FASE 2" in inizio, "SN01 /inizio non ha la voce del worktree"
    voce = inizio[inizio.index(voce):inizio.index("## FASE 2")]
    assert "heredoc" in voce and "<<" in voce, \
        "SN01 la voce del worktree di /inizio non dice che la guardia rifiuta anche un heredoc"
    assert "scratchpad" in voce and voce.index("heredoc") < voce.index("scratchpad"), \
        "SN01 la voce del worktree di /inizio non manda l'heredoc in uno script nello scratchpad"


def test_sn02(repo: Path) -> None:
    stile = read(repo / "output-styles" / "conciso.md")
    titolo = "## I comandi che lancia la persona"
    assert titolo in stile, "SN02 lo stile Conciso non dice come passare un comando alla persona"
    sezione = stile[stile.index(titolo):]
    sezione = sezione[:sezione.find("\n## ", 1)] if "\n## " in sezione[1:] else sezione
    assert all(t in sezione for t in ("`!`", "sudo", "password", "Terminale")), \
        "SN02 lo stile Conciso non dice che sudo e password non passano dal prefisso !"
    assert sezione.index("senza sudo") < sezione.index("Terminale"), \
        "SN02 lo stile Conciso non cerca prima una via senza sudo"


def test_sn03(repo: Path) -> None:
    """Il messaggio "il server non risponde" porta il codice HTTP, o dice che la rete non ha risposto."""
    spec = importlib.util.spec_from_file_location("telemetria_banco", Path(__file__).with_name("test_telemetria.py"))
    assert spec and spec.loader
    banco = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(banco)
    srv = banco.Server()
    srv.status = 503
    for lab, atteso in ((banco.Lab(repo, srv), "(risposta 503)"), (banco.Lab(repo), "(nessuna risposta dalla rete)")):
        bozza = lab.dir / "bozza.md"
        bozza.write_text("La segnalazione non parte.", encoding="utf-8")
        r = lab.arturo("segnala", "prepara", "--tipo", "problema", "--titolo", "prova", "--file", str(bozza))
        pronta = next(x for x in r.stdout.splitlines() if x.startswith("PRONTA: "))[8:]
        r = lab.arturo("segnala", "invia", "--canale", "arturo", "--file", pronta)
        attesa = list((lab.home / ".claude" / "data" / "segnalazioni").glob("*.attesa.json"))
        assert r.returncode == 0 and len(attesa) == 1, f"SN03 la segnalazione non resta in attesa: {r.stdout!r} {r.stderr!r}"
        assert atteso in r.stdout, f"SN03 il messaggio non dice {atteso}: {r.stdout!r}"


TESTS = {"SN01": test_sn01, "SN02": test_sn02, "SN03": test_sn03}


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
