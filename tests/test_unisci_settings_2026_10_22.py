#!/usr/bin/env python3
"""US01-US02: l'aggiornamento unisce settings.json come JSON (22/10/2026).

Il 21/10 l'aggiornamento a v2026-10-21 è andato in conflitto su settings.json per tutte e due le
installazioni attive (telemetria: aggiorna conflitto, deriva file:settings.json): Arturo aveva
aggiunto un hook di avvio, e righe vicine erano cambiate dalla persona o da un'app.

US01 bin/unisci-settings.py, da solo: un hook aggiunto da ciascuna parte nello stesso gruppo, un
permesso della persona e uno di Arturo, un valore cambiato da una parte sola stanno insieme. Lo
stesso valore cambiato in modo diverso dalle due parti è un conflitto: esce 1 e non tocca il file.
US02 il Passo 3 di /aggiorna applica senza conflitto lo stesso caso del 21/10, con la procedura e
l'unione presi dalla versione in arrivo.

Riusa il Lab di test_aggiorna_sicuro.py. Sulla base dbb37e7 ogni controllo deve fallire col suo codice.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable, Dict

_spec = importlib.util.spec_from_file_location("aggiorna_sicuro", Path(__file__).with_name("test_aggiorna_sicuro.py"))
assert _spec and _spec.loader
_sicuro = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_sicuro)
Lab, blocco, read, baseline = _sicuro.Lab, _sicuro.blocco, _sicuro.read, _sicuro.baseline


def hook(comando: str) -> dict:
    return {"type": "command", "command": comando}


BASE = {
    "hooks": {"SessionStart": [{"hooks": [hook("bash ~/.claude/hooks/session-start.sh")]}]},
    "permissions": {"allow": ["Bash(git status:*)"]},
    "env": {"A": "1"},
}


def nostro() -> dict:
    """La persona, o un'app come iTerm2: un hook nello stesso gruppo, un permesso, un valore suo."""
    d = json.loads(json.dumps(BASE))
    d["hooks"]["SessionStart"][0]["hooks"].append(hook("bash ~/.iterm2/cc-status.sh"))
    d["permissions"]["allow"].append("Bash(npm test:*)")
    d["env"]["A"] = "mio"
    return d


def loro() -> dict:
    """Arturo: un hook nuovo dopo quello di avvio, un permesso, un evento nuovo."""
    d = json.loads(json.dumps(BASE))
    d["hooks"]["SessionStart"][0]["hooks"].append(hook("python3 ~/.claude/hooks/gws-token-health.py"))
    d["permissions"]["allow"].append("Bash(git log:*)")
    d["hooks"]["Stop"] = [{"hooks": [hook("bash ~/.claude/bin/telemetria-esito.sh")]}]
    return d


def unisci(repo: Path, cartella: Path, base: dict, n: dict, l: dict) -> tuple:
    file = {}
    for nome, dati in (("base", base), ("nostro", n), ("loro", l)):
        file[nome] = cartella / f"{nome}.json"
        file[nome].write_text(json.dumps(dati, indent=2) + "\n", encoding="utf-8")
    r = subprocess.run([sys.executable, str(repo / "bin" / "unisci-settings.py"),
                        str(file["base"]), str(file["nostro"]), str(file["loro"])],
                       capture_output=True, text=True, timeout=60)
    return r, read(file["nostro"])


def comandi(d: dict, evento: str) -> list:
    return [h["command"] for g in d["hooks"].get(evento, []) for h in g["hooks"]]


def test_us01(repo: Path) -> None:
    assert (repo / "bin" / "unisci-settings.py").exists(), "US01 manca bin/unisci-settings.py"
    with tempfile.TemporaryDirectory() as tmp:
        r, testo = unisci(repo, Path(tmp), BASE, nostro(), loro())
        assert r.returncode == 0, f"US01 l'unione non riesce: {r.stderr!r}"
        d = json.loads(testo)
        assert comandi(d, "SessionStart") == ["bash ~/.claude/hooks/session-start.sh",
                                              "python3 ~/.claude/hooks/gws-token-health.py",
                                              "bash ~/.iterm2/cc-status.sh"], f"US01 hook di avvio: {comandi(d, 'SessionStart')}"
        assert comandi(d, "Stop") == ["bash ~/.claude/bin/telemetria-esito.sh"], "US01 l'evento nuovo di Arturo manca"
        assert d["permissions"]["allow"] == ["Bash(git status:*)", "Bash(git log:*)", "Bash(npm test:*)"], \
            f"US01 permessi: {d['permissions']['allow']}"
        assert d["env"] == {"A": "mio"}, f"US01 il valore cambiato dalla persona si perde: {d['env']}"
        # Arturo toglie un permesso che la persona non ha toccato: esce.
        senza = loro()
        senza["permissions"]["allow"].remove("Bash(git status:*)")
        r, testo = unisci(repo, Path(tmp), BASE, nostro(), senza)
        assert r.returncode == 0 and "git status" not in testo, f"US01 il permesso tolto da Arturo resta: {testo}"
        # Lo stesso valore cambiato in due modi: conflitto, e il file della persona resta com'era.
        diverso = loro()
        diverso["env"]["A"] = "di arturo"
        r, testo = unisci(repo, Path(tmp), BASE, nostro(), diverso)
        assert r.returncode == 1 and json.loads(testo) == nostro(), \
            f"US01 un conflitto vero passa, o tocca il file: {r.returncode} {testo}"


def test_us02(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        lab = Lab(repo, Path(tmp), "bash")
        unione = repo / "bin" / "unisci-settings.py"
        if unione.exists():  # la versione in arrivo porta l'unione, come aggiorna-applica.sh
            shutil.copy(str(unione), str(lab.autore / "bin" / "unisci-settings.py"))
        (lab.autore / "settings.json").write_text(json.dumps(BASE, indent=2) + "\n", encoding="utf-8")
        # Ogni hook citato esiste: uno mancante è config rotta, e l'aggiornamento non parte.
        (lab.autore / "hooks" / "session-start.sh").write_text("#!/bin/bash\nexit 0\n", encoding="utf-8")
        lab.git(lab.autore, "add", "-A")
        lab.git(lab.autore, "commit", "-q", "-m", "v1: settings")
        lab.git(lab.autore, "push", "-q", "origin", "main")
        lab.git(lab.utente, "pull", "-q", "--ff-only")
        (lab.utente / "settings.json").write_text(json.dumps(nostro(), indent=2) + "\n", encoding="utf-8")
        lab.git(lab.utente, "commit", "-q", "-am", "chore: session sync")
        (lab.autore / "hooks" / "gws-token-health.py").write_text("pass\n", encoding="utf-8")
        (lab.autore / "bin" / "telemetria-esito.sh").write_text("#!/bin/bash\nexit 0\n", encoding="utf-8")
        lab.git(lab.autore, "add", "hooks/gws-token-health.py", "bin/telemetria-esito.sh")
        lab.pubblica(lab.autore, {"settings.json": lambda t: json.dumps(loro(), indent=2) + "\n"}, "v2: settings")
        testo = read(repo / "commands" / "aggiorna.md")
        lab.lancia(blocco(testo, "## Passo 1", "US02"))
        uscita = lab.lancia(blocco(testo, "## Passo 3", "US02"))
        assert "APPLICATO" in uscita and "CONFLITTO" not in uscita, f"US02 l'aggiornamento non applica: {uscita[-400:]!r}"
        d = json.loads(read(lab.utente / "settings.json"))
        assert "bash ~/.iterm2/cc-status.sh" in comandi(d, "SessionStart") \
            and "python3 ~/.claude/hooks/gws-token-health.py" in comandi(d, "SessionStart"), \
            f"US02 un hook si è perso: {comandi(d, 'SessionStart')}"
        assert lab.config_integra(), "US02 la config non è integra"


TESTS: Dict[str, Callable[[Path], None]] = {"US01": test_us01, "US02": test_us02}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.baseline_ref:
        rossi, altro = baseline(TESTS, repo)
        assert not altro and rossi == list(TESTS), \
            "baseline non discriminante: ogni controllo deve fallire col suo codice.\n" + "\n".join(altro)
        print(f"BASELINE_DISCRIMINANTE={','.join(rossi)}")
        return 0
    for test in TESTS.values():
        test(repo)
    print(f"PASS {','.join(TESTS)} controlli={len(TESTS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
