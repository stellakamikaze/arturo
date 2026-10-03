#!/usr/bin/env python3
"""U01-U13: il pannello /dafare dentro Claude Code (ciclo 2, 3/10/2026).

Il pannello è un mod di Claude Code in skills/dafare/: Claude Code lo carica da solo come
dafare@skills-dir. Legge e scrive i todo solo con la CLI `arturo todo`.

U01 il manifest, gli hook e niente SKILL.md: è un mod, non una skill. U02 `claude plugin
validate` passa, il mod aggancia gli eventi giusti e chiama solo process.run (niente rete,
niente modello, niente prompt). U03 `claude plugin test` passa con 0 fail e su ogni superficie passano tutti
i test del kit, contati per id con la tabella KIT. U04 la tabella dei tasti (hooks/verbi.mjs) sulla CLI vera:
ogni verbo fa quello che dice e ogni inverso rimette stato, motivo, chi e quando di prima, con
il segno di annullo, anche con un motivo «--» e su ogni Python dalla 3.8 alla 3.11 che c'è; le
chiavi di TodoVoce sono quelle della CLI. U05 in una HOME pulita Claude
Code adotta il mod e `claude -p /dafare` legge l'archivio. U06 il percorso della CLI viene dalla
cartella del mod, e nel mod non ci sono percorsi assoluti né dati personali. U07 i testi del
pannello: niente emoji, niente apostrofo al posto dell'accento, niente «dovresti» o «qualora».
U08 /system-audit riconosce un mod e lo distingue da una skill rotta. U09 .gitignore tiene fuori
i file che Claude Code genera accanto al mod, e dentro il mod vero. U10 il diff di /aggiorna,
lanciato con bash e zsh in un clone fermo alla base, mostra il codice del mod. U11 la persona scopre il pannello da skill, /inizio, README, NOVITA, /setup e
/diagnosi; skill e /inizio lo nominano solo se `claude plugin list --json` mostra il mod acceso;
il referente sa come spegnerlo. U12 il README conta le skill giuste e spiega il mod.
U13 validate e test non eseguono gli hook di sessione e non chiedono rete né accesso: un
controllo positivo prova che la sentinella funziona e che la HOME di prova non ha accesso.

Il gate richiede il binario `claude`: se manca, il banco fallisce con un messaggio esplicito.
Sulla base fc6459f ogni controllo deve fallire.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

OGGI = "2026-10-03"
VERBI_ATTESI = {"fatto", "ferma", "riprendi", "chi", "avvicina", "allontana"}
# Quanti test del kit porta ogni id, su ogni superficie. Si conta, non si confronta un insieme:
# un test tolto da un id che ne ha due deve far fallire U03.
KIT = {f"U{n}": 1 for n in range(20, 34)}
KIT.update(U21=2, U27=2, U28=3, U30=2, U31=3)
TEST_KIT = sum(KIT.values())
PROXY_MORTO = "http://127.0.0.1:9"
GENERATI = (".claude-plugin/types", "tsconfig.json")
# I nomi della config dell'autore, spezzati come in test_allineamento.py perché l'igiene I03 non
# li trovi in questo file.
PERSONALI = "|".join(re.escape(a + b) for a, b in (("fede", "rico"), ("noco", "db"), ("tasks", ".py"),
                                                    ("ufficio", "furore"), ("gani", "mede")))


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def mod(repo: Path) -> Path:
    cartella = repo / "skills" / "dafare"
    if not (cartella / ".claude-plugin" / "plugin.json").is_file():
        raise FileNotFoundError(cartella / ".claude-plugin" / "plugin.json")
    return cartella


def claude() -> str:
    trovato = shutil.which("claude")
    assert trovato, ("claude mancante: il banco del pannello prova il mod con claude plugin validate, "
                     "claude plugin test e claude -p. Installa Claude Code (2.1.287 o successivo).")
    return trovato


def ambiente(home: Path) -> dict:
    """Un ambiente senza accesso e senza rete: niente variabili di Claude Code o Anthropic,
    una HOME di prova e un proxy che non risponde."""
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith(("CLAUDE", "ANTHROPIC"))}
    env.update(HOME=str(home), USERPROFILE=str(home), ARTURO_OGGI=OGGI, PYTHONIOENCODING="utf-8",
               HTTPS_PROXY=PROXY_MORTO, HTTP_PROXY=PROXY_MORTO, ALL_PROXY=PROXY_MORTO,
               https_proxy=PROXY_MORTO, http_proxy=PROXY_MORTO, NO_PROXY="", no_proxy="")
    env.pop("ARTURO_TODO", None)
    return env


def casa_con_sentinella(base: Path) -> Path:
    """Una HOME minima con due hook che lasciano un file se qualcuno apre una sessione."""
    home = base / "home"
    (home / ".claude").mkdir(parents=True)
    hook = lambda nome: [{"hooks": [{"type": "command", "command": f"touch \"{home / nome}\""}]}]  # noqa: E731
    impostazioni = {"hooks": {"SessionStart": hook("SESSIONE"), "UserPromptSubmit": hook("PROMPT")}}
    (home / ".claude" / "settings.json").write_text(json.dumps(impostazioni), encoding="utf-8")
    return home


def lancia(argv: list, home: Path, cwd: Path, timeout: int = 180) -> subprocess.CompletedProcess:
    try:
        r = subprocess.run(argv, cwd=str(cwd), env=ambiente(home), stdin=subprocess.DEVNULL,
                           capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise AssertionError(f"{' '.join(map(str, argv[:3]))} non finisce in {timeout} s: forse cerca la rete o un accesso")
    r.stdout, r.stderr = r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace")
    return r


def cli(repo: Path, home: Path, *argomenti: str, ok: bool = True, python: str = sys.executable) -> subprocess.CompletedProcess:
    r = lancia([python, str(repo / "bin" / "arturo"), "todo", *argomenti], home, home, timeout=60)
    if ok:
        assert r.returncode == 0, f"arturo todo {' '.join(argomenti)}: rc={r.returncode} {r.stderr.strip()}"
    return r


def copia_mod(m: Path, dest: Path) -> None:
    """Copia il mod senza i file che Claude Code genera accanto a lui."""
    def fuori(cartella: str, nomi: list) -> list:
        dove = Path(cartella)
        return [n for n in nomi if (dove.name == ".claude-plugin" and n == "types")
                or (dove == m and n == "tsconfig.json") or n == "__pycache__"]
    shutil.copytree(str(m), str(dest), ignore=fuori)


def validate(repo: Path, base: Path) -> subprocess.CompletedProcess:
    home = casa_con_sentinella(base)
    return lancia([claude(), "plugin", "validate", str(mod(repo))], home, base)


def kit(repo: Path, base: Path) -> subprocess.CompletedProcess:
    home = casa_con_sentinella(base)
    return lancia([claude(), "plugin", "test", str(mod(repo))], home, base, timeout=300)


def test_u01(repo: Path) -> None:
    m = mod(repo)
    manifest = json.loads(read(m / ".claude-plugin" / "plugin.json"))
    assert manifest.get("name") == "dafare" == m.name, f"U01 il nome del mod: {manifest.get('name')}"
    tipi = manifest.get("types")
    assert tipi and (m / ".claude-plugin" / ".." / tipi).resolve().is_file(), f"U01 il contratto dei tipi: {tipi}"
    hooks = json.loads(read(m / "hooks" / "hooks.json"))
    assert hooks == {"modules": ["./register.tsx"]}, f"U01 hooks.json: {hooks}"
    assert (m / "hooks" / "register.tsx").is_file(), "U01 hooks.json nomina un modulo che non esiste"
    assert not (m / "SKILL.md").exists(), "U01 il mod ha una SKILL.md: diventerebbe anche una skill"
    assert (m / ".." / ".." / "bin" / "arturo").resolve().is_file(), "U01 la CLI non sta in skills/dafare/../../bin/arturo"


def test_u02(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        r = validate(repo, Path(tmp))
    testo = r.stdout + r.stderr
    assert r.returncode == 0 and "Validation passed" in testo, f"U02 validate rc={r.returncode}: {testo[-800:]}"
    hooks = [x for x in testo.splitlines() if "register.tsx hooks:" in x]
    calls = [x for x in testo.splitlines() if "register.tsx calls:" in x]
    assert len(hooks) == 1 and len(calls) == 1, f"U02 validate non elenca hooks e calls: {testo[-800:]}"
    for evento in ("session.start", "turn.complete", "command.run{command=dafare}",
                   "ui.render{component=Pane, requestId=dafare}", "ui.render{component=AbovePrompt}"):
        assert evento in hooks[0], f"U02 il mod non aggancia {evento}: {hooks[0]}"
    assert "$.process.run" in calls[0], f"U02 il mod non lancia la CLI: {calls[0]}"
    for vietato in ("$.http", "$.model", "$.prompt.submit", "$.tool.register", "$.session.append", "$.fs.write"):
        assert vietato not in calls[0], f"U02 il mod chiama {vietato}: scrive fuori dalla CLI, esce in rete o avvia turni"


def test_u03(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        r = kit(repo, Path(tmp))
    testo = r.stdout + r.stderr
    falliti = re.findall(r"^\(fail\) (\w+: U\d+)\b", testo, re.M)
    assert not falliti, f"U03 test del kit falliti: {falliti}"
    assert r.returncode == 0 and re.search(r"^\s*0 fail\s*$", testo, re.M), f"U03 claude plugin test: {testo[-1500:]}"
    for superficie in ("terminal", "desktop"):
        passati = re.findall(rf"^\(pass\) {superficie}: (U\d+)\b", testo, re.M)
        contati = {i: passati.count(i) for i in sorted(set(passati))}
        assert contati == KIT and len(passati) == TEST_KIT, \
            f"U03 test del kit passati su {superficie}: {contati} (len {len(passati)}), attesi {KIT} (len {TEST_KIT})"


def calcola_verbi(repo: Path, riga: dict) -> dict:
    """Carica hooks/verbi.mjs con node e calcola argv e inverso di ogni verbo per una riga."""
    verbi = mod(repo) / "hooks" / "verbi.mjs"
    if not verbi.is_file():
        raise FileNotFoundError(verbi)
    codice = ("const { pathToFileURL } = require('url');"
              "import(pathToFileURL(process.argv[1]).href).then(m => {"
              " const t = JSON.parse(process.argv[2]); const fuori = {};"
              " for (const [k, v] of Object.entries(m.VERBI)) fuori[k] = { argv: v.argv(t), inverso: v.inverso(t), tasto: v.tasto };"
              " process.stdout.write(JSON.stringify(fuori)); })")
    r = subprocess.run(["node", "-e", codice, str(verbi), json.dumps(riga)], capture_output=True, timeout=60)
    assert r.returncode == 0, f"U04 node non carica verbi.mjs: {r.stderr.decode('utf-8', 'replace')}"
    return json.loads(r.stdout.decode("utf-8"))


def test_u04(repo: Path) -> None:
    sys.path.insert(0, str(repo / "bin"))
    try:
        import importlib
        sys.modules.pop("todo_store", None)
        ts = importlib.import_module("todo_store")
        chiavi = set(ts.CHIAVI_TODO)
    finally:
        sys.path.remove(str(repo / "bin"))
        sys.modules.pop("todo_store", None)
    tipi = read(mod(repo) / "types" / "index.d.ts")
    blocco = re.search(r"export type TodoVoce = \{(.*?)\n\}", tipi, re.S)
    assert blocco, "U04 types/index.d.ts non dichiara TodoVoce"
    dichiarate = set(re.findall(r"^\s+(\w+)\??:", blocco.group(1), re.M))
    assert dichiarate == chiavi, f"U04 TodoVoce e CHIAVI_TODO non coincidono: {sorted(dichiarate ^ chiavi)}"

    for python in pythons():
        verbi_sulla_cli(repo, chiavi, python)


def pythons() -> list:
    """L'interprete del banco più ogni Python dalla 3.8 alla 3.11 che c'è: fino alla 3.11 argparse
    tratta «--» in un altro modo, e il pannello usa il primo python3 che trova (su macOS il 3.9)."""
    trovati, visti = [], set()
    for nome in [sys.executable, "/usr/bin/python3"] + [shutil.which(f"python3.{n}") or "" for n in range(8, 12)]:
        if not nome or not os.path.isfile(nome):
            continue
        r = subprocess.run([nome, "-c", "import sys; print(sys.version_info >= (3, 8))"], capture_output=True, timeout=30)
        vero = os.path.realpath(nome)
        if r.returncode == 0 and r.stdout.strip() == b"True" and vero not in visti:
            visti.add(vero)
            trovati.append(nome)
    return trovati


def verbi_sulla_cli(repo: Path, chiavi: set, python: str) -> None:
    def cli_(*argomenti: str) -> subprocess.CompletedProcess:
        return cli(repo, home, *argomenti, python=python)

    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / "home"
        home.mkdir()

        def todo() -> dict:
            v = json.loads(cli_("--json").stdout)
            tutti = [t for g in v["gruppi"] for t in g["todo"]]
            if not tutti:
                return json.loads(cli_("mostra", "1", "--json").stdout)
            assert set(tutti[0]) == chiavi, f"U04 le chiavi del JSON vero: {sorted(set(tutti[0]) ^ chiavi)}"
            return tutti[0]

        def mostra() -> dict:
            return json.loads(cli_("mostra", "1", "--json").stdout)

        def prova(verbo: str, atteso: dict) -> None:
            prima = todo()
            calcolati = calcola_verbi(repo, prima)
            assert set(calcolati) == VERBI_ATTESI, f"U04 i verbi del pannello: {sorted(calcolati)} (len {len(calcolati)})"
            v = calcolati[verbo]
            cli_(*v["argv"])
            dopo = mostra()
            for campo, valore in atteso.items():
                assert dopo[campo] == valore, f"U04 {verbo} {v['argv']} con {python}: {campo}={dopo[campo]!r}, atteso {valore!r}"
            cli_(*v["inverso"])
            tornato = mostra()
            for campo in ("stato", "motivo", "chi", "quando", "gruppo"):
                assert tornato[campo] == prima[campo], \
                    f"U04 l'inverso di {verbo} {v['inverso']} con {python}: {campo}={tornato[campo]!r}, prima era {prima[campo]!r}"
            ultimo = tornato["storia"][-1]["dati"]
            assert ultimo.get("annullo") is True, f"U04 l'inverso di {verbo} non porta il segno di annullo: {ultimo}"

        cli_("aggiungi", "Provare il pannello", "--progetto", "prova", "--chi", "tu", "--quando", "settimana")
        prova("fatto", {"stato": "fatto"})
        prova("ferma", {"stato": "fermo", "gruppo": "fermo"})
        prova("chi", {"chi": "decidi", "gruppo": "decidi"})
        prova("avvicina", {"quando": "oggi"})
        prova("allontana", {"quando": "più avanti"})
        cli_("inizia", "1")
        prova("fatto", {"stato": "fatto"})  # l'inverso rimette «in corso», non «da fare»
        cli_("ferma", "1", "aspetto la firma")
        prova("riprendi", {"stato": "da fare", "gruppo": "tu"})  # l'inverso rimette FERMO con il motivo
        assert mostra()["motivo"] == "aspetto la firma", "U04 l'inverso di riprendi perde il motivo"
        # Un motivo di una parola che comincia con un trattino: l'inverso lo passa in --motivo=, e la
        # CLI non lo legge come un'opzione.
        cli_("ferma", "1", "--", "-firma")
        prova("riprendi", {"stato": "da fare", "gruppo": "tu"})
        assert mostra()["motivo"] == "-firma", "U04 l'inverso di riprendi perde il motivo «-firma»"
        prova("fatto", {"stato": "fatto"})
        assert mostra()["motivo"] == "-firma", "U04 l'inverso di fatto perde il motivo «-firma»"
        # Un motivo «--»: fino a Python 3.11 argparse lo toglie da un argomento normale.
        cli_("ripristina", "1", "--motivo=--", "fermo")
        assert mostra()["motivo"] == "--", f"U04 ripristina --motivo=-- con {python}: {mostra()['motivo']!r}"
        prova("riprendi", {"stato": "da fare", "gruppo": "tu"})
        assert mostra()["motivo"] == "--", f"U04 l'inverso di riprendi perde il motivo «--» con {python}"
        prova("fatto", {"stato": "fatto"})
        assert mostra()["motivo"] == "--", f"U04 l'inverso di fatto perde il motivo «--» con {python}"


def test_u05(repo: Path) -> None:
    m = mod(repo)
    exe = claude()
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        home = base / "home"
        shutil.copytree(str(repo / "bin"), str(home / ".claude" / "bin"))
        copia_mod(m, home / ".claude" / "skills" / "dafare")
        r = lancia([exe, "plugin", "list", "--json"], home, base)
        assert r.returncode == 0, f"U05 claude plugin list: {r.stderr[-500:]}"
        voci = {p.get("id"): p for p in json.loads(r.stdout)}
        assert voci.get("dafare@skills-dir", {}).get("enabled") is True, \
            f"U05 Claude Code non adotta il mod da ~/.claude/skills: {sorted(voci)}"
        cli(repo, home, "aggiungi", "Provare il pannello", "--progetto", "prova")
        r = lancia([exe, "-p", "/dafare"], home, base, timeout=120)
        testo = r.stdout + r.stderr
        # Un /dafare che il mod non registra arriva al modello come domanda, e la HOME di prova non ha
        # un accesso: Claude Code chiede il login. Il messaggio nomina tutte e due le cause.
        assert "login" not in testo.lower(), \
            f"U05 /dafare non è un comando del mod, oppure claude -p non parte in HOME isolata: {testo[-500:]}"
        assert r.returncode == 0 and "1 cosa da fare" in r.stdout, f"U05 /dafare in claude -p: rc={r.returncode} {testo[-800:]}"


def test_u06(repo: Path) -> None:
    m = mod(repo)
    modulo = read(m / "hooks" / "register.tsx")
    assert re.search(r"const CLI_REL = '/\.\./\.\./bin/arturo'", modulo), "U06 CLI_REL non è '/../../bin/arturo'"
    assert "$.plugin.root + CLI_REL" in modulo, "U06 il percorso della CLI non parte da $.plugin.root"
    file = [p for p in m.rglob("*") if p.is_file() and not any(g in p.relative_to(m).as_posix() for g in GENERATI)]
    assert len(file) >= 6, f"U06 il mod ha pochi file: {[p.name for p in file]}"
    for p in file:
        testo = read(p)
        if p.name == "plugin.json":
            dati = json.loads(testo)
            dati.pop("author", None)
            testo = json.dumps(dati, ensure_ascii=False)
        nome = p.relative_to(repo).as_posix()
        assert not re.search(r"/Users/|/home/|[A-Za-z]:\\\\|~/\.claude/bin|Documents/ClaudeCode", testo), \
            f"U06 percorso assoluto o della macchina dell'autore in {nome}"
        assert not re.search(PERSONALI, testo, re.I), f"U06 dati personali in {nome}"
    # Lacuna 5: nessuna istruzione della macchina dell'autore nelle .md sotto skills/.
    for p in (repo / "skills").rglob("*.md"):
        assert "Documents/ClaudeCode" not in read(p), f"U06 «Documents/ClaudeCode» in {p.relative_to(repo)}"


EMOJI = re.compile("[\U0001F000-\U0001FAFF\u2600-\u2604\u2606-\u27BF\u2B00-\u2BFF\uFE0F]")


def test_u07(repo: Path) -> None:
    m = mod(repo)
    for nome in ("hooks/register.tsx", "hooks/verbi.mjs"):
        testo = read(m / nome)
        stringhe = re.findall(r"'(?:[^'\\\n]|\\.)*'|`(?:[^`\\]|\\.)*`|\"(?:[^\"\\\n]|\\.)*\"", testo)
        assert len(stringhe) > 10, f"U07 poche stringhe lette in {nome}: {len(stringhe)}"
        for s in stringhe + [testo]:
            assert not EMOJI.search(s), f"U07 emoji in {nome}: {s[:80]!r}"
            assert not re.search(r"\b(e|perche|piu|gia|cosi|puo)'(?!\w)", s, re.I), \
                f"U07 apostrofo al posto dell'accento in {nome}: {s[:80]!r}"
            assert not re.search(r"\b(dovresti|qualora)\b", s, re.I), f"U07 condizionale o «qualora» in {nome}: {s[:80]!r}"


def audit(home: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home))
    r = subprocess.run(["bash", str(home / ".claude" / "skills" / "system-audit" / "audit.sh"), "--strict"],
                       env=env, capture_output=True, timeout=180)
    r.stdout = r.stdout.decode("utf-8", "replace")
    return r


def test_u08(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / "home"
        shutil.copytree(str(repo), str(home / ".claude"), ignore=shutil.ignore_patterns(".git"))
        finto = home / ".claude" / "skills" / "finto"
        (finto / ".claude-plugin").mkdir(parents=True)
        (finto / "hooks").mkdir()
        (finto / ".claude-plugin" / "plugin.json").write_text('{"name": "finto"}', encoding="utf-8")
        (finto / "hooks" / "hooks.json").write_text('{"modules": ["./register.tsx"]}', encoding="utf-8")
        r = audit(home)
        assert r.returncode == 0 and "skill: directory e frontmatter YAML validi" in r.stdout, \
            f"U08 /system-audit non riconosce un mod: {r.stdout[-800:]}"
        mod_rotto = "mod: .claude-plugin/plugin.json non valido"
        (finto / ".claude-plugin" / "plugin.json").write_text('{"name": "altro"}', encoding="utf-8")
        r = audit(home)
        assert r.returncode != 0 and mod_rotto in r.stdout, f"U08 un mod col nome sbagliato passa l'audit: {r.stdout[-800:]}"
        assert "SKILL.md mancante" not in r.stdout, f"U08 un mod rotto chiede una SKILL.md: {r.stdout[-800:]}"
        (finto / ".claude-plugin" / "plugin.json").write_text('{"name": "finto"}', encoding="utf-8")
        (finto / "hooks" / "hooks.json").unlink()
        r = audit(home)
        assert r.returncode != 0 and mod_rotto in r.stdout and "SKILL.md mancante" not in r.stdout, \
            f"U08 un mod senza hooks/hooks.json: {r.stdout[-800:]}"
        shutil.rmtree(str(finto))
        (home / ".claude" / "skills" / "vuota").mkdir()
        r = audit(home)
        assert r.returncode != 0 and "skill: SKILL.md mancante" in r.stdout and mod_rotto not in r.stdout, \
            f"U08 una cartella senza SKILL.md e senza plugin.json passa l'audit: {r.stdout[-800:]}"


def test_u09(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        copia = Path(tmp)
        shutil.copy2(str(repo / ".gitignore"), str(copia / ".gitignore"))
        subprocess.run(["git", "init", "-q"], cwd=str(copia), check=True, timeout=30,
                       env=dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1"))

        def ignorato(path: str) -> bool:
            return subprocess.run(["git", "check-ignore", "-q", "--no-index", path], cwd=str(copia),
                                  timeout=30).returncode == 0
        for path in ("skills/dafare/.claude-plugin/types/claude-code/index.d.ts", "skills/dafare/tsconfig.json"):
            assert ignorato(path), f"U09 .gitignore non esclude {path}: /fine lo committerebbe"
        for path in ("skills/dafare/hooks/register.tsx", "skills/dafare/hooks/verbi.mjs",
                     "skills/dafare/.claude-plugin/plugin.json", "skills/dafare/types/index.d.ts"):
            assert not ignorato(path), f"U09 .gitignore esclude {path}, che è del mod"


# Quello che il diff di /aggiorna deve mostrare: ogni file del codice che gira da solo, anche in
# cartelle che la copia locale non ha ancora (un mod nuovo, gli script di una skill nuova).
DIFF_ATTESI = ("hooks/guardia.py", "settings.json", "skills/todo/scripts/vecchio.py", "skills/nuova/scripts/nuovo.sh",
               "bin/arturo", "skills/dafare/hooks/register.tsx", "skills/dafare/hooks/hooks.json",
               "skills/dafare/.claude-plugin/plugin.json")


def diff_di_aggiorna(repo: Path) -> dict:
    """Lancia la riga del diff di commands/aggiorna.md in un clone fermo alla base, con bash e
    (se c'è) con zsh, la shell di default su macOS. Ritorna, per shell, i file che il diff mostra."""
    righe = [r for r in read(repo / "commands" / "aggiorna.md").splitlines() if r.startswith('git diff "HEAD...$SRC/main"')]
    assert len(righe) == 1, f"il diff del Passo 1 di /aggiorna: {righe}"
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        env = dict(os.environ, HOME=str(base), GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
                   GIT_AUTHOR_NAME="Prova", GIT_AUTHOR_EMAIL="prova@example.invalid",
                   GIT_COMMITTER_NAME="Prova", GIT_COMMITTER_EMAIL="prova@example.invalid")

        def git(cwd: Path, *argomenti: str) -> None:
            subprocess.run(["git", *argomenti], cwd=str(cwd), env=env, check=True, capture_output=True, timeout=60)

        def scrivi(radice: Path, nomi: tuple) -> None:
            for nome in nomi:
                (radice / nome).parent.mkdir(parents=True, exist_ok=True)
                (radice / nome).write_text(f"{nome} {len(nomi)}\n", encoding="utf-8")

        remoto, locale = base / "remoto", base / "locale"
        remoto.mkdir()
        git(remoto, "init", "-q", "-b", "main")
        scrivi(remoto, ("hooks/guardia.py", "settings.json", "skills/todo/scripts/vecchio.py", "bin/arturo",
                        "skills/todo/SKILL.md"))
        git(remoto, "add", "-A")
        git(remoto, "commit", "-q", "-m", "base")
        git(base, "clone", "-q", str(remoto), str(locale))
        scrivi(remoto, DIFF_ATTESI)
        git(remoto, "add", "-A")
        git(remoto, "commit", "-q", "-m", "aggiornamento")
        git(locale, "fetch", "-q", "origin")
        visti = {}
        for shell in [x for x in ("bash", "zsh") if shutil.which(x)]:
            r = subprocess.run([shell, "-c", "SRC=origin\n" + righe[0]], cwd=str(locale), env=env,
                               capture_output=True, timeout=60)
            uscita = r.stdout.decode("utf-8", "replace")
            visti[shell] = set(re.findall(r"^diff --git a/(\S+) ", uscita, re.M))
        return visti


def test_u10(repo: Path) -> None:
    aggiorna = read(repo / "commands" / "aggiorna.md")
    visti = diff_di_aggiorna(repo)
    assert "bash" in visti, "U10 bash mancante: il diff di /aggiorna non si prova"
    for shell, file in visti.items():
        mancano = [f for f in DIFF_ATTESI if f not in file]
        assert not mancano, f"U10 con {shell} il diff di /aggiorna non mostra {mancano} (mostra {sorted(file)})"
    assert "`/dafare`" in aggiorna, "U10 /aggiorna non dice che il pannello è codice che gira da solo"


def sezione(testo: str, titolo: str) -> str:
    m = re.search(rf"^{re.escape(titolo)}\n(.*?)(?=^## |\Z)", testo, re.M | re.S)
    assert m, f"sezione {titolo!r} mancante"
    return m.group(1)


def controllo_del_mod(testo: str, dove: str) -> None:
    """Il modello non vede i comandi di un mod: la skill todo e /inizio sanno se il pannello c'è da
    `claude plugin list --json`. La riga si lancia davvero su tre liste finte."""
    righe = [r.strip() for r in testo.splitlines() if r.strip().startswith("claude plugin list --json")]
    assert len(righe) == 1, f"U11 {dove}: il controllo del pannello con claude plugin list --json: {righe}"
    attesi = (('[{"id": "dafare@skills-dir", "enabled": true}]', "mod caricato"),
              ('[{"id": "dafare@skills-dir", "enabled": false}]', "mod assente"),
              ('[{"id": "altro@skills-dir", "enabled": true}]', "mod assente"))
    with tempfile.TemporaryDirectory() as tmp:
        for lista, atteso in attesi:
            finta = Path(tmp) / "lista.json"
            finta.write_text(lista, encoding="utf-8")
            riga = righe[0].replace("claude plugin list --json", f'cat "{finta}"', 1)
            r = subprocess.run(["bash", "-c", riga], capture_output=True, timeout=30)
            uscita = r.stdout.decode("utf-8", "replace").strip()
            assert uscita == atteso, f"U11 {dove}: con {lista} il controllo stampa {uscita!r}, atteso {atteso!r}"


def test_u11(repo: Path) -> None:
    skill = read(repo / "skills" / "todo" / "SKILL.md")
    assert "/dafare" in skill, "U11 la skill todo non nomina /dafare"
    assert "compare fra i comandi" not in skill, \
        "U11 la skill todo cerca /dafare fra i comandi che vede: il modello non vede i comandi di un mod"
    controllo_del_mod(skill, "skills/todo/SKILL.md")
    inizio = read(repo / "commands" / "inizio.md")
    todo = sezione(inizio, "## Todo")
    assert "/dafare" in todo, "U11 /inizio non nomina /dafare"
    for riga in [r for r in todo.splitlines() if "/dafare" in r]:
        prima = todo.splitlines()[todo.splitlines().index(riga) - 1]
        assert "[solo se" in riga or "[solo se" in prima, f"U11 /inizio propone /dafare senza condizione: {riga!r}"
    controllo_del_mod(sezione(inizio, "## FASE 4: Carica i Todo con Cross-Reference"), "commands/inizio.md FASE 4")
    assert "/dafare" in read(repo / "README.md"), "U11 il README non nomina /dafare"
    novita = read(repo / "NOVITA.md")
    prima = re.search(r"^## .*$", novita, re.M)
    assert prima and prima.group(0) == "## 2026-10-03 — Il pannello delle cose da fare", f"U11 la entry in cima a NOVITA: {prima}"
    entry = sezione(novita, prima.group(0))
    assert "/dafare" in entry and "<!-- Nota dell'autore: la scrive Federico prima del rilascio su main. -->" in entry, \
        "U11 la entry di NOVITA non nomina /dafare o non ha il segnaposto della nota dell'autore"
    referente = read(repo / "docs" / "referente.md")
    for parola in ("skills-dir", "strictKnownMarketplaces", "blockedMarketplaces", "dafare@skills-dir"):
        assert parola in referente, f"U11 docs/referente.md non dice {parola}"
    setup = read(repo / "commands" / "setup.md")
    assert "2.1.287" in setup and "claude --version" in setup, "U11 /setup non controlla la versione di Claude Code"
    diagnosi = read(repo / "commands" / "diagnosi.md")
    assert "claude plugin list --json" in diagnosi and "dafare@skills-dir" in diagnosi and "claude --version" in diagnosi, \
        "U11 /diagnosi non controlla il mod caricato e la versione"


def test_u12(repo: Path) -> None:
    readme = read(repo / "README.md")
    vere = len([d for d in (repo / "skills").iterdir() if (d / "SKILL.md").is_file()])
    scritti = re.findall(r"\*\*(\d+) skill\*\*", readme) + re.findall(r"^skills/\s+(\d+) skill", readme, re.M)
    assert scritti and all(int(n) == vere for n in scritti), f"U12 il README dice {scritti} skill, ce ne sono {vere}"
    paragrafi = [p for p in readme.split("\n\n") if ".claude-plugin/plugin.json" in p and "skills/dafare/" in p]
    assert paragrafi and "mod" in paragrafi[0] and "non una skill" in paragrafi[0], \
        "U12 il README non spiega che una cartella con .claude-plugin/plugin.json è un mod"


def test_u13(repo: Path) -> None:
    m = mod(repo)
    exe = claude()
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        home = casa_con_sentinella(base)
        for argv in ([exe, "plugin", "validate", str(m)], [exe, "plugin", "test", str(m)]):
            r = lancia(argv, home, base, timeout=300)
            assert r.returncode == 0, f"U13 {' '.join(argv[1:3])} senza rete e senza accesso: rc={r.returncode} {(r.stdout + r.stderr)[-500:]}"
            nati = sorted(p.name for p in home.iterdir() if p.name in ("SESSIONE", "PROMPT"))
            assert not nati, f"U13 {' '.join(argv[1:3])} esegue gli hook di sessione: {nati}"
        # Controllo positivo: una sessione vera nella stessa HOME fa scattare la sentinella...
        copia_mod(m, home / ".claude" / "skills" / "dafare")
        shutil.copytree(str(repo / "bin"), str(home / ".claude" / "bin"))
        r = lancia([exe, "-p", "/dafare mostra"], home, base, timeout=120)
        assert (home / "SESSIONE").exists(), f"U13 la sentinella non scatta nemmeno con claude -p: la prova non vale ({r.stdout[-300:]})"
        # ...e la HOME di prova non ha un accesso: validate e test qui sopra non lo usano.
        r = lancia([exe, "-p", "rispondi ok"], home, base, timeout=60)
        assert "login" in (r.stdout + r.stderr).lower(), \
            f"U13 la HOME di prova ha un accesso: la prova «senza login» non vale ({(r.stdout + r.stderr)[-300:]})"


TESTS = {
    "U01": test_u01, "U02": test_u02, "U03": test_u03, "U04": test_u04, "U05": test_u05, "U06": test_u06,
    "U07": test_u07, "U08": test_u08, "U09": test_u09, "U10": test_u10, "U11": test_u11, "U12": test_u12,
    "U13": test_u13,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    parser.add_argument("--solo", nargs="+", choices=list(TESTS), help="solo questi controlli (per i veleni)")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.solo:
        for nome in args.solo:
            TESTS[nome](repo)
        print(f"PASS {','.join(args.solo)} controlli={len(args.solo)} (solo)")
        return 0
    if args.baseline_ref:
        failed = []
        for name, test in TESTS.items():
            try:
                test(repo)
            except (AssertionError, OSError, ValueError, KeyError, IndexError, AttributeError, ImportError,
                    json.JSONDecodeError, subprocess.SubprocessError):
                failed.append(name)
        assert failed == list(TESTS), f"baseline non discriminante: falliscono solo {failed} su {list(TESTS)}"
        print(f"BASELINE_DISCRIMINANTE={','.join(failed)}")
        return 0
    for test in TESTS.values():
        test(repo)
    print(f"PASS {','.join(TESTS)} controlli={len(TESTS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
