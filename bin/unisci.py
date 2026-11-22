#!/usr/bin/env python3
"""arturo progetti unisci: due progetti doppioni diventano uno, e il nome del perdente resta valido.

Uso: arturo progetti unisci PERDENTE VINCITORE [--prova] [--json]

Nasce dal piano di Volta del 20/11/2026 (Fase 4, #6187): in Volta c'erano doppioni come volta, herdr-arturo
e volta-celeste, e l'unione si faceva a mano. Il comando porta dal perdente al vincitore:
  - i todo del perdente, aperti e chiusi, e la sua riga di stato se è più recente;
  - gli handoff, con "- Nome:" e "- Filone:" riscritti; un nome di file già preso dal vincitore passa al
    primo minuto libero, così resta un handoff che /inizio legge; INDEX.md si rigenera;
  - la scheda: il vincitore prende negli alias il perdente e i suoi alias, i campi del codice che non ha
    (cartella, repo, macchina) e in fondo il corpo del perdente sotto "## Da <perdente> (unito il <data>)".
    La scheda del perdente va in _archive/progetti/ con `status: closed` e `unito_in:`. Se il vincitore
    non ha una scheda, la scheda del perdente diventa la sua, come in arturo progetti rinomina;
  - i link [[progetto-<perdente>]] delle altre note e il progetto delle schede dei terminali (cache/scheda);
  - nella fonte esterna dei task, se c'è, il verbo facoltativo `unisci` (docs/fonte-task.md).

Prima di scrivere il comando copia tutto quello che cambia in data/progetti/unioni/<ora>-<perdente>-in-<vincitore>/,
rilegge la copia e conta i file: se la copia non torna, si ferma senza scrivere. --prova stampa
l'anteprima e non scrive niente; --json dà l'anteprima o l'esito in JSON, per Volta.
Si rifiuta se i due progetti hanno due cartelle di codice con repo diversi: due codici non si uniscono qui.
Exit: 0 fatto · 2 non si può (repo diversi, niente da unire, copia che non torna, rifiuto della fonte)
· 3 uso sbagliato o fonte giù.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

QUI = Path(os.path.realpath(__file__)).parent
sys.path.insert(0, str(QUI))
import contesto as cx  # noqa: E402
import progetti as pg  # noqa: E402
import rinomina as rn  # noqa: E402
import todo_store as ts  # noqa: E402

ATTESA_FONTE = 300  # secondi: la fonte sposta i task uno per uno
NOME_HANDOFF = re.compile(r"^HANDOFF_(\d{4}-\d{2}-\d{2})_(\d{2})-(\d{2})\.md$")
CAMPI_CODICE = ("cartella", "repo", "macchina")


GIU = {"giu": True}  # l'anteprima con la fonte giù: l'unione vera non parte


class Ferma(Exception):
    def __init__(self, codice: int, testo: str):
        super().__init__(testo)
        self.codice = codice


# --- frontmatter ------------------------------------------------------------------------------------

def dividi_scheda(testo: str) -> tuple:
    """(righe del frontmatter senza i ---, corpo). Errore se il frontmatter manca o non si chiude."""
    righe = testo.splitlines(keepends=True)
    if not righe or righe[0].strip() != "---":
        raise ValueError("la scheda non ha il frontmatter")
    fine = next((i for i, r in enumerate(righe[1:], 1) if r.strip() == "---"), None)
    if fine is None:
        raise ValueError("il frontmatter della scheda non si chiude")
    return righe[1:fine], "".join(righe[fine + 1:])


def campo(fm: list, chiave: str):
    for r in fm:
        if r.startswith(chiave + ":"):
            return r[len(chiave) + 1:].strip()
    return None


def lista(valore) -> list:
    if not valore:
        return []
    return [x.strip().strip("\"'") for x in valore.strip("[]").split(",") if x.strip().strip("\"'")]


def metti(fm: list, chiave: str, valore: str) -> list:
    """Il frontmatter con `chiave: valore`, al posto della riga che c'è o in fondo."""
    fuori, messo = [], False
    for r in fm:
        if r.startswith(chiave + ":"):
            fuori.append(f"{chiave}: {valore}\n")
            messo = True
        else:
            fuori.append(r)
    if not messo:
        fuori.append(f"{chiave}: {valore}\n")
    return fuori


def scheda_vincitrice(testo_v: str, testo_p: str, perdente: str, vincitore: str, giorno: str) -> str:
    fm_v, corpo_v = dividi_scheda(testo_v)
    fm_p, corpo_p = dividi_scheda(testo_p)
    alias = [a for a in lista(campo(fm_v, "alias")) if cx.slug(a) != vincitore]
    for a in [perdente] + lista(campo(fm_p, "alias")):
        if cx.slug(a) != vincitore and cx.slug(a) not in (cx.slug(x) for x in alias):
            alias.append(a)
    fm_v = metti(fm_v, "alias", f"[{', '.join(alias)}]")
    for c in CAMPI_CODICE:
        if not campo(fm_v, c) and campo(fm_p, c):
            fm_v = metti(fm_v, c, campo(fm_p, c))
    corpo_v = corpo_v.rstrip("\n") + "\n" if corpo_v.strip() else ""
    unito = f"\n## Da {perdente} (unito il {giorno})\n\n{corpo_p.strip()}\n" if corpo_p.strip() else ""
    return "---\n" + "".join(fm_v) + "---\n" + corpo_v + unito


def scheda_archiviata(testo_p: str, vincitore: str) -> str:
    fm, corpo = dividi_scheda(testo_p)
    fm = metti(metti(fm, "status", "closed"), "unito_in", f"progetto-{vincitore}")
    return "---\n" + "".join(fm) + "---\n" + corpo


# --- raccolta ---------------------------------------------------------------------------------------

def git_remoto(cartella: Path) -> str:
    return cx.git(cartella, "remote", "get-url", "origin") if cx.e_cartella(cartella) else ""


def codice_di(s: str) -> tuple:
    """(cartella risolta o None, repo o "") del progetto: la cartella nella base o `cartella:` della scheda."""
    cartella = rn.cartella_progetto(s)
    scheda = pg.scheda_di(s)
    testa = pg.testa(scheda) if scheda else {}
    if cartella is None and testa.get("dove"):
        cartella = Path(os.path.expanduser(testa["dove"]))
    repo = git_remoto(cartella) if cartella else ""
    return (Path(os.path.realpath(cartella)) if cartella else None), (repo or testa.get("repo") or "")


def piano_handoff(perdente: str, vincitore: str) -> list:
    """[(origine, nome nella cartella del vincitore)]: un nome già preso passa al primo minuto libero."""
    hd_p, hd_v = cx.handoff_dir() / perdente, cx.handoff_dir() / vincitore
    if not cx.e_cartella(hd_p):
        return []
    if hd_p.is_symlink() or os.path.realpath(hd_p) != os.path.join(os.path.realpath(hd_p.parent), hd_p.name):
        # herdr-arturo -> volta (17/11/2026): spostare i file del collegamento li rinominava nella cartella stessa
        if os.path.realpath(hd_p) == os.path.realpath(hd_v):
            return []
        raise Ferma(2, f"la cartella degli handoff {hd_p} è un collegamento a {os.path.realpath(hd_p)}: "
                       "sistemala a mano, poi rilancia")
    presi = {p.name for p in hd_v.iterdir()} if cx.e_cartella(hd_v) else set()
    fuori = []
    for p in sorted(hd_p.iterdir()):
        nome = p.name
        if nome in presi:
            m = NOME_HANDOFF.match(nome)
            if m:
                ora = dt.datetime.strptime(f"{m.group(1)} {m.group(2)}:{m.group(3)}", "%Y-%m-%d %H:%M")
                while nome in presi:
                    ora += dt.timedelta(minutes=1)
                    nome = ora.strftime("HANDOFF_%Y-%m-%d_%H-%M.md")
            elif nome.startswith("."):
                # Un file col punto (.ultimo-fine-completo) diventava "-<perdente>.ultimo-fine-completo": un nome
                # col trattino davanti e visibile (revisione del 20/11, bug 16). Il perdente va in coda e il punto resta.
                nome = f"{nome}-{perdente}"
            else:
                base, punto, est = nome.partition(".")
                nome = f"{base}-{perdente}{punto}{est}"
                while nome in presi:
                    nome = "_" + nome
        presi.add(nome)
        fuori.append((p, nome))
    return fuori


def schede_terminali(perdente: str) -> dict:
    """{file: dati nuovi} delle schede dei terminali (cache/scheda/*.json) col progetto del perdente."""
    fuori = {}
    d = cx.radice_orsa() / "cache" / "scheda"
    try:
        voci = sorted(d.glob("*.json"))
    except OSError:
        return fuori
    for f in voci:
        try:
            dati = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(dati, dict) and cx.slug(str(dati.get("progetto") or "")) == perdente:
            fuori[f] = dati
    return fuori


def chiama_fonte(argomenti: list) -> tuple:
    """(exit, JSON o None, ultima riga d'errore) del verbo unisci della fonte; None se non c'è fonte."""
    comando = ts.comando_fonte()
    if not comando:
        return None
    try:
        r = subprocess.run(comando + argomenti, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=ATTESA_FONTE, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError) as e:
        return 3, None, f"la fonte non risponde ({type(e).__name__})"
    try:
        dati = json.loads(r.stdout) if r.stdout.strip() else None
    except ValueError:
        dati = None
    errore = (r.stderr.strip().splitlines() or [""])[-1]
    return r.returncode, dati if isinstance(dati, dict) else None, errore


def esito_fonte(risposta, avvisi: list, perdente: str, prova: bool = False):
    """Il JSON della fonte, oppure None con un avviso; Ferma se la fonte rifiuta, o se è giù fuori dall'anteprima."""
    if risposta is None:
        return None
    codice, dati, errore = risposta
    if codice == 0 and dati is not None:
        avvisi.extend(str(a) for a in dati.get("avvisi") or [])
        return dati
    if codice == 2 and dati and dati.get("rifiuto"):
        raise Ferma(2, f"la fonte dei task rifiuta l'unione: {dati['rifiuto']}")
    if codice == 2:
        avvisi.append(f"la fonte dei task non sa unire ({errore or 'verbo unisci sconosciuto'}): i task di "
                      f"{perdente} restano lì, spostali a mano")
        return None
    if prova:
        avvisi.append(f"la fonte dei task è giù (uscita {codice}): l'anteprima non conta i suoi task, e l'unione "
                      "vera aspetta che torni")
        return GIU
    raise Ferma(3, f"la fonte dei task è giù o incerta (uscita {codice}: {errore}): niente scritto, riprova dopo")


def raccogli(perdente: str, vincitore: str) -> dict:
    cod_p, cod_v = codice_di(perdente), codice_di(vincitore)
    if cod_p[0] and cod_v[0] and cod_p[0] != cod_v[0] and not (cod_p[1] and cod_p[1] == cod_v[1]):
        raise Ferma(2, f"{perdente} e {vincitore} hanno due cartelle di codice con repo diversi "
                       f"({cod_p[0]}: {cod_p[1] or 'senza repo'}; {cod_v[0]}: {cod_v[1] or 'senza repo'}). "
                       "Due codici non si uniscono qui: unisci prima i repo, o tieni due progetti")
    todo = rn.todo_del(perdente)
    stati = ts.stati()
    stato_p, stato_v = stati.get(perdente), stati.get(vincitore)
    porta_stato = bool(stato_p) and (not stato_v or stato_p["ts"] > stato_v["ts"])
    handoff = piano_handoff(perdente, vincitore)
    sch_p, sch_v = pg.scheda_di(perdente), pg.scheda_di(vincitore)
    if sch_p and sch_v and os.path.samefile(sch_p, sch_v):
        sch_p = None  # una scheda collegata all'altra è già la stessa scheda
    testi = {}
    try:
        for f in (sch_p, sch_v):
            if f is not None:
                testi[f] = f.read_text(encoding="utf-8")
                dividi_scheda(testi[f])
    except (OSError, UnicodeDecodeError, ValueError) as e:
        raise Ferma(2, f"scheda non leggibile: {e}")
    terminali = schede_terminali(perdente)
    if not (todo or stato_p or handoff or sch_p or terminali):
        raise Ferma(2, f"non trovo niente di {perdente}: né todo, né stato, né handoff, né scheda")
    salta = {f for f in (sch_p, sch_v) if f is not None}
    link = {f: t for f, t in rn.link_nelle_note(perdente, vincitore, None).items() if f not in salta}
    return {"todo": todo, "stato_p": stato_p, "porta_stato": porta_stato, "handoff": handoff,
            "sch_p": sch_p, "sch_v": sch_v, "testi": testi, "link": link, "terminali": terminali}


def anteprima(perdente: str, vincitore: str, r: dict, fonte, avvisi: list) -> dict:
    rinominati = [{"da": p.name, "a": nome} for p, nome in r["handoff"] if p.name != nome]
    if r["sch_p"] and r["sch_v"]:
        scheda = f"{r['sch_p'].name} entra in {r['sch_v'].name}, l'originale va in _archive/progetti/"
    elif r["sch_p"]:
        scheda = f"{r['sch_p'].name} diventa progetto-{vincitore}.md"
    else:
        scheda = "nessuna scheda del perdente"
    return {"perdente": perdente, "vincitore": vincitore, "todo": len(r["todo"]),
            "stato": r["porta_stato"],
            "handoff": sum(1 for p, _ in r["handoff"] if p.name.startswith("HANDOFF_")),
            "altri_file": sum(1 for p, _ in r["handoff"] if not p.name.startswith("HANDOFF_")),
            "rinominati": rinominati, "scheda": scheda, "link": len(r["link"]),
            "terminali": len(r["terminali"]), "fonte": fonte, "avvisi": avvisi}


def righe_anteprima(a: dict) -> list:
    righe = [f"{a['perdente']} → {a['vincitore']}",
             f"  todo: {a['todo']}",
             f"  riga di stato: {'sì' if a['stato'] else 'no'}",
             f"  handoff: {a['handoff']}" + (f", altri file: {a['altri_file']}" if a["altri_file"] else ""),
             f"  scheda: {a['scheda']}",
             f"  link nelle altre note: {a['link']}",
             f"  schede dei terminali: {a['terminali']}"]
    for x in a["rinominati"]:
        righe.append(f"  nome già preso: {x['da']} diventa {x['a']}")
    f = a["fonte"]
    if f and not f.get("giu"):
        righe.append(f"  fonte dei task: {f.get('task', 0)} task da spostare"
                     + (f" ({f['riassunto']})" if f.get("riassunto") else ""))
    return righe


# --- copia di sicurezza -----------------------------------------------------------------------------

def impronta(f: Path) -> str:
    return hashlib.sha256(f.read_bytes()).hexdigest()


def copia(perdente: str, vincitore: str, r: dict) -> Path:
    """Copia ogni file che l'unione cambia, scrive il manifesto, rilegge e conta. Ferma se non torna."""
    ora = dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    dest = cx.radice_orsa() / "data" / "progetti" / "unioni" / f"{ora}-{perdente}-in-{vincitore}"
    file = [p for p, _ in r["handoff"]] + list(r["testi"]) + list(r["link"]) + list(r["terminali"])
    index = cx.handoff_dir() / "INDEX.md"
    for extra in (index, ts.percorso(), ts.percorso_stati()):
        if extra.is_file():
            file.append(extra)
    manifesto = []
    dest.mkdir(parents=True, exist_ok=False)
    for n, f in enumerate(f for f in file if f.is_file() or f.is_dir()):
        copia_f = dest / "file" / f"{n:03d}-{f.name}"
        copia_f.parent.mkdir(parents=True, exist_ok=True)
        if f.is_dir():
            shutil.copytree(str(f), str(copia_f))
            manifesto.append({"origine": str(f), "copia": str(copia_f), "cartella": True})
        else:
            shutil.copy2(str(f), str(copia_f))
            manifesto.append({"origine": str(f), "copia": str(copia_f), "sha256": impronta(f)})
    (dest / "manifesto.json").write_text(json.dumps({"perdente": perdente, "vincitore": vincitore, "ora": ora,
                                                     "file": manifesto}, ensure_ascii=False, indent=1) + "\n",
                                         encoding="utf-8")
    riletto = json.loads((dest / "manifesto.json").read_text(encoding="utf-8"))["file"]
    sbagliati = [v["origine"] for v in riletto
                 if not Path(v["copia"]).exists()
                 or (not v.get("cartella") and impronta(Path(v["copia"])) != v["sha256"])]
    if len(riletto) != len(manifesto) or sbagliati:
        raise Ferma(2, f"la copia di sicurezza in {dest} non torna ({len(sbagliati)} file): niente scritto")
    return dest


# --- scrittura --------------------------------------------------------------------------------------

def ripristina(backup: Path, creati: list) -> list:
    """Rimette i file della copia di sicurezza e toglie quelli che l'unione ha creato. Torna i file non rimessi."""
    voci = json.loads((backup / "manifesto.json").read_text(encoding="utf-8"))["file"]
    origini = {v["origine"] for v in voci}
    for f in reversed(creati):
        if str(f) not in origini:
            try:
                Path(f).unlink()
            except OSError:
                pass
    mancati = []
    for v in voci:
        origine, copia_f = Path(v["origine"]), Path(v["copia"])
        try:
            origine.parent.mkdir(parents=True, exist_ok=True)
            if v.get("cartella"):
                if origine.exists():
                    shutil.rmtree(str(origine))
                shutil.copytree(str(copia_f), str(origine))
            else:
                shutil.copy2(str(copia_f), str(origine))
        except OSError:
            mancati.append(str(origine))
    return mancati


def scrivi(perdente: str, vincitore: str, r: dict, avvisi: list, creati: list | None = None) -> None:
    """`creati` riceve ogni file che non c'era prima, prima di crearlo: ripristina() li toglie."""
    creati = [] if creati is None else creati
    oggi = ts.oggi()
    giorno = f"{oggi.day}/{oggi.month}/{oggi.year}"
    if r["todo"]:
        eventi = [ts._evento("modifica", t["uid"], ts.normalizza({"progetto": vincitore})) for t in r["todo"]]
        ts._scrivi_molti(eventi, ts.percorso())
        rimasti = rn.todo_del(perdente)
        if rimasti:
            raise Ferma(2, f"rileggendo il registro {len(rimasti)} todo hanno ancora {perdente}: mi fermo qui")
    if r["porta_stato"]:
        ts.scrivi_stato(vincitore, r["stato_p"]["riga"])
    hd_p, hd_v = cx.handoff_dir() / perdente, cx.handoff_dir() / vincitore
    if r["handoff"]:
        hd_v.mkdir(parents=True, exist_ok=True)
        for p, nome in r["handoff"]:
            creati.append(hd_v / nome)
            shutil.move(str(p), str(hd_v / nome))
        try:
            hd_p.rmdir()
        except OSError:
            avvisi.append(f"la cartella {hd_p} non è vuota: guarda cosa è rimasto")
        for f, testo in rn.handoff_nuovi(hd_v, perdente, vincitore).items():
            rn.scrivi_atomico(f, testo)
    index = cx.handoff_dir() / "INDEX.md"
    if index.exists():
        try:
            testo = index.read_text(encoding="utf-8")
            nuovo = rn.index_nuovo(testo, perdente, vincitore)
            for p, nome in r["handoff"]:
                if p.name != nome:
                    nuovo = nuovo.replace(f"{vincitore}/{p.name})", f"{vincitore}/{nome})")
            if nuovo != testo:
                rn.scrivi_atomico(index, nuovo)
        except (OSError, UnicodeDecodeError) as e:
            avvisi.append(f"INDEX.md non letto: {e}")
    if r["handoff"] or index.exists():
        g = subprocess.run([sys.executable, str(QUI / "index-rigenera.py"), "--scrivi"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if g.returncode != 0:
            avvisi.append("INDEX.md non rigenerato: " + (g.stderr.strip().splitlines() or ["errore"])[-1])
    sch_p, sch_v, testi = r["sch_p"], r["sch_v"], r["testi"]
    if sch_p and sch_v:
        nuovo_v = scheda_vincitrice(testi[sch_v], testi[sch_p], perdente, vincitore, giorno)
        rn.scrivi_atomico(sch_v, link_testo(nuovo_v, perdente, vincitore))
        radice = next((x for x in pg.radici_memoria() if dentro(sch_p, x)), sch_p.parent)
        archivio = radice / "_archive" / "progetti"
        archivio.mkdir(parents=True, exist_ok=True)
        dest = archivio / sch_p.name
        if dest.exists():
            dest = archivio / f"{sch_p.stem}-unito-{ts.oggi().isoformat()}.md"
        rn.scrivi_atomico(sch_p, scheda_archiviata(testi[sch_p], vincitore))
        creati.append(dest)
        os.replace(sch_p, dest)
    elif sch_p:
        rn.scrivi_atomico(sch_p, rn.scheda_nuova(testi[sch_p], perdente, vincitore))
        creati.append(sch_p.with_name(f"progetto-{vincitore}.md"))
        os.replace(sch_p, sch_p.with_name(f"progetto-{vincitore}.md"))
    elif sch_v:
        fm, corpo = dividi_scheda(testi[sch_v])
        alias = lista(campo(fm, "alias"))
        if perdente not in (cx.slug(a) for a in alias):
            rn.scrivi_atomico(sch_v, "---\n" + "".join(metti(fm, "alias", f"[{', '.join(alias + [perdente])}]"))
                              + "---\n" + corpo)
    for f, testo in r["link"].items():
        rn.scrivi_atomico(f, testo)
    for f, dati in r["terminali"].items():
        rn.scrivi_atomico(f, json.dumps({**dati, "progetto": vincitore}, ensure_ascii=False))


def dentro(f: Path, radice: Path) -> bool:
    try:
        f.relative_to(radice)
        return True
    except ValueError:
        return False


def link_testo(testo: str, perdente: str, vincitore: str) -> str:
    forma = re.compile(r"\[\[progetto-" + re.escape(perdente) + r"(?=[\]|#])")
    return forma.sub(f"[[progetto-{vincitore}", testo)


def unisci(perdente_nome: str, vincitore_nome: str, prova: bool = False, come_json: bool = False) -> int:
    perdente, vincitore = cx.slug(perdente_nome), cx.slug(vincitore_nome)
    if not perdente or not vincitore:
        raise Ferma(3, "i due nomi devono avere almeno una lettera o una cifra")
    if perdente == vincitore:
        raise Ferma(3, f'"{perdente_nome}" e "{vincitore_nome}" sono lo stesso progetto, {vincitore}')
    avvisi: list = []
    r = raccogli(perdente, vincitore)
    fonte = esito_fonte(chiama_fonte(["unisci", perdente, vincitore, "--prova", "--json"]), avvisi, perdente, prova)
    a = anteprima(perdente, vincitore, r, fonte, avvisi)
    if prova:
        if come_json:
            print(json.dumps({**a, "prova": True, "fatto": False, "backup": None}, ensure_ascii=False))
        else:
            print("\n".join(["Prova, niente scritto:"] + righe_anteprima(a)))
            for x in avvisi:
                print(f"AVVISO: {x}")
        return 0
    backup = copia(perdente, vincitore, r)
    # Prima le scritture locali, che si possono rimettere dalla copia, poi la fonte esterna, che non torna
    # indietro. Fino al 22/11/2026 l'ordine era l'opposto e senza ritorno: un errore in scrivi() lasciava i task
    # della fonte già uniti, i todo spostati e gli handoff a metà (revisione del 20/11, bug 16).
    creati: list = []
    try:
        scrivi(perdente, vincitore, r, avvisi, creati)
        if fonte is not None:
            fatto = esito_fonte(chiama_fonte(["unisci", perdente, vincitore, "--backup", str(backup / "fonte"),
                                              "--json"]), avvisi, perdente)
            a["fonte"] = fatto
    except BaseException as e:
        mancati = ripristina(backup, creati)
        stato = (f"non ho potuto rimettere {len(mancati)} file, li trovi in {backup}: {', '.join(mancati[:3])}"
                 if mancati else f"ho rimesso tutto com'era dalla copia {backup}")
        if isinstance(e, Ferma):
            raise Ferma(e.codice, f"{e}. Unione annullata: {stato}") from None
        print(f"ERRORE: l'unione si è fermata a metà ({type(e).__name__}): {stato}", file=sys.stderr)
        raise
    if come_json:
        print(json.dumps({**a, "prova": False, "fatto": True, "backup": str(backup)}, ensure_ascii=False))
    else:
        print("\n".join(["Fatto:"] + righe_anteprima(a)))
        for x in avvisi:
            print(f"AVVISO: {x}")
        print(f"Copia di prima: {backup}")
        print(f"Il nome {perdente} resta valido in /inizio e apre {vincitore}.")
    return 0


def main(argv: list) -> int:
    prova, come_json = "--prova" in argv, "--json" in argv
    nomi = [a for a in argv if a not in ("--prova", "--json")]
    if len(nomi) != 2 or any(a.startswith("-") for a in nomi):
        print("uso: arturo progetti unisci PERDENTE VINCITORE [--prova] [--json]", file=sys.stderr)
        return 3
    try:
        return unisci(nomi[0], nomi[1], prova, come_json)
    except Ferma as e:
        if come_json:
            print(json.dumps({"perdente": cx.slug(nomi[0]), "vincitore": cx.slug(nomi[1]), "fatto": False,
                              "rifiuto": str(e), "codice": e.codice}, ensure_ascii=False))
        print(f"Errore: {e}", file=sys.stderr)
        return e.codice


if __name__ == "__main__":
    for flusso in (sys.stdout, sys.stderr):
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
