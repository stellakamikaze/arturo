#!/usr/bin/env python3
"""ST01-ST05: il codice di Arturo funziona anche fuori da ~/.claude (strati F1, docs/strati.md).

Il plugin mette hook e bin/ in una cartella sua; ~/.claude resta l'Orsa della persona. Le guardie,
l'avvio e la telemetria devono trovare il codice dalla propria cartella, non da $HOME/.claude.

ST01 nel clone (codice dentro ~/.claude) il dispatcher blocca `rm -rf ~/`;
ST02 col codice fuori da ~/.claude e un'Orsa vuota, il dispatcher blocca `rm -rf ~/`
     (prima la guardia mancava in ~/.claude/hooks e il crash diventava una sola conferma);
ST03 col codice fuori, la lettura delle credenziali chiede conferma come nel clone;
ST04 l'avvio scrive in $CLAUDE_ENV_FILE ARTURO_CODICE e il PATH della cartella del codice;
ST05 dispatcher, inject-now, session-start e telemetria-esito non chiamano codice in
     $HOME/.claude/hooks|bin: restano solo il file .local e le guardie della persona;
ST06 Write su un file della cache di un plugin installato (~/.claude/plugins/cache/...) è negato
     da protect_claude_md: col plugin lì stanno le guardie e l'aggiornamento di Arturo;
ST07 una scrittura via shell nella cache dei plugin chiede conferma, come su ~/.claude/hooks: col
     percorso assoluto, relativa dopo un `cd ~/.claude` e con la sessione già nella cache. Il file ha
     un nome neutro (#4566, 4/11/2026): con aggiornamenti.py il caso passava per il nome, e il
     pre-filtro del dispatcher non conosceva la cartella.
ST08 nessun percorso al codice o all'Orsa scritto a mano negli script di hooks/ e bin/: le radici
     passano da hooks/radici.py (radice_arturo, radice_orsa), i messaggi col comando di Arturo da
     comando_arturo(). Restano solo le eccezioni di AMMESSI_ST08, ognuna col suo motivo (#4531);
ST09 radici.py nei due layout: col clone codice e Orsa sono ~/.claude e il comando è
     "python3 ~/.claude/bin/arturo"; col plugin il codice è la cartella del plugin, l'Orsa resta
     ~/.claude (o CLAUDE_CONFIG_DIR) e il comando ha il percorso vero;
ST10 l'interruttore della memoria non guarda bin/arturo accanto agli hook: senza impostazioni è
     spenta in tutti e due i layout, con "accesa": true è accesa in tutti e due (#4531);
ST11 col codice fuori da ~/.claude le guardie leggono le preferenze della persona da ~/.claude/arturo:
     hosts-interni.local (exfil-guard), protect_claude_md.local e bash-dispatcher.local; finché il file
     nuovo manca vale il vecchio in ~/.claude/hooks (#4531);
ST12 i file ~/.claude/arturo/*.local sono protetti come hooks/*.local: Write negato anche con
     "allow config" e "allow dot-claude" nel .local, scrittura via shell con conferma (assoluta e
     dopo un cd);
ST13 gli altri lettori (fonte dei task, profilo degli handoff, contenitori dell'indice, inventario,
     parole vuote della memoria) leggono ~/.claude/arturo, e il vecchio posto finché il nuovo manca.

Invariante (verde anche sulla base): ST01. Sulla base 94db031 sono rossi ST02-ST13.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

CASI = ["ST01", "ST02", "ST03", "ST04", "ST05", "ST06", "ST07", "ST08", "ST09", "ST10", "ST11", "ST12", "ST13"]
DISCRIMINANTI = ["ST02", "ST03", "ST04", "ST05", "ST06", "ST07", "ST08", "ST09", "ST10", "ST11", "ST12", "ST13"]
BASH = shutil.which("bash") or "bash"
CODICE = ["hooks/bash-dispatcher.sh", "hooks/inject-now.sh", "hooks/session-start.sh", "bin/telemetria-esito.sh"]
# Ammessi: il file delle preferenze della persona e la cartella delle sue guardie.
AMMESSE = re.compile(r'ORSA_HOOKS=|bash-dispatcher\.local')
# ST08: le radici scritte a mano vietate e le eccezioni, ognuna col perché. None esclude il file,
# una regex ammette solo le righe che la contengono.
FISSO_PY = re.compile(r'Path\.home\(\)\s*/\s*["\']\.claude["\']|expanduser\(\s*["\']~/\.claude|python3 ~/\.claude/bin/arturo')
FISSO_SH = re.compile(r'(\$HOME|\$\{HOME\}|~)/\.claude/(hooks|bin)/')
AMMESSI_ST08 = {
    # Le guardie giudicano i percorsi di ~/.claude come li scrive il comando: restano sulla home vera.
    "hooks/forma_comando.py": None,
    "hooks/memory-write-scanner.py": None,
    "hooks/protect_claude_md.py": None,
    "hooks/radici.py": None,  # è la fonte
    # Le guardie della persona e il suo file .local stanno nell'Orsa per definizione.
    "hooks/bash-dispatcher.sh": r"ORSA_HOOKS=|bash-dispatcher\.local",
    # L'aggiornamento del clone gira da ~/.claude. Col plugin la chiusura lancia la copia accanto all'hook
    # ($ARTURO_CODICE), senza radici scritte a mano (test_chiusura_plugin_2026_11_10.py).
    "hooks/session-end.sh": r"bin/aggiornamenti\.py",
    # L'aggiornamento del clone è autonomo: deve girare anche con il resto dell'albero a metà o
    # modificato, quindi non importa radici.py. Vale solo col clone in ~/.claude (col plugin, F3).
    "bin/aggiornamenti.py": None,
    "bin/personale.py": None,  # lo lancia l'aggiornamento a metà: autonomo come lui
    # Le guardie non importano radici.py (un import fallito le spegnerebbe): il loro .local sta
    # nella home vera, ~/.claude/arturo, col vecchio ~/.claude/hooks come ripiego (#4531).
    "hooks/exfil-guard.py": r'claude = Path\.home\(\) / "\.claude"$',
    "hooks/web-egress-guard.py": r'claude = Path\.home\(\) / "\.claude"$',
}


def estrai(repo: Path, ref: str | None, dest: Path) -> None:
    """hooks/ e bin/ del repository (o della base `ref`) dentro dest."""
    dest.mkdir(parents=True, exist_ok=True)
    if ref:
        dati = subprocess.run(["git", "-C", str(repo), "archive", ref, "hooks", "bin"],
                              capture_output=True, check=True).stdout
        with tarfile.open(fileobj=io.BytesIO(dati)) as tar:
            tar.extractall(dest)
        return
    for cartella in ("hooks", "bin"):
        shutil.copytree(repo / cartella, dest / cartella, ignore=shutil.ignore_patterns("__pycache__"))


def ambiente(home: Path, extra: dict | None = None) -> dict:
    return {**os.environ, "HOME": str(home), "USERPROFILE": str(home), "ARTURO_TELEMETRIA": "0",
            "ARTURO_AGGIORNAMENTI": "manuali", "GIT_TERMINAL_PROMPT": "0", **(extra or {})}


def dispatcher(codice: Path, home: Path, comando: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    dati = {"tool_name": "Bash", "tool_input": {"command": comando}, "session_id": "st", "cwd": str(cwd or home)}
    return subprocess.run([BASH, str(codice / "hooks" / "bash-dispatcher.sh")], input=json.dumps(dati),
                          capture_output=True, text=True, encoding="utf-8", errors="replace",
                          env=ambiente(home), timeout=120)


def bloccato(esito: subprocess.CompletedProcess) -> bool:
    return esito.returncode == 2 and "Bloccato" in esito.stderr


def chiede(esito: subprocess.CompletedProcess) -> bool:
    return esito.returncode == 0 and '"permissionDecision": "ask"' in esito.stdout


def prova(repo: Path, ref: str | None) -> list[str]:
    rossi = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        clone_home, orsa_home, plugin = tmp / "clone", tmp / "orsa", tmp / "plugin" / "arturo"
        estrai(repo, ref, clone_home / ".claude")
        (orsa_home / ".claude").mkdir(parents=True)
        estrai(repo, ref, plugin)

        if not bloccato(dispatcher(clone_home / ".claude", clone_home, "rm -rf ~/")):
            rossi.append("ST01 nel clone il dispatcher non blocca rm -rf ~/")
        esito = dispatcher(plugin, orsa_home, "rm -rf ~/")
        if not bloccato(esito):
            rossi.append(f"ST02 col codice fuori da ~/.claude rm -rf ~/ non è bloccato: rc={esito.returncode}")
        if not chiede(dispatcher(plugin, orsa_home, "cat ~/.claude/.credentials.json")):
            rossi.append("ST03 col codice fuori la lettura delle credenziali non chiede conferma")

        env_file = tmp / "env"
        progetto = tmp / "progetto"
        progetto.mkdir()
        subprocess.run([BASH, str(plugin / "hooks" / "session-start.sh")], input='{"source":"startup"}',
                       cwd=progetto, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=ambiente(orsa_home, {"CLAUDE_ENV_FILE": str(env_file)}), timeout=120)
        scritto = env_file.read_text(encoding="utf-8") if env_file.exists() else ""
        # La cartella come la scrive bash: su Windows `/tmp/...` o `/c/...`, non `C:\...` (#4790).
        visto = subprocess.run([BASH, "-c", 'cd "$1" && pwd', "_", str(plugin)], capture_output=True,
                               text=True, encoding="utf-8", errors="replace").stdout.strip() or str(plugin)
        if f'ARTURO_CODICE="{visto}"' not in scritto or f'{visto}/bin:' not in scritto:
            rossi.append(f"ST04 l'avvio non esporta la cartella del codice: {scritto[-200:]!r}")

        fissi = []
        for rel in CODICE:
            for n, riga in enumerate((plugin / rel).read_text(encoding="utf-8").splitlines(), 1):
                if riga.lstrip().startswith("#") or AMMESSE.search(riga):
                    continue
                if re.search(r'\$HOME/\.claude/(hooks|bin)/', riga):
                    fissi.append(f"{rel}:{n}")
        if fissi:
            rossi.append(f"ST05 codice cercato in $HOME/.claude: {', '.join(fissi[:6])}")

        cache = orsa_home / ".claude" / "plugins" / "cache" / "arturo" / "arturo" / "1.0" / "bin"
        cache.mkdir(parents=True)
        # Un nome che nessuna regola conosce: conta solo la cartella (#4566).
        bersaglio = cache / "strumento.py"
        bersaglio.write_text("# firmato\n", encoding="utf-8")
        dati = {"tool_name": "Write", "session_id": "st", "cwd": str(orsa_home),
                "tool_input": {"file_path": str(bersaglio), "content": "print('altro')\n"}}
        esito = subprocess.run([sys.executable, str(plugin / "hooks" / "protect_claude_md.py")],
                               input=json.dumps(dati), capture_output=True, text=True, encoding="utf-8",
                               errors="replace", env=ambiente(orsa_home), timeout=60)
        if '"permissionDecision": "deny"' not in esito.stdout:
            rossi.append(f"ST06 Write nella cache del plugin non è negato: {esito.stdout[-160:]!r}")
        relativo = bersaglio.relative_to(orsa_home / ".claude").as_posix()
        # In bash `C:\Users\...` senza virgolette perde le barre: su Windows le forme vere sono
        # `C:/Users/...` e quella di Git Bash, `/c/Users/...`, che la guardia non riconosceva (#4790).
        assolute = [("assoluta", f"echo x > {bersaglio.as_posix()}", None)]
        if os.name == "nt":
            git_bash = "/" + bersaglio.as_posix()[0].lower() + bersaglio.as_posix()[2:]
            assolute.append(("assoluta di Git Bash", f"echo x > {git_bash}", None))
        for nome, comando, cwd in (*assolute,
                                   ("dopo cd ~/.claude", f"cd ~/.claude && echo x > {relativo}", None),
                                   ("dalla cartella della cache", "echo x > strumento.py", cache)):
            if not chiede(dispatcher(plugin, orsa_home, comando, cwd)):
                rossi.append(f"ST07 la scrittura via shell nella cache del plugin non chiede conferma ({nome})")
                break

        fissi = []
        for file in sorted(list(plugin.glob("hooks/*.py")) + list(plugin.glob("bin/**/*.py"))
                           + list(plugin.glob("hooks/*.sh")) + list(plugin.glob("bin/**/*.sh")) + [plugin / "bin" / "arturo"]):
            rel = file.relative_to(plugin).as_posix()
            if rel in AMMESSI_ST08 and AMMESSI_ST08[rel] is None:
                continue
            ammessa = AMMESSI_ST08.get(rel)
            regola = FISSO_SH if file.suffix == ".sh" else FISSO_PY
            for n, riga in enumerate(file.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if riga.lstrip().startswith("#") or not regola.search(riga):
                    continue
                if ammessa and re.search(ammessa, riga):
                    continue
                fissi.append(f"{rel}:{n}")
        if fissi:
            rossi.append(f"ST08 radici scritte a mano ({len(fissi)}): {', '.join(fissi[:8])}")

        def radici(codice: Path, casa: Path, extra: dict | None = None) -> list[str]:
            prog = ("import sys; sys.path.insert(0, sys.argv[1]); import radici as r; "
                    "print(r.radice_arturo()); print(r.radice_orsa()); print(r.comando_arturo())")
            esito = subprocess.run([sys.executable, "-B", "-c", prog, str(codice / "hooks")], capture_output=True,
                                   text=True, encoding="utf-8", errors="replace", env=ambiente(casa, extra), timeout=60)
            return esito.stdout.splitlines() if esito.returncode == 0 else [esito.stderr.strip()[-160:]]

        reale = lambda q: str(Path(os.path.realpath(q)))  # noqa: E731
        clone = radici(clone_home / ".claude", clone_home)
        atteso_clone = [reale(clone_home / ".claude"), str(clone_home / ".claude"), "python3 ~/.claude/bin/arturo"]
        con_plugin = radici(plugin, orsa_home)
        atteso_plugin = [reale(plugin), str(orsa_home / ".claude"), f"python3 {(Path(reale(plugin)) / 'bin' / 'arturo').as_posix()}"]
        altra = tmp / "altra-config"
        con_config = radici(plugin, orsa_home, {"CLAUDE_CONFIG_DIR": str(altra)})
        if clone != atteso_clone:
            rossi.append(f"ST09 radici col clone: {clone} invece di {atteso_clone}")
        elif con_plugin != atteso_plugin:
            rossi.append(f"ST09 radici col plugin: {con_plugin} invece di {atteso_plugin}")
        elif con_config[1:2] != [str(altra)]:
            rossi.append(f"ST09 radice_orsa non segue CLAUDE_CONFIG_DIR: {con_config}")

        def memoria(codice: Path, casa: Path) -> str:
            prog = "import sys; sys.path.insert(0, sys.argv[1]); import melchior_match as m; print(m.memoria_accesa())"
            esito = subprocess.run([sys.executable, "-B", "-c", prog, str(codice / "hooks")], capture_output=True,
                                   text=True, encoding="utf-8", errors="replace",
                                   env={k: v for k, v in ambiente(casa).items() if k != "ARTURO_MEMORIA"}, timeout=60)
            return esito.stdout.strip() or esito.stderr.strip()[-120:]

        sciolti = tmp / "sciolti"  # gli hook senza bin/arturo accanto
        shutil.copytree(plugin / "hooks", sciolti / "hooks", ignore=shutil.ignore_patterns("__pycache__"))
        casa_vuota = tmp / "casa-memoria"
        (casa_vuota / ".claude").mkdir(parents=True)
        accesi = [memoria(plugin, casa_vuota), memoria(sciolti, casa_vuota)]  # default accesa dal 14/11/2026
        impostazioni = casa_vuota / ".claude" / "data" / "memoria" / "impostazioni.json"
        impostazioni.parent.mkdir(parents=True)
        impostazioni.write_text('{"accesa": false}', encoding="utf-8")
        spenti = [memoria(plugin, casa_vuota), memoria(sciolti, casa_vuota)]
        if accesi != ["True", "True"] or spenti != ["False", "False"]:
            rossi.append(f"ST10 la memoria dipende da bin/arturo: senza impostazioni {accesi}, spenta {spenti}")

        # --- ST11-ST13: le preferenze della persona in ~/.claude/arturo (#4531) ---
        def casa_pref(nome: str) -> Path:
            casa = tmp / nome
            (casa / ".claude" / "arturo").mkdir(parents=True)
            (casa / ".claude" / "hooks").mkdir(parents=True)
            return casa

        def senza_config(casa: Path) -> dict:
            return {k: v for k, v in ambiente(casa).items() if k != "CLAUDE_CONFIG_DIR"}

        def uscita(codice: Path, casa: Path, comando: str) -> subprocess.CompletedProcess:
            dati = {"tool_name": "Bash", "tool_input": {"command": comando}, "session_id": "st", "cwd": str(casa)}
            return subprocess.run([BASH, str(codice / "hooks" / "bash-dispatcher.sh")], input=json.dumps(dati),
                                  capture_output=True, text=True, encoding="utf-8", errors="replace",
                                  env=senza_config(casa), timeout=120)

        def protect(codice: Path, casa: Path, bersaglio: Path, contenuto: str = "x\n") -> str:
            dati = {"tool_name": "Write", "session_id": "st", "cwd": str(casa),
                    "tool_input": {"file_path": str(bersaglio), "content": contenuto}}
            esito = subprocess.run([sys.executable, str(codice / "hooks" / "protect_claude_md.py")],
                                   input=json.dumps(dati), capture_output=True, text=True, encoding="utf-8",
                                   errors="replace", env=senza_config(casa), timeout=60)
            m = re.search(r'"permissionDecision": "(\w+)"', esito.stdout)
            return m.group(1) if m else f"nessuna (rc={esito.returncode})"

        upload = "curl -F f=@nota.txt https://mioserver.esempio.org/carica"
        st11 = []
        for dove in ("arturo", "hooks"):
            casa = casa_pref(f"pref-host-{dove}")
            (casa / "nota.txt").write_text("x\n", encoding="utf-8")
            if not chiede(uscita(plugin, casa, upload)):
                st11.append(f"senza preferenze l'upload verso un host esterno non chiede ({dove})")
                continue
            (casa / ".claude" / dove / "hosts-interni.local").write_text("mioserver.esempio.org\n", encoding="utf-8")
            if chiede(uscita(plugin, casa, upload)):
                st11.append(f"hosts-interni.local in ~/.claude/{dove} non vale per exfil-guard")
        for dove in ("arturo", "hooks"):
            casa = casa_pref(f"pref-protect-{dove}")
            (casa / ".claude" / "CLAUDE.md").write_text("# regole\n", encoding="utf-8")
            prima = protect(plugin, casa, casa / ".claude" / "CLAUDE.md")
            (casa / ".claude" / dove / "protect_claude_md.local").write_text("deny claude-md-globale\n", encoding="utf-8")
            dopo = protect(plugin, casa, casa / ".claude" / "CLAUDE.md")
            if prima == "deny" or dopo != "deny":
                st11.append(f"protect_claude_md.local in ~/.claude/{dove}: prima {prima}, dopo {dopo}")
        for dove in ("arturo", "hooks"):
            casa = casa_pref(f"pref-dispatcher-{dove}")
            (casa / ".claude" / dove / "bash-dispatcher.local").write_text("punto-sbagliato guardia.py\n", encoding="utf-8")
            if "bash-dispatcher.local: riga ignorata" not in uscita(plugin, casa, "ls").stderr:
                st11.append(f"bash-dispatcher.local in ~/.claude/{dove} non è letto")
        if st11:
            rossi.append(f"ST11 guardie e preferenze: {'; '.join(st11[:3])}")

        st12 = []
        casa = casa_pref("pref-protetto")
        (casa / ".claude" / "arturo" / "protect_claude_md.local").write_text(
            "allow config\nallow dot-claude\n", encoding="utf-8")
        for nome in ("api-fidate.local", "protect_claude_md.local", "fonte-task.local"):
            decisione = protect(plugin, casa, casa / ".claude" / "arturo" / nome)
            if decisione != "deny":
                st12.append(f"Write su ~/.claude/arturo/{nome}: {decisione}")
        for nome, comando in (("assoluta", "echo x >> ~/.claude/arturo/api-fidate.local"),
                              ("dopo cd", "cd ~/.claude/arturo && echo x >> hosts-interni.local")):
            esito = uscita(plugin, casa, comando)
            if not (chiede(esito) or bloccato(esito)):
                st12.append(f"scrittura via shell {nome} senza conferma")
        if st12:
            rossi.append(f"ST12 ~/.claude/arturo/*.local non protetti: {'; '.join(st12[:3])}")

        lettori = r"""
import importlib.util, json, sys
from pathlib import Path
codice = Path(sys.argv[1])
sys.path.insert(0, str(codice / "bin")); sys.path.insert(0, str(codice / "hooks"))
def carica(rel, nome):
    spec = importlib.util.spec_from_file_location(nome, codice / rel)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
out = {}
for chiave, fare in (
    ("fonte", lambda: str(carica("bin/todo_store.py", "todo_store").fonte_locale())),
    ("profilo", lambda: carica("bin/handoff_profilo.py", "handoff_profilo").carica()["colonna-id"]),
    ("contenitori", lambda: sorted(carica("bin/index-rigenera.py", "index_rigenera").contenitori())),
    ("inventario", lambda: [x for c in carica("bin/inventario-sessione.py", "inventario").crea_locali()
                            for x in c if isinstance(x, str)]),
    ("stopword", lambda: "zorbaparola" in carica("hooks/melchior_match.py", "melchior_match").STOPWORDS),
):
    try:
        out[chiave] = fare()
    except Exception as e:
        out[chiave] = f"errore {type(e).__name__}: {e}"
print(json.dumps(out))
"""
        st13 = []
        for dove, vecchi in (("arturo", None), ("vecchio", {"fonte-task.local": "bin"})):
            casa = casa_pref(f"pref-lettori-{dove}")
            (casa / ".claude" / "bin").mkdir(parents=True)
            file = {"fonte-task.local": "comando = fonte\n", "handoff-gate.local": "colonna-id = Ticket\n",
                    "index-contenitori.local": "scatola\n", "inventario.local": "Google Doc = duplica\\.py\n",
                    "melchior-stopword.local": "zorbaparola\n"}
            for nome, testo in file.items():
                cartella = "arturo" if dove == "arturo" else (vecchi.get(nome) or "hooks")
                (casa / ".claude" / cartella / nome).write_text(testo, encoding="utf-8")
            esito = subprocess.run([sys.executable, "-B", "-c", lettori, str(plugin)], capture_output=True,
                                   text=True, encoding="utf-8", errors="replace", env=senza_config(casa), timeout=60)
            try:
                visto = json.loads(esito.stdout.strip().splitlines()[-1])
            except (ValueError, IndexError):
                st13.append(f"{dove}: lettori non partiti ({esito.stderr.strip()[-160:]})")
                continue
            atteso_fonte = casa / ".claude" / ("arturo" if dove == "arturo" else "bin") / "fonte-task.local"
            atteso = {"fonte": str(atteso_fonte), "profilo": "Ticket", "contenitori": ["scatola"],
                      "inventario": ["Google Doc"], "stopword": True}
            diversi = [f"{k}={visto.get(k)!r}" for k, v in atteso.items() if visto.get(k) != v]
            if diversi:
                st13.append(f"{dove}: {', '.join(diversi)}")
        if st13:
            rossi.append(f"ST13 preferenze lette accanto al codice: {'; '.join(st13)[:400]}")
    return rossi


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    argomenti = parser.parse_args()
    rossi = prova(Path(argomenti.repo), argomenti.baseline_ref)
    if argomenti.baseline_ref:
        codici = [r.split()[0] for r in rossi]
        assert codici == DISCRIMINANTI, f"baseline non discriminante: rossi {codici}, attesi {DISCRIMINANTI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    print(f"strati: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
