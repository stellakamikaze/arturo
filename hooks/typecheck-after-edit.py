#!/usr/bin/env python3
"""
Type-check dopo ogni Edit/Write su un file TypeScript o Vue (PostToolUse).

«Dopo ogni modifica verifica subito» come garanzia e non come promessa: un errore
di tipo arriva a Claude al passo in cui lo crea, non al build di fine giornata.
Il comando non lo inventa: lo prende dal package.json del progetto (script
`typecheck`, altrimenti il segmento tsc/vue-tsc di `build`), così il check è
lo stesso gate del build. Senza package.json e tsconfig.json, o senza tsc
installato nel progetto, tace.

Exit 0 = verde o fuori ambito (silenzioso). Exit 2 = errori di tipo, stderr al modello.
"""
import hashlib
import json
import os
import shlex
import subprocess
import sys
import tempfile

ESTENSIONI = (".ts", ".tsx", ".vue", ".mts", ".cts")
STRUMENTI = ("tsc", "vue-tsc")
LIMITE_S = 90
RIGHE_MAX = 30


def trova_progetto(path):
    home = os.path.expanduser("~")
    d = os.path.dirname(os.path.abspath(path))
    while d and d != home and d != os.path.dirname(d):
        if os.path.isfile(os.path.join(d, "package.json")) and os.path.isfile(os.path.join(d, "tsconfig.json")):
            return d
        d = os.path.dirname(d)
    return None


def comando_dal_progetto(progetto):
    try:
        with open(os.path.join(progetto, "package.json"), encoding="utf-8") as f:
            script = json.load(f).get("scripts", {}) or {}
    except Exception:
        return None
    for nome in ("typecheck", "build"):
        for segmento in str(script.get(nome, "")).split("&&"):
            try:
                argv = shlex.split(segmento)
            except ValueError:
                continue
            if argv and argv[0] in STRUMENTI:
                return argv
    return None


def in_worktree(progetto):
    try:
        out = subprocess.run(
            ["git", "-C", progetto, "rev-parse", "--path-format=absolute", "--git-dir", "--git-common-dir"],
            capture_output=True, text=True, timeout=5,
        ).stdout.split()
    except Exception:
        return False
    return len(out) == 2 and os.path.realpath(out[0]) != os.path.realpath(out[1])


def prendi_lock(progetto):
    """Lock non bloccante per progetto: due check in parallelo sullo stesso tree si pestano."""
    try:
        import fcntl
    except ImportError:  # Windows: niente lock, il check gira comunque
        return True, None
    h = hashlib.sha1(progetto.encode()).hexdigest()[:12]
    f = open(os.path.join(tempfile.gettempdir(), f"typecheck-{h}.lock"), "w")
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True, f
    except OSError:
        f.close()
        return False, None


def main():
    try:
        dati = json.load(sys.stdin)
    except Exception:
        return 0
    path = (dati.get("tool_input") or {}).get("file_path") or ""
    if not path.endswith(ESTENSIONI):
        return 0
    parti = os.path.normpath(path).split(os.sep)
    if "node_modules" in parti or "dist" in parti:
        return 0

    progetto = trova_progetto(path)
    if not progetto:
        return 0
    argv = comando_dal_progetto(progetto)
    if not argv:
        return 0

    exe = os.path.join(progetto, "node_modules", ".bin", argv[0] + (".cmd" if os.name == "nt" else ""))
    if not os.path.exists(exe):
        print(f"typecheck saltato: manca {exe} (npm install in {progetto})", file=sys.stderr)
        return 0
    argv = [exe] + argv[1:]
    cache_condivisa = []
    if in_worktree(progetto) and ("-b" in argv or "--build" in argv):
        # tsBuildInfoFile sta in node_modules/.tmp, che nel worktree è un symlink al
        # tree principale. --force ignora la cache del principale; dopo il check la
        # cache scritta dal worktree si cancella, o il principale leggerebbe un buildinfo
        # più recente dei suoi sorgenti e darebbe un falso verde.
        if "--force" not in argv:
            argv.append("--force")
        cache_condivisa = [os.path.join(progetto, "node_modules", ".tmp")]

    ok, lock = prendi_lock(progetto)
    if not ok:
        print("typecheck saltato: un altro check è già in corso su questo progetto", file=sys.stderr)
        return 0
    try:
        # node scrive in UTF-8: letto con la codifica di Windows un byte non mappato rende stdout None.
        r = subprocess.run(argv, cwd=progetto, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=LIMITE_S)
    except subprocess.TimeoutExpired:
        print(f"typecheck oltre {LIMITE_S}s su {progetto}: lancialo a mano prima del commit", file=sys.stderr)
        return 0
    except OSError as e:
        print(f"typecheck saltato: {exe} non parte ({e})", file=sys.stderr)
        return 0
    finally:
        for d in cache_condivisa:
            for nome in os.listdir(d) if os.path.isdir(d) else []:
                if nome.endswith(".tsbuildinfo"):
                    try:
                        os.remove(os.path.join(d, nome))
                    except OSError:
                        pass
        if lock:
            lock.close()

    if r.returncode == 0:
        return 0
    righe = [x for x in (r.stdout + r.stderr).splitlines() if x.strip()]
    corpo = "\n".join(righe[:RIGHE_MAX])
    if len(righe) > RIGHE_MAX:
        corpo += f"\n... altre {len(righe) - RIGHE_MAX} righe"
    print(
        f"TYPECHECK ROSSO ({' '.join(os.path.basename(a) if i == 0 else a for i, a in enumerate(argv))}, in {progetto}):\n"
        f"{corpo}\n"
        "Se sei a metà di una modifica su più file, finisci e poi ricontrolla.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
