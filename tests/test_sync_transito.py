#!/usr/bin/env python3
"""bin/sync_transito.py: i dati di transito su un ramo sync, un giro alla volta, un push al minuto (23/11/2026,
revisione del 22/11, D5, #6424).

ST01 un giro senza cambi non fa nessun commit.
ST02 un handoff nuovo: un commit nel ramo sync, nessun commit su main (che lo ignora), push sul ramo sync.
ST03 due giri entro il minuto: il secondo fa il suo commit ma non spinge. Dopo il minuto spinge.
ST04 il lucchetto preso da un processo vivo: il giro esce 0 e non committa. Un pid morto: il lucchetto si riprende.
ST05 una chiave nel file: exit 7, niente commit, il file è nominato e il valore no.
ST06 origin è il repository pubblico di Arturo, o la visibilità non è PRIVATE: commit locale, niente push.
ST07 --migra --prova non scrive niente.
ST08 due macchine scrivono INDEX.md insieme (merge=union): il rebase le unisce, nessun marcatore.
ST09 un lucchetto .lock sotto data/ resta fuori dal ramo sync.
ST10 il pull di main porta il commit che toglie i path di transito (git rm --cached e .gitignore): un file
     cambiato qui non manda in conflitto l'autostash, i file spariti dal disco tornano da --dopo-il-pull con la
     copia più nuova, e il ramo sync non registra cancellazioni.
ST11 una cancellazione vera arrivata da main (la retention di una macchina non migrata) non torna.
ST12 col segno "pull in corso" il giro non committa; un segno vecchio di oltre 10 minuti non ferma più.
ST13 --dopo-il-pull porta i commit dell'altra macchina anche dentro il minuto.
ST14 più di 25 file cancellati in un giro: exit 4, niente commit; con SYNC_TRANSITO_CANCELLAZIONI_OK=1 passa.
ST15 un giro senza niente di nuovo non tocca la rete: con origin irraggiungibile esce 0 senza errori.
ST16 la seconda macchina si aggancia senza un handoff che il ramo ha: non lo cancella dal ramo e lo riprende
     su disco; un file cambiato solo sul ramo vince, uno cambiato da tutte e due le parti si fonde.

La coda di /fine (bin/fine-coda.py) con il ramo sync:
FY01 con .git-sync migrato: handoff e indice non entrano nel commit su main né vanno sul remote main; li porta
     il ramo sync, e il remote lo riceve. La riga della coda lo dice.
FY02 senza .git-sync (macchina non migrata) il comportamento è quello di prima: l'handoff esce su main.
FY03 una chiave in un handoff col ramo sync attivo: exit 7, niente sul ramo sync del remote.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

QUI = Path(__file__).resolve().parent
SCRIPT = QUI.parent / "bin" / "sync_transito.py"
TOKEN = "gh" + "p_" + "A1b2C3d4" * 5


def sh(cwd, *a, env=None):
    p = subprocess.run(list(a), cwd=str(cwd), capture_output=True, text=True, env=env)
    return p.stdout.strip()


class Macchina:
    def __init__(self, tmp: Path, nome: str, origin: Path, url=None):
        self.cl = tmp / nome
        self.cl.mkdir()
        sh(self.cl, "git", "init", "-q", "-b", "main")
        sh(self.cl, "git", "config", "user.name", "Prova")
        sh(self.cl, "git", "config", "user.email", "prova@example.com")
        sh(self.cl, "git", "remote", "add", "origin", url or str(origin))
        (self.cl / ".gitattributes").write_text("data/handoffs/INDEX.md merge=union\n", encoding="utf-8")
        (self.cl / ".gitignore").write_text("data/handoffs/\ndata/memory/\n", encoding="utf-8")
        sh(self.cl, "git", "add", ".")
        sh(self.cl, "git", "commit", "-q", "-m", "base")
        self.env = dict(os.environ, SYNC_TRANSITO_CLAUDE=str(self.cl), SYNC_TRANSITO_VISIBILITA="PRIVATE")

    def scrivi(self, rel, testo):
        p = self.cl / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(testo, encoding="utf-8")

    def lancia(self, *a, env=None):
        return subprocess.run([sys.executable, str(SCRIPT), *a], capture_output=True, text=True,
                              env=env or self.env, timeout=120)

    def sync(self, *a):
        return sh(self.cl, "git", f"--git-dir={self.cl / '.git-sync'}", f"--work-tree={self.cl}", *a)

    def commit_sync(self):
        return int(self.sync("rev-list", "--count", "HEAD") or 0)

    def commit_main(self):
        return int(sh(self.cl, "git", "rev-list", "--count", "HEAD") or 0)


def coppia(tmp):
    origin = tmp / "origin.git"
    sh(tmp, "git", "init", "-q", "--bare", "-b", "main", str(origin))
    return origin


def st01(tmp):
    m = Macchina(tmp, "m", coppia(tmp))
    m.scrivi("data/handoffs/a/HANDOFF_1.md", "uno\n")
    m.lancia("--migra")
    n = m.commit_sync()
    r = m.lancia("--giro")
    if r.returncode != 0 or m.commit_sync() != n or "niente da committare" not in r.stdout:
        return f"rc={r.returncode} commit {n}->{m.commit_sync()} {r.stdout!r}"


def st02(tmp):
    origin = coppia(tmp)
    m = Macchina(tmp, "m", origin)
    main_prima = m.commit_main()
    m.scrivi("data/handoffs/a/HANDOFF_1.md", "uno\n")
    r = m.lancia("--migra")
    remoto = sh(tmp, "git", f"--git-dir={origin}", "ls-tree", "-r", "--name-only", "sync")
    if r.returncode != 0 or m.commit_main() != main_prima or "data/handoffs/a/HANDOFF_1.md" not in remoto:
        return f"rc={r.returncode} main {main_prima}->{m.commit_main()} remoto={remoto!r} {r.stdout!r}{r.stderr!r}"
    if sh(m.cl, "git", "status", "--short"):
        return f"main non pulito: {sh(m.cl, 'git', 'status', '--short')!r}"


def st03(tmp):
    origin = coppia(tmp)
    m = Macchina(tmp, "m", origin)
    m.scrivi("data/handoffs/a/HANDOFF_1.md", "uno\n")
    m.lancia("--migra")
    m.scrivi("data/handoffs/a/HANDOFF_2.md", "due\n")
    r = m.lancia("--giro")
    sul_remoto = sh(tmp, "git", f"--git-dir={origin}", "rev-list", "--count", "sync")
    if "push al prossimo minuto" not in r.stdout or m.commit_sync() <= int(sul_remoto):
        return f"secondo giro: {r.stdout!r} locale {m.commit_sync()} remoto {sul_remoto}"
    env = dict(m.env, SYNC_TRANSITO_MINUTO="0")
    r = m.lancia("--giro", env=env)
    sul_remoto2 = sh(tmp, "git", f"--git-dir={origin}", "rev-list", "--count", "sync")
    if "push riuscito" not in r.stdout or int(sul_remoto2) != m.commit_sync():
        return f"dopo il minuto: {r.stdout!r} locale {m.commit_sync()} remoto {sul_remoto2}"


def st04(tmp):
    m = Macchina(tmp, "m", coppia(tmp))
    m.scrivi("data/handoffs/a/HANDOFF_1.md", "uno\n")
    m.lancia("--migra")
    n = m.commit_sync()
    m.scrivi("data/handoffs/a/HANDOFF_2.md", "due\n")
    lock = m.cl / ".git-sync" / "lock"
    lock.write_text(f"{os.getppid()}\n", encoding="ascii")  # il processo che ha lanciato il banco è vivo
    r = m.lancia("--giro")
    if r.returncode != 0 or m.commit_sync() != n or "lucchetto" not in r.stdout:
        return f"vivo: rc={r.returncode} commit {n}->{m.commit_sync()} {r.stdout!r}"
    lock.write_text("999999\n", encoding="ascii")  # un pid che non esiste
    r = m.lancia("--giro")
    if r.returncode != 0 or m.commit_sync() != n + 1 or lock.exists():
        return f"morto: rc={r.returncode} commit {n}->{m.commit_sync()} lock={lock.exists()} {r.stdout!r}"


def st05(tmp):
    m = Macchina(tmp, "m", coppia(tmp))
    m.scrivi("data/handoffs/a/HANDOFF_1.md", "uno\n")
    m.lancia("--migra")
    n = m.commit_sync()
    m.scrivi("data/memory/nota.md", f"chiave {TOKEN}\n")
    r = m.lancia("--giro")
    if r.returncode != 7 or m.commit_sync() != n or "nota.md" not in r.stdout or TOKEN in r.stdout + r.stderr:
        return f"rc={r.returncode} commit {n}->{m.commit_sync()} {r.stdout!r}"


def st06(tmp):
    origin = coppia(tmp)
    m = Macchina(tmp, "m", origin, url="git@github.com:stellakamikaze/arturo.git")
    m.scrivi("data/handoffs/a/HANDOFF_1.md", "uno\n")
    r = m.lancia("--migra")
    if r.returncode != 0 or m.commit_sync() != 1 or "solo locale" not in r.stdout:
        return f"arturo: rc={r.returncode} commit {m.commit_sync()} {r.stdout!r}"
    origin2 = tmp / "o2.git"
    sh(tmp, "git", "init", "-q", "--bare", "-b", "main", str(origin2))
    m2 = Macchina(tmp, "m2", origin2)
    m2.scrivi("data/handoffs/a/HANDOFF_1.md", "uno\n")
    r = m2.lancia("--migra", env=dict(m2.env, SYNC_TRANSITO_VISIBILITA="PUBLIC"))
    if "solo locale" not in r.stdout or sh(tmp, "git", f"--git-dir={origin2}", "branch", "--list", "sync"):
        return f"pubblico: {r.stdout!r}"


def st07(tmp):
    m = Macchina(tmp, "m", coppia(tmp))
    m.scrivi("data/handoffs/a/HANDOFF_1.md", "uno\n")
    r = m.lancia("--migra", "--prova")
    if r.returncode != 0 or (m.cl / ".git-sync").exists() or "(prova)" not in r.stdout:
        return f"rc={r.returncode} .git-sync={(m.cl / '.git-sync').exists()} {r.stdout!r}"


def st08(tmp):
    origin = coppia(tmp)
    a = Macchina(tmp, "a", origin)
    a.scrivi("data/handoffs/INDEX.md", "riga base\n")
    a.lancia("--migra")
    b = Macchina(tmp, "b", origin)
    b.scrivi("data/handoffs/INDEX.md", "riga base\n")
    b.lancia("--migra")  # aggancia il ramo di a, il file su disco è già uguale
    a.scrivi("data/handoffs/INDEX.md", "riga base\nriga di a\n")
    b.scrivi("data/handoffs/INDEX.md", "riga base\nriga di b\n")
    zero = dict(a.env, SYNC_TRANSITO_MINUTO="0")
    ra = a.lancia("--giro", env=zero)
    rb = b.lancia("--giro", env=dict(b.env, SYNC_TRANSITO_MINUTO="0"))
    ra2 = a.lancia("--giro", env=zero)
    for m, nome in ((a, "a"), (b, "b")):
        testo = (m.cl / "data/handoffs/INDEX.md").read_text(encoding="utf-8")
        if "<<<<<<<" in testo:
            return f"marcatori in {nome}: {testo!r} | {ra.stdout!r} {rb.stdout!r} {rb.stderr!r}"
    tb = (b.cl / "data/handoffs/INDEX.md").read_text(encoding="utf-8")
    if "riga di a" not in tb or "riga di b" not in tb:
        return f"b non ha le due righe: {tb!r} | {rb.stdout!r} {rb.stderr!r}"


def st09(tmp):
    m = Macchina(tmp, "m", coppia(tmp))
    m.scrivi("data/handoffs/a/HANDOFF_1.md", "uno\n")
    m.scrivi("data/memory/.indice.lock", "123\n")
    m.scrivi("data/memory/nota.md.bak-1", "vecchia\n")
    m.lancia("--migra")
    tracciati = m.sync("ls-files")
    if ".lock" in tracciati or ".bak-" in tracciati or "HANDOFF_1.md" not in tracciati:
        return f"tracciati: {tracciati!r}"


def con_dati_su_main(tmp):
    """Una macchina migrata la cui main traccia ancora handoff e stati (prima del passo 5), e un autore che
    lavora su un'altra copia di main."""
    origin = coppia(tmp)
    m = Macchina(tmp, "m", origin)
    (m.cl / ".gitignore").write_text("", encoding="utf-8")
    m.scrivi("data/handoffs/a/HANDOFF_1.md", "uno\n")
    m.scrivi("data/handoffs/a/HANDOFF_2.md", "due\n")
    m.scrivi("data/progetti/stati.json", "{}\n")
    sh(m.cl, "git", "add", "-A")
    sh(m.cl, "git", "commit", "-q", "-m", "dati su main")
    sh(m.cl, "git", "push", "-q", "origin", "main")
    m.lancia("--migra")
    autore = tmp / "autore"
    sh(tmp, "git", "clone", "-q", str(origin), str(autore))
    sh(autore, "git", "config", "user.name", "Autore")
    sh(autore, "git", "config", "user.email", "autore@example.com")
    return origin, m, autore


def pull_di_main(m):
    """Quello che fa config-sync-pull.sh: --prima-del-pull, il pull con l'autostash, poi --dopo-il-pull."""
    prima = sh(m.cl, "git", "rev-parse", "HEAD")
    r1 = m.lancia("--prima-del-pull")
    p = subprocess.run(["git", "pull", "-q", "--rebase", "--autostash", "origin", "main"], cwd=str(m.cl),
                       capture_output=True, text=True)
    conflitti = sh(m.cl, "git", "diff", "--name-only", "--diff-filter=U")
    if p.returncode != 0 or conflitti:
        raise RuntimeError(f"pull di main: rc={p.returncode} conflitti={conflitti!r} {p.stderr[-300:]!r} {r1.stdout!r}")
    return prima, r1


def st10(tmp):
    origin, m, autore = con_dati_su_main(tmp)
    m.scrivi("data/handoffs/a/HANDOFF_1.md", "uno\npiù nuovo\n")  # cambio di questa macchina, solo su disco
    sh(autore, "git", "rm", "-r", "-q", "--cached", "data")
    (autore / ".gitignore").write_text("data/handoffs/\ndata/progetti/stati.json\n", encoding="utf-8")
    sh(autore, "git", "add", ".gitignore")
    sh(autore, "git", "commit", "-q", "-m", "via i path di transito")
    sh(autore, "git", "push", "-q", "origin", "main")
    prima, r1 = pull_di_main(m)
    spariti = not (m.cl / "data/handoffs/a/HANDOFF_1.md").exists()
    r2 = m.lancia("--dopo-il-pull", prima)
    h1 = m.cl / "data/handoffs/a/HANDOFF_1.md"
    testo = h1.read_text(encoding="utf-8") if h1.exists() else None
    tracciati = m.sync("ls-files")
    if not spariti or testo != "uno\npiù nuovo\n" or "ripristinati 3" not in r2.stdout \
            or "HANDOFF_2.md" not in tracciati or (m.cl / ".git-sync" / "pull-in-corso").exists():
        return f"spariti={spariti} testo={testo!r} {r1.stdout!r} {r2.stdout!r}{r2.stderr!r} tracciati={tracciati!r}"
    if m.sync("log", "--diff-filter=D", "--name-only", "--format=") != "":
        return f"cancellazioni nel ramo: {m.sync('log', '--diff-filter=D', '--name-only', '--format=')!r}"


def st11(tmp):
    origin, m, autore = con_dati_su_main(tmp)
    sh(autore, "git", "rm", "-q", "data/handoffs/a/HANDOFF_2.md")
    sh(autore, "git", "commit", "-q", "-m", "retention")
    sh(autore, "git", "push", "-q", "origin", "main")
    prima, _ = pull_di_main(m)
    r = m.lancia("--dopo-il-pull", prima)
    if r.returncode != 0 or "sync dopo il pull" not in r.stdout or "HANDOFF_1.md" not in m.sync("ls-files"):
        return f"dopo il pull non girato: rc={r.returncode} {r.stdout!r}{r.stderr[-200:]!r}"
    if (m.cl / "data/handoffs/a/HANDOFF_2.md").exists() or "HANDOFF_2.md" in m.sync("ls-files") \
            or "ripristinati" in r.stdout:
        return f"la cancellazione è tornata: {r.stdout!r} {m.sync('ls-files')!r}"


def st12(tmp):
    m = Macchina(tmp, "m", coppia(tmp))
    m.scrivi("data/handoffs/a/HANDOFF_1.md", "uno\n")
    m.lancia("--migra")
    n = m.commit_sync()
    m.scrivi("data/handoffs/a/HANDOFF_2.md", "due\n")
    segno = m.cl / ".git-sync" / "pull-in-corso"
    segno.write_text("1 1\n", encoding="utf-8")
    r = m.lancia("--giro")
    if r.returncode != 0 or m.commit_sync() != n or "pull della config in corso" not in r.stdout:
        return f"col segno: rc={r.returncode} commit {n}->{m.commit_sync()} {r.stdout!r}"
    vecchio = time.time() - 700
    os.utime(segno, (vecchio, vecchio))
    r = m.lancia("--giro")
    if m.commit_sync() != n + 1:
        return f"segno vecchio: commit {n}->{m.commit_sync()} {r.stdout!r}"


def st13(tmp):
    origin = coppia(tmp)
    a = Macchina(tmp, "a", origin)
    a.scrivi("data/handoffs/a/HANDOFF_1.md", "uno\n")
    a.lancia("--migra")
    b = Macchina(tmp, "b", origin)
    b.scrivi("data/handoffs/a/HANDOFF_1.md", "uno\n")
    b.lancia("--migra")
    a.scrivi("data/handoffs/a/HANDOFF_2.md", "due di a\n")
    a.lancia("--giro", env=dict(a.env, SYNC_TRANSITO_MINUTO="0"))
    r = b.lancia("--dopo-il-pull", sh(b.cl, "git", "rev-parse", "HEAD"))
    h2 = b.cl / "data/handoffs/a/HANDOFF_2.md"
    if r.returncode != 0 or not h2.exists() or "aggiornato" not in r.stdout:
        return f"rc={r.returncode} h2={h2.exists()} {r.stdout!r}{r.stderr!r}"


def st14(tmp):
    m = Macchina(tmp, "m", coppia(tmp))
    for i in range(30):
        m.scrivi(f"data/memory/nota{i}.md", f"{i}\n")
    m.lancia("--migra")
    n = m.commit_sync()
    shutil.rmtree(m.cl / "data" / "memory")
    r = m.lancia("--giro")
    if r.returncode != 4 or m.commit_sync() != n or "30 file cancellati" not in r.stdout:
        return f"rc={r.returncode} commit {n}->{m.commit_sync()} {r.stdout!r}"
    r = m.lancia("--giro", env=dict(m.env, SYNC_TRANSITO_CANCELLAZIONI_OK="1"))
    if r.returncode != 0 or m.commit_sync() != n + 1:
        return f"col via: rc={r.returncode} commit {n}->{m.commit_sync()} {r.stdout!r}"


def st15(tmp):
    m = Macchina(tmp, "m", coppia(tmp))
    m.scrivi("data/handoffs/a/HANDOFF_1.md", "uno\n")
    m.lancia("--migra")
    sh(m.cl, "git", "remote", "set-url", "origin", str(tmp / "non-esiste.git"))
    r = m.lancia("--giro", env=dict(m.env, SYNC_TRANSITO_MINUTO="0"))
    if r.returncode != 0 or "remote" in r.stdout or "push" in r.stdout:
        return f"rc={r.returncode} {r.stdout!r}{r.stderr!r}"


def st16(tmp):
    origin = coppia(tmp)
    a = Macchina(tmp, "a", origin)
    a.scrivi("data/handoffs/a/HANDOFF_1.md", "uno\n")
    a.scrivi("data/handoffs/INDEX.md", "base\nriga di a\n")
    a.scrivi("data/handoffs/a/HANDOFF_3.md", "tre, versione del ramo\n")
    a.lancia("--migra")
    b = Macchina(tmp, "b", origin)
    b.scrivi("data/handoffs/INDEX.md", "base\nriga di b\n")
    b.scrivi("data/handoffs/a/HANDOFF_3.md", "tre, versione del ramo\n")
    r = b.lancia("--migra", env=dict(b.env, SYNC_TRANSITO_MINUTO="0"))
    remoto = sh(tmp, "git", f"--git-dir={origin}", "ls-tree", "-r", "--name-only", "sync")
    h1 = b.cl / "data/handoffs/a/HANDOFF_1.md"
    indice = (b.cl / "data/handoffs/INDEX.md").read_text(encoding="utf-8")
    if "HANDOFF_1.md" not in remoto or not h1.exists() or b.sync("log", "--diff-filter=D", "--format=%h"):
        return f"cancellato: remoto={remoto!r} h1={h1.exists()} {r.stdout!r}"
    if "riga di a" not in indice or "riga di b" not in indice or "<<<<<<<" in indice:
        return f"indice non fuso: {indice!r} {r.stdout!r}"


def banco_coda():
    spec = importlib.util.spec_from_file_location("banco_fine_coda", QUI / "test_fine_coda_2026_10_30.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def lab_con_sync(repo, tmp, migra):
    fc = banco_coda()
    lab = fc.Lab(repo, None, tmp)
    for rel in ("bin/sync_transito.py", "data/transito.paths"):
        (lab.cl / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(repo / rel, lab.cl / rel)
    lab.git(lab.cl, "add", "-A")
    lab.git(lab.cl, "commit", "-q", "-m", "con il sync")
    lab.git(lab.cl, "push", "-q", "origin", "main")
    if migra:
        p = subprocess.run([sys.executable, "-B", str(lab.cl / "bin" / "sync_transito.py"), "--migra"],
                           capture_output=True, text=True, env=dict(lab.ambiente, SYNC_TRANSITO_CLAUDE=str(lab.cl)))
        if p.returncode != 0:
            raise RuntimeError(f"migra: {p.stdout}{p.stderr}")
    return lab


def sul_ramo_sync(lab):
    return lab.git(lab.remoto, "ls-tree", "-r", "--name-only", "sync").split()


def fy01(tmp):
    repo = SCRIPT.parent.parent
    lab = lab_con_sync(repo, tmp, True)
    h = lab.handoff()
    r = lab.coda(h)
    rel = h.relative_to(lab.cl).as_posix()
    if r.returncode != 0 or rel in lab.nel_remoto() or rel not in sul_ramo_sync(lab) or "ramo sync" not in r.stdout:
        return f"rc={r.returncode} su main={rel in lab.nel_remoto()} su sync={rel in sul_ramo_sync(lab)} {r.stdout.strip()[-300:]!r}"


def fy02(tmp):
    repo = SCRIPT.parent.parent
    lab = lab_con_sync(repo, tmp, False)
    h = lab.handoff()
    r = lab.coda(h)
    rel = h.relative_to(lab.cl).as_posix()
    if r.returncode != 0 or rel not in lab.nel_remoto():
        return f"rc={r.returncode} su main={rel in lab.nel_remoto()} {r.stdout.strip()[-300:]!r}"


def fy03(tmp):
    repo = SCRIPT.parent.parent
    lab = lab_con_sync(repo, tmp, True)
    h = lab.handoff(testo=banco_coda().VERDE + f"\nchiave {TOKEN}\n")
    r = lab.coda(h)
    rami = lab.git(lab.remoto, "branch", "--list", "sync").strip()
    rel = h.relative_to(lab.cl).as_posix()
    if r.returncode != 7 or TOKEN in r.stdout + r.stderr or (rami and rel in sul_ramo_sync(lab)):
        return f"rc={r.returncode} sync={rami!r} {r.stdout.strip()[-300:]!r}"


CASI = [("ST01", st01), ("ST02", st02), ("ST03", st03), ("ST04", st04), ("ST05", st05), ("ST06", st06),
        ("ST07", st07), ("ST08", st08), ("ST09", st09), ("ST10", st10), ("ST11", st11), ("ST12", st12),
        ("ST13", st13), ("ST14", st14), ("ST15", st15), ("ST16", st16),
        ("FY01", fy01), ("FY02", fy02), ("FY03", fy03)]


def main() -> int:
    global SCRIPT
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=QUI.parent)
    parser.add_argument("--baseline-ref")
    args = parser.parse_args()
    SCRIPT = args.repo.resolve() / "bin" / "sync_transito.py"
    rossi = []
    for codice, fn in CASI:
        with tempfile.TemporaryDirectory(prefix="arturo-st-") as tmp:
            try:
                e = fn(Path(tmp))
            except Exception as ex:  # noqa: BLE001 - un banco che salta è rosso, col motivo
                e = f"eccezione {ex!r}"
            if e:
                rossi.append(f"{codice} {e}")
    if args.baseline_ref:
        # La base non ha ancora bin/sync_transito.py: ogni caso deve essere rosso.
        assert len(rossi) == len(CASI), f"baseline non discriminante: rossi {[r.split()[0] for r in rossi]}"
        print(f"baseline {args.baseline_ref}: {len(rossi)}/{len(CASI)} rossi")
        return 0
    for r in rossi:
        print("ROSSO", r)
    print(f"sync dei dati di transito: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
