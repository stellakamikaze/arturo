#!/usr/bin/env python3
"""MS01-MS05: il ramo memoria non approva scritture fuori zona, e lo sblocco della config chiede (#5261).

La review del 10/11/2026 ha trovato tre buchi critici nelle guardie della 0.2.10. Un comando che nominava la
cartella degli handoff riceveva "allow" dal ramo memoria del dispatcher anche se scriveva altrove
(`echo x>>~/.ssh/authorized_keys; ls ~/.claude/data/handoffs/`) o se portava dentro la zona una cartella di
chiavi (`mv ~/.ssh ~/.claude/data/handoffs/s`). Il file che sblocca la config si creava senza conferma con
`mkdir` o con `cp` verso la cartella, e una cartella o un link valevano come sblocco.

"silent" qui vuol dire: nessun allow, il comando torna al flusso normale dei permessi.

MS01 redirezioni attaccate alla parola, `<>`, `>&file`: niente allow fuori zona; `redirezioni` le legge.
MS02 un `cd` che la shell non applica (subshell, fallito, in background) non sposta la cartella del ramo.
MS03 sorgenti: `mv`, `cp`, `cat`, `tee <` e `grep` con una sorgente fuori zona non ricevono allow.
MS04 lo sblocco via `mkdir`, e via `cp`, `mv`, `ln` verso la cartella, chiede; così `settings.json` copiato lì.
MS05 `protect_claude_md.py` accetta come sblocco solo un file vero: una cartella o un link no.

Sulla base 7a8bb69 ogni gruppo fallisce con un AssertionError che comincia col suo codice. Con --avvelena il
banco lo prova da solo: rimette nella copia le guardie di 7a8bb69 (git show) e vuole ogni gruppo rosso col suo
codice. I controlli che restano allow stanno dentro i gruppi: un gruppo di soli casi legittimi sarebbe verde
anche sulla base.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BASE = "7a8bb69"


def _env(home: Path) -> dict:
    temp = home / "tmp"
    temp.mkdir(parents=True, exist_ok=True)
    env = {"HOME": str(home), "USERPROFILE": str(home), "PATH": os.environ.get("PATH", ""),
           "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8", "ARTURO_TELEMETRIA": "0",
           "TEMP": str(temp), "TMP": str(temp), "TMPDIR": str(temp), "ARTURO_REGOLA": "1"}
    for k in ("SYSTEMROOT", "SystemRoot", "WINDIR"):
        if k in os.environ:
            env[k] = os.environ[k]
    return env


def decisione(proc: subprocess.CompletedProcess) -> str:
    if proc.returncode == 2:
        return "block"
    righe = proc.stdout.strip().splitlines()
    if not righe:
        return "silent" if proc.returncode == 0 else f"rc{proc.returncode}"
    try:
        return json.loads(righe[0])["hookSpecificOutput"]["permissionDecision"]
    except (json.JSONDecodeError, KeyError, TypeError, IndexError):
        return "silent"


def bash_vero() -> str:
    # Su Windows "bash" per nome è quello di WSL: si prende il bash del PATH (Git Bash).
    return shutil.which("bash") or "bash"


class Banco:
    def __init__(self, hooks: Path, radice: Path):
        self.hooks = hooks
        self.home = radice / "home"
        self.claude = self.home / ".claude"
        self.zona = self.claude / "data" / "handoffs"
        for d in (self.zona / "r" / "archivio", self.claude / "projects" / "-casa-r" / "memory",
                  self.claude / "plugins", self.claude / "bin", self.home / ".ssh", self.home / "Documents",
                  self.home / "tmp" / "x", self.home / "progetto"):
            d.mkdir(parents=True, exist_ok=True)
        for f in (self.zona / "r" / "a.md", self.zona / "r" / "H.md", self.zona / "r" / "nota.md",
                  self.zona / "INDEX.md", self.home / ".ssh" / "id_ed25519", self.home / ".netrc",
                  self.home / ".zshrc", self.home / "tmp" / "config-unlock-prova", self.home / "tmp" / "a.txt",
                  self.home / "tmp" / "x" / "settings.json", self.home / "progetto" / "CLAUDE.md"):
            f.write_text("x\n", encoding="utf-8")

    def _dati(self, comando: str, cwd: Path | None = None, strumento: str = "Bash", dati: dict | None = None) -> str:
        return json.dumps({"tool_name": strumento, "tool_input": dati or {"command": comando},
                           "cwd": str(cwd or self.home), "hook_event_name": "PreToolUse", "session_id": "ms"})

    def guardia(self, nome: str, comando: str, cwd: Path | None = None) -> str:
        p = subprocess.run([sys.executable, "-B", str(self.hooks / nome)], input=self._dati(comando, cwd), text=True,
                           encoding="utf-8", capture_output=True, timeout=30, check=False, env=_env(self.home))
        return decisione(p)

    def write(self, percorso: Path) -> str:
        dati = self._dati("", strumento="Write", dati={"file_path": str(percorso), "content": "x\n"})
        p = subprocess.run([sys.executable, "-B", str(self.hooks / "protect_claude_md.py")], input=dati, text=True,
                           encoding="utf-8", capture_output=True, timeout=30, check=False, env=_env(self.home))
        return decisione(p)

    def dispatcher(self, comando: str, cwd: Path | None = None) -> str:
        copia = self.claude / "hooks"
        if not (copia / "bash-dispatcher.sh").exists():
            shutil.rmtree(copia, ignore_errors=True)
            shutil.copytree(self.hooks, copia, ignore=shutil.ignore_patterns("__pycache__", "*.local"))
        p = subprocess.run([bash_vero(), str(copia / "bash-dispatcher.sh")], input=self._dati(comando, cwd),
                           text=True, encoding="utf-8", capture_output=True, timeout=120, check=False,
                           env=_env(self.home))
        return decisione(p)

    def modulo(self, nome: str):
        # Su Windows la home di Python viene da USERPROFILE: si spostano tutte e due.
        vecchie = {k: os.environ.get(k) for k in ("HOME", "USERPROFILE")}
        os.environ.update({k: str(self.home) for k in vecchie})
        try:
            spec = importlib.util.spec_from_file_location(nome.replace("-", "_")[:-3] + "_ms", self.hooks / nome)
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
            return m
        finally:
            for k, v in vecchie.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v


def verifica(codice: str, casi) -> int:
    sbagliati = [f"{nome}: atteso {atteso!r}, ottenuto {got!r}" for nome, got, atteso in casi if got != atteso]
    assert not sbagliati, f"{codice} " + " | ".join(sbagliati)
    return len(casi)


def gruppo(funzione):
    def corsa(hooks: Path):
        with tempfile.TemporaryDirectory() as d:
            return funzione(Banco(hooks, Path(d)))
    corsa.__name__ = funzione.__name__
    return corsa


BD = "block-dangerous.py"
Z = "~/.claude/data/handoffs"
HEREDOC = "<<'EOF'\n# Handoff\n- nota: a > b\nEOF"


@gruppo
def test_ms01(b: Banco):
    fuori = [
        ("x>>file attaccato", f'echo "chiave x">>~/.ssh/authorized_keys; ls {Z}/'),
        ("cartella/>file", f"ls {Z}/>~/.zshrc"),
        ("1<>file", f"echo x 1<>~/.zshrc; ls {Z}/"),
        ("cp in zona e poi x>file", f"cp {Z}/r/a.md {Z}/r/b.md&&echo x>~/.bash_profile"),
        ("cp da tmp e poi x>file", f"cp ~/tmp/a.txt {Z}/a.md&&echo x>~/.bash_profile"),
        ("a->file", f"echo a->~/.zshrc; ls {Z}/"),
        (">&file", f"ls {Z}/ >&~/.zshrc"),
        ("&>file attaccato", f"ls {Z}/&>~/.zshrc"),
        (">(processo)", f"ls {Z}/ > >(tee ~/.zshrc)"),
    ]
    casi = [(n, b.dispatcher(c), "silent") for n, c in fuori]
    dentro = [
        ("printf >> zona", f"printf '%s\\n' \"- a > b\" >> {Z}/r/H.md"),
        ("grep, sort e head", f'grep -l "Sessione: x" {Z}/r/HANDOFF_*.md 2>/dev/null | sort -r | head -1'),
        ("heredoc verso la zona", f"cat > {Z}/r/H.md {HEREDOC}"),
        ("redirezione attaccata dentro la zona", f"echo nota>>{Z}/r/H.md"),
        ("2>&1 e /dev/null", f"ls {Z}/r >/dev/null 2>&1"),
    ]
    casi += [(f"resta allow: {n}", b.dispatcher(c), "allow") for n, c in dentro]
    fc = b.modulo("forma_comando.py")
    leggi = getattr(fc, "redirezioni", None)
    assert leggi is not None, "MS01 forma_comando.redirezioni non esiste"
    casi += [
        ("unità x>>f", leggi("echo x>>f"), [("scrive", "f")]),
        ("unità 1<>f", leggi("echo x 1<>f"), [("scrive", "f")]),
        ("unità >&f", leggi("ls >&f"), [("scrive", "f")]),
        ("unità &>f", leggi("ls &>f"), [("scrive", "f")]),
        ("unità >|f", leggi("ls >| f"), [("scrive", "f")]),
        ("unità descrittori", leggi("ls 2>&1 >&- <&3"), []),
        ("unità fra virgolette", leggi('echo "a > b" \'c < d\''), []),
        ("unità heredoc", leggi("cat <<'EOF'"), []),
        ("unità here-string", leggi("cat <<< parola"), []),
        ("unità lettura", leggi("tee a < b"), [("legge", "b")]),
        ("unità processo", leggi("diff <(ls) x"), [("processo", "")]),
        ("unità bersaglio fra virgolette", leggi('echo x > "a b"/c'), [("scrive", "a b/c")]),
        ("unità bersaglio vuoto", leggi("echo x >"), [("scrive", "")]),
    ]
    return verifica("MS01", casi)


@gruppo
def test_ms02(b: Banco):
    fuori = [
        ("cd in subshell", f"(cd {Z}); echo x > .zshrc"),
        ("cd in una cartella che manca", f"cd {Z}/manca; echo x > .zshrc"),
        ("cd in background", f"cd {Z} & echo x > .zshrc"),
        ("cd e ||", f"cd {Z} || echo x > .zshrc"),
        ("cd fallito, && true e poi ;", f"cd {Z}/manca && true; echo x > .zshrc"),
        ("cd in una pipe", f"cd {Z} | echo x > .zshrc"),
        ("cd in un gruppo", f"{{ cd {Z}; }}; echo x > .zshrc"),
        ("cd negato", f"! cd {Z}/manca && echo x > .zshrc"),
        ("cd con CDPATH davanti", f"cd {Z} && CDPATH=~ cd Documents && echo k >> x.md"),
        ("tilde e trattino dopo il cd", f"cd {Z} && echo x > ~-/.zshrc"),
        ("env -C dopo il cd", f"cd {Z}/r && env -C ~ tee .zshrc < a.md"),
    ]
    casi = [(n, b.dispatcher(c), "silent") for n, c in fuori]
    dentro = [
        ("cd && heredoc", f"cd {Z}/r && cat > H.md {HEREDOC}"),
        ("mkdir && cd && ls", f"mkdir -p {Z}/r && cd {Z}/r && ls"),
    ]
    casi += [(f"resta allow: {n}", b.dispatcher(c), "allow") for n, c in dentro]
    return verifica("MS02", casi)


@gruppo
def test_ms03(b: Banco):
    fuori = [
        ("mv della cartella delle chiavi", f"mv ~/.ssh {Z}/s"),
        ("mv di una chiave", f"mv ~/.ssh/id_ed25519 {Z}/k"),
        ("mv dei Documenti", f"mv ~/Documents {Z}/d"),
        ("cat di .netrc", f"cat ~/.netrc > {Z}/n.md"),
        ("tee con ingresso da .netrc", f"tee {Z}/n.md < ~/.netrc"),
        ("cat | tee", f"cat ~/.netrc | tee {Z}/n.md"),
        ("cp da fuori zona", f"cp ~/.zshrc {Z}/"),
        ("grep -r sui Documenti", f"grep -r . ~/Documents > {Z}/x"),
        ("mv della zona intera", f"mv {Z} ~/.claude/projects/p/memory/h"),
        ("head con -n staccato", f"head -n 5 ~/.netrc > {Z}/n.md"),
        ("maggiore fra apici come argomento", f"tee '>' ~/.zshrc < {Z}/r/a.md"),
        ("cat con maggiore fra apici", f"cat '>' ~/.netrc > {Z}/n.md"),
        ("sudo davanti", f"sudo tee {Z}/r/a.md"),
        ("sort -o in un gruppo corto", f"sort -uo.zshrc {Z}/r/a.md"),
        ("sort --o abbreviato", f"sort --o=.zshrc {Z}/r/a.md"),
        ("cp -t attaccato", f"cp -t/tmp {Z}/r/a.md"),
        ("mv -vt attaccato", f"mv -vt/tmp {Z}/r/a.md"),
        ("diff --from-file", f"diff --from-file=~/.netrc {Z}/r/a.md > {Z}/x.md"),
        ("find -H fuori zona", f"find -H ~/Documents -type f > {Z}/x"),
        ("graffe che si espandono", f"tee {{{Z}/r/b.md,~/.zshrc}} < {Z}/r/a.md"),
    ]
    casi = [(n, b.dispatcher(c), "silent") for n, c in fuori]
    casi += [
        ("mv di plugins da ~/.claude", b.dispatcher(f"mv plugins {Z}/p", b.claude), "silent"),
        ("mv di bin e arturo da ~/.claude", b.dispatcher(f"mv bin arturo {Z}/", b.claude), "silent"),
        ("cp di una chiave chiede", b.dispatcher(f"cp ~/.ssh/id_ed25519 {Z}/k"), "ask"),
    ]
    dentro = [
        ("cp dentro la zona", f"cp {Z}/r/a.md {Z}/r/b.md"),
        ("mv dentro la zona", f"mv {Z}/r/a.md {Z}/r/archivio/"),
        ("tail -n", f"tail -n 20 {Z}/r/H.md"),
        ("cat dell'indice", f"cat {Z}/INDEX.md 2>/dev/null"),
        ("tee -a con ingresso dalla zona", f"tee -a ~/.claude/projects/-casa-r/memory/MEMORY.md < {Z}/r/nota.md"),
        ("grep col pattern e il file", f"grep -n -e Sessione {Z}/r/H.md"),
        ("find nella zona", f"find {Z} -name 'HANDOFF_*' -newer {Z}/INDEX.md"),
        ("ls -la e wc -l", f"ls -la {Z}/r && wc -l {Z}/r/H.md"),
        ("head -5", f"head -5 {Z}/r/H.md"),
        ("mkdir -p e touch", f"mkdir -p {Z}/nuovo && touch {Z}/nuovo/H.md"),
    ]
    casi += [(f"resta allow: {n}", b.dispatcher(c), "allow") for n, c in dentro]
    return verifica("MS03", casi)


@gruppo
def test_ms04(b: Banco):
    chiedono = [
        ("mkdir -p dello sblocco", "mkdir -p ~/.claude/config-unlock-5"),
        ("mkdir di system-unlock", "mkdir ~/.claude/system-unlock-x"),
        ("cp verso la cartella", "cp ~/tmp/config-unlock-prova ~/.claude/"),
        ("mv verso la cartella", "mv ~/tmp/config-unlock-prova ~/.claude"),
        ("cp -t", "cp -t ~/.claude ~/tmp/config-unlock-prova"),
        ("ln -s verso la cartella", "ln -s ~/tmp/config-unlock-prova ~/.claude/"),
        ("cd e mv verso il punto", "cd ~/.claude && mv ~/tmp/config-unlock-prova ."),
        ("cp di settings.json verso la cartella", "cp ~/tmp/x/settings.json ~/.claude/"),
        ("mv di settings.json verso la cartella", "mv ~/tmp/x/settings.json ~/.claude/"),
        (">& verso settings.json", "echo x >&~/.claude/settings.json"),
        ("cp dello sblocco con 2>/dev/null", "cp ~/tmp/config-unlock-prova ~/.claude/ 2>/dev/null"),
        ("cp di settings.json con le uscite chiuse", "cp ~/tmp/x/settings.json ~/.claude/ >/dev/null 2>&1"),
        ("cp dello sblocco e ;", "cp ~/tmp/config-unlock-prova ~/.claude;true"),
        ("cp dello sblocco e &&", "cp ~/tmp/config-unlock-prova ~/.claude&&true"),
        ("cd con ; e cp verso il punto", "cd ~/.claude; cp ~/tmp/config-unlock-prova ."),
        ("cp -R del contenuto di una cartella", "cp -R ~/tmp/. ~/.claude/"),
        ("rsync del contenuto di una cartella", "rsync -a ~/tmp/ ~/.claude/"),
    ]
    casi = [(f"guardia: {n}", b.guardia(BD, c), "ask") for n, c in chiedono]
    casi += [(f"dispatcher: {n}", b.dispatcher(c), "ask") for n, c in chiedono]
    tacciono = [
        ("cp di un file qualunque in ~/.claude", "cp ~/tmp/a.txt ~/.claude/", None),
        ("cp di uno sblocco fuori da ~/.claude", "cp ~/.claude/config-unlock-x ~/tmp/", None),
        ("mkdir di una cartella unlock altrove", "mkdir -p ~/progetto/unlock", None),
        ("mkdir sotto data", "mkdir -p ~/.claude/data/appunti", None),
        ("cp fra due cartelle senza config", "cp -R ~/tmp/x ~/progetto/", None),
    ]
    casi += [(f"resta muto: {n}", b.guardia(BD, c, cwd), "silent") for n, c, cwd in tacciono]
    return verifica("MS04", casi)


@gruppo
def test_ms05(b: Banco):
    bersaglio = b.claude / "hooks" / "x.py"
    bersaglio.parent.mkdir(parents=True, exist_ok=True)
    sblocco = b.claude / "config-unlock-ms"
    casi = [("senza sblocco", b.write(bersaglio), "deny")]
    sblocco.mkdir()
    casi.append(("sblocco come cartella", b.write(bersaglio), "deny"))
    sblocco.rmdir()
    vero = b.home / "tmp" / "vero"
    vero.write_text("", encoding="utf-8")
    try:
        os.symlink(vero, sblocco)
    except (OSError, NotImplementedError):
        print("MS05 (link): saltato, qui i link simbolici non si creano")
    else:
        casi.append(("sblocco come link", b.write(bersaglio), "deny"))
        sblocco.unlink()
    sblocco.write_text("", encoding="utf-8")
    casi.append(("sblocco come file vero", b.write(bersaglio), "allow"))
    return verifica("MS05", casi)


TESTS = {"MS01": test_ms01, "MS02": test_ms02, "MS03": test_ms03, "MS04": test_ms04, "MS05": test_ms05}
GUARDIE = ("block-dangerous.py", "bash-dispatcher.sh", "forma_comando.py", "protect_claude_md.py")


def avvelena(repo: Path, ref: str) -> int:
    """Ogni gruppo, con le guardie com'erano su `ref`, deve fallire col suo codice."""
    elenco = subprocess.run(["git", "-C", str(repo), "ls-tree", "--name-only", f"{ref}:hooks"], capture_output=True,
                            text=True, encoding="utf-8", check=False)
    assert elenco.returncode == 0, f"veleno: la base {ref} non si legge da {repo}: {elenco.stderr.strip()}"
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
                    print(f"VELENO {codice} ROSSO: {str(e)[:160]}")
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
    print(f"PASS memoria e sblocco gruppi={len(TESTS)} casi={totale}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
