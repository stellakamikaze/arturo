#!/usr/bin/env python3
"""Nucleo condiviso della memoria (Melchior): dove stanno le note, come si leggono, come si
pesano, e se la memoria è accesa.

Importato da:
  - memory-retrieve.py          (UserPromptSubmit) → richiamo sul testo del messaggio e sul corpo
  - memory-autoload.py          (SessionStart)     → scheda progetto per nome della cartella
  - memory-write-scanner.py     (PostToolUse)      → raggiungibilità di una nota appena scritta
  - melchior-postwrite.py       (PostToolUse)      → interruttore
  - subagent-memory-context.py  (SubagentStart)    → interruttore
  - scripts/melchior_recall.py  (a mano)           → recall profondo BM25

Lo stesso file vive nella config di chi mantiene Arturo e in Arturo, identico byte per byte
(tests/test_melchior_uguale_arturo.py nella config). Ciò che è di una persona sta fuori dal
codice, in file locali ignorati da git: hooks/melchior-stopword.local (parole senza segnale, una
per riga, # per i commenti).

Dove stanno le note (radici), in quest'ordine:
  1. ~/.claude/data/memory/        la memoria curata
  2. ~/.claude/projects/*/memory/  le note che Claude Code scrive da solo
  3. le cartelle aggiunte, chiave "cartelle" di ~/.claude/data/memoria/impostazioni.json
Una cartella raggiunta due volte (un link simbolico verso un'altra radice) conta una volta sola:
il confronto è sul percorso reale. Le note si distinguono per percorso, non per nome: due progetti
possono avere lo stesso feedback_x.md. Si saltano MEMORY.md, index.md, i file e le cartelle che
cominciano con _ o con un punto (_archive/, _reports/), le cartelle che sono link simbolici.

Interruttore (memoria_accesa): ARTURO_MEMORIA=1 o 0 nell'ambiente, poi "accesa" in
data/memoria/impostazioni.json, poi il default. Il default è accesa se accanto alla cartella degli
hook non c'è bin/arturo, spenta se c'è: in Arturo la memoria si accende con «arturo memoria accendi».

Punteggio del richiamo:
  1. tokenize e path_tokens spezzano su `-`, `_` e spazi: `nome-progetto` diventa {nome, progetto}.
  2. i `triggers` si confrontano parola per parola, non come stringhe intere: un trigger di più
     parole («deploy notturno») conta per ciascuna.
  3. score() guarda anche il CORPO, con peso basso: la conoscenza che vive nel corpo si ritrova.

Il parser del frontmatter legge chiavi di primo livello (anche col trattino), liste a trattini e
fra parentesi quadre, blocchi > e |, una mappa annidata di un livello (Claude Code scrive
`metadata:` con `type:` dentro) e `triggers: a, b` scritto come stringa.

Solo libreria standard, Python 3.8 o successivo. Python aggiunge la cartella dello script a
sys.path[0] quando un hook gira come `python3 ~/.claude/hooks/x.py`, quindi `import melchior_match`
funziona da qualunque hook nella stessa cartella.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

QUI = Path(__file__).resolve().parent
CLAUDE_DIR = Path.home() / ".claude"
MEMORY_DIR = CLAUDE_DIR / "data" / "memory"
PROJECTS_DIR = CLAUDE_DIR / "projects"
IMPOSTAZIONI = CLAUDE_DIR / "data" / "memoria" / "impostazioni.json"
NOTES_CACHE = CLAUDE_DIR / "cache" / "melchior-notes.json"  # locale, fuori da git
EXCLUDE = {"MEMORY.md", "index.md"}
MAX_BYTE = 256 * 1024  # una nota più grande si legge solo fino a qui

# Log degli accessi: un file per macchina dal 19/10/2026. Il file unico
# .melchior-access.log era scritto da tre macchine e andava in conflitto a ogni
# sync (674 commit). Il nome della cartella contiene «melchior-access.log» apposta:
# session-start.sh e config-sync-pull.sh escludono dal conteggio dei file sporchi
# ogni path che lo contiene. Il vecchio file resta in sola lettura (storico).
# Si registrano solo le note di MEMORY_DIR, per nome: chi legge il log le cerca lì.
ACCESS_LOG_DIR = MEMORY_DIR / ".melchior-access.log.d"
LEGACY_ACCESS_LOG = MEMORY_DIR / ".melchior-access.log"
_NOME_NOTA = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*\.md$")


# --- Interruttore e radici -----------------------------------------------------------------

def leggi_impostazioni():
    """Il contenuto di data/memoria/impostazioni.json, {} se manca o non si legge."""
    try:
        dati = json.loads(IMPOSTAZIONI.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return dati if isinstance(dati, dict) else {}


def memoria_accesa():
    """ARTURO_MEMORIA (1 o 0) vince, poi "accesa" nelle impostazioni, poi il default:
    accesa senza bin/arturo accanto agli hook, spenta con bin/arturo (Arturo)."""
    valore = os.environ.get("ARTURO_MEMORIA", "").strip()
    if valore in ("1", "0"):
        return valore == "1"
    scelta = leggi_impostazioni().get("accesa")
    if isinstance(scelta, bool):
        return scelta
    return not (QUI.parent / "bin" / "arturo").exists()


def cartelle_progetti():
    """Le cartelle memory/ dei progetti di Claude Code, in ordine."""
    try:
        return sorted(d for d in PROJECTS_DIR.glob("*/memory") if d.is_dir())
    except OSError:
        return []


def cartelle_aggiunte():
    """Le cartelle elencate in "cartelle" delle impostazioni che esistono."""
    voci = leggi_impostazioni().get("cartelle") or []
    out = []
    for v in voci if isinstance(voci, list) else []:
        p = Path(os.path.expanduser(str(v)))
        try:
            if p.is_dir():
                out.append(p)
        except OSError:
            continue
    return out


def radici():
    """MEMORY_DIR, le memory/ dei progetti e le cartelle aggiunte, senza doppioni per
    percorso reale. Nella config due projects/*/memory sono link a data/memory: contano una volta."""
    out, visti = [], set()
    for d in [MEMORY_DIR] + cartelle_progetti() + cartelle_aggiunte():
        try:
            if not d.is_dir():
                continue
            vero = os.path.realpath(str(d))
        except OSError:
            continue
        if vero in visti:
            continue
        visti.add(vero)
        out.append(d)
    return out


def breve(p):
    """Il percorso con ~ al posto della home, a barre dritte: su Windows Claude lo usa in Git Bash."""
    s = str(p)
    casa = str(Path.home())
    if s == casa or s.startswith(casa + os.sep):
        return "~" + s[len(casa):].replace(os.sep, "/")
    return s.replace(os.sep, "/")


def in_memory_dir(p):
    """True se il percorso (come scritto) sta sotto MEMORY_DIR."""
    s, base = os.path.normpath(str(p)), os.path.normpath(str(MEMORY_DIR))
    return s.startswith(base + os.sep)


# --- Log degli accessi ---------------------------------------------------------------------

def access_host():
    """Nome corto della macchina, ripulito per un nome di file; "" se ignoto."""
    import platform
    host = (platform.node() or "").split(".")[0]
    host = re.sub(r"[^A-Za-z0-9_-]", "-", host).strip("-")
    return "" if host in ("", "localhost") else host


def access_log_path():
    """File di log della macchina corrente, None se l'host è ignoto."""
    host = access_host()
    return ACCESS_LOG_DIR / f"{host}.log" if host else None


def nome_nota_valido(name):
    """Scarta i nomi nati da un glob o da un'opzione (`*.md`, `--include=*.md`)."""
    return bool(_NOME_NOTA.match(name or "")) and name not in EXCLUDE


def append_access(names, context, ts=None, log_path=None):
    """Appende una riga per nota: ts, nome, contesto, host. Mai righe senza host
    né nomi non validi. Errori ignorati: il log non deve fermare un hook."""
    try:
        from datetime import datetime
        host = access_host()
        log = log_path or access_log_path()
        if not host or log is None:
            return
        righe = [n for n in names if nome_nota_valido(n)]
        if not righe:
            return
        ts = ts or datetime.now().isoformat(timespec="seconds")
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a", encoding="utf-8") as fh:
            for n in righe:
                fh.write(f"{ts}\t{n}\t{context}\t{host}\n")
    except Exception:
        pass


def registra_accessi(paths, context, log_path=None):
    """Log degli accessi per le sole note di MEMORY_DIR: le altre radici non entrano nel log."""
    append_access([Path(p).name for p in paths if in_memory_dir(p)], context, log_path=log_path)


# --- Parole --------------------------------------------------------------------------------

def _parole_locali(path):
    """Parole di un file .local: una per riga, # commento, righe vuote ignorate."""
    try:
        righe = path.read_text(encoding="utf-8").splitlines()
    except (OSError, ValueError):
        return set()
    return {r.strip().lower() for r in righe if r.strip() and not r.strip().startswith("#")}


# Token generici privi di segnale di task. I primi sono componenti di path
# ricorrenti (senza cui, dal container, ogni scheda profilo affollava il top-k);
# gli altri sono filler italiano/inglese che sporcherebbe il match sul prompt.
# Le parole di una persona (il suo nome, le sue cartelle) stanno in melchior-stopword.local.
STOPWORDS = {
    # path noise
    "users", "user", "documents",
    "desktop", "downloads", "home", "mnt", "tmp", "var", "projects", "claude",
    # filler linguistico (solo per il match sul prompt)
    "the", "and", "for", "with", "this", "that", "you", "are", "not", "can",
    "cosa", "come", "fare", "puoi", "dove", "quando", "quale", "questo",
    "questa", "sono", "hai", "del", "della", "che", "per", "una", "con",
    "mi", "il", "la", "le", "un", "in", "di", "da", "su", "se", "ho", "gli",
}
STOPWORDS |= _parole_locali(QUI / "melchior-stopword.local")


def tokenize(text):
    """Estrae parole >2 char, minuscole, meno STOPWORDS. Per il testo prompt."""
    out = set()
    for w in re.findall(r"[\w']+", (text or "").lower()):
        w = w.strip("'")
        if len(w) > 2 and w not in STOPWORDS:
            out.add(w)
    return out


def path_tokens(cwd):
    """Token dal CWD: name + ultime 3 parti, splittati su -/_/spazio, meno STOPWORDS."""
    toks = set()
    for part in [cwd.name, *cwd.parts[-3:]]:
        for t in re.split(r"[-_\s]+", part.lower()):
            if len(t) > 2 and t not in STOPWORDS:
                toks.add(t)
    return toks


# --- Frontmatter ---------------------------------------------------------------------------

FRONTMATTER_RE = re.compile(r"^---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)", re.S)
CHIAVE_RE = re.compile(r"^([A-Za-z_][\w-]*):\s*(.*)$")
_BLOCCO = (">", "|", ">-", "|-", ">+", "|+")


def _scalare(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def _voce(f):
    return f == "-" or f.startswith("- ")


def frontmatter(text):
    """(campi, corpo). campi è None senza frontmatter."""
    m = FRONTMATTER_RE.match(text or "")
    if not m:
        return None, text
    righe = m.group(1).splitlines()
    campi = {}
    i = 0
    while i < len(righe):
        r = righe[i]
        if not r.strip() or r.lstrip().startswith("#") or r[:1] in (" ", "\t"):
            i += 1
            continue
        k = CHIAVE_RE.match(r)
        if not k:
            i += 1
            continue
        chiave, resto = k.group(1), k.group(2).strip()
        j = i + 1
        figli = []
        while j < len(righe) and righe[j].strip() and (righe[j][:1] in (" ", "\t") or _voce(righe[j].lstrip())):
            f = righe[j].strip()
            if not f.startswith("#"):
                figli.append(f)
            j += 1
        if resto in _BLOCCO:
            campi[chiave] = " ".join(figli)
        elif resto == "" and figli and _voce(figli[0]):
            voci = []
            for f in figli:
                if _voce(f):
                    voci.append(f[1:].strip())
                elif voci:  # continuazione su più righe della voce di prima
                    voci[-1] += " " + f
            campi[chiave] = [_scalare(v) for v in voci]
        elif resto == "" and figli:
            mappa = {}
            for f in figli:
                kk = CHIAVE_RE.match(f)
                if kk:
                    mappa[kk.group(1)] = _scalare(kk.group(2))
            campi[chiave] = mappa
        elif resto == "":
            campi[chiave] = []
        elif resto.startswith("["):
            dentro = resto[1:-1] if resto.endswith("]") else resto[1:]
            campi[chiave] = [_scalare(x) for x in dentro.split(",") if x.strip()]
        else:
            if figli and not any(_voce(f) for f in figli):  # scalare su più righe
                resto = resto + " " + " ".join(figli)
            campi[chiave] = _scalare(resto)
        i = j
    return campi, text[m.end():]


def parse_frontmatter_simple(text):
    """Solo i campi del frontmatter (compat). None se assente."""
    return frontmatter(text)[0]


def campo(fm, nome):
    """Un campo di primo livello o, se manca, dentro `metadata:`."""
    if not isinstance(fm, dict):
        return None
    v = fm.get(nome)
    if v in (None, "", []):
        meta = fm.get("metadata")
        if isinstance(meta, dict):
            v = meta.get(nome, v)
    return v


def tipo(fm):
    return str(campo(fm, "entity_type") or campo(fm, "type") or "?")


def _lista(v):
    if isinstance(v, list):
        return v
    return [v] if v else []


# --- Punteggio -----------------------------------------------------------------------------

def _trigger_words(fm):
    """Trigger tokenizzati in parole (fix del match a stringa-intera)."""
    words = set()
    for t in _lista(campo(fm, "triggers")):
        for w in re.findall(r"\w+", str(t).lower()):
            if len(w) > 2:
                words.add(w)
    return words


def score_detail(fm, tokens, body=""):
    """Ritorna (score, set_di_token_distinti_che_hanno_matchato).

    trigger-word +3 · name (substring) +2 · description +1 · answers +1 · body +1
    Il set di token distinti serve a distinguere "1 token che colpisce piu' campi"
    (score alto ma segnale debole, es. `rassegna`) da "piu' token che convergono"
    (segnale forte). memory-retrieve richiede >=2 token distinti.
    """
    if not isinstance(fm, dict):
        return 0, set()
    trig = _trigger_words(fm)
    name = str(campo(fm, "name") or "").lower()
    desc = str(campo(fm, "description") or "").lower()
    answers = " ".join(str(a) for a in _lista(campo(fm, "answers"))).lower()
    body_l = body.lower() if body else ""
    s = 0
    body_hits = 0
    matched = set()
    for tok in tokens:
        hit = 0
        if tok in trig:
            hit += 3
        if tok in name:
            hit += 2
        if tok in desc:
            hit += 1
        if tok in answers:
            hit += 1
        if body_l and tok in body_l:
            body_hits += 1
            if not hit:
                matched.add(tok)
        if hit:
            s += hit
            matched.add(tok)
    # il body pesa al massimo +2 per file: senza cap i file verbosi (10-40KB)
    # accumulano +1 per ogni token del prompt e affollano i candidati
    s += min(body_hits, 2)
    return s, matched


def score(fm, tokens, body=""):
    """Solo lo score numerico (compat)."""
    return score_detail(fm, tokens, body)[0]


# --- Elenco e lettura delle note -----------------------------------------------------------

def _nascosto(nome):
    return nome.startswith(("_", "."))


def _walk_md(root):
    """(path, rel, mtime_ns, size, symlink) di ogni .md sotto root. scandir prende data e
    dimensione dall'elenco della cartella: su Windows non apre i file. Non scende nelle
    cartelle nascoste o con _ davanti, né nelle cartelle che sono link simbolici."""
    stack = [(root, "")]
    while stack:
        d, rel_d = stack.pop()
        try:
            entries = list(os.scandir(d))
        except OSError:
            continue
        for e in entries:
            try:
                if _nascosto(e.name):
                    continue
                rel = f"{rel_d}/{e.name}" if rel_d else e.name
                if e.is_dir(follow_symlinks=False):
                    stack.append((Path(e.path), rel))
                elif e.name.endswith(".md") and e.name not in EXCLUDE and e.is_file():
                    st = e.stat()
                    yield Path(e.path), rel, st.st_mtime_ns, st.st_size, e.is_symlink()
            except OSError:
                continue


def elenco_note(dirs=None):
    """[(radice, path, chiave, mtime_ns, size)] di ogni nota, senza doppioni. La chiave è il
    percorso reale: la radice risolta più il percorso relativo, o il bersaglio di un file che è
    un link simbolico. Così una nota raggiunta da due radici conta una volta sola."""
    out, visti = [], set()
    for radice in (radici() if dirs is None else [Path(d) for d in dirs]):
        try:
            vera = os.path.realpath(str(radice))
        except OSError:
            continue
        for p, rel, mtime, size, link in _walk_md(radice):
            try:
                chiave = os.path.realpath(str(p)) if link else os.path.normpath(os.path.join(vera, rel))
            except OSError:
                continue
            if chiave in visti:
                continue
            visti.add(chiave)
            out.append((radice, p, chiave, mtime, size))
    return out


def leggi(p):
    """Il testo di una nota, al massimo MAX_BYTE caratteri; "" se non si legge."""
    try:
        with open(str(p), "r", encoding="utf-8", errors="replace") as fh:
            return fh.read(MAX_BYTE)
    except OSError:
        return ""


def _note_texts(memory_dir=None):
    """[(path, text)] delle note attive. Senza memory_dir legge tutte le radici e prende il
    testo da una cache locale: si rilegge solo la nota con data o dimensione cambiate.
    Su Windows la prima apertura di un file costa ~30 ms (scansione antivirus):
    730 note lette a freddo facevano 21 s e il hook moriva al timeout di 5 s
    (17/10/2026). Una cartella passata a mano (banchi) si legge sempre da disco."""
    use_cache = memory_dir is None
    old = {}
    if use_cache:
        try:
            old = json.loads(NOTES_CACHE.read_text(encoding="utf-8"))
        except Exception:
            old = {}
        if not isinstance(old, dict):
            old = {}
    new, changed, out = {}, False, []
    for _radice, p, chiave, mtime, size in elenco_note(None if memory_dir is None else [memory_dir]):
        hit = old.get(chiave)
        if isinstance(hit, list) and len(hit) == 3 and hit[0] == mtime and hit[1] == size:
            text = hit[2]
        else:
            text = leggi(p)
            if not text:
                continue
            changed = True
        new[chiave] = [mtime, size, text]
        out.append((p, text))
    if use_cache and (changed or new.keys() != old.keys()):
        try:
            NOTES_CACHE.parent.mkdir(parents=True, exist_ok=True)
            tmp = NOTES_CACHE.with_name(f"{NOTES_CACHE.name}.{os.getpid()}.tmp")
            tmp.write_text(json.dumps(new, ensure_ascii=False), encoding="utf-8")
            os.replace(str(tmp), str(NOTES_CACHE))
        except Exception:
            pass
    return out


def iter_notes(memory_dir=None, want_body=False):
    """Itera (path, fm, body) sulle note attive di tutte le radici, o della sola memory_dir.
    Le note senza frontmatter non contano."""
    for p, text in _note_texts(memory_dir):
        fm, corpo = frontmatter(text)
        if not isinstance(fm, dict):
            continue
        # per il match sul corpo passiamo solo il testo dopo il frontmatter
        yield p, fm, (corpo if want_body else "")


def rank(tokens, memory_dir=None, want_body=False, min_score=1, min_distinct=1):
    """Ritorna [(score, path, fm)] ordinato desc.

    Filtra per score >= min_score E numero di token distinti matchati >= min_distinct.
    min_distinct=2 (retrieve) scarta i match da un solo token che colpisce piu' campi.
    """
    scored = []
    for p, fm, body in iter_notes(memory_dir, want_body=want_body):
        s, matched = score_detail(fm, tokens, body=body)
        if s >= min_score and len(matched) >= min_distinct:
            scored.append((s, p, fm))
    scored.sort(key=lambda x: (-x[0], x[1].name, str(x[1])))
    return scored
