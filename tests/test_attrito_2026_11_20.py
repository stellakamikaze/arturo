#!/usr/bin/env python3
"""AT01-AT05: le conferme che non proteggono niente, misurate sui transcript dei 7 giorni al 20/11/2026.

Federico, 20/11/2026: "Fai analisi completa dei transcript degli ultimi 7 giorni per verificare permessi
allargabili", poi "si a tutto" sull'elenco. Su 355 conferme delle guardie su un computer:

AT01 rm ricorsivo dentro la cartella temporanea di un job (~/.claude/jobs/<id>/tmp/<x>): 50 conferme. Tace; la
     cartella tmp, il job, jobs, `..` e un link che esce dallo scratchpad chiedono ancora.
AT02 git push --delete di un ramo il cui ultimo commit sul remoto sta già in main o dev: 23 conferme. Tace; un ramo
     con commit che mancano, un flag che forza, un `+` o il ramo principale chiedono ancora.
AT03 letture prese per scritture sulla config: `sed -n`, `wc`, `grep` sulla cache dei plugin, e un `git clone` in
     una cartella temporanea. Le scritture vere (sed -i, >, cp) sulla cache e su settings.json chiedono ancora.
AT04 testo preso per comando: "CLAUDE.md" dentro il testo di un sed su un handoff, `shutil.rmtree` e `gh workflow`
     dentro il codice che si modifica, `trash` contato come cancellazione. I comandi veri chiedono ancora.

Sulla base BASE ogni gruppo fallisce con un AssertionError che comincia col suo codice (--avvelena).
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BASE = "0c1daea"
_QUI = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("banco_ms_at", _QUI / "test_guardie_memoria_sblocco_2026_11_11.py")
ms = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ms)
Banco, verifica, gruppo = ms.Banco, ms.verifica, ms.gruppo

BD = "block-dangerous.py"


def _git(*args, cwd: Path, home: Path) -> str:
    env = dict(ms._env(home), GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t",
               GIT_COMMITTER_EMAIL="t@t", GIT_CONFIG_NOSYSTEM="1")
    return subprocess.run(["git", *args], cwd=cwd, env=env, capture_output=True, text=True, check=True).stdout


@gruppo
def at01(b: Banco) -> int:
    j = b.claude / "jobs" / "abcd1234" / "tmp"
    (j / "lavoro" / "sotto").mkdir(parents=True)
    (j / "lavoro" / "sotto" / "f.txt").write_text("x\n", encoding="utf-8")
    (b.claude / "jobs" / "abcd1234" / "altro").mkdir()
    os.symlink(b.claude / "hooks", j / "link-fuori")
    casi = [
        ("scratchpad", b.guardia(BD, f"rm -rf {j}/lavoro"), "silent"),
        ("scratchpad-tilde", b.guardia(BD, "rm -rf ~/.claude/jobs/abcd1234/tmp/lavoro/sotto"), "silent"),
        ("scratchpad-cd", b.guardia(BD, f"cd {j} && rm -rf lavoro"), "silent"),
        ("tmp-intera", b.guardia(BD, "rm -rf ~/.claude/jobs/abcd1234/tmp"), "ask"),
        ("job-intero", b.guardia(BD, "rm -rf ~/.claude/jobs/abcd1234"), "ask"),
        ("jobs", b.guardia(BD, "rm -rf ~/.claude/jobs"), "ask"),
        ("fuori-tmp", b.guardia(BD, "rm -rf ~/.claude/jobs/abcd1234/altro"), "ask"),
        ("punti", b.guardia(BD, "rm -rf ~/.claude/jobs/abcd1234/tmp/../../../hooks"), "ask"),
        ("link-fuori", b.guardia(BD, f"rm -rf {j}/link-fuori/"), "ask"),
        ("dispatcher-scratchpad", b.dispatcher(f"rm -rf {j}/lavoro"), "silent"),
        ("dispatcher-job", b.dispatcher("rm -rf ~/.claude/jobs/abcd1234"), "ask"),
    ]
    return verifica("AT01", casi)


@gruppo
def at02(b: Banco) -> int:
    remoto = b.home / "remoto.git"
    _git("init", "-q", "--bare", "-b", "main", str(remoto), cwd=b.home, home=b.home)
    repo = b.home / "progetto" / "r"
    _git("clone", "-q", str(remoto), str(repo), cwd=b.home, home=b.home)
    (repo / "a.txt").write_text("a\n", encoding="utf-8")
    _git("add", "a.txt", cwd=repo, home=b.home)
    _git("commit", "-qm", "a", cwd=repo, home=b.home)
    _git("push", "-q", "origin", "main", cwd=repo, home=b.home)
    _git("switch", "-qc", "unito", cwd=repo, home=b.home)
    (repo / "b.txt").write_text("b\n", encoding="utf-8")
    _git("add", "b.txt", cwd=repo, home=b.home)
    _git("commit", "-qm", "b", cwd=repo, home=b.home)
    _git("push", "-q", "origin", "unito", cwd=repo, home=b.home)
    _git("switch", "-q", "main", cwd=repo, home=b.home)
    _git("merge", "-q", "--ff-only", "unito", cwd=repo, home=b.home)
    _git("push", "-q", "origin", "main", cwd=repo, home=b.home)
    _git("switch", "-qc", "solo", cwd=repo, home=b.home)
    (repo / "c.txt").write_text("c\n", encoding="utf-8")
    _git("add", "c.txt", cwd=repo, home=b.home)
    _git("commit", "-qm", "c", cwd=repo, home=b.home)
    _git("push", "-q", "origin", "solo", cwd=repo, home=b.home)
    _git("switch", "-q", "main", cwd=repo, home=b.home)
    casi = [
        ("unito", b.guardia(BD, "git push -q origin --delete unito 2>&1 | tail -1", repo), "silent"),
        ("unito-cd", b.guardia(BD, f"cd {repo} && git push origin --delete unito"), "silent"),
        ("unito-due-punti", b.guardia(BD, "git push origin :unito", repo), "silent"),
        ("non-unito", b.guardia(BD, "git push origin --delete solo", repo), "ask"),
        ("uno-dei-due", b.guardia(BD, "git push origin --delete unito solo", repo), "ask"),
        ("principale", b.guardia(BD, "git push origin --delete main", repo), "ask"),
        ("forza", b.guardia(BD, "git push --force origin --delete unito", repo), "ask"),
        ("piu", b.guardia(BD, "git push origin +unito:solo", repo), "ask"),
        ("inesistente", b.guardia(BD, "git push origin --delete fantasma", repo), "ask"),
        ("repo-ignoto", b.guardia(BD, "cd \"$X\" && git push origin --delete unito", repo), "ask"),
        ("dispatcher-unito", b.dispatcher("git push -q origin --delete unito", repo), "silent"),
        ("dispatcher-non-unito", b.dispatcher("git push origin --delete solo", repo), "ask"),
    ]
    return verifica("AT02", casi)


@gruppo
def at03(b: Banco) -> int:
    f = b.claude / "plugins" / "cache" / "arturo" / "arturo" / "0.2.19" / "shared" / "regole-interfaccia.md"
    f.parent.mkdir(parents=True)
    f.write_text("x\n", encoding="utf-8")
    j = "~/.claude/jobs/abcd1234/tmp/rilascio"
    casi = [
        ("sed-n", b.guardia(BD, f"wc -l {f}; sed -n 1,80p {f}"), "silent"),
        ("sed-n-virgolette", b.guardia(BD, f"sed -n '1,80p' {f}"), "silent"),
        ("clone-scratchpad", b.guardia(BD, f"R={j}; rm -rf $R; git clone -q https://github.com/x/y.git $R/y"), "silent"),
        ("sed-i", b.guardia(BD, f"sed -i '' 's/a/b/' {f}"), "ask"),
        ("sed-ni", b.guardia(BD, f"sed -ni 's/a/b/p' {f}"), "ask"),
        ("sed-in-place", b.guardia(BD, f"sed --in-place=.bak 's/a/b/' {f}"), "ask"),
        ("sed-I-bsd", b.guardia(BD, f"sed -I .bak 's/a/b/' {f}"), "ask"),
        ("redirezione", b.guardia(BD, f"echo x > {f}"), "ask"),
        ("settings", b.guardia(BD, "echo x > ~/.claude/settings.json"), "ask"),
    ]
    return verifica("AT03", casi)


GH = "gh-destructive-guard.py"
PY_CON_TESTO = ("python3 - <<'EOF'\nfrom pathlib import Path\np = Path('bin/x.py'); t = p.read_text()\n"
                "o = '''        shutil.rmtree(cartella)\n        return'''\nt = t.replace(o, '''        pass'''); "
                "p.write_text(t)\nEOF")
PY_RMTREE_VERO = "python3 - <<'EOF'\nimport shutil, sys\nshutil.rmtree(sys.argv[1])\nEOF"
NOTA_GH = ("python3 - <<'EOF'\np = 'nota.md'\nr = '- **CI manuale**: si lancia con `gh workflow run volta.yml`.'\n"
           "open(p, 'a').write(r)\nEOF")


@gruppo
def at04(b: Banco) -> int:
    h = b.claude / "data" / "handoffs" / "r" / "H.md"
    casi = [
        ("sed-testo-claude-md", b.guardia(BD, f"sed -i '' 's/^- Ultimo .*/- Ultimo: 2a8289d - CLAUDE.md di X/' {h}"),
         "silent"),
        ("redirezione-claude-md", b.guardia(BD, "echo x > ~/.claude/CLAUDE.md"), "ask"),
        ("sed-claude-md-globale", b.guardia(BD, "sed -i '' 's/a/b/' ~/.claude/CLAUDE.md"), "ask"),
        ("rmtree-nel-testo", b.guardia(BD, PY_CON_TESTO), "silent"),
        ("rmtree-vero", b.guardia(BD, PY_RMTREE_VERO), "ask"),
        ("gh-nel-testo", b.guardia(GH, NOTA_GH), "silent"),
        ("gh-vero", b.guardia(GH, "gh workflow run volta.yml"), "ask"),
        ("gh-in-sostituzione", b.guardia(GH, "echo \"$(gh workflow run volta.yml)\""), "ask"),
        ("find-vuote", b.guardia(BD, "find ~/.claude/projects -mindepth 2 -type d -empty -delete"), "silent"),
        ("find-delete", b.guardia(BD, "find ~/.claude/projects -name '*.jsonl' -delete"), "ask"),
        ("find-vuote-o", b.guardia(BD, "find ~/x -type d -empty -o -name a -delete"), "ask"),
        ("variabile-claude", b.guardia(BD, "C=~/.local/bin/claude; $C stop a21b487e; $C rm a21b487e"), "silent"),
        ("variabile-rm", b.guardia(BD, "R=/bin/rm; $R -rf ~/Documents"), "ask"),
        ("variabile-calcolata", b.guardia(BD, "C=$(command -v claude); $C rm x"), "ask"),
        ("variabile-due-volte", b.guardia(BD, "C=claude; C=rm; $C -rf ~/Documents"), "ask"),
    ]
    return verifica("AT04", casi)


TESTS = {"AT01": at01, "AT02": at02, "AT03": at03, "AT04": at04}
GUARDIE = ("block-dangerous.py", "bash-dispatcher.sh", "forma_comando.py", "protect_claude_md.py", "heredoc.py",
           "gh-destructive-guard.py")


def avvelena(repo: Path, ref: str) -> int:
    """Ogni gruppo, con le guardie com'erano su `ref`, deve fallire col suo codice."""
    inerti, rossi = [], []
    for codice, test in TESTS.items():
        copia = Path(tempfile.mkdtemp(prefix="arturo-veleno."))
        try:
            shutil.copytree(repo / "hooks", copia / "hooks", ignore=shutil.ignore_patterns("__pycache__", "*.local"))
            for nome in GUARDIE:
                vecchio = subprocess.run(["git", "-C", str(repo), "show", f"{ref}:hooks/{nome}"], capture_output=True,
                                         check=False)
                if vecchio.returncode == 0:
                    (copia / "hooks" / nome).write_bytes(vecchio.stdout)
            try:
                test(copia / "hooks")
                inerti.append(f"{codice}: verde con le guardie di {ref}")
            except AssertionError as e:
                if not str(e).startswith(codice):
                    inerti.append(f"{codice}: rosso col motivo sbagliato: {e}")
                else:
                    rossi.append(codice)
                    print(f"VELENO {codice} ROSSO: {str(e)[:200]}")
        finally:
            shutil.rmtree(copia, ignore_errors=True)
    assert not inerti, "veleni che non attaccano:\n" + "\n".join(inerti)
    print(f"VELENI_ROSSI={','.join(rossi)} veleni={len(rossi)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--baseline-ref")
    parser.add_argument("--avvelena", action="store_true")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.avvelena or args.baseline_ref:
        return avvelena(repo, args.baseline_ref or BASE)
    totale, errori = 0, []
    for prova in TESTS.values():
        try:
            totale += prova(repo / "hooks")
        except AssertionError as e:
            errori.append(str(e))
    for e in errori:
        print("KO", e)
    if errori:
        return 1
    print(f"PASS attrito gruppi={len(TESTS)} casi={totale}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
