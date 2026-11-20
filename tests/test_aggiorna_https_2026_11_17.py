#!/usr/bin/env python3
"""AH01-AH07: /arturo:aggiorna passa dal classificatore e ripiega da solo su HTTPS (17/11/2026, #5880).

Il 13/11 sul MacBook la chiave SSH non entrava su GitHub: Claude Code scaricava il catalogo via HTTPS da solo,
ma `claude plugin install` e `update` usano git@github.com e fallivano (riprodotto il 17/11 con Claude Code
2.1.317, un ssh finto e una config isolata). Il 10/11 la persona ha scritto solo /arturo:aggiorna e il
classificatore della modalità auto ha negato l'installazione come "Self-Modification" (riprodotto il 17/11 con
claude -p: "Destructive or Unwanted Actions"; con la regola nuova passa).

AH01 install che fallisce su SSH si riprova una volta, con GitHub via HTTPS per quel solo processo, e riesce;
AH02 un errore che non è di SSH non si riprova;
AH03 un comando riuscito al primo colpo parte una volta sola e senza voci GIT_CONFIG;
AH04 le voci GIT_CONFIG_* che l'ambiente ha già restano, e le nuove vengono dopo;
AH05 con gh nel PATH git chiede le credenziali di github.com a gh; senza gh nessun helper;
AH06 la copia in ~/.claude (scarica) ripete il fetch via HTTPS quando quello via SSH fallisce;
AH07 la regola autoMode sull'aggiornatore c'è in settings.json, quindi anche nel frammento del plugin, e dice
     cosa non copre.

Niente rete, niente CLI vera: la CLI finta registra argomenti e ambiente. AH02 e AH03 sono verdi anche sulla
base 8e287e4: sorvegliano che il ripiego non si allarghi. --avvelena: ogni copia rotta fa rosso il caso suo.
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

CASI = ["AH01", "AH02", "AH03", "AH04", "AH05", "AH06", "AH07"]
DISCRIMINANTI = ["AH01", "AH04", "AH05", "AH06", "AH07"]
REGOLA = "Arturo's own updater, unmodified"

# FINTO_MODO: ssh = fallisce come GitHub senza chiave, salvo con git@github.com riscritto in HTTPS;
# altro = fallisce per un motivo che non è SSH; ok = riesce.
FINTO = r"""
import json, os, sys
voci = {}
for i in range(int(os.environ.get("GIT_CONFIG_COUNT") or 0)):
    voci.setdefault(os.environ.get(f"GIT_CONFIG_KEY_{i}", ""), []).append(os.environ.get(f"GIT_CONFIG_VALUE_{i}", ""))
with open(os.environ["FINTO_LOG"], "a", encoding="utf-8") as log:
    log.write(json.dumps({"argv": sys.argv[1:], "voci": voci, "chiavi": [os.environ.get(f"GIT_CONFIG_KEY_{i}")
              for i in range(int(os.environ.get("GIT_CONFIG_COUNT") or 0))]}) + "\n")
modo = os.environ.get("FINTO_MODO", "ok")
if modo == "ssh" and "git@github.com:" not in voci.get("url.https://github.com/.insteadOf", []):
    sys.stderr.write("git@github.com: Permission denied (publickey).\nfatal: Could not read from remote repository.\n\n"
                     "Please make sure you have the correct access rights\nand the repository exists.\n")
    sys.exit(1)
if modo == "altro":
    sys.stderr.write('Plugin "arturo@arturo" not found in any configured marketplace\n')
    sys.exit(1)
print("Successfully installed plugin: arturo@arturo")
"""


def carica(repo: Path):
    spec = importlib.util.spec_from_file_location("aggiornamenti_ah", str(repo / "bin" / "aggiornamenti.py"))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def cli_finta(cartella: Path) -> Path:
    if os.name == "nt":
        (cartella / "claude-finto.py").write_text(FINTO, encoding="utf-8")
        finto = cartella / "claude-finto.cmd"
        finto.write_bytes(f'@"{sys.executable}" "%~dp0claude-finto.py" %*\r\n'.encode("utf-8"))
        return finto
    finto = cartella / "claude-finto"
    finto.write_text(f"#!{sys.executable}\n" + FINTO, encoding="utf-8")
    finto.chmod(0o755)
    return finto


class Ambiente:
    """Imposta e rimette l'ambiente del processo: _claude e env_https leggono os.environ."""

    def __init__(self, **voci):
        self.voci, self.prima = voci, {}

    def __enter__(self):
        for chiave, valore in self.voci.items():
            self.prima[chiave] = os.environ.get(chiave)
            if valore is None:
                os.environ.pop(chiave, None)
            else:
                os.environ[chiave] = valore
        return self

    def __exit__(self, *_):
        for chiave, valore in self.prima.items():
            if valore is None:
                os.environ.pop(chiave, None)
            else:
                os.environ[chiave] = valore


def chiamate(log: Path) -> list:
    if not log.exists():
        return []
    return [json.loads(r) for r in log.read_text(encoding="utf-8").splitlines() if r.strip()]


def senza_gh(base: Path) -> str:
    """Un PATH senza gh: una cartella vuota, così shutil.which("gh") non lo trova."""
    vuota = base / "senza-gh"
    vuota.mkdir(exist_ok=True)
    return str(vuota)


def prova(repo: Path, solo: str = None) -> list:
    rossi = []
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        finto = cli_finta(base)
        try:
            agg = carica(repo)
        except Exception as errore:  # noqa: BLE001 - una copia che non si carica fa rosso tutto
            return [f"{c} il modulo non si carica: {errore}" for c in CASI if not solo or c == solo]

        def lancia(caso: str, modo: str, *argomenti, **env) -> list:
            log = base / f"{caso}.log"
            voci = dict(ARTURO_CLAUDE=str(finto), FINTO_LOG=str(log), FINTO_MODO=modo, GIT_CONFIG_COUNT=None,
                        PATH=senza_gh(base))
            voci.update(env)
            with Ambiente(**voci):
                esito = agg._claude(*argomenti, timeout=60)
            return [esito, chiamate(log)]

        def caso(codice: str, funzione) -> None:
            if solo and codice != solo:
                return
            try:
                motivo = funzione()
            except Exception as errore:  # noqa: BLE001 - un'eccezione è un rosso col suo motivo
                motivo = f"eccezione {type(errore).__name__}: {errore}"
            if motivo:
                rossi.append(f"{codice} {motivo}")

        def ah01():
            esito, fatte = lancia("AH01", "ssh", "install", "arturo@arturo")
            if esito.returncode != 0 or len(fatte) != 2:
                return f"install senza chiave SSH: rc {esito.returncode}, {len(fatte)} chiamate (attese 2, la seconda riesce)"
            riscritti = fatte[1]["voci"].get("url.https://github.com/.insteadOf", [])
            if sorted(riscritti) != ["git@github.com:", "ssh://git@github.com/"] or fatte[0]["voci"]:
                return f"la seconda chiamata non riscrive le due forme SSH di GitHub: {fatte[1]['voci']}"
            return ""

        def ah02():
            esito, fatte = lancia("AH02", "altro", "install", "arturo@arturo")
            return "" if esito.returncode == 1 and len(fatte) == 1 else \
                f"un errore che non è SSH si riprova: rc {esito.returncode}, {len(fatte)} chiamate"

        def ah03():
            esito, fatte = lancia("AH03", "ok", "update", "arturo@arturo")
            return "" if esito.returncode == 0 and len(fatte) == 1 and not fatte[0]["voci"] else \
                f"un update riuscito: rc {esito.returncode}, chiamate {fatte}"

        def ah04():
            with Ambiente(GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0="core.mia", GIT_CONFIG_VALUE_0="sì", PATH=senza_gh(base)):
                env = agg.env_https()
            chiavi = [env.get(f"GIT_CONFIG_KEY_{i}") for i in range(int(env["GIT_CONFIG_COUNT"]))]
            if chiavi[:1] != ["core.mia"] or env.get("GIT_CONFIG_VALUE_0") != "sì" or len(chiavi) != 3:
                return f"le voci GIT_CONFIG di prima non restano in testa: {chiavi}"
            return ""

        def ah05():
            cartella = base / "con-gh"
            cartella.mkdir(exist_ok=True)
            gh = cartella / ("gh.exe" if os.name == "nt" else "gh")
            gh.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            gh.chmod(0o755)
            with Ambiente(GIT_CONFIG_COUNT=None, PATH=str(cartella)):
                con = agg.env_https()
            with Ambiente(GIT_CONFIG_COUNT=None, PATH=senza_gh(base)):
                senza = agg.env_https()
            helper = [con[f"GIT_CONFIG_VALUE_{i}"] for i in range(int(con["GIT_CONFIG_COUNT"]))
                      if con[f"GIT_CONFIG_KEY_{i}"] == "credential.https://github.com.helper"]
            if helper[:1] != [""] or len(helper) != 2 or "auth git-credential" not in helper[1] or "\\" in helper[1]:
                return f"con gh l'helper di github.com non è gh: {helper}"
            if any("credential" in str(senza.get(f"GIT_CONFIG_KEY_{i}")) for i in range(int(senza["GIT_CONFIG_COUNT"]))):
                return "senza gh compare comunque un helper delle credenziali"
            return ""

        def ah06():
            fatte = []

            def git_finto(r, *argomenti, timeout=30, https=False):
                fatte.append((argomenti[:1], https))
                if argomenti[:1] == ("fetch",) and not https:
                    return subprocess.CompletedProcess(argomenti, 128, "", "git@github.com: Permission denied (publickey).")
                return subprocess.CompletedProcess(argomenti, 0, "", "")
            vero = agg.git
            agg.git = git_finto
            try:
                agg.scarica(base, "origin")
            finally:
                agg.git = vero
            fetch = [h for a, h in fatte if a == ("fetch",)]
            return "" if fetch == [False, True] else f"scarica non ripete il fetch via HTTPS: {fetch}"

        def ah07():
            settings = json.loads((repo / "settings.json").read_text(encoding="utf-8"))
            regole = [r for r in (settings.get("autoMode") or {}).get("allow", []) if r.startswith(REGOLA)]
            if len(regole) != 1:
                return "manca la regola autoMode.allow sull'aggiornatore di Arturo"
            regola = regole[0]
            for parola in ("/arturo:aggiorna", "aggiornamenti.py", "~/.claude/plugins/cache/arturo/arturo/",
                           "NOT covered", "editing aggiornamenti.py", "POSSIBILE COMPROMISSIONE"):
                if parola not in regola:
                    return f"la regola sull'aggiornatore non dice {parola!r}"
            spec = importlib.util.spec_from_file_location("impacchetta_ah", str(repo / "bin" / "impacchetta.py"))
            imp = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(imp)
            if regola not in imp.impostazioni(settings).get("autoMode", {}).get("allow", []):
                return "la regola non arriva nel frammento del plugin (impostazioni/arturo.json)"
            return ""

        for codice, funzione in zip(CASI, (ah01, ah02, ah03, ah04, ah05, ah06, ah07)):
            caso(codice, funzione)
    return rossi


VELENI = [
    ("AH01", "bin/aggiornamenti.py", 'if argomenti[:1] in (("install",), ("update",), ("marketplace",)) and errore_ssh(esito):',
     'if argomenti[:1] in (("marketplace",),) and errore_ssh(esito):'),
    ("AH02", "bin/aggiornamenti.py", "return esito.returncode != 0 and any(segno in testo for segno in SEGNI_SSH)",
     "return esito.returncode != 0"),
    ("AH04", "bin/aggiornamenti.py", 'n = max(0, int(env.get("GIT_CONFIG_COUNT") or 0))', "n = 0"),
    ("AH05", "bin/aggiornamenti.py", '    gh = shutil.which("gh")\n    if gh:', '    gh = shutil.which("gh")\n    if False:'),
    ("AH06", "bin/aggiornamenti.py", '        git(r, "fetch", "--quiet", "--tags", src, "main", timeout=90, https=True)\n',
     "        pass\n"),
    ("AH07", "settings.json", '"Arturo\'s own updater, unmodified', '"Arturo updater'),
]


def avvelena(repo: Path, solo: str = None) -> int:
    esiti = []
    veleni = [v for v in VELENI if not solo or v[0] == solo]
    for caso, rel, giusto, rotto in veleni:
        with tempfile.TemporaryDirectory() as tmp:
            copia = Path(tmp) / "repo"
            shutil.copytree(repo, copia, ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules", "tests"))
            testo = (copia / rel).read_text(encoding="utf-8")
            assert testo.count(giusto) == 1, f"veleno {caso}: il testo da rompere non c'è più in {rel}"
            with open(copia / rel, "w", encoding="utf-8", newline="\n") as uscita:
                uscita.write(testo.replace(giusto, rotto))
            rossi = prova(copia, solo=caso)
            if not rossi:
                print(f"VELENO {caso} NON ATTACCA: {rotto[:60]!r}")
                return 1
            print(f"VELENO {caso} ROSSO: {rossi[0][:140]}")
            esiti.append(caso)
    print(f"VELENI_ROSSI={','.join(esiti)} veleni={len(veleni)}")
    return 0 if len(esiti) == len(veleni) else 1


def main() -> int:
    for flusso in (sys.stdout, sys.stderr):
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    parser.add_argument("--avvelena", action="store_true")
    parser.add_argument("--solo")
    argomenti = parser.parse_args()
    if argomenti.avvelena:
        return avvelena(Path(argomenti.repo), argomenti.solo)
    rossi = prova(Path(argomenti.repo), argomenti.solo)
    if argomenti.baseline_ref:
        codici = sorted({r.split()[0] for r in rossi})
        assert codici == DISCRIMINANTI, f"baseline non discriminante: rossi {codici}, attesi {DISCRIMINANTI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    totale = 1 if argomenti.solo else len(CASI)
    print(f"aggiorna via HTTPS: {totale - len({r.split()[0] for r in rossi})}/{totale} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
