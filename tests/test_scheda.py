#!/usr/bin/env python3
"""TS01-TS07: titolo e colore della scheda del terminale (hooks/scheda-terminale.py, 16/10/2026).

TS01 lo stato segue l'evento: al lavoro giallo, attende verde, problema rosso (StopFailure). Senza
     colore lo stato è scritto nel titolo.
TS02 il progetto viene da «/inizio <nome>», poi dalla radice git (il repo principale anche da un
     worktree), poi dalla cartella.
TS03 il colore va solo dove il terminale lo sa fare: DECAC in Windows Terminal, OSC 6 in iTerm2,
     altrove solo il titolo. Dove c'è il colore il titolo è il solo progetto, che si legge intero.
TS04 se stato e progetto non cambiano l'hook non scrive niente, e il titolo non porta caratteri
     di controllo.
TS05 un input rotto o un evento sconosciuto non scrive niente ed esce 0.
TS06 settings.json collega l'hook ai sette eventi in async e spegne il titolo di Claude Code.
TS07 un evento partito prima dell'ultimo salvato non sovrascrive lo stato.
TS08 all'avvio di una sessione sparisce lo stato delle sessioni ferme da una settimana, e solo quello.

Nessun caso scrive sul terminale vero: ARTURO_SCHEDA_USCITA manda le sequenze in un file.
Sulla base b0ec3ac ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
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

EVENTI = ("SessionStart", "UserPromptSubmit", "PostToolUse", "Notification", "Stop", "StopFailure", "SessionEnd")


def hook(repo: Path, codice: str) -> Path:
    p = repo / "hooks" / "scheda-terminale.py"
    assert p.is_file(), f"{codice} manca hooks/scheda-terminale.py"
    return p


class Casa:
    def __init__(self, repo: Path, codice: str, terminale: dict | None = None):
        self.hook = hook(repo, codice)
        self.dir = Path(tempfile.mkdtemp(prefix="arturo-scheda."))
        self.home = self.dir / "home"
        self.home.mkdir()
        self.uscita = self.dir / "uscita.txt"
        self.env = {k: v for k, v in os.environ.items()
                    if k not in ("WT_SESSION", "TERM_PROGRAM", "CLAUDE_CONFIG_DIR", "ARTURO_SCHEDA_USCITA")}
        self.env.update(HOME=str(self.home), USERPROFILE=str(self.home), ARTURO_SCHEDA_USCITA=str(self.uscita),
                        PYTHONDONTWRITEBYTECODE="1", **(terminale or {}))

    def evento(self, nome: str, cwd: Path | None = None, sessione: str = "s1", **altro) -> str:
        """Lancia l'hook e rende quello che ha scritto in questo giro."""
        prima = self.uscita.read_text(encoding="utf-8") if self.uscita.exists() else ""
        dati = {"hook_event_name": nome, "session_id": sessione, "cwd": str(cwd or self.dir), **altro}
        r = subprocess.run([sys.executable, "-B", str(self.hook)], input=json.dumps(dati).encode("utf-8"),
                           capture_output=True, env=self.env, timeout=30)
        assert r.returncode == 0, f"hook {nome}: exit {r.returncode} {r.stderr[-300:]!r}"
        dopo = self.uscita.read_text(encoding="utf-8") if self.uscita.exists() else ""
        return dopo[len(prima):]

    def chiudi(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)


def git(cartella: Path, *argomenti: str) -> None:
    env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid")
    subprocess.run(["git", "-C", str(cartella), *argomenti], check=True, capture_output=True, env=env, timeout=60)


def test_ts01(repo: Path) -> None:
    c = Casa(repo, "TS01", {"WT_SESSION": "prova"})
    try:
        lavoro = c.evento("UserPromptSubmit", prompt="scrivi il capitolo")
        assert "\x1b[2;15;3,|" in lavoro, f"TS01 al lavoro non è giallo: {lavoro!r}"
        assert "\x1b[2;15;2,|" in c.evento("Stop"), "TS01 a fine turno non è verde"
        assert "\x1b[2;15;3,|" in c.evento("PostToolUse"), "TS01 dopo un permesso non torna giallo"
        assert "\x1b[2;15;2,|" in c.evento("Notification"), "TS01 una richiesta di permesso non è verde"
        assert "\x1b[2;15;1,|" in c.evento("StopFailure", error="rate_limit"), "TS01 l'errore non è rosso"
        fine = c.evento("SessionEnd")
        assert fine.startswith("\x1b]0;\x07"), f"TS01 a fine sessione il titolo non torna vuoto: {fine!r}"
    finally:
        c.chiudi()
    # Senza colore lo stato sta nel titolo.
    c = Casa(repo, "TS01")
    try:
        for evento, parola in (("UserPromptSubmit", "al lavoro"), ("Stop", "attende"), ("StopFailure", "problema")):
            uscita = c.evento(evento, prompt="vai")
            assert f" · {parola}\x07" in uscita, f"TS01 senza colore il titolo non dice «{parola}»: {uscita!r}"
    finally:
        c.chiudi()


def test_ts02(repo: Path) -> None:
    c = Casa(repo, "TS02")
    try:
        libro = c.dir / "libro"
        (libro / "capitoli").mkdir(parents=True)
        git(libro, "init", "-q")
        (libro / "a.md").write_text("x\n", encoding="utf-8")
        git(libro, "add", "a.md")
        git(libro, "commit", "-qm", "a")
        assert "\x1b]0;libro · " in c.evento("SessionStart", cwd=libro / "capitoli", sessione="g"), \
            "TS02 il progetto non è la radice git"
        ramo = c.dir / "ramo"
        git(libro, "worktree", "add", "-q", str(ramo))
        assert "\x1b]0;libro · " in c.evento("SessionStart", cwd=ramo, sessione="w"), \
            "TS02 da un worktree il progetto non è il repo principale"
        sciolta = c.dir / "appunti"
        sciolta.mkdir()
        assert "\x1b]0;appunti · " in c.evento("SessionStart", cwd=sciolta, sessione="d"), \
            "TS02 fuori da git il progetto non è la cartella"
        uscita = c.evento("UserPromptSubmit", cwd=sciolta, sessione="d", prompt="/inizio --tutti romanzo -- rileggi")
        assert "\x1b]0;romanzo · al lavoro" in uscita, f"TS02 /inizio non dà il progetto: {uscita!r}"
        assert "\x1b]0;romanzo · attende" in c.evento("Stop", cwd=sciolta, sessione="d"), \
            "TS02 il progetto di /inizio non resta per la sessione"
    finally:
        c.chiudi()


def test_ts03(repo: Path) -> None:
    for terminale, atteso, vietati in (
            ({"WT_SESSION": "x"}, "\x1b[2;15;3,|", ("]6;1;bg",)),
            ({"TERM_PROGRAM": "iTerm.app"}, "\x1b]6;1;bg;red;brightness;230\x07", (",|",)),
            ({"TERM_PROGRAM": "Apple_Terminal"}, "\x1b]0;", (",|", "]6;1;bg"))):
        c = Casa(repo, "TS03", terminale)
        try:
            uscita = c.evento("UserPromptSubmit", prompt="vai")
            assert atteso in uscita and not any(v in uscita for v in vietati), \
                f"TS03 sequenze sbagliate per {terminale}: {uscita!r}"
            titolo = uscita.split("\x07", 1)[0]
            assert (" · " in titolo) == (terminale.get("TERM_PROGRAM") == "Apple_Terminal"), \
                f"TS03 dove c'è il colore il titolo è solo il progetto, altrove porta lo stato: {titolo!r}"
        finally:
            c.chiudi()


def test_ts04(repo: Path) -> None:
    c = Casa(repo, "TS04", {"WT_SESSION": "x"})
    try:
        assert c.evento("UserPromptSubmit", prompt="vai"), "TS04 il primo evento non scrive"
        assert c.evento("PostToolUse") == "", "TS04 PostToolUse riscrive uno stato che non cambia"
        uscita = c.evento("UserPromptSubmit", sessione="z", prompt="/inizio ro\x1b]0;finto\x07manzo")
        titolo = uscita.split("\x07", 1)[0]
        assert "\x1b]0;" in titolo and "\x1b" not in titolo[4:] and "finto" not in titolo[:8], \
            f"TS04 il titolo porta caratteri di controllo: {uscita!r}"
    finally:
        c.chiudi()


def test_ts05(repo: Path) -> None:
    c = Casa(repo, "TS05", {"WT_SESSION": "x"})
    try:
        r = subprocess.run([sys.executable, "-B", str(c.hook)], input=b"non json", capture_output=True, env=c.env,
                           timeout=30)
        assert r.returncode == 0 and not c.uscita.exists(), "TS05 un input rotto scrive o fallisce"
        assert c.evento("PreToolUse") == "", "TS05 un evento non previsto scrive"
    finally:
        c.chiudi()


def test_ts06(repo: Path) -> None:
    hook(repo, "TS06")
    s = json.loads((repo / "settings.json").read_text(encoding="utf-8"))
    for evento in EVENTI:
        voci = [h for g in s.get("hooks", {}).get(evento, []) for h in g.get("hooks", [])
                if "scheda-terminale.py" in h.get("command", "")]
        assert len(voci) == 1 and voci[0].get("async") is True, f"TS06 {evento}: l'hook manca, è doppio o non è async"
    assert s.get("env", {}).get("CLAUDE_CODE_DISABLE_TERMINAL_TITLE") == "1", \
        "TS06 Claude Code riscriverebbe il titolo della scheda"


def test_ts07(repo: Path) -> None:
    c = Casa(repo, "TS07", {"WT_SESSION": "x"})
    try:
        cache = c.home / ".claude" / "cache" / "scheda"
        cache.mkdir(parents=True)
        (cache / "s1.json").write_text(json.dumps({"stato": "attende", "progetto": "x", "quando": time.time() + 60}),
                                       encoding="utf-8")
        assert c.evento("PostToolUse") == "", "TS07 un evento arrivato in ritardo sovrascrive lo stato"
    finally:
        c.chiudi()


def test_ts08(repo: Path) -> None:
    c = Casa(repo, "TS08", {"WT_SESSION": "x"})
    try:
        cache = c.home / ".claude" / "cache" / "scheda"
        cache.mkdir(parents=True)
        vecchia, recente = cache / "chiusa-male.json", cache / "altra-aperta.json"
        for f in (vecchia, recente):
            f.write_text(json.dumps({"stato": "lavoro", "progetto": "x", "quando": 0}), encoding="utf-8")
        otto_giorni_fa = time.time() - 8 * 24 * 3600
        os.utime(vecchia, (otto_giorni_fa, otto_giorni_fa))
        c.evento("PostToolUse")
        assert vecchia.exists(), "TS08 un evento qualsiasi pulisce: la pulizia è solo all'avvio"
        c.evento("SessionStart", sessione="s2")
        assert not vecchia.exists(), "TS08 lo stato di una sessione chiusa male resta per sempre"
        assert recente.exists(), "TS08 l'avvio toglie lo stato di un'altra sessione aperta"
    finally:
        c.chiudi()


TESTS = {"TS01": test_ts01, "TS02": test_ts02, "TS03": test_ts03, "TS04": test_ts04, "TS05": test_ts05,
         "TS06": test_ts06, "TS07": test_ts07, "TS08": test_ts08}


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
