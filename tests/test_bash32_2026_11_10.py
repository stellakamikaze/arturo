#!/usr/bin/env python3
"""BS01-BS02: gli script di Arturo si leggono col bash 3.2 di macOS (segnalazione n. 68, 10/11/2026).

Il bash di sistema del Mac è il 3.2. Dentro una sostituzione, `$(...)` o `<(...)`, conta gli apici anche nel
corpo di un heredoc: un apostrofo in un commento ("l'avvio") apre una citazione che non si chiude, e lo script
intero non parte. `/diagnosi` si fermava così su `skills/system-audit/audit.sh`.

BS01 nessuno script `.sh` apre un heredoc dentro `$(...)` o `<(...)` con un apice o un backtick nel corpo.
     Vale su ogni sistema: è il controllo che regge anche dove il bash 3.2 non c'è.
BS02 ogni script `.sh` che gira con bash passa `/bin/bash -n` dove `/bin/bash` è la versione 3. Fuori dal Mac
     è un salto dichiarato.

Sulla base a7c5162 ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
--avvelena: rimettere il heredoc dentro `<(...)` fa rossi BS01 e, sul Mac, BS02.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Un heredoc aperto sulla stessa riga di una sostituzione ancora aperta: `$(cmd <<'X'` o `< <(cmd <<'X'`.
APERTURA = re.compile(r"""(?:\$\(|<\()[^)]*<<-?\s*(['"]?)([A-Za-z_][A-Za-z0-9_]*)\1""")


def script(repo: Path) -> list:
    """Gli script .sh del repo, senza quelli scritti per zsh o per sh."""
    risultato = []
    for f in sorted(repo.rglob("*.sh")):
        # worktrees: le copie di lavoro in .claude/worktrees sono altri branch, fuori da git (11/11/2026).
        if any(p in (".git", "node_modules", "worktrees") for p in f.parts):
            continue
        prima = f.read_text(encoding="utf-8", errors="replace").split("\n", 1)[0]
        if re.search(r"\bzsh\b|/sh$", prima):
            continue
        risultato.append(f)
    return risultato


def heredoc_fragili(testo: str) -> list:
    """Le righe dove un heredoc dentro una sostituzione ha un apice o un backtick nel corpo."""
    righe, trovati = testo.split("\n"), []
    for i, riga in enumerate(righe):
        m = APERTURA.search(riga)
        if not m:
            continue
        fine = m.group(2)
        for corpo in righe[i + 1:]:
            if corpo.strip() == fine:
                break
            if "'" in corpo or "`" in corpo:
                trovati.append(i + 1)
                break
    return trovati


def bash3() -> str:
    """/bin/bash se è la versione 3, altrimenti stringa vuota."""
    if not Path("/bin/bash").exists():
        return ""
    try:
        r = subprocess.run(["/bin/bash", "--version"], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return ""
    return "/bin/bash" if re.search(r"version 3\.", r.stdout) else ""


def test_bs01(repo: Path) -> None:
    fragili = []
    for f in script(repo):
        for n in heredoc_fragili(f.read_text(encoding="utf-8", errors="replace")):
            fragili.append(f"{f.relative_to(repo)}:{n}")
    assert not fragili, f"BS01 heredoc dentro una sostituzione con un apice nel corpo: {', '.join(fragili)}"


def test_bs02(repo: Path) -> None:
    rossi = []
    for f in script(repo):
        r = subprocess.run(["/bin/bash", "-n", str(f)], capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            rossi.append(f"{f.relative_to(repo)}: {r.stderr.strip().splitlines()[-1][:120] if r.stderr.strip() else r.returncode}")
    assert not rossi, "BS02 script che il bash 3.2 non legge: " + "; ".join(rossi)


def casi() -> dict:
    tutti = {"BS01": test_bs01}
    if bash3():
        tutti["BS02"] = test_bs02
    else:
        print("SALTO BS02: qui /bin/bash non è la versione 3 (si prova sul Mac)")
    return tutti


VELENI = [
    ("BS01", "skills/system-audit/audit.sh",
     '  python3 - "$command" "$CLAUDE_DIR" "$CODICE" > "$script_file" <<\'PY\' || true',
     '  cat < <(python3 - "$command" "$CLAUDE_DIR" "$CODICE" <<\'PY\'\n# l\'avvio'),
]


def avvelena(repo: Path) -> int:
    esiti = []
    for caso, rel, giusto, rotto in VELENI:
        with tempfile.TemporaryDirectory() as tmp:
            copia = Path(tmp) / "repo"
            shutil.copytree(repo, copia, ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules"))
            testo = (copia / rel).read_text(encoding="utf-8")
            assert testo.count(giusto) == 1, f"veleno {caso}: il testo da rompere non c'è più in {rel}"
            (copia / rel).write_text(testo.replace(giusto, rotto), encoding="utf-8")
            for nome, test in casi().items():
                try:
                    test(copia)
                except AssertionError as e:
                    if str(e).startswith(nome):
                        print(f"VELENO {nome} ROSSO: {str(e)[:120]}")
                        esiti.append(nome)
                        continue
                    print(f"VELENO {nome} NON ATTACCA ({rel}): {e}")
                    return 1
                print(f"VELENO {nome} NON ATTACCA ({rel}): il caso resta verde")
                return 1
    print(f"VELENI_ROSSI={','.join(esiti)} veleni={len(VELENI)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--baseline-ref")
    parser.add_argument("--avvelena", action="store_true")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.avvelena:
        return avvelena(repo)
    tests = casi()
    if args.baseline_ref:
        rossi, altro = [], []
        for nome, test in tests.items():
            try:
                test(repo)
            except AssertionError as e:
                (rossi if str(e).startswith(nome) else altro).append(f"{nome}: {e}")
            except Exception as e:  # noqa: BLE001
                altro.append(f"{nome}: {type(e).__name__} {e}")
        assert not altro and len(rossi) == len(tests), \
            "baseline non discriminante: ogni controllo deve fallire col suo codice.\n" + "\n".join(altro + rossi)
        print(f"BASELINE_DISCRIMINANTE={','.join(r.split(':')[0] for r in rossi)}")
        return 0
    for test in tests.values():
        test(repo)
    print(f"PASS {','.join(tests)} controlli={len(tests)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
