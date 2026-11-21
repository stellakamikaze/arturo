#!/usr/bin/env python3
"""RL01-RL07: le skill di ruolo (strati F6, #4536, docs/strati.md).

RL01 quando il modello chiama una skill di Arturo col tool Skill (anche come `arturo:<nome>`),
     hooks/estensione-skill.py mette nel contesto ~/.claude/personale/<nome>.md;
RL02 l'hook tace senza file personale, su una skill che non è di Arturo, su un altro plugin e su un
     nome con `..` o una barra;
RL03 l'hook tace su una skill che legge da sola il suo file personale (humanizer): niente doppioni;
RL04 un file personale lungo si taglia a LIMITE caratteri e il messaggio manda al file;
RL05 settings.json registra l'hook su PostToolUse col matcher Skill, e il plugin lo porta in hooks.json
     col percorso del plugin;
RL06 bin/ruoli.py: le skill di Arturo col ruolo (monitor, system-audit, fine) entrano; una skill
     dell'Orsa con lo stesso nome eredita il ruolo, una che il modello non può chiamare lo toglie, una
     sua col proprio `ruolo:` entra;
RL07 l'avvio stampa la riga RUOLI con il triage verso monitor;
RL08 ogni file di tests/scelta-skill/ ha almeno 30 prove, un quarto da non chiamare, e nomina una skill
     che dichiara il suo ruolo; tests/scelta_skill.py legge dallo stream-json solo le chiamate al tool Skill.
     Il banco vero sul modello (tests/scelta_skill.py) costa sessioni e non sta nel gate.
RL09 una skill della persona (21/11/2026, #6277): l'hook la segna in data/correzioni/<sessione>.skill e, se
     ha "## Finito quando", mette nel contesto quella lista e "## Attrezzi", non il resto del corpo. Con
     --prompt fa lo stesso per /<nome> scritto a mano, e inject-now.sh lo lancia. Col clone una skill di
     Arturo non risulta della persona. Un id di sessione con un percorso non scrive niente.

Sulla base 0c1daea ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
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

BASH = shutil.which("bash") or "bash"


def casa() -> Path:
    radice = Path(tempfile.mkdtemp(prefix="arturo-ruoli.")) / ".claude"
    (radice / "personale").mkdir(parents=True)
    return radice


def ambiente(radice: Path) -> dict:
    env = dict(os.environ)
    env.update(HOME=str(radice.parent), USERPROFILE=str(radice.parent), CLAUDE_CONFIG_DIR=str(radice),
               PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8", ARTURO_TELEMETRIA="0",
               ARTURO_AGGIORNAMENTI="manuali", GIT_TERMINAL_PROMPT="0")
    env.pop("CLAUDE_ENV_FILE", None)
    return env


def hook(repo: Path, radice: Path, codice: str, skill) -> str:
    script = repo / "hooks" / "estensione-skill.py"
    assert script.is_file(), f"{codice} manca hooks/estensione-skill.py"
    dati = {"tool_name": "Skill", "tool_input": {"skill": skill}, "session_id": "s", "cwd": str(radice)}
    r = subprocess.run([sys.executable, str(script)], input=json.dumps(dati), env=ambiente(radice),
                       capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert r.returncode == 0, f"{codice} l'hook esce {r.returncode}: {r.stderr!r}"
    return r.stdout


def contesto(uscita: str, codice: str) -> str:
    assert uscita.strip(), f"{codice} l'hook non dice niente"
    dati = json.loads(uscita)
    specifico = dati.get("hookSpecificOutput") or {}
    assert specifico.get("hookEventName") == "PostToolUse", f"{codice} evento sbagliato: {uscita[:200]}"
    return specifico.get("additionalContext") or ""


def pulisci(radice: Path) -> None:
    shutil.rmtree(radice.parent, ignore_errors=True)


def test_rl01(repo: Path) -> None:
    radice = casa()
    try:
        (radice / "personale" / "monitor.md").write_text("Leggi anche la PEC dello studio.\n", encoding="utf-8")
        for nome in ("monitor", "arturo:monitor"):
            testo = contesto(hook(repo, radice, "RL01", nome), "RL01")
            assert "Leggi anche la PEC dello studio." in testo, f"RL01 {nome}: manca il testo personale: {testo[:200]!r}"
            assert "personale/monitor.md" in testo, f"RL01 {nome}: il messaggio non nomina il file"
    finally:
        pulisci(radice)


def test_rl02(repo: Path) -> None:
    radice = casa()
    try:
        assert hook(repo, radice, "RL02", "monitor") == "", "RL02 parla senza file personale"
        (radice / "personale" / "mia-skill.md").write_text("x\n", encoding="utf-8")
        (radice / "personale" / "monitor.md").write_text("x\n", encoding="utf-8")
        for nome in ("mia-skill", "altro-plugin:monitor", "../personale/monitor", "monitor/../monitor", 42):
            assert hook(repo, radice, "RL02", nome) == "", f"RL02 parla su {nome!r}"
    finally:
        pulisci(radice)


def test_rl03(repo: Path) -> None:
    radice = casa()
    try:
        assert (repo / "hooks" / "estensione-skill.py").is_file(), "RL03 manca hooks/estensione-skill.py"
        corpo = (repo / "skills" / "humanizer" / "SKILL.md").read_text(encoding="utf-8")
        assert "personale/humanizer.md" in corpo, "RL03 la skill humanizer non legge più il suo file: caso da rifare"
        (radice / "personale" / "humanizer.md").write_text("## I miei testi\n", encoding="utf-8")
        assert hook(repo, radice, "RL03", "humanizer") == "", "RL03 ripete il file che humanizer legge già"
    finally:
        pulisci(radice)


def test_rl04(repo: Path) -> None:
    radice = casa()
    try:
        (radice / "personale" / "todo.md").write_text("A" * 20000 + "FINE-NASCOSTA", encoding="utf-8")
        testo = contesto(hook(repo, radice, "RL04", "todo"), "RL04")
        assert "FINE-NASCOSTA" not in testo and len(testo) < 8000, f"RL04 non taglia: {len(testo)} caratteri"
        assert "Il resto è nel file" in testo, "RL04 il testo tagliato non manda al file"
    finally:
        pulisci(radice)


def test_rl05(repo: Path) -> None:
    settings = json.loads((repo / "settings.json").read_text(encoding="utf-8"))
    voci = [h.get("command", "") for e in settings["hooks"].get("PostToolUse", [])
            if e.get("matcher") == "Skill" for h in e.get("hooks", [])]
    assert any("estensione-skill.py" in c for c in voci), f"RL05 settings.json non registra l'hook su Skill: {voci}"
    sys.path.insert(0, str(repo / "bin"))
    try:
        spec = importlib.util.spec_from_file_location("impacchetta_rl05", repo / "bin" / "impacchetta.py")
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
    finally:
        sys.path.pop(0)
    plugin = modulo.hooks_json(settings)
    comandi = [h.get("command", "") for e in plugin["hooks"]["PostToolUse"] if e.get("matcher") == "Skill"
               for h in e.get("hooks", [])]
    assert any("${CLAUDE_PLUGIN_ROOT}/hooks/estensione-skill.py" in c for c in comandi), \
        f"RL05 il plugin non porta l'hook col suo percorso: {comandi}"


def ruoli(repo: Path, radice: Path, codice: str) -> dict:
    script = repo / "bin" / "ruoli.py"
    assert script.is_file(), f"{codice} manca bin/ruoli.py"
    r = subprocess.run([sys.executable, str(script), "elenco"], env=ambiente(radice), capture_output=True,
                       text=True, encoding="utf-8", timeout=30)
    assert r.returncode == 0, f"{codice} ruoli.py esce {r.returncode}: {r.stderr!r}"
    return {riga.split("\t")[0]: riga.split("\t")[1:] for riga in r.stdout.splitlines() if riga.strip()}


def skill(radice: Path, nome: str, testa: str) -> None:
    cartella = radice / "skills" / nome
    cartella.mkdir(parents=True)
    (cartella / "SKILL.md").write_text(f"---\nname: {nome}\n{testa}---\n\n# {nome}\n", encoding="utf-8")


def test_rl06(repo: Path) -> None:
    radice = casa()
    try:
        vuota = ruoli(repo, radice, "RL06")
        for nome in ("monitor", "system-audit", "fine"):
            assert nome in vuota and vuota[nome][1] == "arturo", f"RL06 manca il ruolo di {nome}: {vuota}"
        skill(radice, "monitor", "description: il mio monitor\n")
        skill(radice, "system-audit", "description: x\ndisable-model-invocation: true\n")
        skill(radice, "posta", "description: la mia posta\nruolo: scrivere le email di lavoro\n")
        con = ruoli(repo, radice, "RL06")
        assert con.get("monitor", [None, None])[1] == "orsa" and con["monitor"][0] == vuota["monitor"][0], \
            f"RL06 il monitor della persona non eredita il ruolo: {con.get('monitor')}"
        assert "system-audit" not in con, "RL06 una skill che il modello non può chiamare resta nella mappa"
        assert con.get("posta") == ["scrivere le email di lavoro", "orsa"], f"RL06 manca il ruolo della persona: {con}"
    finally:
        pulisci(radice)


def test_rl07(repo: Path) -> None:
    radice = casa()
    try:
        progetto = radice.parent / "progetto"
        progetto.mkdir()
        r = subprocess.run([BASH, str(repo / "hooks" / "session-start.sh")], input="{}", cwd=progetto,
                           env=ambiente(radice), capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=120)
        righe = [x for x in r.stdout.splitlines() if x.startswith("RUOLI:")]
        assert len(righe) == 1, f"RL07 l'avvio non stampa una riga RUOLI: {r.stdout[-400:]!r}"
        assert "→ monitor" in righe[0] and "→ fine" in righe[0], f"RL07 la riga RUOLI non porta i ruoli: {righe[0]}"
    finally:
        pulisci(radice)


def test_rl08(repo: Path) -> None:
    script = repo / "tests" / "scelta_skill.py"
    assert script.is_file(), "RL08 manca tests/scelta_skill.py"
    file = sorted((repo / "tests" / "scelta-skill").glob("*.json"))
    assert any(f.stem == "monitor" for f in file), "RL08 manca tests/scelta-skill/monitor.json"
    for f in file:
        dati = json.loads(f.read_text(encoding="utf-8"))
        prove = dati.get("prove") or []
        falsi = [p for p in prove if p.get("atteso") is False]
        assert dati.get("skill") == f.stem, f"RL08 {f.name}: il campo skill non è {f.stem}"
        assert len(prove) >= 30 and len(falsi) >= len(prove) // 4, \
            f"RL08 {f.name}: servono almeno 30 prove, un quarto da non chiamare ({len(prove)}, {len(falsi)})"
        corpo = repo / "skills" / f.stem / "SKILL.md"
        assert corpo.is_file() and "\nruolo:" in corpo.read_text(encoding="utf-8"), \
            f"RL08 {f.name}: la skill non c'è o non dichiara il suo ruolo"
    spec = importlib.util.spec_from_file_location("scelta_rl08", script)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    stream = "\n".join(json.dumps(e) for e in (
        {"type": "system", "subtype": "init", "skills": ["arturo:monitor"]},
        {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Skill",
                                                       "input": {"skill": "arturo:prompt-master"}}]}},
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "Skill monitor"},
                                                      {"type": "tool_use", "name": "Skill", "input": {"skill": "/monitor"}}]}},
        {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Read", "input": {"skill": "todo"}}]}},
    )) + "\nriga non json"
    assert modulo.skill_chiamate(stream) == ["arturo:prompt-master", "monitor"], \
        f"RL08 lettura delle chiamate sbagliata: {modulo.skill_chiamate(stream)}"


LETTERA = ("---\nname: lettera-cliente\ndescription: la lettera al cliente\n---\n\n# Lettera\n\n"
           "## Cosa fare\nScrivi la lettera.\n\n"
           "## Finito quando\n- Il saluto è Gentile: sì o no\n- La lettera sta in una pagina: sì o no\n\n"
           "## Attrezzi\n- `modello.docx`: il modello della carta intestata\n\n"
           "## Cosa non fare\n- RIGA-FUORI-LISTA\n")


def apre(script: Path, radice: Path, codice: str, dati: dict, *argomenti: str) -> str:
    assert script.is_file(), f"{codice} manca hooks/estensione-skill.py"
    r = subprocess.run([sys.executable, str(script), *argomenti], input=json.dumps(dati), env=ambiente(radice),
                       capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert r.returncode == 0, f"{codice} l'hook esce {r.returncode}: {r.stderr!r}"
    return r.stdout


def in_uso(radice: Path, sessione: str) -> str:
    file = radice / "data" / "correzioni" / f"{sessione}.skill"
    return file.read_text(encoding="utf-8").strip() if file.is_file() else ""


def test_rl09(repo: Path) -> None:
    script = repo / "hooks" / "estensione-skill.py"
    radice = casa()
    try:
        skill(radice, "lettera-cliente", "description: x\n")
        (radice / "skills" / "lettera-cliente" / "SKILL.md").write_text(LETTERA, encoding="utf-8")
        skill(radice, "senza-lista", "description: una skill vecchia\n")
        chiamata = {"tool_name": "Skill", "tool_input": {"skill": "lettera-cliente"}, "session_id": "s-uno"}
        testo = contesto(apre(script, radice, "RL09", chiamata), "RL09")
        for pezzo in ("FINITO QUANDO", "lettera-cliente", "Il saluto è Gentile", "sta in una pagina", "ATTREZZI",
                      "modello.docx"):
            assert pezzo in testo, f"RL09 il promemoria della skill della persona non dice {pezzo!r}: {testo[:300]!r}"
        assert "RIGA-FUORI-LISTA" not in testo and "Scrivi la lettera" not in testo, \
            f"RL09 il promemoria ripete il corpo della skill: {testo[:400]!r}"
        assert in_uso(radice, "s-uno") == "lettera-cliente", "RL09 la skill in uso non è segnata nella sessione"
        # Una skill senza la lista: segnata, nessun promemoria.
        chiamata = {"tool_name": "Skill", "tool_input": {"skill": "senza-lista"}, "session_id": "s-uno"}
        assert apre(script, radice, "RL09", chiamata) == "", "RL09 parla per una skill senza Finito quando"
        assert in_uso(radice, "s-uno") == "senza-lista", "RL09 vale la prima skill aperta, non l'ultima"
        # Una skill scritta a mano con /<nome>: testo semplice, anche attraverso inject-now.sh.
        scritta = {"prompt": "/lettera-cliente per la signora Rossi", "session_id": "s-due"}
        testo = apre(script, radice, "RL09", scritta, "--prompt")
        assert testo.startswith("FINITO QUANDO") and "Il saluto è Gentile" in testo, \
            f"RL09 con --prompt il promemoria non esce come testo: {testo[:200]!r}"
        assert in_uso(radice, "s-due") == "lettera-cliente", "RL09 la skill scritta a mano non è segnata"
        assert apre(script, radice, "RL09", {"prompt": "scrivi /lettera-cliente", "session_id": "s-tre"},
                    "--prompt") == "" and not in_uso(radice, "s-tre"), "RL09 un nome in mezzo al messaggio apre la skill"
        r = subprocess.run([BASH, str(repo / "hooks" / "inject-now.sh")], input=json.dumps(scritta),
                           env=ambiente(radice), capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=60)
        assert "FINITO QUANDO" in r.stdout and "Il saluto è Gentile" in r.stdout, \
            f"RL09 inject-now.sh non porta il promemoria di una skill scritta a mano: {r.stdout[-300:]!r}"
        # Un id di sessione con un percorso non scrive niente.
        chiamata = {"tool_name": "Skill", "tool_input": {"skill": "lettera-cliente"}, "session_id": "../../fuori"}
        apre(script, radice, "RL09", chiamata)
        assert not list(radice.parent.rglob("fuori.skill")), "RL09 un id di sessione con percorso scrive un file"
        # Col clone le skill di Arturo e quelle della persona stanno nella stessa cartella: decide il nome.
        for cartella in ("hooks", "bin", "skills"):
            shutil.copytree(repo / cartella, radice / cartella, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns("__pycache__"))
        clone = radice / "hooks" / "estensione-skill.py"
        chiamata = {"tool_name": "Skill", "tool_input": {"skill": "lettera-cliente"}, "session_id": "s-clone"}
        assert "FINITO QUANDO" in contesto(apre(clone, radice, "RL09", chiamata), "RL09"), \
            "RL09 col clone la skill della persona non riceve il promemoria"
        assert "## Finito quando" in (radice / "skills" / "todo" / "SKILL.md").read_text(encoding="utf-8"), \
            "RL09 la skill todo non ha più Finito quando: caso da rifare"
        chiamata = {"tool_name": "Skill", "tool_input": {"skill": "todo"}, "session_id": "s-clone"}
        assert "FINITO QUANDO" not in apre(clone, radice, "RL09", chiamata), \
            "RL09 col clone una skill di Arturo riceve il promemoria della persona"
        assert in_uso(radice, "s-clone") == "lettera-cliente", "RL09 col clone una skill di Arturo risulta della persona"
    finally:
        pulisci(radice)


TESTS = {"RL01": test_rl01, "RL02": test_rl02, "RL03": test_rl03, "RL04": test_rl04, "RL05": test_rl05,
         "RL06": test_rl06, "RL07": test_rl07, "RL08": test_rl08, "RL09": test_rl09}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
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
            except Exception as e:  # noqa: BLE001
                altro.append(f"{nome}: {type(e).__name__} {e}")
        assert not altro and len(rossi) == len(TESTS), \
            "baseline non discriminante: ogni controllo deve fallire col suo codice.\n" + "\n".join(altro + rossi)
        print(f"BASELINE_DISCRIMINANTE={','.join(r.split(':')[0] for r in rossi)}")
        return 0
    for test in TESTS.values():
        test(repo)
    print(f"PASS {','.join(TESTS)} controlli={len(TESTS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
