#!/usr/bin/env python3
"""RM04-RM10: i bug medi A4-A10 della revisione di Arturo del 20/11/2026 (#6250).

RM04 A4 bin/fine-coda.py: una coda alla volta. Con il lucchetto di un'altra coda viva la seconda aspetta e,
     oltre FINE_CODA_ATTESA, esce 8 senza commit; un lucchetto vecchio (o col pid di un processo morto) si
     toglie da solo; a coda finita il lucchetto non resta.
RM05 A5 bin/salva-automatico.py: dopo un /fine a metà il lavoro venuto dopo entra in un handoff automatico
     nuovo, con la riga "- Dopo il /fine:" e solo le richieste dopo; l'handoff di /fine resta com'era. Una
     risposta corta dopo il /fine ("salva") e un /fine --rotazione lanciato col tool Skill non ne creano.
RM06 A6 hooks/session-end.sh: lo sblocco della protezione config della sessione si cancella anche fuori da
     un progetto e in un worktree (.git è un file).
RM07 A7 bin/handoff-gate.sh: un handoff con a capo Windows (\\r\\n) e la sezione giusta è verde.
RM08 A8 hooks/inject-now.sh: /arturo:fine annuncia personale/fine.md come /fine.
RM09 A9 bin/cleanup-stale-plugins.sh: un plugin spento, Arturo e un plugin di progetto non sono da togliere.
RM10 A10 bin/sync-progetti.sh: un remoto che non risponde e un ramo senza upstream non escono come conflitto.

Sulla base d0f56af sono rossi tutti e sette.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CASI = ["RM04", "RM05", "RM06", "RM07", "RM08", "RM09", "RM10"]
DISCRIMINANTI = list(CASI)
BASH = shutil.which("bash") or "bash"


def env_di(home: Path, **extra) -> dict:
    e = dict(os.environ, HOME=str(home), USERPROFILE=str(home), ARTURO_TELEMETRIA="0", ARTURO_AGGIORNAMENTI="manuali",
             PYTHONDONTWRITEBYTECODE="1", GIT_TERMINAL_PROMPT="0", GIT_CONFIG_GLOBAL=os.devnull,
             GIT_CONFIG_NOSYSTEM="1", ARTURO_TODO=str(home / ".claude" / "data" / "todo" / "eventi.jsonl"))
    for k in ("PROJECTS_BASE", "CLAUDE_CONFIG_DIR", "CLAUDE_CODE_SESSION_ID", "ARTURO_RADICE", "FINE_CODA_CLAUDE"):
        e.pop(k, None)
    e.update(extra)
    return e


def lancia(cmd: list, env: dict, cwd: Path | None = None, entrata: str = "", timeout: int = 120):
    return subprocess.run(cmd, input=entrata, capture_output=True, text=True, encoding="utf-8", errors="replace",
                          env=env, cwd=str(cwd) if cwd else None, timeout=timeout)


def git(dove: Path, *a: str, env: dict) -> None:
    subprocess.run(["git", "-C", str(dove), "-c", "user.name=prova", "-c", "user.email=prova@example.invalid", *a],
                   check=True, capture_output=True, env=env)


def casa(tmp: Path, nome: str) -> Path:
    home = tmp / nome
    (home / ".claude" / "session-env").mkdir(parents=True)
    return home


# --- RM04 ---------------------------------------------------------------------------------------------------

def rm04(repo: Path, tmp: Path) -> list:
    rossi = []
    home = casa(tmp, "h04")
    cl = home / ".claude"
    lucchetto = cl / "session-env" / "fine-coda.lock"
    env = env_di(home, FINE_CODA_CLAUDE=str(cl), FINE_CODA_ATTESA="1")
    coda = [sys.executable, "-B", str(repo / "bin" / "fine-coda.py")]

    lucchetto.write_text(f"{os.getpid()}\n", encoding="ascii")   # la coda di un'altra sessione, viva
    r = lancia(coda, env, cwd=home)
    if r.returncode != 8 or "un'altra /fine" not in r.stdout:
        rossi.append(f"RM04 con un'altra coda viva la seconda non si ferma con 8: rc {r.returncode} {r.stdout[-300:]!r}")
    if not lucchetto.exists():
        rossi.append("RM04 la seconda coda ha tolto il lucchetto dell'altra")

    vecchio = time.time() - 2 * 3600                              # una coda interrotta due ore fa
    os.utime(lucchetto, (vecchio, vecchio))
    r = lancia(coda, env, cwd=home)
    if r.returncode != 0:
        rossi.append(f"RM04 un lucchetto vecchio ferma la coda: rc {r.returncode} {r.stdout[-300:]!r}")
    if lucchetto.exists():
        rossi.append("RM04 a coda finita il lucchetto resta")

    if os.name != "nt":                                          # su Windows viva() non sa leggere il pid
        morto = subprocess.Popen([sys.executable, "-c", "pass"])
        morto.wait()
        lucchetto.write_text(f"{morto.pid}\n", encoding="ascii")
        r = lancia(coda, env, cwd=home)
        if r.returncode != 0 or lucchetto.exists():
            rossi.append(f"RM04 il lucchetto di un processo morto ferma la coda: rc {r.returncode} {r.stdout[-300:]!r}")
    return rossi


# --- RM05 ---------------------------------------------------------------------------------------------------

def utente(testo: str, sid: str) -> dict:
    return {"type": "user", "entrypoint": "cli", "sessionId": sid, "message": {"role": "user", "content": testo}}


def uso(nome: str, inp: dict, tid: str, sid: str) -> dict:
    return {"type": "assistant", "entrypoint": "cli", "sessionId": sid,
            "message": {"role": "assistant", "content": [{"type": "tool_use", "id": tid, "name": nome, "input": inp}]}}


def fine_typed(sid: str) -> dict:
    return utente("<command-message>fine</command-message>\n<command-name>/fine</command-name>\n"
                  "<command-args></command-args>", sid)


def rm05(repo: Path, tmp: Path) -> list:
    rossi = []
    home = casa(tmp, "h05")
    cl = home / ".claude"
    for d in ("bin", "hooks"):
        shutil.copytree(str(repo / d), str(cl / d), ignore=shutil.ignore_patterns("__pycache__", "*.local"))
    progetto = home / "Documents" / "ClaudeCode" / "mio-libro"
    progetto.mkdir(parents=True)
    env = env_di(home, ARTURO_MEMORIA="1")
    git(progetto, "init", "-q", "-b", "main", env=env)
    (progetto / "capitolo.md").write_text("uno\n", encoding="utf-8")
    git(progetto, "add", "-A", env=env)
    git(progetto, "commit", "-q", "-m", "primo", env=env)
    projects = cl / "projects" / "-prova"
    projects.mkdir(parents=True)
    cartella_h = cl / "data" / "handoffs" / "mio-libro"
    cartella_h.mkdir(parents=True)

    def giro(sid: str, record: list) -> tuple:
        t = projects / f"{sid}.jsonl"
        t.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in record), encoding="utf-8")
        h_fine = cartella_h / f"HANDOFF_2026-11-20_10-0{len(list(cartella_h.glob('*.md')))}.md"
        testo_fine = f"# Session Handoff\n## Progetto\n- Nome: mio-libro\n- Sessione: {sid}\n## Task Pendenti\nNessun task pendente.\n"
        h_fine.write_text(testo_fine, encoding="utf-8")
        prima = set(cartella_h.glob("HANDOFF_*.md"))
        dati = {"session_id": sid, "transcript_path": str(t), "cwd": str(progetto), "reason": "prompt_input_exit"}
        r = lancia([sys.executable, "-B", str(cl / "bin" / "salva-automatico.py")], env, cwd=progetto,
                   entrata=json.dumps(dati))
        nuovi = sorted(set(cartella_h.glob("HANDOFF_*.md")) - prima)
        return r, h_fine, testo_fine, nuovi

    sid = "s-meta"
    scritto = progetto / "capitolo-tre.md"
    r, h_fine, testo_fine, nuovi = giro(sid, [
        utente("Riscrivi il capitolo due PRIMA-DEL-FINE", sid), fine_typed(sid),
        utente("Adesso scrivi il capitolo tre con la scena DOPO-IL-FINE", sid),
        uso("Write", {"file_path": str(scritto), "content": "tre\n"}, "t1", sid)])
    if len(nuovi) != 1:
        rossi.append(f"RM05 dopo un /fine a metà il lavoro venuto dopo non ha un handoff nuovo: {r.stdout.strip()!r}")
    else:
        testo = nuovi[0].read_text(encoding="utf-8")
        if f"- Dopo il /fine: {h_fine.name}" not in testo or "DOPO-IL-FINE" not in testo or "PRIMA-DEL-FINE" in testo:
            rossi.append(f"RM05 l'handoff automatico dopo il /fine non porta solo il lavoro venuto dopo: {testo[:600]!r}")
    if h_fine.read_text(encoding="utf-8") != testo_fine:
        rossi.append("RM05 il salvataggio ha riscritto l'handoff di /fine")

    sid = "s-salva"
    r, _, _, nuovi = giro(sid, [utente("Riscrivi il capitolo due con la scena del tram", sid), fine_typed(sid),
                                utente("salva", sid)])
    if nuovi or "NIENTE" not in r.stdout:
        rossi.append(f"RM05 una risposta corta dopo il /fine crea un handoff: {r.stdout.strip()!r}")

    sid = "s-rotazione"
    r, _, _, nuovi = giro(sid, [utente("Riscrivi il capitolo due con la scena del tram", sid),
                                uso("Skill", {"skill": "arturo:fine", "args": "--rotazione"}, "t9", sid)])
    if nuovi or "NIENTE" not in r.stdout:
        rossi.append(f"RM05 un /fine --rotazione col tool Skill non conta come /fine: {r.stdout.strip()!r}")
    return rossi


# --- RM06 ---------------------------------------------------------------------------------------------------

def rm06(repo: Path, tmp: Path) -> list:
    rossi = []
    home = casa(tmp, "h06")
    env = env_di(home, ARTURO_MEMORIA="0")
    fuori = tmp / "fuori"                                          # né git né CLAUDE.md: la home, una cartella qualsiasi
    fuori.mkdir()
    worktree = tmp / "worktree"                                    # un worktree: .git è un file
    worktree.mkdir()
    (worktree / ".git").write_text("gitdir: /altrove/.git/worktrees/w\n", encoding="utf-8")
    for nome, cwd in (("fuori", fuori), ("worktree", worktree)):
        sid = f"s-{nome}"
        sblocco = home / ".claude" / f"config-unlock-{sid}"
        sblocco.write_text("", encoding="utf-8")
        lancia([BASH, str(repo / "hooks" / "session-end.sh")], env, cwd=cwd,
               entrata=json.dumps({"session_id": sid, "hook_event_name": "SessionEnd", "reason": "other"}))
        if sblocco.exists():
            rossi.append(f"RM06 lo sblocco della config resta dopo la chiusura da {nome}")
    return rossi


# --- RM07 ---------------------------------------------------------------------------------------------------

def rm07(repo: Path, tmp: Path) -> list:
    home = casa(tmp, "h07")
    handoff = tmp / "HANDOFF_crlf.md"
    handoff.write_bytes(b"# Session Handoff\r\n\r\n## Ripartenza\r\nFatto.\r\n\r\n## Task Pendenti\r\n\r\n"
                        b"Nessun task pendente.\r\n")
    r = lancia([BASH, str(repo / "bin" / "handoff-gate.sh"), str(handoff)], env_di(home))
    if r.returncode != 0 or "GATE HANDOFF: verde" not in r.stdout:
        return [f"RM07 un handoff con a capo Windows è rosso: rc {r.returncode} {(r.stdout + r.stderr)[-300:]!r}"]
    return []


# --- RM08 ---------------------------------------------------------------------------------------------------

def rm08(repo: Path, tmp: Path) -> list:
    rossi = []
    home = casa(tmp, "h08")
    (home / ".claude" / "personale").mkdir()
    (home / ".claude" / "personale" / "fine.md").write_text("Le mie aggiunte a /fine.\n", encoding="utf-8")
    for prompt in ("/fine", "/arturo:fine --rotazione"):
        r = lancia([BASH, str(repo / "hooks" / "inject-now.sh")], env_di(home, ARTURO_MEMORIA="0"), cwd=home,
                   entrata=json.dumps({"prompt": prompt, "session_id": "s-rm08", "hook_event_name": "UserPromptSubmit"}))
        if "PERSONALE: /fine ha aggiunte" not in r.stdout:
            rossi.append(f"RM08 {prompt!r} non annuncia personale/fine.md: {r.stdout[-300:]!r}")
    return rossi


# --- RM09 ---------------------------------------------------------------------------------------------------

def rm09(repo: Path, tmp: Path) -> list:
    home = casa(tmp, "h09")
    plugins = home / ".claude" / "plugins"
    plugins.mkdir()
    (home / ".claude" / "settings.json").write_text(json.dumps({"enabledPlugins": {"attivo@x": True, "spento@x": False}}),
                                                     encoding="utf-8")
    (plugins / "installed_plugins.json").write_text(json.dumps({"plugins": {
        "attivo@x": [{"scope": "user"}], "spento@x": [{"scope": "user"}], "orfano@y": [{"scope": "user"}],
        "arturo@arturo": [{"scope": "user"}], "progetto@z": [{"scope": "project", "projectPath": "/p"}]}}),
        encoding="utf-8")
    r = lancia([BASH, str(repo / "bin" / "cleanup-stale-plugins.sh"), "--dry-run"], env_di(home))
    elencati = [riga[4:] for riga in r.stdout.splitlines() if riga.startswith("  - ")]
    if r.returncode != 0 or elencati != ["orfano@y"]:
        return [f"RM09 la pulizia toglierebbe {elencati} invece del solo orfano@y: {r.stdout[-300:]!r}"]
    return []


# --- RM10 ---------------------------------------------------------------------------------------------------

def rm10(repo: Path, tmp: Path) -> list:
    rossi = []
    home = casa(tmp, "h10")
    env = env_di(home)
    radice = tmp / "progetti"
    nudo = tmp / "remoto.git"
    subprocess.run(["git", "init", "-q", "--bare", str(nudo)], check=True, capture_output=True, env=env)
    for nome, remoto in (("sparito", str(tmp / "non-esiste.git")), ("senza-upstream", str(nudo))):
        d = radice / nome
        d.mkdir(parents=True)
        git(d, "init", "-q", "-b", "main", env=env)
        (d / "a.txt").write_text("a\n", encoding="utf-8")
        git(d, "add", "-A", env=env)
        git(d, "commit", "-q", "-m", "primo", env=env)
        git(d, "remote", "add", "origin", remoto, env=env)
    r = lancia([BASH, str(repo / "bin" / "sync-progetti.sh"), str(radice)], env, timeout=180)
    righe = {n: [x for x in r.stdout.splitlines() if x.startswith(f"ERRORE: pull {n} ")] for n in ("sparito", "senza-upstream")}
    for nome, attesa in (("sparito", "non raggiungibile"), ("senza-upstream", "ramo remoto da seguire")):
        riga = " ".join(righe[nome])
        if not riga or "conflitto" in riga or attesa not in riga:
            rossi.append(f"RM10 il pull fallito di {nome} non dice la sua causa: {riga or r.stdout[-400:]!r}")
    return rossi


def prova(repo: Path) -> list:
    rossi = []
    for caso in (rm04, rm05, rm06, rm07, rm08, rm09, rm10):
        with tempfile.TemporaryDirectory(prefix="arturo-rm-") as tmp:
            try:
                rossi += caso(repo, Path(tmp))
            except FileNotFoundError as e:                        # sulla base un file del caso può mancare
                rossi.append(f"{caso.__name__.upper()} file assente: {e}")
    return rossi


def main() -> int:
    for flusso in (sys.stdout, sys.stderr):  # su Windows la pipe è in cp1252
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    argomenti = parser.parse_args()
    rossi = prova(Path(argomenti.repo).resolve())
    if argomenti.baseline_ref:
        codici = sorted({r.split()[0] for r in rossi})
        assert codici == DISCRIMINANTI, f"baseline non discriminante: rossi {codici}, attesi {DISCRIMINANTI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    print(f"bug medi della revisione del 20/11: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
