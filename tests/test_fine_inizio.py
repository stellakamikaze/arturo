#!/usr/bin/env python3
"""F01-F12: il ciclo di sessione di /fine e /inizio sopra l'archivio dei todo (15/10/2026).

F01 bin/handoff-gate.sh: la sezione "## Task Pendenti" c'è sempre, ogni riga ha l'ID di un todo
aperto dell'archivio, Chi è una categoria dei todo o la sua forma per la persona ("Claude",
"Decidi tu", "Tu: <cosa serve>", dal 20/10/2026), niente segnaposti del modello mai compilati.
F02 il gate legge le categorie di Chi da bin/todo_store.py: non ne tiene una copia.
F03 bin/handoff-retention.py tiene gli ultimi 5 per filone, in ordine di nome e non di data del
file, stampa vicoli ciechi e task senza ID dei file in uscita; solo con --applica li sposta nel
cestino dello store, dove restano 30 giorni (segnalazione n. 26).
F04 bin/index-rigenera.py: una riga per filone, prossimo passo dalla Ripartenza, archivio oltre
30 giorni, nessun link morto, scrittura atomica, nessun elenco di cartelle personali.
F05 bin/inventario-sessione.py: dalla trascrizione i file della sessione con un destino proposto
(repo, archivia, resta, scarto), le bozze create online, ~/.claude escluso.
F06 arturo contesto: git, ripartenza, todo per chi agisce, chiusi, scadenze in una chiamata;
NON TROVATO con i nomi simili; --tutti e il compito dopo " -- " restano fuori dal nome.
F07 bin/sync-progetti.sh: pull di ogni progetto con stash, conflitti e credenziali riportati.
F08 /fine usa inventario, gate, retention e indice; il modello della tabella passa il gate;
niente find|tail|rm; nessun blocco legge una variabile di un altro blocco.
F09 /fine rilanciato nella stessa sessione riscrive lo stesso handoff.
F10 /inizio prende il contesto con arturo contesto e con --tutti lancia sync-progetti.
F11 l'inventario su Windows (16/10/2026): un file in commit in una sottocartella o in un worktree
va nel repo e non risulta ignorato; lo scratchpad nella cartella temporanea del sistema (su
Windows %TEMP%, che sta dentro la HOME) è volatile e riconosciuto come scratchpad; il JSON esce
in UTF-8 anche se la pipe è in cp1252.
F12 il Config Sync di /fine non pubblica una skill nuova della persona su un remote pubblico: la
nomina e Claude chiede. Verso un remote privato la salva (16/10/2026).
F13 in un worktree (segnalazione n. 11, 22/10/2026): i blocchi che girano dentro il worktree, cioè
/fine fino al commit e /inizio FASE 4, non usano "$HOME" né $(...), che la guardia di Claude Code
rifiuta; /fine esce dal worktree prima del merge sul tree principale.
F14 gli altri comandi che possono girare in un worktree scrivono ~/.claude, non "$HOME/.claude" (#3802).
F15 un progetto che la persona toglie dal sync degli handoff con una riga sua nel .gitignore resta
fuori (segnalazione n. 12, 23/10/2026).
F16 in un worktree (segnalazione n. 13, 26/10/2026): /fine riporta nel tree principale i file ignorati
prima di `git worktree remove`, che li cancella senza avviso; /inizio dice che cicli e variabili
vanno in uno script.
F17 con Arturo come origin un archivio già tracciato esce dal tracciamento (segnalazione n. 14,
26/10/2026): dopo retention e sync git non ha più modifiche non salvate.
F18 /inizio e /aggiorna escludono gli archivi della persona (handoff, todo, memoria) come
bin/aggiorna-applica.sh: un handoff tracciato e modificato non ferma il pull (#4021, 27/10/2026).
F19 un ramo di worktree non riportato (segnalazione n. 20, 27/10/2026): arturo contesto lo elenca coi
commit e il worktree finché non è unito; /inizio lo mette in cima, /fine controlla il merge. Un ramo
riportato con un cherry-pick non compare, e /fine lo controlla con lo stesso git cherry (#4175).
F20 il blocco di /inizio per un progetto nuovo espande la tilde di PROJECTS_BASE (segnalazione n. 19).
F21 arturo contesto trova "mio_progetto" anche scritto come slug (segnalazione n. 21).

Sulla base cbd8305 ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
Lì F15 e F17 falliscono perché manca la FASE 9 di /fine: la loro controprova vera è sulla base prima
del loro commit. Su 5e82705^ F17 è rosso perché dopo il sync restano un INDEX.md cambiato e un
handoff cancellato e non salvati (provato il 27/10/2026, #3987).
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
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import igiene  # noqa: E402  i nomi della config dell'autore, solo come impronte (#3505)

# Su Windows "bash" per nome è quello di WSL: si prende il bash del PATH (Git Bash).
BASH = shutil.which("bash") or "bash"

GIT_ENV = {
    "GIT_AUTHOR_NAME": "prova", "GIT_AUTHOR_EMAIL": "prova@example.invalid",
    "GIT_COMMITTER_NAME": "prova", "GIT_COMMITTER_EMAIL": "prova@example.invalid",
    "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0",
}
OGGI = "2026-10-15"
DA_FUORI = {"HOME", "ARGUMENTS", "PROJECTS_BASE", "PWD", "CLAUDE_CODE_SESSION_ID"}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def serve(repo: Path, relativo: str, codice: str) -> Path:
    p = repo / relativo
    assert p.is_file(), f"{codice} manca {relativo}"
    return p


class Lab:
    """Una HOME finta con il suo archivio dei todo e la cartella dei progetti."""

    def __init__(self, repo: Path, tmp: Path):
        self.repo, self.tmp = repo, tmp
        self.home = tmp / "home"
        self.progetti = self.home / "Documents" / "ClaudeCode"
        self.handoffs = self.home / ".claude" / "data" / "handoffs"
        self.progetti.mkdir(parents=True)
        self.handoffs.mkdir(parents=True)
        self.todo_file = tmp / "eventi.jsonl"

    def env(self, **altro) -> dict:
        e = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home), ARTURO_TODO=str(self.todo_file), ARTURO_OGGI=OGGI,
                 ARTURO_TELEMETRIA="0", PYTHONDONTWRITEBYTECODE="1", **GIT_ENV)
        e.pop("PROJECTS_BASE", None)
        e.pop("CLAUDE_CODE_SESSION_ID", None)
        e.update(altro)
        return e

    def run(self, argv: list, cwd: Path | None = None, **env) -> subprocess.CompletedProcess:
        return subprocess.run(argv, cwd=str(cwd or self.home), env=self.env(**env), capture_output=True,
                              text=True, encoding="utf-8", timeout=120)

    def arturo(self, *argomenti: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
        return self.run([sys.executable, "-B", str(self.repo / "bin" / "arturo"), *argomenti], cwd=cwd)

    def todo(self, *argomenti: str) -> None:
        r = self.arturo("todo", *argomenti)
        assert r.returncode == 0, f"preparazione: arturo todo {argomenti}: {r.stderr}"

    def git(self, cartella: Path, *argomenti: str) -> str:
        r = self.run(["git", "-C", str(cartella), *argomenti])
        assert r.returncode == 0, f"preparazione: git {argomenti}: {r.stderr}"
        return r.stdout


def con_lab(repo: Path, prova) -> None:
    with tempfile.TemporaryDirectory(prefix="arturo-fine-") as tmp:
        prova(Lab(repo, Path(tmp)))


# --- F01 e F02: il gate ---------------------------------------------------------------------------

TESTA = ("| ID | Progetto | Priorità | Task | Status | Descrizione | Chi |\n"
         "|----|----------|----------|------|--------|-------------|-----|\n")


def riga(id_: str, chi: str, task: str = "Rileggere il capitolo", desc: str = "Servono le note dell'editor") -> str:
    return f"| {id_} | libro | alta | {task} | da fare | {desc} | {chi} |\n"


def handoff(sezione: str, extra: str = "") -> str:
    return f"# Session Handoff\n\n## Progetto\n- Nome: libro\n\n{sezione}\n## In sospeso\n- niente\n{extra}"


def gate(lab: Lab, testo: str | None) -> tuple:
    f = lab.tmp / "handoff.md"
    if testo is not None:
        f.write_text(testo, encoding="utf-8")
    elif f.exists():
        f.unlink()
    r = lab.run([BASH, str(lab.repo / "bin" / "handoff-gate.sh"), str(f)])
    rosse = [x for x in r.stdout.splitlines() if x.startswith("GATE HANDOFF: rosso:")]
    return r.returncode, r.stdout + r.stderr, len(rosse)


def prepara_todo(lab: Lab) -> None:
    lab.todo("aggiungi", "Rileggere il capitolo", "--progetto", "libro", "--chi", "io")     # 1
    lab.todo("aggiungi", "Mandare la bozza", "--progetto", "libro", "--chi", "tu")          # 2
    lab.todo("aggiungi", "Scegliere la copertina", "--progetto", "libro", "--chi", "decidi")  # 3
    lab.todo("aggiungi", "Vecchia cosa", "--progetto", "libro")                             # 4
    lab.todo("fatto", "4")


CASI_GATE = [
    # (nome, testo o None per il file assente, exit, marcatore, righe rosse)
    ("sezione assente", handoff(""), 1, "manca la sezione \"## Task Pendenti\"", 1),
    ("sezione con la sola intestazione", handoff("## Task Pendenti\n\n" + TESTA), 1, "non ha righe", 1),
    ("titolo minuscolo", handoff("## Task pendenti\n\n" + TESTA + riga("#1", "io")), 1,
     "il titolo deve essere esatto", 1),
    ("titolo quasi uguale accanto a quello esatto",
     handoff("## Task Pendenti\n\n" + TESTA + riga("#1", "io") + "\n## Task Pendenti (3)\nNessun task pendente.\n"),
     1, "\"## Task Pendenti (3)\"", 1),
    ("frase senza sezione", handoff("Nessun task pendente: il lavoro è chiuso.\n"), 1, "manca la sezione", 1),
    ("ID vuoto", handoff("## Task Pendenti\n\n" + TESTA + riga("", "io")), 1, "ID \"\" non è un #numero", 1),
    ("ID senza cancelletto", handoff("## Task Pendenti\n\n" + TESTA + riga("1", "io")), 1, "ID \"1\" non è", 1),
    ("ID di un todo che non esiste", handoff("## Task Pendenti\n\n" + TESTA + riga("#99", "io")), 1,
     "#99 non esiste", 1),
    ("ID di un todo chiuso", handoff("## Task Pendenti\n\n" + TESTA + riga("#4", "io")), 1, "#4 è già chiuso", 1),
    # 20/10/2026: /fine scrive Chi come la config dell'autore, in forma neutra ("Claude", "Decidi tu",
    # "Tu: <cosa serve>"). "Claude" da solo è entrato fra le forme ammesse: il caso fuori lista è un altro nome.
    ("Chi fuori lista", handoff("## Task Pendenti\n\n" + TESTA + riga("#1", "Qualcuno")), 1, "Chi \"Qualcuno\"", 1),
    ("Chi \"Tu:\" senza cosa serve", handoff("## Task Pendenti\n\n" + TESTA + riga("#2", "Tu:")), 1, "Chi \"Tu:\"", 1),
    ("Chi \"claude\" minuscolo", handoff("## Task Pendenti\n\n" + TESTA + riga("#1", "claude")), 1, "Chi \"claude\"", 1),
    ("Chi vuoto", handoff("## Task Pendenti\n\n" + TESTA + riga("#1", "")), 1, "Chi \"\"", 1),
    ("colonna Chi non ultima",
     handoff("## Task Pendenti\n\n| ID | Chi | Task |\n|---|---|---|\n| #1 | io | Rileggere |\n"), 1,
     "l'ultima colonna della tabella non è \"Chi\"", 1),
    ("colonna ID assente",
     handoff("## Task Pendenti\n\n| Task | Chi |\n|---|---|\n| Rileggere | io |\n"), 1, "non ha la colonna ID", 1),
    ("descrizione del modello mai compilata",
     handoff("## Task Pendenti\n\n" + TESTA + riga("#1", "io", desc="cosa resta")), 1, "segnaposto", 1),
    ("task del modello mai compilato",
     handoff("## Task Pendenti\n\n" + TESTA + riga("#1", "io", task="[task]")), 1, "segnaposto", 1),
    ("due difetti, due righe rosse",
     handoff("## Task Pendenti\n\n" + TESTA + riga("#99", "io") + riga("#2", "forse")), 1, "GATE HANDOFF: rosso", 2),
    ("file assente", None, 2, "file assente", 0),
    ("verde con le tre categorie",
     handoff("## Task Pendenti\n\n" + TESTA + riga("#1", "io") + riga("#2", "tu") + riga("#3", "decidi")),
     0, "GATE HANDOFF: verde", 0),
    ("verde con le forme per la persona",
     handoff("## Task Pendenti\n\n" + TESTA + riga("#1", "Claude") + riga("#2", "Tu: invio a terzi")
             + riga("#3", "Decidi tu")), 0, "GATE HANDOFF: verde", 0),
    ("verde senza task", handoff("## Task Pendenti\nNessun task pendente.\n"), 0, "GATE HANDOFF: verde", 0),
    ("verde con un task che parla di segnaposti",
     handoff("## Task Pendenti\n\n" + TESTA + riga("#1", "io", desc="Togliere i TODO rimasti nel capitolo due")),
     0, "GATE HANDOFF: verde", 0),
    ("verde con una tabella senza ID fuori dalla sezione",
     handoff("## Task Pendenti\n\n" + TESTA + riga("#1", "io"), "\n## Riferimenti\n| a | b |\n|---|---|\n| x | y |\n"),
     0, "GATE HANDOFF: verde", 0),
]


def test_f01(repo: Path) -> None:
    serve(repo, "bin/handoff-gate.sh", "F01")

    def prova(lab: Lab) -> None:
        prepara_todo(lab)
        for nome, testo, rc, marcatore, rosse in CASI_GATE:
            codice, uscita, n = gate(lab, testo)
            assert codice == rc and marcatore in uscita and n == rosse, \
                f"F01 caso \"{nome}\": exit {codice} (atteso {rc}), righe rosse {n} (attese {rosse}): {uscita[-400:]!r}"
        r = lab.run([BASH, str(repo / "bin" / "handoff-gate.sh")])
        assert r.returncode == 2 and "uso:" in r.stderr, f"F01 senza argomento: {r.returncode} {r.stderr!r}"
        print(f"  F01 casi={len(CASI_GATE) + 1}")
    con_lab(repo, prova)


def test_f02(repo: Path) -> None:
    serve(repo, "bin/handoff-gate.sh", "F02")

    def prova(lab: Lab) -> None:
        copia = lab.tmp / "arturo"
        shutil.copytree(str(repo / "bin"), str(copia / "bin"))
        store = copia / "bin" / "todo_store.py"
        testo = read(store)
        assert 'CHI = ("tu", "decidi", "io")' in testo, "F02 preparazione: CHI di todo_store è cambiato"
        store.write_text(testo.replace('CHI = ("tu", "decidi", "io")', 'CHI = ("tu", "decidi", "io", "altro")'),
                         encoding="utf-8")
        prepara_todo(lab)
        f = lab.tmp / "h.md"
        f.write_text(handoff("## Task Pendenti\n\n" + TESTA + riga("#1", "altro")), encoding="utf-8")
        vera = lab.run([BASH, str(repo / "bin" / "handoff-gate.sh"), str(f)])
        nuova = lab.run([BASH, str(copia / "bin" / "handoff-gate.sh"), str(f)])
        assert vera.returncode == 1, f"F02 il gate vero accetta un Chi che l'archivio non conosce: {vera.stdout!r}"
        assert nuova.returncode == 0, \
            f"F02 il gate tiene una sua copia delle categorie: con CHI cambiato in todo_store resta rosso: {nuova.stdout!r}"
    con_lab(repo, prova)


# --- F03 e F04: retention e indice ----------------------------------------------------------------

def documento(nome: str, filone: str = "", ripartenza: str = "", prossimi: str = "", vicolo: str = "",
              task: str = "", status: str = "in progress") -> str:
    f = f"- Filone: {filone}\n" if filone else ""
    r = f"## Ripartenza\nTesto.\nProssimo passo: {ripartenza}\n\n" if ripartenza else ""
    p = f"## Prossimi passi\n1. [ ] {prossimi}\n\n" if prossimi else ""
    v = f"## Vicoli ciechi\n- {vicolo}\n\n" if vicolo else ""
    t = task or "## Task Pendenti\nNessun task pendente.\n"
    return f"# Session Handoff\n\n## Progetto\n- Nome: {nome} / Branch: main / Status: {status}\n{f}\n{r}{v}{p}{t}"


def scrivi(radice: Path, file: dict) -> None:
    for rel, testo in file.items():
        (radice / rel).parent.mkdir(parents=True, exist_ok=True)
        (radice / rel).write_text(testo, encoding="utf-8")


def test_f03(repo: Path) -> None:
    script = serve(repo, "bin/handoff-retention.py", "F03")
    task = ("## Task Pendenti\n\n" + TESTA + "| #12 | libro | alta | TASK-CON-ID | da fare | d | io |\n"
            "| — | libro | media | TASK-SENZA-ID | da fare | d | tu |\n")
    with tempfile.TemporaryDirectory(prefix="arturo-retention-") as tmp:
        radice = Path(tmp)
        date = ["2026-09-01_10-00", "2026-09-05_10-00", "2026-09-10_10-00", "2026-09-15_10-00",
                "2026-09-20_10-00", "2026-09-25_10-00"]
        file = {f"libro/HANDOFF_{d}.md": documento("libro", vicolo="VICOLO-USCENTE" if i == 0 else "",
                                                   task=task if i == 0 else "")
                for i, d in enumerate(date)}
        file.update({f"libro/HANDOFF_2026-08-0{i}_10-00.md": documento("libro", filone="Copertina") for i in (1, 2)})
        file["libro/note.txt"] = "non è un handoff"
        scrivi(radice, file)
        adesso = time.time()  # date dei file al contrario: l'ordine deve venire dal nome
        for i, f in enumerate(sorted((radice / "libro").glob("HANDOFF_*.md"))):
            os.utime(str(f), (adesso - i * 3600, adesso - i * 3600))

        # L'elenco del dry-run è per sessione: --applica sposta solo ciò che il dry-run ha mostrato.
        temp = Path(tmp) / ".tmp"
        temp.mkdir()
        ambiente = {**os.environ, "CLAUDE_CODE_SESSION_ID": "prova-f03", "TMPDIR": str(temp), "TEMP": str(temp),
                    "TMP": str(temp)}

        def lancia(*a: str) -> subprocess.CompletedProcess:
            return subprocess.run([sys.executable, "-B", str(script), *a, "--radice", str(radice)],
                                  capture_output=True, text=True, encoding="utf-8", timeout=60, env=ambiente)
        assert lancia("nessuno").returncode == 2 and lancia("../libro").returncode == 2, "F03 slug assente non è exit 2"
        prima = sorted(p.name for p in (radice / "libro").iterdir())
        r = lancia("libro")
        assert r.returncode == 0 and sorted(p.name for p in (radice / "libro").iterdir()) == prima, \
            f"F03 senza --applica ha cancellato qualcosa: {r.stdout}"
        uscenti = [x.split()[3] for x in r.stdout.splitlines() if x.startswith("=== IN USCITA")]
        assert uscenti == [f"libro/HANDOFF_{date[0]}.md"], f"F03 in uscita {uscenti}: il filone Copertina conta a parte"
        assert "VICOLO-USCENTE" in r.stdout and "TASK-SENZA-ID" in r.stdout and "TASK-CON-ID" not in r.stdout, \
            f"F03 il triage del file in uscita: {r.stdout}"
        # Nel cestino da prima: uno da 31 giorni esce, uno da 29 resta (segnalazione n. 26).
        cestino = radice / ".cestino" / "libro"
        # Anche il cestino di un progetto che non passa più da /fine si svuota (#4264).
        fermo = radice / ".cestino" / "fermo"
        scrivi(radice, {".cestino/libro/HANDOFF_2026-07-01_10-00.md": "vecchio\n",
                        ".cestino/libro/HANDOFF_2026-07-02_10-00.md": "recente\n",
                        ".cestino/fermo/HANDOFF_2026-06-01_10-00.md": "vecchio\n",
                        ".cestino/fermo/HANDOFF_2026-06-02_10-00.md": "recente\n"})
        for cartella in (cestino, fermo):
            for nome, giorni in ((sorted(p.name for p in cartella.iterdir())[0], 31),
                                 (sorted(p.name for p in cartella.iterdir())[1], 29)):
                os.utime(str(cartella / nome), (adesso - giorni * 86400, adesso - giorni * 86400))
        r = lancia("libro", "--applica")
        assert r.returncode == 0 and not (radice / "libro" / f"HANDOFF_{date[0]}.md").exists(), \
            f"F03 --applica non toglie il file in uscita: {r.stdout} {r.stderr}"
        assert (cestino / f"HANDOFF_{date[0]}.md").is_file(), \
            f"F03 l'handoff tolto non è nel cestino dello store, non si recupera: {r.stdout}"
        assert not (cestino / "HANDOFF_2026-07-01_10-00.md").exists() and (cestino / "HANDOFF_2026-07-02_10-00.md").exists(), \
            "F03 il cestino non tiene i 30 giorni"
        assert not (fermo / "HANDOFF_2026-06-01_10-00.md").exists() and (fermo / "HANDOFF_2026-06-02_10-00.md").exists(), \
            f"F03 il cestino di un progetto fermo non si svuota: {r.stdout}"
        assert "Per riportarne uno: sposta il file da" in r.stdout, f"F03 non dice come riportare un handoff: {r.stdout}"
        assert len(list((radice / "libro").glob("HANDOFF_*.md"))) == 7 and (radice / "libro" / "note.txt").exists(), \
            "F03 --applica ha tolto più del file in uscita"


INDEX = """# Indice

| Progetto | Ultimo handoff | Data | Stato | Prossimo passo |
|---|---|---|---|---|
| alfa (etichetta tenuta) | [HANDOFF_2026-09-25_10-00.md](alfa/HANDOFF_2026-09-25_10-00.md) | 2026-09-25 | STATO-INDEX-ALFA | DA-INDEX-ALFA |
| alfa (sessione prima) | [HANDOFF_2026-09-20_10-00.md](alfa/HANDOFF_2026-09-20_10-00.md) | 2026-09-20 | superato | RIGA-SUPERATA |
| beta | [HANDOFF_2026-09-26_10-00.md](beta/HANDOFF_2026-09-26_10-00.md) | 2026-09-26 | x | VECCHIO-BETA |
| gamma (dismesso) | [HANDOFF_2026-09-29_10-00.md](gamma/HANDOFF_2026-09-29_10-00.md) | 2026-09-29 | DISMESSO-GAMMA | — |
"""


def test_f04(repo: Path) -> None:
    script = serve(repo, "bin/index-rigenera.py", "F04")
    testo = read(script)
    # Dal 30/10/2026 le cartelle contenitore vengono da hooks/index-contenitori.local della persona (#4291):
    # nel codice non resta un elenco di cartelle personali.
    assert not re.search(r"CONTENITORI\s*=\s*\{", testo) and "index-contenitori.local" in testo if "CONTENITORI" in testo \
        else True, "F04 index-rigenera tiene un elenco di cartelle personali"
    with tempfile.TemporaryDirectory(prefix="arturo-index-") as tmp:
        radice = Path(tmp)
        scrivi(radice, {
            "libro/HANDOFF_2026-10-01_10-00.md": documento("libro", filone="Copertina", ripartenza="PP-COPERTINA"),
            "libro/HANDOFF_2026-10-02_10-00.md": documento("libro", ripartenza="PP-LIBRO"),
            "libro/HANDOFF_2026-09-30_10-00.md": documento("libro", ripartenza="PP-LIBRO-VECCHIO"),
            "alfa/HANDOFF_2026-09-20_10-00.md": documento("alfa"),
            "alfa/HANDOFF_2026-09-25_10-00.md": documento("alfa", prossimi="DA-PROSSIMI-ALFA"),
            "beta/HANDOFF_2026-09-26_10-00.md": documento("beta", ripartenza="PP-BETA"),
            "delta/HANDOFF_2026-09-27_10-00.md": documento("delta", prossimi="DA-PROSSIMI-DELTA"),
            "lungo/HANDOFF_2026-09-28_10-00.md": documento("lungo", ripartenza="a | b " + "parola " * 80),
            "soglia30/HANDOFF_2026-09-15_10-00.md": documento("soglia30", ripartenza="PP-30"),
            "soglia31/HANDOFF_2026-09-14_10-00.md": documento("soglia31", ripartenza="PP-31"),
            "INDEX.md": INDEX,
        })

        def lancia(*a: str) -> subprocess.CompletedProcess:
            return subprocess.run([sys.executable, "-B", str(script), "--radice", str(radice), "--oggi", OGGI, *a],
                                  capture_output=True, text=True, encoding="utf-8", timeout=60)
        assert lancia().returncode == 2, "F04 senza --dry-run/--out/--scrivi non è exit 2"
        prima = read(radice / "INDEX.md")
        r = lancia("--dry-run")
        assert r.returncode == 0 and read(radice / "INDEX.md") == prima, f"F04 --dry-run: {r.returncode} {r.stderr}"
        attive, _, archivio = r.stdout.partition("## Archivio")

        def righe(testo: str, m: str) -> list:
            return [x for x in testo.splitlines() if x.startswith("|") and m in x]
        morti = [d for d in re.findall(r"\]\(([^)\s]+)\)", r.stdout) if not (radice / d).exists()]
        assert not morti, f"F04 link verso file assenti: {morti}"
        for x in r.stdout.splitlines():
            if x.startswith("|"):
                assert len(re.split(r"(?<!\\)\|", x.strip())) - 2 == 5, f"F04 riga senza cinque colonne: {x[:80]}"
        assert righe(attive, "PP-COPERTINA") and righe(attive, "PP-LIBRO") and not righe(r.stdout, "PP-LIBRO-VECCHIO"), \
            "F04 il filone Copertina e il progetto libro non hanno una riga ciascuno"
        assert righe(attive, "PP-BETA") and not righe(attive, "VECCHIO-BETA"), "F04 la Ripartenza non vince sull'INDEX"
        alfa = righe(attive, "alfa/HANDOFF_2026-09-25")
        assert alfa and "DA-INDEX-ALFA" in alfa[0] and "STATO-INDEX-ALFA" in alfa[0], f"F04 alfa: {alfa}"
        assert not righe(r.stdout, "RIGA-SUPERATA") and righe(attive, "DA-PROSSIMI-DELTA"), "F04 superate o Prossimi passi"
        gamma = righe(r.stdout, "DISMESSO-GAMMA")
        assert gamma and "](gamma/" not in gamma[0], f"F04 la riga senza file ha perso il testo o tiene il link: {gamma}"
        assert righe(attive, "PP-30") and righe(archivio, "PP-31") and not righe(attive, "PP-31"), "F04 soglia 30 giorni"
        lungo = righe(attive, "lungo/HANDOFF")
        assert lungo and re.split(r"(?<!\\)\|", lungo[0].strip())[-2].strip().endswith("…"), "F04 prossimo passo non tagliato"
        r = lancia("--scrivi")
        assert r.returncode == 0 and "PP-BETA" in read(radice / "INDEX.md"), f"F04 --scrivi: {r.stderr}"
        assert not [p for p in radice.iterdir() if p.name.endswith(".tmp")], "F04 file temporanei rimasti"
        vuota = radice / "vuota"
        vuota.mkdir()
        r = subprocess.run([sys.executable, "-B", str(script), "--radice", str(vuota), "--dry-run"],
                           capture_output=True, text=True, encoding="utf-8", timeout=60)
        assert r.returncode == 1, f"F04 senza handoff né INDEX genera lo stesso un indice: {r.returncode}"


# --- F05: inventario ----------------------------------------------------------------------------

def test_f05(repo: Path) -> None:
    script = serve(repo, "bin/inventario-sessione.py", "F05")
    testo = read(script)
    for parola in ("gws", "drive-personale"):
        assert parola not in testo, f"F05 inventario con un destino o un account personale: {parola}"
    assert not igiene.trova(testo, igiene.FINE), "F05 inventario con uno strumento della config dell'autore"

    def prova(lab: Lab) -> None:
        progetto = lab.progetti / "libro"
        progetto.mkdir()
        lab.git(progetto, "init", "-q")
        (progetto / "capitolo.md").write_text("uno\n", encoding="utf-8")
        (lab.home / "Desktop").mkdir()
        sciolto = lab.home / "Desktop" / "note.txt"
        sciolto.write_text("appunti\n", encoding="utf-8")
        fuori = lab.home / "codice.py"
        fuori.write_text("print(1)\n", encoding="utf-8")
        cfg = lab.home / ".claude" / "settings.json"
        cfg.write_text("{}\n", encoding="utf-8")
        sid = "sessione-di-prova"
        cartella = lab.home / ".claude" / "projects" / "libro"
        cartella.mkdir(parents=True)
        ts = "2026-10-15T09:00:00.000Z"

        def uso(i: str, nome: str, inp: dict) -> dict:
            return {"timestamp": ts, "cwd": str(progetto), "message": {"content": [
                {"type": "tool_use", "id": i, "name": nome, "input": inp}]}}
        righe = [
            uso("t1", "Write", {"file_path": str(progetto / "capitolo.md")}),
            uso("t2", "Write", {"file_path": str(sciolto)}),
            uso("t3", "Edit", {"file_path": str(cfg)}),
            uso("t4", "Bash", {"command": f"echo x > {fuori.as_posix()}"}),  # barre dritte, come in Git Bash
            uso("t5", "Bash", {"command": "cp capitolo.md /tmp/arturo-prova-sparito.md"}),
            uso("t6", "mcp__connettore__Gmail__create_draft", {"to": "a@example.invalid"}),
            {"timestamp": ts, "message": {"content": [{"type": "tool_result", "tool_use_id": "t6",
                                                       "content": '{"id": "bozza0000prova"}'}]}},
        ]
        (cartella / f"{sid}.jsonl").write_text("\n".join(json.dumps(x) for x in righe) + "\n", encoding="utf-8")
        r = lab.run([sys.executable, "-B", str(script), "--json", "--session", sid,
                     "--projects", str(lab.home / ".claude" / "projects"), "--home", str(lab.home)])
        assert r.returncode == 0, f"F05 exit {r.returncode}: {r.stderr}"
        inv = json.loads(r.stdout)
        destini = {Path(f["path"]).name: f["destino"] for f in inv["file"]}
        assert destini.get("capitolo.md") == "repo", f"F05 il file del progetto non va nel repo: {destini}"
        assert destini.get("note.txt") == "archivia", f"F05 il documento sulla Scrivania non va archiviato: {destini}"
        assert destini.get("codice.py") == "scarto", f"F05 codice fuori da un repository: {destini}"
        assert "settings.json" not in destini and inv["esclusi"]["~/.claude"] == 1, f"F05 ~/.claude non escluso: {inv['esclusi']}"
        assert any(s["path"].endswith("arturo-prova-sparito.md") for s in inv["spariti"]), "F05 un file assente non è fra gli spariti"
        assert [(o["tipo"], o["id"]) for o in inv["online"]] == [("bozza di email", "bozza0000prova")], \
            f"F05 la bozza creata online manca: {inv['online']}"
        r = lab.run([sys.executable, "-B", str(script), "--session", "nessuna",
                     "--projects", str(lab.home / ".claude" / "projects"), "--home", str(lab.home)])
        assert r.returncode == 2, f"F05 trascrizione assente non è exit 2: {r.returncode}"
    con_lab(repo, prova)


def test_f11(repo: Path) -> None:
    script = serve(repo, "bin/inventario-sessione.py", "F11")

    def prova(lab: Lab) -> None:
        progetto = lab.progetti / "città"
        (progetto / "capitoli").mkdir(parents=True)
        lab.git(progetto, "init", "-q")
        (progetto / "capitoli" / "uno.md").write_text("uno\n", encoding="utf-8")
        lab.git(progetto, "add", "-A")
        lab.git(progetto, "commit", "-q", "-m", "primo")
        albero = progetto / ".claude" / "worktrees" / "prova"
        lab.git(progetto, "worktree", "add", "-q", "-b", "wt-prova", str(albero))
        (albero / "capitoli" / "uno.md").write_text("uno, rivisto\n", encoding="utf-8")
        # Lo scratchpad come lo crea Claude Code: <temp>/claude-<uid>/… sul Mac, %TEMP%\claude\… su Windows
        base = Path(tempfile.gettempdir()) / "claude" / f"arturo-banco-{os.getpid()}"
        appunto = base / "sessione" / "scratchpad" / "prova.py"
        appunto.parent.mkdir(parents=True)
        appunto.write_text("print(1)\n", encoding="utf-8")
        try:
            sid = "sessione-windows"
            cartella = lab.home / ".claude" / "projects" / "citta"
            cartella.mkdir(parents=True)
            righe = [{"timestamp": "2026-10-16T09:00:00.000Z", "cwd": str(progetto), "message": {"content": [
                {"type": "tool_use", "id": f"t{i}", "name": "Write", "input": {"file_path": str(p)}}]}}
                for i, p in enumerate((progetto / "capitoli" / "uno.md", albero / "capitoli" / "uno.md", appunto))]
            (cartella / f"{sid}.jsonl").write_text("\n".join(json.dumps(x) for x in righe) + "\n", encoding="utf-8")
            r = subprocess.run([sys.executable, "-B", str(script), "--json", "--session", sid,
                                "--projects", str(lab.home / ".claude" / "projects"), "--home", str(lab.home)],
                               cwd=str(lab.home), env=lab.env(PYTHONIOENCODING="cp1252", PYTHONUTF8="0"),
                               capture_output=True, timeout=120)
            assert r.returncode == 0, f"F11 exit {r.returncode}: {r.stderr.decode('utf-8', 'replace')}"
            try:
                inv = json.loads(r.stdout.decode("utf-8"))
            except (UnicodeDecodeError, ValueError) as e:
                raise AssertionError(f"F11 il JSON non è UTF-8 con la pipe in cp1252: {e}")
            per_path = {os.path.normcase(f["path"]): f for f in inv["file"]}
            for p, git in ((progetto / "capitoli" / "uno.md", "pulito"), (albero / "capitoli" / "uno.md", "modificato")):
                f = per_path.get(os.path.normcase(str(p)))
                assert f and f["git"] == git and f["destino"] == "repo", \
                    f"F11 file in commit in una sottocartella non va nel repo ({p.parent.parent.name}): {f}"
            f = per_path.get(os.path.normcase(str(appunto)))
            assert f and f["volatile"] and f["scratchpad"], f"F11 lo scratchpad non è riconosciuto: {f}"
        finally:
            shutil.rmtree(base, ignore_errors=True)
    con_lab(repo, prova)


def test_f12(repo: Path) -> None:
    fine = read(serve(repo, "commands/fine.md", "F12"))
    # 20/10/2026: /fine numera le fasi come la config dell'autore, il Config Sync è la FASE 9.
    assert "## FASE 9 · Config Sync" in fine, "F12 manca la FASE 9 · Config Sync di /fine"
    inizio = fine.index("## FASE 9 · Config Sync")
    blocco = fine[fine.index("```bash\n", inizio) + 8:fine.index("\n```", fine.index("```bash\n", inizio))]

    def sync(visibilita: str) -> tuple:
        with tempfile.TemporaryDirectory(prefix="arturo-f12-") as tmp:
            lab = Lab(repo, Path(tmp))
            config = lab.home / ".claude"
            shutil.copytree(str(repo), str(config), ignore=shutil.ignore_patterns(".git", "__pycache__", "worktrees"),
                            dirs_exist_ok=True)
            remoto = Path(tmp) / "config.git"
            lab.git(Path(tmp), "init", "-q", "--bare", "-b", "main", str(remoto))
            lab.git(config, "init", "-q", "-b", "main")
            lab.git(config, "add", "-A")
            lab.git(config, "commit", "-q", "-m", "config")
            lab.git(config, "remote", "add", "origin", str(remoto))
            lab.git(config, "push", "-q", "origin", "main")
            (config / "skills" / "lettera-cliente").mkdir()
            (config / "skills" / "lettera-cliente" / "SKILL.md").write_text("Scrivi alla signora Rossi.\n", encoding="utf-8")
            finti = Path(tmp) / "finti"
            finti.mkdir()
            (finti / "gh").write_text(f"#!/bin/sh\necho {visibilita}\n", encoding="utf-8")
            (finti / "gh").chmod(0o755)
            r = lab.run([BASH, "-c", blocco], cwd=lab.home, PATH=f"{finti}{os.pathsep}{os.environ.get('PATH', '')}")
            nel_remoto = lab.run(["git", "-C", str(remoto), "ls-tree", "-r", "--name-only", "main"]).stdout
            return r.stdout + r.stderr, "skills/lettera-cliente/SKILL.md" in nel_remoto

    uscita, pubblicata = sync("PUBLIC")
    assert not pubblicata, f"F12 /fine pubblica una skill della persona su un remote pubblico: {uscita[-400:]}"
    assert "SKILL TUE NON SALVATE" in uscita and "lettera-cliente" in uscita, \
        f"F12 /fine non dice quali skill non ha salvato: {uscita[-400:]}"
    uscita, pubblicata = sync("PRIVATE")
    assert pubblicata, f"F12 /fine non salva la skill verso un remote privato: {uscita[-400:]}"


def test_f15(repo: Path) -> None:
    """Un progetto che la persona toglie dal sync con una riga sua nel .gitignore resta fuori (segnalazione n. 12)."""
    fine = read(serve(repo, "commands/fine.md", "F15"))
    assert "## FASE 9 · Config Sync" in fine, "F15 manca la FASE 9 · Config Sync di /fine"
    inizio = fine.index("## FASE 9 · Config Sync")
    blocco = fine[fine.index("```bash\n", inizio) + 8:fine.index("\n```", fine.index("```bash\n", inizio))]
    with tempfile.TemporaryDirectory(prefix="arturo-f15-") as tmp:
        lab = Lab(repo, Path(tmp))
        config = lab.home / ".claude"
        shutil.copytree(str(repo), str(config), ignore=shutil.ignore_patterns(".git", "__pycache__", "worktrees"),
                        dirs_exist_ok=True)
        # 23/10/2026, Gigi: un progetto riservato esce dal sync con una riga nel .gitignore della sua config.
        with open(config / ".gitignore", "a", encoding="utf-8") as f:
            f.write("\n# progetto riservato\ndata/handoffs/riservato/\n")
        remoto = Path(tmp) / "config.git"
        lab.git(Path(tmp), "init", "-q", "--bare", "-b", "main", str(remoto))
        lab.git(config, "init", "-q", "-b", "main")
        lab.git(config, "add", "-A")
        lab.git(config, "commit", "-q", "-m", "config")
        lab.git(config, "remote", "add", "origin", str(remoto))
        lab.git(config, "push", "-q", "origin", "main")
        for nome in ("aperto", "riservato"):
            (config / "data" / "handoffs" / nome).mkdir(parents=True, exist_ok=True)
            (config / "data" / "handoffs" / nome / "HANDOFF_2026-10-23_10-00.md").write_text("# h\n", encoding="utf-8")
        finti = Path(tmp) / "finti"
        finti.mkdir()
        (finti / "gh").write_text("#!/bin/sh\necho PRIVATE\n", encoding="utf-8")
        (finti / "gh").chmod(0o755)
        r = lab.run([BASH, "-c", blocco], cwd=lab.home, PATH=f"{finti}{os.pathsep}{os.environ.get('PATH', '')}")
        nel_remoto = lab.run(["git", "-C", str(remoto), "ls-tree", "-r", "--name-only", "main"]).stdout
        uscita = (r.stdout + r.stderr)[-400:]
        assert "data/handoffs/aperto/HANDOFF_2026-10-23_10-00.md" in nel_remoto, \
            f"F15 /fine non salva più gli handoff verso un remote privato: {uscita}"
        assert "data/handoffs/riservato/" not in nel_remoto, \
            f"F15 /fine pubblica gli handoff di un progetto che la persona ha escluso dal sync: {uscita}"


# --- F06: arturo contesto -----------------------------------------------------------------------

def test_f06(repo: Path) -> None:
    serve(repo, "bin/contesto.py", "F06")

    def prova(lab: Lab) -> None:
        progetto = lab.progetti / "Il Libro"
        progetto.mkdir()
        lab.git(progetto, "init", "-q")
        (progetto / "a.md").write_text("a\n", encoding="utf-8")
        lab.git(progetto, "add", "a.md")
        lab.git(progetto, "commit", "-qm", "Primo capitolo scritto")
        scrivi(lab.handoffs, {
            "il-libro/HANDOFF_2026-10-14_10-00.md": documento("il-libro", ripartenza="RIPARTI-DALLA-BOZZA"),
            "il-libro/HANDOFF_2026-09-01_10-00.md": documento("il-libro", ripartenza="VECCHIO-PASSO"),
        })
        lab.todo("aggiungi", "Rileggere il capitolo", "--progetto", "il-libro", "--chi", "io")
        lab.todo("aggiungi", "Mandare la bozza", "--progetto", "il-libro", "--chi", "tu", "--scadenza", "2026-10-16")
        lab.todo("aggiungi", "Firmare il contratto", "--progetto", "generale", "--chi", "tu", "--scadenza", "2026-10-13")
        lab.todo("aggiungi", "Lavoro di un altro progetto", "--progetto", "altro", "--chi", "io")
        lab.todo("aggiungi", "Chiuso adesso", "--progetto", "il-libro")
        lab.todo("fatto", "5")
        r = lab.arturo("contesto", "Il Libro --tutti -- rileggere il capitolo due", cwd=lab.home)
        out = r.stdout
        assert r.returncode == 0, f"F06 exit {r.returncode}: {r.stderr} {out}"
        assert "PROGETTO il-libro" in out and f"cartella: {progetto.resolve()}" in out, f"F06 progetto o cartella: {out[:300]}"
        assert "Primo capitolo scritto" in out and "RIPARTI-DALLA-BOZZA" in out and "VECCHIO-PASSO" not in out, \
            f"F06 git o ripartenza degli ultimi 14 giorni: {out}"
        assert re.search(r"TOCCA A TE\n\s+#2 Mandare la bozza", out) and re.search(r"FACCIO IO\n\s+#1 Rileggere", out), \
            f"F06 i todo del progetto non sono divisi per chi agisce: {out}"
        assert "Lavoro di un altro progetto" not in out, "F06 mostra i todo di un altro progetto"
        assert re.search(r"CHIUSI.*\n\s+#5 Chiuso adesso", out), f"F06 i todo chiusi dopo l'ultimo handoff: {out}"
        scadenze = out[out.index("SCADENZE"):] if "SCADENZE" in out else ""
        assert "Firmare il contratto" in scadenze and "scaduto da 2 g" in scadenze, f"F06 scadenze anche di generale: {out}"
        assert "DA DOVE PARTIRE" in out, "F06 manca il todo da cui ripartire"
        r = lab.arturo("contesto", "il librr", cwd=lab.home)
        assert r.returncode == 2 and "NON TROVATO" in r.stdout and "Il Libro" in r.stdout, \
            f"F06 un refuso non dà NON TROVATO con i nomi simili: {r.returncode} {r.stdout}"
        r = lab.arturo("contesto", cwd=lab.progetti)
        assert r.returncode == 2 and "contiene i progetti" in r.stdout, f"F06 la cartella dei progetti presa per un progetto: {r.stdout}"
        r = lab.arturo("contesto", cwd=progetto)
        assert r.returncode == 0 and "PROGETTO il-libro" in r.stdout, f"F06 senza nome non usa la cartella: {r.stdout}"
        r = lab.arturo("contesto", "libro", "--boh", cwd=lab.home)
        assert r.returncode == 3, f"F06 un'opzione sconosciuta non è exit 3: {r.returncode}"
    con_lab(repo, prova)


# --- F07: sync-progetti -------------------------------------------------------------------------

def test_f07(repo: Path) -> None:
    script = serve(repo, "bin/sync-progetti.sh", "F07")

    def prova(lab: Lab) -> None:
        conti = [0]

        def prepara(nome: str) -> tuple:
            radice = lab.tmp / nome
            nudo, monte = lab.tmp / f"nudo-{nome}", lab.tmp / f"monte-{nome}"
            radice.mkdir()
            lab.git(lab.tmp, "init", "-q", "--bare", "-b", "main", str(nudo))
            lab.git(lab.tmp, "clone", "-q", str(nudo), str(monte))
            lab.git(monte, "checkout", "-q", "-B", "main")
            (monte / "nota.md").write_text("riga uno\nriga due\n", encoding="utf-8")
            (monte / "altro.md").write_text("altro file\n", encoding="utf-8")
            lab.git(monte, "add", "-A")
            lab.git(monte, "commit", "-qm", "base")
            lab.git(monte, "push", "-q", "origin", "main")
            lab.git(lab.tmp, "clone", "-q", str(nudo), str(radice / "repo"))
            return radice, monte

        def avanza(monte: Path, file: str, testo: str) -> None:
            (monte / file).write_text(testo + "\n", encoding="utf-8")
            lab.git(monte, "commit", "-qam", "avanti")
            lab.git(monte, "push", "-q", "origin", "main")

        def lancia(radice: Path, copia: Path | None = None) -> subprocess.CompletedProcess:
            conti[0] += 1
            return lab.run([BASH, str(copia or script), str(radice)])

        radice, _ = prepara("a")
        r = lancia(radice)
        assert r.returncode == 0 and "Già aggiornato" in r.stdout, f"F07 allineato: {r.returncode} {r.stdout}"
        radice, monte = prepara("b")
        avanza(monte, "nota.md", "cambiata a monte")
        r = lancia(radice)
        assert r.returncode == 0 and "Aggiornato: 1 commit" in r.stdout, f"F07 remoto avanti: {r.stdout}"
        radice, monte = prepara("c")
        avanza(monte, "nota.md", "cambiata a monte")
        (radice / "repo" / "altro.md").write_text("modificato in locale\n", encoding="utf-8")
        r = lancia(radice)
        assert r.returncode == 0 and "Stash ripristinato" in r.stdout and \
            "modificato in locale" in read(radice / "repo" / "altro.md"), f"F07 stash pulito: {r.stdout}"
        radice, monte = prepara("d")
        avanza(monte, "nota.md", "riscritta a monte")
        (radice / "repo" / "nota.md").write_text("riscritta in locale\n", encoding="utf-8")
        r = lancia(radice)
        assert r.returncode == 1 and "stash pop con conflitti" in r.stdout, f"F07 il conflitto dello stash: {r.stdout}"
        # controprova: senza l'ultima riga di controllo lo stesso caso esce 0
        senza = lab.tmp / "senza-controllo.sh"
        senza.write_text(read(script).replace('[ "$ERRORS" -eq 0 ] || exit 1\n', ""), encoding="utf-8")
        assert read(senza) != read(script), "F07 la controprova non entra nella copia"
        radice, monte = prepara("d2")
        avanza(monte, "nota.md", "riscritta a monte")
        (radice / "repo" / "nota.md").write_text("riscritta in locale\n", encoding="utf-8")
        assert lancia(radice, senza).returncode == 0, "F07 l'exit 1 non viene dal controllo finale"
        locale = lab.tmp / "e"
        (locale / "repo").mkdir(parents=True)
        lab.git(locale / "repo", "init", "-q")
        (locale / "repo" / "nota.md").write_text("solo locale\n", encoding="utf-8")
        lab.git(locale / "repo", "add", "-A")
        lab.git(locale / "repo", "commit", "-qm", "base")
        (locale / "repo" / "nota.md").write_text("in corso\n", encoding="utf-8")
        (locale / "non-un-repo").mkdir()
        r = lancia(locale)
        assert r.returncode == 0 and "nessun remoto" in r.stdout and "ERRORE" not in r.stdout \
            and "in corso" in read(locale / "repo" / "nota.md") and "non-un-repo" not in r.stdout, \
            f"F07 repository locale o cartella senza git: {r.stdout}"
        r = lab.run([BASH, str(script)], PROJECTS_BASE="~/Documents/ClaudeCode")
        # La cartella di prova per nome: su Windows bash la stampa come /tmp/..., non come C:\...
        assert r.returncode == 0 and f"{lab.tmp.name}/home/Documents/ClaudeCode" in r.stdout, \
            f"F07 PROJECTS_BASE con la tilde: {r.stdout} {r.stderr}"
        classifica = lab.tmp / "classifica.sh"
        corpo = re.search(r'    case "\$PULL_OUT" in.*?\n    esac\n', read(script), re.S)
        assert corpo, "F07 manca la lettura della causa del pull fallito"
        classifica.write_text("name=prova\n" + corpo.group(0), encoding="utf-8")
        cred = lab.run([BASH, str(classifica)], PULL_OUT="fatal: could not read Username for 'https://example.invalid'")
        conf = lab.run([BASH, str(classifica)], PULL_OUT="error: could not apply 3f2a1b9... CONFLICT in nota.md")
        assert "gh auth setup-git" in cred.stdout and "conflitto con modifiche locali" in conf.stdout, \
            f"F07 credenziali e conflitto confusi: {cred.stdout!r} {conf.stdout!r}"
        assert "Documents/ClaudeCode}" in read(script), "F07 la cartella dei progetti non viene da PROJECTS_BASE"
    con_lab(repo, prova)


# --- F08-F10: i comandi -------------------------------------------------------------------------

def blocchi(testo: str) -> list:
    return re.findall(r"```bash\n(.*?)```", testo, re.S)


def variabili_orfane(script: str) -> list:
    assegnate = set(re.findall(r"\b([A-Z_][A-Z0-9_]*)=", script))
    assegnate.update(re.findall(r"\bfor\s+([A-Z_][A-Z0-9_]*)\s+in\b", script))
    lette = set(re.findall(r"\$\{?([A-Z_][A-Z0-9_]*)", script))
    return sorted(lette - assegnate - DA_FUORI)


def test_f08(repo: Path) -> None:
    fine = read(repo / "commands" / "fine.md")
    for pezzo in ("bin/inventario-sessione.py", "bin/handoff-gate.sh", "bin/handoff-retention.py", "bin/fine-coda.py"):
        assert pezzo in fine, f"F08 /fine non usa {pezzo}"
    # dal 30/10/2026 retention con --applica e indice li lancia la coda (#4291)
    coda = read(repo / "bin" / "fine-coda.py")
    assert '"index-rigenera.py"), "--scrivi"' in coda, "F08 la coda di /fine non rigenera l'indice"
    assert "tail -n +6" not in fine, "F08 /fine cancella ancora gli handoff con find | tail | rm"
    # Gli strumenti della config dell'autore: solo le impronte, in tests/igiene.py (#3505).
    assert not igiene.trova(fine, igiene.FINE), "F08 /fine nomina uno strumento della config dell'autore"
    assert "`tu`, `decidi` o `io`" in fine, "F08 /fine non dice i valori di Chi"
    orfane = [f"blocco {n}: ${v}" for n, b in enumerate(blocchi(fine), 1) for v in variabili_orfane(b)]
    assert not orfane, "F08 blocchi di /fine che leggono una variabile nata in un altro blocco: " + "; ".join(orfane)
    modello = re.search(r"## Task Pendenti\n.*?\n(\| ID .*?)\n\n", fine, re.S)
    assert modello, "F08 il modello dell'handoff non ha la tabella con la colonna ID"

    def prova(lab: Lab) -> None:
        for n in range(1, 10):
            lab.todo("aggiungi", f"Todo numero {n}", "--progetto", "libro")
        f = lab.tmp / "dal-modello.md"
        f.write_text(handoff("## Task Pendenti\n\n" + modello.group(1) + "\n"), encoding="utf-8")
        r = lab.run([BASH, str(repo / "bin" / "handoff-gate.sh"), str(f)])
        assert r.returncode == 0, f"F08 la tabella del modello di /fine non passa il gate: {r.stdout}"
    con_lab(repo, prova)


def test_f09(repo: Path) -> None:
    fine = read(repo / "commands" / "fine.md")
    assert "**Dove va l'handoff.**" in fine, "F09 manca la sezione dell'handoff"
    codice = blocchi(fine.split("**Dove va l'handoff.**", 1)[1])[0]
    assert "CLAUDE_CODE_SESSION_ID" in codice, "F09 /fine rilanciato crea un secondo handoff della stessa sessione"

    def prova(lab: Lab) -> None:
        progetto = lab.progetti / "Il Libro"
        progetto.mkdir()
        lab.git(progetto, "init", "-q")
        r = lab.run([BASH, "-c", codice], cwd=progetto, CLAUDE_CODE_SESSION_ID="sess-1")
        m = re.search(r"Handoff: (.+)", r.stdout)
        assert r.returncode == 0 and m and "/handoffs/il-libro/HANDOFF_" in m.group(1), f"F09 percorso: {r.stdout} {r.stderr}"
        # Il percorso come lo stampa bash. Su Windows è in forma msys (/tmp/...): per Python lo traduce cygpath.
        vecchio = m.group(1).strip().rsplit("/", 1)[0] + "/HANDOFF_2026-10-14_09-00.md"
        su_disco = vecchio
        if os.name == "nt" and shutil.which("cygpath"):
            su_disco = subprocess.run(["cygpath", "-w", vecchio], capture_output=True, text=True, check=True).stdout.strip()
        Path(su_disco).write_text("# x\n## Progetto\n- Sessione: sess-1\n", encoding="utf-8")
        r = lab.run([BASH, "-c", codice], cwd=progetto, CLAUDE_CODE_SESSION_ID="sess-1")
        assert f"Handoff: {vecchio}" in r.stdout, f"F09 il secondo /fine non ritrova l'handoff della sessione: {r.stdout}"
        r = lab.run([BASH, "-c", codice], cwd=progetto, CLAUDE_CODE_SESSION_ID="sess-2")
        assert f"Handoff: {vecchio}" not in r.stdout, "F09 una sessione nuova riscrive l'handoff di un'altra"
    con_lab(repo, prova)


def test_f10(repo: Path) -> None:
    inizio = read(repo / "commands" / "inizio.md")
    fase0 = inizio[inizio.index("## FASE 0"):inizio.index("## FASE 1")]
    assert "--tutti" in fase0 and "bin/sync-progetti.sh" in fase0, "F10 /inizio --tutti non aggiorna i progetti"
    fase1 = inizio[inizio.index("## FASE 1"):inizio.index("## FASE 2")]
    assert 'arturo contesto "$ARGUMENTS"' in fase1, "F10 /inizio non prende il contesto in una chiamata"
    assert "[--tutti]" in inizio.split("---", 2)[1], "F10 l'aiuto di /inizio non mostra --tutti"
    codice = blocchi(fase1)[0]

    def prova(lab: Lab) -> None:
        shutil.copytree(str(repo / "bin"), str(lab.home / ".claude" / "bin"))
        progetto = lab.progetti / "libro"
        progetto.mkdir()
        lab.git(progetto, "init", "-q")
        lab.todo("aggiungi", "Rileggere il capitolo", "--progetto", "libro", "--chi", "io")
        r = lab.run([BASH, "-c", codice], cwd=lab.home, ARGUMENTS="libro --tutti")
        assert "PROGETTO libro" in r.stdout and "#1 Rileggere il capitolo" in r.stdout and "rc=0" in r.stdout, \
            f"F10 il blocco della FASE 1 non stampa il contesto: {r.stdout} {r.stderr}"
    con_lab(repo, prova)


def test_f13(repo: Path) -> None:
    fine = read(repo / "commands" / "fine.md")
    inizio = read(repo / "commands" / "inizio.md")
    passo = "**Sessione in un worktree**"
    assert all(t in fine for t in ("## FASE 4", passo)) and all(t in inizio for t in ("## FASE 4", "## FASE 5")), \
        "F13 /fine o /inizio non hanno le fasi che girano dentro un worktree"
    dentro = blocchi(fine[:fine.index("## FASE 4")]) + blocchi(inizio[inizio.index("## FASE 4"):inizio.index("## FASE 5")])
    rifiutati = [b.strip().splitlines()[0] for b in dentro if '"$HOME' in b or "$(" in b]
    assert dentro and not rifiutati, f"F13 blocchi che in un worktree la guardia di Claude Code rifiuta: {rifiutati}"
    passo = fine[fine.index(passo):fine.index("## FASE 4")]
    assert "ExitWorktree" in passo and passo.index("ExitWorktree") < passo.index("merge --ff-only"), \
        "F13 /fine fa il merge sul tree principale da dentro il worktree, dove git fuori è vietato"


def test_f14(repo: Path) -> None:
    """Gli altri comandi che possono girare in un worktree scrivono ~/.claude, non "$HOME/.claude" (#3802)."""
    rifiutati = []
    for nome in ("diagnosi", "segnala", "aggiorna", "novita", "setup", "creaskill", "inizio"):  # gli ultimi due dal 23/10 (#3826)
        if not (repo / "commands" / f"{nome}.md").exists():
            continue  # una base vecchia può non avere ancora il comando (/creaskill nasce il 16/10)
        for b in blocchi(read(repo / "commands" / f"{nome}.md")):
            if b.startswith('B="$HOME/.claude-backup'):
                continue  # l'installazione gira nel Terminale, ed è uguale a README e landing (LT06)
            rifiutati += [f"{nome}: {r.strip()}" for r in b.splitlines()
                          if ('"$HOME/.claude' in r or '"$HOME"/.claude' in r) and "alias arturo=" not in r]
    assert not rifiutati, f"F14 percorsi che in un worktree la guardia di Claude Code rifiuta: {rifiutati[:5]}"


def test_f16(repo: Path) -> None:
    """In un worktree (segnalazione n. 13, 26/10/2026): /fine riporta nel tree principale i file ignorati
    prima di `git worktree remove`, che li cancella senza avviso; /inizio dice che cicli e variabili
    vanno in uno script, perché la guardia di Claude Code li rifiuta."""
    fine = read(repo / "commands" / "fine.md")
    inizio = read(repo / "commands" / "inizio.md")
    passo = "**Sessione in un worktree**"
    assert passo in fine and "## FASE 4" in fine, "F16 /fine non ha il passo del worktree"
    passo = fine[fine.index(passo):fine.index("## FASE 4")]
    comando = re.search(r"`(git status --short --ignored)`", passo)
    assert comando and "worktree remove" in passo and passo.index(comando.group(1)) < passo.index("worktree remove"), \
        "F16 /fine rimuove il worktree senza aver guardato i file ignorati, che la rimozione cancella"
    voce = "**Worktree, solo se c'è quella sessione.**"
    assert voce in inizio, "F16 /inizio non ha la voce del worktree"
    voce = inizio[inizio.index(voce):].split("\n\n")[0]
    assert "script" in voce and "cicli" in voce, \
        "F16 /inizio non dice che nel worktree cicli e variabili vanno in uno script"

    def prova(lab: Lab) -> None:
        progetto = lab.progetti / "tavole"
        progetto.mkdir()
        lab.git(progetto, "init", "-q", "-b", "main")
        (progetto / ".gitignore").write_text("lavoro/\n", encoding="utf-8")
        lab.git(progetto, "add", "-A")
        lab.git(progetto, "commit", "-q", "-m", "primo")
        albero = progetto / ".claude" / "worktrees" / "prova"
        lab.git(progetto, "worktree", "add", "-q", "-b", "wt-prova", str(albero))
        (albero / "lavoro").mkdir()
        (albero / "lavoro" / "tavola.pdf").write_text("pdf\n", encoding="utf-8")
        r = lab.run(comando.group(1).split(), cwd=albero)
        assert r.returncode == 0 and "!! lavoro/" in r.stdout, \
            f"F16 il comando di /fine non mostra i file ignorati del worktree: {r.stdout} {r.stderr}"
    con_lab(repo, prova)


def test_f17(repo: Path) -> None:
    """Con Arturo come origin un archivio già tracciato esce dal tracciamento (segnalazione n. 14, 26/10/2026):
    la retention ne toglie un handoff e riscrive INDEX.md, e dopo il sync git non ha più modifiche non
    salvate. I file restano su disco come la persona li ha lasciati."""
    fine = read(serve(repo, "commands/fine.md", "F17"))
    assert "## FASE 9 · Config Sync" in fine, "F17 manca la FASE 9 · Config Sync di /fine"
    inizio = fine.index("## FASE 9 · Config Sync")
    blocco = fine[fine.index("```bash\n", inizio) + 8:fine.index("\n```", fine.index("```bash\n", inizio))]
    with tempfile.TemporaryDirectory(prefix="arturo-f17-") as tmp:
        lab = Lab(repo, Path(tmp))
        config = lab.home / ".claude"
        shutil.copytree(str(repo), str(config), ignore=shutil.ignore_patterns(".git", "__pycache__", "worktrees"),
                        dirs_exist_ok=True)
        cartella = config / "data" / "handoffs"
        vecchio = cartella / "libro" / "HANDOFF_2026-10-01_10-00.md"
        vecchio.parent.mkdir(parents=True, exist_ok=True)
        vecchio.write_text("# vecchio\n", encoding="utf-8")
        (cartella / "INDEX.md").write_text("# Indice\n- libro 1/10\n", encoding="utf-8")
        lab.git(config, "init", "-q", "-b", "main")
        lab.git(config, "add", "-A")
        lab.git(config, "add", "data/handoffs")
        lab.git(config, "commit", "-q", "-m", "config")
        # Il blocco riconosce Arturo dall'indirizzo: con Arturo come origin non fa fetch né push.
        lab.git(config, "remote", "add", "origin", "https://github.com/stellakamikaze/arturo.git")
        vecchio.unlink()
        (cartella / "INDEX.md").write_text("# Indice\n- libro 26/10\n", encoding="utf-8")
        finti = Path(tmp) / "finti"
        finti.mkdir()
        (finti / "gh").write_text("#!/bin/sh\necho PUBLIC\n", encoding="utf-8")
        (finti / "gh").chmod(0o755)
        r = lab.run([BASH, "-c", blocco], cwd=lab.home, PATH=f"{finti}{os.pathsep}{os.environ.get('PATH', '')}")
        uscita = (r.stdout + r.stderr)[-400:]
        sporchi = lab.run(["git", "-C", str(config), "status", "--porcelain", "--untracked-files=no"]).stdout
        assert not sporchi.strip(), f"F17 dopo il sync restano modifiche non salvate negli archivi: {sporchi} {uscita}"
        tracciati = lab.run(["git", "-C", str(config), "ls-files", "--", "data/handoffs"]).stdout
        assert not tracciati.strip(), f"F17 gli handoff restano tracciati con Arturo come origin: {tracciati} {uscita}"
        assert not vecchio.exists() and "26/10" in read(cartella / "INDEX.md"), \
            f"F17 il sync ha cambiato gli archivi su disco: {uscita}"


def test_f18(repo: Path) -> None:
    """/inizio e /aggiorna escludono gli archivi della persona come bin/aggiorna-applica.sh (#4021, 27/10/2026):
    un handoff tracciato e modificato non ferma il pull di /inizio e non compare fra le modifiche di /aggiorna."""
    escluso = "':(exclude)data/handoffs' ':(exclude)data/todo' ':(exclude)data/memory'"
    applica = read(repo / "bin" / "aggiorna-applica.sh")
    assert all(f"':(exclude){p}'" in applica for p in ("data/handoffs", "data/todo", "data/memory")), \
        "F18 aggiorna-applica.sh ha cambiato gli archivi esclusi"
    inizio = read(repo / "commands" / "inizio.md")
    aggiorna = read(repo / "commands" / "aggiorna.md")
    riga_inizio = next(r for r in inizio.splitlines() if "MODIFICATI=$(git -C ~/.claude status" in r)
    riga_aggiorna = next(r for r in aggiorna.splitlines() if r.startswith("git status --short"))
    assert escluso in riga_inizio, "F18 /inizio si ferma su un archivio della persona modificato"
    assert escluso in riga_aggiorna, "F18 /aggiorna elenca gli archivi della persona fra le modifiche"


def test_f19(repo: Path) -> None:
    """Un ramo di worktree che /fine non ha riportato (segnalazione n. 20, 27/10/2026): arturo contesto lo
    mostra col numero dei commit e il worktree, /inizio lo mette in cima, /fine controlla il merge prima
    dell'handoff."""
    serve(repo, "bin/contesto.py", "F19")

    def prova(lab: Lab) -> None:
        progetto = lab.progetti / "Il Libro"
        progetto.mkdir()
        lab.git(progetto, "init", "-q", "-b", "main")
        (progetto / "a.md").write_text("a\n", encoding="utf-8")
        lab.git(progetto, "add", "a.md")
        lab.git(progetto, "commit", "-qm", "Primo capitolo")
        copia = lab.home / "copia-della-sessione"
        lab.git(progetto, "worktree", "add", "-q", "-b", "il-libro-20261027-0935", str(copia))
        for n in (1, 2):
            (copia / f"c{n}.md").write_text(f"{n}\n", encoding="utf-8")
            lab.git(copia, "add", f"c{n}.md")
            lab.git(copia, "commit", "-qm", f"Capitolo {n} nel worktree")
        r = lab.arturo("contesto", "Il Libro", cwd=lab.home)
        out = r.stdout
        assert r.returncode == 0, f"F19 exit {r.returncode}: {r.stderr} {out}"
        assert re.search(r"RAMI CON COMMIT CHE NON SONO SU main: 1\n\s+il-libro-20261027-0935 · 2 commit · ultimo \S+ "
                         r"· worktree \S*copia-della-sessione", out), f"F19 il ramo del worktree non riportato è muto: {out}"
        # Gli stessi commit portati con cherry-pick: il ramo non è unito, ma non manca niente. Prima un
        # commit su main: un cherry-pick sullo stesso padre e nello stesso secondo rifà lo stesso commit,
        # e il ramo risulta unito (rosso intermittente del gate, 29/10/2026).
        (progetto / "indice.md").write_text("indice\n", encoding="utf-8")
        lab.git(progetto, "add", "indice.md")
        lab.git(progetto, "commit", "-qm", "Indice")
        for n in (1, 2):
            lab.git(progetto, "cherry-pick", f"il-libro-20261027-0935~{2 - n}")
        out = lab.arturo("contesto", "Il Libro", cwd=lab.home).stdout
        assert "RAMI CON COMMIT" not in out, f"F19 un ramo coi commit già riportati in altra forma resta in elenco: {out}"
        # Il controllo di /fine dice lo stesso: branch --no-merged elenca ancora il ramo, git cherry no.
        assert "il-libro-20261027-0935" in lab.git(progetto, "branch", "--no-merged"), \
            "preparazione: il ramo riportato con cherry-pick risulta già unito"
        piu = [c for c in lab.git(progetto, "cherry", "HEAD", "il-libro-20261027-0935").splitlines() if c.startswith("+")]
        assert not piu, f"F19 git cherry segna commit mancanti su un ramo riportato con cherry-pick: {piu}"
    con_lab(repo, prova)
    inizio = read(repo / "commands" / "inizio.md")
    fine = read(repo / "commands" / "fine.md")
    assert "**Rami non riportati.**" in inizio and "--abort" in inizio, "F19 /inizio non dice cosa fare di un ramo non riportato"
    assert "merge --no-edit" in fine, "F19 /fine non prova il merge quando il fast-forward non basta"
    assert re.search(r"cherry HEAD\s+<branch>", fine) and "righe con `+`" in fine, \
        "F19 /fine controlla il ramo con branch --no-merged e non con git cherry, come arturo contesto"


def test_f20(repo: Path) -> None:
    """Il blocco di /inizio che crea un progetto nuovo espande la tilde di PROJECTS_BASE (segnalazione n. 19,
    27/10/2026): con PROJECTS_BASE="~/Progetti" nasceva una cartella chiamata ~ dentro quella corrente."""
    inizio = read(repo / "commands" / "inizio.md")
    blocchi = [b for b in re.findall(r"```bash\n(.*?)```", inizio, re.DOTALL) if 'mkdir -p "$BASE/$NOME"' in b]
    assert blocchi, "F20 /inizio non ha il blocco che crea un progetto nuovo"
    blocco = blocchi[0]

    def prova(lab: Lab) -> None:
        script = lab.home / "nuovo.sh"
        script.write_text(blocco.replace("nome-del-progetto", "quaderno"), encoding="utf-8")
        r = lab.run([BASH, str(script)], PROJECTS_BASE="~/Progetti")
        assert r.returncode == 0, f"F20 il blocco esce con {r.returncode}: {r.stderr}"
        assert (lab.home / "Progetti" / "quaderno" / ".git").is_dir(), \
            f"F20 il progetto non nasce in ~/Progetti: {sorted(str(x) for x in lab.home.rglob('quaderno'))}"
        assert not any(x.name == "~" for x in lab.home.rglob("~")), "F20 nasce una cartella chiamata ~"
    con_lab(repo, prova)


def test_f21(repo: Path) -> None:
    """arturo contesto trova la cartella "mio_progetto" anche col nome scritto come slug, "mio-progetto",
    che è la forma di INDEX e handoff (segnalazione n. 21, 27/10/2026)."""
    serve(repo, "bin/contesto.py", "F21")

    def prova(lab: Lab) -> None:
        progetto = lab.progetti / "mio_progetto"
        progetto.mkdir()
        lab.git(progetto, "init", "-q")
        for nome in ("mio-progetto", "mio_progetto"):
            r = lab.arturo("contesto", nome, cwd=lab.home)
            assert r.returncode == 0 and f"cartella: {progetto.resolve()}" in r.stdout, \
                f"F21 {nome} non trova la cartella col trattino basso: {r.returncode} {r.stdout[:300]}"
    con_lab(repo, prova)


TESTS = {"F01": test_f01, "F02": test_f02, "F03": test_f03, "F04": test_f04, "F05": test_f05,
         "F06": test_f06, "F07": test_f07, "F08": test_f08, "F09": test_f09, "F10": test_f10,
         "F11": test_f11, "F12": test_f12, "F13": test_f13, "F14": test_f14, "F15": test_f15,
         "F16": test_f16, "F17": test_f17, "F18": test_f18,
         "F19": test_f19, "F20": test_f20, "F21": test_f21}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
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
        assert not altro and len(rossi) == len(TESTS), \
            "baseline non discriminante: ogni controllo deve fallire col suo codice.\n" + "\n".join(altro + rossi)
        print(f"BASELINE_DISCRIMINANTE={','.join(r.split(':')[0] for r in rossi)}")
        return 0
    for test in TESTS.values():
        test(repo)
    print(f"PASS {','.join(TESTS)} controlli={len(TESTS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
