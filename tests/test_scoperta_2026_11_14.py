#!/usr/bin/env python3
"""La Scoperta v1 (piano del 14/11/2026, passo S7): proposte dalle versioni dei file.

SC01 etichette: i campi cambiati si leggono da una tabella, da "Campo: valore" e dai titoli markdown;
     le cifre diventano #; in uno script un "#" è un commento, non un titolo.
SC02 cadenza: cinque giorni a una settimana l'uno dall'altro hanno un ritmo; tre giorni in dieci no;
     lo stesso giorno della settimana per quattro volte dà il nome del giorno.
SC03 analizza --json, da transcript finti e file-history: la versione 1 sta solo su disco, il percorso
     relativo vale dalla cartella che compare dopo l'istantanea, e un worktree conta come il repository.
     Esce la cadenza di report.md con i campi "stato" e "data", le date delle cinque volte e la famiglia
     fattura-N.md come file nuovi; diario.md cresce di una voce a settimana, con le voci "umore" e "fatto"
     e senza il titolo che la contiene.
SC04 esclusioni: un handoff di Arturo non entra mai; dopo `escludi` la cartella del report sparisce.
SC05 proponi: blocco SCOPERTA con prove e bozza; una sola proposta per sessione (la seconda chiamata
     esce con 3) e due nei sette giorni (la terza sessione esce con 3).
SC06 rispondi no: la proposta non torna più, anche con i limiti liberi.
SC07 rispondi si, creata, annulla: la skill esce da skills/ e resta in data/scoperta/annullate/.
SC08 l'hook scoperta-indice.py: una riga con campi e righe cambiate, mai il testo; un file escluso non
     entra; un ingresso rotto esce con 0 e senza parlare.
SC09 impronta e confronta: un file cambiato a mano entra in manuali.jsonl coi campi; uno che Claude ha
     toccato (l'indice lo dice) no; rilanciato, confronta non raddoppia. Un'impronta di più di 14 giorni
     sparisce con la copia che usava solo lei.
SC10 i collegamenti: settings.json registra l'hook su Edit e Write, bin/arturo ha il comando, /inizio
     prende l'impronta, /fine confronta sempre e propone solo fuori dal Modo rotazione.

Sulla base 31ee9e7 (dev prima della Scoperta) sono rossi tutti i casi: bin/scoperta.py non c'è. Con
--avvelena una copia del repository rotta in un punto alla volta deve far fallire i casi che lo sorvegliano.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CASI = ["SC01", "SC02", "SC03", "SC04", "SC05", "SC06", "SC07", "SC08", "SC09", "SC10"]
PERCORSI = ["bin", "hooks/radici.py", "hooks/scoperta-indice.py", "settings.json", "commands/fine.md",
            "commands/inizio.md"]
VELENI = [
    (["SC01"], "bin/scoperta.py", '            nome = re.sub(r"\\d+", "#", nome)\n', ""),
    (["SC02"], "bin/scoperta.py", "    if regolari / len(intervalli) < 0.75:", "    if regolari / len(intervalli) < 2:"),
    (["SC03"], "bin/scoperta.py", '        uno = storia / sessione / f"{impronta_}@v1"', '        uno = storia / sessione / f"{impronta_}@v0"'),
    (["SC03"], "bin/scoperta.py", 'return re.sub(r"/\\.claude/worktrees/[^/]+(?=/|$)", "", p)', "return p"),
    (["SC03"], "bin/scoperta.py", "v.piu >= 3 * max(1, v.meno)", "v.piu >= 30 * max(1, v.meno)"),
    (["SC04"], "bin/scoperta.py", '"~/.claude/data/handoffs/*/HANDOFF_*", ', ""),
    (["SC05"], "bin/scoperta.py", "PER_SESSIONE = 1", "PER_SESSIONE = 5"),
    (["SC05"], "bin/scoperta.py", "PER_SETTIMANA = 2", "PER_SETTIMANA = 9"),
    (["SC06"], "bin/scoperta.py", '        if c["id"] in proposte:\n            continue', '        if False:\n            continue'),
    (["SC07"], "bin/scoperta.py", "        shutil.move(str(sorgente), str(destinazione / sorgente.name))",
     "        shutil.copytree(str(sorgente), str(destinazione / sorgente.name))"),
    (["SC08"], "hooks/scoperta-indice.py", '"campi": campi[:6]}', '"campi": campi[:6], "testo": coppie}'),
    (["SC09"], "bin/scoperta.py", "        if percorso in claude or escluso(percorso, modelli):",
     "        if escluso(percorso, modelli):"),
    (["SC09"], "bin/scoperta.py", '    tenute = [r for r in _righe(file_manuali) if r.get("sessione") != sessione]',
     "    tenute = list(_righe(file_manuali))"),
    (["SC09"], "bin/scoperta.py", "    pulisci_impronte()\n", ""),
    (["SC10"], "commands/fine.md", "Fuori dal Modo rotazione lancia poi", "Lancia poi"),
]

REPORT_0 = "# Report settimanale\n\n| Campo | Valore |\n|---|---|\n| Stato | verde |\n| Data | 1/9 |\n\nNote fisse.\n"


def _report(n: int) -> str:
    return REPORT_0.replace("| Stato | verde |", f"| Stato | giro {n} |").replace("| Data | 1/9 |", f"| Data | {n}/10 |")


class Lab:
    def __init__(self, repo: Path, tmp: Path):
        self.home = tmp / "home"
        self.cl = self.home / ".claude"
        self.cl.mkdir(parents=True)
        for rel in PERCORSI:
            sorgente = repo / rel
            if not sorgente.exists():
                continue
            if sorgente.is_dir():
                shutil.copytree(str(sorgente), str(self.cl / rel), ignore=shutil.ignore_patterns("__pycache__"))
            else:
                (self.cl / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(sorgente), str(self.cl / rel))
        self.lavoro = self.home / "Documents" / "Lavoro"
        self.lavoro.mkdir(parents=True)
        self.ambiente = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home), ARTURO_TELEMETRIA="0",
                             PYTHONDONTWRITEBYTECODE="1", CLAUDE_CODE_SESSION_ID="sessione-prova-01")
        self.ambiente.pop("CLAUDE_CONFIG_DIR", None)
        self.n = 0

    def lancia(self, *a: str, entrata: str | None = None, sessione: str | None = None) -> subprocess.CompletedProcess:
        env = dict(self.ambiente)
        if sessione:
            env["CLAUDE_CODE_SESSION_ID"] = sessione
        return subprocess.run([sys.executable, "-B", *a], capture_output=True, text=True, encoding="utf-8",
                              errors="replace", env=env, timeout=120, input=entrata, cwd=str(self.home))

    def scoperta(self, *a: str, sessione: str | None = None) -> subprocess.CompletedProcess:
        return self.lancia(str(self.cl / "bin" / "arturo"), "scoperta", *a, sessione=sessione)

    def sessione(self, quando: dt.datetime, file: dict, cwd: Path, relativi: bool = False) -> str:
        """Un transcript con le istantanee e la versione 1 di ogni file su disco. `file`: percorso ->
        contenuto prima delle modifiche (None se il file non c'era)."""
        self.n += 1
        sid = f"sessione-finta-{self.n:02d}"
        cartella = self.cl / "projects" / "-finto"
        cartella.mkdir(parents=True, exist_ok=True)
        storia = self.cl / "file-history" / sid
        storia.mkdir(parents=True, exist_ok=True)
        copie = {}
        for i, (percorso, prima) in enumerate(file.items()):
            impronta = f"{self.n:02d}{i:02d}abcdef012345"
            chiave = os.path.relpath(percorso, cwd) if relativi else str(percorso)
            # La versione 1 sta solo su disco; il transcript nomina la 2, come fa Claude Code.
            if prima is not None:
                (storia / f"{impronta}@v1").write_text(prima, encoding="utf-8")
                os.utime(storia / f"{impronta}@v1", (quando.timestamp(), quando.timestamp()))
            # La copia della versione 2 manca, come dopo una pulizia parziale: lo stato iniziale
            # si legge solo dalla versione 1.
            copie[chiave] = {"backupFileName": f"{impronta}@v2" if prima is not None else None, "version": 2,
                             "backupTime": (quando + dt.timedelta(minutes=5)).astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")}
        righe = [{"type": "file-history-snapshot", "messageId": "m1",
                  "snapshot": {"messageId": "m1", "trackedFileBackups": copie, "timestamp": quando.isoformat()},
                  "isSnapshotUpdate": False},
                 {"parentUuid": None, "cwd": str(cwd), "sessionId": sid, "type": "user", "message": {"content": "x"}},
                 {"type": "file-history-snapshot", "messageId": "m2",
                  "snapshot": {"messageId": "m2", "trackedFileBackups": copie, "timestamp": quando.isoformat()},
                  "isSnapshotUpdate": True}]
        (cartella / f"{sid}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in righe), encoding="utf-8")
        return sid

    def popola(self) -> None:
        """Report ogni settimana (stato e data), fattura-N nuova ogni settimana, a.csv e b.md insieme."""
        oggi = dt.datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
        report = self.lavoro / "report.md"
        for k in range(5, 0, -1):
            quando = oggi - dt.timedelta(days=7 * k + 1)
            # Nella terza volta il report si cambia da un worktree: conta come il file del repository.
            percorso = self.lavoro / ".claude" / "worktrees" / "prova" / "report.md" if k == 3 else report
            self.sessione(quando, {percorso: _report(5 - k)}, self.lavoro, relativi=(k == 4))
        report.write_text(_report(5), encoding="utf-8")
        diario, testo = self.home / "Documents" / "Diario" / "diario.md", "# Diario\n"
        diario.parent.mkdir(parents=True)
        for k in range(4, 0, -1):
            self.sessione(oggi - dt.timedelta(days=7 * k + 2), {diario: testo}, diario.parent)
            testo = testo.replace("# Diario\n", f"# Diario\n\n## Settimana {k}\nUmore: buono\nFatto: molto\nNote: {k}\n")
        diario.write_text(testo, encoding="utf-8")
        fatture = self.home / "Documents" / "Fatture"
        fatture.mkdir(parents=True)
        for k, n in ((26, 11), (19, 12), (12, 13), (5, 14)):
            self.sessione(oggi - dt.timedelta(days=k), {fatture / f"fattura-{n}.md": None}, fatture)
            (fatture / f"fattura-{n}.md").write_text(f"Fattura {n}\nImporto: 100\n", encoding="utf-8")
        coppia = self.home / "Documents" / "Coppia"
        coppia.mkdir(parents=True)
        for k in (3, 2, 1):
            self.sessione(oggi - dt.timedelta(days=k, hours=-2),
                          {coppia / "a.csv": f"x,{k}\n", coppia / "b.md": f"riga {k}\n"}, coppia)
        (coppia / "a.csv").write_text("x,0\n", encoding="utf-8")
        (coppia / "b.md").write_text("riga 0\n", encoding="utf-8")
        handoff = self.cl / "data" / "handoffs" / "libro"
        handoff.mkdir(parents=True)
        for k in (21, 14, 7, 1):
            self.sessione(oggi - dt.timedelta(days=k), {handoff / "HANDOFF_2026-01-01.md": "## Stato\nx\n"}, handoff)

    def analizza(self) -> list:
        r = self.scoperta("analizza", "--json")
        return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip().startswith("[") else []


def importa(lab: Lab):
    sys.path.insert(0, str(lab.cl / "bin"))
    sys.path.insert(0, str(lab.cl / "hooks"))
    for nome in ("scoperta", "radici"):
        sys.modules.pop(nome, None)
    try:
        import scoperta  # noqa: E402
        return scoperta
    finally:
        sys.path.pop(0)
        sys.path.pop(0)


def sc01(lab: Lab) -> str:
    s = importa(lab)
    campi, piu, meno = s.etichette(REPORT_0, _report(3))
    if campi[:2] != ["stato", "data"] or (piu, meno) != (2, 2):
        return f"campi della tabella {campi} righe {piu}/{meno}"
    campi, _, _ = s.etichette("# Settimana 46\nTotale: 10\n\n## Spese\nluce\n", "# Settimana 47\nTotale: 12\n\n## Spese\ngas\n")
    if campi != ["§ settimana #", "totale", "§ spese"]:
        return f"titoli e campi {campi}"
    campi, _, _ = s.etichette("# commento\nx=1\n", "# commento\nx=2\n", titoli=False)
    if campi:
        return f"un commento di script letto come titolo: {campi}"
    return ""


def sc02(lab: Lab) -> str:
    s = importa(lab)
    base = dt.date(2026, 9, 2)
    settimane = [base + dt.timedelta(days=d) for d in (0, 8, 13, 22, 28)]
    ritmo = s._cadenza(settimane)
    if not ritmo or ritmo[0] not in ("ogni settimana",):
        return f"cinque volte a una settimana: {ritmo}"
    if s._cadenza([base, base + dt.timedelta(days=4), base + dt.timedelta(days=10)]) is not None:
        return "tre giorni in dieci hanno avuto un ritmo"
    lunedi = [dt.date(2026, 9, 7) + dt.timedelta(days=d) for d in (0, 7, 21, 28, 30)]
    ritmo = s._cadenza(lunedi)
    if not ritmo or ritmo[0] != "il lunedì":
        return f"quattro lunedì su cinque: {ritmo}"
    return ""


def sc03(lab: Lab) -> str:
    lab.popola()
    trovati = lab.analizza()
    report = [c for c in trovati if c["segnale"] == "cadenza" and c["famiglia"].endswith("/Lavoro/report.md")]
    if not report:
        return f"nessuna cadenza per report.md: {[(c['segnale'], c['famiglia'] or c['file']) for c in trovati]}"
    c = report[0]
    if c["volte"] != 5 or c["campi"][:2] != ["stato", "data"]:
        return f"report.md: {c['volte']} volte, campi {c['campi']}"
    if any("worktrees" in p["percorso"] for p in c["prove"]) or len(c["prove"]) != 5:
        return f"prove del report: {[p['percorso'] for p in c['prove']]}"
    fatture = [x for x in trovati if x["famiglia"].endswith("/Fatture/fattura-#.md")]
    if not fatture or fatture[0]["nuovi"] != 4:
        return f"la serie fattura-N: {fatture[:1]}"
    diario = [x for x in trovati if x["famiglia"].endswith("/Diario/diario.md")]
    if not diario or not diario[0]["aggiunta"] or diario[0]["campi"][:2] != ["umore", "fatto"]:
        return f"il diario che cresce: {[(x['aggiunta'], x['campi']) for x in diario]}"
    if c["aggiunta"]:
        return "il report che si aggiorna letto come un file che cresce"
    if not any(x["segnale"] == "insieme" and len(x["file"]) == 2 and x["file"][0].endswith("a.csv") for x in trovati):
        return "a.csv e b.md insieme non trovati"
    return ""


def sc04(lab: Lab) -> str:
    lab.popola()
    trovati = lab.analizza()
    if any("HANDOFF" in (x["famiglia"] or "") for x in trovati):
        return "un handoff di Arturo è entrato fra i candidati"
    r = lab.scoperta("escludi", "~/Documents/Lavoro/*")
    if r.returncode:
        return f"escludi: {r.stderr}"
    if any("/Lavoro/" in (x["famiglia"] or "") for x in lab.analizza()):
        return "la cartella esclusa resta fra i candidati"
    return ""


def sc05(lab: Lab) -> str:
    lab.popola()
    r = lab.scoperta("proponi", sessione="sessione-a-0001")
    if r.returncode != 0 or not r.stdout.startswith("SCOPERTA ") or "Prove:" not in r.stdout or "Bozza della skill:" not in r.stdout:
        return f"prima proposta: rc {r.returncode} {r.stdout[:200]}"
    if "report.md" not in r.stdout:
        return f"la prima proposta non è il report: {r.stdout[:200]}"
    if lab.scoperta("proponi", sessione="sessione-a-0001").returncode != 3:
        return "seconda proposta nella stessa sessione"
    if lab.scoperta("proponi", sessione="sessione-b-0002").returncode != 0:
        return "la seconda sessione non ha la sua proposta"
    if lab.scoperta("proponi", sessione="sessione-c-0003").returncode != 3:
        return "tre proposte in una settimana"
    return ""


def _invecchia(lab: Lab) -> None:
    file = lab.cl / "data" / "scoperta" / "proposte.json"
    dati = json.loads(file.read_text(encoding="utf-8"))
    for voce in dati.values():
        voce["quando"] = "2020-01-01T10:00:00"
    file.write_text(json.dumps(dati), encoding="utf-8")


def sc06(lab: Lab) -> str:
    lab.popola()
    r = lab.scoperta("proponi", sessione="sessione-a-0001")
    ident = r.stdout.split()[1].rstrip(":") if r.returncode == 0 else ""
    if not ident:
        return f"nessuna proposta: {r.stdout} {r.stderr}"
    if lab.scoperta("rispondi", ident, "no").returncode:
        return "rispondi no non riesce"
    for i in range(4):
        _invecchia(lab)
        r = lab.scoperta("proponi", sessione=f"sessione-z-{i:04d}")
        if ident in r.stdout:
            return "la proposta rifiutata è tornata"
    stato = lab.scoperta("stato").stdout
    if "rifiutate 1" not in stato:
        return f"stato: {stato}"
    return ""


def sc07(lab: Lab) -> str:
    lab.popola()
    r = lab.scoperta("proponi", sessione="sessione-a-0001")
    ident = r.stdout.split()[1].rstrip(":") if r.returncode == 0 else ""
    if not ident or lab.scoperta("rispondi", ident, "si").returncode:
        return f"rispondi si: {r.stdout[:120]}"
    skill = lab.cl / "skills" / "aggiorna-report"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: aggiorna-report\n---\n", encoding="utf-8")
    if lab.scoperta("creata", ident, str(skill)).returncode:
        return "creata non registra la skill"
    r = lab.scoperta("annulla", ident)
    copie = list((lab.cl / "data" / "scoperta" / "annullate").glob("*/aggiorna-report/SKILL.md"))
    if r.returncode or skill.exists() or len(copie) != 1:
        return f"annulla: rc {r.returncode}, skill ancora lì {skill.exists()}, copie {len(copie)}"
    if "annullate 1" not in lab.scoperta("stato").stdout:
        return "stato non conta l'annullata"
    return ""


def sc08(lab: Lab) -> str:
    hook = str(lab.cl / "hooks" / "scoperta-indice.py")
    nota = lab.lavoro / "note.md"
    dati = {"session_id": "sessione-hook-01", "tool_name": "Edit", "cwd": str(lab.lavoro),
            "tool_input": {"file_path": str(nota), "old_string": "Stato: bozza segreta\n", "new_string": "Stato: pronta segreta\n"}}
    r = lab.lancia(hook, entrata=json.dumps(dati))
    indice = lab.cl / "data" / "scoperta" / "indice.jsonl"
    if r.returncode or r.stdout or not indice.exists():
        return f"hook: rc {r.returncode} out {r.stdout!r} indice {indice.exists()}"
    righe = [json.loads(x) for x in indice.read_text(encoding="utf-8").splitlines()]
    if len(righe) != 1 or righe[0]["campi"] != ["stato"] or righe[0]["percorso"] != str(nota) or righe[0]["piu"] != 1:
        return f"riga dell'indice: {righe}"
    if "segreta" in indice.read_text(encoding="utf-8"):
        return "il testo della modifica è entrato nell'indice"
    escluso = dict(dati, tool_input=dict(dati["tool_input"], file_path=str(lab.cl / "data" / "memory" / "x.md")))
    lab.lancia(hook, entrata=json.dumps(escluso))
    r = lab.lancia(hook, entrata="{rotto")
    if len(indice.read_text(encoding="utf-8").splitlines()) != 1 or r.returncode or r.stdout or r.stderr:
        return "un file escluso o un ingresso rotto hanno lasciato traccia"
    return ""


def sc09(lab: Lab) -> str:
    progetto = lab.home / "Documents" / "Libro"
    progetto.mkdir(parents=True)
    (progetto / "capitolo.md").write_text("# Uno\nStato: bozza\n", encoding="utf-8")
    (progetto / "indice.md").write_text("Pagine: 10\n", encoding="utf-8")
    sid = "sessione-mano-01"
    vecchia = lab.cl / "data" / "scoperta" / "impronte" / "sessione-vecchia-01.json"
    vecchia.parent.mkdir(parents=True)
    vecchia.write_text(json.dumps({"file": {"/x": "ff" * 32}}), encoding="utf-8")
    os.utime(vecchia, (0, 1_000_000_000))
    copia_vecchia = lab.cl / "data" / "scoperta" / "copie" / "ff" / ("ff" * 32)
    copia_vecchia.parent.mkdir(parents=True)
    copia_vecchia.write_text("vecchio", encoding="utf-8")
    r = lab.lancia(str(lab.cl / "bin" / "arturo"), "scoperta", "impronta", "--cartella", str(progetto), sessione=sid)
    if "impronta di 2 file" not in r.stdout:
        return f"impronta: {r.stdout} {r.stderr}"
    if vecchia.exists() or copia_vecchia.exists():
        return "l'impronta di una sessione di 14 giorni fa e la sua copia sono rimaste"
    (progetto / "capitolo.md").write_text("# Uno\nStato: rivisto\n", encoding="utf-8")
    (progetto / "indice.md").write_text("Pagine: 12\n", encoding="utf-8")
    dati = {"session_id": sid, "tool_name": "Write", "cwd": str(progetto),
            "tool_input": {"file_path": str(progetto / "indice.md"), "content": "Pagine: 12\n"}}
    lab.lancia(str(lab.cl / "hooks" / "scoperta-indice.py"), entrata=json.dumps(dati))
    for _ in range(2):
        r = lab.scoperta("confronta", sessione=sid)
    manuali = lab.cl / "data" / "scoperta" / "manuali.jsonl"
    righe = [json.loads(x) for x in manuali.read_text(encoding="utf-8").splitlines()] if manuali.exists() else []
    if len(righe) != 1 or not righe[0]["percorso"].endswith("capitolo.md") or righe[0]["campi"] != ["stato"]:
        return f"modifiche a mano: {[(x['percorso'], x['campi']) for x in righe]}"
    if "rivisto" not in righe[0]["diff"]:
        return "il diff della modifica a mano manca"
    return ""


def sc10(lab: Lab) -> str:
    impostazioni = json.loads((lab.cl / "settings.json").read_text(encoding="utf-8"))
    registrato = any("scoperta-indice.py" in h.get("command", "") and "Write" in (e.get("matcher") or "")
                     and "Edit" in (e.get("matcher") or "")
                     for e in impostazioni.get("hooks", {}).get("PostToolUse", []) for h in e.get("hooks", []))
    if not registrato:
        return "settings.json non registra scoperta-indice.py su Edit e Write"
    if '"scoperta": ("scoperta"' not in (lab.cl / "bin" / "arturo").read_text(encoding="utf-8"):
        return "bin/arturo non ha il comando scoperta"
    if "arturo scoperta impronta" not in (lab.cl / "commands" / "inizio.md").read_text(encoding="utf-8"):
        return "/inizio non prende l'impronta"
    fine = (lab.cl / "commands" / "fine.md").read_text(encoding="utf-8")
    if "Lancia sempre `python3 ~/.claude/bin/arturo scoperta confronta`" not in fine \
            or "Fuori dal Modo rotazione lancia poi" not in fine:
        return "/fine non confronta sempre o propone anche in rotazione"
    return ""


PROVE = {"SC01": sc01, "SC02": sc02, "SC03": sc03, "SC04": sc04, "SC05": sc05, "SC06": sc06, "SC07": sc07,
         "SC08": sc08, "SC09": sc09, "SC10": sc10}


def prova(repo: Path) -> list:
    assert list(PROVE) == CASI, f"casi {list(PROVE)} diversi dall'elenco {CASI}"
    rossi = []
    for codice, fn in PROVE.items():
        with tempfile.TemporaryDirectory(prefix="arturo-sc-") as tmp:
            try:
                lab = Lab(repo, Path(tmp).resolve())
                esito = fn(lab) if (lab.cl / "bin" / "scoperta.py").exists() else "bin/scoperta.py assente"
            except Exception as e:  # noqa: BLE001 - un caso che si rompe è rosso, non ferma il banco
                esito = f"eccezione {type(e).__name__}: {e}"
        if esito:
            rossi.append(f"{codice} {esito}")
    return rossi


def avvelena(repo: Path) -> int:
    for casi, rel, giusto, rotto in VELENI:
        with tempfile.TemporaryDirectory(prefix="arturo-sc-veleno-") as tmp:
            copia = Path(tmp) / "repo"
            for p in PERCORSI:
                if (repo / p).is_dir():
                    shutil.copytree(str(repo / p), str(copia / p), ignore=shutil.ignore_patterns("__pycache__"))
                else:
                    (copia / p).parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(repo / p), str(copia / p))
            testo = (copia / rel).read_text(encoding="utf-8")
            assert testo.count(giusto) == 1, f"veleno {'+'.join(casi)}: il testo da rompere non c'è più in {rel}"
            (copia / rel).write_text(testo.replace(giusto, rotto), encoding="utf-8")
            codici = [r.split()[0] for r in prova(copia)]
            mancano = [c for c in casi if c not in codici]
            if mancano:
                print(f"VELENO {'+'.join(casi)} NON ATTACCA: rossi {codici}")
                return 1
            print(f"VELENO {'+'.join(casi)} ROSSO")
    print("VELENI OK: ogni copia rotta fa rosso il banco col motivo atteso")
    return 0


def main() -> int:
    for flusso in (sys.stdout, sys.stderr):
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--avvelena", action="store_true")
    argomenti = parser.parse_args()
    repo = Path(argomenti.repo).resolve()
    if argomenti.avvelena:
        return avvelena(repo)
    rossi = prova(repo)
    for r in rossi:
        print("ROSSO", r)
    print(f"scoperta: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    print("BANCO ROSSO" if rossi else "BANCO VERDE")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
