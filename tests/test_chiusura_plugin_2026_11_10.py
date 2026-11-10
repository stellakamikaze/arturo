#!/usr/bin/env python3
"""PC01-PC13: col plugin un rilascio firmato si installa da solo alla chiusura della sessione (10/11/2026).

Dal 6/11/2026 Arturo è un plugin di Claude Code, e da allora un rilascio nuovo arrivava solo con /aggiorna:
hooks/session-end.sh lanciava ~/.claude/bin/aggiornamenti.py, che col plugin non c'è, e `applica` col plugin non
faceva niente. Ora la chiusura lancia la copia accanto all'hook, e `applica` passa dalla strada di /aggiorna
(cmd_plugin: tag firmato, sha del catalogo, MANIFEST).

PC01 controlla, con un rilascio nuovo, scrive lo stato "pronto"; con gli aggiornamenti a mano scrive "manuale";
PC02 l'avvio dice che la versione nuova si installa da sola alla chiusura;
PC03 la chiusura vera (session-end.sh della copia installata) installa il rilascio firmato: sha nuovo, voce nuova
     in settings.json, e l'avvio dopo lo dice una volta sola;
PC04 un tag firmato da un'altra chiave non si installa: lo stato dice la compromissione, l'avvio la dice, e il
     controllo dell'ora dopo non la cancella;
PC05 una firma che questo computer non sa verificare non si installa, e l'avvio dice di aggiornare git e OpenSSH;
PC06 un rilascio che non si scarica lascia l'esito: l'avvio dice "non è partito", non "si installa da sola";
PC07 con gli aggiornamenti a mano la chiusura non installa niente; tolta la scelta, installa;
PC08 un /clear non installa niente; una chiusura vera sì;
PC09 un lucchetto fresco ferma la chiusura e /aggiorna ("AGGIORNAMENTO IN CORSO"); uno vecchio no;
PC10 con altre sessioni aperte aspetta, poi installa lo stesso: mai un rinvio;
PC11 senza `claude` nel PATH la chiusura trova la CLI in ~/.local/bin;
PC12 una sessione rimasta sulla copia di prima dice "parte alla prossima apertura", e l'esito resta da dire;
PC13 un checkout di sviluppo (con .git) alla chiusura non lancia niente; la copia del plugin sì.

Rilasci, catalogo, chiavi e CLI finta sono quelli di test_fiducia_2026_11_05.py: niente rete, niente CLI vera.
Sulla base 62786fd sono tutti rossi. --avvelena: ogni copia rotta fa rosso il caso suo.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

CASI = ["PC01", "PC02", "PC03", "PC04", "PC05", "PC06", "PC07", "PC08", "PC09", "PC10", "PC11", "PC12", "PC13"]
DISCRIMINANTI = list(CASI)
BASH = shutil.which("bash") or "bash"

_spec = importlib.util.spec_from_file_location("fd", str(Path(__file__).resolve().parent / "test_fiducia_2026_11_05.py"))
fd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fd)

# La CLI finta di FD12, con una spia: il file FINTO_SPIA nasce solo se `plugin update` parte.
FINTO = fd.CLAUDE_FINTO + '    open(os.environ["FINTO_SPIA"], "w").close()\n'


def leggi(f: Path) -> dict:
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


class Scena:
    """Una 0.3.0 installata come plugin, un rilascio 0.4.0 nel catalogo, un'Orsa e una casa vuote."""

    def __init__(self, repo: Path, base: Path, chiavi: dict, firma: str = "rilasci", pubblica: bool = True):
        base.mkdir(parents=True)
        self.repo, self.base = repo, base
        privata, firmatari = chiavi["rilasci"]
        self.r = fd.Rilasci(repo, base, chiavi)
        self.r.rilascio("0.3.0", "rilasci")
        self.prima = fd.copia_plugin(repo, base / "cache" / "0.3.0", "0.3.0", firmatari, privata)
        # Senza `pubblica` il catalogo indica un tag che nel repository dei rilasci non c'è: come senza rete.
        self.sha = self.r.rilascio("0.4.0", firma) if pubblica else "b" * 40
        self.r.indica("plugin-v0.4.0", self.sha)
        self.nuova = fd.copia_plugin(repo, base / "cache" / "0.4.0", "0.4.0", firmatari, privata,
                                     frammento={"permissions": {"deny": [fd.DENY_NUOVA]}})
        self.orsa = self.r.orsa
        (self.orsa / "plugins").mkdir()
        (self.orsa / "plugins" / "known_marketplaces.json").write_text(
            json.dumps({"arturo": {"installLocation": str(self.r.catalogo)}}), encoding="utf-8")
        (self.orsa / "plugins" / "installed_plugins.json").write_text(json.dumps({"plugins": {"arturo@arturo": [
            {"scope": "user", "installPath": str(self.prima), "version": "0.3.0", "gitCommitSha": "a" * 40}]}}),
            encoding="utf-8")
        (self.orsa / "settings.json").write_text(json.dumps({"model": "mio", "permissions": {"deny": []}}),
                                                 encoding="utf-8")
        (self.orsa / "data").mkdir()
        (self.orsa / "data" / "arturo-impostazioni.lock").write_text(json.dumps({"versione": "0.3.0", "frammento": {
            "permissions": {"deny": []}}}), encoding="utf-8")
        fd.modulo_fiducia(repo).fissa_ancora(self.prima, self.orsa)
        self.casa = base / "casa"
        self.casa.mkdir()
        self.spia = base / "update-partito"
        self.finto = fd.cli_finta(base, FINTO)
        installa = {"path": str(self.nuova), "version": "0.4.0", "sha": self.sha}
        self.env = dict(self.r.env, HOME=str(self.casa), USERPROFILE=str(self.casa), ARTURO_RADICE=str(self.orsa),
                        ARTURO_CLAUDE=str(self.finto), FINTO_INSTALLA=json.dumps(installa), FINTO_SPIA=str(self.spia),
                        ARTURO_ALTRE_SESSIONI="0", ARTURO_ATTESA_MAX="0")
        self.env.pop("ARTURO_AGGIORNAMENTI", None)
        self.file_stato = self.orsa / "session-env" / "aggiornamento.json"
        self.file_esito = self.orsa / "session-env" / "aggiornamento-esito.json"
        self.log = self.orsa / "session-env" / "aggiornamento.log"

    def agg(self, *argomenti, copia: Path = None, **env):
        return fd.esegui([sys.executable, (copia or self.prima) / "bin" / "aggiornamenti.py", *argomenti],
                         env=dict(self.env, **env))

    def chiusura(self, motivo: str = "logout", copia: Path = None, **env):
        """L'hook vero della chiusura, da una cartella che non è un progetto."""
        return fd.esegui([BASH, (copia or self.prima) / "hooks" / "session-end.sh"], input=json.dumps({"reason": motivo}),
                         stdin=None, cwd=str(self.base), env=dict(self.env, **env))

    def aspetta_esito(self, secondi: float = 60) -> dict:
        """applica gira staccato dalla chiusura: si aspetta che scriva l'esito e lasci il lucchetto."""
        fine = time.time() + secondi
        while time.time() < fine:
            if self.file_esito.exists() and not (self.orsa / "session-env" / "aggiornamento.lock").exists():
                break
            time.sleep(0.25)
        return leggi(self.file_esito)

    def installato(self) -> str:
        return str(self.r.installato().get("gitCommitSha"))


def caso_pc01_pc02(repo, tmp, chiavi) -> list:
    rossi = []
    s = Scena(repo, tmp / "pc01", chiavi)
    c = s.agg("controlla", "--subito")
    pronto = leggi(s.file_stato)
    avvio = s.agg("stato")
    (s.orsa / "data" / "aggiornamenti.json").write_text('{"modo": "manuali"}', encoding="utf-8")
    s.agg("controlla", "--subito")
    a_mano = leggi(s.file_stato)
    if c.returncode != 0 or pronto.get("stato") != "pronto" or pronto.get("versione") != "0.4.0" \
            or a_mano.get("stato") != "manuale":
        rossi.append(f"PC01 controlla: rc {c.returncode}, stato {pronto}, a mano {a_mano}")
    if "0.4.0 di Arturo: si installa da sola alla chiusura" not in avvio.stdout:
        rossi.append(f"PC02 avvio col rilascio pronto: {avvio.stdout[-200:]!r}")
    return rossi


def caso_pc03(repo, tmp, chiavi) -> list:
    s = Scena(repo, tmp / "pc03", chiavi)
    h = s.chiusura()
    esito = s.aspetta_esito()
    deny = (leggi(s.orsa / "settings.json").get("permissions") or {}).get("deny") or []
    avvio = s.agg("stato", copia=s.nuova)
    avvio2 = s.agg("stato", copia=s.nuova)
    if esito.get("esito") != "APPLICATO" or esito.get("versione") != "0.4.0" or s.installato() != s.sha \
            or fd.DENY_NUOVA not in deny or "aggiornato a 0.4.0 alla chiusura" not in avvio.stdout \
            or "aggiornato a" in avvio2.stdout:
        log = s.log.read_text(encoding="utf-8", errors="replace")[-200:] if s.log.exists() else "nessun log"
        return [f"PC03 chiusura vera: hook rc {h.returncode}, esito {esito}, installato {s.installato()[:12]}, deny {deny}, "
                f"avvio {avvio.stdout[-120:]!r} poi {avvio2.stdout[-80:]!r}, log {log!r}"]
    return []


def caso_pc04(repo, tmp, chiavi) -> list:
    s = Scena(repo, tmp / "pc04", chiavi, firma="altra")
    s.agg("controlla", "--subito")
    p = s.agg("applica")
    stato = leggi(s.file_stato)
    avvio = s.agg("stato")
    s.agg("controlla", "--subito")
    dopo = leggi(s.file_stato)
    if s.spia.exists() or s.installato() != "a" * 40 or not stato.get("compromesso") or stato.get("versione") != "0.4.0" \
            or "possibile compromissione" not in avvio.stdout or "si installa da sola" in avvio.stdout \
            or not dopo.get("compromesso"):
        return [f"PC04 firma di un'altra chiave: rc {p.returncode}, update partito {s.spia.exists()}, stato {stato}, "
                f"dopo il controllo {dopo}, avvio {avvio.stdout[-160:]!r}"]
    return []


def caso_pc05(repo, tmp, chiavi) -> list:
    s = Scena(repo, tmp / "pc05", chiavi)
    # Un ssh-keygen prima della 8.2, senza -Y, come in AF08: la firma c'è ma questo computer non la sa leggere.
    vecchio = s.base / "ssh-keygen-vecchio"
    vecchio.write_text("#!/bin/sh\necho 'unknown option -- Y' >&2\nexit 1\n", encoding="utf-8")
    vecchio.chmod(0o755)
    config = s.base / "gitconfig"
    config.write_text(f"[gpg \"ssh\"]\n\tprogram = {vecchio.as_posix()}\n", encoding="utf-8")
    env = {"GIT_CONFIG_GLOBAL": str(config), "GIT_CONFIG_NOSYSTEM": "1"}
    p = s.agg("applica", **env)
    stato = leggi(s.file_stato)
    avvio = s.agg("stato", **env)
    if s.spia.exists() or not stato.get("non_verificabile") or stato.get("compromesso") \
            or "git e OpenSSH" not in avvio.stdout or "compromissione" in avvio.stdout:
        return [f"PC05 firma non verificabile: rc {p.returncode}, update partito {s.spia.exists()}, stato {stato}, "
                f"avvio {avvio.stdout[-200:]!r}"]
    return []


def caso_pc06(repo, tmp, chiavi) -> list:
    s = Scena(repo, tmp / "pc06", chiavi, pubblica=False)
    s.agg("controlla", "--subito")
    p = s.agg("applica")
    esito, stato = leggi(s.file_esito), leggi(s.file_stato)
    avvio = s.agg("stato")
    if s.spia.exists() or esito.get("esito") != "NESSUN RILASCIO" or stato.get("stato") != "pronto" \
            or "non è partito" not in avvio.stdout or "Ci riprova alla prossima chiusura" not in avvio.stdout \
            or "si installa da sola" in avvio.stdout:
        return [f"PC06 rilascio che non si scarica: rc {p.returncode}, esito {esito}, stato {stato.get('stato')}, "
                f"avvio {avvio.stdout[-200:]!r}"]
    return []


def caso_pc07(repo, tmp, chiavi) -> list:
    s = Scena(repo, tmp / "pc07", chiavi)
    scelta = s.orsa / "data" / "aggiornamenti.json"
    scelta.write_text('{"modo": "manuali"}', encoding="utf-8")
    s.agg("applica")
    fermo_file = not s.spia.exists() and not s.file_esito.exists()
    scelta.unlink()
    s.chiusura(ARTURO_AGGIORNAMENTI="manuali")
    time.sleep(1)
    fermo_env = not s.spia.exists() and not s.log.exists()
    s.agg("applica")
    if not fermo_file or not fermo_env or leggi(s.file_esito).get("esito") != "APPLICATO":
        return [f"PC07 aggiornamenti a mano: fermo col file {fermo_file}, fermo con la variabile {fermo_env}, senza la "
                f"scelta {leggi(s.file_esito)}"]
    return []


def caso_pc08(repo, tmp, chiavi) -> list:
    s = Scena(repo, tmp / "pc08", chiavi)
    s.chiusura("clear")
    time.sleep(1)
    fermo = not s.log.exists() and not s.spia.exists()
    s.chiusura("logout")
    esito = s.aspetta_esito()
    if not fermo or esito.get("esito") != "APPLICATO":
        return [f"PC08 /clear: fermo {fermo}, poi la chiusura vera {esito}"]
    return []


def caso_pc09(repo, tmp, chiavi) -> list:
    s = Scena(repo, tmp / "pc09", chiavi)
    blocco = s.orsa / "session-env" / "aggiornamento.lock"
    blocco.mkdir(parents=True)
    a = s.agg("applica")
    fermo = a.returncode == 0 and not s.spia.exists()
    m = s.agg("plugin")
    in_corso = m.returncode == 1 and "AGGIORNAMENTO IN CORSO" in m.stdout and not s.spia.exists()
    vecchio = time.time() - 1000
    os.utime(str(blocco), (vecchio, vecchio))
    s.agg("applica")
    if not fermo or not in_corso or not s.spia.exists() or blocco.exists():
        return [f"PC09 lucchetto: chiusura ferma {fermo}, /aggiorna {m.returncode} {m.stdout[-80:]!r}, col lucchetto "
                f"vecchio update partito {s.spia.exists()}, lucchetto rimasto {blocco.exists()}"]
    return []


def caso_pc10(repo, tmp, chiavi) -> list:
    s = Scena(repo, tmp / "pc10", chiavi)
    inizio = time.time()
    s.agg("applica", ARTURO_ALTRE_SESSIONI="2", ARTURO_ATTESA_MAX="6")
    durata = time.time() - inizio
    esito = leggi(s.file_esito)
    # Senza attesa l'installazione dura circa un secondo: sei secondi li spiega solo il ciclo di attesa.
    if durata < 6 or esito.get("esito") != "APPLICATO" or s.installato() != s.sha:
        return [f"PC10 altre sessioni aperte: {durata:.1f} s, esito {esito}"]
    return []


def caso_pc11(repo, tmp, chiavi) -> list:
    s = Scena(repo, tmp / "pc11", chiavi)
    posto = s.casa / ".local" / "bin"
    posto.mkdir(parents=True)
    if os.name == "nt":
        shutil.copy2(s.base / "claude-finto.py", posto / "claude-finto.py")
        shutil.copy2(s.finto, posto / "claude.cmd")
    else:
        shutil.copy2(s.finto, posto / "claude")
    # Un PATH senza nessun `claude`, come quello di un processo staccato dall'app.
    senza = os.pathsep.join(c for c in os.environ.get("PATH", "").split(os.pathsep)
                            if c and not any((Path(c) / n).exists() for n in ("claude", "claude.exe", "claude.cmd")))
    s.agg("applica", ARTURO_CLAUDE="", PATH=senza)
    esito = leggi(s.file_esito)
    if esito.get("esito") != "APPLICATO" or not s.spia.exists():
        return [f"PC11 claude fuori dal PATH: esito {esito}, update partito {s.spia.exists()}"]
    return []


def caso_pc12(repo, tmp, chiavi) -> list:
    s = Scena(repo, tmp / "pc12", chiavi)
    s.agg("applica")
    vecchia = s.agg("stato")  # la sessione rimasta aperta gira ancora dalla 0.3.0
    resta = leggi(s.file_esito).get("mostrato") is False
    nuova = s.agg("stato", copia=s.nuova)
    if "0.4.0 di Arturo è installata: parte alla prossima apertura" not in vecchia.stdout or not resta \
            or "aggiornato a 0.4.0" in vecchia.stdout or "aggiornato a 0.4.0" not in nuova.stdout:
        return [f"PC12 sessione sulla copia di prima: {vecchia.stdout[-160:]!r}, esito da dire {resta}, poi "
                f"{nuova.stdout[-100:]!r}"]
    return []


def caso_pc13(repo, tmp, chiavi) -> list:
    s = Scena(repo, tmp / "pc13", chiavi)
    (s.prima / ".git").mkdir()
    s.chiusura()
    time.sleep(1)
    fermo = not s.log.exists() and not s.spia.exists()
    (s.prima / ".git").rmdir()
    s.chiusura()
    esito = s.aspetta_esito()
    if not fermo or esito.get("esito") != "APPLICATO":
        return [f"PC13 checkout di sviluppo: fermo {fermo}, poi la copia del plugin {esito}"]
    return []


GRUPPI = [(("PC01", "PC02"), caso_pc01_pc02), (("PC03",), caso_pc03), (("PC04",), caso_pc04), (("PC05",), caso_pc05),
          (("PC06",), caso_pc06), (("PC07",), caso_pc07), (("PC08",), caso_pc08), (("PC09",), caso_pc09),
          (("PC10",), caso_pc10), (("PC11",), caso_pc11), (("PC12",), caso_pc12), (("PC13",), caso_pc13)]


def prova(repo: Path, solo: str | None = None) -> list:
    rossi = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp).resolve()
        chiavi = {"rilasci": fd.chiave(tmp, "rilasci"), "altra": fd.chiave(tmp, "altra")}
        for casi, funzione in GRUPPI:
            if solo and solo not in casi:
                continue
            try:
                rossi.extend(funzione(repo, tmp, chiavi))
            except Exception as errore:  # noqa: BLE001 - un caso che si rompe è rosso, non un banco fermo
                rossi.extend(f"{c} eccezione: {type(errore).__name__}: {str(errore)[:160]}" for c in casi)
        time.sleep(0.5)  # un applica staccato rimasto in coda lascia la cartella prima che sparisca
    return [r for r in rossi if not solo or r.startswith(solo)]


# (caso, file, testo giusto, testo rotto): ogni veleno toglie la riga che il caso sorveglia.
AGG = "bin/aggiornamenti.py"
VELENI = [
    ("PC01", AGG, '"manuale" if manuali(r) else "pronto"', '"manuale"'),
    ("PC02", AGG, 'and stato.get("stato") == "pronto" and fallito != nuova', 'and False and fallito != nuova'),
    ("PC03", "hooks/session-end.sh", 'elif [ -f "$ARTURO_CODICE/.claude-plugin/plugin.json" ] && [ ! -e "$ARTURO_CODICE/.git" ]; then',
     'elif false; then'),
    ("PC03", AGG, '                return cmd_applica(r, fare=_applica_plugin)\n', '                return 0\n'),
    ("PC04", AGG, '    elif nuova and vecchio.get("chiusura") and vecchio.get("versione") == nuova:',
     '    elif False:'),
    ("PC04", AGG, '                 "compromesso" if rc == 3 else "non_verificabile": True}',
     '                 "non_verificabile": True}'),
    ("PC05", AGG, '    elif nuova and nuova == stato["versione"] and stato.get("non_verificabile"):', '    elif False:'),
    ("PC06", AGG, '    elif parola not in ("POSSIBILE COMPROMISSIONE", "FIRMA NON VERIFICABILE"):\n        fallito = versione\n',
     '    elif parola not in ("POSSIBILE COMPROMISSIONE", "FIRMA NON VERIFICABILE"):\n        fallito = ""\n'),
    ("PC07", AGG, '    if manuali(r):\n        return 0\n    prima = processi_claude()', '    prima = processi_claude()'),
    ("PC08", "hooks/session-end.sh", '!= "manuali" ] && [ "$MOTIVO" != clear ]; then', '!= "manuali" ]; then'),
    ("PC09", AGG, 'rc = cmd_applica(r, fare=lambda _r: cmd_plugin(), occupato=OCCUPATO)', 'rc = cmd_plugin()'),
    ("PC10", AGG, '    while prima > 0 and processi_claude() >= prima and time.time() < limite:', '    while False:'),
    ("PC11", AGG, '            if (cartella / nome).is_file():', '            if False:'),
    ("PC12", AGG, '    if parola == "APPLICATO" and numero(in_uso) < numero(versione):', '    if False:'),
    ("PC13", "hooks/session-end.sh", '[ -f "$ARTURO_CODICE/.claude-plugin/plugin.json" ] && [ ! -e "$ARTURO_CODICE/.git" ]; then',
     '[ -f "$ARTURO_CODICE/.claude-plugin/plugin.json" ]; then'),
]


def avvelena(repo: Path, solo: str | None = None) -> int:
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
    print(f"chiusura col plugin: {totale - len({r.split()[0] for r in rossi})}/{totale} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
