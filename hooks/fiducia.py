"""La catena di fiducia del plugin di Arturo (strati F3, #4533, docs/strati.md).

Col clone la fiducia la dà git: un rilascio è un tag firmato, e la storia dice cosa è cambiato. Col
plugin la cartella del codice è una copia senza git (la cache dei plugin di Claude Code), quindi ogni
rilascio porta due file accanto a plugin.json:

  .claude-plugin/MANIFEST       una riga "sha256  percorso" per ogni file del pacchetto
  .claude-plugin/MANIFEST.sig   la firma del MANIFEST, con la chiave dei rilasci (ssh-keygen -Y sign,
                                spazio dei nomi "arturo-manifest")

La chiave che verifica non si prende dalla copia da verificare: chi la cambia cambierebbe anche la
chiave. Si prende dall'ancora nell'Orsa (~/.claude/arturo/rilasci.allowed_signers), scritta alla prima
verifica e cambiata solo da un aggiornamento verificato con l'ancora di prima.

Prova del 5/11/2026 (Claude Code 2.1.318): Claude Code installa lo sha scritto nel catalogo anche se
nessun tag firmato lo indica. La verifica del tag la fa quindi Arturo, prima di `claude plugin update`.
Solo libreria standard, Python 3.8 o successivo.
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
from pathlib import Path

MANIFEST = ".claude-plugin/MANIFEST"
FIRMA = ".claude-plugin/MANIFEST.sig"
SPAZIO = "arturo-manifest"
FIRMATARI = "firme/rilasci.allowed_signers"
TESTA = "# MANIFEST di Arturo: sha256 e percorso di ogni file del pacchetto"
# Cosa non entra nel MANIFEST: la firma stessa, la cartella che Claude Code aggiunge alla cache
# (.in_use) e quello che Python scrive accanto agli script quando girano.
FUORI = re.compile(r"(^|/)(\.git|\.in_use|__pycache__|\.DS_Store)(/|$)|\.pyc$")
RIGA = re.compile(r"^([0-9a-f]{64})  (\S(?:.*\S)?)$")


def plugin(cartella: Path) -> bool:
    """Vero se `cartella` è una copia del plugin (c'è plugin.json e non c'è git): col clone vale git."""
    return (cartella / ".claude-plugin" / "plugin.json").is_file() and not (cartella / ".git").exists()


def impronte(cartella: Path) -> dict:
    """percorso (con /) -> sha256 di ogni file della copia, MANIFEST e firma esclusi."""
    fuori = {MANIFEST, FIRMA}
    trovate = {}
    for radice, cartelle, file in os.walk(str(cartella)):
        cartelle[:] = sorted(c for c in cartelle if not FUORI.search(c))
        for nome in file:
            percorso = Path(radice) / nome
            rel = percorso.relative_to(cartella).as_posix()
            if rel in fuori or FUORI.search(rel) or percorso.is_symlink() and not percorso.exists():
                continue
            h = hashlib.sha256()
            with open(str(percorso), "rb") as f:
                for blocco in iter(lambda: f.read(1 << 16), b""):
                    h.update(blocco)
            trovate[rel] = h.hexdigest()
    return trovate


def scrivi_manifest(cartella: Path) -> Path:
    righe = [TESTA] + [f"{h}  {p}" for p, h in sorted(impronte(cartella).items())]
    destinazione = cartella / MANIFEST
    destinazione.parent.mkdir(parents=True, exist_ok=True)
    destinazione.write_bytes(("\n".join(righe) + "\n").encode("utf-8"))
    vecchia = cartella / FIRMA
    if vecchia.exists():
        vecchia.unlink()  # una firma di prima non vale per il MANIFEST nuovo
    return destinazione


def leggi_manifest(cartella: Path):
    """{percorso: sha256}, o None se il MANIFEST manca o ha una riga fuori forma."""
    try:
        testo = (cartella / MANIFEST).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    voci = {}
    for riga in testo.splitlines():
        if not riga or riga.startswith("#"):
            continue
        m = RIGA.match(riga)
        if not m or ".." in m.group(2).split("/"):
            return None
        voci[m.group(2)] = m.group(1)
    return voci


def firma(cartella: Path, chiave: Path) -> None:
    """Firma il MANIFEST con la chiave privata dei rilasci: la usa solo chi pubblica un rilascio."""
    # Da stdin, con la firma sull'uscita: col file, una MANIFEST.sig già presente resta com'era e
    # ssh-keygen esce lo stesso con 0 ("already exists. Overwrite (y/n)?", prova del 5/11/2026).
    with open(str(cartella / MANIFEST), "rb") as dati:
        r = subprocess.run(["ssh-keygen", "-Y", "sign", "-f", str(chiave), "-n", SPAZIO], stdin=dati,
                           capture_output=True, timeout=60)
    if r.returncode != 0 or b"BEGIN SSH SIGNATURE" not in r.stdout:
        raise SystemExit(f"firma del MANIFEST non riuscita: {r.stderr.decode('utf-8', 'replace').strip()[:200]}")
    tmp = cartella / (FIRMA + ".tmp")
    tmp.write_bytes(r.stdout)
    os.replace(str(tmp), str(cartella / FIRMA))


def principali(firmatari: Path) -> list:
    try:
        righe = firmatari.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    return [r.split()[0] for r in righe if r.strip() and not r.lstrip().startswith("#")]


def verifica_firma(cartella: Path, firmatari: Path) -> tuple:
    """(esito, motivo): esito "ok", "manca", "non-torna" o "non-verificabile". "non-verificabile" vuol dire
    che questo computer non sa controllare (ssh-keygen senza -Y, OpenSSH prima della 8.2): non è un allarme."""
    manifest, sig = cartella / MANIFEST, cartella / FIRMA
    if not manifest.is_file() or not sig.is_file():
        return "manca", "la copia del plugin non ha il MANIFEST firmato"
    nomi = principali(firmatari)
    if not nomi:
        return "non-verificabile", f"manca la chiave che verifica ({firmatari})"
    if not shutil.which("ssh-keygen"):
        return "non-verificabile", "manca ssh-keygen: servono OpenSSH 8.2 o più recente"
    ultimo = ""
    for nome in nomi:
        try:
            with open(str(manifest), "rb") as dati:
                r = subprocess.run(["ssh-keygen", "-Y", "verify", "-f", str(firmatari), "-I", nome, "-n", SPAZIO,
                                    "-s", str(sig)], stdin=dati, capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.SubprocessError) as errore:
            return "non-verificabile", str(errore)[:200]
        if r.returncode == 0:
            return "ok", ""
        ultimo = (r.stderr or r.stdout or "").strip()
    if re.search(r"unknown option|illegal option|usage:", ultimo, re.I):
        return "non-verificabile", "ssh-keygen non sa verificare le firme: servono OpenSSH 8.2 o più recente"
    return "non-torna", "la firma del MANIFEST non è della chiave dei rilasci di Arturo"


def confronta(cartella: Path) -> dict:
    """I file della copia diversi dal MANIFEST: {'cambiati', 'mancano', 'in_piu'}; None se non c'è un MANIFEST."""
    attese = leggi_manifest(cartella)
    if attese is None:
        return None
    vere = impronte(cartella)
    return {
        "cambiati": sorted(p for p in attese if p in vere and vere[p] != attese[p]),
        "mancano": sorted(p for p in attese if p not in vere),
        "in_piu": sorted(p for p in vere if p not in attese),
    }


def ancora(orsa: Path) -> Path:
    return orsa / "arturo" / "rilasci.allowed_signers"


def firmatari_per(cartella: Path, orsa: Path) -> Path:
    """La chiave che verifica `cartella`: l'ancora nell'Orsa se c'è, altrimenti quella della copia (la
    prima volta, quando l'ancora non esiste ancora)."""
    a = ancora(orsa)
    return a if a.is_file() else cartella / FIRMATARI


def fissa_ancora(cartella: Path, orsa: Path) -> bool:
    """Copia la chiave della copia nell'ancora, solo dopo che la copia è stata verificata. Vero se è cambiata."""
    sorgente, a = cartella / FIRMATARI, ancora(orsa)
    try:
        nuova = sorgente.read_bytes()
        if a.is_file() and a.read_bytes() == nuova:
            return False
        a.parent.mkdir(parents=True, exist_ok=True)
        tmp = a.with_name(a.name + ".tmp")
        tmp.write_bytes(nuova)
        os.replace(str(tmp), str(a))
        return True
    except OSError:
        return False


def controlla(cartella: Path, orsa: Path) -> dict:
    """Firma e impronte di una copia del plugin: {'firma', 'motivo', 'cambiati', 'mancano', 'in_piu'}.
    Con la firma che manca o non torna i file non si confrontano: il MANIFEST stesso non vale."""
    esito, motivo = verifica_firma(cartella, firmatari_per(cartella, orsa))
    dati = {"firma": esito, "motivo": motivo, "cambiati": [], "mancano": [], "in_piu": []}
    if esito in ("ok", "non-verificabile"):
        differenze = confronta(cartella)
        if differenze is None:
            dati.update(firma="manca", motivo="il MANIFEST della copia non si legge")
        else:
            dati.update(differenze)
    return dati
