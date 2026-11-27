#!/usr/bin/env python3
"""SG01-SG08: le segnalazioni n. 36, 37, 38, 40 e 41 di fine ottobre 2026, lette il 2/11/2026.

SG01 il classificatore della modalità auto ferma un passo già approvato senza offrire una conferma:
     la scrittura di brew shellenv in ~/.zprofile (n. 36), il touch dello sblocco di una guardia (n. 38),
     un aggiornamento via ssh (n. 41). Lo stile Conciso dice di preparare un solo comando con `!`, dà la
     riga di Homebrew e avvisa che un LaunchAgent non scrive in iCloud Drive, Documenti e Scrivania.
SG02 la guardia dei percorsi di avvio automatico e quella dei file di config dicevano a Claude
     "esegui: touch ~/.claude/system-unlock-..." e "config-unlock-...": in modalità auto il classificatore
     lo ferma come [Self-Modification]. Lo sblocco resta alla persona: il messaggio le fa lanciare il
     touch col prefisso `!`.
SG03 un progetto fuori dalle cartelle della sessione fa tornare la shell alla cartella di partenza a ogni
     comando (n. 37): /inizio propone /add-dir e, con /fine, apre i comandi con `cd "<cartella>" &&`.
     Dopo /chrome a sessione aperta gli strumenti arrivano solo con claude --continue (n. 40).
SG04 con due Chrome collegati Claude resta sul browser scelto per deviceId e, dopo una disconnessione,
     controlla inUse e lo dice (n. 44, 3/11/2026).
SG05 prima di aprire per la persona Claude sceglie la macchina: quella nominata, questa se è interattiva,
     altrimenti la macchina davanti di Volta (volta_davanti.py leggi) o una domanda (#5881, 17/11/2026).
SG06 Claude usa il browser che la persona nomina, ne carica la skill prima di ripiegare su un altro server
     MCP del browser, e prima di toccare i dati di un account dice quale account è collegato (n. 74, #5600).
SG07 un elenco di più di 30 righe va in un file aperto alla persona, in chat il conteggio (proposta n. 76),
     e il brief chiede una riga d'esempio per un foglio di un terzo con colonne ambigue (proposta n. 82).
SG08 prima della prima scrittura su un sito con più account o spazi Claude apre il menu dell'account,
     confronta il nome con quello atteso e, se non coincide o non è chiaro, chiede (n. 96, #6359).

Sulla base 8b141c0 ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_sg01(repo: Path) -> None:
    stile = read(repo / "output-styles" / "conciso.md")
    titolo = "## I comandi che lancia la persona"
    assert titolo in stile, "SG01 lo stile Conciso non ha la sezione dei comandi della persona"
    sezione = stile[stile.index(titolo):]
    sezione = sezione[:sezione.find("\n## ", 1)] if "\n## " in sezione[1:] else sezione
    for pezzo in ("auto mode classifier", "`!`", "brew shellenv", "~/.zprofile", "LaunchAgent", "iCloud Drive"):
        assert pezzo in sezione, f"SG01 la sezione dei comandi della persona non dice: {pezzo}"


def messaggio(repo: Path, relativo: str) -> str:
    """La ragione del deny di protect_claude_md.py per un Write su ~/<relativo>, in una home finta."""
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        hooks = home / ".claude" / "hooks"
        hooks.mkdir(parents=True)
        (hooks / "protect_claude_md.py").write_text(read(repo / "hooks" / "protect_claude_md.py"), encoding="utf-8")
        bersaglio = home / relativo
        bersaglio.parent.mkdir(parents=True, exist_ok=True)
        bersaglio.write_text("riga\n", encoding="utf-8")
        env = {**os.environ, "HOME": str(home), "USERPROFILE": str(home), "ARTURO_TELEMETRIA": "0"}
        ingresso = {"tool_name": "Edit", "session_id": "sg02",
                    "tool_input": {"file_path": str(bersaglio), "old_string": "riga", "new_string": "altra"}}
        p = subprocess.run([sys.executable, "-B", str(hooks / "protect_claude_md.py")], input=json.dumps(ingresso),
                           capture_output=True, text=True, encoding="utf-8", env=env, timeout=30)
        uscita = json.loads(p.stdout)["hookSpecificOutput"] if p.stdout.strip() else {}
        return uscita.get("permissionDecision", "") + " " + uscita.get("permissionDecisionReason", "")


def test_sg02(repo: Path) -> None:
    for relativo, sblocco in (("Library/LaunchAgents/com.prova.backup.plist", "system-unlock"),
                              (".claude/hooks/mia-guardia.py", "config-unlock")):
        m = messaggio(repo, relativo)
        assert m.startswith("deny"), f"SG02 {relativo} non è più protetto: {m[:200]}"
        assert f"! touch ~/.claude/{sblocco}-sg02" in m, \
            f"SG02 lo sblocco di {relativo} non passa alla persona col prefisso !: {m[:300]}"


def test_sg03(repo: Path) -> None:
    inizio, fine = read(repo / "commands" / "inizio.md"), read(repo / "commands" / "fine.md")
    for nome, testo in (("inizio", inizio), ("fine", fine)):
        assert "Shell cwd was reset" in testo and 'cd "<cartella' in testo, \
            f"SG03 /{nome} non dice cosa fare se la shell torna alla cartella di partenza"
    assert "/add-dir" in inizio, "SG03 /inizio non propone /add-dir per una cartella fuori dalla sessione"
    stile = read(repo / "output-styles" / "conciso.md")
    assert "/chrome" in stile and "claude --continue" in stile, \
        "SG03 lo stile non dice che dopo /chrome serve claude --continue"


def test_sg04(repo: Path) -> None:
    stile = read(repo / "output-styles" / "conciso.md")
    for pezzo in ("deviceId", "list_connected_browsers", "inUse", "select_browser", "segnalazione n. 44"):
        assert pezzo in stile, f"SG04 lo stile non dice come restare sul Chrome scelto: manca {pezzo}"


def test_sg05(repo: Path) -> None:
    stile = read(repo / "output-styles" / "conciso.md")
    for pezzo in ("scegli la macchina", "`python3 ~/.config/herdr-app/mods/arturo/volta_davanti.py leggi`",
                  "Se dice \"ignota\", o lo script manca, chiedi una", "\"Apro sul MacBook, in"):
        assert pezzo in stile, f"SG05 lo stile non dice come scegliere la macchina davanti: manca {pezzo}"


def test_sg06(repo: Path) -> None:
    stile = " ".join(read(repo / "output-styles" / "conciso.md").split())
    for pezzo in ("Quando la persona nomina un browser", "carica la skill di quel browser prima di ogni altra via",
                  "Un altro server MCP del browser vale solo col sì della persona", "`tabs_context_mcp`",
                  "segnalazione n. 74", "Prima di cercare o modificare i dati di un account",
                  "\"Uso il Chrome con l'account del lavoro\"", "Permission denied"):
        assert pezzo in stile, f"SG06 lo stile non dice quale browser e quale account usare: manca {pezzo}"


def test_sg07(repo: Path) -> None:
    stile = " ".join(read(repo / "output-styles" / "conciso.md").split())
    for pezzo in ("## Gli elenchi lunghi", "più di 30 righe", "apri il file alla persona", "In chat restano il conteggio",
                  "proposta n. 76"):
        assert pezzo in stile, f"SG07 lo stile non dice dove va un elenco lungo: manca {pezzo}"
    brief = " ".join(read(repo / "skills" / "prompt-master" / "SKILL.md").split())
    for pezzo in ("chiede una riga d'esempio", "arriva da un terzo", "proposta n. 82"):
        assert pezzo in brief, f"SG07 il brief non chiede la riga d'esempio per un foglio ambiguo: manca {pezzo}"



def test_sg08(repo: Path) -> None:
    stile = " ".join(read(repo / "output-styles" / "conciso.md").split())
    for pezzo in ("Prima della prima scrittura su un sito con più account", "apri il menu dell'account",
                  "confronta il nome con quello atteso", "Una pagina quasi vuota",
                  "Se il nome non coincide o non è chiaro, chiedi prima di scrivere", "segnalazione n. 96"):
        assert pezzo in stile, f"SG08 lo stile non fa controllare l'account prima della prima scrittura: manca {pezzo}"


TESTS = {"SG01": test_sg01, "SG02": test_sg02, "SG03": test_sg03, "SG04": test_sg04, "SG05": test_sg05,
         "SG06": test_sg06, "SG07": test_sg07, "SG08": test_sg08}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--baseline-ref")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.baseline_ref:
        # Il gate passa in --repo la copia della base estratta con git archive, come per gli altri banchi.
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
