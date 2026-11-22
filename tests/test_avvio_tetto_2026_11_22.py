#!/usr/bin/env python3
"""AT01-AT06: l'hook di avvio dentro il limite di Claude Code, e il suo fetch staccato (#6370, 22/11/2026).

Su un computer Windows Claude Code annullava hooks/session-start.sh al timeout di 10 secondi in 10 avvii su 11 dal
20/11: lo stesso hook dura 4 secondi a macchina ferma e 11 sotto carico. Un hook annullato perde tutto quello
che ha stampato, e il fetch in background moriva con lui.

AT01 un passo lento non fa sforare il tetto: l'hook esce in tempo, con le righe già uscite e la riga AVVIO;
AT02 un avvio veloce esce intero, nell'ordine, e il JSON di stdin arriva al lavoro (source compact);
AT03 il fetch staccato finisce anche se l'albero dei processi di chi l'ha lanciato viene chiuso subito;
AT04 un tentativo di fetch senza esito ferma i nuovi per 30 minuti, non per 6 ore;
AT05 senza un fetch mai riuscito l'avviso dei 7 giorni conta dal primo tentativo;
AT06 deriva.py usa l'esito di controlla-config.py che l'avvio gli passa, senza rifare i git.

Invariante (verde anche sulla base): AT02.
Sulla base e57fe9f sono rossi AT01, AT03, AT04, AT05, AT06.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CASI = ["AT01", "AT02", "AT03", "AT04", "AT05", "AT06"]
DISCRIMINANTI = ["AT01", "AT03", "AT04", "AT05", "AT06"]
BASH = shutil.which("bash") or "bash"
GIT = shutil.which("git") or "git"
WINDOWS = os.name == "nt"
TOGLI = ("CLAUDE_ENV_FILE", "ARTURO_CODICE", "CLAUDE_PLUGIN_ROOT", "ARTURO_AVVIO_CORPO", "ARTURO_AVVIO_TETTO_MS",
         "ARTURO_CONFIG_CONTROLLATA", "ARTURO_CONFIG_RIGHE", "ARTURO_RESTANTE")


def scrivi(percorso: Path, testo: str) -> None:
    percorso.parent.mkdir(parents=True, exist_ok=True)
    with open(str(percorso), "w", encoding="utf-8", newline="\n") as f:  # write_text(newline=) vuole Python 3.10
        f.write(testo)


def ambiente(home: Path, **altro: str) -> dict:
    env = {k: v for k, v in os.environ.items() if k not in TOGLI}
    env.update({"HOME": str(home), "USERPROFILE": str(home), "ARTURO_TELEMETRIA": "0",
                "ARTURO_AGGIORNAMENTI": "manuali", "GIT_TERMINAL_PROMPT": "0", "ARTURO_BANCHI_AVVIO": "0",
                "PYTHONIOENCODING": "utf-8", "ARTURO_PATH_CANDIDATE": ""})
    env.update(altro)
    return env


def casa(tmp: Path, repo: Path, personale: str = "") -> Path:
    """Una HOME di prova: ~/.claude repository git con l'hook di avvio, e il fetch staccato se c'è."""
    home = tmp / "home"
    cartella = home / ".claude"
    (cartella / "session-env").mkdir(parents=True)
    for nome in ("session-start.sh", "avvio-fetch.py"):
        if (repo / "hooks" / nome).exists():
            scrivi(cartella / "hooks" / nome, (repo / "hooks" / nome).read_text(encoding="utf-8"))
    if personale:
        scrivi(cartella / "personale" / "session-start.sh", personale)
    subprocess.run([GIT, "init", "-q", str(cartella)], check=True)
    return home


def avvia(home: Path, progetto: Path, dati: dict, **env: str):
    inizio = time.monotonic()
    esito = subprocess.run([BASH, str(home / ".claude" / "hooks" / "session-start.sh")], input=json.dumps(dati),
                           cwd=progetto, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           env=ambiente(home, **env), timeout=60)
    return esito.stdout, time.monotonic() - inizio


def nuova_cartella() -> Path:
    return Path(tempfile.mkdtemp(prefix="arturo-at-"))


def butta(tmp: Path) -> None:
    # Su Windows un processo che lavora ancora nella cartella la tiene aperta: riprova per qualche secondo.
    for _ in range(20):
        shutil.rmtree(tmp, ignore_errors=True)
        if not tmp.exists():
            return
        time.sleep(0.5)


def caso_tetto(repo: Path) -> list:
    tmp = nuova_cartella()
    try:
        home = casa(tmp, repo, "sleep 6\necho PERSONALE-FINE\n")
        progetto = tmp / "progetto"
        progetto.mkdir()
        uscita, durata = avvia(home, progetto, {"source": "startup"}, ARTURO_AVVIO_TETTO_MS="2000")
        rossi = []
        if durata > 4.5:
            rossi.append(f"AT01 l'hook con un passo di 6 secondi esce dopo {durata:.1f} s, oltre il tetto di 2")
        elif "DIRECTORY:" not in uscita or "AVVIO:" not in uscita:
            rossi.append(f"AT01 mancano le righe già uscite o la riga AVVIO: {uscita[-300:]!r}")
        time.sleep(6)  # il lavoro rimasto finisce prima della pulizia
        return rossi
    finally:
        butta(tmp)


def caso_intero(repo: Path) -> list:
    tmp = nuova_cartella()
    try:
        home = casa(tmp, repo, "echo PERSONALE-FINE\n")
        progetto = tmp / "progetto"
        progetto.mkdir()
        (home / ".claude" / "session-env" / "ultimo-fetch").write_text(str(int(time.time())), encoding="utf-8")
        uscita, _ = avvia(home, progetto, {"source": "compact"})
        righe = uscita.splitlines()
        if "AVVIO:" in uscita:
            return [f"AT02 un avvio veloce viene tagliato: {uscita[-300:]!r}"]
        if not righe or righe[-1] != "PERSONALE-FINE" or "COMPACT APPENA AVVENUTO" not in uscita:
            return [f"AT02 l'avvio non esce intero e nell'ordine, o stdin non arriva: {uscita[-300:]!r}"]
        i = [n for n, r in enumerate(righe) if r.startswith("DIRECTORY:")]
        if not i or i[0] > righe.index("PERSONALE-FINE"):
            return [f"AT02 l'ordine delle righe è cambiato: {righe!r}"]
        return []
    finally:
        butta(tmp)


def git_lento(cartella: Path) -> Path:
    """Un git che aspetta 3 secondi prima di ogni comando e poi chiama quello vero."""
    cartella.mkdir(parents=True)
    if WINDOWS:
        scrivi(cartella / "git.cmd", f'@echo off\r\nping -n 4 127.0.0.1 >nul\r\n"{GIT}" %*\r\n')
    else:
        scrivi(cartella / "git", f'#!/bin/sh\nsleep 3\nexec "{GIT}" "$@"\n')
        (cartella / "git").chmod(0o755)
    return cartella


def chiudi_albero(p: subprocess.Popen) -> None:
    if WINDOWS:
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True)
    else:
        os.killpg(p.pid, signal.SIGKILL)


def caso_staccato(repo: Path) -> list:
    script = repo / "hooks" / "avvio-fetch.py"
    if not script.exists():
        return ["AT03 manca hooks/avvio-fetch.py: il fetch gira in un ( ... ) & figlio dell'hook"]
    tmp = nuova_cartella()
    try:
        sorgente = tmp / "sorgente.git"
        subprocess.run([GIT, "init", "-q", "--bare", "-b", "main", str(sorgente)], check=True)
        lavoro = tmp / "lavoro"
        subprocess.run([GIT, "init", "-q", "-b", "main", str(lavoro)], check=True)
        subprocess.run([GIT, "-C", str(lavoro), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q",
                        "--allow-empty", "-m", "uno"], check=True)
        subprocess.run([GIT, "-C", str(lavoro), "push", "-q", str(sorgente), "main"], check=True)
        radice = tmp / "claude"
        subprocess.run([GIT, "clone", "-q", str(sorgente), str(radice)], check=True)
        riuscito = tmp / "riuscito"
        fatto = tmp / "stacca-fatto"
        lento = git_lento(tmp / "finto")
        env = {**os.environ, "PATH": str(lento) + os.pathsep + os.environ.get("PATH", "")}
        comando = (f'"{sys.executable}" "{script}" stacca "{radice}" 123 "{riuscito}"; '
                   f'echo fatto > "{fatto}"; sleep 30')
        opzioni = {} if WINDOWS else {"start_new_session": True}
        padre = subprocess.Popen([BASH, "-c", comando.replace("\\", "/")], env=env, stdin=subprocess.DEVNULL,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **opzioni)
        time.sleep(3)
        staccato_subito = fatto.exists()
        chiudi_albero(padre)
        padre.wait(timeout=10)
        fine = time.monotonic() + 30
        while time.monotonic() < fine and not riuscito.exists():
            time.sleep(0.5)
        if not staccato_subito:
            return ["AT03 stacca non è uscito entro 3 secondi: aspetta il fetch invece di staccarlo"]
        if not riuscito.exists() or riuscito.read_text(encoding="utf-8") != "123":
            return ["AT03 il fetch è morto con l'albero dei processi di chi l'ha lanciato"]
        return []
    finally:
        butta(tmp)


def caso_ritenta(repo: Path) -> list:
    rossi = []
    for minuti, deve in ((40, True), (10, False)):
        tmp = nuova_cartella()
        try:
            home = casa(tmp, repo)
            progetto = tmp / "progetto"
            progetto.mkdir()
            marcatore = home / ".claude" / "session-env" / "ultimo-fetch"
            prima = int(time.time()) - minuti * 60
            marcatore.write_text(str(prima), encoding="utf-8")
            avvia(home, progetto, {"source": "startup"})
            ritentato = marcatore.read_text(encoding="utf-8").strip() != str(prima)
            if ritentato != deve:
                rossi.append(f"AT04 con l'ultimo tentativo senza esito {minuti} minuti fa il fetch "
                             f"{'non riparte' if deve else 'riparte'}")
            time.sleep(1)
        finally:
            butta(tmp)
    return rossi[:1]


def caso_sette_giorni(repo: Path) -> list:
    rossi = []
    for riuscito_fa, deve in ((None, True), (86400, False)):
        tmp = nuova_cartella()
        try:
            home = casa(tmp, repo)
            progetto = tmp / "progetto"
            progetto.mkdir()
            env_dir = home / ".claude" / "session-env"
            adesso = int(time.time())
            (env_dir / "ultimo-fetch").write_text(str(adesso), encoding="utf-8")
            (env_dir / "primo-fetch-tentato").write_text(str(adesso - 8 * 86400), encoding="utf-8")
            if riuscito_fa:
                (env_dir / "ultimo-fetch-riuscito").write_text(str(adesso - riuscito_fa), encoding="utf-8")
            uscita, _ = avvia(home, progetto, {"source": "startup"})
            avvisa = "7 giorni" in uscita
            if avvisa != deve:
                rossi.append("AT05 " + ("senza un fetch mai riuscito l'avviso dei 7 giorni tace" if deve
                                        else "l'avviso dei 7 giorni esce con un fetch riuscito ieri"))
        finally:
            butta(tmp)
    return rossi[:1]


def caso_deriva(repo: Path) -> list:
    codice = ("import sys; from pathlib import Path; sys.path.insert(0, sys.argv[1]); "
              "import importlib.util as u; s = u.spec_from_file_location('d', sys.argv[1] + '/deriva.py'); "
              "m = u.module_from_spec(s); s.loader.exec_module(m); print(m.categorie_config(Path(sys.argv[2])))")
    tmp = nuova_cartella()
    try:
        env = {k: v for k, v in os.environ.items() if k not in TOGLI}
        env.update({"ARTURO_CONFIG_CONTROLLATA": "1", "PYTHONIOENCODING": "utf-8",
                    "ARTURO_CONFIG_RIGHE": "CONFIG ROTTA: settings.json non è JSON valido (x): le guardie sono spente"})
        esito = subprocess.run([sys.executable, "-c", codice, str(repo / "hooks"), str(tmp / "manca")],
                               capture_output=True, text=True, encoding="utf-8", env=env, timeout=60)
        if "rotta-settings" not in esito.stdout:
            return [f"AT06 deriva.py non usa l'esito passato dall'avvio: {esito.stdout.strip()!r} {esito.stderr[-200:]!r}"]
        return []
    finally:
        butta(tmp)


def prova(repo: Path) -> list:
    rossi = []
    for caso in (caso_tetto, caso_intero, caso_staccato, caso_ritenta, caso_sette_giorni, caso_deriva):
        rossi += caso(repo)
    return rossi


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    argomenti = parser.parse_args()
    rossi = prova(Path(argomenti.repo))
    if argomenti.baseline_ref:
        codici = [r.split()[0] for r in rossi]
        assert codici == DISCRIMINANTI, f"baseline non discriminante: rossi {codici}, attesi {DISCRIMINANTI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    print(f"avvio con tetto: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
