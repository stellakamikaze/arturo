#!/usr/bin/env python3
"""
Session-start health check per i token OAuth di gws.

Trova da solo gli account: ogni cartella ~/.config/gws o ~/.config/gws-<nome> con una
credenziale dentro. Gli account che devono esserci in ogni caso (e vanno segnalati se
mancano) si elencano, uno per riga, in ~/.claude/arturo/gws-account.local (prima hooks/), fuori da git: così il file
è lo stesso nella config dell'autore e in Arturo (20/10/2026). Senza gws e senza cartelle tace.

L'hook non lancia mai `gws` dentro l'avvio: mostra l'ultimo esito in cache e, se la cache ha più di
6 ore o un login è più recente, lancia un processo staccato (`--refresh`) che rifà i check. Il refresh
ha un lock di 3 minuti, così due sessioni non ne lanciano due, e 30 s di limite per account: al limite
chiude l'intero albero dei processi di gws (su Windows cmd, node e gws.exe) e scrive "non verificato".
Dopo un login nuovo, o senza cache, l'esito arriva alla sessione successiva.

Marcatori: "!" guasto (token invalido, refresh token assente, credenziali in chiaro), "-" account
mancante, "?" non verificato (limite superato o check fallito, senza la riga fix). Non blocca mai
l'avvio sessione: exit 0 anche in caso di errori interni.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from concurrent.futures import TimeoutError as AttesaScaduta  # prima di python 3.11 non è il TimeoutError di serie
from pathlib import Path
sys.path.append(str(Path(os.path.realpath(__file__)).parent))
from radici import file_locale, radice_orsa  # noqa: E402

CONFIG_DIR = Path.home() / ".config"
GWS_BIN = shutil.which("gws")
ATTESI_FILE = file_locale("gws-account.local", radice_orsa() / "hooks" / "gws-account.local")


def _account():
    """{nome: cartella} degli account trovati, più quelli attesi da gws-account.local."""
    trovati = {}
    try:
        for d in CONFIG_DIR.iterdir():
            if (d.is_dir() and re.fullmatch(r"gws(-[a-z0-9]+)?", d.name)
                    and ((d / "credentials.enc").exists() or (d / "credentials.json").exists())):
                trovati[d.name] = d
    except OSError:
        pass
    try:
        for riga in ATTESI_FILE.read_text(encoding="utf-8").splitlines():
            nome = riga.split("#", 1)[0].strip()
            # "gws-lavoro|gws-ufficio": vale la prima che esiste (nomi diversi fra le macchine).
            scelte = [n.strip() for n in nome.split("|") if re.fullmatch(r"gws(-[a-z0-9]+)?", n.strip())]
            if scelte and not any(n in trovati for n in scelte):
                trovati[scelte[0]] = CONFIG_DIR / scelte[0]
    except OSError:
        pass
    return trovati


EXPECTED_ACCOUNTS = _account()

# Il check vero gira in background (--refresh), fuori dal timeout di 12 s dell'hook: su Windows
# un solo `gws auth status` impiega 5-9 s, e con 8 s di limite ogni account risultava in timeout,
# nascondendo il token davvero scaduto di un account (verifica su un PC Windows, 31/10/2026).
GWS_TIMEOUT_SEC = int(os.environ.get("ARTURO_GWS_TIMEOUT_SEC") or 30)  # la variabile serve ai banchi


def _chiudi_albero(proc: subprocess.Popen) -> None:
    """Chiude gws e i suoi figli. Su Windows lo shim npm è cmd -> node -> gws.exe, e kill() chiude solo
    cmd: gli altri tengono aperte le pipe e communicate() resta appeso (1/11/2026, F31)."""
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True, timeout=10,
                           check=False)
        else:
            import signal
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except (OSError, subprocess.SubprocessError):
        pass
    try:
        proc.kill()
    except OSError:
        pass


def check_account(alias: str, config_path: Path) -> tuple[str, str, str]:
    """Return (alias, status, detail) dove status è 'ok' | 'warn' | 'missing' | 'unverified'."""
    if not config_path.exists():
        return alias, "missing", f"config dir non esistente ({config_path})"

    has_enc = (config_path / "credentials.enc").exists()
    has_plain = (config_path / "credentials.json").exists()
    if not has_enc and not has_plain:
        return alias, "missing", "nessuna credenziale (mai fatto login)"

    if not GWS_BIN:
        return alias, "warn", "comando gws non trovato nel PATH"

    env = os.environ.copy()
    env["GOOGLE_WORKSPACE_CLI_CONFIG_DIR"] = str(config_path)

    kw = {"creationflags": 0x00000200} if os.name == "nt" else {"start_new_session": True}  # gruppo nuovo
    try:
        proc = subprocess.Popen([GWS_BIN, "auth", "status"], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", env=env, **kw)
    except (FileNotFoundError, OSError):
        return alias, "warn", f"gws binary non eseguibile ({GWS_BIN})"
    try:
        stdout, _ = proc.communicate(timeout=GWS_TIMEOUT_SEC)
    except subprocess.TimeoutExpired:
        # Un timeout non dice che il token è guasto: si dichiara "non verificato".
        _chiudi_albero(proc)
        try:
            proc.communicate(timeout=5)
        except (subprocess.TimeoutExpired, OSError, ValueError):
            pass
        return alias, "unverified", f"non verificato (auth status oltre {GWS_TIMEOUT_SEC}s)"

    if proc.returncode != 0:
        return alias, "warn", f"gws auth status exit {proc.returncode}"

    # gws stampa un banner su stderr/stdout prima del JSON
    stdout = stdout or ""
    brace_idx = stdout.find("{")
    if brace_idx < 0:
        return alias, "warn", "output non contiene JSON"
    try:
        data = json.loads(stdout[brace_idx:])
    except json.JSONDecodeError:
        return alias, "warn", "output non parsabile"

    if not data.get("has_refresh_token"):
        return alias, "warn", "manca refresh token - rifai login"

    if not data.get("token_valid"):
        user = data.get("user")
        per = f" per {user}" if user else ""  # senza utente nel JSON l'avviso diceva "per ?" (#4424)
        return alias, "warn", f"token invalido{per} - rifai login"

    if data.get("plain_credentials_exists"):
        return alias, "warn", "credentials.json in chiaro - rimuovi"

    return alias, "ok", data.get("user", "?")


CACHE_FILE = radice_orsa() / "session-env" / "gws-health.cache"
CACHE_TTL_SEC = 6 * 3600


LOCK_FILE = CACHE_FILE.with_suffix(".lock")
LOCK_TTL_SEC = 180  # un refresh in corso da meno di 3 minuti non se ne lancia un altro


def run_checks() -> str:
    """Esegue i check (fino a GWS_TIMEOUT_SEC per account, in parallelo) e restituisce l'avviso."""
    issues = []
    pool = ThreadPoolExecutor(max_workers=len(EXPECTED_ACCOUNTS))
    futures = {
        pool.submit(check_account, alias, path): alias
        for alias, path in EXPECTED_ACCOUNTS.items()
    }
    finiti = set()
    try:
        # Seconda rete: un check che non torna entro il limite vale "non verificato" (1/11/2026, F31).
        for future in as_completed(futures, timeout=GWS_TIMEOUT_SEC + 15):
            finiti.add(future)
            try:
                alias, status, detail = future.result()
            except Exception as exc:
                alias = futures[future]
                status, detail = "unverified", f"check fallito: {exc}"
            if status != "ok":
                issues.append((alias, status, detail))
    except AttesaScaduta:
        for future, alias in futures.items():
            if future not in finiti:
                issues.append((alias, "unverified", "non verificato (il check non è tornato)"))
    # Python 3.8 non ha cancel_futures (arriva col 3.9): i check in coda si annullano a mano (#4434).
    for future in futures:
        future.cancel()
    pool.shutdown(wait=False)
    if not issues:
        return ""
    issues.sort(key=lambda x: x[0])
    lines = ["GWS TOKEN HEALTH:"]
    for alias, status, detail in issues:
        marker = {"warn": "!", "missing": "-", "unverified": "?"}.get(status, "!")
        lines.append(f"  {marker} {alias}: {detail}")
    # Una riga fix per ogni account guasto, con la sua cartella vera al posto di <path> (#4424).
    for alias, status, _ in issues:
        if status in ("warn", "missing"):
            cartella = EXPECTED_ACCOUNTS.get(alias, CONFIG_DIR / alias)
            lines.append(f"  fix: GOOGLE_WORKSPACE_CLI_CONFIG_DIR={cartella} gws auth login "
                         "-s drive,docs,sheets,gmail,calendar,tasks")
    return "\n".join(lines) + "\n"


def refresh() -> int:
    """Modo --refresh: gira staccato dalla sessione, scrive la cache e libera il lock."""
    try:
        out = run_checks()
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = CACHE_FILE.with_suffix(".tmp")
        tmp.write_text(out, encoding="utf-8")
        os.replace(tmp, CACHE_FILE)
    finally:
        try:
            LOCK_FILE.unlink()
        except OSError:
            pass
    return 0


def lancia_refresh() -> None:
    """Lancia --refresh in un processo staccato, se non ce n'è già uno recente."""
    import time
    try:
        if LOCK_FILE.exists() and time.time() - LOCK_FILE.stat().st_mtime < LOCK_TTL_SEC:
            return
        LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
        LOCK_FILE.write_text(str(os.getpid()), encoding="utf-8")
    except OSError:
        return
    kw = dict(stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True)
    if os.name == "nt":
        kw["creationflags"] = 0x08000000 | 0x00000200  # NO_WINDOW | NEW_GROUP: con DETACHED, NO_WINDOW è ignorato e i figli aprono finestre
    else:
        kw["start_new_session"] = True
    subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--refresh"], **kw)


def main() -> int:
    # I check gws girano al massimo ogni 6 h e mai dentro l'hook: se la cache è scaduta, parte un
    # refresh in background e la sessione mostra l'ultimo esito noto (vuoto = tutto ok).
    import time
    if not EXPECTED_ACCOUNTS:
        return 0
    if "--refresh" in sys.argv:
        return refresh()
    fresca = False
    cached = ""
    try:
        # Un login rifatto dopo l'ultimo check invalida la cache (16/9/2026: avviso stale per ore).
        creds_mtime = max((p.stat().st_mtime for d in EXPECTED_ACCOUNTS.values()
                           for p in (d / "credentials.enc", d / "credentials.json") if p.exists()), default=0)
        if CACHE_FILE.exists():
            eta = time.time() - CACHE_FILE.stat().st_mtime
            valida = CACHE_FILE.stat().st_mtime > creds_mtime
            fresca = valida and eta < CACHE_TTL_SEC
            if valida:
                cached = CACHE_FILE.read_text(encoding="utf-8")
    except Exception:
        pass
    if cached.strip():
        sys.stdout.write(cached)
    if not fresca:
        lancia_refresh()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # Fail-safe: non bloccare mai la sessione
        sys.exit(0)
