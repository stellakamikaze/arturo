#!/usr/bin/env python3
"""memory-firma.py — PostToolUseFailure: la nota giusta quando un comando fallisce (v3-5).
L'audit del 24/10/2026 ha misurato che la lezione arriva sul prompt e non sul
comando: con la nota nel contesto un errore di timeout si ripeteva 0 volte su 5,
senza 63 su 79. memory-retrieve guarda il messaggio della persona, nessun hook
guardava il testo dell'errore. Questo sì.
Una nota della memoria porta nel frontmatter il campo `firma:`, una lista di
sottostringhe esatte del messaggio d'errore (confronto in minuscolo, almeno 8
caratteri). Quando un tool fallisce e il testo contiene una firma, l'hook inietta
il pointer della nota (nome e description, i primi 220 caratteri come
memory-retrieve), una volta sola per nota e per sessione, al massimo due per errore.
Legge tutta data/memory, compreso _archive: una nota archiviata che torna utile
si dichiara, invece di ri-derivare la lezione.
Il pointer arriva dopo il primo errore: serve contro la ripetizione nella stessa
sessione. Prevenire il primo errore resta compito delle guardie PreToolUse.
Dal 18/11/2026 è in Arturo per tutti (prima viveva solo nella config di chi lo mantiene).
Mai un blocco: qualunque guasto esce 0 in silenzio.
"""
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import melchior_match as mm  # noqa: E402

MEMORY = mm.MEMORY_DIR
CACHE = mm.CLAUDE_DIR / "cache" / "melchior-firme.json"
STATE_DIR = mm.CLAUDE_DIR / "session-env"
DESC_LEN = 220
MAX_NOTE = 2  # al massimo due pointer per errore


def _stato_dirs():
    files = sorted(p for p in MEMORY.rglob("*.md") if "_reports" not in p.parts) if MEMORY.is_dir() else []
    return files, [[str(p), p.stat().st_mtime] for p in files]


def firme():
    """Lista di (firma minuscola, nome, description, archiviata, percorso), con cache per mtime."""
    files, stato = _stato_dirs()
    try:
        c = json.loads(CACHE.read_text(encoding="utf-8"))
        if c.get("stato") == stato and c.get("forma") == 2:
            return [tuple(x) for x in c["firme"]]
    except Exception:
        pass
    out = []
    for p in files:
        try:
            testo = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "firma" not in testo:
            continue
        fm = mm.parse_frontmatter_simple(testo)
        for f in mm._lista(mm.campo(fm, "firma")):
            f = str(f).strip().lower()
            if len(f) >= 8:  # una firma corta matcherebbe errori qualunque
                out.append((f, p.stem, str(mm.campo(fm, "description") or "")[:DESC_LEN],
                            "_archive" in p.parts, mm.breve(p)))
    try:
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps({"stato": stato, "forma": 2, "firme": out}, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass
    return out


def pulisci_seen(giorni=7):
    """Toglie i firma-*.seen più vecchi di 7 giorni: session-end conosce solo i retrieve-*.seen."""
    limite = time.time() - giorni * 86400
    for f in STATE_DIR.glob("firma-*.seen"):
        try:
            if f.stat().st_mtime < limite:
                f.unlink()
        except OSError:
            pass


def testo_errore(payload):
    e = payload.get("error")
    if isinstance(e, str):
        return e
    r = payload.get("tool_response")
    return json.dumps(r, ensure_ascii=False) if r is not None else ""


def main():
    try:
        payload = json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}")
    except Exception:
        return 0
    if not mm.memoria_accesa():
        return 0
    errore = testo_errore(payload).lower()
    if not errore.strip():
        return 0
    sid = re.sub(r"[^A-Za-z0-9_-]", "", str(payload.get("session_id") or ""))[:64]
    seen_file = STATE_DIR / f"firma-{sid}.seen" if sid else None
    seen = set()
    if seen_file and seen_file.is_file():
        seen = set(seen_file.read_text(encoding="utf-8").split())
    trovate = []
    for f, nome, desc, archiviata, dove in firme():
        if f in errore and nome not in seen and nome not in {t[0] for t in trovate}:
            trovate.append((nome, desc, archiviata, dove))
        if len(trovate) >= MAX_NOTE:
            break
    if not trovate:
        return 0
    righe = ["MEMORIA (firma d'errore): questo errore ha già una lezione scritta. Leggila prima di riprovare."]
    for nome, desc, archiviata, dove in trovate:
        extra = " (nota ARCHIVIATA: se vale ancora, spostala fuori da _archive)" if archiviata else ""
        righe.append(f"- {nome}: {desc}{extra} → {dove}")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUseFailure",
                                             "additionalContext": "\n".join(righe)}}, ensure_ascii=False))
    if seen_file:
        try:
            STATE_DIR.mkdir(parents=True, exist_ok=True)
            with seen_file.open("a", encoding="utf-8") as fh:
                fh.write("".join(f"{t[0]}\n" for t in trovate))
        except OSError:
            pass
        pulisci_seen()
    origine = "sub" if payload.get("agent_id") else "main"
    mm.append_access([f"{t[0]}.md" for t in trovate], "firma", extra=(sid[:8], origine))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
