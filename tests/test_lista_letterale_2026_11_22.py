#!/usr/bin/env python3
"""LL01: curl e wget in una lista python letterale sono un programma visibile (22/11/2026, #6353).

La regola codice-nascosto (#6323) chiedeva conferma su `subprocess.run(['curl', '-s', 'https://x'])` in un heredoc
python: vedeva codice che lancia e la parola curl. AL01 (21/10) vuole muti il GET e l'invio verso un host
interno, perché exfil-guard legge già l'invio di un file in quella forma e il GET lo giudica il classificatore.
Ora una lista di soli testi letterali, passata direttamente a run, Popen, call, check_call o check_output, conta
curl e wget come visti. Un argomento calcolato lascia la lista nascosta, e rm, gh e i percorsi dei segreti in una
lista chiedono ancora.

Sulla base f69db25 il controllo deve fallire con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

_HEREDOC = "python3 - <<'PY'\nimport subprocess\n%s\nPY"


def test_ll01(repo: Path) -> None:
    spec = importlib.util.spec_from_file_location("gs_banco", repo / "tests" / "test_guardie_sicurezza.py")
    gs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gs)
    chiedono = [
        "subprocess.run(['rm', '-rf', '/tmp/x'])",
        "subprocess.run(['curl'] + args)",
        "subprocess.run(['curl', '-s', u])",
        "subprocess.run(['curl', f'https://{h}/'])",
        "subprocess.run(['curl', '-s', 'https://x']); subprocess.run(['curl', '-s', u])",
        "subprocess.run(['gh', 'repo', 'delete', 'x'])",
        "subprocess.run(['curl', '-s', 'https://x']); os.system('rm -rf ~')",
        "subprocess.run(['curl', '-s', '~/.ssh/id_rsa'])",
    ]
    tacciono = [
        "subprocess.run(['curl', '-s', 'https://example.org/'])",
        "subprocess.check_output([\"wget\", \"-q\", \"-O-\", \"http://127.0.0.1:8096/\"])",
        "r = subprocess.run(['curl', '-sS', 'http://localhost:9000/x',], capture_output=True)",
    ]
    sbagliati = []

    def prova(b) -> None:
        for c in chiedono:
            e = b.esito(_HEREDOC % c)
            if e not in ("ask", "block"):
                sbagliati.append(f"passa ({e}): {c}")
        for c in tacciono:
            e = b.esito(_HEREDOC % c)
            if e not in ("silent", "allow"):
                sbagliati.append(f"chiede ({e}): {c}")
    gs.con_banco(repo, prova)
    assert not sbagliati, "LL01 " + " | ".join(sbagliati)


TESTS = {"LL01": test_ll01}


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
        assert not altro and len(rossi) == len(TESTS), \
            "baseline non discriminante: ogni controllo deve fallire col suo codice.\n" + "\n".join(altro + rossi)
        print(f"BASELINE_DISCRIMINANTE={','.join(r.split(':')[0] for r in rossi)}")
        return 0
    for test in TESTS.values():
        test(repo)
    print(f"PASS {','.join(TESTS)} controlli={len(TESTS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
