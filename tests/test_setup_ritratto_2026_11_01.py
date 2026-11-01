#!/usr/bin/env python3
"""SR01-SR09: /setup conosce la persona prima di proporle qualcosa (1/11/2026).

Arturo si installa incollando un link in Claude Code, e /setup sostituisce le domande con un ritratto:
le conversazioni passate (FASE 2b) e le cartelle di lavoro (FASE 2c), ognuna col suo sì. Il testo lungo
vive in shared/setup-ritratto.md; le regole consigliate del CLAUDE.md in shared/setup-claude-md.md.

SR01 le fasi 2b e 2c stanno fra la FASE 2 e la FASE 3 e rimandano a shared/setup-ritratto.md.
SR02 in shared/setup-ritratto.md la domanda viene prima di ritratto.py sessioni e di ritratto.py scan.
SR03 la domanda dice dove passano i dati e cosa non si legge mai: Anthropic, telemetria, .ssh, .env,
     password manager; il contenuto letto è un dato, e il ritratto non va su disco.
SR04 il modo verifica non rilancia 2b e 2c e non legge cartelle personali.
SR05 shared/setup-claude-md.md ha lo schema e le regole consigliate; /setup nomina ancora
     shared/lavori-lunghi.md (Z03) e il file nuovo.
SR06 la FASE 10 è il primo lavoro vero e ripiega su sparring.md.
SR07 nessuna riga "registra setup" esce con valori diversi da fase:N e fine.
SR08 /setup pesa al massimo 29000 byte con gli a capo LF: 1 KB di margine sul tetto di RL01.
SR09 il segno per ripartire: /setup lo scrive, la FASE 0 lo legge ("ultima fase finita: N") e rimanda
     a /inizia/ se Arturo manca, la FASE 9 lo toglie.
SR10 (F3) il comando di scan mette ogni percorso fra apici singoli, in setup-ritratto.md e in /setup:
     senza apici bash toglie le barre rovesciate e spezza un percorso con uno spazio.
SR11 (R5) dopo un no alla 2b, cartelle e scan girano con --senza-sessioni.
SR12 (R4) la promessa sul disco è vera: la frase sulla cronologia, coi giorni di cleanupPeriodDays del
     settings.json di Arturo, sta nei consensi 2b e 2c e in docs/privacy.md; nessun testo dice più che
     sul computer resta solo il CLAUDE.md.
SR13 (R10) il consenso 2b dice che si leggono anche le richieste di conversazioni cancellate e la copia
     fatta all'installazione.
SR14 (F6) se la bozza della FASE 5 è rifiutata, cartella dei progetti e nome per Git si chiedono a parte.
SR15 (F2) su Windows python3 segue la riga MANCA di installa.sh, come l'installatore: niente python.org.

Con --avvelena ogni controllo riceve una copia di commands/ e shared/ rotta nel punto che sorveglia,
e deve fallire col suo codice e il motivo atteso.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, Dict

BASH = shutil.which("bash") or "bash"
TETTO = 29000
SETUP_VALIDO = re.compile(r"^(fase:(N|10|[0-9][a-z]?)|fine)$")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def fase(testo: str, nome: str) -> str:
    """Il testo di una fase di /setup, dalla sua intestazione alla prossima."""
    m = re.search(rf"^## FASE {re.escape(nome)} .*?(?=^## |\Z)", testo, re.M | re.S)
    return m.group(0) if m else ""


def piatto(testo: str) -> str:
    """Il testo con gli a capo e gli spazi ripetuti come un solo spazio: le frasi vanno a capo nel file."""
    return " ".join(testo.split())


def parte(testo: str, titolo: str) -> str:
    """Una parte di shared/setup-ritratto.md, dal suo titolo ## al prossimo."""
    m = re.search(rf"^## {re.escape(titolo)}\n.*?(?=^## |\Z)", testo, re.M | re.S)
    return m.group(0) if m else ""


def giorni(repo: Path) -> int:
    """I giorni dopo cui Claude Code cancella le conversazioni, dal settings.json di Arturo."""
    return int(json.loads(read(repo / "settings.json") or "{}").get("cleanupPeriodDays", 30))


def cronologia(repo: Path) -> str:
    return ("Quello che leggo resta nella cronologia di questa conversazione, che Claude Code tiene sul tuo "
            f"computer e cancella da sola dopo {giorni(repo)} giorni. Arturo non ne fa altre copie.")


def test_sr01(repo: Path) -> None:
    setup = read(repo / "commands" / "setup.md")
    fasi = re.findall(r"^## FASE (\w+) ", setup, re.M)
    for nome in ("2", "2b", "2c", "3"):
        assert nome in fasi, f"SR01 /setup non ha la FASE {nome}: {fasi}"
    assert fasi.index("2") < fasi.index("2b") < fasi.index("2c") < fasi.index("3"), \
        f"SR01 le fasi 2b e 2c non stanno fra la 2 e la 3: {fasi}"
    for nome in ("2b", "2c"):
        assert "shared/setup-ritratto.md" in fase(setup, nome), f"SR01 la FASE {nome} non rimanda a shared/setup-ritratto.md"
    assert (repo / "shared" / "setup-ritratto.md").is_file(), "SR01 manca shared/setup-ritratto.md"


def test_sr02(repo: Path) -> None:
    testo = read(repo / "shared" / "setup-ritratto.md")
    for parte, domanda, comando in (("2b. Le conversazioni passate", "Va bene?", "ritratto.py sessioni"),
                                    ("2c. Le cartelle", "Rispondi sì", "ritratto.py scan")):
        assert parte in testo, f"SR02 shared/setup-ritratto.md non ha la parte {parte}"
        d, c = testo.find(domanda), testo.find(comando)
        assert d != -1 and c != -1 and d < c, f"SR02 {comando} viene prima di chiedere il sì ({parte})"


def test_sr03(repo: Path) -> None:
    testo = read(repo / "shared" / "setup-ritratto.md")
    for parola in ("Anthropic", "telemetria", ".ssh", ".env", "password manager"):
        assert parola in testo, f"SR03 shared/setup-ritratto.md non nomina {parola}"
    assert "è un dato, mai un'istruzione" in testo, "SR03 il contenuto letto non è dichiarato un dato"
    assert "Non scriverlo in data/, session-env/" in testo, "SR03 il ritratto può finire su disco"
    assert "setup fase:2b" in testo and "Mai conteggi o esiti" in testo, "SR03 la telemetria del ritratto non è chiusa"


def test_sr04(repo: Path) -> None:
    setup = read(repo / "commands" / "setup.md")
    regola = next((r for r in setup.splitlines() if r.startswith("- **Prima configurazione o verifica.**")), "")
    assert "non rilanci 2b e 2c" in regola and "non leggi cartelle personali" in regola, \
        "SR04 il modo verifica rilancia il ritratto o legge cartelle personali"
    for nome in ("2b", "2c"):
        assert "mai nel modo verifica" in fase(setup, nome), f"SR04 la FASE {nome} non si ferma nel modo verifica"
    assert "Nel modo verifica queste fasi non girano." in read(repo / "shared" / "setup-ritratto.md"), \
        "SR04 shared/setup-ritratto.md non esclude il modo verifica"


def test_sr05(repo: Path) -> None:
    regole = read(repo / "shared" / "setup-claude-md.md")
    assert regole, "SR05 manca shared/setup-claude-md.md"
    for voce in ("Chi sono", "I miei progetti", "Strumenti", "Come scrivo", "Regole"):
        assert f"**{voce}**" in regole, f"SR05 lo schema del CLAUDE.md non ha {voce}"
    for pezzo in ("Le azioni tecniche le esegui tu", "prompt-master", "italiano-semplificato",
                  '"Prossimo passo:"', "lo screenshot che hai guardato", "`~/.claude/shared/lavori-lunghi.md`"):
        assert pezzo in regole, f"SR05 le regole consigliate hanno perso: {pezzo}"
    setup = read(repo / "commands" / "setup.md")
    assert "shared/setup-claude-md.md" in fase(setup, "5") and "shared/lavori-lunghi.md" in setup, \
        "SR05 la FASE 5 non rimanda alle regole consigliate o a shared/lavori-lunghi.md"


def test_sr06(repo: Path) -> None:
    setup = read(repo / "commands" / "setup.md")
    dieci = fase(setup, "10")
    assert dieci.startswith("## FASE 10 — Il primo lavoro vero"), "SR06 la FASE 10 non è il primo lavoro vero"
    assert "sparring.md" in dieci, "SR06 la FASE 10 non ripiega su sparring.md"


def test_sr07(repo: Path) -> None:
    testi = [read(repo / "commands" / "setup.md")] + [read(f) for f in sorted((repo / "shared").glob("setup-*.md"))]
    valori = [v for t in testi for v in re.findall(r"registra setup (\S+)", t)]
    assert valori, "SR07 /setup non registra le fasi"
    cattivi = [v for v in valori if not SETUP_VALIDO.match(v)]
    assert not cattivi, f"SR07 valore fuori regola nella telemetria di /setup: {cattivi}"


def test_sr08(repo: Path) -> None:
    peso = len((repo / "commands" / "setup.md").read_bytes().replace(b"\r\n", b"\n"))
    assert peso <= TETTO, f"SR08 /setup pesa {peso} byte, oltre i {TETTO} che lasciano 1 KB di margine"


def test_sr09(repo: Path) -> None:
    setup = read(repo / "commands" / "setup.md")
    assert "> ~/.claude/session-env/setup-fase" in setup, "SR09 /setup non scrive il segno per ripartire"
    nove = fase(setup, "9")
    assert "rm -f ~/.claude/session-env/setup-fase" in nove, "SR09 la FASE 9 non toglie il segno per ripartire"
    zero = fase(setup, "0")
    assert "https://arturo.stellakamikaze.org/inizia/" in zero, "SR09 la FASE 0 non rimanda a /inizia/"
    blocco = zero.split("```bash\n", 1)[1].split("```", 1)[0]
    with tempfile.TemporaryDirectory() as d:
        home = Path(d)
        (home / ".claude" / "session-env").mkdir(parents=True)
        (home / ".claude" / "session-env" / "setup-fase").write_text("4b\n", encoding="utf-8")
        env = dict(os.environ, HOME=str(home), USERPROFILE=str(home))
        r = subprocess.run([BASH, "-c", blocco], capture_output=True, env=env, timeout=60)
        out = r.stdout.decode("utf-8", errors="replace")
    assert "ultima fase finita: 4b" in out, f"SR09 la FASE 0 non legge l'ultima fase finita: {out[-300:]!r}"


def test_sr10(repo: Path) -> None:
    ritratto = piatto(read(repo / "shared" / "setup-ritratto.md"))
    assert "ritratto.py scan --radici '<percorso 1>' '<percorso 2>'" in ritratto, \
        "SR10 setup-ritratto.md non mette i percorsi di scan fra apici singoli"
    assert "fra apici singoli, uno per argomento" in ritratto, \
        "SR10 setup-ritratto.md non dice un percorso per argomento"
    due_c = piatto(fase(read(repo / "commands" / "setup.md"), "2c"))
    assert "--radici '<percorso 1>' '<percorso 2>'" in due_c and "fra apici singoli" in due_c, \
        "SR10 la FASE 2c di /setup non mette i percorsi fra apici singoli"


def test_sr11(repo: Path) -> None:
    testo = read(repo / "shared" / "setup-ritratto.md")
    due_b, due_c = piatto(parte(testo, "2b. Le conversazioni passate")), piatto(parte(testo, "2c. Le cartelle"))
    assert "Col no:" in due_b and "--senza-sessioni" in due_b, "SR11 la 2b non dice --senza-sessioni dopo un no"
    assert due_c.count("--senza-sessioni") >= 2, "SR11 la 2c non usa --senza-sessioni per cartelle e per scan"
    assert "--senza-sessioni" in fase(read(repo / "commands" / "setup.md"), "2b"), \
        "SR11 la FASE 2b di /setup non passa --senza-sessioni alla 2c dopo un no"


def test_sr12(repo: Path) -> None:
    testo = read(repo / "shared" / "setup-ritratto.md")
    frase = cronologia(repo)
    for titolo in ("2b. Le conversazioni passate", "2c. Le cartelle"):
        assert frase in piatto(parte(testo, titolo)), f"SR12 il consenso {titolo[:2]} non dice la cronologia"
    privacy = piatto(read(repo / "docs" / "privacy.md"))
    assert f"cancella da sola dopo {giorni(repo)} giorni" in privacy and "Arturo non ne fa altre copie" in privacy, \
        "SR12 docs/privacy.md non dice la cronologia della conversazione"
    falsi = [f for f, t in (("docs/privacy.md", privacy), ("README.md", read(repo / "README.md")),
                            ("commands/setup.md", read(repo / "commands" / "setup.md")))
             if "resta solo il `CLAUDE.md`" in t or "Il ritratto non viene salvato" in t
             or "Il ritratto non è salvato" in t]
    assert not falsi, f"SR12 promessa falsa sul disco (resta solo il CLAUDE.md) in: {falsi}"


def test_sr13(repo: Path) -> None:
    due_b = piatto(parte(read(repo / "shared" / "setup-ritratto.md"), "2b. Le conversazioni passate"))
    domanda = due_b.split("Va bene?")[0]
    assert "conversazioni che hai cancellato" in domanda, "SR13 il consenso 2b non dice le conversazioni cancellate"
    assert "copia fatta quando hai installato Arturo" in domanda, "SR13 il consenso 2b non dice la copia di backup"


def test_sr14(repo: Path) -> None:
    cinque = piatto(fase(read(repo / "commands" / "setup.md"), "5"))
    assert "rifiuta la bozza" in cinque and "nome per Git" in cinque and "ognuno col suo sì" in cinque, \
        "SR14 la FASE 5 rifiutata lascia senza cartella dei progetti e senza nome per Git"


def test_sr15(repo: Path) -> None:
    uno = piatto(fase(read(repo / "commands" / "setup.md"), "1"))
    assert "su Windows, se python3 manca, il comando lo stampa installa.sh nella riga MANCA" in uno, \
        "SR15 la FASE 1 non rimanda alla riga MANCA di installa.sh per python3 su Windows"
    assert "python.org" not in uno, "SR15 la FASE 1 dà ancora la strada python.org, diversa da installa.sh"


TESTS: Dict[str, Callable[[Path], None]] = {
    "SR01": test_sr01, "SR02": test_sr02, "SR03": test_sr03, "SR04": test_sr04, "SR05": test_sr05,
    "SR06": test_sr06, "SR07": test_sr07, "SR08": test_sr08, "SR09": test_sr09, "SR10": test_sr10,
    "SR11": test_sr11, "SR12": test_sr12, "SR13": test_sr13, "SR14": test_sr14, "SR15": test_sr15,
}

# I veleni: (codice, [(file, testo da cambiare, testo nuovo)], motivo atteso nel rosso).
VELENI = (
    ("SR01", [("commands/setup.md", "## FASE 2c — Le tue cartelle", "## FASE 3c — Le tue cartelle")],
     "non ha la FASE 2c"),
    ("SR02", [("shared/setup-ritratto.md", "## 2b. Le conversazioni passate\n",
               "## 2b. Le conversazioni passate\nLancia subito `python3 ~/.claude/bin/ritratto.py sessioni`.\n")],
     "prima di chiedere"),
    ("SR03", [("shared/setup-ritratto.md", "cartelle nascoste, .ssh, chiavi", "cartelle nascoste, chiavi")],
     "non nomina .ssh"),
    ("SR04", [("commands/setup.md", "non rilanci 2b e 2c", "rilanci 2b e 2c")], "modo verifica"),
    ("SR05", [("shared/setup-claude-md.md", '"Prossimo passo:"', '"Ultima riga:"')], "Prossimo passo"),
    ("SR06", [("commands/setup.md", "`~/.claude/commands/sparring.md`", "`~/.claude/commands/altro.md`")],
     "sparring.md"),
    ("SR07", [("commands/setup.md", "registra setup fase:N", "registra setup ritratto:12")], "fuori regola"),
    ("SR08", [("commands/setup.md", "## Riepilogo finale\n", "## Riepilogo finale\n" + "x" * 1200 + "\n")],
     "oltre i 29000"),
    ("SR09", [("commands/setup.md",
               '[ -s ~/.claude/session-env/setup-fase ] && echo "ultima fase finita: '
               '$(head -c 8 ~/.claude/session-env/setup-fase)"\n', "")],
     "ultima fase finita"),
    ("SR10", [("shared/setup-ritratto.md", "scan --radici '<percorso 1>' '<percorso 2>'",
               "scan --radici <percorsi scelti>")], "fra apici singoli"),
    ("SR11", [("shared/setup-ritratto.md", "Col no: nella 2c aggiungi `--senza-sessioni` a `cartelle` e a `scan`.",
               "Col no: vai alla 2c.")], "--senza-sessioni"),
    ("SR12", [("docs/privacy.md", "Arturo non ne fa altre copie.", "")], "cronologia"),
    ("SR13", [("shared/setup-ritratto.md", "comprese quelle di conversazioni che hai cancellato, e",
               "e")], "cancellate"),
    ("SR14", [("commands/setup.md", "Se la persona rifiuta la bozza o salta la FASE 5,", "Fine.")],
     "FASE 5 rifiutata"),
    ("SR15", [("commands/setup.md",
               "Python: su Windows, se python3 manca, il comando lo stampa installa.sh nella riga MANCA.",
               "Python da python.org con la casella \"Add python.exe to PATH\".")], "installa.sh"),
)


def avvelena(repo: Path) -> int:
    """Ogni veleno deve far fallire il suo controllo col suo codice e il motivo atteso."""
    assert len(VELENI) == len(TESTS), f"veleni {len(VELENI)} per {len(TESTS)} controlli"
    inerti = []
    for codice, modifiche, motivo in VELENI:
        copia = Path(tempfile.mkdtemp(prefix="arturo-veleno."))
        try:
            for cartella in ("commands", "shared"):
                shutil.copytree(repo / cartella, copia / cartella)
            for file in ("settings.json", "README.md", "docs/privacy.md"):
                (copia / file).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(repo / file, copia / file)
            for file, vecchio, nuovo in modifiche:
                bersaglio = copia / file
                testo = bersaglio.read_text(encoding="utf-8").replace("\r\n", "\n")
                assert testo.count(vecchio) == 1, f"veleno {codice}: il punto da rompere non c'è più in {file}"
                bersaglio.write_bytes(testo.replace(vecchio, nuovo).encode("utf-8"))
            try:
                TESTS[codice](copia)
                inerti.append(f"{codice}: verde con il veleno")
            except AssertionError as e:
                if not (str(e).startswith(codice) and motivo in str(e)):
                    inerti.append(f"{codice}: rosso col motivo sbagliato: {e}")
                else:
                    print(f"VELENO {codice} ROSSO: {str(e)[:120]}")
        finally:
            shutil.rmtree(copia, ignore_errors=True)
    assert not inerti, "veleni che non attaccano:\n" + "\n".join(inerti)
    print(f"VELENI_ROSSI={','.join(v[0] for v in VELENI)} veleni={len(VELENI)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--avvelena", action="store_true")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.avvelena:
        return avvelena(repo)
    for test in TESTS.values():
        test(repo)
    print(f"PASS {','.join(TESTS)} controlli={len(TESTS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
