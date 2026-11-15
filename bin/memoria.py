"""arturo memoria: la memoria di Arturo. È accesa di default, e "arturo memoria spegni" la spegne.

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

Le note sono quelle che Claude Code scrive da solo (~/.claude/projects/*/memory/*.md), quelle di
~/.claude/data/memory/, più le cartelle che aggiungi tu. Lo schema è uno, in docs/memoria.md:
name, description e type. Le note stanno su questo computer. Il richiamo ne tiene una copia del
testo in ~/.claude/cache/melchior-notes.json, per leggerle in fretta. Le note che Claude apre
passano ad Anthropic come il resto della conversazione. Niente della memoria entra nella telemetria.

  stato                          accesa o spenta, dove cerca, quante note (anche senza comando)
  accendi | spegni               accende o spegne gli hook della memoria
  cerca "testo" [-n N] [--json]  le note più vicine al testo, anche a memoria spenta
  controlla [--json]             frontmatter mancanti o illeggibili, link rotti
  cartella aggiungi DIR          aggiunge una tua cartella di note
  cartella togli DIR             la toglie (i file restano dove sono)
  scheda SLUG                    la scheda del progetto: cos'è, dove sta, decisioni chiuse, errori
  scheda SLUG --cosa T [--titolo T] [--cartella DIR] [--alias a,b] [--decisione T]... [--errore T]...
                                 la scrive o la aggiorna (/fine); le righe scritte a mano restano
  nota --tipo T --nome N --descrizione D [--testo T]
                                 salva una nota nuova in data/memory/<cartella del tipo>/ (testo
                                 anche da stdin) e la mette fra quelle da annunciare (/fine)
  ricordate [--annuncia] [--json] le note salvate e non ancora annunciate; --annuncia le numera
  togli N | NOME                 archivia la nota N dell'ultimo annuncio (o per nome), senza cancellarla
  igiene [--prova] [--se-dovuta] [--json]
                                 note dormienti (mai proposte da 90 giorni), coppie quasi uguali,
                                 link rotti; --se-dovuta gira una volta a settimana (/fine completo)

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

TIPI = mm.TIPI
INDICE = "MEMORY.md"
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


scrivi_impostazioni = mm.scrivi_impostazioni


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
                errori.append({"file": dove, "motivo": f'manca "{k}" nel frontmatter'})
        t = campo(fm, "type")
        if not t:
            avvisi.append({"file": dove, "motivo": f"manca \"type\" ({', '.join(TIPI)}): il richiamo la trova, "
                                                   "ma una nota nuova non sa in che cartella andare"})
        elif str(t) not in TIPI:
            avvisi.append({"file": dove, "motivo": f"type \"{t}\" fuori dai quattro di Claude Code ({', '.join(TIPI)})"})
        for grave, motivo in mm.problemi_frontmatter(testo):
            (errori if grave else avvisi).append({"file": dove, "motivo": motivo})
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
    if env is not None:
        perche = " (lo decide ARTURO_MEMORIA nell'ambiente)"
    elif not isinstance(leggi_impostazioni().get("accesa"), bool):
        perche = " (di default)"
    else:
        perche = ""
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
    print("Le note stanno su questo computer. Quelle che Claude apre passano ad Anthropic con la conversazione.")
    print("Niente della memoria entra nella telemetria. Cosa ricorda e dove: docs/memoria.md.")
    print('Accendi con "arturo memoria accendi", spegni con "arturo memoria spegni".')
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


# --- La scheda del progetto (M3 del piano della memoria, 14/11/2026) -----------------------
# /fine la scrive, arturo contesto (/inizio) la rilegge. Ha cos'è, dove sta, decisioni chiuse ed errori
# da non ripetere: stato e todo restano negli handoff e in arturo todo.

COSA = "## Cos'è"
SEZIONI = {"decisione": "## Decisioni chiuse", "errore": "## Errori da non ripetere"}
MAX_VOCE = 300
MAX_DESCRIZIONE = 200
_SCANNER = []


def slug_progetto(nome: str) -> str:
    """Lo slug di /inizio, /fine e arturo todo (come bin/contesto.py)."""
    return re.sub(r"^-+|-+$", "", re.sub(r"[^a-z0-9]+", "-", str(nome).lower()))


def una_riga(testo, n: int = MAX_VOCE) -> str:
    testo = " ".join(str(testo or "").split())
    return testo if len(testo) <= n else testo[:n - 1].rstrip() + "…"


def motivi_scanner(testo: str) -> list:
    """I motivi di sospetto di hooks/memory-write-scanner.py: una scrittura da script non passa dall'hook
    di Write, quindi il controllo lo chiama qui. Senza scanner, nessun motivo."""
    if not _SCANNER:
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("memory_write_scanner",
                                                          str(QUI.parent / "hooks" / "memory-write-scanner.py"))
            modulo = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(modulo)
            _SCANNER.append(modulo)
        except Exception:
            _SCANNER.append(None)
    try:
        return list(_SCANNER[0].trova(testo)) if _SCANNER[0] is not None else []
    except Exception:
        return []


def cartella_con_tilde(cartella: str) -> str:
    """La cartella sotto la home diventa ~/...: la scheda vale anche su un computer con un'altra home."""
    if not cartella:
        return ""
    try:
        vera, casa = Path(os.path.expanduser(cartella)).resolve(), Path.home().resolve()
        return "~/" + vera.relative_to(casa).as_posix() if vera != casa else "~"
    except (OSError, ValueError, RuntimeError):
        return cartella


def _valore_fm(v: str) -> str:
    return '"' + v.replace('"', "'") + '"'


def _imposta_fm(righe: list, fine: int, chiave: str, valore: str) -> int:
    """Scrive `chiave: valore` nel frontmatter righe[1:fine]; ritorna il nuovo indice della riga ---."""
    for i in range(1, fine):
        if not righe[i].startswith((" ", "\t")) and righe[i].split(":", 1)[0].strip() == chiave:
            righe[i] = f"{chiave}: {valore}"
            return fine
    righe.insert(fine, f"{chiave}: {valore}")
    return fine + 1


def _alias_di(righe: list, fine: int) -> list:
    for i in range(1, fine):
        if righe[i].startswith("alias:"):
            return [a for a in (x.strip().strip("\"'") for x in righe[i][6:].strip().strip("[]").split(",")) if a]
    return []


def _sezione(righe: list, titolo: str, inizio: int) -> tuple:
    """(indice del titolo, indice dopo l'ultima riga piena della sezione), o (None, None)."""
    for i in range(inizio, len(righe)):
        if righe[i].strip().lower() == titolo.lower():
            j = i + 1
            while j < len(righe) and not righe[j].startswith("## "):
                j += 1
            while j > i + 1 and not righe[j - 1].strip():
                j -= 1
            return i, j
    return None, None


def _norma(voce: str) -> str:
    return " ".join(voce.lstrip("-* ").split()).casefold()


def testo_nuova_scheda(s: str, cosa: str, titolo: str, cartella: str, alias: list) -> str:
    righe = ["---", f"name: progetto-{s}", f"description: {_valore_fm(una_riga(cosa, MAX_DESCRIZIONE))}",
             "type: project"]
    if titolo:
        righe.append(f"titolo: {_valore_fm(titolo)}")
    if alias:
        righe.append(f"alias: [{', '.join(alias)}]")
    if cartella:
        righe.append(f"cartella: {cartella}")
    righe += ["---", f"# {titolo or s}", "", COSA, una_riga(cosa, 1000)]
    return "\n".join(righe) + "\n"


def aggiorna_scheda(testo: str, cosa: str, titolo: str, cartella: str, alias: list, voci: dict) -> tuple:
    """(testo nuovo, {decisione: n, errore: n} voci aggiunte). Tocca solo i campi dati e aggiunge in coda
    alle sezioni le voci che non ci sono già: le righe scritte a mano restano."""
    righe = testo.splitlines()
    fine = None
    if righe and righe[0].strip() == "---":
        fine = next((i for i, r in enumerate(righe[1:], 1) if r.strip() == "---"), None)
    if fine is None:
        raise ValueError("la scheda non ha il frontmatter fra due righe ---")
    if cosa:
        fine = _imposta_fm(righe, fine, "description", _valore_fm(una_riga(cosa, MAX_DESCRIZIONE)))
    if titolo:
        fine = _imposta_fm(righe, fine, "titolo", _valore_fm(titolo))
    if alias:
        uniti = list(dict.fromkeys(_alias_di(righe, fine) + alias))
        fine = _imposta_fm(righe, fine, "alias", f"[{', '.join(uniti)}]")
    if cartella:
        fine = _imposta_fm(righe, fine, "cartella", cartella)
    if cosa:
        i, j = _sezione(righe, COSA, fine + 1)
        if i is None:
            dove = next((k + 1 for k in range(fine + 1, len(righe)) if righe[k].startswith("# ")), fine + 1)
            righe[dove:dove] = ["", COSA, una_riga(cosa, 1000)]
        else:
            righe[i + 1:j] = [una_riga(cosa, 1000)]
    aggiunte = {}
    for chiave, titolo_sez in SEZIONI.items():
        nuove = [una_riga(v) for v in voci.get(chiave, []) if una_riga(v)]
        i, j = _sezione(righe, titolo_sez, fine + 1)
        gia = {_norma(r) for r in righe[i + 1:j]} if i is not None else set()
        nuove = [v for v in dict.fromkeys(nuove) if _norma(v) not in gia]
        aggiunte[chiave] = len(nuove)
        if not nuove:
            continue
        if i is None:
            while righe and not righe[-1].strip():
                righe.pop()
            righe += ["", titolo_sez] + [f"- {v}" for v in nuove]
        else:
            righe[j:j] = [f"- {v}" for v in nuove]
    return "\n".join(righe).rstrip("\n") + "\n", aggiunte


def comando_scheda(argv: list) -> int:
    """arturo memoria scheda <slug> [--cosa T] [--titolo T] [--cartella DIR] [--alias a,b]
    [--decisione T]... [--errore T]...: senza opzioni stampa la scheda."""
    p = argparse.ArgumentParser(prog="arturo memoria scheda", add_help=False)
    p.add_argument("slug")
    p.add_argument("--cosa", default="")
    p.add_argument("--titolo", default="")
    p.add_argument("--cartella", default="")
    p.add_argument("--alias", default="")
    p.add_argument("--decisione", action="append", default=[])
    p.add_argument("--errore", action="append", default=[])
    try:
        a = p.parse_args(argv)
    except SystemExit:
        print('uso: arturo memoria scheda <slug> [--cosa "..."] [--titolo "..."] [--cartella DIR] '
              '[--alias a,b] [--decisione "..."]... [--errore "..."]...', file=sys.stderr)
        return 3
    s = slug_progetto(a.slug)
    if not s:
        print(f'nome di progetto non valido: "{a.slug}"', file=sys.stderr)
        return 3
    esistente = mm.trova_scheda(s)
    cosa, titolo, cartella = una_riga(a.cosa, 1000), una_riga(a.titolo, 60), una_riga(a.cartella, 400)
    cartella = cartella_con_tilde(cartella)
    alias = [x for x in (slug_progetto(v) for v in a.alias.split(",")) if x and x != s]
    voci = {"decisione": a.decisione, "errore": a.errore}
    if not (cosa or titolo or cartella or alias or a.decisione or a.errore):
        if not esistente:
            print(f"nessuna scheda per {s}")
            return 2
        print(f"scheda: {breve(esistente)}")
        print(leggi(esistente).rstrip())
        return 0
    if not mm.memoria_accesa():
        print("memoria spenta: la scheda non si scrive. Per accenderla: arturo memoria accendi")
        return 4
    motivi = motivi_scanner("\n".join([cosa, titolo, cartella] + a.decisione + a.errore))
    if motivi:
        print(f"scheda di {s} non scritta: " + "; ".join(motivi), file=sys.stderr)
        return 5
    if esistente:
        f = esistente
        prima = leggi(f)
        try:
            testo, aggiunte = aggiorna_scheda(prima, cosa, titolo, cartella, alias, voci)
        except ValueError as e:
            print(f"{breve(f)}: {e}", file=sys.stderr)
            return 2
        esito = "aggiornata" if testo != prima else "invariata"
    else:
        if not cosa:
            print(f"la scheda di {s} non c'è ancora: la prima volta serve --cosa \"di cosa si tratta, in una riga\"",
                  file=sys.stderr)
            return 3
        f = mm.MEMORY_DIR / "progetti" / f"progetto-{s}.md"
        testo, aggiunte = aggiorna_scheda(testo_nuova_scheda(s, cosa, titolo, cartella, alias), "", "", "", [], voci)
        esito = "creata"
    if esito != "invariata":
        f.parent.mkdir(parents=True, exist_ok=True)
        tmp = f.with_name(f".{f.name}.tmp")
        tmp.write_text(testo, encoding="utf-8")
        os.replace(str(tmp), str(f))
    print(f"scheda {esito}: {breve(f)} · decisioni nuove {aggiunte['decisione']} · errori nuovi {aggiunte['errore']}")
    return 0


# --- Note salvate e annunciate (M5 del piano della memoria, 15/11/2026) -----------------------
# /fine salva una nota nuova senza chiedere e la annuncia nella chiusura che la persona legge:
# "Ho ricordato: 1. … 2. …". "togli N" la sposta in data/memory/_archive/, non la cancella.
# Il registro sta in data/memoria/ricordate.json, fuori da git come l'interruttore.

NOME_NOTA = re.compile(r"^[a-z0-9][a-z0-9-]{1,79}$")
MAX_TESTO = 20000


def file_registro() -> Path:
    return mm.IMPOSTAZIONI.parent / "ricordate.json"


def leggi_registro() -> dict:
    try:
        dati = json.loads(file_registro().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"voci": [], "annuncio": 0}
    if not isinstance(dati, dict) or not isinstance(dati.get("voci"), list):
        return {"voci": [], "annuncio": 0}
    dati["voci"] = [v for v in dati["voci"] if isinstance(v, dict) and isinstance(v.get("file"), str)]
    if not isinstance(dati.get("annuncio"), int):
        dati["annuncio"] = 0
    return dati


def scrivi_registro(dati: dict) -> None:
    f = file_registro()
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_name(f".{f.name}.tmp")
    tmp.write_text(json.dumps(dati, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(str(tmp), str(f))


def oggi() -> str:
    from datetime import date
    return date.today().isoformat()


def note_curate() -> list:
    """Le note di data/memory, fuori da _archive e dai file che iniziano con _ o punto."""
    return [p for _d, p in file_note([mm.MEMORY_DIR])] if mm.MEMORY_DIR.is_dir() else []


def comando_nota(argv: list) -> int:
    p = argparse.ArgumentParser(prog="arturo memoria nota", add_help=False)
    p.add_argument("--tipo", required=True)
    p.add_argument("--nome", required=True)
    p.add_argument("--descrizione", required=True)
    p.add_argument("--testo", default=None)
    try:
        a = p.parse_args(argv)
    except SystemExit:
        print('uso: arturo memoria nota --tipo user|feedback|project|reference --nome nome-della-nota '
              '--descrizione "una riga" [--testo "..."] (senza --testo lo legge da stdin)', file=sys.stderr)
        return 3
    if a.tipo not in TIPI:
        print(f'tipo "{a.tipo}" sconosciuto: usa uno di {", ".join(TIPI)}', file=sys.stderr)
        return 3
    nome = a.nome.strip()
    if not NOME_NOTA.match(nome):
        print(f'nome "{nome}" non valido: lettere minuscole, cifre e trattini, da 2 a 80', file=sys.stderr)
        return 3
    testo = a.testo if a.testo is not None else ("" if sys.stdin is None or sys.stdin.isatty() else sys.stdin.read())
    testo = (testo or "").strip()
    descrizione = una_riga(a.descrizione, MAX_DESCRIZIONE)
    if not descrizione or not testo:
        print("servono una descrizione e un testo: una nota vuota non si salva", file=sys.stderr)
        return 3
    if len(testo) > MAX_TESTO:
        print(f"testo di {len(testo)} caratteri: una nota sta sotto i {MAX_TESTO}. Tieni il fatto, non il documento.",
              file=sys.stderr)
        return 3
    if not mm.memoria_accesa():
        print("memoria spenta: la nota non si salva. Per accenderla: arturo memoria accendi")
        return 4
    motivi = motivi_scanner("\n".join([nome, descrizione, testo]))
    if motivi:
        print(f"nota {nome} non salvata: " + "; ".join(motivi), file=sys.stderr)
        return 5
    gia = [q for q in note_curate() if q.stem == nome]
    if gia:
        print(f"la nota {nome} c'è già: {breve(gia[0])}. Aggiorna quella invece di farne una nuova.", file=sys.stderr)
        return 6
    f = mm.MEMORY_DIR / mm.CARTELLA_TIPO[a.tipo] / f"{nome}.md"
    corpo = "\n".join(["---", f"name: {nome}", f"description: {_valore_fm(descrizione)}", f"type: {a.tipo}",
                       f"created: {oggi()}", "---", testo]) + "\n"
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_name(f".{f.name}.tmp")
    tmp.write_text(corpo, encoding="utf-8")
    os.replace(str(tmp), str(f))
    dati = leggi_registro()
    dati["voci"].append({"nome": nome, "file": f.relative_to(mm.MEMORY_DIR).as_posix(), "descrizione": descrizione,
                         "giorno": oggi(), "annuncio": None, "tolta": False})
    scrivi_registro(dati)
    print(f"nota salvata: {breve(f)} · la annuncia la chiusura di /fine")
    return 0


def _ultimo_annuncio(dati: dict) -> list:
    return [v for v in dati["voci"] if dati["annuncio"] and v.get("annuncio") == dati["annuncio"]]


def comando_ricordate(argv: list) -> int:
    dati = leggi_registro()
    attesa = [v for v in dati["voci"] if v.get("annuncio") is None and not v.get("tolta")
              and (mm.MEMORY_DIR / v["file"]).is_file()]
    if "--json" in argv:
        print(json.dumps({"da_annunciare": attesa, "ultimo_annuncio": _ultimo_annuncio(dati)},
                         ensure_ascii=False, indent=1))
        return 0 if attesa else 3
    if not attesa:
        return 3
    if "--annuncia" in argv:
        dati["annuncio"] += 1
        for v in attesa:
            v["annuncio"] = dati["annuncio"]
        scrivi_registro(dati)
    print("Ho ricordato:")
    for n, v in enumerate(attesa, 1):
        print(f"{n}. {v.get('descrizione') or v['nome']} ({breve(mm.MEMORY_DIR / v['file'])})")
    if "--annuncia" in argv:
        print("Se una non ti serve, scrivimi togli e il numero: la sposto nell'archivio, non la cancello.")
    return 0


def comando_togli(argv: list) -> int:
    if len(argv) != 1:
        print("uso: arturo memoria togli N | nome-della-nota", file=sys.stderr)
        return 3
    chiave = argv[0].strip()
    dati = leggi_registro()
    voce, f = None, None
    if chiave.isdigit():
        ultime = _ultimo_annuncio(dati)
        n = int(chiave)
        if not 1 <= n <= len(ultime):
            print(f"nell'ultimo annuncio non c'è la nota {n}: le note annunciate sono {len(ultime)}", file=sys.stderr)
            return 2
        voce = ultime[n - 1]
        f = mm.MEMORY_DIR / voce["file"]
    else:
        trovate = [q for q in note_curate() if q.stem == chiave]
        if not trovate:
            print(f"nessuna nota {chiave} in {breve(mm.MEMORY_DIR)}", file=sys.stderr)
            return 2
        f = trovate[0]
        rel = f.relative_to(mm.MEMORY_DIR).as_posix()
        voce = next((v for v in reversed(dati["voci"]) if v["file"] == rel), None)
    if voce is not None and voce.get("tolta"):
        print(f"la nota {voce['nome']} è già nell'archivio")
        return 0
    if not f.is_file():
        print(f"la nota {breve(f)} non c'è più", file=sys.stderr)
        return 2
    dest = mm.MEMORY_DIR / "_archive" / f.relative_to(mm.MEMORY_DIR)
    if dest.exists():
        dest = dest.with_name(f"{dest.stem}-{oggi()}{dest.suffix}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    os.replace(str(f), str(dest))
    if voce is not None:
        voce["tolta"] = True
        scrivi_registro(dati)
    print(f"tolta: {f.stem}, spostata in {breve(dest)}. Non è cancellata: per riaverla rimettila in {breve(f.parent)}.")
    return 0


# --- Igiene (M5): il primo lettore del log degli accessi in Arturo ---------------------------
# Senza modello e senza cancellare: segna le note dormienti nel frontmatter, segnala le coppie
# quasi uguali e i link rotti. Una nota dormiente torna sveglia appena il richiamo la propone.

GIORNI_DORMIENTE = 90
GIORNI_IGIENE = 7
SOGLIA_COPPIA = 0.7
MAX_COPPIE = 20


def file_ultima_igiene() -> Path:
    return mm.IMPOSTAZIONI.parent / "ultima-igiene"


def accessi(log_dir: Path) -> tuple:
    """({nome della nota: ultima proposta}, prima riga del log): i datetime sono ingenui, ora locale."""
    from datetime import datetime
    ultime, prima = {}, None
    try:
        logs = sorted(log_dir.glob("*.log")) if log_dir.is_dir() else []
    except OSError:
        logs = []
    for log in logs:
        try:
            righe = log.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for r in righe:
            parti = r.split("\t")
            if len(parti) < 2:
                continue
            try:
                ts = datetime.fromisoformat(parti[0].strip()[:19])
            except ValueError:
                continue
            nome = parti[1].strip()
            if nome not in ultime or ts > ultime[nome]:
                ultime[nome] = ts
            if prima is None or ts < prima:
                prima = ts
    return ultime, prima


def _chiave_fm(testo: str, chiave: str):
    """Il valore di `chiave:` al primo livello del frontmatter, None se manca."""
    righe = testo.splitlines()
    if not righe or righe[0].strip() != "---":
        return None
    for r in righe[1:]:
        if r.strip() == "---":
            return None
        if not r.startswith((" ", "\t")) and r.split(":", 1)[0].strip() == chiave and ":" in r:
            return r.split(":", 1)[1].strip()
    return None


def _cambia_fm(testo: str, chiave: str, valore) -> str:
    """Scrive (valore stringa) o toglie (None) `chiave:` nel frontmatter; il resto resta com'è."""
    righe = testo.split("\n")
    fine = next((i for i, r in enumerate(righe[1:], 1) if r.strip() == "---"), None)
    if not righe or righe[0].strip() != "---" or fine is None:
        return testo
    righe_fm = [i for i in range(1, fine) if not righe[i].startswith((" ", "\t"))
                and righe[i].split(":", 1)[0].strip() == chiave]
    if valore is None:
        for i in reversed(righe_fm):
            del righe[i]
    elif righe_fm:
        righe[righe_fm[0]] = f"{chiave}: {valore}"
    else:
        righe.insert(fine, f"{chiave}: {valore}")
    return "\n".join(righe)


def _parole_titolo(p: Path, fm) -> set:
    nome = str(campo(fm, "name") or p.stem).replace("-", " ").replace("_", " ")
    return set(mr.tokenize(nome + " " + str(campo(fm, "description") or "")))


def igiene(prova: bool = False) -> dict:
    from datetime import datetime, timedelta
    ora = datetime.now()
    soglia = ora - timedelta(days=GIORNI_DORMIENTE)
    ultime, prima = accessi(mm.ACCESS_LOG_DIR)
    copertura = (ora - prima).days if prima else 0
    dormienti, sveglie = [], []
    if copertura >= GIORNI_DORMIENTE:
        for p in note_curate():
            testo = leggi(p)
            segno = _chiave_fm(testo, "dormiente")
            proposta = ultime.get(p.name)
            recente = proposta is not None and proposta >= soglia
            if segno is not None and recente:
                sveglie.append(breve(p))
                nuovo = _cambia_fm(testo, "dormiente", None)
            elif segno is None and not recente:
                try:
                    vecchia = datetime.fromtimestamp(p.stat().st_mtime) < soglia
                except OSError:
                    continue
                if not vecchia:
                    continue
                dormienti.append(breve(p))
                nuovo = _cambia_fm(testo, "dormiente", ora.date().isoformat())
            else:
                continue
            if not prova and nuovo != testo:
                tmp = p.with_name(f".{p.name}.tmp")
                tmp.write_text(nuovo, encoding="utf-8")
                os.replace(str(tmp), str(p))

    voci = []
    for _d, p in file_note(cartelle()):
        fm, _ = frontmatter(leggi(p))
        parole = _parole_titolo(p, fm if isinstance(fm, dict) else {})
        if len(parole) >= 3:
            voci.append((p, parole))
    coppie = []
    for i in range(len(voci)):
        a, pa = voci[i]
        for b, pb in voci[i + 1:]:
            if a.parent == b.parent and a.stem == b.stem:
                continue
            sim = len(pa & pb) / len(pa | pb)
            if sim >= SOGLIA_COPPIA:
                coppie.append((round(sim, 2), breve(a), breve(b)))
    coppie.sort(key=lambda c: (-c[0], c[1], c[2]))

    esito = controlla()
    rotti = [v for v in esito["errori"] if "riga" in v]
    if not prova:
        f = file_ultima_igiene()
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(ora.date().isoformat() + "\n", encoding="utf-8")
    return {"copertura_giorni": copertura, "dormienti": dormienti, "sveglie": sveglie,
            "coppie": coppie[:MAX_COPPIE], "coppie_totali": len(coppie), "link_rotti": rotti, "prova": prova}


def igiene_dovuta() -> bool:
    from datetime import date
    try:
        ultima = date.fromisoformat(file_ultima_igiene().read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return True
    return (date.today() - ultima).days >= GIORNI_IGIENE


def comando_igiene(argv: list) -> int:
    noti = {"--prova", "--se-dovuta", "--json"}
    if any(a not in noti for a in argv):
        print("uso: arturo memoria igiene [--prova] [--se-dovuta] [--json]", file=sys.stderr)
        return 3
    if not mm.memoria_accesa():
        print("memoria spenta: niente igiene. Per accenderla: arturo memoria accendi")
        return 4
    if "--se-dovuta" in argv and not igiene_dovuta():
        return 3
    e = igiene(prova="--prova" in argv)
    if "--json" in argv:
        print(json.dumps(e, ensure_ascii=False, indent=1))
        return 0
    verbo = "da segnare" if e["prova"] else "segnate"
    print("IGIENE DELLA MEMORIA" + (" (prova: non scrive niente)" if e["prova"] else ""))
    if e["copertura_giorni"] < GIORNI_DORMIENTE:
        print(f"- Note dormienti: il registro delle proposte copre {e['copertura_giorni']} giorni, ne servono "
              f"{GIORNI_DORMIENTE}. Per ora nessuna.")
    else:
        print(f"- Note dormienti {verbo}: {len(e['dormienti'])}. Restano nel richiamo, e tornano sveglie "
              f"appena servono.")
        for d in e["dormienti"][:10]:
            print(f"    {d}")
        if len(e["dormienti"]) > 10:
            print(f"    e altre {len(e['dormienti']) - 10}")
        if e["sveglie"]:
            print(f"- Tornate sveglie: {len(e['sveglie'])}.")
    print(f"- Coppie quasi uguali: {e['coppie_totali']}." + (" Valuta se unirle:" if e["coppie"] else ""))
    for sim, a, b in e["coppie"]:
        print(f"    {a} ~ {b}")
    print(f"- Link rotti: {len(e['link_rotti'])}.")
    for v in e["link_rotti"][:10]:
        print(f"    {v['file']}:{v['riga']}: {v['motivo']}")
    return 0


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
    if argv[0] == "scheda" and len(argv) > 1:
        return comando_scheda(argv[1:])
    if argv[0] == "nota":
        return comando_nota(argv[1:])
    if argv[0] == "ricordate":
        return comando_ricordate(argv[1:])
    if argv[0] == "togli":
        return comando_togli(argv[1:])
    if argv[0] == "igiene":
        return comando_igiene(argv[1:])
    if len(argv) == 3 and argv[0] == "cartella" and argv[1] in ("aggiungi", "togli"):
        return cartella(argv[1], argv[2])
    print(f"Errore: comando sconosciuto: \"{' '.join(argv)}\"\n\n{AIUTO}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    for flusso in (sys.stdout, sys.stderr):  # su Windows la pipe è in cp1252, Claude legge UTF-8
        try:
            flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    raise SystemExit(main(sys.argv[1:]))
