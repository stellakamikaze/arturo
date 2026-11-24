#!/usr/bin/env python3
"""CS01-CS06: la carta di una sessione per la Coda di Volta, in hooks/carta-sessione.py (15/11/2026, in Arturo dal 23/11/2026).

CS01 chiede(): le stesse risposte di chiede() di sessioni.js di Volta su una tabella di testi; con node e
     il clone di Volta (VOLTA_MOD o ~/src/volta-celeste/arturo/mods/arturo) le confronta anche con la
     funzione vera.
CS02 la carta dal testo: esito dalla prima riga, domanda dall'ultima riga con "?", opzioni dal grassetto
     dell'ultima riga, raccomandazione, tipo "invio" da una richiesta di invio, prove solo se il file c'è,
     prove anche dalla cartella cache/carte/prove/<sessione>/, link.
CS03 l'hook intero: Stop con una domanda scrive la carta, Stop senza domanda la toglie, UserPromptSubmit e
     SessionEnd la tolgono, un altro strumento in PreToolUse non la tocca, ARTURO_CARTE=0 spegne.
CS04 la carta del menu: AskUserQuestion dà domande, opzioni, raccomandazione da "(Raccomandato)", menu.
CS05 il tetto: una carta enorme resta sotto TETTO byte e tiene la prima domanda.
CS06 senza Volta (nessuna ~/.config/herdr-app) e senza ARTURO_CARTE=1 l'hook non scrive niente; con la cartella
     di Volta scrive.

--avvelena rompe ogni regola su una copia dell'hook (carta-sessione.py o fine_turno.py, il modulo comune con
continua.py) ed esce 0 solo se ogni rottura fa rosso il suo caso.
Solo libreria standard. Nessun modello.
"""
from __future__ import annotations

import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "hooks" / "carta-sessione.py"  # --repo lo cambia

# testo, atteso: le risposte di chiede() di sessioni.js (lette dalla regola il 15/11/2026)
TABELLA = [
    ("Fatto: il banco è verde.\nNiente da fare per te", False),
    ("Vuoi che proceda?", True),
    ("Parto adesso.\nScrivimi **fatto** quando hai finito", True),
    ("Prossimo passo: tu apri la pagina e guardi lo scatto", True),
    ("Prossimo passo: rilancio io il banco domani", False),
    ("Comandi:\n! bw unlock", True),
    ("Rispondi con i numeri (**1 tutte, 2 orario**)", True),
    ("Ho chiuso il lavoro, il commit è su origin.", False),
]


def carica(percorso: Path, casa: Path):
    # fine_turno.py (il testo di fine turno e chiede(), comune con continua.py) si importa dalla cartella
    # dell'hook: una copia avvelenata deve portare il suo, non quello già in memoria.
    sys.modules.pop("fine_turno", None)
    spec = importlib.util.spec_from_file_location(f"carta_{abs(hash(str(percorso)))}", percorso)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.cartella = lambda: casa / "cache" / "carte"
    return m


def riga(tipo: str, testo: str) -> str:
    if tipo == "user":
        return json.dumps({"type": "user", "message": {"role": "user", "content": testo}})
    return json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": testo}]}})


def lancia(m, evento: dict) -> None:
    vecchio = sys.stdin
    sys.stdin = io.TextIOWrapper(io.BytesIO(json.dumps(evento).encode("utf-8")))
    try:
        m.main()
    finally:
        sys.stdin = vecchio


def cs01(m) -> str | None:
    for testo, atteso in TABELLA:
        if m.chiede(testo) != atteso:
            return f"CS01 ROSSO: chiede({testo[:40]!r}) dà {not atteso}, sessioni.js dà {atteso}"
    node = shutil.which("node")
    mod = Path(os.environ.get("VOLTA_MOD") or Path.home() / "src/volta-celeste/arturo/mods/arturo")
    if node and (mod / "sessioni.js").exists():
        with tempfile.TemporaryDirectory(prefix="cs01-") as d:
            shutil.copy(mod / "sessioni.js", Path(d) / "sessioni.mjs")
            prova = Path(d) / "prova.mjs"
            prova.write_text(
                "import { chiede } from './sessioni.mjs';\n"
                f"const t = {json.dumps([t for t, _ in TABELLA])};\n"
                "console.log(JSON.stringify(t.map(chiede)));\n", encoding="utf-8")
            r = subprocess.run([node, str(prova)], capture_output=True, text=True, timeout=30)
            if r.returncode == 0:
                veri = json.loads(r.stdout.strip().splitlines()[-1])
                if veri != [a for _, a in TABELLA]:
                    return f"CS01 ROSSO: la tabella non segue più chiede() di sessioni.js: {veri}"
    return None


def cs02(m, casa: Path) -> str | None:
    img = casa / "scatto.png"
    img.write_bytes(b"\x89PNG")
    testo = (
        "**Fatto: la pagina è pronta.**\n"
        f"Scatto in {img} e anteprima su https://esempio.test/pagina.\n"
        "Manca /non/esiste/foto.png.\n"
        "RACCOMANDAZIONE: invia oggi, perché il cliente aspetta\n"
        "Invio la bozza al cliente?\n"
        "Scrivimi **invia** oppure **aspetta**"
    )
    c = m.carta_testo(testo, "s1", 1.0)
    if c["esito"] != "Fatto: la pagina è pronta.":
        return f"CS02 ROSSO: esito {c['esito']!r}"
    if c["domanda"] != "Invio la bozza al cliente?":
        return f"CS02 ROSSO: domanda {c['domanda']!r}"
    if c["opzioni"] != ["invia", "aspetta"]:
        return f"CS02 ROSSO: opzioni {c['opzioni']!r}"
    if not c["raccomandazione"].startswith("invia oggi"):
        return f"CS02 ROSSO: raccomandazione {c['raccomandazione']!r}"
    if c["tipo"] != "invio":
        return f"CS02 ROSSO: tipo {c['tipo']!r}, atteso invio"
    if c["prove"] != [str(img)]:
        return f"CS02 ROSSO: prove {c['prove']!r} (il file che non c'è non entra)"
    if c["link"] != ["https://esempio.test/pagina"]:
        return f"CS02 ROSSO: link {c['link']!r}"
    cart = casa / "cache" / "carte" / "prove" / "s2"
    cart.mkdir(parents=True)
    (cart / "demo.mp4").write_bytes(b"0")
    c2 = m.carta_testo("Guarda la demo?\nScrivimi **ok**", "s2", 1.0)
    if c2["prove"] != [str(cart / "demo.mp4")]:
        return f"CS02 ROSSO: la cartella delle prove non entra: {c2['prove']!r}"
    if c2["tipo"] != "scelta":
        return f"CS02 ROSSO: tipo {c2['tipo']!r}, atteso scelta"
    c3 = m.carta_testo("Serve un account Apple a pagamento e un token nuovo.\nTi consiglio la 1.\n"
                       "Scrivimi **tema** oppure **lascia così**", "s3", 1.0)
    if c3["tipo"] != "scelta":
        return f"CS02 ROSSO: tipo {c3['tipo']!r} da una parola del corpo, non della richiesta"
    c4 = m.carta_testo("Il token è scaduto.\nLancia `! gh auth login -h github.com --web`, poi scrivimi **fatto**.", "s4", 1.0)
    if c4["tipo"] != "oauth":
        return f"CS02 ROSSO: tipo {c4['tipo']!r}, atteso oauth per un login"
    return None


def cs03(m, casa: Path) -> str | None:
    tr = casa / "t.jsonl"
    f = casa / "cache" / "carte" / "s3.json"
    tr.write_text(riga("user", "fai il lavoro") + "\n" + riga("assistant", "Ho finito il primo pezzo.\nProcedo col secondo?") + "\n", encoding="utf-8")
    lancia(m, {"hook_event_name": "Stop", "session_id": "s3", "transcript_path": str(tr)})
    if not f.exists():
        return "CS03 ROSSO: Stop con una domanda non scrive la carta"
    if json.loads(f.read_text(encoding="utf-8")).get("domanda") != "Procedo col secondo?":
        return "CS03 ROSSO: la carta di Stop non porta la domanda"
    lancia(m, {"hook_event_name": "PreToolUse", "session_id": "s3", "tool_name": "Bash", "tool_input": MENU})
    if not f.exists() or json.loads(f.read_text(encoding="utf-8")).get("domanda") != "Procedo col secondo?":
        return "CS03 ROSSO: un altro strumento in PreToolUse tocca la carta"
    lancia(m, {"hook_event_name": "UserPromptSubmit", "session_id": "s3", "prompt": "sì"})
    if f.exists():
        return "CS03 ROSSO: UserPromptSubmit non toglie la carta"
    lancia(m, {"hook_event_name": "Stop", "session_id": "s3", "last_assistant_message": "Serve il tuo sì: confermi?"})
    if not f.exists():
        return "CS03 ROSSO: Stop non legge last_assistant_message"
    tr.write_text(riga("assistant", "Fatto, il commit è su origin.") + "\n", encoding="utf-8")
    lancia(m, {"hook_event_name": "Stop", "session_id": "s3", "transcript_path": str(tr)})
    if f.exists():
        return "CS03 ROSSO: Stop senza domanda lascia la carta di prima"
    lancia(m, {"hook_event_name": "Stop", "session_id": "s3", "last_assistant_message": "Vado?"})
    lancia(m, {"hook_event_name": "SessionEnd", "session_id": "s3"})
    if f.exists():
        return "CS03 ROSSO: SessionEnd non toglie la carta"
    os.environ["ARTURO_CARTE"] = "0"
    try:
        lancia(m, {"hook_event_name": "Stop", "session_id": "s3", "last_assistant_message": "Vado?"})
    finally:
        os.environ["ARTURO_CARTE"] = "1"
    if f.exists():
        return "CS03 ROSSO: ARTURO_CARTE=0 non spegne l'hook"
    return None


MENU = {"questions": [
    {"question": "Quale vista apro per prima?", "header": "Vista", "multiSelect": False, "options": [
        {"label": "Coda (Raccomandato)", "description": "toglie il passaggio fra le chat"},
        {"label": "Tessere", "description": "i progetti in griglia"}]},
    {"question": "Lead a orario?", "header": "Lead", "multiSelect": False, "options": [
        {"label": "Sì", "description": ""}, {"label": "No", "description": ""}]},
]}


def cs04(m, casa: Path) -> str | None:
    lancia(m, {"hook_event_name": "PreToolUse", "session_id": "s4", "tool_name": "AskUserQuestion", "tool_input": MENU})
    f = casa / "cache" / "carte" / "s4.json"
    if not f.exists():
        return "CS04 ROSSO: AskUserQuestion non scrive la carta"
    c = json.loads(f.read_text(encoding="utf-8"))
    if not c.get("menu") or c.get("fonte") != "menu":
        return "CS04 ROSSO: la carta del menu non dice menu"
    if c.get("domanda") != "Quale vista apro per prima?" or c.get("opzioni") != ["Coda (Raccomandato)", "Tessere"]:
        return f"CS04 ROSSO: domanda o opzioni sbagliate: {c.get('domanda')!r} {c.get('opzioni')!r}"
    if c.get("raccomandazione") != "Coda (Raccomandato)":
        return f"CS04 ROSSO: raccomandazione {c.get('raccomandazione')!r}"
    if len(c.get("domande", [])) != 2 or c["domande"][1]["domanda"] != "Lead a orario?":
        return "CS04 ROSSO: le domande dopo la prima si perdono"
    return None


def cs05(m, casa: Path) -> str | None:
    grande = {"questions": [{"question": "D" * 900, "header": "H", "options": [
        {"label": f"op{i}", "description": "x" * 500} for i in range(6)]} for _ in range(4)]}
    c = m.nel_tetto(m.carta_menu(grande, "s5", 1.0))
    peso = len(json.dumps(c, ensure_ascii=False).encode("utf-8"))
    if peso > m.TETTO:
        return f"CS05 ROSSO: la carta pesa {peso} byte, oltre {m.TETTO}"
    if not c.get("domande") or not c.get("opzioni"):
        return "CS05 ROSSO: il tetto toglie anche la prima domanda"
    return None


def cs06(m, casa: Path) -> str | None:
    """Senza Volta l'hook tace; con la cartella di Volta scrive; ARTURO_CARTE=1 lo accende lo stesso."""
    f = casa / "cache" / "carte" / "s6.json"
    evento = {"hook_event_name": "Stop", "session_id": "s6", "last_assistant_message": "Procedo?"}
    vecchio = dict(os.environ)
    try:
        os.environ.pop("ARTURO_CARTE", None)
        os.environ["HOME"] = os.environ["USERPROFILE"] = str(casa / "senza-volta")
        (casa / "senza-volta").mkdir()
        lancia(m, evento)
        if f.exists():
            return "CS06 ROSSO: senza Volta e senza ARTURO_CARTE=1 l'hook scrive la carta"
        (casa / "senza-volta" / ".config" / "herdr-app").mkdir(parents=True)
        lancia(m, evento)
        if not f.exists():
            return "CS06 ROSSO: con la cartella di Volta l'hook non scrive la carta"
        f.unlink()
        os.environ["HOME"] = os.environ["USERPROFILE"] = str(casa / "altra-casa")
        (casa / "altra-casa").mkdir()
        os.environ["ARTURO_CARTE"] = "1"
        lancia(m, evento)
        if not f.exists():
            return "CS06 ROSSO: ARTURO_CARTE=1 non accende l'hook senza Volta"
    finally:
        os.environ.clear()
        os.environ.update(vecchio)
    return None


def prova(percorso: Path) -> list:
    rossi = []
    with tempfile.TemporaryDirectory(prefix="cs-") as d:
        casa = Path(d)
        vecchio = dict(os.environ)
        os.environ["ARTURO_CARTE"] = "1"  # la guardia "Volta presente" la prova solo CS06
        os.environ.pop("ARTURO_TITOLO_FIGLIO", None)
        try:
            m = carica(percorso, casa)
            for caso in (lambda: cs01(m), lambda: cs02(m, casa), lambda: cs03(m, casa),
                         lambda: cs04(m, casa), lambda: cs05(m, casa), lambda: cs06(m, casa)):
                try:
                    r = caso()
                except Exception as e:  # noqa: BLE001 - un caso che getta è rosso, col suo motivo
                    r = f"ROSSO per eccezione: {type(e).__name__}: {e}"
                if r:
                    rossi.append(r)
        finally:
            os.environ.clear()
            os.environ.update(vecchio)
    return rossi


VELENI = [
    ("CS01", '    re.compile(r"\\?[\\s*_`)]*$"),\n', ''),
    ("CS02", '    for r in reversed(rr[-8:]):\n        if "?" in r:', '    for r in rr[:1]:\n        if "?" in r:'),
    ("CS02", '    ultima = rr[-1]\n', '    ultima = rr[0]\n'),
    ("CS02", '        if os.path.isfile(vero) and vero not in trovate:', '        if vero not in trovate:'),
    ("CS02", '    fine = domanda_di(testo) + "\\n" + (rr[-1] if rr else "")\n', '    fine = testo\n'),
    ("CS02", '|\\blogin\\b|\\baccedi\\b', ''),
    ("CS03", '    if evento in ("UserPromptSubmit", "SessionEnd"):\n        togli(f)\n        return 0\n', ''),
    ("CS03", '        else:\n            togli(f)\n        spazza(adesso)', '        spazza(adesso)'),
    ("CS03", '        if dati.get("tool_name") != "AskUserQuestion":\n            return 0\n', ''),
    ("CS04", '    for q in (entrata.get("questions") or [])[:4]:', '    for q in (entrata.get("questions") or [])[:1]:'),
    ("CS04", '                 if re.search(r"\\((Raccomandato|Recommended)\\)", o["etichetta"])), "")', '                 if False), "")'),
    ("CS05", '    if peso(carta) <= TETTO:\n        return carta\n', '    return carta\n'),
    ("CS06", '    if os.environ.get("ARTURO_CARTE") != "1" and not volta_presente():\n        return 0\n', ''),
    ("CS06", 'return (Path.home() / ".config" / "herdr-app").is_dir()', 'return False'),
]


def avvelena() -> int:
    nomi = ("carta-sessione.py", "fine_turno.py")
    testi = {n: (HOOK.parent / n).read_text(encoding="utf-8") for n in nomi}
    morsi = 0
    for codice, vecchio, nuovo in VELENI:
        dove = [n for n in nomi if testi[n].count(vecchio) == 1]
        if len(dove) != 1 or sum(testi[n].count(vecchio) for n in nomi) != 1:
            print(f"VELENO {codice} NON SI APPLICA: {vecchio[:60]!r}")
            continue
        with tempfile.TemporaryDirectory(prefix="cs-veleno-") as d:
            copia = Path(d) / "hooks" / "carta-sessione.py"
            copia.parent.mkdir()
            for n in nomi:
                (copia.parent / n).write_text(testi[n].replace(vecchio, nuovo) if n == dove[0] else testi[n],
                                              encoding="utf-8")
            shutil.copy(HOOK.parent / "radici.py", copia.parent / "radici.py")
            rossi = [r for r in prova(copia) if r.startswith(f"{codice} ROSSO")]
        print(f"VELENO {codice} " + (f"ROSSO: {rossi[0][:120]}" if rossi else "NON ATTACCA"))
        morsi += bool(rossi)
    print(f"veleni rossi {morsi}/{len(VELENI)}")
    if morsi != len(VELENI):
        return 1
    print(f"VELENI_ROSSI={','.join(sorted({c for c, _, _ in VELENI}))} veleni={len(VELENI)}")
    return 0


def main() -> int:
    global HOOK
    if "--repo" in sys.argv:
        HOOK = Path(sys.argv[sys.argv.index("--repo") + 1]) / "hooks" / "carta-sessione.py"
    if "--avvelena" in sys.argv:
        return avvelena()
    rossi = prova(HOOK)
    for r in rossi:
        print(r)
    print(f"carta-sessione: {6 - len(rossi)}/6 casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    raise SystemExit(main())
