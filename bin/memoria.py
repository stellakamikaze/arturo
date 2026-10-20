"""arturo memoria: la memoria facoltativa di Arturo. È spenta finché non la accendi.

Arturo usa Melchior, la stessa memoria della config di chi lo mantiene: lo stesso codice, in
hooks/melchior_match.py e negli hook qui sotto. Cosa fa quando è accesa:
- a ogni tuo messaggio l'hook memory-retrieve.py cerca le note che parlano della stessa cosa e
  ne dà a Claude il percorso. Claude apre una nota solo se gli serve;
- all'avvio memory-autoload.py indica la scheda del progetto (progetto-<cartella>.md), se c'è;
- i subagenti sanno che la memoria esiste e come cercarla (subagent-memory-context.py);
- melchior-postwrite.py tiene in ordine solo le note di ~/.claude/data/memory/ (date e cartelle).
Sempre acceso, anche a memoria spenta: ogni scrittura in una nota o in un handoff passa da
memory-write-scanner.py, e se il testo contiene un segreto o un'istruzione nascosta Claude riceve
un avviso.

Le note sono quelle che Claude Code scrive da solo (~/.claude/projects/*/memory/*.md, frontmatter
con name, description e type), quelle di ~/.claude/data/memory/, più le cartelle che aggiungi tu.
Nessuna nota viene copiata o spostata fuori dalla sua cartella. Nessun server: tutto resta su
questo computer, e niente della memoria entra nella telemetria.

  stato                          accesa o spenta, dove cerca, quante note (anche senza comando)
  accendi | spegni               accende o spegne gli hook della memoria
  cerca "testo" [-n N] [--json]  le note più vicine al testo, anche a memoria spenta
  controlla [--json]             frontmatter mancanti o illeggibili, link rotti
  cartella aggiungi DIR          aggiunge una tua cartella di note
  cartella togli DIR             la toglie (i file restano dove sono)

L'interruttore sta in ~/.claude/data/memoria/impostazioni.json, fuori da git. La variabile
ARTURO_MEMORIA=1 o ARTURO_MEMORIA=0 (nell'ambiente o in "env" di settings.json) vince sul file.
`cerca` è scripts/melchior_recall.py (BM25). Solo libreria standard, Python 3.8 o successivo.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

QUI = Path(__file__).resolve().parent
sys.path.insert(0, str(QUI.parent / "scripts"))
sys.path.insert(0, str(QUI.parent / "hooks"))
import melchior_match as mm  # noqa: E402
import melchior_recall as mr  # noqa: E402

AIUTO = __doc__.split("\n\n")[3] if __doc__ else ""

TIPI = ("user", "feedback", "project", "reference")
INDICE = "MEMORY.md"
FM = mm.FRONTMATTER_RE
CHIAVE = mm.CHIAVE_RE
frontmatter = mm.frontmatter
campo = mm.campo
breve = mm.breve
leggi = mm.leggi


# --- Interruttore e cartelle ---------------------------------------------------------------

def radice() -> Path:
    return mm.CLAUDE_DIR


def file_impostazioni() -> Path:
    return mm.IMPOSTAZIONI


def leggi_impostazioni() -> dict:
    return mm.leggi_impostazioni()


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
    return mm.memoria_accesa()


def cartelle_native() -> list:
    return mm.cartelle_progetti()


def cartelle_mie() -> list:
    return mm.cartelle_aggiunte()


def cartelle() -> list:
    return mm.radici()


tipo = mm.tipo


def file_note(dirs=None) -> list:
    """(cartella, percorso) delle note, senza indici, file e cartelle che iniziano con _ o punto,
    doppioni per percorso reale. Lo stesso elenco del richiamo (melchior_match.elenco_note)."""
    return [(d, p) for d, p, _chiave, _m, _s in mm.elenco_note(dirs)]


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
    if mm.MEMORY_DIR.is_dir():
        print(f"Note curate: {len(file_note([mm.MEMORY_DIR]))} in {breve(mm.MEMORY_DIR)}.")
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
    if len(set(mr.tokenize(testo))) < 2:
        print("Scrivi almeno due parole che dicono di cosa parla la nota.", file=sys.stderr)
        return 2
    # Il recall profondo di Melchior (scripts/melchior_recall.py) su tutte le radici.
    # --solo-frontmatter è la sua controprova: serve solo al banco.
    risultati = mr.build(controprova=a.solo_frontmatter).rank(testo, n=a.n)
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
