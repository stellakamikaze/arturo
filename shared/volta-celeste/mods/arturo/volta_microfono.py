#!/usr/bin/env python3
"""volta_microfono: il microfono di questa macchina arriva alle sessioni di Claude che girano su un'altra.

Claude Code registra la dettatura (barra spaziatrice tenuta premuta) dall'ingresso audio predefinito
della macchina dove gira la sessione, e non permette di sceglierne un altro. Quando la sessione è
aperta in Volta da un'altra macchina, la voce va portata là: questo script cattura il microfono qui,
lo manda in ssh, e là lo suona dentro un microfono virtuale (BlackHole 2ch), che per la durata del
ponte diventa l'ingresso predefinito. Alla fine torna l'ingresso di prima. La trascrizione resta
quella di Claude Code.

Lato locale (lo lancia il mod, microfono.js):
  python3 volta_microfono.py accendi TARGET   apre il ponte verso TARGET (il nome ssh), o lo rinnova
  python3 volta_microfono.py spegni           lo chiude
Lato remoto (lo lancia il ponte via ssh, o il mod prima di accendere):
  python3 volta_microfono.py ricevi           suona in BlackHole il PCM che arriva da stdin
  python3 volta_microfono.py ripara           rimette l'ingresso di prima se un ponte è morto male
Tutti e due:
  python3 volta_microfono.py stato            JSON: ponte locale, ingresso attuale, BlackHole presente
  python3 volta_microfono.py --prova          esce 0

Regole:
  - il ponte locale vive finché il mod lo rinnova: senza un `accendi` per SCADENZA secondi si chiude
    da solo (Volta chiusa, mod fermo, macchina in stop);
  - `ricevi` non tocca niente se BlackHole manca o se un altro ponte è vivo; salva l'UID dell'ingresso
    di prima e lo rimette quando il flusso finisce, anche su SIGTERM e SIGHUP;
  - l'ingresso di prima torna solo se l'ingresso attuale è ancora BlackHole: una scelta fatta a mano
    nel frattempo non si tocca;
  - il ricevitore chiude da solo dopo SILENZIO secondi senza audio in arrivo: la rete è caduta;
  - `ripara` copre il ricevitore ucciso senza poter ripulire (kill -9, riavvio).

Sta nella cartella del mod, come volta_sonda.py: arriva su ogni macchina con l'aggiornamento del mod, e
il ponte lo trova là allo stesso posto (~/.config/herdr-app/mods/arturo).

Solo macOS per ora: su Windows `accendi` e `ricevi` rispondono che manca il supporto.
Variabili per i banchi: VOLTA_CACHE, VOLTA_MIC_AUDIO (un file JSON al posto di CoreAudio:
{"predefinito": uid, "ingressi": [{"uid", "nome"}]}), VOLTA_MIC_CATTURA, VOLTA_MIC_SUONA e
VOLTA_MIC_SSH (JSON: l'argv che sostituisce ffmpeg di cattura, ffmpeg di uscita e ssh col comando),
VOLTA_MIC_SCADENZA e VOLTA_MIC_SILENZIO (secondi).
Solo libreria standard, Python 3.8+.
"""
from __future__ import annotations

import json
import os
import re
import select
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

VIRTUALE = "BlackHole"          # il microfono virtuale si riconosce dal nome
SCADENZA = float(os.environ.get("VOLTA_MIC_SCADENZA") or 100)   # secondi senza rinnovo dopo i quali il ponte locale si chiude
FREQUENZA = 16000               # PCM 16 bit mono in viaggio: basta alla voce, 32 kB al secondo
SILENZIO = float(os.environ.get("VOLTA_MIC_SILENZIO") or 8)     # secondi senza un byte dopo i quali il ricevitore chiude: la rete è caduta


def cache() -> Path:
    return Path(os.environ.get("VOLTA_CACHE") or Path.home() / ".cache" / "volta")


def leggi(f: Path) -> dict:
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def scrivi(f: Path, dati: dict) -> None:
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_name(f.name + ".%d.tmp" % os.getpid())
    tmp.write_text(json.dumps(dati, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(str(tmp), str(f))


def vivo(pid) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except PermissionError:
        return True
    except OSError:
        return False


def finto(nome: str):
    v = os.environ.get(nome)
    return json.loads(v) if v else None


def ffmpeg() -> str | None:
    for p in (shutil.which("ffmpeg"), "/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg"):
        if p and os.path.exists(p):
            return p
    return None


# ---- l'ingresso predefinito: CoreAudio con ctypes, niente da installare ----

class Audio:
    """ingressi() -> [{"uid", "nome"}], predefinito() -> uid, metti(uid) -> bool."""

    def __init__(self):
        import ctypes
        import struct
        self.c, self.s = ctypes, struct
        self.ca = ctypes.CDLL("/System/Library/Frameworks/CoreAudio.framework/CoreAudio")
        self.cf = ctypes.CDLL("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
        u32, vp = ctypes.c_uint32, ctypes.c_void_p

        class Indirizzo(ctypes.Structure):
            _fields_ = [("selettore", u32), ("ambito", u32), ("elemento", u32)]
        self.Indirizzo = Indirizzo
        pi, pu = ctypes.POINTER(Indirizzo), ctypes.POINTER(u32)
        self.ca.AudioObjectGetPropertyDataSize.argtypes = [u32, pi, u32, vp, pu]
        self.ca.AudioObjectGetPropertyData.argtypes = [u32, pi, u32, vp, pu, vp]
        self.ca.AudioObjectSetPropertyData.argtypes = [u32, pi, u32, vp, u32, vp]
        self.cf.CFStringGetCString.argtypes = [vp, ctypes.c_char_p, ctypes.c_long, u32]
        self.cf.CFStringGetCString.restype = ctypes.c_bool
        self.cf.CFRelease.argtypes = [vp]

    def _q(self, quattro: str) -> int:
        return self.s.unpack(">I", quattro.encode("ascii"))[0]

    def _dato(self, oggetto: int, selettore: str, ambito: str = "glob") -> bytes:
        c = self.c
        a = self.Indirizzo(self._q(selettore), self._q(ambito), 0)
        n = c.c_uint32(0)
        if self.ca.AudioObjectGetPropertyDataSize(oggetto, c.byref(a), 0, None, c.byref(n)) != 0 or not n.value:
            return b""
        buf = c.create_string_buffer(n.value)
        if self.ca.AudioObjectGetPropertyData(oggetto, c.byref(a), 0, None, c.byref(n), buf) != 0:
            return b""
        return buf.raw[:n.value]

    def _testo(self, oggetto: int, selettore: str) -> str:
        c = self.c
        b = self._dato(oggetto, selettore)
        if len(b) != c.sizeof(c.c_void_p):
            return ""
        ref = c.c_void_p(self.s.unpack("@P", b)[0])
        out = c.create_string_buffer(512)
        riuscito = self.cf.CFStringGetCString(ref, out, 512, 0x08000100)  # UTF-8
        self.cf.CFRelease(ref)
        return out.value.decode("utf-8", "replace") if riuscito else ""

    def _dispositivi(self) -> list:
        b = self._dato(1, "dev#")  # 1 = kAudioObjectSystemObject
        return [i for i in self.s.unpack("@%dI" % (len(b) // 4), b) if self._dato(i, "stm#", "inpt")]

    def ingressi(self) -> list:
        return [{"uid": self._testo(i, "uid "), "nome": self._testo(i, "lnam")} for i in self._dispositivi()]

    def predefinito(self) -> str:
        b = self._dato(1, "dIn ")
        return self._testo(self.s.unpack("@I", b)[0], "uid ") if len(b) == 4 else ""

    def metti(self, uid: str) -> bool:
        c = self.c
        for i in self._dispositivi():
            if self._testo(i, "uid ") == uid:
                a = self.Indirizzo(self._q("dIn "), self._q("glob"), 0)
                v = c.c_uint32(i)
                return self.ca.AudioObjectSetPropertyData(1, c.byref(a), 0, None, 4, c.byref(v)) == 0
        return False


class AudioFinto:
    """Lo stesso contratto su un file JSON, per i banchi."""

    def __init__(self, file: str):
        self.f = Path(file)

    def ingressi(self) -> list:
        return leggi(self.f).get("ingressi") or []

    def predefinito(self) -> str:
        return leggi(self.f).get("predefinito") or ""

    def metti(self, uid: str) -> bool:
        d = leggi(self.f)
        if not any(x.get("uid") == uid for x in d.get("ingressi") or []):
            return False
        d["predefinito"] = uid
        scrivi(self.f, d)
        return True


def audio():
    """L'audio di questa macchina, o None dove non si sa leggerlo (Windows, Linux)."""
    file = os.environ.get("VOLTA_MIC_AUDIO")
    if file:
        return AudioFinto(file)
    if sys.platform != "darwin":
        return None
    try:
        return Audio()
    except (OSError, AttributeError):
        return None


def virtuale(a) -> dict | None:
    return next((x for x in a.ingressi() if VIRTUALE.lower() in (x.get("nome") or "").lower()), None)


# ---- lato remoto ----

def file_remoto() -> Path:
    return cache() / "microfono.json"


def rimetti(a, stato: dict) -> bool:
    """L'ingresso di prima torna solo se l'attuale è ancora quello virtuale. True se l'ha cambiato."""
    prima, messo = stato.get("prima"), stato.get("virtuale")
    if prima and messo and prima != messo and a.predefinito() == messo:
        return a.metti(prima)
    return False


def cmd_ripara() -> int:
    stato = leggi(file_remoto())
    if not stato:
        print(json.dumps({"esito": "niente da riparare"}))
        return 0
    if vivo(stato.get("pid")):
        print(json.dumps({"esito": "ponte vivo"}))
        return 0
    a = audio()
    cambiato = rimetti(a, stato) if a else False
    file_remoto().unlink(missing_ok=True)
    print(json.dumps({"esito": "riparato", "rimesso": cambiato}))
    return 0


def indice_uscita(ff: str, nome: str) -> int | None:
    """L'indice che ffmpeg (audiotoolbox) dà al dispositivo: sta nell'elenco che stampa su stderr."""
    try:
        r = subprocess.run([ff, "-hide_banner", "-f", "lavfi", "-i", "anullsrc", "-t", "0.1", "-f", "audiotoolbox",
                            "-list_devices", "true", "-"], capture_output=True, text=True, errors="replace",
                           stdin=subprocess.DEVNULL, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    for riga in (r.stderr or "").splitlines():
        m = re.search(r"\[(\d+)\]\s+(.+?),\s", riga)
        if m and nome.lower() in m.group(2).lower():
            return int(m.group(1))
    return None


def cmd_ricevi() -> int:
    def esci(codice: int, **d) -> int:
        print(json.dumps(d, ensure_ascii=False), flush=True)
        return codice
    a = audio()
    if a is None:
        return esci(2, esito="errore", motivo="su questa macchina il ponte del microfono non c'è ancora")
    bh = virtuale(a)
    if not bh:
        return esci(3, esito="errore", motivo="manca BlackHole")
    stato = leggi(file_remoto())
    if vivo(stato.get("pid")):
        return esci(4, esito="errore", motivo="microfono usato da un'altra macchina")
    if stato:  # un ponte morto male: prima torna il suo ingresso, poi si parte da capo
        rimetti(a, stato)
        file_remoto().unlink(missing_ok=True)
    suona = finto("VOLTA_MIC_SUONA")
    if not suona:
        ff = ffmpeg()
        if not ff:
            return esci(5, esito="errore", motivo="manca ffmpeg")
        indice = indice_uscita(ff, bh["nome"])
        if indice is None:
            return esci(5, esito="errore", motivo="ffmpeg non vede BlackHole fra le uscite")
        suona = [ff, "-loglevel", "error", "-fflags", "nobuffer", "-probesize", "32", "-analyzeduration", "0",
                 "-f", "s16le", "-ar", str(FREQUENZA), "-ac", "1", "-i", "-",
                 "-ac", "2", "-ar", "48000", "-f", "audiotoolbox", "-audio_device_index", str(indice), "-"]
    prima = a.predefinito()
    stato = {"pid": os.getpid(), "prima": prima, "virtuale": bh["uid"], "da": time.time()}
    scrivi(file_remoto(), stato)

    def ferma(*_):
        raise SystemExit(0)
    for s in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
        signal.signal(s, ferma)
    figlio = None
    try:
        if prima != bh["uid"] and not a.metti(bh["uid"]):
            return esci(6, esito="errore", motivo="non riesco a cambiare l'ingresso audio")
        figlio = subprocess.Popen(suona, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(json.dumps({"esito": "attivo", "prima": prima}), flush=True)
        # Il flusso passa di qui e non va dritto a ffmpeg: la cattura manda audio di continuo, anche nel
        # silenzio, quindi SILENZIO secondi senza un byte vogliono dire rete caduta. sshd da solo se ne
        # accorgerebbe dopo ore, e intanto l'ingresso resterebbe quello virtuale.
        entrata = sys.stdin.fileno()
        while figlio.poll() is None:
            pronto, _, _ = select.select([entrata], [], [], SILENZIO)
            if not pronto:
                break
            pezzo = os.read(entrata, 8192)
            if not pezzo:
                break
            try:
                figlio.stdin.write(pezzo)
                figlio.stdin.flush()
            except (BrokenPipeError, OSError):
                break
        return 0
    finally:
        if figlio and figlio.poll() is None:
            figlio.kill()
        rimetti(a, stato)
        file_remoto().unlink(missing_ok=True)


# ---- lato locale ----

def file_locale() -> Path:
    return cache() / "microfono-locale.json"


def file_rinnovo() -> Path:
    return cache() / "microfono-rinnovo"


REMOTO = ('for p in /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do '
          'if [ -x "$p" ]; then exec "$p" "$HOME/.config/herdr-app/mods/arturo/volta_microfono.py" ricevi; fi; done; '
          'echo \'{"esito": "errore", "motivo": "manca python3"}\'')


def perche(testo: str) -> str:
    """L'errore di ffmpeg o di ssh in una frase per la barra."""
    t = testo.lower()
    if "not authorized" in t or "permission" in t or "input/output error" in t or "failed to create av capture" in t:
        return "permesso microfono negato"
    if "could not resolve" in t or "connection refused" in t or "timed out" in t or "permission denied (publickey" in t:
        return "l'altra macchina non risponde"
    righe = [x.strip() for x in testo.splitlines() if x.strip()]
    return righe[-1][:160] if righe else "il ponte si è chiuso"


def cmd_ponte(target: str) -> int:
    """Il processo che tiene il ponte: cattura | ssh. Lo lancia `accendi`, staccato da Volta."""
    stato = {"pid": os.getpid(), "target": target, "stato": "avvio", "da": time.time()}
    scrivi(file_locale(), stato)
    cattura = finto("VOLTA_MIC_CATTURA")
    if not cattura:
        ff = ffmpeg()
        if not ff:
            scrivi(file_locale(), dict(stato, stato="errore", motivo="manca ffmpeg"))
            return 5
        cattura = [ff, "-loglevel", "error", "-fflags", "nobuffer", "-probesize", "32", "-analyzeduration", "0",
                   "-f", "avfoundation", "-i", ":default", "-ac", "1", "-ar", str(FREQUENZA),
                   "-flush_packets", "1", "-f", "s16le", "-"]
    ssh = finto("VOLTA_MIC_SSH") or ["ssh", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
                                     "-o", "ServerAliveInterval=5", "-o", "ServerAliveCountMax=2", target, REMOTO]
    errori = cache() / "microfono.err"
    fermo = {"motivo": None}

    def ferma(*_):
        fermo["motivo"] = "spento"
    for s in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
        signal.signal(s, ferma)
    with open(errori, "wb") as err:
        a = subprocess.Popen(cattura, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=err)
        b = subprocess.Popen(ssh, stdin=a.stdout, stdout=subprocess.PIPE, stderr=err)
        a.stdout.close()

        def ascolta():  # la prima riga del ricevitore dice se il ponte è su o perché no
            for riga in b.stdout:
                try:
                    d = json.loads(riga.decode("utf-8", "replace"))
                except ValueError:
                    continue
                if d.get("esito") == "attivo":
                    scrivi(file_locale(), dict(stato, stato="attivo"))
                elif d.get("esito") == "errore":
                    fermo["motivo"] = d.get("motivo") or "errore sull'altra macchina"
        threading.Thread(target=ascolta, daemon=True).start()
        try:
            while fermo["motivo"] is None:
                if a.poll() is not None or b.poll() is not None:
                    time.sleep(0.3)  # lascia arrivare la riga del ricevitore
                    if fermo["motivo"] is None:
                        fermo["motivo"] = "caduto"
                    break
                try:
                    if time.time() - file_rinnovo().stat().st_mtime > SCADENZA:
                        fermo["motivo"] = "spento"
                except OSError:
                    fermo["motivo"] = "spento"
                time.sleep(0.5)
        finally:
            for p in (a, b):
                if p.poll() is None:
                    p.terminate()
            for p in (a, b):
                try:
                    p.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    p.kill()
    if fermo["motivo"] == "spento":
        file_locale().unlink(missing_ok=True)
        return 0
    motivo = fermo["motivo"]
    if motivo == "caduto":
        try:
            motivo = perche(errori.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            motivo = "il ponte si è chiuso"
    scrivi(file_locale(), dict(stato, stato="errore", motivo=motivo, fine=time.time()))
    return 1


def stato_locale() -> dict:
    d = leggi(file_locale())
    if not d:
        return {"stato": "spento"}
    if d.get("stato") in ("avvio", "attivo") and not vivo(d.get("pid")):
        return {"stato": "errore", "target": d.get("target"), "motivo": "il ponte si è chiuso"}
    return {k: d.get(k) for k in ("stato", "target", "motivo") if d.get(k) is not None}


def ferma_locale() -> None:
    d = leggi(file_locale())
    pid = d.get("pid")
    if d.get("stato") in ("avvio", "attivo") and vivo(pid):
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
        for _ in range(40):
            if not vivo(pid):
                break
            time.sleep(0.1)
    file_locale().unlink(missing_ok=True)


def cmd_accendi(argv: list) -> int:
    if len(argv) != 1 or argv[0].startswith("-"):
        print("uso: volta_microfono.py accendi <target ssh>")
        return 2
    target = argv[0]
    if os.name == "nt":
        print(json.dumps({"stato": "errore", "target": target, "motivo": "su Windows il ponte del microfono non c'è ancora"}))
        return 0
    cache().mkdir(parents=True, exist_ok=True)
    file_rinnovo().write_text(str(time.time()), encoding="utf-8")
    d = leggi(file_locale())
    stesso = d.get("target") == target
    if stesso and d.get("stato") in ("avvio", "attivo") and vivo(d.get("pid")):
        print(json.dumps(stato_locale(), ensure_ascii=False))
        return 0
    # dopo un errore sullo stesso target si riprova solo dopo mezzo minuto: niente raffica di ssh
    if stesso and d.get("stato") == "errore" and time.time() - float(d.get("fine") or 0) < 30:
        print(json.dumps(stato_locale(), ensure_ascii=False))
        return 0
    ferma_locale()
    registro = open(cache() / "microfono.log", "ab")
    p = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "ponte", target], stdin=subprocess.DEVNULL,
                         stdout=registro, stderr=registro, start_new_session=True)
    scrivi(file_locale(), {"pid": p.pid, "target": target, "stato": "avvio", "da": time.time()})
    print(json.dumps({"stato": "avvio", "target": target}))
    return 0


def cmd_spegni() -> int:
    ferma_locale()
    print(json.dumps({"stato": "spento"}))
    return 0


def cmd_stato() -> int:
    d = {"locale": stato_locale()}
    a = audio()
    if a is not None:
        r = leggi(file_remoto())
        d["remoto"] = {"virtuale": bool(virtuale(a)), "ingresso": a.predefinito(), "ponte": vivo(r.get("pid")),
                       "prima": r.get("prima")}
    print(json.dumps(d, ensure_ascii=False))
    return 0


def main(argv: list) -> int:
    if argv[:1] == ["--prova"]:
        return 0
    if argv[:1] == ["accendi"]:
        return cmd_accendi(argv[1:])
    if argv[:1] == ["ponte"] and len(argv) == 2:
        return cmd_ponte(argv[1])
    if argv[:1] == ["spegni"]:
        return cmd_spegni()
    if argv[:1] == ["ricevi"]:
        return cmd_ricevi()
    if argv[:1] == ["ripara"]:
        return cmd_ripara()
    if argv[:1] == ["stato"]:
        return cmd_stato()
    print(__doc__.strip())
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
