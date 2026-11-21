#!/usr/bin/env python3
"""SC01-SC08: quando la scansione dei segreti non arriva in fondo, Arturo registra la causa (21/11/2026, #5761).

In 30 giorni commit-secret-gate.py.scansione-fallita ha chiesto 27 volte con 20 sì, su 3 installazioni, e il
campo errori del riepilogo era vuoto: nessun dato diceva quale ramo della guardia parlava. Ora la guardia
scrive la causa in una riga "CAUSA:", il dispatcher la registra come evento `errore`
(commit-secret-gate.py.<causa>) e /diagnosi la legge con `--prova`. La regola della guardia non cambia:
chiede come prima, con lo stesso nome.

SC01 git non si avvia (PATH senza git): causa strumento-mancante.
SC02 git più lento di 4 secondi: causa tempo-scaduto.
SC03 indice di git rotto: causa errore.
SC04 più file nuovi del tetto, con git add e git commit insieme: causa troppi-file.
SC05 l'elenco delle cause è lo stesso nella guardia, in bin/telemetria.py e in server/logica.js; una causa
     fuori elenco cade e resta il nome della guardia; una causa non entra in `chiede`.
SC06 dal dispatcher: in coda vanno `errore` con la causa e `chiede` con scansione-fallita, e a Claude Code
     arriva solo il JSON.
SC07 invariante: senza il dispatcher di Arturo la riga CAUSA non esce, e la guardia chiede in ogni caso.
SC08 `--prova` dice ok in un repository sano e NON PARTE con la causa sull'indice rotto.

SC02 usa un git finto nel PATH, uno script bash: su Windows è saltato e dichiarato.
Sulla base e794f3e (dev prima della modifica) sono rossi tutti tranne SC07.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import salti_windows  # noqa: E402
from test_telemetria import Lab  # noqa: E402

CASI = ["SC01", "SC02", "SC03", "SC04", "SC05", "SC06", "SC07", "SC08"]
DISCRIMINANTI = [c for c in CASI if c != "SC07" and not (os.name == "nt" and c == "SC02")]
GIT_ENV = {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1", "GIT_AUTHOR_NAME": "t",
           "GIT_AUTHOR_EMAIL": "t@esempio.org", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@esempio.org"}
GIT_VERO = shutil.which("git") or "git"
ATTESE = {"strumento-mancante", "tempo-scaduto", "errore", "troppi-file"}


def _repo(cartella: Path) -> Path:
    cartella.mkdir()
    env = dict(os.environ, **GIT_ENV)
    subprocess.run([GIT_VERO, "init", "-q", str(cartella)], env=env, check=True, capture_output=True)
    (cartella / "a.txt").write_text("ciao\n", encoding="utf-8")
    subprocess.run([GIT_VERO, "-C", str(cartella), "add", "a.txt"], env=env, check=True, capture_output=True)
    return cartella


def _rotto(cartella: Path) -> Path:
    _repo(cartella)
    (cartella / ".git" / "index").write_bytes(b"DIRC questo indice non e' valido")
    return cartella


def _git_lento(cartella: Path) -> Path:
    cartella.mkdir()
    finto = cartella / "git"
    finto.write_text('#!/usr/bin/env bash\nfor a in "$@"; do\n  if [ "$a" = diff ]; then\n    exec sleep 6\n'
                     f'  fi\ndone\nexec "{GIT_VERO}" "$@"\n', encoding="utf-8")
    finto.chmod(0o755)
    return cartella


def _guardia(repo: Path, cwd: Path, comando: str = "git commit -m x", path: str | None = None,
             solo_path: bool = False, dispatcher: bool = True) -> tuple[str, str, str]:
    """(decisione, regola, causa) della guardia lanciata come la lancia il dispatcher."""
    env = dict(os.environ, PYTHONUTF8="1", ARTURO_TELEMETRIA="0", **GIT_ENV)
    env.pop("ARTURO_REGOLA", None)
    if dispatcher:
        env["ARTURO_REGOLA"] = "1"
    if path:
        env["PATH"] = path if solo_path else path + os.pathsep + env.get("PATH", "")
    p = subprocess.run([sys.executable, "-B", str(repo / "hooks" / "commit-secret-gate.py")], text=True,
                       input=json.dumps({"tool_name": "Bash", "tool_input": {"command": comando}, "cwd": str(cwd)}),
                       capture_output=True, timeout=60, env=env, encoding="utf-8")
    righe = p.stdout.strip().splitlines()
    if not righe:
        return "silent", "", ""
    decisione = json.loads(righe[0])["hookSpecificOutput"]["permissionDecision"]
    regola = next((r[len("REGOLA: "):].strip() for r in righe[1:] if r.startswith("REGOLA: ")), "")
    causa = next((r[len("CAUSA: "):].strip() for r in righe[1:] if r.startswith("CAUSA: ")), "")
    return decisione, regola, causa


def _carica(file: Path, nome: str):
    spec = importlib.util.spec_from_file_location(nome, file)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nome] = modulo  # i dataclass del modulo lo cercano qui
    spec.loader.exec_module(modulo)
    return modulo


def _sc05(repo: Path) -> str | None:
    guardia = re.search(r"^CAUSE = \((.*?)\)", (repo / "hooks" / "commit-secret-gate.py").read_text(encoding="utf-8"),
                        re.M)
    nella_guardia = set(re.findall(r'"([a-z-]+)"', guardia.group(1))) if guardia else set()
    if nella_guardia != ATTESE:
        return f"la guardia ha le cause {sorted(nella_guardia)}, attese {sorted(ATTESE)}"
    tel = _carica(repo / "bin" / "telemetria.py", "telemetria_sc05")
    nel_client = set(getattr(tel, "CAUSE", {}).get("commit-secret-gate.py", ()))
    if nel_client != ATTESE:
        return f"bin/telemetria.py ha le cause {sorted(nel_client)}"
    js = (repo / "server" / "logica.js").read_text(encoding="utf-8")
    m = re.search(r'export const CAUSE = \{\s*"commit-secret-gate\.py": \[(.*?)\]', js, re.S)
    nel_server = set(re.findall(r'"([^"]+)"', m.group(1))) if m else set()
    if nel_server != ATTESE:
        return f"server/logica.js ha le cause {sorted(nel_server)}"
    if "errore: GUARDIA_E_CAUSA" not in js:
        return "il server non accetta la causa nell'evento errore"
    g = "commit-secret-gate.py"
    prove = [("errore", f"{g}.tempo-scaduto", f"{g}.tempo-scaduto"), ("errore", g, g),
             ("errore", f"{g}.inventata", g), ("errore", f"{g}.scansione-fallita", g),
             ("chiede", f"{g}.tempo-scaduto", g), ("chiede", f"{g}.scansione-fallita", f"{g}.scansione-fallita"),
             ("errore", "block-dangerous.py.errore", "block-dangerous.py"), ("errore", "hook-di-rossi.py.errore", None)]
    for evento, valore, atteso in prove:
        uscito = tel.normalizza(evento, valore)
        if uscito != atteso:
            return f"normalizza({evento!r}, {valore!r}) dà {uscito!r}, atteso {atteso!r}"
    return None


def _sc06(repo: Path) -> str | None:
    lab = Lab(repo)
    rotto = _rotto(lab.dir / "rotto")
    r = lab.hook("bash-dispatcher.sh", json.dumps({"tool_name": "Bash", "cwd": str(rotto),
                                                    "tool_input": {"command": "git commit -m prova"},
                                                    "tool_use_id": "toolu_sc06"}))
    if '"ask"' not in r.stdout or "CAUSA" in r.stdout or "REGOLA" in r.stdout:
        return f"a Claude Code arriva altro dal JSON che chiede: {r.stdout[:160]!r}"
    try:
        json.loads(r.stdout)
    except ValueError:
        return f"l'uscita del dispatcher non è un JSON solo: {r.stdout[:160]!r}"
    coda = sorted((e["evento"], e["valore"]) for e in lab.coda())
    attesa = [("chiede", "commit-secret-gate.py.scansione-fallita"), ("errore", "commit-secret-gate.py.errore")]
    if coda != attesa:
        return f"in coda {coda}, attesi {attesa}"
    if "rotto" in json.dumps(lab.coda()):
        return "il percorso del repository esce nella telemetria"
    return None


def _sc08(repo: Path, radice: Path) -> str | None:
    def prova(cartella: Path) -> str:
        env = dict(os.environ, PYTHONUTF8="1", **GIT_ENV)
        p = subprocess.run([sys.executable, "-B", str(repo / "hooks" / "commit-secret-gate.py"), "--prova"], text=True,
                           input="", capture_output=True, timeout=60, env=env, encoding="utf-8", cwd=str(cartella))
        return p.stdout.strip()
    sano = prova(_repo(radice / "sano"))
    if sano != "scansione segreti: ok":
        return f"repository sano: {sano[:120]!r}"
    rotto = prova(_rotto(radice / "rotto-prova"))
    if not rotto.startswith("scansione segreti: NON PARTE (errore): ") or "git status" not in rotto:
        return f"indice rotto: {rotto[:160]!r}"
    return None


def prova(repo: Path) -> list[str]:
    rossi, decisioni = [], []

    def caso(codice: str, esito: tuple[str, str, str], regola: str, causa: str) -> None:
        decisioni.append((codice, esito[0]))
        if esito[1:] != (regola, causa):
            rossi.append(f"{codice} regola e causa {esito[1:]}, attese {(regola, causa)}")

    with tempfile.TemporaryDirectory() as tmp:
        radice = Path(tmp)
        vuoto = radice / "bin-vuoto"
        vuoto.mkdir()
        caso("SC01", _guardia(repo, _repo(radice / "senza-git"), path=str(vuoto), solo_path=True),
             "scansione-fallita", "strumento-mancante")

        if os.name == "nt":
            salti_windows.dichiara("SC02", "il git finto è uno script bash")
        else:
            caso("SC02", _guardia(repo, _repo(radice / "lento"), path=str(_git_lento(radice / "bin-lento"))),
                 "scansione-fallita", "tempo-scaduto")

        caso("SC03", _guardia(repo, _rotto(radice / "rotto")), "scansione-fallita", "errore")

        tanti = _repo(radice / "tanti")
        pezzo = ("riga di prova senza segreti\n" * 8000)[:200_000]
        for n in range(110):  # 22 MB: il tetto della guardia è 20
            (tanti / f"nuovo-{n:03}.txt").write_text(pezzo, encoding="utf-8")
        caso("SC04", _guardia(repo, tanti, "git add -A && git commit -m x"), "scansione-fallita", "troppi-file")

        for codice, funzione in (("SC05", lambda: _sc05(repo)), ("SC06", lambda: _sc06(repo)),
                                 ("SC08", lambda: _sc08(repo, radice))):
            try:
                motivo = funzione()
            except Exception as e:  # noqa: BLE001 - sulla base il codice nuovo manca: il caso è rosso, non rotto
                motivo = f"{type(e).__name__}: {e}"
            if motivo:
                rossi.append(f"{codice} {motivo}")

        senza = _guardia(repo, _rotto(radice / "rotto-solo"), dispatcher=False)
        decisioni.append(("SC07", senza[0]))
        if senza[1] or senza[2]:
            rossi.append(f"SC07 senza il dispatcher escono REGOLA o CAUSA: {senza}")
        elif any(d != "ask" for _, d in decisioni):
            rossi.append(f"SC07 la guardia non chiede in ogni caso: {decisioni}")
    return sorted(rossi)


def main() -> int:
    for flusso in (sys.stdout, sys.stderr):
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    a = parser.parse_args()
    rossi = prova(Path(a.repo))
    if a.baseline_ref:
        codici = [r.split()[0] for r in rossi]
        assert codici == DISCRIMINANTI, f"baseline non discriminante: rossi {codici}, attesi {DISCRIMINANTI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    print(f"causa della scansione fallita: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
