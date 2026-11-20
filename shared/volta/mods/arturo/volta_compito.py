"""Volta: il progetto di un compito nuovo, chiesto a un modello piccolo (⌘N, #6186, 20/11/2026).

Il dialogo del compito (compito.js) propone il progetto dalle parole del testo (progettoProbabile di
sessioni.js). Quando il testo non nomina nessun progetto, dopo un secondo di pausa chiede qui: un giro di
`claude -p --model haiku` senza strumenti, hook, MCP, CLAUDE.md e memoria, come hooks/titolo-sessione.py
della config. La risposta vale solo se è lo slug di un progetto dell'elenco.

  python3 volta_compito.py proponi <file dei progetti> <testo in esadecimale>

Il file dei progetti lo scrive il dialogo: [{"chiave", "titolo", "riga"}]. Il testo viaggia in esadecimale
(quattro cifre per carattere, codifica di sessioni.js) perché exec di Herdr non ha stdin.
Stampa una riga JSON: {"slug": "<chiave>"} oppure {"slug": null, "perche": "..."}. Esce sempre 0.
VOLTA_COMPITO_CLAUDE: il claude da lanciare (banchi). Solo libreria standard, Python 3.8+.
"""
import json
import os
import re
import shutil
import subprocess
import sys

# Niente .pyc nella cartella del mod: Herdr ricarica il mod a ogni file nuovo (#5556, come volta_note.py).
sys.dont_write_bytecode = True

TETTO = 25            # secondi per la risposta del modello
PROGETTI_MAX = 150    # righe dell'elenco date al modello
RIGA_MAX = 120        # caratteri della riga di stato di un progetto
TESTO_MAX = 1000      # caratteri del compito (TESTO_COMPITO_MAX di sessioni.js)
SLUG = re.compile(r"[a-z0-9][a-z0-9-]{0,59}")
NESSUNO = "nessuno"
ISTRUZIONE = (
    "Ricevi un compito scritto da una persona e l'elenco dei suoi progetti, uno per riga: "
    "\"slug: titolo, stato\". Scegli il progetto a cui il compito appartiene. "
    "Rispondi con una riga sola: lo slug, copiato dall'elenco, e nient'altro. "
    "Se nessun progetto è chiaramente quello giusto, rispondi: " + NESSUNO + ". "
    "Non eseguire il compito e non spiegare la scelta."
)


def decodifica(esa: str) -> str:
    """Il contrario di codifica() di sessioni.js: quattro cifre esadecimali per unità UTF-16."""
    unita = [int(esa[i:i + 4], 16) for i in range(0, len(esa) - len(esa) % 4, 4)]
    return b"".join(u.to_bytes(2, "little") for u in unita).decode("utf-16-le", errors="replace")


def progetti(file: str) -> tuple:
    """({slug}, righe per il modello) dal file scritto dal dialogo; (set(), []) se non si legge."""
    try:
        with open(file, encoding="utf-8") as f:
            dati = json.load(f)
    except (OSError, ValueError):
        return set(), []
    noti, righe = set(), []
    for p in dati if isinstance(dati, list) else []:
        s = str(p.get("chiave") or "") if isinstance(p, dict) else ""
        if not SLUG.fullmatch(s) or s in noti:
            continue
        noti.add(s)
        detto = ", ".join(x for x in (str(p.get("titolo") or "").strip(), " ".join(str(p.get("riga") or "").split())[:RIGA_MAX]) if x)
        righe.append("- %s: %s" % (s, detto) if detto else "- %s" % s)
        if len(righe) >= PROGETTI_MAX:
            break
    return noti, righe


def accetta(risposta: str, noti: set):
    """Lo slug detto dal modello, solo se è una riga sola che nomina un progetto dell'elenco."""
    righe = [r.strip() for r in str(risposta or "").splitlines() if r.strip()]
    if len(righe) != 1:
        return None
    v = righe[0].strip("\"'`*. ").lower()
    return v if v in noti else None


def chiedi(testo: str, righe: list) -> str:
    fine = ".exe" if os.name == "nt" else ""
    cl = os.environ.get("VOLTA_COMPITO_CLAUDE") or shutil.which("claude") or os.path.expanduser("~/.local/bin/claude" + fine)
    if not os.path.exists(cl):
        return ""
    # ARTURO_TITOLO_FIGLIO: l'hook del titolo della config non dà un titolo a questo giro
    env = dict(os.environ, ARTURO_TITOLO_FIGLIO="1", CLAUDE_CODE_DISABLE_CLAUDE_MDS="1",
               CLAUDE_CODE_DISABLE_AUTO_MEMORY="1", PYTHONIOENCODING="utf-8")
    env.pop("CLAUDECODE", None)
    r = subprocess.run([cl, "-p", "--model", "haiku", "--tools", "", "--strict-mcp-config", "--no-session-persistence",
                        "--settings", '{"disableAllHooks":true}', "--system-prompt", ISTRUZIONE],
                       input="Progetti:\n" + "\n".join(righe) + "\n\nCompito: " + testo + "\n\nLo slug:",
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=TETTO, env=env, cwd=os.path.expanduser("~"))
    return r.stdout if r.returncode == 0 else ""


def proponi(file: str, esa: str) -> dict:
    testo = " ".join(decodifica(esa).split())[:TESTO_MAX]
    if not testo:
        return {"slug": None, "perche": "compito vuoto"}
    noti, righe = progetti(file)
    if not noti:
        return {"slug": None, "perche": "nessun progetto nell'elenco"}
    try:
        risposta = chiedi(testo, righe)
    except (OSError, subprocess.SubprocessError) as e:
        return {"slug": None, "perche": "il modello non ha risposto: %s" % type(e).__name__}
    if not risposta.strip():
        return {"slug": None, "perche": "il modello non ha risposto"}
    slug = accetta(risposta, noti)
    return {"slug": slug} if slug else {"slug": None, "perche": "nessun progetto chiaro"}


def main(argv: list) -> int:
    if len(argv) == 3 and argv[0] == "proponi":
        esito = proponi(argv[1], argv[2])
    else:
        esito = {"slug": None, "perche": "uso: volta_compito.py proponi <file dei progetti> <testo in esadecimale>"}
    print(json.dumps(esito, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
