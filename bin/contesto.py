#!/usr/bin/env python3
"""arturo contesto: il contesto di un progetto per /inizio, in una chiamata e in sola lettura.

Uso: arturo contesto [nome] [--giorni N]
     arturo contesto <nome> --json    le fonti del contesto (istruzioni, indice della memoria, scheda,
                                      quadro di /inizio, ultimo handoff, note collegate) con file, data,
                                      peso e prime righe: la finestra "Contesto del progetto" di Volta
     arturo contesto --stdin          gli argomenti di /inizio su stdin, mai nella riga di comando: il
                                      compito può contenere virgolette, # e $(...) che la shell eseguirebbe
  Senza nome usa la cartella in cui sei. Accetta anche gli argomenti interi di /inizio:
  "--tutti" si ignora, e il compito (le parole dopo il nome, o dopo " -- ") non fa parte del nome.
  "<nome> -- --rotazione <compito>" è la marca della rotazione automatica: --rotazione esce dal compito
  e il contesto stampa la riga "rotazione: sì". Con " --in-attesa <domanda>" in fondo, la domanda alla persona
  rimasta aperta dopo la rotazione esce dal compito e il contesto stampa "in attesa: <domanda>".

Stampa, in quest'ordine: progetto e cartella, la quota di 5 ore e settimana vista dalla barra, la scheda del
progetto dalla memoria (se è accesa: cos'è, decisioni chiuse, errori da non ripetere; la sua cartella vale
anche fuori dalla base dei progetti), git (branch, modifiche, conflitti, commit dopo
l'ultimo handoff, rami locali non riportati), la ripartenza degli handoff degli ultimi N giorni (14), i todo aperti del
progetto divisi per chi agisce, i todo chiusi dopo l'ultimo handoff, le scadenze dei prossimi
7 giorni (anche fuori dal progetto), il todo da cui ripartire e gli avvisi.
Tra due blocchi bash le variabili si perdono: qui tutto vive in un processo.

Con ~/.claude/arturo/fonte-task.local i todo vengono dalla fonte esterna (arturo todo --progetto <slug> --json --tutti).
Se non risponde, la sezione dei todo mostra la tabella Task Pendenti dell'ultimo handoff con l'avviso
NON VERIFICATO: mai "nessuno" quando la fonte è giù.

Exit: 0 contesto stampato · 2 NON TROVATO (né cartella, né handoff, né todo, né scheda; stampa i nomi
simili) · 3 uso sbagliato. Non scrive niente: niente pull, niente mkdir, niente todo. Le uniche eccezioni
sono il segno della domanda dell'intervista (INTERVISTA, bin/intervista.py) e, nei giorni senza domanda, il
segno della proposta di uno spazio (SPAZIO, bin/spazi.py), tutte e due fuori dalla rotazione.
"""
from __future__ import annotations

import datetime as dt
import difflib
import importlib.util
import json
import os
import re
import subprocess
import sys
import threading
from pathlib import Path

QUI = Path(os.path.realpath(__file__)).parent
sys.path.insert(0, str(QUI))
import todo_store as ts  # noqa: E402
import riporti  # noqa: E402
sys.path.append(str(Path(os.path.realpath(__file__)).parent.parent / "hooks"))
from radici import radice_orsa  # noqa: E402

GIORNI = 14
GIORNI_SCADENZE = 7
GIORNI_FERMI = 3  # proposta n. 52: un todo di Claude senza un passo da più di 3 giorni torna in vista
MAX_STATUS = 15
MAX_COMMIT = 15
MAX_RIPARTENZA = 700
MAX_CARATTERI = 28000
PAROLE_COMPITO = 4  # da quante parole un testo senza progetto è un compito e non un nome
SALVATO_AUTO = "- Salvato: in automatico"  # la marca di bin/salva-automatico.py
ETICHETTE = {"tu": "TOCCA A TE", "decidi": "DECIDI TU, POI FACCIO IO", "io": "FACCIO IO", "fermo": "FERMO"}


def slug(nome: str) -> str:
    """Lo stesso slug di /inizio, /fine e arturo todo."""
    return re.sub(r"^-+|-+$", "", re.sub(r"[^a-z0-9]+", "-", nome.lower()))


def base_progetti() -> Path:
    pb = os.environ.get("PROJECTS_BASE") or str(Path.home() / "Documents" / "ClaudeCode")
    if pb.startswith("~"):
        pb = str(Path.home()) + pb[1:]
    return Path(pb)


def handoff_dir() -> Path:
    return radice_orsa() / "data" / "handoffs"


def git(cartella: Path, *argomenti: str) -> str:
    try:
        r = subprocess.run(["git", "-c", "core.fsmonitor=false", "-C", str(cartella), *argomenti],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15,
                           env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"})
    except (OSError, subprocess.SubprocessError):
        return ""
    return r.stdout.rstrip("\n") if r.returncode == 0 else ""


def cima_git(cartella: Path) -> Path | None:
    radice = git(cartella, "rev-parse", "--show-toplevel")
    return Path(radice) if radice else None


def leggi_argomenti(argv: list) -> tuple:
    """(nome, giorni). Gli argomenti di /inizio arrivano spesso come una stringa sola."""
    testo = " ".join(argv)
    testo = re.split(r"(?:^|\s)--(?:\s|$)", testo, maxsplit=1)[0]  # il compito dopo " -- "
    giorni = GIORNI
    m = re.search(r"--giorni(?:=|\s+)(\S+)", testo)
    if m:
        if not m.group(1).isdigit() or int(m.group(1)) < 1:
            raise ValueError(f'--giorni vuole un numero intero da 1 in su, non "{m.group(1)}"')
        giorni = int(m.group(1))
        testo = testo.replace(m.group(0), " ")
    parole = [p for p in testo.split() if p != "--tutti"]
    # Un'opzione sconosciuta ("-x", "--boh") sta in testa o subito dopo il nome: "libro --boh" e
    # "libro --rotazione scrivi" (la marca va dopo " -- ") escono 3. Più avanti è una parola del compito
    # ("libro togli il flag --force"), e un trattino da solo è punteggiatura ("libro - capitolo tre"):
    # li separa risolvi_nome (review del 7/11/2026, finding 33).
    strani = [p for p in parole[:2] if re.match(r"--?[^\W\d_]", p)]
    if strani:
        raise ValueError(f"opzione sconosciuta: {strani[0]}")
    return " ".join(parole), giorni


def e_cartella(p: Path) -> bool:
    """is_dir() che regge un nome lungo: fino a Python 3.13 un componente oltre 255 byte solleva OSError
    ENAMETOOLONG invece di dare False (segnalazione n. 42, 1/11/2026, Python 3.9.6)."""
    try:
        return p.is_dir()
    except OSError:
        return False


def trova_cartella(nome: str) -> tuple:
    """(cartella o None, contenitore). Senza nome vale la cartella corrente, se è un progetto."""
    cwd, home, pb = Path.cwd().resolve(), Path.home().resolve(), base_progetti()
    if not nome:
        if cwd in (home, pb.resolve() if pb.exists() else pb):
            return None, True
        return (cima_git(cwd) or cwd), False
    cima = cima_git(cwd)
    if cima and slug(cima.name) == slug(nome) and cima != home:
        return cima, False
    for c in (pb / nome, home / "Documents" / nome, home / "Projects" / nome, home / nome, cwd / nome):
        if e_cartella(c) and c != home:
            return c.resolve(), False
    # Il nome scritto come slug ("mio-progetto") per una cartella "mio_progetto" o "Mio Progetto":
    # l'INDEX e gli handoff usano lo slug (segnalazione n. 21, 27/10/2026).
    if pb.is_dir() and slug(nome):
        for c in sorted(pb.iterdir()):
            if c.is_dir() and not c.name.startswith(".") and slug(c.name) == slug(nome):
                return c.resolve(), False
    return None, False


def modulo_index():
    spec = importlib.util.spec_from_file_location("index_rigenera", str(QUI / "index-rigenera.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def handoff_di(s: str) -> list:
    """Gli handoff del progetto, dal più recente: (nome, data, ora, percorso)."""
    d = handoff_dir() / s
    if not s or not e_cartella(d):
        return []
    out = []
    for f in sorted(d.glob("HANDOFF_*.md"), key=lambda p: p.name, reverse=True):
        m = re.match(r"^HANDOFF_(\d{4}-\d{2}-\d{2})_(\d{2})-(\d{2})\.md$", f.name)
        if m:
            out.append((f.name, m.group(1), f"{m.group(2)}:{m.group(3)}", f))
    return out


def nomi_noti() -> set:
    """Le cartelle dei progetti e quelle degli handoff."""
    nomi = set()
    for d in (base_progetti(), handoff_dir()):
        try:
            nomi.update(p.name for p in d.iterdir() if p.is_dir() and not p.name.startswith("."))
        except OSError:
            continue
    return nomi


def nomi_vecchi() -> dict:
    """{nome vecchio: progetto} dagli alias delle schede della memoria: dopo arturo progetti rinomina il nome
    vecchio apre il progetto nuovo (proposta n. 90, 19/11/2026). Un alias che è ancora un progetto vero non
    conta. Senza memoria: {}."""
    try:
        import progetti as _pg
        schede = _pg.schede()
    except Exception:  # noqa: BLE001 - la memoria è facoltativa: /inizio non si ferma per lei
        return {}
    veri = {slug(n) for n in nomi_noti()}
    fuori = {}
    for s, v in schede.items():
        for a in v.get("alias") or []:
            if a and a != s and a not in veri:
                fuori.setdefault(a, s)
    return fuori


def forti(pref: str, nomi) -> list:
    """I nomi che contengono il prefisso intero, o tutte le sue parole di 3 lettere o più. Un prefisso di una
    o due lettere non somiglia a niente: "ti ricordi…" sceglieva un progetto con "ti" nel nome (segnalazione
    n. 64, 10/11/2026). Il nome scritto intero resta valido anche corto: lo trova trova_cartella."""
    if len(pref.replace("-", "")) < 3:
        return []
    parole = [p for p in pref.split("-") if len(p) >= 3]
    return sorted(n for n in nomi if pref in slug(n) or (len(parole) > 1 and all(p in slug(n) for p in parole)))


def risolvi_nome(nome: str) -> tuple:
    """(nome, resto, avviso). Il compito scritto subito dopo il nome, senza " -- ", resta fuori dal nome: si
    prova il prefisso più lungo che porta a un progetto. Se nessun prefisso ci porta, un candidato forte
    unico vale con l'avviso "interpretato" ("due mondi" per due-mondi-myway)."""
    parole = nome.split()
    prefissi = [(" ".join(parole[:k]), " ".join(parole[k:])) for k in range(len(parole), 0, -1)]
    for pref, resto in prefissi:
        if slug(pref) and (trova_cartella(pref)[0] or e_cartella(handoff_dir() / slug(pref))):
            return pref, resto, None
    nuovi = nomi_vecchi()
    for pref, resto in prefissi:
        if slug(pref) in nuovi:
            return nuovi[slug(pref)], resto, f'il nome vecchio "{pref}" ora è {nuovi[slug(pref)]}'
    nomi = nomi_noti()
    for pref, resto in prefissi:
        f = forti(slug(pref), nomi) if slug(pref) else []
        if len(f) == 1:
            return f[0], resto, f'interpretato "{pref}" come {f[0]}'
        if f:
            break  # più candidati: un prefisso più corto ne darebbe di più
    # Una frase senza nome di progetto ("oggi ho scaricato molti documenti, riordinameli") è un compito:
    # vale la cartella corrente, e da una cartella contenitore /inizio propone i progetti col compito in
    # mano (segnalazione n. 39, 31/10/2026). Fino a tre parole resta un nome, magari con un refuso.
    if len(parole) >= PAROLE_COMPITO:
        return "", nome, "nessun nome di progetto nel testo: è il compito della sessione"
    return nome, "", None


def candidati(nome: str) -> list:
    nomi = nomi_noti()
    if not nome:
        return sorted(n for n in nomi if not n.startswith("_"))[:15]  # _backup, _bozze: non sono progetti
    per_minuscolo = {}
    for n in sorted(nomi):
        per_minuscolo.setdefault(n.lower(), n)
    simili = difflib.get_close_matches(nome.lower(), list(per_minuscolo), n=5, cutoff=0.5)
    return [per_minuscolo[n] for n in simili]


def corto(testo: str, n: int) -> str:
    testo = re.sub(r"\s+", " ", testo).strip()
    return testo if len(testo) <= n else testo[:n].rsplit(" ", 1)[0] + "…"


def sezione_git(cartella: Path, dal: str | None) -> list:
    if not cima_git(cartella):
        return ["GIT", "  la cartella non è un repository git"]
    righe = ["GIT"]
    branch = git(cartella, "branch", "--show-current") or "(nessun branch)"
    ultimo = git(cartella, "log", "-1", "--format=%h %s (%cs)")
    righe.append(f"  branch {branch}" + (f" · ultimo commit {ultimo}" if ultimo else " · nessun commit"))
    status = [r for r in git(cartella, "status", "--short").splitlines() if r.strip()]
    if status:
        righe.append(f"  modifiche non salvate in un commit: {len(status)} file")
        righe += [f"    {r}" for r in status[:MAX_STATUS]]
        if len(status) > MAX_STATUS:
            righe.append(f"    … e altri {len(status) - MAX_STATUS}")
    conflitti = [r for r in git(cartella, "diff", "--name-only", "--diff-filter=U").splitlines() if r]
    if conflitti:
        righe.append("  CONFLITTI DI MERGE: risolvili prima di tutto")
        righe += [f"    {r}" for r in conflitti]
    if dal:
        nuovi = [r for r in git(cartella, "log", f"--since={dal}", "--format=%h %s (%cs)").splitlines() if r]
        righe.append(f"  commit dal giorno dell'ultimo handoff ({dal}): {len(nuovi)}")
        righe += [f"    {r}" for r in nuovi[:MAX_COMMIT]]
    rami = rami_non_riportati(cartella)
    if rami:
        righe.append(f"  RAMI CON COMMIT CHE NON SONO SU {branch}: {len(rami)}")
        righe += [f"    {r}" for r in rami[:MAX_STATUS]]
    return righe


def rami_non_riportati(cartella: Path) -> list:
    """I rami locali con commit che il branch corrente non ha, col worktree se ne hanno uno.
    Il ramo di un worktree che /fine non ha riportato resta qui finché qualcuno non lo unisce
    (segnalazione n. 20, 27/10/2026: venti commit fermi sul ramo e /inizio zitto). Un ramo coi
    commit già arrivati in altra forma (cherry-pick, rebase) non compare: lo dice git cherry, lo
    stesso controllo che /fine fa prima dell'handoff."""
    worktree, percorso = {}, ""
    for r in git(cartella, "worktree", "list", "--porcelain").splitlines():
        if r.startswith("worktree "):
            percorso = r[len("worktree "):]
        elif r.startswith("branch refs/heads/"):
            worktree[r[len("branch refs/heads/"):]] = percorso
    # Il segno di shared/fine-worktree.md: la sessione ha chiuso il ramo ma non poteva toccare il
    # tree principale (#4007, 19/11/2026). Manca solo il merge, e lo fa /inizio. Dal 25/11/2026 il segno
    # sta in data/riporti.json (bin/riporti.py, segnalazione n. 97): la guardia del worktree rifiuta
    # git config. Si leggono ancora i segni vecchi in git config, che spariscono con git branch -d.
    segnati = {}
    for r in git(cartella, "config", "--get-regexp", r"^branch\..*\.arturo-riporta$").splitlines():
        chiave, _, valore = r.partition(" ")
        segnati[chiave[len("branch."):-len(".arturo-riporta")]] = valore
    segnati.update(riporti.segnati(cartella))
    righe = []
    elenco = git(cartella, "for-each-ref", "refs/heads", "--no-merged=HEAD",
                 "--format=%(refname:short)\t%(committerdate:short)")
    for r in elenco.splitlines():
        if "\t" not in r:
            continue
        ramo, data = r.split("\t", 1)
        # git cherry segna con "-" un commit già arrivato in altra forma (cherry-pick, rebase): non manca.
        mancanti = [c for c in git(cartella, "cherry", "HEAD", f"refs/heads/{ramo}").splitlines() if c.startswith("+")]
        if not mancanti:
            continue
        quanti = len(mancanti)
        dove = f" · worktree {worktree[ramo]}" if ramo in worktree else ""
        chiuso = segnati.get(ramo, "")
        segno = f" · chiuso da /fine il {chiuso}, da riportare" if chiuso else ""
        righe.append((not chiuso, f"{ramo} · {quanti} commit · ultimo {data}{dove}{segno}"))
    # I rami chiusi da /fine vanno in cima: l'elenco si taglia a MAX_STATUS, e con 32 rami un repository vero
    # perdeva proprio quello da riportare (prova dal vivo del 19/11/2026).
    return [r for _, r in sorted(righe, key=lambda x: x[0])]


def sezione_handoff(elenco: list, giorni: int, ir) -> list:
    if not elenco:
        return ["RIPARTENZA", "  nessun handoff per questo progetto"]
    limite = (ts.oggi() - dt.timedelta(days=giorni)).isoformat()
    recenti = [h for h in elenco if h[1] >= limite] or elenco[:1]
    titolo = f"RIPARTENZA (handoff degli ultimi {giorni} giorni)"
    if recenti[0][1] < limite:
        titolo = f"RIPARTENZA (nessun handoff negli ultimi {giorni} giorni: il più recente)"
    righe = [titolo]
    for n, (nome, data, ora, percorso) in enumerate(recenti[:5]):
        testo = percorso.read_text(encoding="utf-8", errors="replace")
        filone = ir.filone_esplicito(testo)
        stato = ir.stato_handoff(testo)
        testa = f"  {data} {ora}" + (f" · filone {filone}" if filone else "") + (f" · {stato}" if stato else "")
        righe.append(f"{testa} · {nome}")
        if n == 0 and SALVATO_AUTO in testo.splitlines():
            # M4 della memoria (15/11/2026): l'ultima sessione si è chiusa senza /fine e bin/salva-automatico.py
            # ha scritto questo handoff dal transcript. /inizio lo dice, e il primo /fine lo completa.
            righe.append("    SALVATO IN AUTOMATICO: L'ultima volta non hai chiuso con /fine: ecco cosa stavi facendo. "
                         "Il primo /fine di questa sessione completa questo handoff, senza farne un altro.")
            for sez in ("Ultime richieste", "Lavoro aperto nella sessione", "Correzioni"):
                voci = [r.strip() for r in ir.sezione(testo, sez).splitlines() if r.strip()]
                if voci:
                    righe.append(f"    {sez}: " + " · ".join(corto(v, 200) for v in voci[-5:]))
        corpo = ir.sezione(testo, "Ripartenza") or ir.sezione(testo, "Cosa stavamo facendo")
        corpo = "\n".join(r for r in corpo.splitlines() if not re.match(r"^\s*\**Prossimo passo", r))
        if corpo.strip():
            righe.append(f"    {corto(corpo, MAX_RIPARTENZA)}")
        prossimo = ir.prossimo_handoff(testo) or ir.prossimi_passi(testo)
        if prossimo:
            righe.append(f"    Prossimo passo: {corto(prossimo, 300)}")
    if len(recenti) > 5:
        righe.append(f"  … e altri {len(recenti) - 5} handoff recenti")
    righe.append(f"  da leggere per intero: {elenco[0][3]}")
    return righe


def riga_todo(t: dict, con_progetto: bool = False) -> str:
    # .get: una fonte esterna può non avere tutti i campi dell'archivio di Arturo
    pezzi = [f"#{t.get('id')} {t.get('titolo', '')}"]
    if con_progetto:
        pezzi.append(t.get("progetto", ""))
    if t.get("scadenza_testo"):
        pezzi.append(t["scadenza_testo"])
    if t.get("priorita") == "alta":
        pezzi.append("priorità alta")
    if t.get("perche"):
        pezzi.append(f"perché: {t['perche']}")
    if t.get("stato") == "fermo" and t.get("motivo"):
        pezzi.append(f"aspetta: {t['motivo']}")
    if t.get("attende"):
        pezzi.append("dopo " + ", ".join(f"#{n}" for n in t["attende"]))
    if t.get("stato") == "in corso":
        pezzi.append("in corso")
    return "    " + " · ".join(pezzi)


def sezione_todo(todo: dict, progetto: str, dal: str | None) -> list:
    v = ts.vista(todo, [], progetto=progetto)
    aperti = sum(len(g["todo"]) for g in v["gruppi"])
    righe = []
    # La riga di stato scritta dall'ultima /fine (arturo todo stato), prima dei todo.
    stato = ts.stati().get(progetto)
    if stato:
        righe += [f"STATO DEL PROGETTO (scritto il {stato['ts'][:10]})", f"    {stato['riga']}", ""]
    righe.append(f'TODO APERTI DEL PROGETTO "{progetto}" ({aperti})')
    if not aperti:
        righe.append("  nessuno")
    for g in v["gruppi"]:
        if g["todo"]:
            righe.append(f"  {ETICHETTE.get(g['tipo'], g['titolo'])}")
            righe += [riga_todo(t) for t in g["todo"]]

    fermi = ts.fermi_da(todo, progetto, GIORNI_FERMI)
    if fermi:
        # Proposta n. 52: /inizio li dice in una riga anche con un compito e in rotazione (inizio.md).
        righe += ["", f"FACCIO IO FERMI DA PIÙ DI {GIORNI_FERMI} GIORNI ({len(fermi)})"]
        righe += [f"    #{t['id']} {t['titolo']} · fermo da {g} g" for t, g in fermi]

    if dal:
        chiusi = sorted((t for t in todo.values() if t["progetto"] == progetto and t["chiuso"]
                         and t["chiuso"][:10] >= dal), key=lambda t: t["chiuso"])
        if chiusi:
            righe += ["", f"CHIUSI DAL GIORNO DELL'ULTIMO HANDOFF ({dal})"]
            righe += [f"    #{t['id']} {t['titolo']} · {t['stato']} il {t['chiuso'][:10]}" for t in chiusi]

    vicine = []
    for t in todo.values():
        if t["stato"] in ts.APERTI and t["progetto"] in (progetto, "generale"):
            g = ts.giorni(t)
            if g is not None and g <= GIORNI_SCADENZE:
                vicine.append((g, ts.esporta(t, todo)))
    if vicine:
        righe += ["", f'SCADENZE (scadute o entro {GIORNI_SCADENZE} giorni, anche di "generale")']
        righe += [riga_todo(t, con_progetto=True) for _, t in sorted(vicine, key=lambda x: (x[0], x[1]["id"]))]

    del_progetto = {u: t for u, t in todo.items() if t["progetto"] == progetto}
    partenza = ts.da_dove(del_progetto)
    if partenza:
        titolo = next(t["titolo"] for t in del_progetto.values() if t["id"] == partenza["id"])
        righe += ["", "DA DOVE PARTIRE", f"    #{partenza['id']} {titolo}: {partenza['motivo']}"]
    return righe


def leggi_esterna(progetto: str) -> tuple:
    """(vista, errore) dalla fonte esterna, con lo stesso comando che userebbe la persona."""
    try:
        r = subprocess.run([sys.executable, str(QUI / "arturo"), "todo", "--progetto", progetto, "--json", "--tutti"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90)
    except (OSError, subprocess.SubprocessError) as e:
        return None, str(e)
    if r.returncode != 0:
        righe = [x for x in (r.stderr + r.stdout).splitlines() if x.strip()]
        return None, f"exit {r.returncode}" + (f": {righe[-1][:160]}" if righe else "")
    try:
        v = json.loads(r.stdout)
    except ValueError:
        return None, "risposta non in JSON"
    if not isinstance(v, dict) or not isinstance(v.get("gruppi"), list):
        return None, "JSON senza \"gruppi\""
    return v, None


def sezione_esterna(v: dict, progetto: str, dal: str | None) -> list:
    gruppi = [g for g in v["gruppi"] if isinstance(g, dict)]
    aperti = sum(len(g.get("todo") or []) for g in gruppi)
    righe = [f'TODO APERTI DEL PROGETTO "{progetto}" ({aperti}, dalla fonte di {ts.nome_fonte()})']
    if not aperti:
        righe.append("  nessuno")
    for g in gruppi:
        if g.get("todo"):
            righe.append(f"  {ETICHETTE.get(g.get('tipo'), g.get('titolo') or g.get('tipo') or '')}")
            righe += [riga_todo(t) for t in g["todo"] if isinstance(t, dict)]
    chiusi = [t for t in v.get("chiusi_todo") or []
              if isinstance(t, dict) and dal and str(t.get("chiuso") or "")[:10] >= dal]
    if chiusi:
        righe += ["", f"CHIUSI DAL GIORNO DELL'ULTIMO HANDOFF ({dal})"]
        righe += [f"    #{t.get('id')} {t.get('titolo', '')} · {t.get('stato', '')} il {str(t.get('chiuso'))[:10]}"
                  for t in chiusi]
    return righe


def sezione_non_verificata(elenco: list, ir, errore: str) -> list:
    """I task della tabella dell'ultimo handoff, quando la fonte esterna non risponde."""
    righe = [f"TODO NON VERIFICATO: la fonte dei task non risponde ({errore}). Questi sono i task pendenti "
             "dell'ultimo handoff: possono essere già chiusi o cambiati."]
    if not elenco:
        return righe + ["  nessun handoff da cui leggerli"]
    nome, _, _, percorso = elenco[0]
    try:
        testo = percorso.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return righe + [f"  {nome} non si legge"]
    testa, trovati = None, 0
    for riga in ir.sezione(testo, "Task Pendenti").splitlines():
        if not riga.lstrip().startswith("|"):
            continue
        c = ir.celle(riga)
        if testa is None:
            testa = [x.lower() for x in c]
            continue
        if set("".join(c)) <= set("-: "):
            continue
        campo = dict(zip(testa, c))
        ident = next((x for x in c if re.fullmatch(r"#\d+|OFFLINE", x)), "")
        trovati += 1
        righe.append(f"    {ident} {campo.get('task', ' '.join(c))} · Chi: {c[-1] if c else ''}")
    return righe + ([] if trovati else ["  nessuna riga nella tabella Task Pendenti"]) + [f"  da {nome}"]


def riga_quota(adesso: float | None = None) -> str | None:
    """La quota condivisa fra tutte le sessioni, come l'ha vista la barra in basso (proposta n. 54, #4771).

    La scrive hooks/statusline.js in cache/statusline/quota.json. Una finestra già azzerata o senza
    orario non si stampa: il numero sarebbe vecchio. Senza file, o senza dati validi, niente riga.
    """
    radice = str(radice_orsa())
    try:
        dati = json.loads((Path(radice) / "cache" / "statusline" / "quota.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(dati, dict):
        return None
    adesso = dt.datetime.now().timestamp() if adesso is None else adesso
    pezzi = []
    for chiave, nome, formato in (("cinque_ore", "5 ore", "%H:%M"), ("settimana", "settimana", "%d/%m %H:%M")):
        q = dati.get(chiave)
        if not isinstance(q, dict):
            continue
        pct, resets = q.get("pct"), q.get("resets")
        if isinstance(pct, bool) or not isinstance(pct, int):
            continue
        if isinstance(resets, bool) or not isinstance(resets, (int, float)) or resets <= adesso:
            continue
        pezzi.append(f"{nome} al {pct}%, si azzera {dt.datetime.fromtimestamp(resets).strftime(formato)}")
    return "quota: " + " · ".join(pezzi) if pezzi else None


def sezione_filoni(progetto: str, ir) -> list:
    """I filoni di tutti gli handoff del progetto, non solo degli ultimi giorni: /fine riusa questi nomi
    nella riga "- Filone:", così un filone non si spezza in due."""
    try:
        tutti = [h for h in ir.elenca(handoff_dir()) if h["slug"] == progetto]
    except Exception:  # noqa: BLE001 - i filoni sono un aiuto, non fermano il contesto
        return []
    if not tutti:
        return []
    righe = ["", 'FILONI NOTI (/fine riusa questi nomi nella riga "- Filone:")']
    for chiave, gruppo in sorted(ir.per_chiave(tutti).items()):
        nome = ir.filone_esplicito(gruppo[0]["testo"]) or progetto
        righe.append(f'  {nome} · {len(gruppo)} handoff, ultimo {gruppo[0]["data"]} {gruppo[0]["ora"]}')
    return righe


MAX_SCHEDA = 3000  # caratteri: la scheda di un progetto grande non deve mangiare todo e avvisi
RIGHE_SCHEDA = 40


def memoria():
    """Il modulo melchior_match se la memoria è accesa, altrimenti None. Una sua rottura non ferma /inizio."""
    try:
        import melchior_match as mm
        return mm if mm.memoria_accesa() else None
    except Exception:
        return None


def scheda_progetto(*nomi: str):
    """(percorso, frontmatter, corpo) della scheda progetto-<slug>.md per il primo nome che la trova, o None.
    La scrive /fine con arturo memoria scheda (M3 del piano della memoria, 14/11/2026)."""
    mm = memoria()
    if mm is None:
        return None
    for nome in nomi:
        try:
            p = mm.trova_scheda(slug(nome)) if nome and slug(nome) else None
            if p:
                fm, corpo = mm.frontmatter(mm.leggi(p))
                return p, fm or {}, corpo or ""
        except Exception:
            continue
    return None


def cartella_da_scheda(scheda) -> Path | None:
    """La cartella scritta nella scheda, se c'è su questo computer: /inizio la trova anche fuori da
    Documents e Projects, aperto dalla home."""
    if not scheda:
        return None
    valore = str(scheda[1].get("cartella") or "").strip().strip("\"'")
    if not valore:
        return None
    c = Path(os.path.expanduser(valore))
    try:
        return c.resolve() if e_cartella(c) and c.resolve() != Path.home().resolve() else None
    except OSError:
        return None


def sezione_scheda(scheda) -> list:
    if not scheda:
        return []
    p, _, corpo = scheda
    try:
        breve = "~/" + p.resolve().relative_to(Path.home().resolve()).as_posix()
    except (OSError, ValueError):
        breve = str(p)
    righe = [r.rstrip() for r in corpo.strip("\n").splitlines()]
    tenute, n = [], 0
    for r in righe:
        if len(tenute) >= RIGHE_SCHEDA or n + len(r) > MAX_SCHEDA:
            break
        tenute.append(r)
        n += len(r) + 1
    fuori = [f"SCHEDA DEL PROGETTO (memoria, {breve})"] + [f"  {r}" if r else "" for r in tenute]
    if len(tenute) < len(righe):
        fuori.append(f"  … altre {len(righe) - len(tenute)} righe: leggi il file")
    return fuori


def sezione_intervista() -> list:
    """La domanda dell'intervista che continua (bin/intervista.py, #5709): al massimo una al giorno, mai in
    rotazione, dove nessuno risponde. È l'unica scrittura di contesto: il segno della domanda fatta oggi in
    data/intervista/stato.json. Una sua rottura non ferma /inizio."""
    try:
        import intervista
        d = intervista.proponi()
        return ["", *intervista.righe_contesto(d)] if d else []
    except Exception:
        return []


def sezione_spazio() -> list:
    """La proposta di uno spazio (bin/spazi.py, #5711): Volta, Melchior o l'Orsa, una volta sola e col segnale
    che l'ha fatta nascere. Mai in rotazione, e mai lo stesso giorno della domanda dell'intervista: una
    richiesta sola per /inizio. Scrive il segno della proposta in data/spazi/stato.json. Una sua rottura non
    ferma /inizio."""
    try:
        import spazi
        s = spazi.proponi()
        return ["", *spazi.righe_contesto(s)] if s else []
    except Exception:
        return []


def compito_da(argv: list) -> tuple:
    """(compito, rotazione). Il compito sono le parole dopo " -- ". Se la prima è --rotazione, è la marca
    della rotazione automatica (3/11/2026: "/inizio <slug> -- --rotazione <compito>") e non fa parte del
    compito. Prima di " -- " --rotazione resta un'opzione sconosciuta, rifiutata da leggi_argomenti."""
    parti = re.split(r"(?:^|\s)--(?:\s|$)", " ".join(argv), maxsplit=1)
    parole = parti[1].split() if len(parti) > 1 else []
    rotazione = parole[:1] == ["--rotazione"]
    if rotazione:
        parole = parole[1:]
    return " ".join(parole), rotazione


def separa_attesa(compito: str) -> tuple:
    """(compito, domanda). Il mod della rotazione mette " --in-attesa <domanda>" in fondo quando la sessione
    vecchia ha fatto una domanda alla persona dopo ruota (segnalazione n. 65, 10/11/2026)."""
    parti = re.split(r"(?:^|\s)--in-attesa(?:\s|$)", compito, maxsplit=1)
    return parti[0].strip(), (parti[1].strip() if len(parti) > 1 else "")


def fonte(id_: str, titolo: str, perche: str, percorso: Path | None, testo: str | None = None, voci: int | None = None) -> dict:
    """Una fonte del contesto per `--json`: il file (o il testo già pronto), la data, il peso, le prime righe."""
    out = {"id": id_, "titolo": titolo, "perche": perche, "percorso": str(percorso) if percorso else None, "presente": False}
    try:
        if testo is None and percorso is not None and percorso.is_file():
            testo = percorso.read_text(encoding="utf-8", errors="replace")
            out["data"] = dt.datetime.fromtimestamp(percorso.stat().st_mtime).isoformat(timespec="seconds")
    except OSError:
        testo = None
    if testo is None:
        return out
    righe = [r.rstrip() for r in testo.splitlines()]
    out.update({"presente": True, "caratteri": len(testo), "righe": len(righe),
                "anteprima": [corto(r, 140) for r in righe if r.strip()][:6]})
    if voci is not None:
        out["voci"] = voci
    return out


def collegate(scheda: Path | None, radici: list) -> list:
    """Le note che la scheda del progetto collega con [[nome]], trovate nelle radici della memoria."""
    if not scheda or not scheda.is_file():
        return []
    nomi = []
    for n in re.findall(r"\[\[([^\]|#]+)", scheda.read_text(encoding="utf-8", errors="replace")):
        n = n.strip()
        if n and n not in nomi:
            nomi.append(n)
    out = []
    for n in nomi[:40]:
        for r in radici:
            try:
                f = next((x for x in r.rglob(f"{n}.md") if not any(p[:1] in "._" for p in x.relative_to(r).parts)), None)
            except OSError:
                f = None
            if f:
                out.append(f)
                break
    return out


def contesto_json(nome: str) -> dict:
    """Come si forma il contesto di un progetto, per la finestra di Volta (12/11/2026): le
    fonti nell'ordine in cui una sessione aperta con /inizio le legge. Sola lettura, come il resto."""
    prog = importlib.util.spec_from_file_location("progetti_arturo", str(QUI / "progetti.py"))
    pm = importlib.util.module_from_spec(prog)
    prog.loader.exec_module(pm)
    if nome:
        nome = risolvi_nome(nome)[0]
    cartella, _ = trova_cartella(nome)
    s = slug(cartella.name) if cartella else slug(nome)
    # uno spazio di Volta col nome alternativo ("volta" per herdr-arturo) lo porta già risolvi_nome, con
    # gli alias delle schede (nomi_vecchi)
    tutte = pm.schede() if s else {}
    radice = radice_orsa()
    base = base_progetti()
    chiave_base = re.sub(r"[^A-Za-z0-9]", "-", str(base))
    scheda = pm.scheda_di(s) if s else None
    elenco = handoff_di(s)
    # quello che /inizio stampa nella FASE 1: lo stesso comando, in testo
    try:
        r = subprocess.run([sys.executable, str(Path(__file__).resolve()), s], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=60, cwd=str(base) if base.is_dir() else None)
        inizio = r.stdout if r.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        inizio = None
    fonti = [
        fonte("globale", "Istruzioni di tutte le sessioni", "Il tuo CLAUDE.md: Claude lo legge all'avvio di ogni sessione.", radice / "CLAUDE.md"),
        fonte("indice", "Indice della memoria", "MEMORY.md: l'elenco delle note che Claude ha sempre davanti.",
              radice / "projects" / chiave_base / "memory" / "MEMORY.md"),
        fonte("progetto", "Istruzioni del progetto", "Il CLAUDE.md nella cartella del progetto.", (cartella / "CLAUDE.md") if cartella else None),
        fonte("scheda", "Scheda del progetto", "La nota progetto-" + (s or "…") + ".md: cos'è, dove sta, le decisioni.", scheda),
        fonte("inizio", "Quadro di /inizio", "Quello che stampa arturo contesto: git, ripartenza, todo per chi agisce, scadenze.", None, inizio),
        fonte("handoff", "Ultimo handoff", "Il salvataggio dell'ultimo /fine, letto per intero da /inizio.", elenco[0][3] if elenco else None),
    ]
    for f in collegate(scheda, pm.radici_memoria()):
        fonti.append(fonte("nota-" + f.stem, f.stem, "Nota collegata dalla scheda: entra se Claude la apre.", f))
    titolo = (tutte.get(s) or {}).get("titolo") if s else None
    return {"versione": 1, "progetto": {"slug": s, "titolo": titolo or (cartella.name if cartella else s), "cartella": str(cartella) if cartella else None},
            "fonti": fonti, "avvisi": [] if (cartella or elenco or scheda) else [f'Nessuna cartella, scheda o handoff per "{nome}".']}


def main(argv: list) -> int:
    if argv and argv[0] in ("-h", "--help", "aiuto", "help"):
        print(__doc__.strip())
        return 0
    if "--json" in argv:
        nome = " ".join(a for a in argv if a != "--json").strip()
        print(json.dumps(contesto_json(nome), ensure_ascii=False))
        return 0
    if argv and argv[0] == "--stdin":
        # Gli argomenti di /inizio arrivano da un heredoc: la shell non li tocca (#4291, inizio.md).
        argv = [sys.stdin.read(), *argv[1:]]
    compito, rotazione = compito_da(argv)
    compito, attesa = separa_attesa(compito) if rotazione else (compito, "")
    try:
        nome, giorni = leggi_argomenti(argv)
    except ValueError as e:
        print(f"contesto: {e}", file=sys.stderr)
        return 3
    if nome and not slug(nome):
        print(f'contesto: nome non valido: "{nome}"', file=sys.stderr)
        return 3
    interpretato = None
    if nome:
        nome, resto, interpretato = risolvi_nome(nome)
        compito = " ".join(x for x in (resto, compito) if x)

    cartella, contenitore = trova_cartella(nome)
    scheda = None
    if not contenitore:
        if nome and not cartella:  # la cartella scritta nella scheda vale anche fuori dalla base dei progetti
            scheda = scheda_progetto(nome)
            cartella = cartella_da_scheda(scheda)
    s = slug(cartella.name) if cartella else slug(nome)
    if not contenitore and not scheda:
        scheda = scheda_progetto(s, nome)
    elenco = handoff_di(s)
    dal = elenco[0][1] if elenco else None
    esterna = ts.comando_fonte()
    # La fonte esterna dei todo (rete, fino a 90 s) e git non leggono l'una il risultato dell'altro: girano
    # insieme, e /inizio aspetta la più lenta invece della somma (#6317).
    letta: dict = {}
    lettore = threading.Thread(target=lambda: letta.update(r=leggi_esterna(s)), daemon=True) if esterna else None
    if lettore:
        lettore.start()
    righe_git = [] if contenitore else (sezione_git(cartella, dal) if cartella else ["GIT", "  nessuna cartella"])
    if lettore:
        lettore.join()
    vista, errore = letta.get("r", (None, "lettura dei todo interrotta")) if esterna else (None, None)
    if esterna:
        todo, avvisi = {}, []
        ha_todo = bool(vista and any(g.get("todo") for g in vista["gruppi"] if isinstance(g, dict)))
    else:
        todo, avvisi = ts.carica()
        ha_todo = any(t["progetto"] == s for t in todo.values())

    if contenitore or not (cartella or elenco or ha_todo or scheda):
        motivo = ("la cartella in cui sei contiene i progetti, non è un progetto" if contenitore
                  else f'nessuna cartella, nessun handoff e nessun todo per "{nome}"')
        print(f"NON TROVATO: {motivo}")
        if interpretato:
            print(f"NOME: {interpretato}")
        if compito:
            print(f"compito: {compito}")
        simili = candidati(nome)
        print("Progetti simili: " + (", ".join(simili) if simili else "nessuno"))
        print(f"Cercato in: ./  {base_progetti()}/  ~/Documents/  ~/Projects/  ~/")
        return 2

    ir = modulo_index()
    righe = [f"PROGETTO {s}", f"cartella: {cartella if cartella else 'nessuna'}"]
    if interpretato:
        # Il consiglio di ripetere col nome giusto vale per un nome interpretato, non per una frase che è
        # tutta compito (2/11/2026, #4481).
        consiglio = " Se è un altro progetto, ripeti /inizio col nome giusto." if interpretato.startswith("interpretato") else ""
        righe.append(f"NOME: {interpretato}.{consiglio}")
    if compito:
        righe.append(f"compito: {compito}")
    if rotazione:
        righe.append("rotazione: sì (sessione aperta dalla rotazione automatica)")
    if attesa:
        righe.append(f"in attesa: {attesa}")
    if not rotazione and (Path.home() / ".config" / "herdr-app").is_dir():
        # La checklist della ripartenza la legge solo Volta: senza la sua cartella /inizio non la scrive (A9).
        righe.append("VOLTA: sì, passa la ripartenza alla checklist con arturo ripartenza scrivi")
    quota = riga_quota()
    if quota:
        righe.append(quota)
    if cartella:
        vecchi = sorted(cartella.glob("HANDOFF_*.md"), key=lambda p: p.name, reverse=True)
        if vecchi and (not elenco or vecchi[0].name > elenco[0][0]):
            righe.append(f"handoff nella cartella del progetto, più recente dello store: {vecchi[0]}")
    righe.append("")
    if scheda:
        righe += sezione_scheda(scheda) + [""]
    righe += righe_git
    righe.append("")
    righe += sezione_handoff(elenco, giorni, ir)
    righe.append("")
    if not esterna:
        righe += sezione_todo(todo, s, dal)
    elif vista:
        righe += sezione_esterna(vista, s, dal)
    else:
        righe += sezione_non_verificata(elenco, ir, errore)
    if not rotazione:
        domanda = sezione_intervista()
        righe += domanda or sezione_spazio()
    if avvisi:
        righe += ["", "AVVISI"] + [f"  Attenzione: {a}" for a in avvisi]
    righe += sezione_filoni(s, ir)
    testo = "\n".join(righe)
    if len(testo) > MAX_CARATTERI:
        # Un'uscita lunga finisce troncata dal tool e /inizio perde la coda (todo, avvisi): meglio tagliare
        # qui e dirlo.
        testo = testo[:MAX_CARATTERI].rsplit("\n", 1)[0] + (
            f"\nTAGLIATO: il contesto supera {MAX_CARATTERI} caratteri. Riduci i giorni con --giorni.")
    print(testo)
    return 0


if __name__ == "__main__":
    for flusso in (sys.stdout, sys.stderr):
        try:
            flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    raise SystemExit(main(sys.argv[1:]))
