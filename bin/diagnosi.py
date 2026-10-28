#!/usr/bin/env python3
"""arturo diagnosi: due controlli su un progetto intero, in sola lettura (/diagnosi).

Uso: arturo diagnosi percorsi [nome] [--json]
     arturo diagnosi materiali [nome] [--json]
  Senza nome usa la cartella in cui sei, se sta sotto la cartella dei progetti (PROJECTS_BASE).

percorsi   legge i percorsi di file scritti nella sezione "## File e materiali" degli handoff del
           progetto e nella sezione "Materiali" del suo CLAUDE.md. Le righe hanno forma
           "- descrizione → percorso", col percorso anche tra backtick e con ~. URL, link e destini
           che non sono file ("resta", "scarto", "link") non contano. Per ogni percorso che non
           esiste più stampa "MANCA: <percorso> (da <file>)", in fondo "OK <n> presenti, <m> mancanti".
materiali  trova i file del progetto sparsi e propone un destino (repo, archivia, resta, scarto):
           in Download e Scrivania i file col nome del progetto o citati per nome dagli handoff,
           nella cartella del progetto i file non tracciati e non ignorati da git, dentro git i
           file tracciati sopra 20 MB. Propone soltanto: non sposta e non cancella niente.

Exit: percorsi 0 nessuno manca · 1 ne manca almeno uno. materiali 0 sempre.
      Entrambi: 2 progetto non trovato · 3 uso sbagliato.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

QUI = Path(os.path.realpath(__file__)).parent
sys.path.insert(0, str(QUI))
from contesto import base_progetti, candidati, handoff_di, slug, trova_cartella  # noqa: E402

SOTTOCOMANDI = ("percorsi", "materiali")
NON_FILE = {"resta", "scarto", "scartato", "scartati", "link"}
RE_TITOLO = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
RE_URL = re.compile(r"^(?:[a-z][a-z0-9+.-]*://|www\.|mailto:)", re.I)
RE_ASSOLUTO = re.compile(r"(?:~[/\\]|/|[A-Za-z]:[/\\])")
RE_TOKEN = re.compile(r"(?:(?<=\s)|^)(~[/\\][^\s`]*|/[^\s`]+|[A-Za-z]:[/\\][^\s`]*)")
# Cache, dipendenze, build e le copie di lavoro di Claude Code: si rigenerano, o sono un altro
# checkout. Non vanno nel repository (segnalazione n. 22, 27/10/2026).
RIGENERABILI = {"__pycache__", "node_modules", ".venv", "venv", "dist", ".pytest_cache", ".mypy_cache",
                ".ruff_cache", ".DS_Store"}
WORKTREE = (".claude/worktrees/", ".claude/worktrees")


def rigenerabile(rel: str) -> bool:
    rel = rel.replace("\\", "/")
    return rel.startswith(WORKTREE) or any(parte in RIGENERABILI for parte in rel.split("/"))


def assoluto_scritto(p: str) -> bool:
    """~/…, C:\\… oppure /a/b: "/fine" da solo è un comando, non un file."""
    return bool(RE_ASSOLUTO.match(p)) and (not p.startswith("/") or p.count("/") >= 2)


def inventario():
    """bin/inventario-sessione.py: il nome ha il trattino, si carica dal file."""
    spec = importlib.util.spec_from_file_location("inventario_sessione", str(QUI / "inventario-sessione.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --- il progetto ---------------------------------------------------------------------------------

def sotto_di(p: Path, radice: Path) -> bool:
    try:
        p.relative_to(radice)
        return True
    except ValueError:
        return False


def progetto(nome: str) -> tuple:
    """(slug, cartella o None, motivo se non trovato)."""
    if not nome:
        cwd, pb = Path.cwd().resolve(), base_progetti()
        pb = pb.resolve() if pb.exists() else pb
        if cwd == pb or not sotto_di(cwd, pb):
            return "", None, f"la cartella in cui sei non è un progetto sotto {pb}: scrivi il nome"
        cartella = pb / cwd.relative_to(pb).parts[0]
        return slug(cartella.name), cartella, ""
    cartella, _ = trova_cartella(nome)
    s = slug(cartella.name) if cartella else slug(nome)
    if cartella or handoff_di(s):
        return s, cartella, ""
    return s, None, f'nessuna cartella e nessun handoff per "{nome}"'


# --- percorsi ------------------------------------------------------------------------------------

def sezione(testo: str, vale) -> list:
    """Le righe delle sezioni il cui titolo soddisfa vale(titolo minuscolo), fuori dai blocchi di codice."""
    righe, livello, codice = [], 0, False
    for r in testo.splitlines():
        if r.lstrip().startswith("```"):
            codice = not codice
            if livello:
                continue
        m = None if codice else RE_TITOLO.match(r)
        if m:
            if livello and len(m.group(1)) <= livello:
                livello = 0
            if not livello and vale(m.group(2).lower()):
                livello = len(m.group(1))
            continue
        if livello and not codice:
            righe.append(r)
    return righe


def da_msys(p: str) -> str:
    """Su Windows Git Bash scrive /c/Users/...: per Python è C:/Users/..."""
    m = re.match(r"^/([A-Za-z])(/.*)?$", p)
    if os.name == "nt" and m:
        return f"{m.group(1).upper()}:{m.group(2) or '/'}"
    return p


def pulito(p: str) -> str:
    p = p.strip().strip("\"'")
    while p and p[-1] in ".,;:" and not p.endswith(".."):
        p = p[:-1]
    if p.endswith(")") and p.count("(") < p.count(")"):
        p = p[:-1]
    return p


def candidati_riga(riga: str) -> list:
    """I percorsi scritti in una riga di elenco: dopo la freccia se c'è, tra backtick o assoluti."""
    testo = re.sub(r"^\s*(?:[-*+]|\d+[.)])\s+", "", riga).strip()
    if not testo:
        return []
    freccia = "→" in testo
    if freccia:
        testo = testo.split("→", 1)[1].strip()
        prima = re.sub(r"[^\w']+$", "", testo.split(" ", 1)[0].lower()) if testo else ""
        if not testo or prima in NON_FILE or testo.startswith("["):
            return []
    tra_backtick = re.findall(r"`([^`]+)`", testo)
    if tra_backtick:
        trovati = [pulito(x) for x in tra_backtick]
        # tra backtick vale anche un percorso relativo alla cartella del progetto
        return [x for x in trovati if x and not re.search(r"[*?]", x) and (assoluto_scritto(x) or (
            not x.startswith("/") and " " not in x and ("/" in x or re.search(r"\.\w{1,5}$", x))))]
    if freccia:
        # fuori dai backtick il percorso finisce al primo ", ", " (", " — ", " → " o spazio
        pezzo = re.split(r",\s|\s\(|\s—\s|\s→\s", testo, maxsplit=1)[0]
        pezzo = pulito(pezzo.split()[0]) if pezzo.strip() else ""
        return [pezzo] if assoluto_scritto(pezzo) else []
    return [x for x in (pulito(y) for y in RE_TOKEN.findall(testo)) if assoluto_scritto(x)]


def assoluto(p: str, cartella: Path | None) -> Path | None:
    p = da_msys(p)
    if p == "~" or p.startswith(("~/", "~\\")):
        return Path(str(Path.home()) + p[1:])
    q = Path(p)
    if q.is_absolute() or RE_ASSOLUTO.match(p):
        return q
    return (cartella / q) if cartella else None


def fonti_percorsi(s: str, cartella: Path | None) -> list:
    """(nome del file, testo, righe) delle fonti: gli handoff dal più recente, poi il CLAUDE.md."""
    out = []
    for nome, _, _, f in handoff_di(s):
        testo = f.read_text(encoding="utf-8", errors="replace")
        out.append((nome, testo, sezione(testo, lambda t: t.startswith("file e materiali"))))
    if cartella and (cartella / "CLAUDE.md").is_file():
        testo = (cartella / "CLAUDE.md").read_text(encoding="utf-8", errors="replace")
        out.append(("CLAUDE.md", testo, sezione(testo, lambda t: "materiali" in t)))
    return out


def percorsi(s: str, cartella: Path | None) -> dict:
    visti, presenti, mancanti = set(), [], []
    for nome, _, righe in fonti_percorsi(s, cartella):
        for r in righe:
            for scritto in candidati_riga(r):
                if RE_URL.match(scritto) or "](" in scritto:
                    continue
                a = assoluto(scritto, cartella)
                if a is None:
                    continue
                chiave = os.path.normcase(os.path.normpath(str(a)))
                if chiave in visti:
                    continue
                visti.add(chiave)
                voce = {"percorso": scritto, "assoluto": str(a), "da": nome}
                (presenti if a.exists() else mancanti).append(voce)
    return {"progetto": s, "cartella": str(cartella) if cartella else None,
            "presenti": presenti, "mancanti": mancanti}


def stampa_percorsi(esito: dict) -> None:
    righe = [f"PERCORSI DEL PROGETTO {esito['progetto']}"]
    righe += [f"MANCA: {m['percorso']} (da {m['da']})" for m in esito["mancanti"]]
    righe.append(f"OK {len(esito['presenti'])} presenti, {len(esito['mancanti'])} mancanti")
    print("\n".join(righe))


# --- materiali -----------------------------------------------------------------------------------

def git(cartella: Path, *argomenti: str):
    try:
        r = subprocess.run(["git", "-c", "core.fsmonitor=false", "-C", str(cartella), *argomenti],
                           capture_output=True, timeout=60, env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"))
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.decode("utf-8", "replace") if r.returncode == 0 else None


def file_sparsi(inv, s: str, citati: str, home: str) -> list:
    """Download e Scrivania, fino a due livelli: col nome del progetto o citati dagli handoff."""
    out = []
    for radice in inv.cartelle_lavoro(home)[:2]:
        base = radice.count(os.sep)
        for d, sottocart, files in os.walk(radice):
            sottocart[:] = [x for x in sottocart if not x.startswith(".")
                            and not x.endswith((".app", ".photoslibrary", ".bundle"))]
            if d.count(os.sep) - base >= 2:
                sottocart[:] = []
            for x in sorted(files):
                if x.startswith(".") or x.endswith((".crdownload", ".part", ".download")):
                    continue
                dove = os.path.basename(radice)
                if s and f"-{s}-" in f"-{slug(x)}-":
                    out.append((os.path.join(d, x), f"in {dove}, col nome del progetto"))
                elif len(x) >= 5 and x in citati:
                    out.append((os.path.join(d, x), f"in {dove}, citato per nome dagli handoff"))
    return out


def file_progetto(cartella: Path) -> tuple:
    """(non tracciati, tracciati sopra 20 MB, avvisi) della cartella del progetto."""
    radice = git(cartella, "rev-parse", "--show-toplevel")
    if radice is None:
        return [], [], ["la cartella del progetto non è un repository git: i file non tracciati non si vedono"]
    radice = Path(radice.strip())
    stato = git(cartella, "status", "--porcelain=v1", "-z", "--untracked-files=all", "--", ".")
    tracciati = git(cartella, "ls-files", "-z", "--full-name", "--", ".")
    if stato is None or tracciati is None:
        return [], [], ["git non risponde nella cartella del progetto"]
    tutti = [v[3:] for v in stato.split("\0") if v.startswith("?? ")]
    nuovi = [str(radice / v) for v in tutti if not rigenerabile(v)]
    avvisi = []
    if len(nuovi) < len(tutti):
        avvisi.append(f"{len(tutti) - len(nuovi)} file di cache, dipendenze o worktree non tracciati restano fuori "
                      "dalle proposte: non vanno nel repository, mettili nel .gitignore")
    pesanti = []
    for rel in (x for x in tracciati.split("\0") if x):
        p = radice / rel
        try:
            if p.is_file() and p.stat().st_size > 20 * 1024 * 1024:
                pesanti.append(str(p))
        except OSError:
            continue
    return nuovi, pesanti, avvisi


def materiali(s: str, cartella: Path | None) -> dict:
    inv, home = inventario(), os.path.normpath(str(Path.home()))
    citati = "\n".join(testo for _, testo, _ in fonti_percorsi(s, None))
    trovati, avvisi = [], []
    for p, origine in file_sparsi(inv, s, citati, home):
        trovati.append((p, origine, None, None))
    if cartella:
        nuovi, pesanti, avvisi = file_progetto(cartella)
        radice = str(cartella)
        trovati += [(p, "nel progetto, non tracciato da git", radice, "non tracciato") for p in nuovi]
        trovati += [(p, "tracciato da git e sopra 20 MB", None, None) for p in pesanti]
    voci = []
    for p, origine, repo, stato in trovati:
        byte = inv.dimensione(p)
        f = {"path": p, "tipo": inv.tipo_file(p, byte), "repo": repo, "git": stato, "volatile": False}
        if f["tipo"] == "binario pesante":
            f["repo"] = None        # un file pesante non va in un commit: resta, col path nel CLAUDE.md
        destino, motivo = inv.proponi(f, home)
        voci.append({"path": p, "destino": destino, "origine": origine, "motivo": motivo,
                     "tipo": f["tipo"], "byte": byte})
    return {"progetto": s, "cartella": str(cartella) if cartella else None, "file": voci, "avvisi": avvisi}


def stampa_materiali(esito: dict) -> None:
    home = os.path.normpath(str(Path.home()))
    corto = lambda p: "~" + p[len(home):] if p == home or p.startswith(home + os.sep) else p  # noqa: E731
    righe = [f"MATERIALI DEL PROGETTO {esito['progetto']} ({len(esito['file'])} file)"]
    if esito["file"]:
        largo = max(len(corto(v["path"])) for v in esito["file"])
        righe.append(f"  {'DESTINO':<9} | {'PATH':<{largo}} | perché")
        for v in esito["file"]:
            righe.append(f"  {v['destino']:<9} | {corto(v['path']):<{largo}} | {v['origine']} · {v['motivo']}")
    else:
        righe.append("  nessun file sparso")
    righe += [f"  Attenzione: {a}" for a in esito["avvisi"]]
    righe.append("Solo proposte: niente è stato spostato né cancellato.")
    print("\n".join(righe))


# --- ingresso ------------------------------------------------------------------------------------

def main(argv: list) -> int:
    if not argv or argv[0] in ("-h", "--help", "aiuto", "help"):
        print(__doc__.strip())
        return 0 if argv else 3
    comando, resto = argv[0], argv[1:]
    if comando not in SOTTOCOMANDI:
        print(f'diagnosi: sottocomando sconosciuto "{comando}": usa percorsi o materiali', file=sys.stderr)
        return 3
    come_json = "--json" in resto
    parole = [p for p in resto if p != "--json"]
    strani = [p for p in parole if p.startswith("-")]
    if strani:
        print(f"diagnosi: opzione sconosciuta: {strani[0]}", file=sys.stderr)
        return 3
    nome = " ".join(parole)
    if nome and not slug(nome):
        print(f'diagnosi: nome non valido: "{nome}"', file=sys.stderr)
        return 3

    s, cartella, motivo = progetto(nome)
    if motivo:
        print(f"NON TROVATO: {motivo}")
        if nome:
            simili = candidati(nome)
            print("Progetti simili: " + (", ".join(simili) if simili else "nessuno"))
        return 2

    if comando == "percorsi":
        esito = percorsi(s, cartella)
        if come_json:
            print(json.dumps(esito, ensure_ascii=False, indent=2))
        else:
            stampa_percorsi(esito)
        return 1 if esito["mancanti"] else 0
    esito = materiali(s, cartella)
    if come_json:
        print(json.dumps(esito, ensure_ascii=False, indent=2))
    else:
        stampa_materiali(esito)
    return 0


if __name__ == "__main__":
    for flusso in (sys.stdout, sys.stderr):
        try:
            flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    raise SystemExit(main(sys.argv[1:]))
