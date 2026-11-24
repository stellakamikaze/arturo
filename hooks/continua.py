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
Senza PASSO_MIO l'hook tace sempre: un hook Stop che blocca ogni turno chiude la sessione in un giro
infinito (errore-comune-impeccable-stop-hook-blocca-turni).

Tetto: al massimo TETTO continuazioni di fila senza un messaggio della persona. Il conto sta in
<CLAUDE_CONFIG_DIR o ~/.claude>/cache/continua/<sessione>, e `hub.py prompt` lo azzera (azzera()). Anche
con stop_hook_active vero (Claude sta già continuando per un hook Stop) il giro conta verso il tetto.
Ogni block e ogni tetto raggiunto lasciano una riga in cache/continua/registro.jsonl, tenuto sotto
REGISTRO_TETTO byte.

Si spegne con ARTURO_CONTINUA=0, e non gira dentro la chiamata al modello di titolo-sessione.py
(ARTURO_TITOLO_FIGLIO). Ogni errore: exit 0 in silenzio. Solo libreria standard, Python 3.8+.
Banco: tests/test_continua.py (CN01-CN07).
"""
from __future__ import annotations

import json
import os
import re
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
RINVIO = re.compile(r"\bquando\b|\bappena\b|\balla\s+prossima\b|\bla\s+prossima\s+volta\b|\bdomani\b|\bstasera\b"
                    r"|\bpiù\s+tardi\b|\b(?:dal|dopo\s+il|entro\s+il)\s+\d", re.I)
# La rotazione ha già il suo giro: una riga "ruoto:", e anche "ruoto adesso", "dopo la rotazione", "riparte
# da sola col contesto pulito". Sui transcript del 17-24/11 sei block su otto cadevano su turni così, e
# continuare lì toglie il /clear che la rotazione ha appena armato.
RUOTO = re.compile(r"^\s*(?:\W\s*)?ruoto:|\bruot(?:o|a|are|iamo)\b|\brotazion[ei]\b|\bripart[eo]\s+da\s+sol[ao]\b"
                   r"|\bcontesto\s+pulito\b", re.I | re.M)
TOOL_RUOTA = re.compile(r"(?:^|__)ruota$")


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


def ruota_nel_turno(trascrizione: str) -> bool:
    """Vero se nel turno in corso (dopo l'ultimo messaggio della persona) Claude ha chiamato il tool ruota."""
    try:
        with open(trascrizione, "rb") as fh:
            fh.seek(0, os.SEEK_END)
            fh.seek(max(0, fh.tell() - CODA))
            righe = fh.read().decode("utf-8", "replace").splitlines()
    except OSError:
        return False
    visto = False
    for r in righe:
        try:
            d = json.loads(r)
        except ValueError:
            continue
        if not isinstance(d, dict) or d.get("isSidechain"):
            continue
        if prompt_vero(d):
            visto = False
        elif d.get("type") == "assistant":
            for b in (d.get("message") or {}).get("content") or []:
                if isinstance(b, dict) and b.get("type") == "tool_use" and TOOL_RUOTA.search(str(b.get("name") or "")):
                    visto = True
    return visto


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


def main() -> int:
    if os.environ.get("ARTURO_CONTINUA") == "0" or os.environ.get("ARTURO_TITOLO_FIGLIO"):
        return 0
    dati = json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}")
    if not isinstance(dati, dict) or str(dati.get("hook_event_name") or "Stop") != "Stop":
        return 0
    sessione = sessione_di(dati.get("session_id"))
    if not sessione:
        return 0
    if decidi(testo_del_turno(dati)) != "continua":
        return 0
    if ruota_nel_turno(str(dati.get("transcript_path") or "")):
        return 0
    attivo = bool(dati.get("stop_hook_active"))
    f = cartella() / sessione
    giri = leggi_conto(f)
    if giri >= TETTO:
        registra("tetto", sessione, giri, attivo)
        return 0
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(str(giri + 1), encoding="utf-8")
    registra("block", sessione, giri + 1, attivo)
    sys.stdout.write(json.dumps({"decision": "block", "reason": MOTIVO}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # noqa: BLE001 - un hook di Stop rotto non deve mai fermare né trattenere la sessione
        sys.exit(0)
