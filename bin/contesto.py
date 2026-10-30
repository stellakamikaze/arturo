#!/usr/bin/env python3
"""arturo contesto: il contesto di un progetto per /inizio, in una chiamata e in sola lettura.

Uso: arturo contesto [nome] [--giorni N]
     arturo contesto --stdin          gli argomenti di /inizio su stdin, mai nella riga di comando: il
                                      compito può contenere virgolette, # e $(...) che la shell eseguirebbe
  Senza nome usa la cartella in cui sei. Accetta anche gli argomenti interi di /inizio:
  "--tutti" si ignora, e il testo dopo " -- " (il compito) non fa parte del nome.

Stampa, in quest'ordine: progetto e cartella, git (branch, modifiche, conflitti, commit dopo
l'ultimo handoff, rami locali non riportati), la ripartenza degli handoff degli ultimi N giorni (14), i todo aperti del
progetto divisi per chi agisce, i todo chiusi dopo l'ultimo handoff, le scadenze dei prossimi
7 giorni (anche fuori dal progetto), il todo da cui ripartire e gli avvisi.
Tra due blocchi bash le variabili si perdono: qui tutto vive in un processo.

Con bin/fonte-task.local i todo vengono dalla fonte esterna (arturo todo --progetto <slug> --json --tutti).
Se non risponde, la sezione dei todo mostra la tabella Task Pendenti dell'ultimo handoff con l'avviso
NON VERIFICATO: mai "nessuno" quando la fonte è giù.

Exit: 0 contesto stampato · 2 NON TROVATO (né cartella, né handoff, né todo; stampa i nomi
simili) · 3 uso sbagliato. Non scrive niente: niente pull, niente mkdir, niente todo.
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
from pathlib import Path

QUI = Path(os.path.realpath(__file__)).parent
sys.path.insert(0, str(QUI))
import todo_store as ts  # noqa: E402

GIORNI = 14
GIORNI_SCADENZE = 7
MAX_STATUS = 15
MAX_COMMIT = 15
MAX_RIPARTENZA = 700
MAX_CARATTERI = 28000
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
    return Path.home() / ".claude" / "data" / "handoffs"


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
    strani = [p for p in parole if p.startswith("-")]
    if strani:
        raise ValueError(f"opzione sconosciuta: {strani[0]}")
    return " ".join(parole), giorni


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
        if c.is_dir() and c != home:
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
    if not s or not d.is_dir():
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


def forti(pref: str, nomi) -> list:
    """I nomi che contengono il prefisso intero, o tutte le sue parole di 3 lettere o più."""
    parole = [p for p in pref.split("-") if len(p) >= 3]
    return sorted(n for n in nomi if pref in slug(n) or (len(parole) > 1 and all(p in slug(n) for p in parole)))


def risolvi_nome(nome: str) -> tuple:
    """(nome, resto, avviso). Il compito scritto subito dopo il nome, senza " -- ", resta fuori dal nome: si
    prova il prefisso più lungo che porta a un progetto. Se nessun prefisso ci porta, un candidato forte
    unico vale con l'avviso "interpretato" ("due mondi" per due-mondi-myway)."""
    parole = nome.split()
    prefissi = [(" ".join(parole[:k]), " ".join(parole[k:])) for k in range(len(parole), 0, -1)]
    for pref, resto in prefissi:
        if slug(pref) and (trova_cartella(pref)[0] or (handoff_dir() / slug(pref)).is_dir()):
            return pref, resto, None
    nomi = nomi_noti()
    for pref, resto in prefissi:
        f = forti(slug(pref), nomi) if slug(pref) else []
        if len(f) == 1:
            return f[0], resto, f'interpretato "{pref}" come {f[0]}'
        if f:
            break  # più candidati: un prefisso più corto ne darebbe di più
    return nome, "", None


def candidati(nome: str) -> list:
    nomi = nomi_noti()
    if not nome:
        return sorted(nomi)[:15]
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
        righe.append(f"{ramo} · {quanti} commit · ultimo {data}{dove}")
    return righe


def sezione_handoff(elenco: list, giorni: int, ir) -> list:
    if not elenco:
        return ["RIPARTENZA", "  nessun handoff per questo progetto"]
    limite = (ts.oggi() - dt.timedelta(days=giorni)).isoformat()
    recenti = [h for h in elenco if h[1] >= limite] or elenco[:1]
    titolo = f"RIPARTENZA (handoff degli ultimi {giorni} giorni)"
    if recenti[0][1] < limite:
        titolo = f"RIPARTENZA (nessun handoff negli ultimi {giorni} giorni: il più recente)"
    righe = [titolo]
    for nome, data, ora, percorso in recenti[:5]:
        testo = percorso.read_text(encoding="utf-8", errors="replace")
        filone = ir.filone_esplicito(testo)
        stato = ir.stato_handoff(testo)
        testa = f"  {data} {ora}" + (f" · filone {filone}" if filone else "") + (f" · {stato}" if stato else "")
        righe.append(f"{testa} · {nome}")
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
    righe = [f'TODO APERTI DEL PROGETTO "{progetto}" ({aperti})']
    if not aperti:
        righe.append("  nessuno")
    for g in v["gruppi"]:
        if g["todo"]:
            righe.append(f"  {ETICHETTE.get(g['tipo'], g['titolo'])}")
            righe += [riga_todo(t) for t in g["todo"]]

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
    righe = [f'TODO APERTI DEL PROGETTO "{progetto}" ({aperti}, dalla fonte di bin/fonte-task.local)']
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


def compito_da(argv: list) -> str:
    parti = re.split(r"(?:^|\s)--(?:\s|$)", " ".join(argv), maxsplit=1)
    return " ".join(parti[1].split()) if len(parti) > 1 else ""


def main(argv: list) -> int:
    if argv and argv[0] in ("-h", "--help", "aiuto", "help"):
        print(__doc__.strip())
        return 0
    if argv and argv[0] == "--stdin":
        # Gli argomenti di /inizio arrivano da un heredoc: la shell non li tocca (#4291, inizio.md).
        argv = [sys.stdin.read(), *argv[1:]]
    compito = compito_da(argv)
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
    s = slug(cartella.name) if cartella else slug(nome)
    elenco = handoff_di(s)
    esterna = ts.comando_fonte()
    vista, errore = (leggi_esterna(s) if esterna else (None, None))
    if esterna:
        todo, avvisi = {}, []
        ha_todo = bool(vista and any(g.get("todo") for g in vista["gruppi"] if isinstance(g, dict)))
    else:
        todo, avvisi = ts.carica()
        ha_todo = any(t["progetto"] == s for t in todo.values())

    if contenitore or not (cartella or elenco or ha_todo):
        motivo = ("la cartella in cui sei contiene i progetti, non è un progetto" if contenitore
                  else f'nessuna cartella, nessun handoff e nessun todo per "{nome}"')
        print(f"NON TROVATO: {motivo}")
        simili = candidati(nome)
        print("Progetti simili: " + (", ".join(simili) if simili else "nessuno"))
        print(f"Cercato in: ./  {base_progetti()}/  ~/Documents/  ~/Projects/  ~/")
        return 2

    ir = modulo_index()
    dal = elenco[0][1] if elenco else None
    righe = [f"PROGETTO {s}", f"cartella: {cartella if cartella else 'nessuna'}"]
    if interpretato:
        righe.append(f"NOME: {interpretato}. Se è un altro progetto, ripeti /inizio col nome giusto.")
    if compito:
        righe.append(f"compito: {compito}")
    if cartella:
        vecchi = sorted(cartella.glob("HANDOFF_*.md"), key=lambda p: p.name, reverse=True)
        if vecchi and (not elenco or vecchi[0].name > elenco[0][0]):
            righe.append(f"handoff nella cartella del progetto, più recente dello store: {vecchi[0]}")
    righe.append("")
    righe += sezione_git(cartella, dal) if cartella else ["GIT", "  nessuna cartella"]
    righe.append("")
    righe += sezione_handoff(elenco, giorni, ir)
    righe.append("")
    if not esterna:
        righe += sezione_todo(todo, s, dal)
    elif vista:
        righe += sezione_esterna(vista, s, dal)
    else:
        righe += sezione_non_verificata(elenco, ir, errore)
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
