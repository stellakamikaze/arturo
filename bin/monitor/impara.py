#!/usr/bin/env python3
"""impara.py: /monitor impara dalle correzioni della persona.

Il /monitor di ogni persona produce segnali: un task scartato o rimesso in piedi, una proposta da un
mittente nuovo accolta o rifiutata, una voce del report su cui la persona ha agito. Questo modulo li
tiene, ne ricava cosa cambiare e lo applica col sì della persona, oppure da solo se lei l'ha scelto.
Ogni modifica ha un id e si annulla.

  impara.py segna <tipo> [--campo valore ...]   aggiunge un segnale (campi sotto)
  impara.py raccogli <file.jsonl>                importa i segnali di un ponte, senza doppioni
  impara.py calcola [--modo auto|proposta]       ricava le modifiche; con auto le applica
  impara.py applica <id> [<id> ...]              applica le modifiche proposte scelte
  impara.py riepilogo [--dal AAAA-MM-GGTHH:MM]   le righe "Appreso" per il report, con l'annullo
  impara.py annulla <id>                         riporta una modifica allo stato di prima
  impara.py mostra                               lo stato appreso

Tipi di segnale:
  scartato, fatto, gia_fatto        un task chiuso dalla persona (gia_fatto: era fatto prima che
                                    /monitor lo proponesse)
  ripristinato                      un task scartato o un item declassato rimesso in piedi; con
                                    --regola è un errore di quella regola
  declassato                        /monitor ha declassato un item con una regola (--regola)
  proposta_accolta, proposta_rifiutata
                                    la persona ha accolto o rifiutato la proposta di un mittente nuovo
                                    (--mittente)
  voce_mostrata, voce_agita         una voce del report di un giro (--sezione, --giro), e la persona
                                    che ci ha agito sopra
Campi: --quando --fonte --mittente --regola --sezione --giro --motivo --task --hash --origine
(chat, pannello, coda, monitor, altro) --intoccabile (una cifra, una scadenza vicina, una domanda
diretta: un segnale intoccabile non conta mai verso un "no" o una sezione compressa).

Cosa impara, con soglie fisse:
  mittenti  una proposta accolta e nessun rifiuto in più: il mittente va da solo nei task ("si");
            due rifiuti e nessuna accolta: il mittente non torna fra le proposte ("no")
  regole    due ripristini sugli ultimi cinque usi della regola: la regola si sospende
  sezioni   nessuna azione negli ultimi cinque giri che la mostrano: la sezione si comprime in una
            riga contata. Le sezioni dichiarate "sempre" non si comprimono mai. L'ordine delle sezioni
            segue la quota di voci agite

Il modo di serie è "proposta": le modifiche si stampano e non si scrivono. La persona lo cambia in
personale/monitor/apprendimento.json: {"modo": "auto", "sempre": ["scadenze"]}.

File, tutti in data/monitor/ e solo di Arturo: segnali.jsonl, appreso.json, appreso-registro.jsonl.
Variabile per il banco: ARTURO_HOME (al posto della radice dell'Orsa). Solo libreria standard,
Python 3.8 o successivo.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
sys.path.append(str(Path(os.path.realpath(__file__)).parents[2] / "hooks"))
from radici import comando_arturo, radice_orsa  # noqa: E402

CASA = Path(os.environ.get("ARTURO_HOME") or radice_orsa())
CARTELLA = CASA / "data" / "monitor"
SEGNALI = CARTELLA / "segnali.jsonl"
APPRESO = CARTELLA / "appreso.json"
REGISTRO = CARTELLA / "appreso-registro.jsonl"
CONFIG = CASA / "personale" / "monitor" / "apprendimento.json"

TIPI = ("scartato", "fatto", "gia_fatto", "ripristinato", "declassato", "proposta_accolta",
        "proposta_rifiutata", "voce_mostrata", "voce_agita")
CAMPI = ("quando", "fonte", "mittente", "regola", "sezione", "giro", "motivo", "task", "hash", "origine")
ORIGINI = ("chat", "pannello", "coda", "monitor", "altro")
RICHIESTI = {"proposta_accolta": ("mittente",), "proposta_rifiutata": ("mittente",),
             "declassato": ("regola",), "voce_mostrata": ("sezione", "giro"), "voce_agita": ("sezione", "giro")}
MODI = ("auto", "proposta")
LUNGHEZZA = 300
FINESTRA_GIORNI = 180
ULTIMI_USI = 5
FALLIMENTI_PER_SOSPENDERE = 2
GIRI_PER_SEZIONE = 5


class Errore(Exception):
    pass


# --- lettura e scrittura ---------------------------------------------------------------------------

def adesso() -> datetime:
    return datetime.now().replace(second=0, microsecond=0)


def data(valore):
    """Un istante AAAA-MM-GGTHH:MM (o solo il giorno) senza fuso; None se non lo è."""
    try:
        d = datetime.fromisoformat(str(valore))
    except ValueError:
        return None
    return None if d.tzinfo is not None else d


def scrivi_atomico(file: Path, testo: str):
    file.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(file.parent), prefix=f".{file.stem}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(testo)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, str(file))
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def accoda(file: Path, righe):
    if not righe:
        return
    file.parent.mkdir(parents=True, exist_ok=True)
    with open(file, "a", encoding="utf-8", newline="\n") as f:
        for r in righe:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def leggi_jsonl(file: Path):
    """Le righe valide di un file jsonl; una riga rotta si salta, non ferma il resto."""
    if not file.exists():
        return []
    righe = []
    for riga in file.read_text(encoding="utf-8-sig").split("\n"):
        riga = riga.strip()
        if not riga:
            continue
        try:
            r = json.loads(riga)
        except ValueError:
            continue
        if isinstance(r, dict):
            righe.append(r)
    return righe


def config():
    """Il modo e le sezioni "sempre" scelte dalla persona. Un file rotto vale come assente: modo proposta."""
    base = {"modo": "proposta", "sempre": []}
    try:
        dati = json.loads(CONFIG.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return base
    if isinstance(dati, dict):
        if dati.get("modo") in MODI:
            base["modo"] = dati["modo"]
        if isinstance(dati.get("sempre"), list):
            base["sempre"] = [str(s) for s in dati["sempre"]]
    return base


def vuoto():
    return {"mittenti": {}, "regole": {}, "sezioni": {}, "ordine": [], "bloccate": {}, "aggiornato": None}


def carica_appreso():
    """Lo stato appreso; None se il file c'è ma non si legge: riscriverlo perderebbe quanto imparato."""
    if not APPRESO.exists():
        return vuoto()
    try:
        dati = json.loads(APPRESO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(dati, dict):
        return None
    stato = vuoto()
    for chiave, base in stato.items():
        if isinstance(base, (dict, list)) and isinstance(dati.get(chiave), type(base)):
            stato[chiave] = dati[chiave]
    stato["aggiornato"] = dati.get("aggiornato")
    return stato


# --- segnali ---------------------------------------------------------------------------------------

def valida(r):
    """Il segnale normalizzato, oppure Errore col motivo."""
    if not isinstance(r, dict):
        raise Errore("il segnale non è un oggetto JSON")
    ignoti = set(r) - set(CAMPI) - {"tipo", "intoccabile"}
    if ignoti:
        raise Errore(f"campo non previsto: {', '.join(sorted(ignoti))}")
    tipo = r.get("tipo")
    if tipo not in TIPI:
        raise Errore(f"tipo non previsto: {tipo!r}")
    s = {"tipo": tipo}
    for campo in CAMPI:
        valore = r.get(campo)
        if valore is None or valore == "":
            continue
        if not isinstance(valore, (str, int)) or isinstance(valore, bool):
            raise Errore(f"{campo}: serve un testo")
        valore = str(valore).strip()
        if "\n" in valore or "\r" in valore or len(valore) > LUNGHEZZA:
            raise Errore(f"{campo}: una riga sola, al massimo {LUNGHEZZA} caratteri")
        s[campo] = valore
    if "mittente" in s:
        s["mittente"] = s["mittente"].lower()
    quando = data(s.get("quando") or adesso().isoformat(timespec="minutes"))
    if quando is None:
        raise Errore("quando: serve AAAA-MM-GGTHH:MM senza fuso")
    s["quando"] = quando.isoformat(timespec="minutes")
    if "origine" in s and s["origine"] not in ORIGINI:
        raise Errore(f"origine: una fra {', '.join(ORIGINI)}")
    for campo in RICHIESTI.get(tipo, ()):
        if campo not in s:
            raise Errore(f"{tipo} vuole --{campo}")
    intoccabile = r.get("intoccabile")
    if intoccabile not in (None, False, True):
        raise Errore("intoccabile: vero o falso")
    if intoccabile:
        s["intoccabile"] = True
    return s


def chiave_segnale(s):
    return tuple(s.get(c) for c in ("tipo", "quando", "task", "mittente", "regola", "sezione", "giro", "hash"))


def recenti(segnali, ora):
    limite = ora - timedelta(days=FINESTRA_GIORNI)
    return [s for s in segnali if (data(s.get("quando")) or limite) >= limite]


# --- calcolo ---------------------------------------------------------------------------------------

def conta(n, uno, molti):
    return f"{n} {uno if n == 1 else molti}"


def stato_mittente(segnali):
    accolte = sum(1 for s in segnali if s["tipo"] == "proposta_accolta")
    rifiutate = sum(1 for s in segnali if s["tipo"] == "proposta_rifiutata" and not s.get("intoccabile"))
    if accolte and accolte >= rifiutate:
        return "si", conta(accolte, "proposta accolta", "proposte accolte")
    if rifiutate >= 2 and not accolte:
        return "no", conta(rifiutate, "proposta rifiutata", "proposte rifiutate")
    return None, None


def stato_regola(segnali):
    usi = sorted((s for s in segnali if s["tipo"] in ("declassato", "ripristinato")), key=lambda s: s["quando"])
    ultimi = usi[-ULTIMI_USI:]
    errori = sum(1 for s in ultimi if s["tipo"] == "ripristinato")
    if errori >= FALLIMENTI_PER_SOSPENDERE:
        return "sospesa", f"{errori} ripristini sugli ultimi {len(ultimi)} usi"
    return "attiva", None


def stato_sezione(sezione, segnali, sempre):
    giri = sorted({s["giro"] for s in segnali if s["tipo"] == "voce_mostrata"})
    ultimi = giri[-GIRI_PER_SEZIONE:]
    agiti = {s["giro"] for s in segnali if s["tipo"] == "voce_agita"}
    mostrate = sum(1 for s in segnali if s["tipo"] == "voce_mostrata" and s["giro"] in ultimi)
    azioni = sum(1 for s in segnali if s["tipo"] == "voce_agita" and s["giro"] in ultimi)
    quota = round(azioni / mostrate, 2) if mostrate else 0.0
    if sezione in sempre or len(ultimi) < GIRI_PER_SEZIONE or any(g in agiti for g in ultimi):
        return "piena", quota, None
    if any(s.get("intoccabile") for s in segnali if s["giro"] in ultimi):
        return "piena", quota, None
    return "compressa", quota, f"nessuna azione negli ultimi {len(ultimi)} giri"


def per_chiave(segnali, campo, tipi):
    gruppi = {}
    for s in segnali:
        if s["tipo"] in tipi and s.get(campo):
            gruppi.setdefault(s[campo], []).append(s)
    return gruppi


def dopo_blocco(gruppo, blocco):
    """Dopo un annullo contano solo i segnali arrivati dopo: le stesse prove non rifanno la stessa modifica."""
    if not blocco:
        return gruppo
    return [s for s in gruppo if s["quando"] > blocco.get("dal", "")]


def modifiche(stato, segnali, sempre):
    """Le modifiche fra lo stato appreso e quello che i segnali dicono, con un id stabile."""
    fuori = []

    def proponi(genere, chiave, prima, dopo, perche):
        if prima == dopo:
            return
        impronta = hashlib.md5(f"{genere}:{chiave}:{dopo}".encode("utf-8")).hexdigest()[:8]
        fuori.append({"id": impronta, "genere": genere, "chiave": chiave, "prima": prima, "dopo": dopo,
                      "perche": perche})

    bloccate = stato.get("bloccate", {})
    for mittente, gruppo in sorted(per_chiave(segnali, "mittente", ("proposta_accolta", "proposta_rifiutata")).items()):
        blocco = bloccate.get(f"mittente:{mittente}")
        nuovo, perche = stato_mittente(dopo_blocco(gruppo, blocco))
        attuale = (stato["mittenti"].get(mittente) or {}).get("stato")
        if blocco and nuovo is None:
            continue
        proponi("mittente", mittente, attuale, nuovo, perche)
    for regola, gruppo in sorted(per_chiave(segnali, "regola", ("declassato", "ripristinato")).items()):
        blocco = bloccate.get(f"regola:{regola}")
        nuovo, perche = stato_regola(dopo_blocco(gruppo, blocco))
        attuale = (stato["regole"].get(regola) or {}).get("stato", "attiva")
        if blocco and nuovo == "attiva":
            continue
        proponi("regola", regola, attuale, nuovo, perche)
    for sezione, gruppo in sorted(per_chiave(segnali, "sezione", ("voce_mostrata", "voce_agita")).items()):
        blocco = bloccate.get(f"sezione:{sezione}")
        nuovo, _quota, perche = stato_sezione(sezione, dopo_blocco(gruppo, blocco), sempre)
        attuale = (stato["sezioni"].get(sezione) or {}).get("stato", "piena")
        if blocco and nuovo == "piena":
            continue
        proponi("sezione", sezione, attuale, nuovo, perche)
    return fuori


def conteggi(stato, segnali, sempre):
    """I numeri che accompagnano lo stato (colpi, quote): si aggiornano sempre, non sono modifiche."""
    for regola, gruppo in per_chiave(segnali, "regola", ("declassato", "ripristinato")).items():
        voce = stato["regole"].setdefault(regola, {"stato": "attiva"})
        voce["usi"] = sum(1 for s in gruppo if s["tipo"] == "declassato")
        voce["ripristini"] = sum(1 for s in gruppo if s["tipo"] == "ripristinato")
    quote = {}
    for sezione, gruppo in per_chiave(segnali, "sezione", ("voce_mostrata", "voce_agita")).items():
        _stato, quota, _ = stato_sezione(sezione, gruppo, sempre)
        stato["sezioni"].setdefault(sezione, {"stato": "piena"})["quota"] = quota
        quote[sezione] = quota
    stato["ordine"] = sorted(quote, key=lambda k: (k not in sempre, -quote[k], k))


def applica_modifica(stato, m):
    gruppo = {"mittente": "mittenti", "regola": "regole", "sezione": "sezioni"}[m["genere"]]
    voce = stato[gruppo].setdefault(m["chiave"], {})
    if m["dopo"] is None:
        stato[gruppo].pop(m["chiave"], None)
    else:
        voce["stato"] = m["dopo"]
        voce["dal"] = adesso().isoformat(timespec="minutes")


def salva_appreso(stato):
    stato["aggiornato"] = adesso().isoformat(timespec="minutes")
    scrivi_atomico(APPRESO, json.dumps(stato, ensure_ascii=False, indent=1, sort_keys=True) + "\n")


# --- frasi -----------------------------------------------------------------------------------------

def frase(m):
    k, dopo = m["chiave"], m["dopo"]
    if m["genere"] == "mittente":
        cosa = {"si": f"{k} va da solo nei task", "no": f"{k} non torna fra le proposte",
                None: f"{k} torna fra le proposte"}[dopo]
    elif m["genere"] == "regola":
        cosa = f"la regola {k} è sospesa" if dopo == "sospesa" else f"la regola {k} torna attiva"
    else:
        cosa = f"la sezione {k} si comprime in una riga" if dopo == "compressa" else f"la sezione {k} torna piena"
    perche = f" ({m['perche']})" if m.get("perche") else ""
    return f"{cosa}{perche}"


# --- comandi ---------------------------------------------------------------------------------------

def cmd_segna(argv):
    if not argv:
        raise Errore("segna vuole un tipo")
    r = {"tipo": argv[0]}
    resto = argv[1:]
    i = 0
    while i < len(resto):
        opz = resto[i]
        if opz == "--intoccabile":
            r["intoccabile"] = True
            i += 1
            continue
        if not opz.startswith("--") or i + 1 >= len(resto):
            raise Errore(f"opzione senza valore: {opz}")
        campo = opz[2:]
        if campo not in CAMPI:
            raise Errore(f"campo non previsto: {campo}")
        r[campo] = resto[i + 1]
        i += 2
    s = valida(r)
    accoda(SEGNALI, [s])
    print(f"OK: segnale {s['tipo']} alle {s['quando']}")
    return 0


def cmd_raccogli(argv):
    if len(argv) != 1:
        raise Errore("raccogli vuole un file jsonl, oppure - per lo standard input")
    if argv[0] == "-":
        testo = sys.stdin.buffer.read().decode("utf-8-sig")
    else:
        try:
            testo = Path(argv[0]).read_text(encoding="utf-8-sig")
        except OSError as e:
            raise Errore(f"il file non si legge: {e}")
    visti = {chiave_segnale(s) for s in leggi_jsonl(SEGNALI)}
    nuovi, doppi, rotti = [], 0, 0
    for n, riga in enumerate(testo.split("\n"), 1):
        riga = riga.strip()
        if not riga:
            continue
        try:
            s = valida(json.loads(riga))
        except (ValueError, Errore) as e:
            rotti += 1
            print(f"riga {n} scartata: {e}", file=sys.stderr)
            continue
        k = chiave_segnale(s)
        if k in visti:
            doppi += 1
            continue
        visti.add(k)
        nuovi.append(s)
    accoda(SEGNALI, nuovi)
    print(f"OK: {len(nuovi)} segnali nuovi, {doppi} già presenti, {rotti} scartati")
    return 1 if rotti else 0


def ricalcola():
    stato = carica_appreso()
    if stato is None:
        raise Errore(f"{APPRESO} non si legge: correggilo o spostalo, niente scritto")
    sempre = config()["sempre"]
    segnali = []
    for s in recenti(leggi_jsonl(SEGNALI), adesso()):
        try:
            segnali.append(valida(s))
        except Errore:
            continue
    return stato, segnali, sempre


def registra(stato, scelte):
    quando = adesso().isoformat(timespec="minutes")
    for m in scelte:
        applica_modifica(stato, m)
    accoda(REGISTRO, [dict(m, quando=quando, azione="applicata") for m in scelte])


def cmd_calcola(argv):
    modo = config()["modo"]
    if argv[:1] == ["--modo"] and len(argv) == 2 and argv[1] in MODI:
        modo = argv[1]
    elif argv:
        raise Errore("calcola vuole al massimo --modo auto|proposta")
    stato, segnali, sempre = ricalcola()
    trovate = modifiche(stato, segnali, sempre)
    if modo == "proposta":
        for m in trovate:
            print(f"PROPOSTA {m['id']}: {frase(m)}")
        print(f"OK: {len(trovate)} proposte, niente scritto. Per applicarle: {comando_arturo()} monitor impara applica <id>")
        return 0
    registra(stato, trovate)
    conteggi(stato, segnali, sempre)
    salva_appreso(stato)
    for m in trovate:
        print(f"APPLICATA {m['id']}: {frase(m)}")
    print(f"OK: {len(trovate)} modifiche applicate")
    return 0


def cmd_applica(argv):
    if not argv:
        raise Errore("applica vuole almeno un id")
    stato, segnali, sempre = ricalcola()
    trovate = {m["id"]: m for m in modifiche(stato, segnali, sempre)}
    ignoti = [i for i in argv if i not in trovate]
    if ignoti:
        raise Errore(f"id non fra le proposte di adesso: {', '.join(ignoti)}; niente scritto")
    scelte = [trovate[i] for i in argv]
    registra(stato, scelte)
    conteggi(stato, segnali, sempre)
    salva_appreso(stato)
    for m in scelte:
        print(f"APPLICATA {m['id']}: {frase(m)}")
    return 0


def cmd_annulla(argv):
    if len(argv) != 1:
        raise Errore("annulla vuole un id")
    stato = carica_appreso()
    if stato is None:
        raise Errore(f"{APPRESO} non si legge: niente annullato")
    voci = [r for r in leggi_jsonl(REGISTRO) if r.get("id") == argv[0] and r.get("azione") == "applicata"]
    if not voci:
        raise Errore(f"nessuna modifica applicata con id {argv[0]}")
    m = voci[-1]
    if m.get("genere") not in ("mittente", "regola", "sezione"):
        raise Errore(f"la voce {argv[0]} del registro è rotta: niente annullato")
    indietro = dict(m, dopo=m.get("prima"), prima=m.get("dopo"), perche=None)
    applica_modifica(stato, indietro)
    quando = adesso().isoformat(timespec="minutes")
    stato["bloccate"][f"{m['genere']}:{m['chiave']}"] = {"valore": m.get("prima"), "dal": quando}
    salva_appreso(stato)
    accoda(REGISTRO, [dict(indietro, id=m["id"], quando=quando, azione="annullata")])
    print(f"OK: annullata {m['id']}: {frase(indietro)}. Le stesse prove non la rifanno")
    return 0


def cmd_riepilogo(argv):
    dal = adesso() - timedelta(days=1)
    if argv[:1] == ["--dal"] and len(argv) == 2:
        dal = data(argv[1])
        if dal is None:
            raise Errore("--dal vuole AAAA-MM-GGTHH:MM")
    elif argv:
        raise Errore("riepilogo vuole al massimo --dal AAAA-MM-GGTHH:MM")
    righe = [r for r in leggi_jsonl(REGISTRO) if (data(r.get("quando")) or datetime.min) >= dal]
    comando = comando_arturo()
    for r in righe:
        if r.get("genere") not in ("mittente", "regola", "sezione"):
            continue
        if r.get("azione") == "annullata":
            print(f"Annullato: {frase(r)}.")
        else:
            print(f"Appreso: {frase(r)}. Per annullare: {comando} monitor impara annulla {r['id']}")
    return 0


def cmd_mostra(_argv):
    stato = carica_appreso()
    if stato is None:
        raise Errore(f"{APPRESO} non si legge")
    print(json.dumps({"modo": config()["modo"], **stato}, ensure_ascii=False, indent=1, sort_keys=True))
    return 0


COMANDI = {"segna": cmd_segna, "raccogli": cmd_raccogli, "calcola": cmd_calcola, "applica": cmd_applica,
           "annulla": cmd_annulla, "riepilogo": cmd_riepilogo, "mostra": cmd_mostra}


def main(argv):
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


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
