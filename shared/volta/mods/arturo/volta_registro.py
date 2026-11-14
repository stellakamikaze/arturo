"""Volta: il registro degli eventi di questa macchina, per capire dove le sessioni si inceppano (#5549, 14/11/2026).

  python3 volta_registro.py scrivi [--righe JSON]   righe JSON da stdin, una per evento, o una lista JSON
                                                   come argomento (la manda volta.js a lotti)
  python3 volta_registro.py riassunto [--ore N] [--json] [--tutte]   cosa è successo nelle ultime N ore (24 di
                                                   serie); --tutte anche sulle macchine di hc machine ls

Un file per giorno, eventi-AAAA-MM-GG.jsonl, in <cartella di Volta>-registro (come cacheVolta("volta-registro")
di dati.js): ~/.cache/volta-registro per la finestra vera, <HERDR_APP_HOME>/cache/volta-registro per una
finestra di prova, VOLTA_REGISTRO per i banchi. Non in cacheVolta(): volta.js rilegge l'elenco a ogni cambio
di quella cartella. I file più vecchi di TENUTA giorni si tolgono alla prima scrittura del giorno.

Una riga tiene solo i campi di CAMPI, tagliati: verbo, macchina, id corto della sessione, durata, esito e la
prima riga dell'errore. Mai prompt, testo delle conversazioni o segreti. Una scrittura che non riesce non
ferma chi scrive: registra() non solleva mai.
Lo importano volta_sonda.py e volta_sposta.py (stessa cartella); volta.js lo chiama con `scrivi`.
"""
from __future__ import annotations

import json
import math
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True  # come gli altri script del mod: niente __pycache__ nella cartella (#5556)

TENUTA = 14
CAMPI = {"ora": 32, "fonte": 20, "evento": 40, "macchina": 60, "sid": 12, "esito": 20, "errore": 160}
ID = re.compile(r"[^0-9A-Za-z-]")


def cartella() -> Path:
    if os.environ.get("VOLTA_REGISTRO"):
        return Path(os.environ["VOLTA_REGISTRO"])
    serie = Path.home() / ".config" / "herdr-app"
    app = Path(os.environ.get("HERDR_APP_HOME") or serie)
    if os.path.normcase(os.path.abspath(app)) != os.path.normcase(os.path.abspath(serie)):
        return app / "cache" / "volta-registro"
    return Path.home() / ".cache" / "volta-registro"


def pulisci(d) -> dict | None:
    """La riga come entra nel registro, o None se non è un evento (manca evento o non è un oggetto)."""
    if not isinstance(d, dict) or not isinstance(d.get("evento"), str) or not d["evento"]:
        return None
    r = {}
    for k, n in CAMPI.items():
        v = d.get(k)
        if v is None or isinstance(v, (dict, list)):
            continue
        v = str(v)
        if k == "errore":
            v = (v.strip().splitlines() or [""])[0]
        if k == "sid":
            v = ID.sub("", v)
        r[k] = v[:n]
    ms = d.get("ms")
    if isinstance(ms, (int, float)) and not isinstance(ms, bool) and ms >= 0:
        r["ms"] = int(ms)
    quando = d.get("t")  # dal JS: millisecondi dall'epoca; l'ora si scrive qui, nell'ora locale
    if isinstance(quando, (int, float)) and not isinstance(quando, bool) and quando > 0:
        r["ora"] = time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(quando / 1000))
    r.setdefault("ora", time.strftime("%Y-%m-%dT%H:%M:%S%z"))
    return r


def file_del_giorno(c: Path, giorno: str) -> Path:
    return c / ("eventi-%s.jsonl" % giorno)


def togli_vecchi(c: Path, oggi: float) -> None:
    limite = time.strftime("%Y-%m-%d", time.localtime(oggi - TENUTA * 86400))
    for f in c.glob("eventi-*.jsonl"):
        if f.stem[len("eventi-"):] < limite:
            try:
                f.unlink()
            except OSError:
                pass


def scrivi_righe(righe) -> int:
    """Aggiunge le righe al file di oggi. Torna quante ne ha scritte; non solleva."""
    try:
        c = cartella()
        c.mkdir(parents=True, exist_ok=True)
        adesso = time.time()
        f = file_del_giorno(c, time.strftime("%Y-%m-%d", time.localtime(adesso)))
        if not f.exists():
            togli_vecchi(c, adesso)
        buone = [x for x in (pulisci(r) for r in righe) if x]
        if not buone:
            return 0
        testo = "".join(json.dumps(x, ensure_ascii=True, separators=(",", ":")) + "\n" for x in buone)
        with open(f, "a", encoding="utf-8") as fh:  # append: due scrittori insieme non si cancellano
            fh.write(testo)
        return len(buone)
    except (OSError, ValueError, TypeError):
        return 0


def registra(evento, fonte="sonda", **campi) -> None:
    """Un evento da Python. Non solleva mai: il registro non deve fermare Volta."""
    scrivi_righe([dict(campi, evento=evento, fonte=fonte)])


class Durata:
    """with Durata("giro", macchina=m) as d: ... ; d.esito = "errore"; d.errore = "..." -> una riga con ms."""

    def __init__(self, evento, fonte="sonda", **campi):
        self.evento, self.fonte, self.campi = evento, fonte, campi
        self.esito, self.errore = "ok", None

    def __enter__(self):
        self.t = time.monotonic()
        return self

    def __exit__(self, tipo, valore, _tb):
        if tipo is not None:
            self.esito, self.errore = "eccezione", "%s: %s" % (tipo.__name__, valore)
        registra(self.evento, self.fonte, ms=(time.monotonic() - self.t) * 1000, esito=self.esito,
                 errore=self.errore, **self.campi)
        return False


def leggi(ore: float) -> list:
    c = cartella()
    dal = time.time() - ore * 3600
    giorni = {time.strftime("%Y-%m-%d", time.localtime(dal + i * 86400)) for i in range(int(ore // 24) + 2)}
    righe = []
    for g in sorted(giorni):
        f = file_del_giorno(c, g)
        try:
            testo = f.read_text(encoding="utf-8")
        except OSError:
            continue
        for x in testo.splitlines():
            try:
                d = json.loads(x)
            except ValueError:
                continue  # una riga a metà (scrittura interrotta): si salta
            try:
                t = time.mktime(time.strptime(d.get("ora", "")[:19], "%Y-%m-%dT%H:%M:%S"))
            except (ValueError, TypeError):
                continue
            if t >= dal:
                righe.append(d)
    return righe


def quantile(v: list, q: float) -> int:
    """Il quantile q col rango più vicino: la mediana di [1, 9] è 1, il p95 è 9."""
    s = sorted(v)
    return s[min(len(s) - 1, max(0, math.ceil(q * len(s)) - 1))] if s else 0


def riassunto(righe: list) -> dict:
    """Per fonte, evento e macchina: quante volte, quanti errori, durate (mediana, p95, massimo) e gli
    errori più frequenti."""
    gruppi = {}
    for r in righe:
        k = (r.get("fonte", ""), r.get("evento", ""), r.get("macchina", ""))
        g = gruppi.setdefault(k, {"volte": 0, "errori": 0, "ms": [], "messaggi": {}})
        g["volte"] += 1
        if r.get("esito") not in (None, "ok"):
            g["errori"] += 1
            m = r.get("errore") or r.get("esito")
            g["messaggi"][m] = g["messaggi"].get(m, 0) + 1
        if isinstance(r.get("ms"), int):
            g["ms"].append(r["ms"])
    voci = []
    for (fonte, evento, macchina), g in sorted(gruppi.items()):
        voci.append({"fonte": fonte, "evento": evento, "macchina": macchina, "volte": g["volte"],
                     "errori": g["errori"], "mediana_ms": quantile(g["ms"], 0.5), "p95_ms": quantile(g["ms"], 0.95),
                     "max_ms": max(g["ms"]) if g["ms"] else 0,
                     "messaggi": sorted(g["messaggi"].items(), key=lambda x: -x[1])[:3]})
    return {"righe": len(righe), "voci": voci}


def stampa(r: dict, ore: float, qui: bool = True) -> str:
    if not r["righe"]:
        return "registro: nessun evento nelle ultime %g ore%s" % (ore, " (%s)" % cartella() if qui else "")
    out = ["registro: %d eventi nelle ultime %g ore" % (r["righe"], ore),
           "%-10s %-24s %-22s %6s %6s %8s %8s %8s" % ("fonte", "evento", "macchina", "volte", "errori", "mediana", "p95", "max")]
    for v in r["voci"]:
        out.append("%-10s %-24s %-22s %6d %6d %7.1fs %7.1fs %7.1fs" % (
            v["fonte"][:10], v["evento"][:24], (v["macchina"] or "-")[:22], v["volte"], v["errori"],
            v["mediana_ms"] / 1000, v["p95_ms"] / 1000, v["max_ms"] / 1000))
        for m, n in v["messaggi"]:
            out.append("    %dx %s" % (n, m))
    return "\n".join(out)


def altre_macchine(ore: float) -> list:
    """[(nome, riassunto o {"errore"})] delle macchine collegate di Herdr: questo file gira là con hc exec
    (python3, poi python), così non serve che il mod di là sia aggiornato."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import base64  # noqa: PLC0415
    import volta_sonda as vs  # noqa: PLC0415
    codice = ("import base64,sys;sys.argv=['r','riassunto','--json','--ore',%r];"
              "exec(compile(base64.b64decode(%r),'volta_registro','exec'))"
              % (str(ore), base64.b64encode(Path(__file__).read_bytes()).decode()))
    out = []
    for m in vs.macchine() or []:
        if m.get("stato") != "connected":
            out.append((m["nome"], {"errore": m.get("perche") or "Herdr non la raggiunge"}))
            continue
        d = {"errore": "nessun Python"}
        for py in ("python3", "python"):
            try:
                rc, so, se = vs.lancia(vs.hc() + ["exec", "--on", m["nome"], "--timeout", "40", py, "-c", codice], timeout=45)
            except (OSError, subprocess.SubprocessError) as e:
                d = {"errore": str(e)[:160]}
                break
            if rc != 0 and vs.non_parte(so, se):
                continue
            try:
                d = json.loads(so.strip().splitlines()[-1])
            except (ValueError, IndexError):
                d = {"errore": ((se or so).strip().splitlines() or ["rc %d" % rc])[-1][:160]}
            break
        out.append((m["nome"], d))
    return out


def main(argv: list) -> int:
    if argv[:1] == ["scrivi"]:
        righe = []
        if "--righe" in argv:  # volta.js: exec di Herdr non ha stdin, il lotto arriva come lista JSON
            try:
                d = json.loads(argv[argv.index("--righe") + 1])
                righe = d if isinstance(d, list) else []
            except (IndexError, ValueError):
                righe = []
        else:
            for x in sys.stdin.read().splitlines():
                try:
                    righe.append(json.loads(x))
                except ValueError:
                    pass
        print(json.dumps({"scritte": scrivi_righe(righe)}))
        return 0
    if argv[:1] == ["riassunto"]:
        ore = 24.0
        if "--ore" in argv:
            try:
                ore = max(0.1, float(argv[argv.index("--ore") + 1]))
            except (IndexError, ValueError):
                print("--ore vuole un numero", file=sys.stderr)
                return 2
        r = riassunto(leggi(ore))
        if "--tutte" not in argv:
            print(json.dumps(r, ensure_ascii=False) if "--json" in argv else stampa(r, ore))
            return 0
        tutte = [("questa macchina", r)] + altre_macchine(ore)
        if "--json" in argv:
            print(json.dumps(dict(tutte), ensure_ascii=False))
        else:
            print("\n\n".join("== %s\n%s" % (n, d["errore"] if "errore" in d else stampa(d, ore, n == "questa macchina"))
                               for n, d in tutte))
        return 0
    print(__doc__.strip().splitlines()[2], file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
