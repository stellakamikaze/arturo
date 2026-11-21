#!/usr/bin/env python3
"""giro.py: il giro quotidiano di /monitor, dalle fonti scelte ai todo, senza doppioni.

Il giro ha cinque passi. Lo script fa le parti meccaniche; leggere il testo di altri e scrivere il report
restano al modello, dentro le regole della skill monitor.

  giro.py inizia             apre il giro: cartella, ora d'inizio e, per ogni fonte scelta, come si legge
                             e quanti giorni (cursori.py). Exit 3 senza fonti scelte: è il primo avvio
  giro.py leggi <fonte>      legge una fonte che sta sul disco (task, sessioni o un ponte personale) e
                             scrive consegna-<fonte>.jsonl nella cartella del giro
  giro.py raccogli           valida tutte le consegne (righe.py), toglie i doppioni coi todo che /monitor
                             ha già creato, e dà a ogni item il suo esito: items.jsonl e raccolta.json
  giro.py aggiungi <hash> [--titolo T] [--progetto P] [--chi tu|decidi|io]
                             crea il todo di un item, con la sua impronta: arturo todo aggiungi --chiave
  giro.py chiudi             avanza i cursori delle fonti lette per intero all'ora d'inizio, segna come
                             viste le proposte mostrate, scrive giro.json

Gli esiti di un item (raccogli):
  stock       viene dai todo o dalle sessioni: è già tracciato per costruzione, va nel report
  agenda      un evento del calendario: si mostra, non diventa un todo
  tracciato   un todo con la stessa impronta c'è già (aperto o chiuso): silenzio
  visto       proposto in un giro di prima e non accolto: si conta, salvo che sia intoccabile
  auto        da un mittente accolto (appreso.json): diventa todo da solo
  respinto    da un mittente rifiutato due volte: si conta in una riga, salvo che sia intoccabile
  proposta    il resto: la persona dice "aggiungi N"
Intoccabile: urgenza rosso, una promessa, o una scadenza entro 7 giorni. Non si declassa mai.

I file del giro stanno in ~/.claude/data/monitor/giri/<AAAA-MM-GG_HHMM>/; giri/CORRENTE dice qual è
l'ultimo. I todo creati da /monitor stanno anche in data/monitor/creati.jsonl: una fonte dei task esterna
che non conosce --chiave non perde la dedup. Le proposte mostrate stanno in data/monitor/visti.jsonl.

Variabili per il banco: ARTURO_HOME (al posto di ~/.claude), ARTURO_OGGI (la data di oggi, AAAA-MM-GG).
Solo libreria standard, Python 3.8 o successivo.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

QUI = Path(os.path.realpath(__file__)).parent
sys.path.insert(0, str(QUI))
import cursori  # noqa: E402
import impara  # noqa: E402
import ponti  # noqa: E402
import righe  # noqa: E402

CASA = ponti.CASA
CARTELLA = CASA / "data" / "monitor"
GIRI = CARTELLA / "giri"
CORRENTE = GIRI / "CORRENTE"
FONTI = CARTELLA / "fonti.json"
CREATI = CARTELLA / "creati.jsonl"
VISTI = CARTELLA / "visti.jsonl"
ARTURO = QUI.parent / "arturo"

# Come si legge ogni ponte di serie. I ponti google leggono tutti la stessa posta: le loro righe portano la
# fonte "email" (e "calendario"), così passare da un ponte all'altro non cambia l'impronta di un thread.
DISCO = ("task", "sessioni")
LETTORE = {"google-connettori": "email", "google-gws": "email"}
DOPO = ("memoria",)
PRIORITA = {"rosso": "alta", "giallo": "media", "verde": "bassa"}
TIMEOUT_PONTE = 300
FERMO_GIORNI = 7


class Errore(Exception):
    """Un problema che la persona o il modello possono correggere: il messaggio dice come."""


def oggi() -> date:
    o = os.environ.get("ARTURO_OGGI")
    return date.fromisoformat(o) if o else date.today()


def leggi_json(file: Path, vuoto=None):
    try:
        return json.loads(file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return vuoto


def scrivi_json(file: Path, dati) -> None:
    file.parent.mkdir(parents=True, exist_ok=True)
    tmp = file.with_name(f".{file.name}.tmp")
    tmp.write_text(json.dumps(dati, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    os.replace(tmp, file)


def jsonl(file: Path) -> list:
    if not file.is_file():
        return []
    fuori = []
    for riga in file.read_text(encoding="utf-8").split("\n"):
        try:
            r = json.loads(riga) if riga.strip() else None
        except ValueError:
            r = None
        if isinstance(r, dict):
            fuori.append(r)
    return fuori


def accoda(file: Path, voci: list) -> None:
    if not voci:
        return
    file.parent.mkdir(parents=True, exist_ok=True)
    with open(file, "a", encoding="utf-8", newline="\n") as f:
        for v in voci:
            f.write(json.dumps(v, ensure_ascii=False) + "\n")


def giro_corrente() -> Path:
    try:
        cartella = Path(CORRENTE.read_text(encoding="utf-8").strip())
    except OSError:
        raise Errore("nessun giro aperto: lancia prima giro.py inizia")
    if not (cartella / "giro.json").is_file():
        raise Errore(f"il giro {cartella.name} non ha giro.json: lancia di nuovo giro.py inizia")
    return cartella


def fonti_scelte() -> list:
    dati = leggi_json(FONTI)
    if dati is None:
        return []
    voci = dati.get("fonti") if isinstance(dati, dict) else None
    return [v for v in voci or [] if isinstance(v, dict) and isinstance(v.get("nome"), str)]


def come(nome: str) -> str:
    if nome in DISCO or nome not in LETTORE and nome not in DOPO:
        return "disco"
    return "lettore" if nome in LETTORE else "dopo"


# --- inizia ---------------------------------------------------------------------------------------

def cmd_inizia(argv) -> int:
    if argv:
        raise Errore("inizia non vuole argomenti")
    scelte = fonti_scelte()
    if not scelte:
        print("primo avvio: nessuna fonte scelta. Prima la scelta delle fonti (fonti.py scrivi)", file=sys.stderr)
        return 3
    stato = cursori.carica()
    if stato is None:
        raise Errore(f"{cursori.FILE} non si legge: correggilo o spostalo prima del giro")
    adesso = datetime.now().replace(second=0, microsecond=0)
    cartella = GIRI / adesso.strftime("%Y-%m-%d_%H%M")
    n = 2
    while (cartella / "giro.json").exists():
        cartella = GIRI / f"{adesso:%Y-%m-%d_%H%M}-{n}"
        n += 1
    piano = []
    for f in scelte:
        modo = come(f["nome"])
        voce = {"nome": f["nome"], "come": modo,
                "giorni": cursori.finestra(stato, f["nome"], int(f.get("finestra") or 7), adesso)}
        if modo == "lettore":
            voce["righe_con_fonte"] = LETTORE[f["nome"]]
        piano.append(voce)
    giro = {"inizio": adesso.isoformat(timespec="minutes"), "cartella": str(cartella), "fonti": piano}
    scrivi_json(cartella / "giro.json", giro)
    CORRENTE.write_text(str(cartella) + "\n", encoding="utf-8")
    print(json.dumps(giro, ensure_ascii=False, indent=1))
    return 0


# --- leggi ----------------------------------------------------------------------------------------

def copertura(fonte, listati, letti, motivo=None, dettaglio=None) -> dict:
    c = {"tipo": "copertura", "fonte": fonte, "listati": listati, "letti": letti, "troncato": bool(motivo)}
    if motivo:
        c["motivo"] = motivo[:300]
    if dettaglio:
        c["dettaglio"] = dettaglio[:300]
    return c


def lancia_todo(*argomenti, timeout=120):
    """La CLI dei todo, con la fonte esterna della persona se c'è: stessi argomenti, stesso codice."""
    try:
        r = subprocess.run([sys.executable, str(ARTURO), "todo", *argomenti], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL, timeout=timeout,
                           env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        return r.returncode, r.stdout, r.stderr
    except (OSError, subprocess.SubprocessError) as e:
        return 3, "", str(e)


def leggi_task(giorni: int) -> list:
    """Gli item dello stock: scaduti, in scadenza entro domani, fermi. Non diventano todo: lo sono già."""
    cod, out, err = lancia_todo("--json")
    try:
        vista = json.loads(out) if cod == 0 else None
    except ValueError:
        vista = None
    if not isinstance(vista, dict):
        return [copertura("task", 0, 0, f"la fonte dei task non risponde (exit {cod}): {err.strip()[-200:]}")]
    adesso, fuori, n = oggi(), [], 0
    for g in vista.get("gruppi") or []:
        if not isinstance(g, dict):
            continue
        for t in g.get("todo") or []:
            if not isinstance(t, dict) or "id" not in t or not t.get("titolo"):
                continue
            n += 1
            gg = t.get("giorni")
            if isinstance(gg, int) and gg < 0:
                urgenza, perche = "rosso", f"scaduto da {-gg} giorni"
            elif isinstance(gg, int) and gg <= 1:
                urgenza, perche = "giallo", "scade oggi" if gg == 0 else "scade domani"
            elif g.get("tipo") == "fermo":
                urgenza, perche = "verde", "fermo: " + (t.get("motivo") or "senza motivo scritto")
            else:
                continue
            scadenza = (adesso + timedelta(days=gg)).isoformat() if isinstance(gg, int) else None
            fuori.append({"tipo": "item", "fonte": "task", "id_sorgente": str(t["id"]), "data": adesso.isoformat(),
                          "scadenza": scadenza, "progetto": t.get("progetto") or None,
                          "riassunto": f"#{t['id']} {t['titolo']}: {perche}"[:300].replace("\n", " "),
                          "urgenza": urgenza, "promessa": None,
                          "extra": {"todo": t["id"], "chi": g.get("tipo")}})
    return fuori + [copertura("task", n, n)]


RIGA_INDICE = re.compile(r"^\|\s*(?P<progetto>[^|]+?)\s*\|\s*\[(?P<file>HANDOFF_[^\]]+)\]\([^)]*\)\s*\|"
                         r"\s*(?P<data>\d{4}-\d{2}-\d{2})\s*\|\s*(?P<stato>[^|]*?)\s*\|\s*(?P<passo>.*?)\s*\|?\s*$")


def leggi_sessioni(giorni: int) -> list:
    """Il prossimo passo dei filoni toccati nella finestra, dall'indice degli handoff (index-rigenera.py)."""
    indice = CASA / "data" / "handoffs" / "INDEX.md"
    try:
        testo = indice.read_text(encoding="utf-8")
    except OSError as e:
        return [copertura("sessioni", 0, 0, f"indice degli handoff illeggibile: {e}")]
    dal = oggi() - timedelta(days=giorni)
    fuori, listati, scartate = [], 0, 0
    for riga in testo.split("\n"):
        m = RIGA_INDICE.match(riga.strip())
        if not m:
            continue
        listati += 1
        try:
            quando = date.fromisoformat(m["data"])
        except ValueError:
            scartate += 1
            continue
        passo = m["passo"].strip()
        if quando < dal or not passo or passo.lower().startswith("niente"):
            continue
        progetto = re.split(r"\s+[—-]\s+", m["progetto"], maxsplit=1)[0].strip()
        stato = m["stato"].lower()
        urgenza = "giallo" if stato.startswith("chiede") or re.match(r"^tu\b", passo, re.I) else "verde"
        fuori.append({"tipo": "item", "fonte": "sessioni", "id_sorgente": m["file"], "data": m["data"],
                      "scadenza": None, "progetto": progetto or None,
                      "riassunto": f"{m['progetto']}: {passo}"[:300], "urgenza": urgenza, "promessa": None,
                      "extra": {"stato": m["stato"]}})
    motivo = f"{scartate} righe con una data illeggibile" if scartate else None
    return fuori + [copertura("sessioni", listati, listati - scartate, motivo)]


def leggi_personale(nome: str, giorni: int) -> list:
    """Un ponte personale: il suo comando, con la finestra nell'ambiente. Consegna solo righe della sua fonte."""
    voce = next((v for v in ponti.personali() if v["nome"] == nome), None)
    if voce is None or voce["stato"] != "pronto":
        motivo = voce["passo"] if voce else "non è più fra i ponti personali (ponti.json)"
        return [copertura(nome, 0, 0, f"ponte non pronto: {motivo}")]
    dichiarati = (leggi_json(CASA / "personale" / "monitor" / "ponti.json", {}) or {}).get("ponti") or []
    argv = next((v["comando"] for v in dichiarati if isinstance(v, dict) and v.get("nome") == nome), None)
    env = dict(os.environ, MONITOR_GIORNI=str(giorni), MONITOR_DAL=(oggi() - timedelta(days=giorni)).isoformat(),
               PYTHONIOENCODING="utf-8")
    try:
        r = subprocess.run([os.path.expanduser(str(a)) for a in argv], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL, timeout=TIMEOUT_PONTE, env=env)
    except (OSError, subprocess.SubprocessError, TypeError) as e:
        return [copertura(nome, 0, 0, f"il ponte non parte: {e}")]
    fuori, altre = [], 0
    for testo in r.stdout.split("\n"):
        try:
            riga = json.loads(testo) if testo.strip() else None
        except ValueError:
            riga = testo  # righe.py la scarta col suo motivo
        if isinstance(riga, dict) and riga.get("fonte") != nome:
            altre += 1  # un ponte non parla a nome di un altro: le sue righe portano il suo nome
            continue
        if riga is not None:
            fuori.append(riga)
    if r.returncode != 0 or altre:
        motivo = (f"il ponte esce con {r.returncode}: {r.stderr.strip()[-150:]}" if r.returncode
                  else f"{altre} righe con una fonte diversa da {nome}, scartate")
        fuori = [x for x in fuori if not (isinstance(x, dict) and x.get("tipo") == "copertura")]
        fuori.append(copertura(nome, 0, 0, motivo))
    return fuori


def cmd_leggi(argv) -> int:
    if len(argv) != 1:
        raise Errore("leggi vuole il nome di una fonte scelta")
    nome = argv[0]
    cartella = giro_corrente()
    giro = leggi_json(cartella / "giro.json", {})
    voce = next((f for f in giro.get("fonti", []) if f.get("nome") == nome), None)
    if voce is None:
        raise Errore(f"{nome} non è fra le fonti di questo giro")
    if voce["come"] != "disco":
        raise Errore(f"{nome} non si legge dal disco: " + ("la legge il lettore (agente monitor-lettore)"
                                                           if voce["come"] == "lettore" else "si usa dopo il report"))
    if nome == "task":
        righe_fonte = leggi_task(voce["giorni"])
    elif nome == "sessioni":
        righe_fonte = leggi_sessioni(voce["giorni"])
    else:
        righe_fonte = leggi_personale(nome, voce["giorni"])
    file = cartella / f"consegna-{nome}.jsonl"
    file.write_text("".join((json.dumps(r, ensure_ascii=False) if isinstance(r, dict) else str(r)) + "\n"
                            for r in righe_fonte), encoding="utf-8", newline="\n")
    item = sum(1 for r in righe_fonte if isinstance(r, dict) and r.get("tipo") == "item")
    cop = next((r for r in righe_fonte if isinstance(r, dict) and r.get("tipo") == "copertura"), None)
    esito = f", NON LETTA PER INTERO: {cop['motivo']}" if cop and cop.get("troncato") else ""
    print(f"OK: {nome}, {item} item in {file.name}{esito}")
    return 0


# --- raccogli -------------------------------------------------------------------------------------

def attese(giro: dict) -> list:
    fuori = []
    for f in giro.get("fonti", []):
        if f["come"] == "dopo":
            continue
        nome = LETTORE.get(f["nome"], f["nome"])
        if nome not in fuori:
            fuori.append(nome)
    return fuori


def intoccabile(r: dict) -> bool:
    if r.get("urgenza") == "rosso" or r.get("promessa"):
        return True
    try:
        return bool(r.get("scadenza")) and date.fromisoformat(r["scadenza"]) <= oggi() + timedelta(days=7)
    except ValueError:
        return False


def impronte_dei_todo() -> tuple:
    """(hash -> id del todo, avviso). La fonte dei task prima, poi i creati di /monitor."""
    noti, avviso = {}, None
    cod, out, _ = lancia_todo("chiavi", "--json")
    try:
        for r in json.loads(out).get("chiavi", []) if cod == 0 else []:
            noti[r["chiave"]] = r.get("id")
    except (ValueError, AttributeError, KeyError, TypeError):
        cod = 2
    if cod != 0:
        avviso = "la fonte dei task non conosce le impronte: la dedup usa solo i todo creati da /monitor"
    for r in jsonl(CREATI):
        if isinstance(r.get("hash"), str):
            noti.setdefault(r["hash"], r.get("id"))
    return noti, avviso


def cmd_raccogli(argv) -> int:
    if argv:
        raise Errore("raccogli non vuole argomenti")
    cartella = giro_corrente()
    giro = leggi_json(cartella / "giro.json", {})
    testo = []
    for file in sorted(cartella.glob("consegna-*.jsonl")):
        testo += [r.rstrip("\r") for r in file.read_text(encoding="utf-8-sig").split("\n")]
    valide, scarti = righe.valida(testo, attese(giro))
    noti, avviso = impronte_dei_todo()
    visti = {r.get("hash") for r in jsonl(VISTI)}
    appreso = impara.carica_appreso() or impara.vuoto()
    mittenti = appreso.get("mittenti") or {}
    items, conti, coperture = [], {}, []
    for r in valide:
        if r["tipo"] == "copertura":
            coperture.append(r)
            continue
        mittente = str((r.get("extra") or {}).get("mittente") or "").strip().lower()
        stato_m = (mittenti.get(mittente) or {}).get("stato") if mittente else None
        if r["fonte"] in DISCO:
            esito = "stock"
        elif r["fonte"] == "calendario":
            esito = "agenda"
        elif r["hash"] in noti:
            esito = "tracciato"
        elif r["hash"] in visti and not intoccabile(r):
            esito = "visto"
        elif stato_m == "si":
            esito = "auto"
        elif stato_m == "no" and not intoccabile(r):
            esito = "respinto"
        else:
            esito = "proposta"
        voce = dict(r, esito=esito, intoccabile=intoccabile(r))
        if esito == "tracciato":
            voce["todo"] = noti[r["hash"]]
        items.append(voce)
        conti[esito] = conti.get(esito, 0) + 1
    ordine = {"rosso": 0, "giallo": 1, "verde": 2}
    items.sort(key=lambda v: (ordine[v["urgenza"]], v.get("scadenza") or "9999", v["data"]))
    for n, v in enumerate(items, 1):
        v["n"] = n
    (cartella / "items.jsonl").write_text("".join(json.dumps(v, ensure_ascii=False) + "\n" for v in items),
                                          encoding="utf-8", newline="\n")
    coperte = {c["fonte"] for c in coperture}
    raccolta = {"conti": conti, "coperture": coperture, "scarti": scarti, "avvisi": [avviso] if avviso else [],
                "non_lette": [f for f in attese(giro) if f not in coperte]}
    scrivi_json(cartella / "raccolta.json", raccolta)
    print(json.dumps(raccolta, ensure_ascii=False, indent=1))
    return 1 if scarti else 0


# --- aggiungi -------------------------------------------------------------------------------------

def cmd_aggiungi(argv) -> int:
    if not argv or argv[0].startswith("-"):
        raise Errore("aggiungi vuole l'hash di un item di items.jsonl")
    h, opzioni, i = argv[0], {}, 1
    while i < len(argv):
        if argv[i] not in ("--titolo", "--progetto", "--chi") or i + 1 >= len(argv):
            raise Errore(f"opzione non prevista o senza valore: {argv[i]}")
        opzioni[argv[i][2:]] = argv[i + 1]
        i += 2
    cartella = giro_corrente()
    voce = next((v for v in jsonl(cartella / "items.jsonl") if v.get("hash") == h), None)
    if voce is None:
        raise Errore(f"{h}: non è un item di questo giro (items.jsonl)")
    if voce["esito"] in ("stock", "agenda", "tracciato"):
        raise Errore(f"{h}: è {voce['esito']}, non diventa un todo nuovo")
    titolo = (opzioni.get("titolo") or voce["riassunto"]).strip()
    base = ["aggiungi", "--", titolo] if titolo.startswith("-") else ["aggiungi", titolo]
    args = [*base, "--progetto", opzioni.get("progetto") or voce.get("progetto") or "generale",
            "--priorita", PRIORITA[voce["urgenza"]], "--perche", f"{voce['fonte']} {voce['id_sorgente']}: "
            + voce["riassunto"]]
    if voce.get("scadenza"):
        args += ["--scadenza", voce["scadenza"]]
    if opzioni.get("chi"):
        args += ["--chi", opzioni["chi"]]
    cod, out, err = lancia_todo(*args, "--chiave", h)
    if cod == 2 and "--chiave" in err:
        cod, out, err = lancia_todo(*args)  # una fonte esterna senza impronte: la dedup resta in creati.jsonl
    m = re.search(r"#(\d+)", out)
    if cod != 0 or not m:
        print((err or out).strip(), file=sys.stderr)
        print(f"ERRORE: todo non creato per {h} (exit {cod})", file=sys.stderr)
        return 3 if cod == 3 else 2
    accoda(CREATI, [{"hash": h, "id": int(m[1]), "giro": cartella.name, "fonte": voce["fonte"],
                     "quando": datetime.now().isoformat(timespec="minutes")}])
    mittente = str((voce.get("extra") or {}).get("mittente") or "").strip().lower()
    if voce["esito"] in ("proposta", "respinto", "visto") and mittente:
        # La persona ha accolto un mittente nuovo: il segnale lo impara, e dal giro dopo va da solo (impara.py).
        impara.accoda(impara.SEGNALI, [impara.valida({"tipo": "proposta_accolta", "mittente": mittente,
                                                      "hash": h, "giro": cartella.name, "origine": "monitor"})])
    print(out.strip())
    return 0


# --- chiudi ---------------------------------------------------------------------------------------

def cmd_chiudi(argv) -> int:
    if argv:
        raise Errore("chiudi non vuole argomenti")
    cartella = giro_corrente()
    giro = leggi_json(cartella / "giro.json", {})
    raccolta = leggi_json(cartella / "raccolta.json")
    if raccolta is None:
        raise Errore("manca raccolta.json: lancia prima giro.py raccogli")
    intere = {c["fonte"] for c in raccolta.get("coperture", []) if not c.get("troncato")}
    troncate = {c["fonte"] for c in raccolta.get("coperture", []) if c.get("troncato")}
    avanzate, ferme = [], []
    for f in giro.get("fonti", []):
        if f["come"] == "dopo":
            continue
        letta = LETTORE.get(f["nome"], f["nome"])
        # Una fonte avanza solo se letta per intero e senza una consegna troncata: il giro dopo rilegge il buco.
        (avanzate if letta in intere and letta not in troncate else ferme).append(f["nome"])
    stato = cursori.carica()
    if stato is None:
        raise Errore(f"{cursori.FILE} non si legge: nessun cursore avanzato")
    for nome in avanzate:
        stato["cursori"][nome] = giro["inizio"]
    if avanzate:
        cursori.salva(stato)
    items = jsonl(cartella / "items.jsonl")
    gia = {r.get("hash") for r in jsonl(VISTI)}
    creati = {r.get("hash") for r in jsonl(CREATI)}
    nuovi = [{"hash": v["hash"], "giro": cartella.name, "esito": v["esito"]} for v in items
             if v["esito"] in ("proposta", "respinto") and v["hash"] not in gia and v["hash"] not in creati]
    accoda(VISTI, nuovi)
    giro.update(fine=datetime.now().isoformat(timespec="minutes"), cursori_avanzati=avanzate, ferme=ferme,
                conti=raccolta.get("conti", {}), proposte_viste=len(nuovi),
                creati=sum(1 for r in jsonl(CREATI) if r.get("giro") == cartella.name))
    scrivi_json(cartella / "giro.json", giro)
    print(f"OK: giro chiuso. Cursori avanzati: {', '.join(avanzate) or 'nessuno'}"
          + (f". Restano indietro: {', '.join(ferme)}" if ferme else ""))
    return 0


COMANDI = {"inizia": cmd_inizia, "leggi": cmd_leggi, "raccogli": cmd_raccogli, "aggiungi": cmd_aggiungi,
           "chiudi": cmd_chiudi}


def main(argv) -> int:
    for flusso in (sys.stdout, sys.stderr):
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    if not argv or argv[0] not in COMANDI:
        print(__doc__, file=sys.stderr)
        return 2
    try:
        return COMANDI[argv[0]](argv[1:])
    except Errore as e:
        print(f"ERRORE: {e}", file=sys.stderr)
        return 2
    except impara.Errore as e:
        print(f"ERRORE: segnale non registrato: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
