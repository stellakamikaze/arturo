"""arturo note: il lato di Claude delle note sulla finestra di Volta Celeste (⌘⇧N).

Federico lascia una nota su un punto della finestra: il mod scrive una cartella per nota in
~/.claude/data/note-finestra/<data-ora>/ con nota.json (versione 2) e finestra.png, e un todo di Claude.
Da qui Claude legge le note, guarda il ritaglio dello scatto attorno al punto, le prende, risponde e le
chiude. È il server MCP di Agentation (get_pending, acknowledge, reply, resolve, dismiss) fatto CLI: niente
porte aperte, e la finestra se ne accorge da sola perché guarda la cartella (watchFolder).

  elenco    le note aperte (aperte e prese), con --tutte anche le chiuse; --md come brief per Claude
  mostra    la nota intera e ritaglio.png attorno al punto, col percorso stampato
  prendi    Claude ci lavora: la finestra mostra il segno grigio e il todo passa in corso
  rispondi  una voce nel filo: la finestra avvisa "Claude ha risposto alla nota N"
  risolvi   chiude la nota col riassunto e chiude il todo collegato
  scarta    chiude la nota col motivo e scarta il todo collegato

Il formato di nota.json lo leggono anche nota.js (leggiNota, noteAperte) e il velo: numeri, stati e
lettura di una nota versione 1 qui fanno le stesse cose. Mod e CLI scrivono lo stesso file: il mod
scrive solo se il file è ancora quello letto (writeTextFile con l'atteso), la CLI rilegge e rifà la
modifica se il file è cambiato fra lettura e scrittura, così nessuna delle due perde il filo dell'altra.
Il todo si chiude con "arturo todo", che passa dalla fonte dei task della persona se c'è. Solo libreria
standard, Python 3.8 o successivo.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path
sys.path.append(str(Path(os.path.realpath(__file__)).parent.parent / "hooks"))
from radici import radice_orsa  # noqa: E402

# Il formato di nota.json vive anche in nota.js del mod (TIPI, STATI, APERTE, VUOTO): HZ32 confronta le due copie.
TIPI = {"correggere": "Correggere", "cambiare": "Cambiare", "domanda": "Domanda", "va-bene": "Va bene così"}
TIPO_PREDEFINITO = "correggere"
STATI = {"aperta": "Aperta", "presa": "Claude ci lavora", "risolta": "Risolta", "scartata": "Scartata"}
APERTE = ("aperta", "presa")
VUOTO = {"blocco": None, "parte": None, "elemento": None, "terminale": None, "titolo": None, "cwd": None, "testo_terminale": None}
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
RITAGLIO = (640, 400)   # il ritaglio attorno al punto, in punti della finestra (lo scatto può essere al doppio)
TENTATIVI = 5           # riletture se il file cambia fra lettura e scrittura

AIUTO = """arturo note: le note sulla finestra di Volta Celeste (⌘⇧N), dal lato di Claude.

  arturo note elenco [--tutte] [--progetto P] [--json | --md]   le note aperte; --md come brief
  arturo note mostra ID [--json]                                 la nota intera e il ritaglio del punto
  arturo note prendi ID [--json]                                 Claude ci lavora (il todo va in corso)
  arturo note rispondi ID "testo" [--chi C] [--json]             una risposta nel filo della nota
  arturo note risolvi ID "riassunto" [--chi C] [--json]          la chiude e chiude il todo
  arturo note scarta ID "motivo" [--chi C] [--json]              la chiude senza farla e scarta il todo

ID è il nome della cartella della nota (2026-11-10_07-00-00), oppure il suo numero se fra le note
aperte un solo segno ha quel numero. Il giro di Claude: elenco, mostra, prendi, lavoro, risolvi.

--chi dice chi scrive: claude (il predefinito) o federico, cioè la persona che ha lasciato la nota.
I bottoni della finestra usano --chi federico, e con lui risolvi e scarta vanno anche senza testo.
--json stampa la nota dopo il gesto, con todo_esito: cosa è successo al todo collegato.
Un testo che comincia con due trattini va dopo --: arturo note rispondi 3 -- "--tutte non serve"."""


class ErroreNota(ValueError):
    """Un uso sbagliato o una nota che non c'è: il messaggio è già in italiano."""


def cartella() -> Path:
    """La stessa del mod (nota.js, cartellaNote): ~/.claude/data/note-finestra, dall'Orsa (radici.py)."""
    return radice_orsa() / "data" / "note-finestra"


def adesso() -> str:
    """L'ora come la scrive il mod (toISOString): UTC con i millesimi e la Z."""
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _data(quando) -> dt.datetime | None:
    try:
        d = dt.datetime.fromisoformat(str(quando).replace("Z", "+00:00"))
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)


def eta(quando, ora: dt.datetime | None = None) -> str:
    """Come eta() di nota.js: "adesso", "12 min fa", "3 ore fa", "ieri", "4 giorni fa"."""
    t = _data(quando)
    if t is None:
        return ""
    minuti = max(0, int(((ora or dt.datetime.now(dt.timezone.utc)) - t).total_seconds() // 60))
    if minuti < 1:
        return "adesso"
    if minuti < 60:
        return f"{minuti} min fa"
    ore = minuti // 60
    if ore < 24:
        return "1 ora fa" if ore == 1 else f"{ore} ore fa"
    giorni = ore // 24
    return "ieri" if giorni == 1 else f"{giorni} giorni fa"


def leggi_nota(testo: str, ident: str) -> dict | None:
    """Come leggiNota() di nota.js: una nota versione 1 o 2 come versione 2, None se non si legge."""
    try:
        d = json.loads(testo)
    except ValueError:
        return None
    if not isinstance(d, dict) or not d.get("punto") or not d.get("finestra") or not isinstance(d.get("testo"), str):
        return None
    filo = d.get("filo") if isinstance(d.get("filo"), list) and d.get("filo") else \
        [{"chi": "federico", "quando": d.get("quando"), "testo": d["testo"]}]
    numero = d.get("numero")
    return {**d, "versione": 2, "id": d.get("id") or ident,
            "numero": numero if isinstance(numero, int) and not isinstance(numero, bool) else None,
            "tipo": d.get("tipo") if d.get("tipo") in TIPI else TIPO_PREDEFINITO,
            "dove": {**VUOTO, **(d.get("dove") if isinstance(d.get("dove"), dict) else {})},
            "stato": d.get("stato") if d.get("stato") in STATI else "aperta",
            "chiusa_quando": d.get("chiusa_quando"), "riassunto": d.get("riassunto"), "motivo": d.get("motivo"),
            "filo": filo, "todo": d.get("todo")}


def tutte() -> list:
    """Tutte le note leggibili, in ordine di nome: [nota, ...]. Una cartella senza nota.json si salta."""
    base = cartella()
    out = []
    for nome in (sorted(os.listdir(base)) if base.is_dir() else []):
        try:
            testo = (base / nome / "nota.json").read_text(encoding="utf-8")
        except OSError:
            continue
        n = leggi_nota(testo, nome)
        if n:
            out.append(n)
    return out


def numerate(lista: list) -> list:
    """Come noteAperte() di nota.js, per ogni progetto: una nota aperta senza numero prende il primo libero,
    nell'ordine in cui è nata. Ritorna la lista con i numeri messi; le chiuse restano senza numero."""
    per_progetto = {}
    for n in lista:
        if n["stato"] in APERTE:
            per_progetto.setdefault(n.get("progetto") or None, []).append(n)
    numeri = {}
    for qui in per_progetto.values():
        qui.sort(key=lambda n: str(n.get("quando") or n["id"]))
        presi = {n["numero"] for n in qui if n["numero"] is not None}
        libero = 1
        for n in qui:
            if n["numero"] is not None:
                numeri[n["id"]] = n["numero"]
                continue
            while libero in presi:
                libero += 1
            presi.add(libero)
            numeri[n["id"]] = libero
    return [{**n, "numero": numeri.get(n["id"]) if n["stato"] in APERTE else None} for n in lista]


def trova(ident: str, lista: list | None = None) -> dict:
    """La nota col nome di cartella `ident`, o l'unica aperta col numero `ident`."""
    ident = str(ident).strip().lstrip("#")
    lista = numerate(tutte() if lista is None else lista)
    for n in lista:
        if n["id"] == ident:
            return n
    if ident.isdigit():
        stesse = [n for n in lista if n["numero"] == int(ident)]
        if len(stesse) == 1:
            return stesse[0]
        if len(stesse) > 1:
            raise ErroreNota(f"più note aperte hanno il numero {ident} ({', '.join(n['progetto'] or '-' for n in stesse)}): "
                             "scrivi il nome della cartella, lo trovi con arturo note elenco")
    if not ID.match(ident):
        raise ErroreNota(f'"{ident}" non è il nome di una nota')
    raise ErroreNota(f"nessuna nota {ident} in {cartella()}")


def _sostituisci(file: Path, letto: str, nuovo: str) -> bool:
    """Scrive `nuovo` al posto di `file` solo se il file è ancora `letto`: False se nel frattempo è cambiato.
    Il testo passa da un file temporaneo nella stessa cartella: chi legge trova la nota vecchia o la nuova."""
    fd, temporaneo = tempfile.mkstemp(prefix=".nota.", suffix=".tmp", dir=str(file.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(nuovo)
            f.flush()
            os.fsync(f.fileno())
        try:
            ora = file.read_text(encoding="utf-8")
        except OSError:
            ora = None
        if ora != letto:
            os.unlink(temporaneo)
            return False
        os.replace(temporaneo, str(file))
        return True
    except BaseException:
        try:
            os.unlink(temporaneo)
        except FileNotFoundError:
            pass
        raise


def aggiorna(ident: str, cambia) -> dict:
    """Rilegge la nota, applica cambia(nota) -> nota nuova, e la scrive solo se il file non è cambiato nel
    frattempo; se è cambiato (il velo ha appena scritto), rilegge e rifà la modifica sulla versione nuova."""
    n = trova(ident)
    file = cartella() / n["id"] / "nota.json"
    for _ in range(TENTATIVI):
        letto = file.read_text(encoding="utf-8")
        attuale = leggi_nota(letto, n["id"])
        if attuale is None:
            raise ErroreNota(f"{file} non si legge come nota")
        attuale["numero"] = attuale["numero"] if attuale["numero"] is not None else n["numero"]
        nuova = cambia(attuale)
        if _sostituisci(file, letto, json.dumps(nuova, ensure_ascii=False, indent=2)):
            return nuova
    raise ErroreNota(f"la nota {n['id']} cambia di continuo: riprova fra poco")


def _pulito(testo) -> str:
    return " ".join(str(testo or "").split())


def voce(chi: str, testo: str) -> dict:
    return {"chi": chi, "quando": adesso(), "testo": testo}


def prendi(n: dict) -> dict:
    if n["stato"] not in APERTE:
        raise ErroreNota(f"la nota {n['id']} è già {n['stato']}")
    return {**n, "stato": "presa"}


def rispondi(n: dict, testo: str, chi: str = "claude") -> dict:
    return {**n, "filo": [*n["filo"], voce(chi, testo)]}


def chiudi(n: dict, stato: str, testo: str, chi: str = "claude") -> dict:
    """Come chiudiNota() di nota.js: "risolta" col riassunto o "scartata" col motivo; il testo va nel filo."""
    if n["stato"] not in APERTE:
        raise ErroreNota(f"la nota {n['id']} è già {n['stato']}")
    v = voce(chi, testo) if testo else None
    return {**n, "stato": stato, "chiusa_quando": v["quando"] if v else adesso(),
            "riassunto": (testo or None) if stato == "risolta" else None,
            "motivo": (testo or None) if stato == "scartata" else None,
            "filo": [*n["filo"], v] if v else n["filo"]}


def todo(argv: list) -> tuple:
    """`arturo todo <argv>` con lo stesso Python: passa dalla fonte dei task della persona, se c'è.
    Ritorna (codice, prima riga utile dell'uscita)."""
    arturo = Path(os.path.realpath(__file__)).parent / "arturo"
    try:
        r = subprocess.run([sys.executable, str(arturo), "todo", *argv], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=150,
                           env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    except (OSError, subprocess.SubprocessError) as e:
        return 3, str(e)
    righe = [x.strip() for x in (r.stdout + "\n" + r.stderr).splitlines() if x.strip()]
    return r.returncode, (righe[0] if righe else "")


def sul_todo(n: dict, argv: list) -> str | None:
    """Porta il gesto sul todo della nota; il messaggio da stampare, o None se la nota non ha todo."""
    if n.get("todo") in (None, ""):
        return None
    codice, testo = todo([argv[0], str(n["todo"]), *argv[1:]])
    if codice == 0:
        return f"Todo #{n['todo']}: {testo}"
    return f"Attenzione: il todo #{n['todo']} non è cambiato ({testo or f'uscita {codice}'})"


# Il ritaglio dello scatto attorno al punto.

def misura_png(file: Path) -> tuple | None:
    """(larghezza, altezza) in pixel di un PNG, dall'intestazione IHDR; None se non è un PNG."""
    try:
        with open(file, "rb") as f:
            testa = f.read(24)
    except OSError:
        return None
    if len(testa) < 24 or testa[:8] != b"\x89PNG\r\n\x1a\n" or testa[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", testa[16:24])


def riquadro(n: dict, pixel: tuple) -> dict:
    """Il riquadro del ritaglio in pixel dello scatto: RITAGLIO attorno al punto, tenuto dentro lo scatto.
    Lo scatto può essere al doppio della finestra (Retina): la scala viene dalle due larghezze. Dà anche
    dove cade il punto dentro il ritaglio."""
    W, H = pixel
    f = n["finestra"]
    scala = W / f["larghezza"] if f.get("larghezza") else 1
    w, h = min(W, round(RITAGLIO[0] * scala)), min(H, round(RITAGLIO[1] * scala))
    px, py = round(n["punto"]["x"] * scala), round(n["punto"]["y"] * scala)
    x = min(max(px - w // 2, 0), W - w)
    y = min(max(py - h // 2, 0), H - h)
    # sips di macOS 27 ignora il ritaglio nell'angolo in basso a sinistra esatto (x 0 e y H-h, provato il
    # 10/11/2026) e ridà lo scatto intero: un pixel più su non si vede e lo fa ritagliare.
    if x == 0 and y == H - h and y > 0:
        y -= 1
    return {"x": x, "y": y, "larghezza": w, "altezza": h, "punto": {"x": px - x, "y": py - y}, "scala": scala}


def ritaglia(n: dict) -> dict:
    """ritaglio.png accanto allo scatto. Con ffmpeg il punto ha un quadrato arancione attorno; senza, sips
    (macOS) ritaglia soltanto. Senza nessuno dei due vale lo scatto intero. Ritorna { file, come, riquadro }."""
    base = cartella() / n["id"]
    scatto = base / (n.get("screenshot") or "finestra.png")
    pixel = misura_png(scatto)
    if not pixel:
        return {"file": None, "come": "nessuno scatto", "riquadro": None}
    r = riquadro(n, pixel)
    fuori = base / "ritaglio.png"
    lato = max(16, round(24 * r["scala"]))
    spesso = max(2, round(2 * r["scala"]))
    ffmpeg, sips = shutil.which("ffmpeg"), shutil.which("sips")
    prove = []
    if ffmpeg:
        filtro = (f"crop={r['larghezza']}:{r['altezza']}:{r['x']}:{r['y']},"
                  f"drawbox=x={r['punto']['x'] - lato // 2}:y={r['punto']['y'] - lato // 2}:w={lato}:h={lato}:"
                  f"color=0xf2a24a:t={spesso}")
        prove.append(("ffmpeg", [ffmpeg, "-v", "error", "-y", "-i", str(scatto), "-vf", filtro, "-frames:v", "1",
                                 str(fuori)]))
    if sips:
        prove.append(("sips", [sips, "-c", str(r["altezza"]), str(r["larghezza"]), "--cropOffset", str(r["y"]),
                               str(r["x"]), str(scatto), "--out", str(fuori)]))
    for come, argv in prove:
        try:
            esito = subprocess.run(argv, capture_output=True, timeout=60)
        except (OSError, subprocess.SubprocessError):
            continue
        if esito.returncode == 0 and misura_png(fuori) == (r["larghezza"], r["altezza"]):
            return {"file": str(fuori), "come": come, "riquadro": r}
    return {"file": str(scatto), "come": "scatto intero", "riquadro": None}


# La stampa.

def _ultima_di_claude(n: dict) -> str | None:
    voci = [v for v in n["filo"] if isinstance(v, dict) and v.get("chi") == "claude"]
    return voci[-1].get("testo") if voci else None


def _dove(n: dict) -> str:
    d = n["dove"]
    # L'elemento (riga, bottone, scheda) c'è nelle note prese con Volta Celeste, che sa dove sta ogni elemento.
    e = d.get("elemento") if isinstance(d.get("elemento"), dict) else None
    pezzi = [f"su {e.get('nome') or e['id']} ({e['id']})" if e and e.get("id") else "",
             f"parte {d['blocco']}" if d.get("blocco") else "",
             f"terminale {d['titolo'] or d['terminale']}" if d.get("terminale") else "",
             f"in {d['cwd']}" if d.get("cwd") else ""]
    return ", ".join(p for p in pezzi if p) or "parte non nota"


def scelte(lista: list, tutte_: bool, progetto: str | None) -> list:
    """Le note dell'elenco: aperte per progetto e numero, poi con --tutte le chiuse dalla più recente."""
    lista = numerate(lista)
    if progetto is not None:
        lista = [n for n in lista if (n.get("progetto") or None) == (progetto or None)]
    aperte = sorted((n for n in lista if n["stato"] in APERTE), key=lambda n: (str(n.get("progetto") or ""), n["numero"]))
    chiuse = sorted((n for n in lista if n["stato"] not in APERTE),
                    key=lambda n: str(n.get("chiusa_quando") or n.get("quando") or n["id"]), reverse=True) if tutte_ else []
    return aperte + chiuse


def per_json(n: dict) -> dict:
    return {**n, "cartella": str(cartella() / n["id"]), "eta": eta(n.get("quando")),
            "ultima_di_claude": _ultima_di_claude(n)}


def stampa_elenco(lista: list) -> None:
    if not lista:
        print("Nessuna nota aperta sulla finestra.")
        return
    for n in lista:
        segno = f"[{n['numero']}]" if n["numero"] is not None else "[-]"
        print(f"{segno} {n['id']} · {n.get('progetto') or 'senza progetto'} · {TIPI[n['tipo']]} · "
              f"{STATI[n['stato']]} · {eta(n.get('chiusa_quando') if n['stato'] not in APERTE else n.get('quando'))}")
        print(f"    {n['testo']}")
        print(f"    {_dove(n)}")
        risposta = _ultima_di_claude(n)
        if risposta:
            print(f"    Claude: {risposta}")
        if n["stato"] not in APERTE and (n.get("riassunto") or n.get("motivo")):
            print(f"    chiusa: {n.get('riassunto') or n.get('motivo')}")


def brief(lista: list) -> str:
    """Le note come il brief di Agentation: una sezione per nota, con cosa, dove e da dove partire."""
    aperte = [n for n in lista if n["stato"] in APERTE]
    righe = [f"# Note sulla finestra di Volta Celeste: {len(aperte)} {'aperta' if len(aperte) == 1 else 'aperte'}", ""]
    if not lista:
        righe.append("Nessuna nota.")
    for n in lista:
        segno = f"Nota {n['numero']}" if n["numero"] is not None else "Nota chiusa"
        righe += [f"## {segno} · {TIPI[n['tipo']]} · {n.get('progetto') or 'senza progetto'}", "",
                  f"- **Cosa:** {n['testo']}",
                  f"- **Dove:** {_dove(n)}, punto {n['punto']['x']},{n['punto']['y']} su una finestra di "
                  f"{n['finestra']['larghezza']}x{n['finestra']['altezza']}",
                  f"- **Stato:** {STATI[n['stato']]}, {eta(n.get('quando'))}"
                  + (f" · todo #{n['todo']}" if n.get("todo") not in (None, "") else "")]
        risposta = _ultima_di_claude(n)
        if risposta:
            righe.append(f"- **Ultima risposta di Claude:** {risposta}")
        if n["stato"] not in APERTE:
            righe.append(f"- **Chiusa:** {n.get('riassunto') or n.get('motivo') or n['stato']}")
        else:
            righe.append(f"- **Per leggerla:** `arturo note mostra {n['id']}`")
        righe.append("")
    return "\n".join(righe).rstrip() + "\n"


def stampa_nota(n: dict, rit: dict) -> None:
    print(f"Nota {n['numero'] if n['numero'] is not None else '(chiusa)'} · {n['id']} · {TIPI[n['tipo']]} · {STATI[n['stato']]}")
    print(f"  progetto   {n.get('progetto') or 'nessuno'}")
    print(f"  quando     {n.get('quando')} ({eta(n.get('quando'))})")
    print(f"  dove       {_dove(n)}")
    print(f"  punto      {n['punto']['x']},{n['punto']['y']} su una finestra di "
          f"{n['finestra']['larghezza']}x{n['finestra']['altezza']}" + (f", schermata {n['schermo']}" if n.get("schermo") else ""))
    if n.get("todo") not in (None, ""):
        print(f"  todo       #{n['todo']}")
    if n["stato"] not in APERTE:
        print(f"  chiusa     {n.get('chiusa_quando')}: {n.get('riassunto') or n.get('motivo') or n['stato']}")
    print("  filo")
    for v in n["filo"]:
        if isinstance(v, dict):
            print(f"    {'Claude' if v.get('chi') == 'claude' else 'Federico'}: {v.get('testo')}")
    if rit["file"]:
        r = rit["riquadro"]
        dove = f", il punto è a {r['punto']['x']},{r['punto']['y']} nel ritaglio" if r else ""
        print(f"  ritaglio   {rit['file']} ({rit['come']}{dove})")
    else:
        print("  ritaglio   nessuno: la cartella non ha lo scatto")
    scatto = cartella() / n["id"] / (n.get("screenshot") or "finestra.png")
    if scatto.exists():
        print(f"  scatto     {scatto}")
    testo = n["dove"].get("testo_terminale")
    if testo:
        print("  terminale (ultime righe al momento della nota)")
        for r in str(testo).splitlines():
            print(f"    | {r}")


# I comandi.

def _opzioni(argv: list, valori: tuple = (), interruttori: tuple = ()) -> tuple:
    """(posizionali, opzioni): --x VALORE per `valori`, --x per `interruttori`; dopo "--" tutto è testo."""
    posizionali, opzioni = [], {}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--":
            posizionali += argv[i + 1:]
            break
        nome = a[2:].split("=", 1)[0] if a.startswith("--") else None
        if nome in interruttori:
            opzioni[nome] = True
        elif nome in valori:
            if "=" in a:
                opzioni[nome] = a.split("=", 1)[1]
            elif i + 1 < len(argv):
                i += 1
                opzioni[nome] = argv[i]
            else:
                raise ErroreNota(f"--{nome} vuole un valore")
        elif a.startswith("--"):
            raise ErroreNota(f"opzione sconosciuta: {a}")
        else:
            posizionali.append(a)
        i += 1
    return posizionali, opzioni


def main(argv: list) -> int:
    verbo = argv[0] if argv else "elenco"
    if verbo in ("-h", "--help", "aiuto", "help"):
        print(AIUTO)
        return 0
    try:
        return _esegui(verbo, argv[1:])
    except ErroreNota as e:
        print(f"Errore: {e}", file=sys.stderr)
        return 2


def _esegui(verbo: str, resto: list) -> int:
    if verbo == "elenco":
        pos, op = _opzioni(resto, valori=("progetto",), interruttori=("tutte", "json", "md"))
        if pos:
            raise ErroreNota(f"elenco non vuole argomenti: {' '.join(pos)}")
        lista = scelte(tutte(), bool(op.get("tutte")), op.get("progetto"))
        if op.get("json"):
            print(json.dumps({"versione": 1, "cartella": str(cartella()), "note": [per_json(n) for n in lista]},
                             ensure_ascii=False, indent=2))
        elif op.get("md"):
            print(brief(lista), end="")
        else:
            stampa_elenco(lista)
        return 0
    if verbo == "mostra":
        pos, op = _opzioni(resto, interruttori=("json",))
        if len(pos) != 1:
            raise ErroreNota("scrivi la nota: arturo note mostra ID")
        n = trova(pos[0])
        rit = ritaglia(n)
        if op.get("json"):
            print(json.dumps({**per_json(n), "ritaglio": rit}, ensure_ascii=False, indent=2))
        else:
            stampa_nota(n, rit)
        return 0
    if verbo in ("prendi", "rispondi", "risolvi", "scarta"):
        pos, op = _opzioni(resto, valori=("chi",), interruttori=("json",))
        chi = op.get("chi", "claude")
        if chi not in ("claude", "federico"):
            raise ErroreNota(f'--chi vuole claude o federico, non "{chi}"')
        if not pos:
            raise ErroreNota(f"scrivi la nota: arturo note {verbo} ID" + ("" if verbo == "prendi" else ' "testo"'))
        ident, testo = pos[0], _pulito(" ".join(pos[1:]))
        if verbo == "prendi":
            if testo:
                raise ErroreNota("prendi vuole solo la nota; per scrivere usa rispondi")
            n = aggiorna(ident, prendi)
            esito = f"Presa la nota {n['numero']} ({n['id']}): la finestra mostra che Claude ci lavora"
            todo_msg = sul_todo(n, ["inizia"])
        elif verbo == "rispondi":
            if not testo:
                raise ErroreNota('scrivi la risposta: arturo note rispondi ID "testo"')
            n = aggiorna(ident, lambda x: rispondi(x, testo, chi))
            esito = f"Risposta scritta sulla nota {n['numero']} ({n['id']})"
            todo_msg = sul_todo(n, ["nota", f"{'Claude' if chi == 'claude' else 'Federico'} sulla nota {n['numero']}: {testo}"])
        else:
            stato = "risolta" if verbo == "risolvi" else "scartata"
            if not testo and chi == "claude":
                raise ErroreNota(f'scrivi {"cosa hai fatto" if verbo == "risolvi" else "perché la scarti"}: '
                                 f'arturo note {verbo} ID "testo"')
            n = aggiorna(ident, lambda x: chiudi(x, stato, testo, chi))
            esito = f"Nota {n['id']} {stato}: il segno sparisce dalla finestra"
            todo_msg = sul_todo(n, ["fatto"] if stato == "risolta" else ["scarta", testo or "Nota scartata dalla finestra"])
        if op.get("json"):
            print(json.dumps({**per_json(n), "todo_esito": todo_msg}, ensure_ascii=False))
        else:
            print(esito)
            if todo_msg:
                print(todo_msg)
        return 0
    raise ErroreNota(f"comando sconosciuto: {verbo}. I comandi sono elenco, mostra, prendi, rispondi, risolvi e scarta")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
