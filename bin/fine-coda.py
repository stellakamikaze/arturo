#!/usr/bin/env python3
"""La coda di /fine in una chiamata: gate, retention, indice, commit e push della config (#4291, F0 L3).

Questi passi non chiedono giudizio, e ogni chiamata a un tool rilegge tutto il contesto di fine sessione:
qui girano in un processo solo. Il giudizio resta in /fine: destino dei file, handoff, scelta di cosa
salvare degli handoff in uscita (il dry-run della retention), memoria.

Uso:
  python3 ~/.claude/bin/fine-coda.py --handoff <path> --slug <slug> [--trailer <riga>] [-- <argomenti tuoi>]

Ordine dei passi:
  1. stop se ~/.claude è a metà di un rebase, o se hooks/controlla-config.py la trova rotta;
  2. gate (bin/handoff-gate.sh): rosso = niente commit;
  3. retention con --applica: escono solo i file dell'elenco del dry-run della FASE 6;
  4. indice (bin/index-rigenera.py --scrivi);
  5. aggancio personale "dopo-index";
  6. git add per percorso: i file di Arturo, gli handoff, e solo verso un remote privato CLAUDE.md,
     data/todo, personale/ e data/memory (senza lucchetti, log di Melchior, copie .bak-* e indice
     della memoria, che si rigenera);
  7. controllo dei marcatori di conflitto nei file in stage;
  8. aggancio personale "prima-commit";
  9. commit della memoria ("memoria: applicata da /fine") separato dal commit di sync;
 10. push, con un pull --rebase --autostash e un secondo tentativo se il primo è rifiutato. Niente push
     se origin è il repository pubblico di Arturo.

Aggancio personale: se esiste ~/.claude/personale/fine-coda.py, la coda lo lancia ai passi 5 e 8 con un
JSON su stdin: {"fase", "handoff", "slug", "radice", "argomenti" (quelli dopo --), "in_stage"}. Risponde
su stdout {"esiti": [...], "path": [...], "blocca": null o "motivo"}. I "path" (relativi a ~/.claude)
entrano nel commit di sync. Exit 0 fatto, 3 servizio giù (la coda prosegue e lo dice), 4 blocca.

Exit:
  0 fatto (l'ultima riga è la riga tecnica per la chiusura) · 1 gate rosso · 3 l'aggancio personale
  dice che un servizio è giù · 4 rebase a metà, config rotta, marcatori di conflitto o blocco
  dell'aggancio: niente commit · 5 uso sbagliato · 6 git add o git commit falliti

FINE_CODA_CLAUDE sposta la radice (per i banchi).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

CL = Path(os.environ.get("FINE_CODA_CLAUDE") or Path.home() / ".claude")
QUI = Path(__file__).resolve().parent
PY = sys.executable
# Su Windows "bash" senza percorso apre il bash di WSL da System32, prima del PATH: serve quello di Git.
BASH = shutil.which("bash") or "bash"
RE_MARKER = re.compile(r"^\+(<<<<<<< |=======$|>>>>>>> )", re.M)
RE_ARTURO = re.compile(r"github\.com[:/]stellakamikaze/arturo(\.git)?/?$")
ARTURO = ["settings.json", ".gitattributes", ".gitignore", "bin", "commands", "agents", "hooks", "shared",
          "docs", "tools", "tests", "output-styles", "NOVITA.md", "README.md", "package.json"]
PRIVATI = ["CLAUDE.md", "data/todo", "personale", "data/memory"]
# Restano fuori anche verso un remote privato: il lucchetto di arturo todo, i log e le cache di
# Melchior, le copie di sicurezza e l'indice della memoria, che si rigenera. L'elenco dei file lo fa la
# coda: git add -f con un pathspec ":(exclude)" su una cartella ignorata a volte non aggiunge niente e
# non dà errore (git 2.55 su Windows, 30/10/2026, stesso comando con esiti diversi).
INDICE_MEMORIA = "data/memory/index.md"


def escluso(rel):
    parti = rel.split("/")
    nome = parti[-1]
    return (rel == INDICE_MEMORIA or nome.endswith(".lock") or ".bak-" in nome
            or any(x.startswith(".melchior-") or x == ".git" for x in parti))


def file_privati(radice, percorsi):
    """I file da aggiungere con -f: quelli su disco sotto i percorsi, più i tracciati cancellati, senza gli
    esclusi."""
    out = []
    for p in percorsi:
        pieno = radice / p
        if pieno.is_file():
            out.append(p)
            continue
        for cartella, dirs, nomi in os.walk(pieno):
            dirs[:] = [d for d in dirs if d != ".git"]
            base = Path(cartella).relative_to(radice).as_posix()
            out += [f"{base}/{n}" for n in nomi]
    tracciati = git("ls-files", "-z", "--", *percorsi)[1].split("\0")
    out += [t for t in tracciati if t and not (radice / t).exists()]
    return [x for x in dict.fromkeys(out) if not escluso(x)]
STOP_REBASE = ("REBASE A METÀ in ~/.claude: STOP, niente commit né push. Guarda con git -C ~/.claude status,\n"
               "poi rebase --continue (o --abort), e rilancia la coda.")


def run(cmd, timeout=180, entrata=None, cwd=None):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=timeout, input=entrata, cwd=cwd)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return None, "", f"timeout dopo {timeout} s"
    except OSError as e:
        return None, "", str(e)


def git(*a, timeout=120):
    return run(["git", "-C", str(CL), *a], timeout)


def ultima(*testi):
    righe = [r.strip() for t in testi for r in (t or "").splitlines() if r.strip()]
    return righe[-1][:160] if righe else "nessun messaggio"


def rebase_a_meta():
    return (CL / ".git" / "rebase-merge").is_dir() or (CL / ".git" / "rebase-apply").is_dir()


def visibilita(url):
    """PRIVATE, PUBLIC, INTERNAL o "" se gh non risponde: solo PRIVATE apre i file personali."""
    if not url:
        return ""
    # gh passa da bash, come nella FASE 9 di prima: bash lo trova anche quando è uno script, su ogni sistema
    rc, out, _ = run([BASH, "-c", 'gh repo view "$1" --json visibility -q .visibility', "gh", url], 30)
    return out.strip() if rc == 0 else ""


def handoff_della_sessione():
    """L'handoff di questa sessione (riga "- Sessione: <id>"), il più recente per nome, o None."""
    sid = os.environ.get("CLAUDE_CODE_SESSION_ID", "").strip()
    if not sid:
        return None
    trovati = []
    for f in (CL / "data" / "handoffs").glob("*/HANDOFF_*.md"):
        try:
            if re.search(rf"(?m)^- Sessione: {re.escape(sid)}\s*$", f.read_text(encoding="utf-8", errors="replace")):
                trovati.append(f)
        except OSError:
            continue
    return max(trovati, key=lambda f: f.name) if trovati else None


def personale(fase, base, in_stage):
    """L'aggancio personale: (esiti, path, blocca, offline). Assente = niente."""
    script = CL / "personale" / "fine-coda.py"
    if not script.is_file():
        return [], [], None, False
    rc, out, err = run([PY, str(script)], 300, entrata=json.dumps({**base, "fase": fase, "in_stage": in_stage}))
    try:
        dati = json.loads(out.strip().splitlines()[-1]) if out.strip() else {}
    except (ValueError, IndexError):
        dati = {}
    esiti = [str(x) for x in dati.get("esiti") or []] if isinstance(dati, dict) else []
    path = [str(x) for x in dati.get("path") or []] if isinstance(dati, dict) else []
    blocca = dati.get("blocca") if isinstance(dati, dict) else None
    if rc == 4 and not blocca:
        blocca = ultima(err, out)
    if rc not in (0, 3, 4):
        esiti.append(f"personale/fine-coda.py ({fase}) rc={rc}: {ultima(err, out)}")
    if err.strip() and rc in (0, 3):
        print(err.strip())
    return esiti, path, blocca, rc == 3


def push(origin_url):
    """(ok, motivo). Un push rifiutato passa da un pull --rebase --autostash e riprova una volta. Se il
    pull lascia un rebase a metà, il secondo push non parte."""
    rc, out, err = git("push", "-q", "origin", "HEAD:main", timeout=90)
    if rc == 0:
        return True, ""
    rc, out2, err2 = git("pull", "-q", "--rebase", "--autostash", "origin", "main", timeout=120)
    if rebase_a_meta():
        return False, "rebase"
    if rc != 0:
        return False, f"pull prima del secondo push fermo: {ultima(err2, out2)}"
    rc, out, err = git("push", "-q", "origin", "HEAD:main", timeout=90)
    return rc == 0, ultima(err, out)


def aggiungi(*argomenti):
    rc, _, err = git("add", *argomenti)
    return rc == 0 or "did not match any files" in err, err


def aggiungi_forzati(elenco):
    """git add -A -f per un elenco esplicito di file, passato su stdin: niente limiti di riga di comando."""
    if not elenco:
        return True, ""
    rc, _, err = run(["git", "-C", str(CL), "add", "-A", "-f", "--pathspec-from-file=-", "--pathspec-file-nul"],
                     120, entrata="\0".join(elenco))
    return rc == 0, err


def main(argv):
    for flusso in (sys.stdout, sys.stderr):  # su Windows la pipe è in cp1252, chi legge vuole UTF-8
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    propri = argv[:argv.index("--")] if "--" in argv else argv
    suoi = argv[argv.index("--") + 1:] if "--" in argv else []
    ap = argparse.ArgumentParser(description="Coda di /fine")
    ap.add_argument("--handoff", help="default: l'handoff di questa sessione (CLAUDE_CODE_SESSION_ID)")
    ap.add_argument("--slug", help="default: la cartella dell'handoff")
    ap.add_argument("--trailer", action="append", default=[])
    ap.error = lambda m: (sys.stderr.write(f"fine-coda: {m}\n"), sys.exit(5))
    a = ap.parse_args(propri)

    handoff = Path(a.handoff).expanduser().resolve() if a.handoff else handoff_della_sessione()
    if a.handoff and not handoff.is_file():
        ap.error(f"handoff assente: {handoff}")
    if handoff:
        try:
            handoff.resolve().relative_to((CL / "data" / "handoffs").resolve())
        except ValueError:
            ap.error(f"l'handoff non sta sotto {CL / 'data' / 'handoffs'}: {handoff}")
    slug = a.slug or (handoff.parent.name if handoff else "")
    if slug and ("/" in slug or "\\" in slug or slug.startswith(".")):
        ap.error(f"slug non valido: {slug}")
    base = {"handoff": str(handoff or ""), "slug": slug, "radice": str(CL), "argomenti": suoi}
    esiti, offline = [], False

    # 1. config integra
    if rebase_a_meta():
        print(STOP_REBASE)
        return 4
    controlla = CL / "hooks" / "controlla-config.py"
    if controlla.is_file():
        rc, out, err = run([PY, str(controlla), "--quiet"], 60)
        if rc != 0:
            print((out + err).strip())
            print("fine-coda: la config non è integra, niente commit. Sistemala prima (vedi sopra) e rilancia.")
            return 4

    if not handoff:
        # Senza handoff della sessione la coda fa solo il sync della config: /fine senza handoff, o un
        # salvataggio della config a mano.
        esiti.append("nessun handoff di questa sessione: solo il sync della config")
        extra = []
    else:
        # 2. gate: bloccante
        rc, out, err = run([BASH, str(QUI / "handoff-gate.sh"), str(handoff)], 60)
        if rc != 0:
            print((out + err).strip())
            print("fine-coda: gate ROSSO, niente commit. Correggi l'handoff e rilancia.")
            return 1
        esiti.append("gate verde")

        # 3. retention: esce solo l'elenco del dry-run che /fine ha già letto
        rc, out, err = run([PY, str(QUI / "handoff-retention.py"), slug, "--applica",
                            "--radice", str(CL / "data" / "handoffs")], 60)
        if rc == 0:
            n = len(re.findall(r"(?m)^NEL CESTINO ", out))
            resta = len(re.findall(r"(?m)^RESTA ", out))
            if "AVVISO: nessun elenco" in out:
                esiti.append("retention NON applicata: manca il dry-run della FASE 6"
                             + (f", {resta} file oltre il keep restano" if resta else ""))
            else:
                esiti.append("retention ok" + (f" ({n} nel cestino)" if n else "")
                             + (f", {resta} restano: fuori dal dry-run" if resta else ""))
        elif rc == 2 and "cartella assente" in err:
            esiti.append("retention: nessun handoff per questo slug")
        else:
            print((out + err).strip())
            esiti.append(f"retention rc={rc}: {ultima(err, out)}")

        # 4. indice
        rc, out, err = run([PY, str(QUI / "index-rigenera.py"), "--scrivi", "--radice", str(CL / "data" / "handoffs")], 60)
        esiti.append("indice ok" if rc == 0 else f"indice NON rigenerato: {ultima(err, out)}")

        # 5. aggancio personale dopo l'indice
        e, extra, blocca, off = personale("dopo-index", base, [])
        esiti += e
        offline |= off
        if blocca:
            print(f"fine-coda: personale/fine-coda.py (dopo-index) blocca: {blocca}")
            return 4

    # 6. add per percorso
    if not (CL / ".git").exists():
        esiti.append("config senza git: niente commit")
        print("coda: " + " · ".join(esiti))
        return 3 if offline else 0
    origin = git("remote", "get-url", "origin")[1].strip()
    origin_arturo = bool(RE_ARTURO.search(origin))
    vis = visibilita(origin) if origin and not origin_arturo else ""
    falliti = []
    for p in ARTURO:
        if (CL / p).exists():
            ok, err = aggiungi("--", p)
            if not ok:
                falliti.append(f"{p}: {ultima(err)}")
    if (CL / "skills").is_dir():
        aggiungi("-u", "--", "skills")
        nuove = git("ls-files", "--others", "--exclude-standard", "--directory", "--", "skills")[1].split()
        if nuove:
            if vis == "PRIVATE" or origin_arturo or not origin:
                aggiungi("--", "skills")
            else:
                print(f"SKILL TUE NON SALVATE: {' '.join(nuove)} - il remote della config non risulta privato "
                      f"(visibilità: {vis or 'sconosciuta'}). Restano su questa macchina.")
    if vis == "PRIVATE":
        ok, err = aggiungi_forzati(file_privati(CL, [p for p in PRIVATI if (CL / p).exists()]))
        if not ok:
            falliti.append(f"{', '.join(PRIVATI)}: {ultima(err)}")
        # Gli handoff senza -f: una riga della persona nel .gitignore (un progetto riservato) va rispettata.
        if (CL / "data" / "handoffs").exists():
            aggiungi("-A", "--", "data/handoffs")
    else:
        esiti.append(f"CLAUDE.md, personale/, handoff, todo e memoria solo su questa macchina: il remote "
                     f"non risulta privato (visibilità: {vis or 'sconosciuta'})")
        if origin_arturo or not origin:
            for p in ("data/handoffs", "data/todo", "data/memory"):
                if git("ls-files", "--", p)[1].strip() and git("rm", "-r", "-q", "--cached", "--", p)[0] == 0:
                    esiti.append(f"{p} tolto dal tracciamento di git, i file restano su questa macchina")
    if falliti:
        print("fine-coda: git add fallito su " + "; ".join(falliti))
        return 6

    # 7. marcatori di conflitto
    staged = [p for p in git("diff", "--cached", "--name-only", "--no-renames", "-z")[1].split("\0") if p]
    if staged and RE_MARKER.search(git("diff", "--cached")[1]):
        print("MARCATORI DI CONFLITTO: STOP. Nei file in stage ci sono righe <<<<<<< ======= >>>>>>>.")
        print("In un log o una lista tieni le due versioni, in una regola scegli, poi rilancia.")
        return 4

    # 8. aggancio personale prima del commit
    e, extra2, blocca, off = personale("prima-commit", base, staged)
    esiti += e
    offline |= off
    if blocca:
        print(f"fine-coda: personale/fine-coda.py (prima-commit) blocca: {blocca}")
        return 4
    extra = [p for p in dict.fromkeys(extra + extra2) if p and not p.startswith(("/", ".."))]
    if extra and vis != "PRIVATE":
        # personale/ e i .local sono ignorati da Arturo: senza un remote privato restano fuori
        rc, _, err = git("add", "-A", "--", *extra)
        if rc != 0:
            esiti.append(f"path dell'aggancio personale fuori dal commit: il remote non risulta privato")
        extra = []
    if extra:
        ok, err = aggiungi_forzati(file_privati(CL, extra))
        if not ok:
            print(f"fine-coda: git add fallito sui path dell'aggancio personale: {ultima(err)}")
            return 6
        staged = [p for p in git("diff", "--cached", "--name-only", "--no-renames", "-z")[1].split("\0") if p]

    # 9. commit: la memoria a parte, così si annulla da sola
    trailer = "".join(f"\n{t}" for t in a.trailer)
    memoria = [p for p in staged if p.startswith("data/memory/")]
    resto = [p for p in staged if p not in memoria]
    # Commit dall'indice, mai "git commit -- <path>": con i path git riprende i file dal disco e annulla un
    # "rm --cached" (test F17). La memoria va prima, con una copia dell'indice senza il resto.
    indice = Path(git("rev-parse", "--git-path", "index")[1].strip())
    indice = indice if indice.is_absolute() else CL / indice
    for paths, msg, nome in ((memoria, "memoria: applicata da /fine", "commit memoria"),
                             (resto, f"chore: session sync {date.today()}", "commit")):
        if not paths:
            continue
        stat = git("diff", "--cached", "--stat", "--", *paths)[1].rstrip()
        messaggio = msg + ("\n" + trailer if trailer else "")
        if paths is memoria and resto:
            copia = indice.with_name("index.fine-coda")
            shutil.copy2(str(indice), str(copia))
            env = dict(os.environ, GIT_INDEX_FILE=str(copia))
            try:
                subprocess.run(["git", "-C", str(CL), "reset", "-q", "--", *resto], env=env, capture_output=True)
                p = subprocess.run(["git", "-C", str(CL), "commit", "-q", "-m", messaggio], env=env,
                                   capture_output=True, text=True, encoding="utf-8", errors="replace")
                rc, out, err = p.returncode, p.stdout, p.stderr
            finally:
                copia.unlink(missing_ok=True)
        else:
            rc, out, err = git("commit", "-q", "-m", messaggio)
        if rc != 0:
            print(f"fine-coda: commit fallito: {ultima(err, out)}")
            return 6
        h = git("rev-parse", "--short", "HEAD")[1].strip()
        print(f"-- {nome} {h} --\n{stat}")
        esiti.append(f"{nome} {h}")
    if not staged:
        esiti.append("config: niente da committare")
    fuori = [r for r in git("status", "--short")[1].splitlines() if r.strip()]
    if fuori:
        print(f"-- fuori dal commit: {len(fuori)} righe di git status --")
        print("\n".join(fuori[:15]) + (f"\n... e altre {len(fuori) - 15}" if len(fuori) > 15 else ""))

    # 10. push
    if origin_arturo:
        esiti.append("config: solo locale, origin è il repository pubblico di Arturo (vedi /setup FASE 7)")
    elif not origin:
        esiti.append("config: solo locale, nessun remote origin")
    else:
        git("fetch", "-q", "origin", "main", timeout=90)
        avanti = git("rev-list", "--count", "origin/main..HEAD")[1].strip()
        if avanti == "0":
            esiti.append("config: niente da pushare")
        else:
            ok, perche = push(origin)
            if perche == "rebase":
                print("coda: " + " · ".join(esiti))
                print(STOP_REBASE)
                return 4
            esiti.append("config: push riuscito" if ok else f"config: push non riuscito ({perche}), "
                         f"{avanti or '?'} commit da ritentare")

    print("coda: " + " · ".join(esiti))
    return 3 if offline else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
