#!/usr/bin/env python3
"""La sessione continua da sola quando il passo dopo è di Claude (Stop, 24/11/2026).

Il 24/11/2026 una sessione ha chiuso il turno con "il prossimo passo è mio" e si è fermata: la persona ha
dovuto scrivere "procedi". La regola (un passo reversibile di Claude si esegue nello stesso turno) era solo
testo. Questo hook la fa valere: su Stop legge l'ultimo testo di Claude (fine_turno.py, comune con
carta-sessione.py) e, se la fine dice che il passo è di Claude, risponde con decision "block". Claude Code
allora non chiude il turno e passa il motivo a Claude, che esegue il passo.

Continua solo se, nelle ultime FINESTRA battute:
- c'è una frase del passo mio (PASSO_MIO): "il prossimo passo è mio", "il passo dopo è mio",
  "Prossimo passo: ... (io)", "Prossimo passo: io ...", "Prossimo passo: ... faccio io";
- e non c'è una domanda (chiede() di fine_turno.py, la regola della Coda di Volta);
- né un rinvio (RINVIO: "quando finisce", "appena", "alla prossima", "domani", "dal 25/11");
- né una parola di freno (FRENO: conferma, password, 2FA, OTP, invio, pagamento, firma, sblocco, una
  riga con un comando `! `);
- né la rotazione (una riga "ruoto:", "ruoto adesso", "dopo la rotazione", o il tool ruota chiamato
  nel turno), perché la rotazione ha già il suo giro.
Senza PASSO_MIO l'hook guarda solo la chiusura del turno (#6403, chiusura()): un passo di Claude passato alla
persona, il via chiesto per un lavoro di Claude, un controllo promesso a un'ora senza un richiamo armato nel
turno. Ognuna dà un block col suo motivo una volta sola: col secondo Stop (stop_hook_active) tace, perché un hook
Stop che blocca ogni turno chiude la sessione in un giro infinito (errore-comune-impeccable-stop-hook-blocca-turni).

Tetto: al massimo TETTO continuazioni di fila senza un messaggio della persona. Il conto sta in
<CLAUDE_CONFIG_DIR o ~/.claude>/cache/continua/<sessione>, e `hub.py prompt` lo azzera (azzera()). Anche
con stop_hook_active vero (Claude sta già continuando per un hook Stop) il giro conta verso il tetto.
Ogni block e ogni tetto raggiunto lasciano una riga in cache/continua/registro.jsonl, tenuto sotto
REGISTRO_TETTO byte.

Lo stato verso Herdr (25/11/2026, #6594): fino a 0.2.25 un hook Stop a parte (`herdr-stato.sh done`) girava in
parallelo a questo e segnava fatto anche il turno che questo hook faceva continuare. Ora lo stato di fine
turno lo manda solo questo hook, dopo la decisione: "working" se continua, "done" in ogni altro caso, anche
con l'hook spento o rotto. Fuori da Herdr (HC_TERMINAL_ID vuoto) non parte nessun processo.

Si spegne con ARTURO_CONTINUA=0, e non gira dentro la chiamata al modello di titolo-sessione.py
(ARTURO_TITOLO_FIGLIO), dove tace anche verso Herdr. Ogni errore: exit 0 in silenzio. Solo libreria standard,
Python 3.8+. Banco: tests/test_continua.py (CN01-CN09).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from fine_turno import CODA, chiede, testo_del_turno  # noqa: E402
from radici import radice_orsa  # noqa: E402

FINESTRA = 300       # battute dal fondo del testo
TETTO = 3            # continuazioni di fila senza un messaggio della persona
REGISTRO_TETTO = 200_000
MOTIVO = ("Il passo dopo è tuo e reversibile: eseguilo ora, nello stesso turno. "
          "Se tocca un freno, fermati e dillo.")

PASSO_MIO = [
    re.compile(r"\b(?:il\s+)?prossimo\s+passo\s+(?:è|e'|resta)\s+mio\b", re.I),
    re.compile(r"\b(?:il\s+)?passo\s+dopo\s+(?:è|e'|resta)\s+mio\b", re.I),
    re.compile(r"\bprossimo\s+passo\b[^\n]{0,200}\((?:io|faccio\s+io|mio)\)", re.I),
    re.compile(r"\bprossimo\s+passo\s*:\s*(?:[*_]+\s*)?io\b", re.I),
    re.compile(r"\bprossimo\s+passo\b[^\n]{0,200}(?<!\bnon )(?<!\bnon lo )\bfaccio\s+io\b", re.I),
]
FRENO = [
    re.compile(r"\bconferm\w*|\bpassword\b|\b2FA\b|\bOTP\b|\bsblocc\w*|\bfren[oi]\b", re.I),
    re.compile(r"\binvi(?:o|are|arla|arlo|arle|arli|ata|ato|ate|ati|a|i)\b|\bpagament\w*|\bpaga(?:re)?\b|\bfirm(?:a|are|arla|arlo)\b", re.I),
    re.compile(r"^\s*`?!\s*\S", re.M),
    re.compile(r"\btuo\s+(?:via|ok|s[iì])\b|\bsenza\s+il\s+tuo\b", re.I),
]
# Un passo mio ma per dopo, nella riga stessa del passo: "quando finisce", "appena è accesa", "alla prossima
# apertura", "dal 25/11". Sui transcript del 17-24/11 erano cinque block su dieci: continuare lì fa provare
# adesso un passo che aspetta altro.
RINVIO = re.compile(r"\bquando\b|\bappena\b|\balla\s+prossima\b|\bla\s+prossima\s+volta\b|\bdomani\b|\bdomattina\b|\bstasera\b|\bstanotte\b"
                    r"|\bpiù\s+tardi\b|\b(?:dal|dopo\s+il|entro\s+il)\s+\d", re.I)
# La rotazione ha già il suo giro: una riga "ruoto:", e anche "ruoto adesso", "dopo la rotazione", "riparte
# da sola col contesto pulito". Sui transcript del 17-24/11 sei block su otto cadevano su turni così, e
# continuare lì toglie il /clear che la rotazione ha appena armato.
RUOTO = re.compile(r"^\s*(?:\W\s*)?ruoto:|\bruot(?:o|a|are|iamo)\b|\brotazion[ei]\b|\bripart[eo]\s+da\s+sol[ao]\b"
                   r"|\bcontesto\s+pulito\b", re.I | re.M)
TOOL_RUOTA = re.compile(r"(?:^|__)ruota$")

# La chiusura del turno (#6403, 26/11/2026). Tre forme dello stesso difetto, misurate sui transcript del 16-26/11
# (3000 chiusure): un passo di Claude passato alla persona (4), il via chiesto per un lavoro di Claude (8), un
# controllo promesso per più tardi senza niente che richiami la sessione (6). Ognuna dà un block col suo motivo,
# una volta sola per turno: con stop_hook_active vero (Claude sta già rispondendo a un block) tacciono, così
# Claude può chiudere di nuovo se il passo era davvero della persona. I menu (AskUserQuestion) con un'opzione di via
# erano 2 su 100, tutti scelte vere: niente controllo lì.
MOTIVO_PASSATO = ("La chiusura passa alla persona un passo tuo (/clear e /inizio, la rotazione, un messaggio a "
                  "un'altra sessione): fallo tu ora, col tool ruota o con SendMessage.")
MOTIVO_VIA = ("La chiusura chiede il via per un lavoro tuo e reversibile: eseguilo ora, nello stesso turno. "
              "Se è un freno o una scelta di direzione, chiudi dicendo quale in una riga, senza chiedere il via.")
MOTIVO_RINVIO = ("Prometti un controllo per più tardi, ma niente richiamerà la sessione: arma ora un richiamo "
                 "(Monitor, CronCreate o un comando con run_in_background) e dillo in una riga, oppure fai il "
                 "controllo adesso, oppure mettilo in un todo con la data e togli la promessa.")
PASSATO = [
    re.compile(r"\b(?:scrivi|lancia|digita|dai|fai)\s+(?:tu\s+)?[`*]*/clear\b", re.I),
    re.compile(r"/clear[`*]*\s+e\s+(?:poi\s+)?[`*]*/inizio\b[^\n]{0,60}\b(?:aprono|apri|lanci|riparte|ripartono)\b", re.I),
    re.compile(r"\bfai\s+tu\s+la\s+rotazione\b", re.I),
    re.compile(r"\b(?:scrivi|manda|inoltra)\s+(?:tu\s+)?(?:all['’]\s*|alla\s+)(?:altra\s+)?sessione\b", re.I),
]
_PAROLA_VIA = r"(?:vai|procedi|ok|parti|correggi|avanti|fallo)"
_FACCIO = (r"(?:parto|procedo|faccio|preparo|applico|scrivo|rivedo|avvio|correggo|sposto|lancio|metto|apro|sistemo"
           r"|chiudo|rifaccio|continuo|riparto)")
VIA = [
    re.compile(r"\b(?:scrivimi|rispondimi|rispondi|dimmi)\s+[*_\"]*" + _PAROLA_VIA + r"\b[^\n]{0,60}?\be\s+(?:poi\s+)?"
               + _FACCIO + r"\b", re.I),
    re.compile(r"\bparto\s+(?:solo\s+)?se\s+mi\s+(?:scrivi|dici|dai)\b", re.I),
]
# Il via per una spesa resta della persona anche senza le parole di FRENO: "parti e avvio la sponsorizzata da 330 euro".
SPESA = re.compile(r"€|\beuro\b|\bsponsorizzat\w*", re.I)
# Un controllo a un'ora, non a un evento: "domattina guardo io", "fra 10 minuti verifico". Un rinvio a un evento
# ("quando finisce", "alla prossima accensione") resta com'è: lì il richiamo è il todo.
RINVIO_ORA = re.compile(r"\b(?:domattina|domani|stasera|stanotte|più\s+tardi|fra\s+poco|tra\s+poco|dopo\s+pranzo"
                        r"|(?:fra|tra)\s+\d+\s*(?:min\w*|or[ae]|h)\b)", re.I)
_CONTROLLO = r"(?:guardo|controllo|verifico|riprovo|rilancio|riguardo|ricontrollo|rileggo|leggo|ti\s+dico|ti\s+scrivo|ti\s+aggiorno)"
RINVIO_MIO = [
    re.compile(RINVIO_ORA.pattern + r"[^\n.]{0,60}?\b" + _CONTROLLO + r"\b", re.I),
    # Il verbo prima dell'ora: "guardo io domattina". Senza "controllo" e "riguardo", che qui sono quasi sempre
    # nomi ("il controllo di domani").
    re.compile(r"\b(?:guardo|verifico|riprovo|rilancio|ricontrollo|rileggo|ti\s+aggiorno)\b(?:\s+io)?[^\n.]{0,40}?"
               + RINVIO_ORA.pattern, re.I),
]
ARMA = {"Monitor", "ScheduleWakeup", "CronCreate", "RemoteTrigger"}


def passo_mio(fine: str) -> bool:
    return any(r.search(fine) for r in PASSO_MIO)


def righe_del_passo(fine: str) -> str:
    """Le righe che dicono il passo mio: il rinvio conta solo lì. Il 24/11 un "quando torna online" di un'altra
    voce, due righe sopra "il prossimo passo è mio", spegneva il caso che ha fatto nascere l'hook."""
    righe = []
    for r in PASSO_MIO:
        for m in r.finditer(fine):
            inizio = fine.rfind("\n", 0, m.start()) + 1
            fine_riga = fine.find("\n", m.end())
            righe.append(fine[inizio:fine_riga if fine_riga >= 0 else len(fine)])
    return "\n".join(righe)


def decidi(testo: str) -> str:
    """'continua' se il passo dopo è di Claude e non tocca niente della persona; altrimenti il motivo del no."""
    fine = str(testo or "")[-FINESTRA:]
    if not passo_mio(fine):
        return "niente"
    if chiede(testo):
        return "domanda"
    if any(r.search(fine) for r in FRENO):
        return "freno"
    if RINVIO.search(righe_del_passo(fine)):
        return "rinvio"
    if RUOTO.search(fine):
        return "rotazione"
    return "continua"


def prompt_vero(d: dict) -> bool:
    """Un messaggio della persona, non il risultato di uno strumento."""
    if d.get("type") != "user" or d.get("isMeta"):
        return False
    c = (d.get("message") or {}).get("content")
    if isinstance(c, str):
        return bool(c.strip())
    return isinstance(c, list) and any(isinstance(b, dict) and b.get("type") == "text" for b in c)


def strumenti_del_turno(trascrizione: str) -> list:
    """Gli strumenti chiamati nel turno in corso (dopo l'ultimo messaggio della persona): coppie (nome, input)."""
    try:
        with open(trascrizione, "rb") as fh:
            fh.seek(0, os.SEEK_END)
            fh.seek(max(0, fh.tell() - CODA))
            righe = fh.read().decode("utf-8", "replace").splitlines()
    except OSError:
        return []
    visti = []
    for r in righe:
        try:
            d = json.loads(r)
        except ValueError:
            continue
        if not isinstance(d, dict) or d.get("isSidechain"):
            continue
        if prompt_vero(d):
            visti = []
        elif d.get("type") == "assistant":
            for b in (d.get("message") or {}).get("content") or []:
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    inp = b.get("input")
                    visti.append((str(b.get("name") or ""), inp if isinstance(inp, dict) else {}))
    return visti


def ruota_nel_turno(strumenti: list) -> bool:
    """Vero se nel turno in corso Claude ha chiamato il tool ruota."""
    return any(TOOL_RUOTA.search(nome) for nome, _ in strumenti)


def armato_nel_turno(strumenti: list) -> bool:
    """Vero se nel turno Claude ha armato qualcosa che lo richiama: Monitor, un cron, un comando in background."""
    return any(nome in ARMA or (nome == "Bash" and inp.get("run_in_background")) for nome, inp in strumenti)


def chiusura(testo: str, strumenti: list) -> str:
    """Il difetto della chiusura del turno (#6403): 'passato', 'via', 'rinvio', oppure 'niente'."""
    fine = str(testo or "")[-FINESTRA:]
    if any(r.search(fine) for r in PASSATO) and not ruota_nel_turno(strumenti):
        return "passato"
    righe_via = "\n".join(m.string[m.string.rfind("\n", 0, m.start()) + 1:] for r in VIA for m in [r.search(fine)] if m)
    if righe_via and not SPESA.search(righe_via) and not any(r.search(fine) for r in FRENO):
        return "via"
    promessa = any(r.search(fine) for r in RINVIO_MIO) or (passo_mio(fine) and RINVIO_ORA.search(righe_del_passo(fine)))
    if promessa and not armato_nel_turno(strumenti):
        return "rinvio"
    return "niente"


def sessione_di(sid) -> str:
    return re.sub(r"[^\w-]", "", str(sid or ""))[:64]


def cartella() -> Path:
    return Path(str(radice_orsa())) / "cache" / "continua"


def azzera(sid) -> None:
    """Un messaggio della persona: il conto delle continuazioni riparte da zero (lo chiama hub.py prompt)."""
    s = sessione_di(sid)
    if not s:
        return
    try:
        (cartella() / s).unlink()
    except OSError:
        pass


def leggi_conto(f: Path) -> int:
    try:
        return max(0, int(f.read_text(encoding="utf-8").strip() or 0))
    except (OSError, ValueError):
        return 0


def registra(esito: str, sessione: str, giro: int, attivo: bool) -> None:
    try:
        f = cartella() / "registro.jsonl"
        f.parent.mkdir(parents=True, exist_ok=True)
        if f.is_file() and f.stat().st_size > REGISTRO_TETTO:
            os.replace(str(f), str(f) + ".1")
        riga = {"quando": time.strftime("%Y-%m-%dT%H:%M:%S"), "esito": esito, "sid": sessione,
                "giro": giro, "stop_hook_active": attivo}
        with f.open("a", encoding="utf-8") as h:
            h.write(json.dumps(riga, ensure_ascii=False) + "\n")
    except OSError:
        pass


def herdr(stato: str) -> None:
    """Lo stato di fine turno verso Herdr, con herdr-stato.sh accanto a questo file. Fuori da Herdr niente."""
    if not os.environ.get("HC_TERMINAL_ID") or os.environ.get("ARTURO_TITOLO_FIGLIO"):
        return
    script = os.path.join(os.path.dirname(os.path.realpath(__file__)), "herdr-stato.sh")
    sh = shutil.which("sh")
    if not sh or not os.path.isfile(script):
        return
    try:
        subprocess.run([sh, script, stato], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=3)
    except (OSError, subprocess.SubprocessError):
        pass


def main() -> bool:
    """Vero se il turno continua (block scritto su stdout)."""
    if os.environ.get("ARTURO_CONTINUA") == "0" or os.environ.get("ARTURO_TITOLO_FIGLIO"):
        return False
    dati = json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}")
    if not isinstance(dati, dict) or str(dati.get("hook_event_name") or "Stop") != "Stop":
        return False
    sessione = sessione_di(dati.get("session_id"))
    if not sessione:
        return False
    testo = testo_del_turno(dati)
    strumenti = strumenti_del_turno(str(dati.get("transcript_path") or ""))
    attivo = bool(dati.get("stop_hook_active"))
    esito, motivo = "block", MOTIVO
    if decidi(testo) != "continua" or ruota_nel_turno(strumenti):
        # La chiusura si controlla una volta sola per turno: col secondo Stop Claude può confermarla.
        difetto = "niente" if attivo else chiusura(testo, strumenti)
        if difetto == "niente":
            return False
        esito, motivo = difetto, {"passato": MOTIVO_PASSATO, "via": MOTIVO_VIA, "rinvio": MOTIVO_RINVIO}[difetto]
    f = cartella() / sessione
    giri = leggi_conto(f)
    if giri >= TETTO:
        registra("tetto", sessione, giri, attivo)
        return False
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(str(giri + 1), encoding="utf-8")
    registra(esito, sessione, giri + 1, attivo)
    sys.stdout.write(json.dumps({"decision": "block", "reason": motivo}, ensure_ascii=False))
    sys.stdout.flush()
    return True


if __name__ == "__main__":
    continua = False
    try:
        continua = main()
    except Exception:  # noqa: BLE001 - un hook di Stop rotto non deve mai fermare né trattenere la sessione
        pass
    herdr("working" if continua else "done")
    sys.exit(0)
