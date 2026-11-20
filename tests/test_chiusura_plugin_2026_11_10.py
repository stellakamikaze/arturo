#!/usr/bin/env python3
"""PC01-PC25: col plugin un rilascio firmato si installa da solo alla chiusura della sessione (10/11/2026).

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

Dall'11/11/2026, con le correzioni della review del 10/11 (#5264) e il lavoro C del piano (#5307):
PC14 dopo "ho disattivato Arturo", /aggiorna non dice "già aggiornato" su una copia che non torna col MANIFEST, e
     la barra smette di dire "disattivato" quando la persona riattiva il plugin;
PC15 un ARTURO_CLAUDE che indica un programma che non c'è non batte il ripiego: la CLI si trova lo stesso;
PC16 una sessione rimasta sulla copia di prima non riporta indietro settings.json, il blocco e l'ancora delle chiavi;
PC17 Claude Code installa uno sha diverso e la copia di prima non torna: il plugin si disattiva, lo stato lo dice, e
     il controllo dell'ora dopo non cancella l'allarme;
PC18 un fallimento della chiusura, poi un /aggiorna riuscito: l'avvio non dice "non è partito";
PC19 un catalogo che chiama 0.5.0 il tag plugin-v0.4.0 non installa niente: è una compromissione;
PC20 settings.json come collegamento simbolico resta un collegamento, e il file vero riceve la regola nuova;
PC21 un doppione nei permessi della persona non ferma l'unione: la regola di blocco nuova arriva;
PC22 un lucchetto fresco lasciato da un processo che non c'è più non ferma la chiusura;
PC23 col plugin disattivato e la cartella della copia di prima sparita, la barra in basso dice "Arturo disattivato"
     e come riattivarlo; senza quel file dice dove guardare; riattivato il plugin, il file sparisce;
PC24 un catalogo che non si scarica non rinnova l'ultimo controllo riuscito: dopo 7 giorni l'avvio lo dice, e
     un controllo riuscito toglie l'avviso;
PC25 la barra dice "riapri Claude Code" solo alla sessione rimasta sulla copia di prima.
Dal 14/11/2026 (#5610):
PC26 un'installazione riuscita alla chiusura manda l'evento aggiorna "automatico", una volta per versione; un
     rilascio che non si scarica manda "non-partito": prima col plugin non partiva nessuno dei due.

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

CASI = ["PC01", "PC02", "PC03", "PC04", "PC05", "PC06", "PC07", "PC08", "PC09", "PC10", "PC11", "PC12", "PC13",
        "PC14", "PC15", "PC16", "PC17", "PC18", "PC19", "PC20", "PC21", "PC22", "PC23", "PC24", "PC25", "PC26"]
DISCRIMINANTI = list(CASI)
BASH = shutil.which("bash") or "bash"

_spec = importlib.util.spec_from_file_location("fd", str(Path(__file__).resolve().parent / "test_fiducia_2026_11_05.py"))
fd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fd)

# La CLI finta di FD12, con una spia: il file FINTO_SPIA nasce solo se `plugin update` parte. `plugin disable`
# lascia FINTO_SPIA.disable.
FINTO = fd.CLAUDE_FINTO + ('    open(os.environ["FINTO_SPIA"], "w").close()\n'
                           'if sys.argv[1:3] == ["plugin", "disable"]:\n'
                           '    open(os.environ["FINTO_SPIA"] + ".disable", "w").close()\n'
                           'if sys.argv[1:4] == ["plugin", "marketplace", "update"] and os.environ.get("FINTO_CATALOGO_GIU"):\n'
                           '    sys.exit("catalogo: rete assente")\n')
NODE = shutil.which("node") or "node"


def leggi(f: Path) -> dict:
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


class Scena:
    """Una 0.3.0 installata come plugin, un rilascio 0.4.0 nel catalogo, un'Orsa e una casa vuote."""

    def __init__(self, repo: Path, base: Path, chiavi: dict, firma: str = "rilasci", pubblica: bool = True,
                 frammento: dict = None, frammento_prima: dict = None):
        base.mkdir(parents=True)
        self.repo, self.base = repo, base
        privata, firmatari = chiavi["rilasci"]
        self.r = fd.Rilasci(repo, base, chiavi)
        self.r.rilascio("0.3.0", "rilasci")
        self.prima = fd.copia_plugin(repo, base / "cache" / "0.3.0", "0.3.0", firmatari, privata,
                                     frammento=frammento_prima)
        # Senza `pubblica` il catalogo indica un tag che nel repository dei rilasci non c'è: come senza rete.
        self.sha = self.r.rilascio("0.4.0", firma) if pubblica else "b" * 40
        self.r.indica("plugin-v0.4.0", self.sha)
        self.nuova = fd.copia_plugin(repo, base / "cache" / "0.4.0", "0.4.0", firmatari, privata,
                                     frammento=frammento or {"permissions": {"deny": [fd.DENY_NUOVA]}})
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


def _deny(s) -> list:
    return (leggi(s.orsa / "settings.json").get("permissions") or {}).get("deny") or []


def caso_pc14(repo, tmp, chiavi) -> list:
    s = Scena(repo, tmp / "pc14", chiavi)
    # Lo sha è quello del catalogo, ma un file della copia installata è cambiato dopo la firma; quella di prima
    # non c'è più.
    guardia = s.nuova / "hooks" / "block-dangerous.py"
    guardia.write_text(guardia.read_text(encoding="utf-8") + "\n# allentata\n", encoding="utf-8")
    (s.orsa / "plugins" / "installed_plugins.json").write_text(json.dumps({"plugins": {"arturo@arturo": [
        {"scope": "user", "installPath": str(s.base / "sparita"), "version": "0.3.0", "gitCommitSha": "a" * 40}]}}),
        encoding="utf-8")
    s.agg("applica")
    stato = leggi(s.file_stato)
    m = s.agg("plugin")
    dopo = leggi(s.file_stato)
    (s.orsa / "settings.json").write_text(json.dumps({"enabledPlugins": {"arturo@arturo": False}}), encoding="utf-8")
    s.agg("controlla", "--subito")
    spento = leggi(s.file_stato)
    (s.orsa / "settings.json").write_text(json.dumps({"enabledPlugins": {"arturo@arturo": True}}), encoding="utf-8")
    s.agg("controlla", "--subito")
    acceso = leggi(s.file_stato)
    if not stato.get("disattivato") or m.returncode != 3 or "GIÀ AGGIORNATO" in m.stdout or not dopo.get("compromesso") \
            or not spento.get("disattivato") or acceso.get("disattivato") or not acceso.get("compromesso"):
        return [f"PC14 copia che non torna, poi /aggiorna: stato {stato}, plugin rc {m.returncode} "
                f"{(m.stdout + m.stderr)[-100:]!r}, dopo {dopo}, spento {spento}, riacceso {acceso}"]
    return []


def caso_pc15(repo, tmp, chiavi) -> list:
    s = Scena(repo, tmp / "pc15", chiavi)
    posto = s.casa / ".local" / "bin"
    posto.mkdir(parents=True)
    if os.name == "nt":
        shutil.copy2(s.base / "claude-finto.py", posto / "claude-finto.py")
        shutil.copy2(s.finto, posto / "claude.cmd")
    else:
        shutil.copy2(s.finto, posto / "claude")
    senza = os.pathsep.join(c for c in os.environ.get("PATH", "").split(os.pathsep)
                            if c and not any((Path(c) / n).exists() for n in ("claude", "claude.exe", "claude.cmd")))
    # Il percorso POSIX che `command -v claude` dà in Git Bash: Python non lo sa lanciare.
    s.agg("applica", ARTURO_CLAUDE="/c/Users/nessuno/.local/bin/claude", PATH=senza)
    esito = leggi(s.file_esito)
    if esito.get("esito") != "APPLICATO" or not s.spia.exists():
        return [f"PC15 ARTURO_CLAUDE che non c'è: esito {esito}, update partito {s.spia.exists()}"]
    return []


def caso_pc16(repo, tmp, chiavi) -> list:
    # La copia di prima porta il suo frammento, quello del blocco: senza, non avrebbe niente da riportare indietro.
    s = Scena(repo, tmp / "pc16", chiavi, frammento_prima={"permissions": {"deny": []}})
    s.agg("applica")
    # Il rilascio nuovo ha portato una chiave in più nell'ancora: la copia di prima ne conosce una sola.
    ancora = s.orsa / "arturo" / "rilasci.allowed_signers"
    due = ancora.read_bytes() + chiavi["altra"][1].read_bytes()
    ancora.write_bytes(due)
    vecchia = s.agg("stato")  # la sessione rimasta aperta gira ancora dalla 0.3.0
    fd.esegui([sys.executable, s.prima / "hooks" / "deriva.py", str(s.orsa)], env=s.env)
    blocco = leggi(s.orsa / "data" / "arturo-impostazioni.lock").get("versione")
    if fd.DENY_NUOVA not in _deny(s) or blocco != "0.4.0" or "IMPOSTAZIONI APPLICATE" in vecchia.stdout \
            or ancora.read_bytes() != due:
        return [f"PC16 sessione sulla copia di prima: deny {_deny(s)}, blocco {blocco}, ancora intatta "
                f"{ancora.read_bytes() == due}, avvio {vecchia.stdout[-160:]!r}"]
    return []


def caso_pc17(repo, tmp, chiavi) -> list:
    s = Scena(repo, tmp / "pc17", chiavi)
    # La cartella della versione di prima non c'è più, e Claude Code installa uno sha che nessuno ha verificato.
    (s.orsa / "plugins" / "installed_plugins.json").write_text(json.dumps({"plugins": {"arturo@arturo": [
        {"scope": "user", "installPath": str(s.base / "sparita"), "version": "0.3.0", "gitCommitSha": "a" * 40}]}}),
        encoding="utf-8")
    installa = json.dumps({"path": str(s.nuova), "version": "0.4.0", "sha": "d" * 40})
    p = s.agg("applica", FINTO_INSTALLA=installa)
    stato = leggi(s.file_stato)
    disattivato = Path(str(s.spia) + ".disable").exists()
    s.agg("controlla", "--subito")
    dopo = leggi(s.file_stato)
    avvio = s.agg("stato")
    if not disattivato or not stato.get("compromesso") or not stato.get("disattivato") or not dopo.get("compromesso") \
            or "possibile compromissione" not in avvio.stdout:
        log = (p.stdout + p.stderr)[-200:]
        return [f"PC17 copia non verificata rimasta: disable partito {disattivato}, stato {stato}, dopo il controllo "
                f"{dopo}, avvio {avvio.stdout[-120:]!r}, uscita {log!r}"]
    return []


def caso_pc18(repo, tmp, chiavi) -> list:
    s = Scena(repo, tmp / "pc18", chiavi)
    s.file_esito.parent.mkdir(parents=True, exist_ok=True)
    s.file_esito.write_text(json.dumps({"quando": int(time.time()), "versione": "0.4.0", "esito": "NESSUN RILASCIO",
                                        "riga": "NESSUN RILASCIO: rete", "mostrato": False}), encoding="utf-8")
    m = s.agg("plugin")
    avvio = s.agg("stato", copia=s.nuova)
    if m.returncode != 0 or "non è partito" in avvio.stdout or leggi(s.file_esito).get("mostrato") is not True:
        return [f"PC18 fallimento poi /aggiorna: plugin rc {m.returncode}, esito {leggi(s.file_esito)}, avvio "
                f"{avvio.stdout[-160:]!r}"]
    return []


def caso_pc19(repo, tmp, chiavi) -> list:
    s = Scena(repo, tmp / "pc19", chiavi)
    catalogo = s.r.catalogo / ".claude-plugin" / "marketplace.json"
    dati = leggi(catalogo)
    dati["plugins"][0]["version"] = "0.5.0"
    catalogo.write_text(json.dumps(dati), encoding="utf-8")
    p = s.agg("applica")
    stato = leggi(s.file_stato)
    if s.spia.exists() or s.installato() != "a" * 40 or not stato.get("compromesso"):
        return [f"PC19 versione del catalogo diversa dal tag: rc {p.returncode}, update partito {s.spia.exists()}, "
                f"stato {stato}"]
    return []


def caso_pc20(repo, tmp, chiavi) -> list:
    s = Scena(repo, tmp / "pc20", chiavi)
    vero = s.base / "dotfiles" / "settings.json"
    vero.parent.mkdir()
    shutil.move(str(s.orsa / "settings.json"), str(vero))
    try:
        os.symlink(str(vero), str(s.orsa / "settings.json"))
    except (OSError, NotImplementedError):
        shutil.move(str(vero), str(s.orsa / "settings.json"))  # Windows senza il permesso dei collegamenti
        s.agg("applica")
        return [] if fd.DENY_NUOVA in _deny(s) else [f"PC20 senza collegamenti: deny {_deny(s)}"]
    s.agg("applica")
    nel_vero = (leggi(vero).get("permissions") or {}).get("deny") or []
    if not (s.orsa / "settings.json").is_symlink() or fd.DENY_NUOVA not in nel_vero:
        return [f"PC20 settings.json collegamento: ancora collegamento {(s.orsa / 'settings.json').is_symlink()}, "
                f"deny nel file vero {nel_vero}"]
    return []


def caso_pc21(repo, tmp, chiavi) -> list:
    s = Scena(repo, tmp / "pc21", chiavi,
              frammento={"permissions": {"allow": ["Bash(nuova:*)"], "deny": [fd.DENY_NUOVA]}})
    (s.orsa / "settings.json").write_text(json.dumps({"model": "mio", "permissions": {
        "allow": ["Bash(mia:*)", "Bash(mia:*)"], "deny": []}}), encoding="utf-8")
    s.agg("applica")
    esito = leggi(s.file_esito)
    allow = (leggi(s.orsa / "settings.json").get("permissions") or {}).get("allow") or []
    if esito.get("esito") != "APPLICATO" or esito.get("impostazioni") or fd.DENY_NUOVA not in _deny(s) \
            or "Bash(mia:*)" not in allow or "Bash(nuova:*)" not in allow:
        return [f"PC21 doppione nei permessi: esito {esito}, deny {_deny(s)}, allow {allow}"]
    return []


def caso_pc22(repo, tmp, chiavi) -> list:
    if os.name == "nt":
        return []  # su Windows il lucchetto ha solo la scadenza: os.kill(pid, 0) chiuderebbe il processo
    s = Scena(repo, tmp / "pc22", chiavi)
    morto = fd.esegui([sys.executable, "-c", "import os; print(os.getpid())"], env=s.env).stdout.strip()
    blocco = s.orsa / "session-env" / "aggiornamento.lock"
    blocco.mkdir(parents=True)
    (blocco / "pid").write_text(morto, encoding="utf-8")
    s.agg("applica")
    if not s.spia.exists() or blocco.exists():
        return [f"PC22 lucchetto di un processo che non c'è più (pid {morto}): update partito {s.spia.exists()}, "
                f"lucchetto rimasto {blocco.exists()}"]
    return []


def _barra(repo: Path, s) -> str:
    """Il comando statusLine che il pacchetto mette nei settings, lanciato come fa Claude Code. Legge ~/.claude:
    la cartella arturo/ dell'Orsa si copia nella casa di prova (un collegamento su Windows non è garantito)."""
    spec = importlib.util.spec_from_file_location("impacchetta_pc23", str(repo / "bin" / "impacchetta.py"))
    imp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(imp)
    comando = imp.impostazioni(leggi(repo / "settings.json"))["statusLine"]["command"]
    shutil.rmtree(s.casa / ".claude", ignore_errors=True)
    if (s.orsa / "arturo").is_dir():
        shutil.copytree(s.orsa / "arturo", s.casa / ".claude" / "arturo")
    p = fd.esegui([BASH, "-c", comando], input="{}", stdin=None, env=s.env)
    return p.stdout + p.stderr


def caso_pc23(repo, tmp, chiavi) -> list:
    s = Scena(repo, tmp / "pc23", chiavi)
    # Come PC17, e il puntatore della barra indica la cartella di prima, che non c'è più: col plugin spento
    # nessun codice di Arturo può girare (prova con la CLI vera dell'11/11/2026, #5319).
    sparita = s.base / "sparita"
    (s.orsa / "plugins" / "installed_plugins.json").write_text(json.dumps({"plugins": {"arturo@arturo": [
        {"scope": "user", "installPath": str(sparita), "version": "0.3.0", "gitCommitSha": "a" * 40}]}}),
        encoding="utf-8")
    (s.orsa / "arturo").mkdir(exist_ok=True)
    (s.orsa / "arturo" / "radice").write_text(str(sparita), encoding="utf-8")
    senza_file = _barra(repo, s)
    s.agg("applica", FINTO_INSTALLA=json.dumps({"path": str(s.nuova), "version": "0.4.0", "sha": "d" * 40}))
    spento = _barra(repo, s)
    (s.orsa / "settings.json").write_text(json.dumps({"enabledPlugins": {"arturo@arturo": True}}), encoding="utf-8")
    s.agg("controlla", "--subito")
    resta = (s.orsa / "arturo" / "barra-ferma").exists()
    if "Arturo disattivato" not in spento or "claude plugin enable arturo@arturo" not in spento or "0.4.0" not in spento \
            or "claude plugin list" not in senza_file or resta:
        return [f"PC23 barra col plugin spento: senza il file {senza_file[-120:]!r}, spento {spento[-200:]!r}, "
                f"il file resta dopo la riattivazione {resta}"]
    return []


def caso_pc24(repo, tmp, chiavi) -> list:
    s = Scena(repo, tmp / "pc24", chiavi)
    s.agg("controlla", "--subito")
    primo = float(leggi(s.file_stato).get("riuscito") or 0)
    time.sleep(1.1)
    s.agg("controlla", "--subito", FINTO_CATALOGO_GIU="1")
    fermo = float(leggi(s.file_stato).get("riuscito") or 0)
    presto = s.agg("stato")
    s.file_stato.write_text(json.dumps(dict(leggi(s.file_stato), riuscito=time.time() - 8 * 86400,
                                            controllato=time.time())), encoding="utf-8")
    tardi = s.agg("stato")
    s.agg("controlla", "--subito")
    dopo = s.agg("stato")
    frase = "da più di 7 giorni non riesco a controllare gli aggiornamenti"
    if not primo or fermo != primo or frase in presto.stdout or frase not in tardi.stdout or frase in dopo.stdout:
        return [f"PC24 controllo riuscito: primo {primo}, da offline {fermo}, avviso presto {frase in presto.stdout}, "
                f"dopo 8 giorni {tardi.stdout[-160:]!r}, dopo un controllo riuscito {frase in dopo.stdout}"]
    return []


def caso_pc25(repo, tmp, chiavi) -> list:
    s = Scena(repo, tmp / "pc25", chiavi)

    def barra(copia: Path, sessione: str) -> str:
        entrata = json.dumps({"model": {"display_name": "Opus"}, "workspace": {"current_dir": str(s.casa)},
                              "session_id": sessione})
        return fd.esegui([NODE, copia / "hooks" / "statusline.js"], input=entrata, stdin=None, env=s.env).stdout

    s.agg("stato", ARTURO_SESSIONE="sessione-di-prima")
    prima = barra(s.prima, "sessione-di-prima")
    s.agg("applica")
    aperta = barra(s.prima, "sessione-di-prima")
    s.agg("stato", copia=s.nuova, ARTURO_SESSIONE="sessione-nuova")
    nuova = barra(s.nuova, "sessione-nuova")
    ancora_aperta = barra(s.nuova, "sessione-di-prima")  # il puntatore della barra è già passato alla copia nuova
    frase = "Arturo 0.4.0 installata · riapri Claude Code"
    if "riapri" in prima or frase not in aperta or "riapri" in nuova or frase not in ancora_aperta:
        return [f"PC25 barra della sessione rimasta aperta: prima {prima[-80:]!r}, dopo {aperta[-80:]!r}, sessione "
                f"nuova {nuova[-80:]!r}, la vecchia con la barra nuova {ancora_aperta[-80:]!r}"]
    return []


def _spia_telemetria(s) -> Path:
    """Una telemetria finta nell'Orsa: _segnala_ostacolo la cerca lì prima che accanto a sé, e qui annota gli eventi."""
    (s.orsa / "bin").mkdir(exist_ok=True)
    annotati = s.orsa / "eventi-annotati.txt"
    (s.orsa / "bin" / "telemetria.py").write_text(
        "import sys\n"
        f"open({str(annotati)!r}, 'a', encoding='utf-8').write(' '.join(sys.argv[1:]) + '\\n')\n", encoding="utf-8")
    return annotati


def caso_pc26(repo, tmp, chiavi) -> list:
    rossi = []
    s = Scena(repo, tmp / "pc26", chiavi)
    annotati = _spia_telemetria(s)
    s.agg("applica")
    s.agg("applica")
    riuscita = annotati.read_text(encoding="utf-8").splitlines() if annotati.exists() else []
    if riuscita != ["registra aggiorna automatico"]:
        rossi.append(f"PC26 installazione riuscita alla chiusura: eventi {riuscita}, esito {leggi(s.file_esito)}")
    f = Scena(repo, tmp / "pc26b", chiavi, pubblica=False)
    annotati = _spia_telemetria(f)
    f.agg("controlla", "--subito")
    f.agg("applica")
    ferma = annotati.read_text(encoding="utf-8").splitlines() if annotati.exists() else []
    if ferma != ["registra aggiorna non-partito"]:
        rossi.append(f"PC26 rilascio che non si scarica: eventi {ferma}, esito {leggi(f.file_esito)}")
    return rossi


GRUPPI = [(("PC26",), caso_pc26), (("PC24",), caso_pc24), (("PC25",), caso_pc25), (("PC23",), caso_pc23), (("PC01", "PC02"), caso_pc01_pc02), (("PC03",), caso_pc03), (("PC04",), caso_pc04), (("PC05",), caso_pc05),
          (("PC06",), caso_pc06), (("PC07",), caso_pc07), (("PC08",), caso_pc08), (("PC09",), caso_pc09),
          (("PC10",), caso_pc10), (("PC11",), caso_pc11), (("PC12",), caso_pc12), (("PC13",), caso_pc13),
          (("PC14",), caso_pc14), (("PC15",), caso_pc15), (("PC16",), caso_pc16), (("PC17",), caso_pc17),
          (("PC18",), caso_pc18), (("PC19",), caso_pc19), (("PC20",), caso_pc20), (("PC21",), caso_pc21),
          (("PC22",), caso_pc22)]


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
    ("PC04", AGG, '    elif sospetta or (nuova and vecchio.get("chiusura") and vecchio.get("versione") == nuova):',
     '    elif sospetta:'),
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
    ("PC14", AGG, '        if vecchio.get("chiusura") and vecchio.get("compromesso") and not installata_pulita(orsa):',
     '        if False:'),
    ("PC14", AGG, '        if stato.get("disattivato") and plugin_acceso(orsa):', '        if False:'),
    ("PC15", AGG, 'scelto = (shutil.which(dato) if dato else None) or shutil.which("claude")',
     'scelto = dato or shutil.which("claude")'),
    ("PC16", AGG, '    if not percorso or os.path.realpath(percorso) != os.path.realpath(str(copia)):', '    if False:'),
    ("PC16", "hooks/deriva.py",
     'if controllo["firma"] == "ok" and (not fiducia.ancora(orsa).is_file() or installata(codice, orsa)):',
     'if controllo["firma"] == "ok":'),
    ("PC17", AGG, '    elif sospetta or (nuova and vecchio.get("chiusura") and vecchio.get("versione") == nuova):',
     '    elif nuova and vecchio.get("chiusura") and vecchio.get("versione") == nuova:'),
    ("PC17", AGG, '    if _claude("disable", NOME_PLUGIN, timeout=120).returncode == 0:', '    if False:'),
    ("PC18", AGG, '            and numero(in_uso) >= numero(versione):', '            and False:'),
    ("PC19", AGG, '    if voce.get("version") and numero(str(voce["version"])) != numero(tag):', '    if False:'),
    ("PC20", "bin/impostazioni.py", '    percorso = Path(os.path.realpath(str(percorso)))\n', ''),
    ("PC21", "bin/impostazioni.py", 'nostro = senza_ripetuti(senza_doppi(attuale) if togli_doppi else attuale)',
     'nostro = senza_doppi(attuale) if togli_doppi else attuale'),
    ("PC22", AGG, 'if not _lucchetto_orfano(blocco) and time.time() - blocco.stat().st_mtime < 900:',
     'if time.time() - blocco.stat().st_mtime < 900:'),
    ("PC23", AGG, '        _barra_ferma(orsa, stato["versione"])\n', ''),
    ("PC23", AGG, '            _barra_ferma(orsa, togli=True)\n', ''),
    ("PC23", "bin/impacchetta.py", '        linea["command"] = SENZA_CODICE + linea["command"]\n', ''),
    ("PC24", AGG, '    if catalogo.returncode == 0:\n        stato["riuscito"] = time.time()\n    else:',
     '    if True:\n        stato["riuscito"] = time.time()\n    else:'),
    ("PC24", AGG, 'and time.time() - riuscito > SENZA_CONTROLLO:', 'and False:'),
    ("PC25", "hooks/statusline.js", "  const riapri = daRiaprire(sessione);", "  const riapri = '';"),
    ("PC25", AGG, '        (cartella / sessione).write_text(in_uso, encoding="utf-8")', '        pass'),
    ("PC26", AGG, '        _segnala_ostacolo(r, {"versione": versione}, "automatico")\n', ''),
    ("PC26", AGG, '        _segnala_ostacolo(r, {"versione": versione}, "non-partito")\n', '        pass\n'),
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
