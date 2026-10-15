#!/usr/bin/env python3
"""inventario-sessione.py: elenca i file prodotti da una sessione Claude Code e propone dove vanno.

Serve a /fine (passo 1): per ogni file dice dove sta, se è in un repository git e un destino
PROPOSTO. Il giudizio finale sul destino lo dà Claude in /fine.

USO
  inventario-sessione.py [--session ID] [--json]
    --session ID   id della sessione (default: $CLAUDE_CODE_SESSION_ID)
    --json         stampa JSON invece della tabella
  Solo per i banchi: --projects DIR (default ~/.claude/projects) e --home DIR (default ~).

FONTI
  - il transcript ~/.claude/projects/*/<ID>.jsonl e i subagent in <ID>/subagents/**/*.jsonl;
  - tool_use Write, Edit, MultiEdit, NotebookEdit (file_path o notebook_path);
  - comandi Bash: > >> &> tee, cp e mv (destinazione), -o --output --out, --pdf <file.pdf>.
    Le righe si dividono solo fuori dalle virgolette: una stringa su più righe resta un comando;
  - oggetti creati online con i connettori (un file su Drive, una bozza di email): vanno nell'handoff;
  - file in ~/Downloads e ~/Desktop modificati durante la sessione.
  Scarta ~/.claude/** (lo copre il Config Sync di /fine) e /dev/*. I file assenti finiscono in
  «spariti». Lo scratchpad e /tmp restano in elenco, marcati: si perdono al riavvio.

DESTINI PROPOSTI
  repo (commit) · archivia (documento fuori da un repository: va in una cartella che resta) ·
  resta (binario pesante, col percorso nel CLAUDE.md del progetto) · scarto (temporaneo)

EXIT
  0 inventario stampato · 2 id di sessione assente o transcript non trovato
"""
import argparse, glob, json, os, re, shlex, subprocess, sys
from datetime import datetime, timezone

PESANTE = 20 * 1024 * 1024

EST = {
    "codice": {".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".sh", ".bash", ".zsh", ".rb", ".go",
               ".rs", ".java", ".c", ".h", ".cpp", ".css", ".scss", ".vue", ".astro", ".html", ".htm",
               ".json", ".jsonl", ".yaml", ".yml", ".toml", ".sql", ".ps1", ".vbs", ".swift", ".php",
               ".lua", ".ipynb", ".svelte", ".plist", ".ini", ".cfg", ".conf"},
    "testo": {".md", ".txt", ".csv", ".tsv", ".log", ".eml", ".ics", ".xml", ".srt", ".vtt", ".rst"},
    "documento": {".pdf", ".docx", ".doc", ".odt", ".pptx", ".ppt", ".key", ".xlsx", ".xls", ".ods",
                  ".pages", ".numbers", ".rtf", ".epub"},
    "immagine": {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".heic", ".tif", ".tiff", ".bmp",
                  ".avif", ".psd", ".ico"},
}

# comandi dove -o non prende un file
NO_O = {"grep", "egrep", "fgrep", "rg", "ag", "ack", "ls", "ps", "set", "bash", "sh", "zsh", "ssh",
        "scp", "sftp", "rsync", "mount", "find", "awk", "gawk", "tar", "git", "unzip", "zip", "pgrep",
        "pkill", "lsof", "top", "shopt", "read", "column", "xargs"}
WRAPPER = {"sudo", "command", "time", "nohup", "exec", "then", "do", "else", "elif", "if", "while",
           "until", "!", "{", "}", "builtin"}
SEPARATORI = {";", "&&", "||", "|", "&", "(", ")", "|&", ";;", ";&"}
REDIR_OUT = {">", ">>", ">|", "&>", "&>>", ">&"}
SUBST = "\x00SUBST\x00"

# --- lettura del transcript -------------------------------------------------------------------

def testo_risultato(c):
    cont = c.get("content")
    if isinstance(cont, list):
        return "\n".join(x.get("text", "") for x in cont if isinstance(x, dict))
    return cont if isinstance(cont, str) else ""

def leggi_jsonl(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        for riga in f:
            try:
                yield json.loads(riga)
            except ValueError:
                continue

def timestamp(r):
    ts = r.get("timestamp")
    if isinstance(ts, str):
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None

def primo_timestamp(path):
    for r in leggi_jsonl(path):
        if (t := timestamp(r)):
            return t
    return None

# --- analisi dei comandi Bash -----------------------------------------------------------------

def togli_heredoc(cmd):
    """Toglie i corpi degli heredoc: il loro contenuto non è un comando."""
    righe, out, attesi = cmd.split("\n"), [], []
    for r in righe:
        if attesi:
            tag, tab = attesi[0]
            if (r.lstrip("\t") if tab else r).rstrip() == tag:
                attesi.pop(0)
            continue
        out.append(r)
        for m in re.finditer(r"(?<!<)<<(-?)\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\2", r):
            attesi.append((m.group(3), m.group(1) == "-"))
    return "\n".join(out)

def togli_sostituzioni(s):
    """Sostituisce $(...) e `...` con un segnaposto: il loro output non si conosce."""
    out, i = [], 0
    while i < len(s):
        if s.startswith("$(", i):
            prof, j = 1, i + 2
            while j < len(s) and prof:
                prof += {"(": 1, ")": -1}.get(s[j], 0)
                j += 1
            out.append(SUBST); i = j
        elif s[i] == "`":
            j = s.find("`", i + 1)
            j = len(s) if j < 0 else j + 1
            out.append(SUBST); i = j
        else:
            out.append(s[i]); i += 1
    return "".join(out)

def espandi(tok, var, home):
    if tok.startswith("~/") or tok == "~":
        tok = home + tok[1:]
    def sost(m):
        nome = m.group(1) or m.group(2)
        return var.get(nome, m.group(0))
    tok = re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)", sost, tok)
    if "$" in tok or "`" in tok or SUBST in tok or any(ch in tok for ch in "*?["):
        return None
    return tok

def assoluto(p, cwd):
    if not p:
        return None
    if not os.path.isabs(p):
        if not cwd:
            return None
        p = os.path.join(cwd, p)
    return os.path.normpath(p)

def righe_comando(testo):
    """Divide sui \\n fuori dalle virgolette e toglie i commenti #.
    Le righe dentro una stringa su più righe non sono comandi."""
    righe, cur, q, i, n, inizio = [], [], None, 0, len(testo), 0
    while i < n:
        ch = testo[i]
        if q == "'":
            if ch == "'":
                q = None
        elif q == '"':
            if ch == "\\" and i + 1 < n:
                cur.append(ch); i += 1; ch = testo[i]
            elif ch == '"':
                q = None
        elif ch == "\\" and i + 1 < n:
            cur.append(ch); i += 1; ch = testo[i]
        elif ch in "'\"":
            q = ch
        elif ch == "#" and (not cur or cur[-1] in " \t;&|()"):
            j = testo.find("\n", i)                   # commento fino a fine riga
            i = n if j < 0 else j
            continue
        elif ch == "\n":
            righe.append("".join(cur)); cur = []; i += 1; inizio = i
            continue
        cur.append(ch); i += 1
    if q:                                             # virgoletta mai chiusa: righe come prima
        return righe + testo[inizio:].split("\n")
    return righe + ["".join(cur)]

def comandi_semplici(riga):
    lex = shlex.shlex(riga, posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    toks = list(lex)
    cmd = []
    for t in toks:
        if t in SEPARATORI:
            if cmd:
                yield cmd
            cmd = []
        else:
            cmd.append(t)
    if cmd:
        yield cmd

def analizza_bash(comando, cwd, home, var=None):
    """Ritorna (scritture, spostati, non_risolti). scritture: lista (path, fonte)."""
    var = dict(var or {})
    var.setdefault("HOME", home)
    if os.environ.get("TMPDIR"):
        var.setdefault("TMPDIR", os.environ["TMPDIR"].rstrip("/"))
    scritte, spostati, irrisolti = [], [], 0
    testo = togli_heredoc(comando).replace("\\\n", " ")
    testo = re.sub(r"\(\(.*?\)\)", " ", testo)          # aritmetica (( a > b ))
    testo = re.sub(r"\[\[.*?\]\]", " true ", testo)      # test [[ a > b ]]
    testo = togli_sostituzioni(testo)
    for riga in righe_comando(testo):
        try:
            semplici = list(comandi_semplici(riga))
        except ValueError:
            irrisolti += 1
            continue
        for toks in semplici:
            parole, redir, i = [], [], 0
            while i < len(toks):
                t = toks[i]
                if t in REDIR_OUT or t in {"<", "<<", "<<<", "<>"}:
                    if parole and parole[-1].isdigit() and t != "&>":
                        parole.pop()
                    nxt = toks[i + 1] if i + 1 < len(toks) else None
                    if t in REDIR_OUT and nxt is not None and not (t == ">&" and (nxt.isdigit() or nxt == "-")):
                        redir.append(nxt)
                    i += 2
                    continue
                parole.append(t); i += 1
            for r in redir:
                p = espandi(r, var, home)
                if p is None:
                    irrisolti += 1
                elif (a := assoluto(p, cwd)):
                    scritte.append((a, "Bash >"))
            # assegnazioni e wrapper in testa
            while parole and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", parole[0]):
                if len(parole) == 1 or all(re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", w) for w in parole):
                    for w in parole:
                        k, v = w.split("=", 1)
                        e = espandi(v, var, home) if v else ""
                        if e is None:
                            var.pop(k, None)
                        else:
                            var[k] = e
                    parole = []
                    break
                parole.pop(0)
            while parole and parole[0] in WRAPPER:
                parole.pop(0)
            if parole and parole[0] == "export":
                for w in parole[1:]:
                    if "=" in w:
                        k, v = w.split("=", 1)
                        e = espandi(v, var, home)
                        if e is None:
                            var.pop(k, None)
                        else:
                            var[k] = e
                continue
            if parole and parole[0] == "env":
                parole = parole[1:]
                while parole and (parole[0].startswith("-") or "=" in parole[0]):
                    parole.pop(0)
            # timeout/gtimeout/nice con le loro opzioni e la durata: il comando vero viene dopo
            while parole and os.path.basename(parole[0]) in ("timeout", "gtimeout", "nice"):
                parole.pop(0)
                while parole and (parole[0].startswith("-") or re.fullmatch(r"[0-9.]+[smhd]?", parole[0])):
                    parole.pop(0)
            if not parole:
                continue
            nome = os.path.basename(parole[0])
            args = parole[1:]
            if nome == "cd":
                dest = args[0] if args and args[0] != "-" else home
                e = espandi(dest, var, home)
                cwd = assoluto(e, cwd) if e else None
                continue
            if nome in ("cp", "mv"):
                destdir, posiz, fine_opz, j = None, [], False, 0
                while j < len(args):
                    a = args[j]
                    if not fine_opz and a == "--":
                        fine_opz = True
                    elif not fine_opz and a in ("-t", "--target-directory"):
                        destdir = args[j + 1] if j + 1 < len(args) else None; j += 1
                    elif not fine_opz and a.startswith("--target-directory="):
                        destdir = a.split("=", 1)[1]
                    elif not fine_opz and a.startswith("-") and a != "-":
                        pass
                    else:
                        posiz.append(a)
                    j += 1
                if destdir is None:
                    if len(posiz) < 2:
                        continue
                    destdir, sorgenti = posiz[-1], posiz[:-1]
                    unico = len(sorgenti) == 1
                else:
                    sorgenti, unico = posiz, False
                d = espandi(destdir, var, home)
                d = assoluto(d, cwd) if d else None
                if not d:
                    irrisolti += 1
                    continue
                for s in sorgenti:
                    sp = espandi(s, var, home)
                    sa = assoluto(sp, cwd) if sp else None
                    if unico and not os.path.isdir(d) and not destdir.endswith("/"):
                        target = d
                    elif sa:
                        target = os.path.join(d, os.path.basename(sa.rstrip("/")))
                    else:
                        irrisolti += 1
                        continue
                    scritte.append((target, f"Bash {nome}"))
                    if nome == "mv" and sa:
                        spostati.append((sa, target))
                continue
            if nome == "tee":
                for a in args:
                    if a.startswith("-"):
                        continue
                    p = espandi(a, var, home)
                    if p is None:
                        irrisolti += 1
                    elif (x := assoluto(p, cwd)):
                        scritte.append((x, "Bash tee"))
                continue
            if nome in NO_O:
                continue
            j = 0
            while j < len(args):
                a, val = args[j], None
                if a in ("-o", "--output", "--out") and j + 1 < len(args):
                    val = args[j + 1]; j += 1
                elif a.startswith("--output=") or a.startswith("--out="):
                    val = a.split("=", 1)[1]
                # --pdf vale solo con un file .pdf: altrove può essere un flag senza valore
                elif a == "--pdf" and j + 1 < len(args) and args[j + 1].lower().endswith(".pdf"):
                    val = args[j + 1]; j += 1
                elif a.startswith("--pdf=") and a.lower().endswith(".pdf"):
                    val = a.split("=", 1)[1]
                j += 1
                if val is None or val in ("", "-") or val.startswith("-"):
                    continue
                p = espandi(val, var, home)
                if p is None:
                    irrisolti += 1
                elif (x := assoluto(p, cwd)):
                    scritte.append((x, "Bash -o"))
    return scritte, spostati, irrisolti

# --- oggetti creati online -----------------------------------------------------------------

# Connettori che creano qualcosa fuori dal computer: il nome del tool finisce così.
CONNETTORI = {"Google_Drive__create_file": "file su Drive", "Google_Drive__copy_file": "file su Drive",
              "Gmail__create_draft": "bozza di email"}
RE_ID_JSON = re.compile(r"[\"'](?:id|fileId|draftId)[\"']\s*:\s*[\"']([A-Za-z0-9_-]{8,})[\"']")


def id_online(risultato):
    m = RE_ID_JSON.search(risultato)
    return m.group(1) if m else None


# --- classificazione --------------------------------------------------------------------------

def sotto(path, radice):
    radice = radice.rstrip("/")
    return path == radice or path.startswith(radice + "/")

def volatile(path, home=None):
    """Vero per /tmp e simili: si perdono al riavvio. La HOME non lo è mai, anche se sta lì (i banchi)."""
    if home and sotto(path, home):
        return False
    return any(sotto(path, r) for r in ("/tmp", "/private/tmp", "/var/folders", "/private/var/folders"))

def scratchpad(path):
    return re.match(r"^(/private)?/tmp/claude-\d+/", path) is not None

def tipo_file(path, byte):
    if os.path.isdir(path):
        return "cartella"
    if byte is not None and byte > PESANTE:
        return "binario pesante"
    ext = os.path.splitext(path)[1].lower()
    for t, s in EST.items():
        if ext in s:
            return t
    return "altro"

def repo_di(path, cache):
    d = path if os.path.isdir(path) else os.path.dirname(path)
    visti = []
    while d and d != "/":
        if d in cache:
            r = cache[d]; break
        visti.append(d)
        if os.path.exists(os.path.join(d, ".git")):
            r = d; break
        d = os.path.dirname(d)
    else:
        r = None
    for v in visti:
        cache[v] = r
    return r

def stato_git(repo, paths):
    """Ritorna {path: pulito|modificato|non tracciato|ignorato}."""
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
    rel = [os.path.relpath(p, repo) for p in paths]
    def git(*a):
        p = subprocess.run(["git", "-C", repo, *a, "--", *rel], capture_output=True, env=env)
        return p.stdout.decode("utf-8", "replace") if p.returncode == 0 else None
    ls = git("ls-files", "-z")
    st = git("status", "--porcelain=v1", "-z", "--untracked-files=all")
    if ls is None or st is None:
        return {p: "sconosciuto" for p in paths}
    tracciati = {x for x in ls.split("\0") if x}
    stati, voci, k = {}, st.split("\0"), 0
    while k < len(voci):
        v = voci[k]
        if len(v) > 3:
            stati[v[3:]] = v[:2]
            if v[0] in "RC":
                k += 1                      # la voce dopo è il nome vecchio
        k += 1
    out = {}
    for p, r in zip(paths, rel):
        if os.path.isdir(p):
            dentro = [s for s in stati if s == r or s.startswith(r.rstrip("/") + "/")]
            if any(stati[s] == "??" for s in dentro):
                out[p] = "non tracciato"
            elif dentro:
                out[p] = "modificato"
            elif any(t.startswith(r.rstrip("/") + "/") for t in tracciati):
                out[p] = "pulito"
            else:
                out[p] = "ignorato"
        elif r in tracciati:
            out[p] = "modificato" if r in stati else "pulito"
        else:
            out[p] = "non tracciato" if stati.get(r) == "??" else "ignorato"
    return out

def cartelle_lavoro(home):
    """Download, Scrivania e la cartella dei progetti (PROJECTS_BASE, come /inizio)."""
    base = os.environ.get("PROJECTS_BASE") or os.path.join(home, "Documents", "ClaudeCode")
    if base.startswith("~"):
        base = home + base[1:]
    return [os.path.join(home, "Downloads"), os.path.join(home, "Desktop"), os.path.normpath(base)]


def proponi(f, home):
    p, tipo = f["path"], f["tipo"]
    lavoro = any(sotto(p, d) for d in cartelle_lavoro(home))
    if f["repo"] and f["git"] not in ("ignorato", "sconosciuto"):
        if f["git"] == "pulito":
            return "repo", "già committato nel repo"
        return "repo", "dentro un repo git: va committato per pathspec"
    if tipo == "binario pesante":
        return "resta", "oltre 20 MB: resta dov'è, col path nel CLAUDE.md del progetto"
    if f["volatile"]:
        if tipo in ("documento", "immagine"):
            return "archivia", "si perde al riavvio: se è un documento che serve, spostalo in una cartella che resta"
        return "scarto", "file temporaneo che si perde al riavvio"
    if tipo in ("documento", "immagine", "testo", "cartella"):
        if lavoro:
            return "archivia", "documento fuori da un repository: va nella cartella del progetto o in una che tieni"
        return "resta", "documento fuori dalle cartelle di lavoro: resta dov'è, l'handoff dice dove"
    if tipo == "codice":
        return "scarto", "codice fuori da un repo: portalo in un repo o scartalo"
    return "resta", "tipo non riconosciuto: decide il modello"

def dimensione(path):
    try:
        if os.path.isdir(path):
            tot, n = 0, 0
            for radice, _, files in os.walk(path):
                for x in files:
                    n += 1
                    if n > 5000:
                        return tot
                    try:
                        tot += os.lstat(os.path.join(radice, x)).st_size
                    except OSError:
                        pass
            return tot
        return os.path.getsize(path)
    except OSError:
        return None

def umano(n):
    if n is None:
        return "-"
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024 or u == "GB":
            return f"{n:.0f} {u}" if u == "B" else f"{n:.1f} {u}".replace(".", ",")
        n /= 1024

# --- raccolta ---------------------------------------------------------------------------------

def trova_transcript(sid, projects):
    principali = sorted(glob.glob(os.path.join(projects, "*", f"{sid}.jsonl")))
    sub = []
    for cart in glob.glob(os.path.join(projects, "*", sid, "subagents")):
        sub += glob.glob(os.path.join(cart, "**", "*.jsonl"), recursive=True)
    return principali, sorted(sub)

def raccogli(sid, projects, home):
    principali, sub = trova_transcript(sid, projects)
    if not principali:
        return None
    inizio = min((t for t in (primo_timestamp(p) for p in principali) if t), default=None)
    ultimo = inizio
    file, spostati, online, irrisolti = {}, {}, [], 0

    def aggiungi(path, fonte, agente):
        f = file.setdefault(path, {"fonti": set(), "agenti": set(), "operazioni": 0})
        f["fonti"].add(fonte); f["agenti"].add(agente); f["operazioni"] += 1

    for tr in principali + sub:
        agente = "sessione" if tr in principali else "subagent"
        attesi = {}                                   # tool_use_id -> tipo dell'oggetto online
        for r in leggi_jsonl(tr):
            t = timestamp(r)
            if t and (ultimo is None or t > ultimo):
                ultimo = t
            m = r.get("message")
            if not isinstance(m, dict) or not isinstance(m.get("content"), list):
                continue
            for c in m["content"]:
                if not isinstance(c, dict):
                    continue
                if c.get("type") == "tool_use":
                    nome, inp = c.get("name", ""), c.get("input") or {}
                    if nome in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
                        p = inp.get("file_path") or inp.get("notebook_path")
                        if isinstance(p, str) and (a := assoluto(p, r.get("cwd"))):
                            aggiungi(a, nome, agente)
                    elif nome == "Bash":
                        cmd = inp.get("command") or ""
                        sc, sp, ir = analizza_bash(cmd, r.get("cwd"), home)
                        irrisolti += ir
                        for p, fonte in sc:
                            aggiungi(p, fonte, agente)
                        for s, d in sp:
                            spostati[s] = d
                    else:
                        for chiave, t in CONNETTORI.items():
                            if nome.endswith(chiave):
                                attesi[c.get("id")] = t
                elif c.get("type") == "tool_result" and c.get("tool_use_id") in attesi:
                    t = attesi.pop(c["tool_use_id"])
                    online.append({"tipo": t, "id": id_online(testo_risultato(c)), "agente": agente})

    # Downloads e Desktop tra l'avvio e l'ultimo record (più 10 minuti): una sessione
    # vecchia non raccoglie i download dei giorni dopo
    if inizio:
        soglia, tetto = inizio.timestamp(), ultimo.timestamp() + 600
        for nome_d in ("Downloads", "Desktop"):
            radice = os.path.join(home, nome_d)
            base = radice.count(os.sep)
            for d, sottocart, files in os.walk(radice):
                sottocart[:] = [s for s in sottocart if not s.startswith(".")
                                and not s.endswith((".app", ".photoslibrary", ".bundle"))]
                if d.count(os.sep) - base >= 2:
                    sottocart[:] = []
                for x in files:
                    if x.startswith(".") or x.endswith((".crdownload", ".part", ".download")):
                        continue
                    p = os.path.join(d, x)
                    try:
                        st = os.stat(p)
                    except OSError:
                        continue
                    if soglia < max(st.st_mtime, getattr(st, "st_birthtime", 0)) <= tetto:
                        aggiungi(p, nome_d, "disco")

    # filtro, esistenza, classificazione
    claude_dirs = {os.path.join(home, ".claude")}
    try:
        claude_dirs.add(os.path.realpath(os.path.join(home, ".claude")))
    except OSError:
        pass
    esclusi = {"~/.claude": 0, "/dev": 0}
    vivi, spariti = [], []
    for p in sorted(file):
        info = file[p]
        reale = os.path.realpath(p)
        if any(sotto(p, c) or sotto(reale, c) for c in claude_dirs):
            esclusi["~/.claude"] += 1; continue
        if sotto(p, "/dev"):
            esclusi["/dev"] += 1; continue
        base = {"path": p, "fonti": sorted(info["fonti"]), "agenti": sorted(info["agenti"]),
                "operazioni": info["operazioni"]}
        if not os.path.exists(p):
            nota = f"spostato con mv in {spostati[p]}" if p in spostati else "non esiste più"
            spariti.append({**base, "esiste": False, "nota": nota, "volatile": volatile(p, home)})
            continue
        vivi.append({**base, "esiste": True})

    # sorgenti di mv mai scritte nella sessione: compaiono solo tra gli spariti
    for src, dest in sorted(spostati.items()):
        if src in file or os.path.exists(src) or any(sotto(src, c) for c in claude_dirs) or sotto(src, "/dev"):
            continue
        spariti.append({"path": src, "fonti": ["Bash mv"], "agenti": [], "operazioni": 1, "esiste": False,
                        "nota": f"spostato con mv in {dest}", "volatile": volatile(src, home)})

    cache, per_repo = {}, {}
    for f in vivi:
        f["byte"] = dimensione(f["path"])
        f["tipo"] = tipo_file(f["path"], f["byte"])
        f["repo"] = repo_di(f["path"], cache)
        f["volatile"] = volatile(f["path"], home)
        f["scratchpad"] = scratchpad(f["path"])
        if f["repo"]:
            per_repo.setdefault(f["repo"], []).append(f["path"])
    stati = {}
    for repo, paths in per_repo.items():
        stati.update(stato_git(repo, paths))
    for f in vivi:
        f["git"] = stati.get(f["path"])
        f["destino"], f["motivo"] = proponi(f, home)
        if f["volatile"]:
            f["nota"] = ("scratchpad" if f["scratchpad"] else "/tmp") + ": si perde al riavvio, destino da decidere"

    for o in online:
        if o["tipo"] == "bozza di email":
            o["destino"], o["motivo"] = "resta", "bozza da mandare: l'handoff dice se è partita o scartata"
        else:
            o["destino"], o["motivo"] = "resta", "creato online: l'handoff dice dove sta"

    return {"sessione": sid, "inizio": inizio.isoformat() if inizio else None,
            "transcript": principali, "subagent": len(sub), "file": vivi, "online": online,
            "spariti": spariti, "esclusi": esclusi, "non_risolti": irrisolti}

# --- uscita -----------------------------------------------------------------------------------

def stampa(inv, home):
    corto = lambda p: "~" + p[len(home):] if sotto(p, home) else p
    print(f"INVENTARIO SESSIONE {inv['sessione']}")
    print(f"avvio {inv['inizio'] or '?'} · {len(inv['transcript'])} transcript · {inv['subagent']} subagent")
    stabili = [f for f in inv["file"] if not f["volatile"]]
    volatili = [f for f in inv["file"] if f["volatile"]]
    def tabella(titolo, righe):
        print(f"\n{titolo} ({len(righe)})")
        if not righe:
            print("  nessuno")
            return
        print(f"  {'DESTINO':<16} {'TIPO':<16} {'DIM':>9}  {'GIT':<14} PATH")
        for f in righe:
            print(f"  {f['destino']:<16} {f['tipo']:<16} {umano(f['byte']):>9}  {(f['git'] or '-'):<14} {corto(f['path'])}")
            print(f"  {'':<16} perché: {f['motivo']} · fonti: {', '.join(f['fonti'])}")
    tabella("FILE", stabili)
    tabella("SCRATCHPAD E /tmp: si perdono al riavvio, destino da decidere", volatili)
    print(f"\nCREATI ONLINE ({len(inv['online'])})")
    if not inv["online"]:
        print("  nessuno")
    for o in inv["online"]:
        print(f"  {o['destino']:<16} {o['tipo']:<16} {o['id'] or '-'}  ({o['motivo']})")
    print(f"\nSPARITI ({len(inv['spariti'])})")
    if not inv["spariti"]:
        print("  nessuno")
    for s in inv["spariti"]:
        print(f"  {corto(s['path'])}  ({s['nota']}{', era in /tmp' if s['volatile'] else ''})")
    e = inv["esclusi"]
    print(f"\nESCLUSI: {e['~/.claude']} in ~/.claude, {e['/dev']} in /dev · path non risolti nei comandi Bash: {inv['non_risolti']}")

def main():
    ap = argparse.ArgumentParser(description="Inventario dei file prodotti da una sessione Claude Code.")
    ap.add_argument("--session", default=os.environ.get("CLAUDE_CODE_SESSION_ID"))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--projects", help=argparse.SUPPRESS)
    ap.add_argument("--home", help=argparse.SUPPRESS)
    a = ap.parse_args()
    home = os.path.normpath(a.home or os.path.expanduser("~"))
    projects = a.projects or os.path.join(home, ".claude", "projects")
    if not a.session:
        print("INVENTARIO: manca l'id di sessione: passa --session o imposta CLAUDE_CODE_SESSION_ID", file=sys.stderr)
        return 2
    inv = raccogli(a.session, projects, home)
    if inv is None:
        print(f"INVENTARIO: transcript non trovato per la sessione {a.session} in {projects}", file=sys.stderr)
        return 2
    if a.json:
        json.dump(inv, sys.stdout, ensure_ascii=False, indent=2)
        print()
    else:
        stampa(inv, home)
    return 0

if __name__ == "__main__":
    sys.exit(main())
