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
        ("clone-checkout", b.guardia(BD, f"R={j}; git clone -q https://github.com/x/y.git $R/y && "
                                         "git -C $R/y checkout -q 11543bf && git -C $R/y log --oneline -1"), "silent"),
        ("checkout-config", b.guardia(BD, "git -C ~/.claude checkout -- settings.json"), "ask"),
        ("checkout-config-ramo", b.guardia(BD, "git -C ~/.claude checkout -q dev"), "ask"),
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


def _dispatcher_nudo(b: Banco, comando: str, cartelle: str) -> str:
    """Il dispatcher con un PATH senza timeout, e le cartelle extra dove cercarlo."""
    import json as _json
    nudo = b.home.parent / "bin-nudo"
    if not nudo.exists():
        nudo.mkdir()
        for programma in ("bash", "python3", "git", "jq", "sh", "cat", "printf", "date", "mkdir", "basename", "sed",
                          "grep", "tr", "wc", "dirname", "env"):
            percorso = shutil.which(programma)
            if percorso:
                (nudo / programma).symlink_to(percorso)
    copia = b.claude / "hooks"
    if not (copia / "bash-dispatcher.sh").exists():
        shutil.rmtree(copia, ignore_errors=True)
        shutil.copytree(b.hooks, copia, ignore=shutil.ignore_patterns("__pycache__", "*.local"))
    env = dict(ms._env(b.home), PATH=str(nudo), ARTURO_TIMEOUT_CARTELLE=cartelle)
    dati = _json.dumps({"tool_name": "Bash", "tool_input": {"command": comando}, "cwd": str(b.home),
                        "hook_event_name": "PreToolUse", "session_id": "at"})
    p = subprocess.run([str(nudo / "bash"), str(copia / "bash-dispatcher.sh")], input=dati, text=True,
                       encoding="utf-8", capture_output=True, timeout=120, check=False, env=env)
    return ms.decisione(p)


@gruppo
def at05(b: Banco) -> int:
    if os.name == "nt":
        return 0  # su Windows timeout c'è in Git Bash
    brew = b.home.parent / "brew-finto"
    brew.mkdir()
    (brew / "timeout").write_text("#!/bin/sh\nshift; exec \"$@\"\n", encoding="utf-8")
    (brew / "timeout").chmod(0o755)
    casi = [
        ("timeout-in-homebrew", _dispatcher_nudo(b, "timeout 5 ls", str(brew)), "silent"),
        ("timeout-assente", _dispatcher_nudo(b, "timeout 5 ls", ""), "block"),
        ("timeout-cartella-vuota", _dispatcher_nudo(b, "timeout 5 ls", str(b.home / "tmp")), "block"),
    ]
    return verifica("AT05", casi)


def _bd_job(b: Banco, comando: str, cwd: Path, sessione: str, job: str | None, dopo: bool = False) -> str:
    import json as _json
    env = dict(ms._env(b.home))
    if job:
        env["CLAUDE_JOB_DIR"] = str(b.claude / "jobs" / job)
    dati = _json.dumps({"tool_name": "Bash", "tool_input": {"command": comando}, "cwd": str(cwd),
                        "hook_event_name": "PostToolUse" if dopo else "PreToolUse", "session_id": sessione})
    p = subprocess.run([sys.executable, "-B", str(b.hooks / BD)] + (["dopo"] if dopo else []), input=dati,
                       text=True, encoding="utf-8", capture_output=True, timeout=30, check=False, env=env)
    return ms.decisione(p)


@gruppo
def at06(b: Banco) -> int:
    repo = b.home / "progetto" / "amend"
    repo.mkdir(parents=True)
    _git("init", "-q", "-b", "main", cwd=repo, home=b.home)
    (repo / "a.txt").write_text("a\n", encoding="utf-8")
    _git("add", "a.txt", cwd=repo, home=b.home)
    _git("commit", "-qm", "a", cwd=repo, home=b.home)
    # La sessione A del job j1 registra il suo commit; dopo /clear la sessione B dello stesso job fa l'amend.
    _bd_job(b, "git commit -qm a", repo, "sessione-a", "j1", dopo=True)
    amend = "git commit -q --amend --no-edit"
    casi = [
        ("stesso-job", _bd_job(b, amend, repo, "sessione-b", "j1"), "silent"),
        ("altro-job", _bd_job(b, amend, repo, "sessione-c", "j2"), "ask"),
        ("senza-job", _bd_job(b, amend, repo, "sessione-d", None), "ask"),
        ("stessa-sessione", _bd_job(b, amend, repo, "sessione-a", None), "silent"),
    ]
    return verifica("AT06", casi)


CG = "commit-secret-gate.py"


@gruppo
def at07(b: Banco) -> int:
    repo = b.home / "progetto" / "gate"
    repo.mkdir(parents=True)
    _git("init", "-q", "-b", "main", cwd=repo, home=b.home)
    (repo / "a.txt").write_text("a\n", encoding="utf-8")
    nota = (f"F={repo}/a.txt; cat >> $F <<'EOF'\n- la richiesta d'importo al partner\nEOF\n"
            f"cd {repo} && git add a.txt && git commit -qm nota")
    pr = f"cd {repo} && gh pr create --title t --body-file - <<'EOF'\nL'ultima revisione\nEOF"
    veleno = (f"cd {repo} && bash <<'EOF'\necho l'apostrofo\ngit commit -am segreto\nEOF")
    casi = [
        ("apostrofo-nel-corpo", b.guardia(CG, nota), "silent"),
        ("pr-con-apostrofo", b.guardia(CG, pr), "silent"),
        ("commit-nel-corpo", b.guardia(CG, veleno), "ask"),
    ]
    return verifica("AT07", casi)


@gruppo
def at08(b: Banco) -> int:
    import re as _re
    sorgente = b.hooks.parent / "tests" / "banchi-avvio.sh"
    banchi = _re.search(r'^BANCHI="([^"]+)"', sorgente.read_text(encoding="utf-8"), _re.M).group(1).split()

    def corsa(con_banchi: list) -> tuple:
        config = b.home.parent / f"config-{len(con_banchi)}"
        (config / "tests").mkdir(parents=True)
        shutil.copy2(sorgente, config / "tests" / "banchi-avvio.sh")
        for nome in con_banchi:
            (config / "tests" / nome).write_text("pass\n", encoding="utf-8")
        env = dict(ms._env(b.home), ARTURO_DIR=str(config), ARTURO_TELEMETRIA="0")
        p = subprocess.run(["bash", str(config / "tests" / "banchi-avvio.sh")], env=env, capture_output=True,
                           text=True, encoding="utf-8", timeout=300, check=False)
        esito = (config / "cache" / "banchi-ultimo-esito.txt").read_text(encoding="utf-8").splitlines()[:1]
        return p.returncode, (esito or [""])[0]
    casi = [
        ("nessun-banco", corsa([]), (0, "SALTATO")),
        ("ne-manca-uno", corsa(banchi[1:]), (1, "ROSSO")),
        ("tutti", corsa(banchi), (0, "VERDE")),
    ]
    return verifica("AT08", casi)


TESTS = {"AT01": at01, "AT02": at02, "AT03": at03, "AT04": at04, "AT05": at05, "AT06": at06, "AT07": at07,
         "AT08": at08}
GUARDIE = ("block-dangerous.py", "bash-dispatcher.sh", "forma_comando.py", "protect_claude_md.py", "heredoc.py",
           "gh-destructive-guard.py", "commit-secret-gate.py")


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
            (copia / "tests").mkdir()
            vecchio = subprocess.run(["git", "-C", str(repo), "show", f"{ref}:tests/banchi-avvio.sh"],
                                     capture_output=True, check=False)
            (copia / "tests" / "banchi-avvio.sh").write_bytes(vecchio.stdout)
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
