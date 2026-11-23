#!/usr/bin/env python3
"""La carta di una sessione: cosa chiede alla persona, per la Coda di Volta (15/11/2026).

Una sola coda di decisioni invece di decine di chat. Quando una sessione ha bisogno della persona, questo
hook scrive ~/.claude/cache/carte/<sessione>.json; la sonda di Volta (volta_sonda.py) la legge e la vista
Coda la mostra, una carta per volta. Dal 23/11/2026 (revisione, passo 9, #6422) l'hook vive in Arturo e gira
solo dove c'è Volta (~/.config/herdr-app) o con ARTURO_CARTE=1: chi non usa Volta non scrive niente.

  PreToolUse di AskUserQuestion  carta col menu: domande e opzioni come le ha scritte Claude (menu: true).
  Stop                           se l'ultimo testo di Claude chiede qualcosa (stessa regola di chiede() in
                                 sessioni.js di Volta), carta dal testo: esito (prima riga), domanda,
                                 opzioni (il grassetto dell'ultima riga), raccomandazione, tipo (le
                                 categorie umane di A20), prove (immagini e video esistenti nominati nel
                                 testo, più i file di cache/carte/prove/<sessione>/) e link. Se non chiede
                                 niente, la carta di prima si toglie.
  UserPromptSubmit e SessionEnd  la carta si toglie: la persona ha risposto, o la sessione è finita.

Campi: versione, sid, quando, fonte (menu|testo), tipo, esito, domanda, opzioni, raccomandazione,
domande (solo menu), prove, link, menu. Il file resta sotto TETTO byte. Si spegne con ARTURO_CARTE=0, e
non gira dentro la chiamata al modello di titolo-sessione.py (ARTURO_TITOLO_FIGLIO). Ogni errore: exit 0.
Solo libreria standard, Python 3.8+. Banco: tests/test_carta_sessione.py (CS01-CS06).
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from radici import radice_orsa  # noqa: E402

VERSIONE = 1
TETTO = 4096         # byte del file della carta
CODA = 3000000       # byte della trascrizione letti dal fondo, come la sonda di Volta
VECCHIA = 7 * 24 * 3600
PROVE = 4
OPZIONI = 6
ESTENSIONI = ("png", "jpg", "jpeg", "gif", "webp", "mp4", "mov")

# Le stesse regole di chiede() in arturo/mods/arturo/sessioni.js di Volta: se cambiano là, cambiano qui
# (CS01 le confronta con node quando c'è).
CHIEDE = [
    re.compile(r"\?[\s*_`)]*$"),
    re.compile(r"\?\s*\n"),
    re.compile(r"^\s*!\s*\S", re.M),
    re.compile(r"\b(scrivimi|scrivi|dimmi|dimmelo|rispondi|rispondimi|fammi sapere|conferma|confermi|scegli|decidi|lancia|tocca a te|serve il tuo|il tuo s[iì]|aspetto la tua|attendo la tua)\b", re.I),
    re.compile(r"prossimo passo:[^\n]*(\btu\b|\btuo\b|\btua\b|\(tu\))", re.I),
]

# Le categorie umane di A20 (CHI_TU di pm/progetti/indice.py), cercate nella fine del testo.
TIPI = [
    ("invio", re.compile(r"\binvi(o|are|i|a|alo|ala|amo)\b|\bmanda(re|la|lo)?\b|\bpubblica(re)?\b", re.I)),
    ("pagamento", re.compile(r"\bpaga(mento|re|menti)\b", re.I)),
    ("segreto", re.compile(r"\bpassword\b|\bsegreto\b|\btoken\b", re.I)),
    ("otp", re.compile(r"\bOTP\b|\b2FA\b", re.I)),
    ("oauth", re.compile(r"\bOAuth\b|\bconsenso\b|\blogin\b|\baccedi\b", re.I)),
    ("gesto", re.compile(r"\bgesto fisico\b|\bcollega(re)? il cavo\b", re.I)),
]
GRASSETTO = re.compile(r"\*\*(.+?)\*\*")
RACCOMANDA = re.compile(r"^\s*(?:\*\*)?(?:RACCOMANDAZIONE|Raccomandazione|Da dove partirei|Raccomando)(?:\*\*)?\s*[:.]?\s*(?:\*\*)?\s*(.+)$", re.M)
# Anche C:\... e C:/...: su Windows Claude scrive i percorsi con la lettera dell'unità (#6455, CS02).
PERCORSO = re.compile(r"(?<![\w/.~-])((?:~|/|[A-Za-z]:[\\/])[^\s`'\"()<>\[\]]+\.(?:%s))\b" % "|".join(ESTENSIONI),
                      re.I)
LINK = re.compile(r"https?://[^\s`'\"()<>\[\]]+")


def volta_presente() -> bool:
    """Volta tiene la sua config in ~/.config/herdr-app, sul Mac e su Windows: senza, nessuno legge le carte."""
    return (Path.home() / ".config" / "herdr-app").is_dir()


def cartella() -> Path:
    return Path(str(radice_orsa())) / "cache" / "carte"


def scrivi(f: Path, dati: dict) -> None:
    f.parent.mkdir(parents=True, exist_ok=True)
    provvisorio = f.with_name(f"{f.stem}.{os.getpid()}.tmp")
    provvisorio.write_text(json.dumps(dati, ensure_ascii=False), encoding="utf-8")
    os.replace(str(provvisorio), str(f))


def togli(f: Path) -> None:
    try:
        f.unlink()
    except OSError:
        pass


def chiede(testo: str) -> bool:
    c = str(testo or "")[-220:]
    return any(r.search(c) for r in CHIEDE)


def pulisci(riga: str, lungo: int) -> str:
    t = re.sub(r"[*_`#>]+", "", riga or "")
    t = re.sub(r"\s+", " ", t).strip(" -·:")
    return t if len(t) <= lungo else t[: lungo - 1].rstrip() + "…"


def righe(testo: str) -> list:
    return [r for r in (testo or "").splitlines() if r.strip()]


def tipo_di(testo: str) -> str:
    """Il tipo dalla richiesta sola (domanda e ultima riga): nel resto del testo "a pagamento" o "token"
    descrivono, non chiedono (prova dal vivo del 15/11/2026, due carte su quattro col tipo sbagliato)."""
    rr = righe(testo)
    fine = domanda_di(testo) + "\n" + (rr[-1] if rr else "")
    for nome, regola in TIPI:
        if regola.search(fine):
            return nome
    return "scelta"


def domanda_di(testo: str) -> str:
    rr = righe(testo)
    for r in reversed(rr[-8:]):
        if "?" in r:
            return pulisci(r, 600)
    return pulisci(rr[-1], 600) if rr else ""


def opzioni_di(testo: str) -> list:
    rr = righe(testo)
    if not rr:
        return []
    ultima = rr[-1]
    viste = []
    for g in GRASSETTO.findall(ultima):
        o = pulisci(g, 80)
        if o and o not in viste:
            viste.append(o)
    return viste[:OPZIONI]


def raccomandazione_di(testo: str) -> str:
    m = RACCOMANDA.findall(testo or "")
    if m:
        return pulisci(m[-1], 300)
    for r in righe(testo):
        if "(Raccomandato)" in r:
            return pulisci(r.replace("(Raccomandato)", ""), 300)
    return ""


def prove_di(testo: str, sessione: str) -> list:
    trovate = []
    for p in PERCORSO.findall(testo or ""):
        vero = os.path.expanduser(p.rstrip(".,;:"))
        if os.path.isfile(vero) and vero not in trovate:
            trovate.append(vero)
    cartella_prove = cartella() / "prove" / sessione
    try:
        extra = sorted((f for f in cartella_prove.iterdir()
                        if f.is_file() and f.suffix.lower().lstrip(".") in ESTENSIONI),
                       key=lambda f: f.stat().st_mtime, reverse=True)
        for f in extra:
            if str(f) not in trovate:
                trovate.append(str(f))
    except OSError:
        pass
    return trovate[:PROVE]


def link_di(testo: str) -> list:
    viste = []
    for u in LINK.findall(testo or ""):
        u = u.rstrip(".,;:")
        if u not in viste:
            viste.append(u)
    return viste[:3]


def testo_di(contenuto) -> str:
    if isinstance(contenuto, str):
        return contenuto
    if isinstance(contenuto, list):
        return "\n".join(b.get("text", "") for b in contenuto if isinstance(b, dict) and b.get("type") == "text")
    return ""


def ultimo_testo(trascrizione: str) -> str:
    """L'ultimo testo di Claude nella trascrizione (solo i blocchi di testo, non gli strumenti)."""
    try:
        with open(trascrizione, "rb") as fh:
            fh.seek(0, os.SEEK_END)
            lungo = fh.tell()
            fh.seek(max(0, lungo - CODA))
            dati = fh.read().decode("utf-8", "replace")
    except OSError:
        return ""
    ultimo = ""
    for r in dati.splitlines():
        try:
            d = json.loads(r)
        except ValueError:
            continue
        if not isinstance(d, dict) or d.get("type") != "assistant":
            continue
        t = testo_di((d.get("message") or {}).get("content"))
        if t.strip():
            ultimo = t
    return ultimo


def carta_testo(testo: str, sessione: str, adesso: float) -> dict:
    rr = righe(testo)
    return {
        "versione": VERSIONE, "sid": sessione, "quando": adesso, "fonte": "testo",
        "tipo": tipo_di(testo), "esito": pulisci(rr[0], 200) if rr else "",
        "domanda": domanda_di(testo), "opzioni": opzioni_di(testo),
        "raccomandazione": raccomandazione_di(testo),
        "prove": prove_di(testo, sessione), "link": link_di(testo), "menu": False,
    }


def carta_menu(entrata: dict, sessione: str, adesso: float) -> dict:
    domande = []
    for q in (entrata.get("questions") or [])[:4]:
        if not isinstance(q, dict):
            continue
        opz = []
        for o in (q.get("options") or [])[:OPZIONI]:
            if isinstance(o, dict) and o.get("label"):
                opz.append({"etichetta": pulisci(str(o["label"]), 80),
                            "spiega": pulisci(str(o.get("description") or ""), 160)})
        domande.append({"domanda": pulisci(str(q.get("question") or ""), 600),
                        "titolo": pulisci(str(q.get("header") or ""), 40),
                        "multipla": bool(q.get("multiSelect")), "opzioni": opz})
    if not domande:
        return {}
    prima = domande[0]
    racc = next((o["etichetta"] for o in prima["opzioni"]
                 if re.search(r"\((Raccomandato|Recommended)\)", o["etichetta"])), "")
    tutto = " ".join(d["domanda"] for d in domande)
    return {
        "versione": VERSIONE, "sid": sessione, "quando": adesso, "fonte": "menu",
        "tipo": tipo_di(tutto), "esito": prima["titolo"], "domanda": prima["domanda"],
        "opzioni": [o["etichetta"] for o in prima["opzioni"]], "raccomandazione": racc,
        "domande": domande, "prove": [], "link": [], "menu": True,
    }


def nel_tetto(carta: dict) -> dict:
    """La carta sotto TETTO byte: accorcia prima le domande del menu, poi la domanda, poi le spiegazioni."""
    def peso(c):
        return len(json.dumps(c, ensure_ascii=False).encode("utf-8"))
    if peso(carta) <= TETTO:
        return carta
    for d in carta.get("domande", []):
        for o in d.get("opzioni", []):
            o["spiega"] = ""
    while peso(carta) > TETTO and len(carta.get("domande", [])) > 1:
        carta["domande"].pop()
    if peso(carta) > TETTO:
        carta["domanda"] = pulisci(carta["domanda"], 200)
    return carta


def spazza(adesso: float) -> None:
    try:
        for f in cartella().glob("*.json"):
            if adesso - f.stat().st_mtime > VECCHIA:
                f.unlink()
    except OSError:
        pass


def main() -> int:
    if os.environ.get("ARTURO_CARTE") == "0" or os.environ.get("ARTURO_TITOLO_FIGLIO"):
        return 0
    if os.environ.get("ARTURO_CARTE") != "1" and not volta_presente():
        return 0
    adesso = time.time()
    dati = json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}")
    evento = str(dati.get("hook_event_name") or "")
    sessione = re.sub(r"[^\w-]", "", str(dati.get("session_id") or ""))[:64]
    if not sessione:
        return 0
    f = cartella() / f"{sessione}.json"
    if evento in ("UserPromptSubmit", "SessionEnd"):
        togli(f)
        return 0
    if evento == "PreToolUse":
        if dati.get("tool_name") != "AskUserQuestion":
            return 0
        carta = carta_menu(dati.get("tool_input") or {}, sessione, adesso)
        if carta:
            scrivi(f, nel_tetto(carta))
        return 0
    if evento == "Stop":
        testo = str(dati.get("last_assistant_message") or "") or ultimo_testo(str(dati.get("transcript_path") or ""))
        if testo and chiede(testo):
            scrivi(f, nel_tetto(carta_testo(testo, sessione, adesso)))
        else:
            togli(f)
        spazza(adesso)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # noqa: BLE001 - una carta mancata non deve mai rompere la sessione
        sys.exit(0)
