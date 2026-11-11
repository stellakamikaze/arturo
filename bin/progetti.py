#!/usr/bin/env python3
"""arturo progetti: tutti i progetti che la persona segue, letti dalla memoria che c'è già.

Uso: arturo progetti [--json]

Non crea e non scrive niente: unisce per slug quello che Arturo ha già su disco.
  - le cartelle della base dei progetti (PROJECTS_BASE);
  - gli handoff (data/handoffs/<slug>/): data dell'ultimo, stato e prossimo passo dall'INDEX.md, oppure
    dall'ultimo handoff quando l'INDEX manca o è più vecchio di lui;
  - le righe di stato dei progetti (arturo todo stato);
  - le schede progetto-<slug>.md della memoria, se ci sono: la loro descrizione;
  - il catalogo della fonte esterna dei task (fonte-task.local, verbo facoltativo "catalogo --json"): i
    progetti che stanno nello strumento della persona, con titolo, categoria e i nomi alternativi (alias).

Un nome alternativo senza handoff suoi (il nome vecchio di un progetto, il nome che ha nello strumento)
entra nella voce del progetto, in "alias". Un nome alternativo con i suoi handoff resta una voce a parte:
la persona lo apre da solo con /inizio, e dalla fonte prende solo la categoria.
Se la fonte non conosce "catalogo" o non risponde, resta l'elenco locale con un avviso.

Uscita --json: {versione, progetti: [{slug, nome, titolo, categoria, descrizione, riga, data, stato,
prossimo, filoni, cartella, handoff, alias, fonte}], avvisi}, dal progetto con l'handoff più recente.
Exit: 0 · 3 uso sbagliato.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

QUI = Path(os.path.realpath(__file__)).parent
sys.path.insert(0, str(QUI))
import contesto as cx  # noqa: E402
import todo_store as ts  # noqa: E402

VERSIONE = 1
ATTESA_FONTE = 10  # secondi: Volta rilegge l'elenco ogni 30 e non può restare appesa alla fonte
MAX_RIGA = 200
RIGHE_SCHEDA = 40  # il frontmatter di una scheda sta in cima: non serve leggerla tutta


def cartelle() -> dict:
    """{slug: nome} delle cartelle della base dei progetti, senza le nascoste e quelle con "_" davanti."""
    fuori = {}
    try:
        voci = sorted(cx.base_progetti().iterdir())
    except OSError:
        return fuori
    for p in voci:
        if p.name[:1] in "._" or not cx.e_cartella(p):
            continue
        s = cx.slug(p.name)
        if s:
            fuori.setdefault(s, p.name)
    return fuori


def ultimi_handoff() -> dict:
    """{slug: (nome cartella, data, percorso dell'ultimo handoff)}: si leggono solo i nomi dei file."""
    fuori = {}
    try:
        voci = sorted(cx.handoff_dir().iterdir())
    except OSError:
        return fuori
    for d in voci:
        if d.name.startswith(".") or not cx.e_cartella(d):
            continue
        lista = cx.handoff_di(d.name)
        s = cx.slug(d.name)
        if lista and s and (s not in fuori or lista[0][0] > fuori[s][2].name):
            fuori[s] = (d.name, lista[0][1], lista[0][3])
    return fuori


def righe_index(ix) -> dict:
    """{slug: {file, stato, prossimo, filoni}} dalla riga più recente di ogni progetto nell'INDEX."""
    fuori = {}
    for r in ix.leggi_index(cx.handoff_dir() / "INDEX.md"):
        cartella = r["file"].split("/")[0] if "/" in r["file"] else ix.slug_etichetta(r["etichetta"])
        s = cx.slug(cartella)
        if not s:
            continue
        v = fuori.setdefault(s, {"file": "", "stato": "", "prossimo": "", "etichette": set()})
        v["etichette"].add(r["etichetta"])
        nome_file = r["file"].split("/")[-1]
        if nome_file >= v["file"]:
            v.update(file=nome_file, stato=r["stato"], prossimo=r["prossimo"])
    for v in fuori.values():
        v["filoni"] = len(v.pop("etichette"))
    return fuori


def schede() -> dict:
    """{slug: descrizione} dalle schede progetto-<slug>.md della memoria. Senza memoria: {}."""
    try:
        sys.path.append(str(QUI.parent / "hooks"))
        import melchior_match as mm
        radici = mm.radici()
    except Exception:  # la memoria è facoltativa: una sua rottura non ferma l'elenco
        return {}
    fuori = {}
    for radice in radici:
        try:
            trovate = sorted(radice.rglob("progetto-*.md"))
        except OSError:
            continue
        for f in trovate:
            if any(p[:1] in "._" for p in f.relative_to(radice).parts):
                continue
            s = cx.slug(f.stem[len("progetto-"):])
            if not s or s in fuori:
                continue
            fuori[s] = descrizione(f)
    return fuori


def descrizione(f: Path) -> str:
    try:
        with open(f, encoding="utf-8", errors="replace") as fh:
            righe = [next(fh, "") for _ in range(RIGHE_SCHEDA)]
    except OSError:
        return ""
    if not righe or righe[0].strip() != "---":
        return ""
    for r in righe[1:]:
        if r.strip() == "---":
            break
        if r.startswith("description:"):
            return corta(r.split(":", 1)[1].strip().strip("\"'"))
    return ""


def corta(testo: str) -> str:
    testo = " ".join(ts.pulisci(testo or "").split())
    return testo if len(testo) <= MAX_RIGA else testo[:MAX_RIGA - 1].rstrip() + "…"


def catalogo_fonte(avvisi: list) -> list:
    """Le voci del catalogo della fonte esterna: [{slug, titolo, categoria, alias}]. Senza fonte: []."""
    comando = ts.comando_fonte()
    if not comando:
        return []
    try:
        r = subprocess.run(comando + ["catalogo", "--json"], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=ATTESA_FONTE, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError) as e:
        avvisi.append(f"la fonte dei task non risponde a catalogo ({type(e).__name__}): elenco senza i suoi progetti")
        return []
    if r.returncode == 2:
        avvisi.append("la fonte dei task non ha il verbo catalogo: elenco senza i suoi progetti e senza alias")
        return []
    try:
        voci = json.loads(r.stdout)["progetti"] if r.returncode == 0 else None
    except (ValueError, KeyError, TypeError):
        voci = None
    if not isinstance(voci, list):
        avvisi.append(f"la fonte dei task ha risposto male a catalogo (uscita {r.returncode}): elenco senza i suoi progetti")
        return []
    fuori = []
    for v in voci:
        if not isinstance(v, dict) or not cx.slug(str(v.get("slug") or "")):
            continue
        alias = v.get("alias") if isinstance(v.get("alias"), list) else []
        fuori.append({"slug": cx.slug(str(v["slug"])), "titolo": corta(str(v.get("titolo") or "")),
                      "categoria": corta(str(v.get("categoria") or "")),
                      "alias": [a for a in (cx.slug(str(x)) for x in alias) if a]})
    return fuori


def locali() -> dict:
    """Le voci dalla memoria su file, per slug."""
    ix = cx.modulo_index()
    dirs, ultimi, index, note = cartelle(), ultimi_handoff(), righe_index(ix), schede()
    stati = {}
    for nome, v in ts.stati().items():
        stati.setdefault(cx.slug(nome), v)
    voci = {}
    for s in sorted(set(dirs) | set(ultimi) | set(stati)):
        fonte = [n for n, c in (("cartella", dirs), ("handoff", ultimi), ("stato", stati), ("scheda", note)) if s in c]
        v = {"slug": s, "nome": dirs.get(s) or (ultimi[s][0] if s in ultimi else s), "titolo": "", "categoria": "",
             "descrizione": note.get(s, ""), "riga": "", "data": "", "stato": "", "prossimo": "", "filoni": 0,
             "cartella": s in dirs, "handoff": s in ultimi, "alias": [], "fonte": fonte}
        if s in ultimi:
            _, v["data"], percorso = ultimi[s]
            riga = index.get(s)
            if riga and riga["file"] >= percorso.name:
                v.update(stato=riga["stato"], prossimo=corta(riga["prossimo"]), filoni=riga["filoni"])
            else:  # l'INDEX manca o è rimasto indietro: vale l'ultimo handoff
                try:
                    testo = percorso.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    testo = ""
                v.update(stato=ix.stato_handoff(testo), prossimo=corta(ix.prossimo_handoff(testo)),
                         filoni=riga["filoni"] if riga else 1)
        v["riga"] = corta(stati[s]["riga"]) if s in stati else v["prossimo"]
        voci[s] = v
    return voci


def fondi(voci: dict, catalogo: list) -> dict:
    """Porta il catalogo della fonte nelle voci. Il capo di un gruppo di nomi è lo slug della fonte se ha
    handoff, altrimenti il nome con l'handoff più recente. I nomi senza handoff entrano nel capo."""
    for c in catalogo:
        gruppo = [c["slug"]] + [a for a in c["alias"] if a != c["slug"]]
        presenti = [voci[s] for s in gruppo if s in voci]
        if presenti:
            capo = max(presenti, key=lambda v: (v["handoff"] and v["slug"] == c["slug"], v["data"], v["cartella"],
                                                v["slug"] == c["slug"]))
        else:
            capo = {"slug": c["slug"], "nome": c["slug"], "titolo": "", "categoria": "", "descrizione": "", "riga": "",
                    "data": "", "stato": "", "prossimo": "", "filoni": 0, "cartella": False, "handoff": False,
                    "alias": [], "fonte": []}
            voci[c["slug"]] = capo
        for v in presenti:
            if v is capo:
                continue
            if v["handoff"]:  # un filone che la persona apre da solo: resta, con la categoria del gruppo
                v["categoria"] = v["categoria"] or c["categoria"]
                if "fonte" not in v["fonte"]:
                    v["fonte"].append("fonte")
                continue
            capo["cartella"] = capo["cartella"] or v["cartella"]
            capo["filoni"] += v["filoni"]
            for campo in ("descrizione", "riga"):
                capo[campo] = capo[campo] or v[campo]
            capo["fonte"] += [f for f in v["fonte"] if f not in capo["fonte"]]
            del voci[v["slug"]]
        capo["alias"] = sorted(set(capo["alias"]) | {s for s in gruppo if s != capo["slug"] and s not in voci})
        capo["titolo"], capo["categoria"] = c["titolo"] or capo["titolo"], c["categoria"] or capo["categoria"]
        if "fonte" not in capo["fonte"]:
            capo["fonte"].append("fonte")
    return voci


def elenco() -> dict:
    avvisi = []
    voci = fondi(locali(), catalogo_fonte(avvisi))
    ordinati = sorted(voci.values(), key=lambda v: v["slug"])
    ordinati.sort(key=lambda v: v["data"], reverse=True)
    return {"versione": VERSIONE, "progetti": ordinati, "avvisi": avvisi}


def main(argv: list) -> int:
    if any(a in ("-h", "--help", "aiuto") for a in argv):
        print(__doc__.strip())
        return 0
    if [a for a in argv if a != "--json"]:
        print("uso: arturo progetti [--json]", file=sys.stderr)
        return 3
    dati = elenco()
    if "--json" in argv:
        print(json.dumps(dati, ensure_ascii=False))
        return 0
    for v in dati["progetti"]:
        pezzi = [v["titolo"] or v["nome"], v["data"] or "senza handoff", v["stato"], v["riga"]]
        print(" · ".join(p for p in pezzi if p))
    for a in dati["avvisi"]:
        print(f"AVVISO: {a}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    for flusso in (sys.stdout, sys.stderr):  # su Windows la pipe è in cp1252
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
