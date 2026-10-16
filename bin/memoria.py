"""arturo memoria: la memoria facoltativa di Arturo. È spenta finché non la accendi.

Cosa fa quando è accesa:
- a ogni tuo messaggio l'hook memoria-richiamo.py cerca le note che parlano della stessa cosa e
  ne dà a Claude il percorso. Claude apre una nota solo se gli serve;
- i subagenti sanno che la memoria esiste e come cercarla (memoria-subagente.py);
- ogni scrittura in una nota o in un handoff passa da memoria-scrittura.py: se il testo contiene
  un segreto o un'istruzione nascosta, Claude riceve un avviso.

Le note sono quelle che Claude Code scrive da solo (~/.claude/projects/*/memory/*.md, frontmatter
con name, description e type), più le cartelle che aggiungi tu. Nessun archivio nuovo e nessun
server: tutto resta su questo computer, e niente della memoria entra nella telemetria.

  stato                          accesa o spenta, dove cerca, quante note (anche senza comando)
  accendi | spegni               accende o spegne gli hook della memoria
  cerca "testo" [-n N] [--json]  le note più vicine al testo, anche a memoria spenta
  controlla [--json]             frontmatter mancanti o illeggibili, link rotti
  cartella aggiungi DIR          aggiunge una tua cartella di note
  cartella togli DIR             la toglie (i file restano dove sono)

L'interruttore sta in ~/.claude/data/memoria/impostazioni.json, fuori da git. La variabile
ARTURO_MEMORIA=1 o ARTURO_MEMORIA=0 (nell'ambiente o in "env" di settings.json) vince sul file.
Solo libreria standard, Python 3.8 o successivo.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time
from datetime import date, datetime
from pathlib import Path

AIUTO = __doc__.split("\n\n")[3] if __doc__ else ""

TIPI = ("user", "feedback", "project", "reference")
INDICE = "MEMORY.md"
MAX_BYTE = 256 * 1024  # una nota più grande si legge solo fino a qui

# Parole senza segnale: pezzi di percorso ricorrenti e riempitivi italiani e inglesi.
STOPWORDS = {
    "users", "user", "documents", "desktop", "downloads", "home", "mnt", "tmp", "var",
    "projects", "claude", "memory", "memoria",
    "the", "and", "for", "with", "this", "that", "you", "are", "not", "can",
    "cosa", "come", "fare", "puoi", "dove", "quando", "quale", "questo",
    "questa", "sono", "hai", "del", "della", "che", "per", "una", "con",
    "nel", "nella", "alla", "dei", "delle", "gli", "anche", "poi", "solo",
}


# --- Interruttore e cartelle ---------------------------------------------------------------

def radice() -> Path:
    return Path.home() / ".claude"


def file_impostazioni() -> Path:
    return radice() / "data" / "memoria" / "impostazioni.json"


def leggi_impostazioni() -> dict:
    try:
        dati = json.loads(file_impostazioni().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return dati if isinstance(dati, dict) else {}


def scrivi_impostazioni(dati: dict) -> None:
    f = file_impostazioni()
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_name(f.name + ".tmp")
    tmp.write_text(json.dumps(dati, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(str(tmp), str(f))


def da_ambiente():
    """True o False se ARTURO_MEMORIA decide, None se il file decide."""
    valore = os.environ.get("ARTURO_MEMORIA", "").strip()
    if valore in ("1", "0"):
        return valore == "1"
    return None


def accesa() -> bool:
    env = da_ambiente()
    if env is not None:
        return env
    return leggi_impostazioni().get("accesa") is True


def breve(p) -> str:
    """Il percorso con ~ al posto della cartella home, a barre dritte: su Windows Claude lo usa in Git Bash."""
    s = str(p)
    casa = str(Path.home())
    if s == casa or s.startswith(casa + os.sep):
        return "~" + s[len(casa):].replace(os.sep, "/")
    return s.replace(os.sep, "/")


def cartelle_native() -> list:
    base = radice() / "projects"
    try:
        return sorted(d for d in base.glob("*/memory") if d.is_dir())
    except OSError:
        return []


def cartelle_mie() -> list:
    voci = leggi_impostazioni().get("cartelle") or []
    out = []
    for v in voci if isinstance(voci, list) else []:
        p = Path(os.path.expanduser(str(v)))
        if p.is_dir():
            out.append(p)
    return out


def cartelle() -> list:
    return cartelle_native() + cartelle_mie()


# --- Lettura delle note ----------------------------------------------------------------------

FM = re.compile(r"^---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)", re.S)
CHIAVE = re.compile(r"^([A-Za-z_][\w-]*):\s*(.*)$")


def _scalare(v: str) -> str:
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def frontmatter(testo: str):
    """(campi, corpo). campi è None senza frontmatter. Legge chiavi di primo livello, liste,
    blocchi > e |, e una mappa annidata di un livello (Claude Code scrive `metadata:` con
    `type:` dentro)."""
    m = FM.match(testo)
    if not m:
        return None, testo
    righe = m.group(1).splitlines()
    campi = {}
    i = 0
    while i < len(righe):
        r = righe[i]
        if not r.strip() or r.lstrip().startswith("#") or r[:1] in (" ", "\t"):
            i += 1
            continue
        k = CHIAVE.match(r)
        if not k:
            i += 1
            continue
        chiave, resto = k.group(1), k.group(2).strip()
        j = i + 1
        figli = []
        while j < len(righe) and (righe[j][:1] in (" ", "\t") or righe[j].lstrip().startswith("- ")) and righe[j].strip():
            figli.append(righe[j].strip())
            j += 1
        if resto in (">", "|", ">-", "|-", ">+", "|+"):
            campi[chiave] = " ".join(figli)
        elif resto == "" and figli and all(f.startswith("- ") for f in figli):
            campi[chiave] = [_scalare(f[2:]) for f in figli]
        elif resto == "" and figli:
            mappa = {}
            for f in figli:
                kk = CHIAVE.match(f)
                if kk:
                    mappa[kk.group(1)] = _scalare(kk.group(2))
            campi[chiave] = mappa
        elif resto.startswith("[") and resto.endswith("]"):
            campi[chiave] = [_scalare(x) for x in resto[1:-1].split(",") if x.strip()]
        else:
            campi[chiave] = _scalare(resto)
        i = j
    return campi, testo[m.end():]


def campo(fm: dict, nome: str):
    """Un campo di primo livello o dentro `metadata:`."""
    if not isinstance(fm, dict):
        return None
    v = fm.get(nome)
    if v in (None, "", []):
        meta = fm.get("metadata")
        if isinstance(meta, dict):
            v = meta.get(nome)
    return v


def tipo(fm: dict) -> str:
    return str(campo(fm, "type") or campo(fm, "entity_type") or "?")


def nascosta(rel: Path) -> bool:
    return any(p.startswith(("_", ".")) for p in rel.parts)


def file_note(dirs=None) -> list:
    """I file .md delle note, senza indici, file e cartelle che iniziano con _ o punto, doppioni."""
    visti = set()
    out = []
    for d in cartelle() if dirs is None else dirs:
        try:
            trovati = sorted(d.rglob("*.md"))
        except OSError:
            continue
        for p in trovati:
            if p.name == INDICE or nascosta(p.relative_to(d)):
                continue
            try:
                vero = os.path.realpath(str(p))
            except OSError:
                continue
            if vero in visti:
                continue
            visti.add(vero)
            out.append((d, p))
    return out


def leggi(p: Path) -> str:
    try:
        with p.open("r", encoding="utf-8", errors="replace") as fh:
            return fh.read(MAX_BYTE)
    except OSError:
        return ""


def note(dirs=None):
    """(cartella, percorso, campi, corpo) per ogni nota con frontmatter."""
    for d, p in file_note(dirs):
        fm, corpo = frontmatter(leggi(p))
        if isinstance(fm, dict):
            yield d, p, fm, corpo


def eta_giorni(fm: dict, p: Path):
    """Giorni da last_verified o created; senza date, dall'ultima modifica del file."""
    for k in ("last_verified", "created"):
        v = str(campo(fm, k) or "").strip()
        if v:
            try:
                return (date.today() - datetime.strptime(v[:10], "%Y-%m-%d").date()).days
            except ValueError:
                continue
    try:
        return int((time.time() - p.stat().st_mtime) // 86400)
    except OSError:
        return None


# --- Richiamo per contenuto (il match dell'hook) ---------------------------------------------

def parole(testo: str) -> list:
    out = []
    for w in re.findall(r"[\w']+", (testo or "").lower()):
        w = w.strip("'")
        if len(w) > 2 and w not in STOPWORDS:
            out.append(w)
    return out


def _lista(v) -> list:
    if isinstance(v, list):
        return v
    return [v] if v else []


def punteggio(fm: dict, gettoni: set, corpo: str = "") -> tuple:
    """(punti, gettoni distinti che hanno colpito).

    trigger +3 · name +2 · description +1 · answers +1 · corpo +1, al massimo +2 per nota.
    triggers e answers sono facoltativi: Claude Code non li scrive, una cartella tua sì.
    """
    trig = set()
    for t in _lista(campo(fm, "triggers")):
        trig.update(w for w in re.findall(r"\w+", str(t).lower()) if len(w) > 2)
    nome = str(campo(fm, "name") or "").lower()
    desc = str(campo(fm, "description") or "").lower()
    risposte = " ".join(str(a) for a in _lista(campo(fm, "answers"))).lower()
    corpo_l = corpo.lower()
    punti, nel_corpo, colpiti = 0, 0, set()
    for g in gettoni:
        h = (3 if g in trig else 0) + (2 if g in nome else 0) + (1 if g in desc else 0) + (1 if g in risposte else 0)
        if corpo_l and g in corpo_l:
            nel_corpo += 1
            colpiti.add(g)
        if h:
            punti += h
            colpiti.add(g)
    # il corpo pesa al massimo +2: senza tetto le note lunghe affollano i risultati
    return punti + min(nel_corpo, 2), colpiti


def classifica(gettoni: set, minimo: int = 4, distinti: int = 2, dirs=None) -> list:
    """[(punti, percorso, campi)] in ordine. Servono almeno `distinti` gettoni diversi: un solo
    gettone che colpisce più campi è un segnale debole."""
    out = []
    for _d, p, fm, corpo in note(dirs):
        s, colpiti = punteggio(fm, gettoni, corpo)
        if s >= minimo and len(colpiti) >= distinti:
            out.append((s, p, fm))
    out.sort(key=lambda x: (-x[0], str(x[1])))
    return out


# --- Recall profondo (BM25) -----------------------------------------------------------------

def indice_bm25(dirs=None, solo_frontmatter: bool = False) -> dict:
    """Indicizza frontmatter (peso doppio) e corpo. solo_frontmatter serve solo al banco."""
    docs, df, totale = [], {}, 0
    for _d, p, fm, corpo in note(dirs):
        testa = " ".join(str(campo(fm, k) or "") for k in ("name", "description", "type", "triggers", "answers"))
        gettoni = parole(testa + " " + testa + " " + ("" if solo_frontmatter else corpo))
        tf = {}
        for g in gettoni:
            tf[g] = tf.get(g, 0) + 1
        for g in tf:
            df[g] = df.get(g, 0) + 1
        docs.append({"path": p, "fm": fm, "tf": tf, "dl": len(gettoni)})
        totale += len(gettoni)
    n = len(docs)
    return {"docs": docs, "df": df, "n": n, "avgdl": (totale / n) if n else 1.0}


def cerca(testo: str, n: int = 8, dirs=None, solo_frontmatter: bool = False) -> list:
    """BM25 k1=1,5 b=0,75: [(punti, percorso, campi, gettoni)] con punti > 0."""
    q = parole(testo)
    if len(set(q)) < 2:
        return []
    ix = indice_bm25(dirs, solo_frontmatter)
    k1, b = 1.5, 0.75
    out = []
    for doc in ix["docs"]:
        s, colpiti = 0.0, set()
        for g in q:
            f = doc["tf"].get(g, 0)
            if f <= 0:
                continue
            df = ix["df"].get(g, 0)
            idf = math.log(1 + (ix["n"] - df + 0.5) / (df + 0.5))
            s += idf * (f * (k1 + 1)) / (f + k1 * (1 - b + b * doc["dl"] / ix["avgdl"]))
            colpiti.add(g)
        if s > 0:
            out.append((s, doc["path"], doc["fm"], sorted(colpiti)))
    out.sort(key=lambda r: (-r[0], str(r[1])))
    return out[:n]


# --- Controllo (lint minimo) ----------------------------------------------------------------

WIKILINK = re.compile(r"\[\[([^\]]+)\]\]")
LINK_MD = re.compile(r"\]\(([^)\s]+\.md)(?:#[^)]*)?\)")
RECINTO = re.compile(r"^\s*(```|~~~)")
CODICE = re.compile(r"`[^`]*`")
BARRATO = re.compile(r"~~.*?~~")


def righe_utili(testo: str):
    """(numero, riga) fuori dai blocchi di codice, senza `codice` e ~~barrato~~."""
    dentro = False
    for n, r in enumerate(testo.splitlines(), 1):
        if RECINTO.match(r):
            dentro = not dentro
            continue
        if not dentro:
            yield n, BARRATO.sub("", CODICE.sub("", r))


def bersaglio(interno: str):
    """[[cartella/nome|testo#ancora]] -> nome in minuscolo, None se non sembra un nome."""
    t = interno.replace("\\|", "|").split("|", 1)[0].split("#", 1)[0].strip()
    t = t.split("/")[-1].strip().lower()
    if t.endswith(".md"):
        t = t[:-3]
    if not t or re.search(r"\s", t) or not re.search(r"[a-z0-9]", t):
        return None
    return t


def controlla(dirs=None) -> dict:
    dirs = cartelle() if dirs is None else dirs
    errori, avvisi, da_scrivere = [], [], []
    elenco = file_note(dirs)
    testi = {p: leggi(p) for _d, p in elenco}
    nomi = set()
    for _d, p in elenco:
        nomi.add(p.stem.lower())
        fm, _ = frontmatter(testi[p])
        if isinstance(fm, dict) and campo(fm, "name"):
            nomi.add(str(campo(fm, "name")).lower())

    for _d, p in elenco:
        testo = testi[p]
        fm, _ = frontmatter(testo)
        dove = breve(p)
        if fm is None:
            errori.append({"file": dove, "motivo": "senza frontmatter: il richiamo non la vede"})
            continue
        for k in ("name", "description"):
            if not campo(fm, k):
                errori.append({"file": dove, "motivo": f"manca «{k}» nel frontmatter"})
        t = campo(fm, "type")
        if t and str(t) not in TIPI:
            avvisi.append({"file": dove, "motivo": f"type «{t}» fuori dai quattro di Claude Code ({', '.join(TIPI)})"})
        m = FM.match(testo)
        for r in (m.group(1).splitlines() if m else []):
            k = CHIAVE.match(r)
            if not k or r[:1] in (" ", "\t"):
                continue
            valore = k.group(2).strip()
            if not valore or valore[0] in "\"'[{>|":
                continue
            if ": " in valore:
                errori.append({"file": dove, "motivo": f"il valore di «{k.group(1)}» contiene «: » senza virgolette: "
                                                       "il frontmatter non si legge come YAML"})
            elif " #" in valore:
                avvisi.append({"file": dove, "motivo": f"il valore di «{k.group(1)}» contiene « #»: in YAML il resto "
                                                       "della riga diventa un commento e si perde"})
        for n, r in righe_utili(testo):
            for w in WIKILINK.finditer(r):
                b = bersaglio(w.group(1))
                if b and b not in nomi:
                    da_scrivere.append({"file": dove, "riga": n, "link": b})
            for l in LINK_MD.finditer(r):
                dest = l.group(1)
                if "://" in dest:
                    continue
                if not (p.parent / dest).exists():
                    errori.append({"file": dove, "riga": n, "motivo": f"link rotto: {dest} non esiste"})

    for d in dirs:
        indice = d / INDICE
        if not indice.is_file():
            continue
        testo = leggi(indice)
        citati = set()
        for n, r in righe_utili(testo):
            for l in LINK_MD.finditer(r):
                dest = l.group(1)
                if "://" in dest:
                    continue
                citati.add(os.path.normpath(str(d / dest)))
                if not (d / dest).exists():
                    errori.append({"file": breve(indice), "riga": n,
                                   "motivo": f"l'indice punta a {dest}, che non esiste"})
        for dd, p in elenco:
            if dd == d and p.parent == d and os.path.normpath(str(p)) not in citati:
                avvisi.append({"file": breve(p), "motivo": f"fuori da {INDICE}: Claude Code non la vede all'avvio"})

    return {"note": len(elenco), "cartelle": len(dirs), "errori": errori, "avvisi": avvisi,
            "da_scrivere": da_scrivere}


# --- Comandi ---------------------------------------------------------------------------------

def stato() -> int:
    env = da_ambiente()
    acc = accesa()
    perche = " (lo decide ARTURO_MEMORIA nell'ambiente)" if env is not None else ""
    print(f"Memoria: {'accesa' if acc else 'spenta'}{perche}.")
    native = cartelle_native()
    mie = cartelle_mie()
    print(f"Note di Claude Code: {len(file_note(native))} in {len(native)} cartelle ({breve(radice() / 'projects')}/*/memory).")
    if mie:
        print("Cartelle tue:")
        for d in mie:
            print(f"  - {breve(d)} ({len(file_note([d]))} note)")
    print("Tutto resta su questo computer. Niente della memoria entra nella telemetria.")
    print("Accendi con «arturo memoria accendi», spegni con «arturo memoria spegni».")
    return 0


def interruttore(acceso: bool) -> int:
    dati = leggi_impostazioni()
    dati["accesa"] = acceso
    scrivi_impostazioni(dati)
    if acceso:
        print("Memoria accesa: dal prossimo messaggio Claude riceve le note che parlano di quello che chiedi.")
    else:
        print("Memoria spenta: gli hook della memoria non fanno più niente. Le note restano dove sono.")
    env = da_ambiente()
    if env is not None and env != acceso:
        print(f"Attenzione: ARTURO_MEMORIA={'1' if env else '0'} nell'ambiente vince su questa scelta.")
    return 0


def cartella(azione: str, percorso: str) -> int:
    p = Path(os.path.expanduser(percorso)).resolve()
    dati = leggi_impostazioni()
    voci = [str(v) for v in (dati.get("cartelle") or []) if isinstance(v, str)]
    scritta = breve(p)
    presenti = {str(Path(os.path.expanduser(v)).resolve()) for v in voci}
    if azione == "aggiungi":
        if not p.is_dir():
            print(f"Errore: {percorso} non è una cartella.", file=sys.stderr)
            return 2
        if str(p) in presenti:
            print(f"{scritta} c'è già.")
            return 0
        voci.append(scritta)
        print(f"Aggiunta {scritta}: {len(file_note([p]))} note.")
    else:
        resto = [v for v in voci if str(Path(os.path.expanduser(v)).resolve()) != str(p)]
        if len(resto) == len(voci):
            print(f"{scritta} non era fra le tue cartelle.")
            return 0
        voci = resto
        print(f"Tolta {scritta}. I file restano dove sono.")
    dati["cartelle"] = voci
    scrivi_impostazioni(dati)
    return 0


def comando_cerca(argv: list) -> int:
    ap = argparse.ArgumentParser(prog="arturo memoria cerca", add_help=False)
    ap.add_argument("testo", nargs="+")
    ap.add_argument("-n", type=int, default=8)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--solo-frontmatter", action="store_true", help=argparse.SUPPRESS)
    try:
        a = ap.parse_args(argv)
    except SystemExit:
        print('Uso: arturo memoria cerca "testo" [-n N] [--json]', file=sys.stderr)
        return 2
    testo = " ".join(a.testo)
    if len(set(parole(testo))) < 2:
        print("Scrivi almeno due parole che dicono di cosa parla la nota.", file=sys.stderr)
        return 2
    risultati = cerca(testo, n=a.n, solo_frontmatter=a.solo_frontmatter)
    if a.json:
        print(json.dumps([{"punti": round(s, 3), "nome": str(campo(fm, "name") or p.stem), "file": breve(p),
                           "tipo": tipo(fm), "parole": colpiti, "description": str(campo(fm, "description") or "")}
                          for s, p, fm, colpiti in risultati], ensure_ascii=False, indent=1))
        return 0
    if not risultati:
        print("Nessuna nota.")
        return 0
    for s, p, fm, colpiti in risultati:
        desc = str(campo(fm, "description") or "")[:100]
        print(f"  - {campo(fm, 'name') or p.stem} [{tipo(fm)}] · {s:.1f} · {','.join(colpiti)} — {desc}")
        print(f"    {breve(p)}")
    return 0


def comando_controlla(argv: list) -> int:
    esito = controlla()
    if "--json" in argv:
        print(json.dumps(esito, ensure_ascii=False, indent=1))
        return 1 if esito["errori"] else 0
    print(f"Note controllate: {esito['note']} in {esito['cartelle']} cartelle.")
    for titolo, voci in (("ERRORI", esito["errori"]), ("AVVISI", esito["avvisi"])):
        if voci:
            print(f"\n{titolo} ({len(voci)}):")
            for v in voci:
                riga = f":{v['riga']}" if "riga" in v else ""
                print(f"  - {v['file']}{riga}: {v['motivo']}")
    if esito["da_scrivere"]:
        print(f"\nDA SCRIVERE ({len(esito['da_scrivere'])}): link [[nome]] senza nota. Per Claude Code va bene: "
              "segnano una nota da scrivere più avanti.")
        for v in esito["da_scrivere"]:
            print(f"  - [[{v['link']}]] in {v['file']}:{v['riga']}")
    n = len(esito["errori"])
    print("\nEsito: " + ("tutto a posto." if not n else f"{n} errori da correggere."))
    return 1 if n else 0


def main(argv: list) -> int:
    if not argv or argv[0] == "stato":
        return stato()
    if argv[0] in ("-h", "--help", "aiuto", "help"):
        print(AIUTO)
        return 0
    if argv == ["accendi"]:
        return interruttore(True)
    if argv == ["spegni"]:
        return interruttore(False)
    if argv[0] == "cerca":
        return comando_cerca(argv[1:])
    if argv[0] == "controlla":
        return comando_controlla(argv[1:])
    if len(argv) == 3 and argv[0] == "cartella" and argv[1] in ("aggiungi", "togli"):
        return cartella(argv[1], argv[2])
    print(f"Errore: comando sconosciuto: «{' '.join(argv)}»\n\n{AIUTO}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    for flusso in (sys.stdout, sys.stderr):  # su Windows la pipe è in cp1252, Claude legge UTF-8
        try:
            flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    raise SystemExit(main(sys.argv[1:]))
