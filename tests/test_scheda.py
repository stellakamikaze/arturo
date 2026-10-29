#!/usr/bin/env python3
"""TS01-TS07: titolo e colore della scheda del terminale (hooks/scheda-terminale.py, 16/10/2026).

TS01 lo stato segue l'evento: al lavoro giallo, attende verde, problema rosso (StopFailure). Il titolo
     è "LAVORANDO · <progetto>" al lavoro e "SBLOCCA · <progetto>" quando la sessione aspetta la persona
     (29/10/2026).
TS02 il progetto viene da "/inizio <nome>", poi dalla radice git (il repo principale anche da un
     worktree), poi dalla cartella.
TS03 il colore va solo dove il terminale lo sa fare: DECAC in Windows Terminal, OSC 6 in iTerm2,
     altrove solo il titolo. Al lavoro il titolo è "LAVORANDO · <progetto>" in ogni terminale.
TS04 se stato e progetto non cambiano l'hook non scrive niente, e il titolo non porta caratteri
     di controllo.
TS05 un input rotto o un evento sconosciuto non scrive niente ed esce 0.
TS06 settings.json collega l'hook ai sette eventi in async e spegne il titolo di Claude Code.
TS07 un evento partito prima dell'ultimo salvato non sovrascrive lo stato.
TS08 all'avvio di una sessione sparisce lo stato delle sessioni ferme da una settimana, e solo quello.
TS10 in Terminal di Apple la campanella (BEL) suona quando la sessione passa la mano (Notification,
     StopFailure); all'avvio, al lavoro, alla sola fine del turno e negli altri terminali no.
TS11 "SBLOCCA" solo quando la persona serve: permesso, domanda, errore, idle_prompt. La fine del turno
     da sola (Claude può aspettare un job in background) e le notifiche come auth_success no.
TS12 il nome è lo slug che il risolutore di /inizio stampa ("PROGETTO <slug>"), non le parole scritte,
     che cedono a un file scritto; un grep del sorgente non conta, neanche senza numeri di riga; senza
     /inizio vale la cartella di progetto dove Claude scrive (PROJECTS_BASE), e in ~/.claude contano
     hook e comandi, non piani e memoria; il titolo non porta caratteri di controllo o di formato.
TS13 a fine turno e su idle_prompt un job in background senza la sua notifica di fine nel transcript vale
     "LAVORANDO" (idle_prompt arriva anche con un comando Bash in background, 29/10/2026); un job finito o
     fermato, un server (vite, http.server) e un permesso tornano a SBLOCCA.
TS09 senza terminale di controllo (il caso normale di un hook su macOS e Linux) le sequenze vanno sul
     tty del processo claude trovato fra i padri. Senza claude fra i padri non si scrive niente.

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
        assert "\x1b[2;15;2,|" in c.evento("Notification", notification_type="permission_prompt"), \
            "TS01 una richiesta di permesso non è verde"
        assert "\x1b[2;15;1,|" in c.evento("StopFailure", error="rate_limit"), "TS01 l'errore non è rosso"
        fine = c.evento("SessionEnd")
        assert fine.startswith("\x1b]0;\x07"), f"TS01 a fine sessione il titolo non torna vuoto: {fine!r}"
    finally:
        c.chiudi()
    # Il titolo: LAVORANDO o SBLOCCA davanti al progetto.
    c = Casa(repo, "TS01")
    try:
        nome = c.dir.name
        for evento, titolo in (("UserPromptSubmit", f"]0;LAVORANDO · {nome}\x07"), ("StopFailure", f"]0;SBLOCCA · {nome}\x07")):
            uscita = c.evento(evento, prompt="vai")
            assert titolo in uscita, f"TS01 il titolo non dice {titolo!r}: {uscita!r}"
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
        assert "]0;libro\x07" in c.evento("SessionStart", cwd=libro / "capitoli", sessione="g"), \
            "TS02 il progetto non è la radice git"
        ramo = c.dir / "ramo"
        git(libro, "worktree", "add", "-q", str(ramo))
        assert "]0;libro\x07" in c.evento("SessionStart", cwd=ramo, sessione="w"), \
            "TS02 da un worktree il progetto non è il repo principale"
        sciolta = c.dir / "appunti"
        sciolta.mkdir()
        assert "]0;appunti\x07" in c.evento("SessionStart", cwd=sciolta, sessione="d"), \
            "TS02 fuori da git il progetto non è la cartella"
        uscita = c.evento("UserPromptSubmit", cwd=sciolta, sessione="d", prompt="/inizio --tutti romanzo -- rileggi")
        assert "\x1b]0;LAVORANDO · romanzo\x07" in uscita, f"TS02 /inizio non dà il progetto: {uscita!r}"
        assert "SBLOCCA · romanzo\x07" in c.evento("Notification", cwd=sciolta, sessione="d",
                                                   notification_type="idle_prompt"), \
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
            assert titolo == f"\x1b]0;LAVORANDO · {c.dir.name}", f"TS03 al lavoro il titolo non è LAVORANDO: {titolo!r}"
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


PS_FINTO = """#!/bin/sh
# ps finto: a ogni chiamata il padre successivo della catena in $CATENA (una riga per chiamata).
n=$(cat "$CONTA" 2>/dev/null || echo 0); n=$((n + 1)); echo $n > "$CONTA"
sed -n "${n}p" "$CATENA"
"""


def test_ts09(repo: Path) -> None:
    if os.name == "nt":
        print("TS09 saltato: su Windows la scheda passa da AttachConsole")
        return
    c = Casa(repo, "TS09", {"TERM_PROGRAM": "iTerm.app"})
    try:
        bin_, dev = c.dir / "bin", c.dir / "dev"
        bin_.mkdir()
        dev.mkdir()
        (bin_ / "ps").write_text(PS_FINTO, encoding="utf-8")
        (bin_ / "ps").chmod(0o755)
        del c.env["ARTURO_SCHEDA_USCITA"]
        for catena, atteso in ((["900 ?? /bin/sh", "800 ttys042 /opt/homebrew/bin/claude"], True),
                               (["900 ?? /bin/sh", "1 ?? /sbin/launchd"], False)):
            (c.dir / "catena").write_text("\n".join(catena) + "\n", encoding="utf-8")
            (c.dir / "conta").unlink(missing_ok=True)
            tty = dev / "ttys042"
            tty.write_text("", encoding="utf-8")
            env = dict(c.env, PATH=f"{bin_}:{c.env.get('PATH', '')}", ARTURO_SCHEDA_DEV=str(dev),
                       CATENA=str(c.dir / "catena"), CONTA=str(c.dir / "conta"))
            dati = {"hook_event_name": "UserPromptSubmit", "session_id": f"s{len(catena)}{atteso}", "cwd": str(c.dir)}
            # start_new_session: il hook nasce senza terminale di controllo, come sotto Claude Code.
            r = subprocess.run([sys.executable, "-B", str(c.hook)], input=json.dumps(dati).encode("utf-8"),
                               capture_output=True, env=env, timeout=30, start_new_session=True)
            assert r.returncode == 0, f"TS09 exit {r.returncode} {r.stderr[-300:]!r}"
            scritto = tty.read_text(encoding="utf-8")
            if atteso:
                assert "\x1b]6;1;bg;red;brightness;230\x07" in scritto, \
                    f"TS09 senza /dev/tty il colore non arriva al tty di claude: {scritto!r}"
            else:
                assert scritto == "", f"TS09 senza claude fra i padri ha scritto lo stesso: {scritto!r}"
    finally:
        c.chiudi()


def test_ts10(repo: Path) -> None:
    c = Casa(repo, "TS10", {"TERM_PROGRAM": "Apple_Terminal"})
    try:
        avvio = c.evento("SessionStart")
        assert avvio == f"\x1b]0;{c.dir.name}\x07", f"TS10 all'avvio il titolo è sbagliato o suona: {avvio!r}"
        lavoro = c.evento("UserPromptSubmit", prompt="vai")
        assert not lavoro.endswith("\x07\x07"), f"TS10 al lavoro suona la campanella: {lavoro!r}"
        assert not c.evento("Stop").endswith("\x07\x07"), "TS10 la sola fine del turno suona la campanella"
        for evento, altro in (("Notification", {"notification_type": "idle_prompt"}), ("StopFailure", {})):
            c.evento("UserPromptSubmit", prompt="vai")
            fermo = c.evento(evento, **altro)
            assert fermo.endswith("\x07\x07"), f"TS10 {evento} non suona la campanella: {fermo!r}"
    finally:
        c.chiudi()
    c = Casa(repo, "TS10")
    try:
        c.evento("UserPromptSubmit", prompt="vai")
        fermo = c.evento("Notification", notification_type="permission_prompt")
        assert "SBLOCCA" in fermo and not fermo.endswith("\x07\x07"), \
            f"TS10 fuori da Terminal di Apple suona la campanella: {fermo!r}"
    finally:
        c.chiudi()


def test_ts11(repo: Path) -> None:
    c = Casa(repo, "TS11", {"TERM_PROGRAM": "Apple_Terminal"})
    try:
        c.evento("UserPromptSubmit", prompt="/inizio romanzo")
        fermo = c.evento("Stop")
        assert "SBLOCCA" not in fermo, f"TS11 la sola fine del turno dice SBLOCCA: {fermo!r}"
        assert c.evento("Notification", notification_type="auth_success") == "", \
            "TS11 una notifica che non chiede niente cambia il titolo"
        for tipo in ("idle_prompt", "permission_prompt", "elicitation_dialog", "worker_permission_prompt"):
            c.evento("UserPromptSubmit", prompt="vai")
            uscita = c.evento("Notification", notification_type=tipo)
            assert "]0;SBLOCCA · romanzo\x07" in uscita, f"TS11 {tipo} non dice SBLOCCA · romanzo: {uscita!r}"
    finally:
        c.chiudi()


def bash(comando: str, stdout: str) -> dict:
    return {"tool_name": "Bash", "tool_input": {"command": comando}, "tool_response": {"stdout": stdout}}


def test_ts12(repo: Path) -> None:
    c = Casa(repo, "TS12", {"TERM_PROGRAM": "Apple_Terminal"})
    c.env.pop("PROJECTS_BASE", None)  # quella di chi lancia il banco punterebbe fuori dalla HOME di prova
    try:
        assert "]0;LAVORANDO · due mondi\x07" in c.evento("UserPromptSubmit", prompt="/inizio due mondi"), \
            "TS12 prima della risoluzione il titolo non è il testo intero di /inizio"
        uscita = c.evento("PostToolUse", **bash('python3 ~/.claude/bin/arturo contesto "due mondi"',
                                                "PROGETTO due-mondi-myway\ncartella: x\nrc=0"))
        assert "]0;LAVORANDO · due-mondi-myway\x07" in uscita, f"TS12 lo slug risolto non arriva al titolo: {uscita!r}"
        c.evento("UserPromptSubmit", sessione="g", prompt="/inizio x y")
        grep = c.evento("PostToolUse", sessione="g", **bash("grep -n PROGETTO bin/contesto.py",
                                                           '314:    righe = [f"PROGETTO {s}"]'))
        assert grep == "", f"TS12 un grep del sorgente cambia il progetto: {grep!r}"
        nudo = c.evento("PostToolUse", sessione="g", **bash("grep -h PROGETTO bin/contesto.py tests/*.py",
                                                            "PROGETTO finto\nPROGETTO {s}"))
        assert nudo == "", f"TS12 un grep senza numeri di riga cambia il progetto: {nudo!r}"
        cede = c.evento("PostToolUse", sessione="g", tool_name="Edit",
                        tool_input={"file_path": str(c.home / "Documents" / "ClaudeCode" / "saggio" / "a.md")},
                        tool_response={})
        assert "]0;LAVORANDO · saggio\x07" in cede, f"TS12 il testo di /inizio non risolto non cede a un file scritto: {cede!r}"
        config = c.home / ".claude"
        c.evento("UserPromptSubmit", sessione="p", prompt="fai il piano")
        piano = c.evento("PostToolUse", sessione="p", tool_name="Write",
                         tool_input={"file_path": str(config / "plans" / "piano.md")}, tool_response={})
        assert "claude-config" not in piano, f"TS12 un piano scritto rinomina la scheda: {piano!r}"
        hook_ = c.evento("PostToolUse", sessione="p", tool_name="Edit",
                         tool_input={"file_path": str(config / "hooks" / "x.py")}, tool_response={})
        assert "]0;LAVORANDO · claude-config\x07" in hook_, f"TS12 un hook modificato non è lavoro sulla config: {hook_!r}"
        sporco = c.evento("PostToolUse", sessione="q", tool_name="Write",
                          tool_input={"file_path": str(c.home / "Documents" / "ClaudeCode" / "ab\u009c\u202ecd" / "x")},
                          tool_response={})
        assert "]0;LAVORANDO · abcd\x07" in sporco, f"TS12 il titolo porta caratteri di controllo o di formato: {sporco!r}"
        progetti = c.home / "Documents" / "ClaudeCode"
        c.evento("UserPromptSubmit", sessione="f", prompt="sistema il capitolo")
        scritto = c.evento("PostToolUse", sessione="f", tool_name="Edit",
                           tool_input={"file_path": str(progetti / "romanzo" / "cap1.md")}, tool_response={})
        assert "]0;LAVORANDO · romanzo\x07" in scritto, f"TS12 senza /inizio la cartella scritta non dà il progetto: {scritto!r}"
        c.env["PROJECTS_BASE"] = "~/Progetti"
        c.evento("UserPromptSubmit", sessione="b", prompt="sistema il capitolo")
        scelta = c.evento("PostToolUse", sessione="b", tool_name="Write",
                          tool_input={"file_path": str(c.home / "Progetti" / "saggio" / "a.md")}, tool_response={})
        assert "]0;LAVORANDO · saggio\x07" in scelta, f"TS12 la cartella dei progetti scelta in /setup non conta: {scelta!r}"
    finally:
        c.chiudi()


def riga_transcript(**dati) -> str:
    return json.dumps({"timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()), **dati}) + "\n"


def avvio(id_job: str, comando: str) -> str:
    """Il comando lanciato in background e il suo risultato, come li scrive Claude Code nel transcript."""
    return (riga_transcript(type="assistant", message={"role": "assistant", "content": [
        {"type": "tool_use", "id": f"t_{id_job}", "name": "Bash", "input": {"command": comando, "run_in_background": True}}]})
            + riga_transcript(type="user", toolUseResult={"stdout": "", "backgroundTaskId": id_job}, message={
                "role": "user", "content": [{"type": "tool_result", "tool_use_id": f"t_{id_job}", "content": "running"}]}))


def fine(id_job: str) -> str:
    return riga_transcript(type="user", message={"role": "user", "content": (
        f"<task-notification>\n<task-id>{id_job}</task-id>\n<status>completed</status>\n</task-notification>")})


def test_ts13(repo: Path) -> None:
    c = Casa(repo, "TS13", {"TERM_PROGRAM": "Apple_Terminal"})
    try:
        t = c.dir / "t.jsonl"
        voce = {"transcript_path": str(t)}
        c.evento("UserPromptSubmit", prompt="/inizio romanzo", **voce)
        t.write_text(avvio("b1", "bash tests/verifica-allineamento.sh > gate.log 2>&1"), encoding="utf-8")
        fermo = c.evento("Stop", **voce)
        assert fermo == "", f"TS13 a fine turno col gate in background la scheda lascia LAVORANDO: {fermo!r}"
        attesa = c.evento("Notification", notification_type="idle_prompt", **voce)
        assert attesa == "", f"TS13 idle_prompt col gate in background cambia il titolo: {attesa!r}"
        uscita = c.evento("Notification", notification_type="permission_prompt", **voce)
        assert "]0;SBLOCCA · romanzo\x07" in uscita, f"TS13 un permesso col job in background non è SBLOCCA: {uscita!r}"
        c.evento("UserPromptSubmit", prompt="vai", **voce)
        with t.open("a", encoding="utf-8") as f:
            f.write(fine("b1") + avvio("b2", "npx vite --port 5181 --strictPort > dev.log 2>&1")
                    + avvio("b3", "python3 -m http.server 8000"))
        c.evento("Stop", **voce)
        uscita = c.evento("Notification", notification_type="idle_prompt", **voce)
        assert "]0;SBLOCCA · romanzo\x07" in uscita, \
            f"TS13 a job finito, con i soli server accesi, idle_prompt non è SBLOCCA: {uscita!r}"
    finally:
        c.chiudi()


TESTS = {"TS01": test_ts01, "TS02": test_ts02, "TS03": test_ts03, "TS04": test_ts04, "TS05": test_ts05,
         "TS06": test_ts06, "TS07": test_ts07, "TS08": test_ts08, "TS09": test_ts09, "TS10": test_ts10,
         "TS11": test_ts11, "TS12": test_ts12, "TS13": test_ts13}


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
