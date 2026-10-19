#!/usr/bin/env python3
"""GU01-GU05: le guardie di Arturo e della config di chi lo mantiene diventano una sola (19/10/2026, #3612).

Fino al 19/10 le guardie si erano divise: Arturo aveva le correzioni #3506, la config di chi
mantiene Arturo aveva falsi positivi tolti e il confronto per dominio. Ora i file sono gli stessi,
e ciò che è personale sta in hooks/hosts-interni.local e hooks/api-fidate.local.

GU01 una voce col punto davanti in hosts-interni.local (`.esempio-interno.org`) vale per il dominio
     e per i sottodomini, e non apre un dominio che la contiene solo come prefisso.
GU02 una voce di una sola etichetta (`.org`) viene ignorata: non apre tutti i domini .org.
GU03 web-egress-guard tratta come interni i nomi `.local` (mDNS) e `.internal` (riservato da ICANN).
GU04 data-guard non chiede conferma per un file `.sql` scritto con una redirezione: è uno script, non
     un database. Un `.db` sovrascritto chiede ancora.
GU05 comms-prefilter toglie il corpo python che non usa la rete e non lancia programmi: un `mailto:`
     scritto in una stringa non è un invio. Tiene invece il corpo che lancia un programma per alias
     (`from os import system as s`), con os.posix_spawn o con os.startfile.

Sulla base dbaefa1 ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

LUNGA = "q=" + "x" * 400  # query mostruosa: verso un host esterno web-egress chiede conferma


def guardia(repo: Path, nome: str, dati: dict, interni: str = "") -> str:
    """La decisione della guardia copiata in una cartella di prova, con hosts-interni.local dato."""
    with tempfile.TemporaryDirectory() as td:
        hooks = Path(os.path.realpath(td)) / "hooks"
        shutil.copytree(repo / "hooks", hooks, ignore=shutil.ignore_patterns("__pycache__", "test_*", "test-*"))
        if interni:
            (hooks / "hosts-interni.local").write_text(interni, encoding="utf-8")
        env = dict(os.environ, HOME=td, USERPROFILE=td, ARTURO_TELEMETRIA="0")
        p = subprocess.run([sys.executable, "-B", str(hooks / nome)], input=json.dumps(dati),
                           capture_output=True, text=True, env=env, encoding="utf-8")
    if p.returncode == 2:
        return "block"
    out = p.stdout.strip()
    if not out:
        return "silent"
    try:
        return json.loads(out.splitlines()[-1])["hookSpecificOutput"]["permissionDecision"]
    except Exception:
        return "?"


def fetch(url: str) -> dict:
    return {"tool_name": "WebFetch", "tool_input": {"url": url, "prompt": "leggi"}, "cwd": "/", "session_id": "banco"}


def bash(comando: str) -> dict:
    return {"tool_name": "Bash", "tool_input": {"command": comando}, "cwd": "/", "session_id": "banco"}


def test_gu01(repo: Path) -> None:
    interni = ".esempio-interno.org\n"
    fuori = guardia(repo, "web-egress-guard.py", fetch(f"https://cattivo.example/?{LUNGA}"), interni)
    assert fuori == "ask", f"GU01 il banco non discrimina: un host esterno con query lunga riceve {fuori}"
    for host in ("esempio-interno.org", "api.esempio-interno.org"):
        d = guardia(repo, "web-egress-guard.py", fetch(f"https://{host}/?{LUNGA}"), interni)
        assert d in ("silent", "allow"), f"GU01 {host} con la voce .esempio-interno.org riceve {d}"
    d = guardia(repo, "web-egress-guard.py", fetch(f"https://esempio-interno.org.cattivo.example/?{LUNGA}"), interni)
    assert d == "ask", f"GU01 esempio-interno.org.cattivo.example passa come interno: {d}"


def test_gu02(repo: Path) -> None:
    d = guardia(repo, "web-egress-guard.py", fetch(f"https://cattivo.org/?{LUNGA}"), ".org\n.esempio-interno.org\n")
    assert d == "ask", f"GU02 la voce .org apre cattivo.org: {d}"
    d = guardia(repo, "web-egress-guard.py", fetch(f"https://api.esempio-interno.org/?{LUNGA}"),
                ".org\n.esempio-interno.org\n")
    assert d in ("silent", "allow"), f"GU02 il banco non discrimina: la voce valida non apre il suo dominio ({d})"


def test_gu03(repo: Path) -> None:
    for host in ("stampante.local", "nas.internal"):
        d = guardia(repo, "web-egress-guard.py", fetch(f"http://{host}/?{LUNGA}"))
        assert d in ("silent", "allow"), f"GU03 {host} non conta come interno: {d}"


def test_gu04(repo: Path) -> None:
    db = guardia(repo, "data-guard.py", bash("sqlite3 x.db .dump > master.db"))
    assert db == "ask", f"GU04 il banco non discrimina: sovrascrivere un .db riceve {db}"
    d = guardia(repo, "data-guard.py", bash("cat > /tmp/query.sql <<'SQL'\nSELECT 1;\nSQL"))
    assert d in ("silent", "allow"), f"GU04 scrivere uno script .sql chiede conferma: {d}"


def ridotto(repo: Path, comando: str) -> str:
    """Il comando come lo vede comms-prefilter dopo aver tolto il testo che nessuno esegue."""
    with tempfile.TemporaryDirectory() as td:
        hooks = Path(os.path.realpath(td)) / "hooks"
        shutil.copytree(repo / "hooks", hooks, ignore=shutil.ignore_patterns("__pycache__", "test_*", "test-*"))
        leggi = ("import importlib.util, sys\n"
                 "spec = importlib.util.spec_from_file_location('cp', sys.argv[1])\n"
                 "m = importlib.util.module_from_spec(spec)\n"
                 "spec.loader.exec_module(m)\n"
                 "sys.stdout.write(m.reduce(sys.stdin.read()))\n")
        env = dict(os.environ, HOME=td, USERPROFILE=td, ARTURO_TELEMETRIA="0")
        p = subprocess.run([sys.executable, "-B", "-c", leggi, str(hooks / "comms-prefilter.py")], input=comando,
                           capture_output=True, text=True, env=env, encoding="utf-8")
    return p.stdout


def test_gu05(repo: Path) -> None:
    testo = ("python3 - <<'EOF'\np = 'segnala.py'; s = open(p).read()\n"
             "open(p, 'w').write(s.replace('apre un mailto: verso X', 'scrive su file'))\nEOF")
    assert "mailto" not in ridotto(repo, testo), "GU05 un mailto: dentro una stringa python resta un invio"
    eseguono = (
        "python3 - <<'EOF'\nfrom os import system as s\ns('sendmail a@esempio.org < x')\nEOF",
        "python3 - <<'EOF'\nimport os\nos.posix_spawn('/usr/sbin/sendmail', ['sendmail', 'a@esempio.org'], {})\nEOF",
        "python3 - <<'EOF'\nimport os\nos.startfile('mailto:a@esempio.org')\nEOF",
    )
    for comando in eseguono:
        r = ridotto(repo, comando)
        assert "sendmail" in r or "mailto" in r, f"GU05 codice che lancia un programma sparisce: {comando.splitlines()[1]}"


TESTS = {"GU01": test_gu01, "GU02": test_gu02, "GU03": test_gu03, "GU04": test_gu04, "GU05": test_gu05}


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
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
