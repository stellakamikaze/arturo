#!/usr/bin/env python3
"""Rigenera l'INDEX degli handoff dai file in ~/.claude/data/handoffs/.

Uso:
  index-rigenera.py --dry-run [--diff]      stampa l'INDEX generato (con --diff solo il diff)
  index-rigenera.py --out PATH [--diff]     scrive l'INDEX generato in PATH
  index-rigenera.py --scrivi [--diff]       sostituisce l'INDEX vero (file temporaneo + rename)
Opzioni di prova: --radice DIR (default ~/.claude/data/handoffs),
  --index FILE (INDEX attuale da leggere, default <radice>/INDEX.md), --oggi AAAA-MM-GG.

Una riga per filone. La chiave del filone (la usa anche handoff-retention.py):
  - la riga "- Filone: <nome>" nella sezione ## Progetto dà <slug>/<nome normalizzato>;
  - senza quella riga la chiave è lo slug: un progetto, una riga.
La data viene dal nome del file (HANDOFF_AAAA-MM-GG_HH-MM.md), mai dalla data del file.
Prossimo passo: la riga "Prossimo passo:" di ## Ripartenza, poi l'ultima colonna dell'INDEX
attuale (se la riga punta allo stesso file), poi la prima voce di ## Prossimi passi.
Stato: quello dell'INDEX attuale se la riga punta allo stesso file, altrimenti "Status:".
Le righe con l'ultimo handoff più vecchio di 30 giorni vanno in ## Archivio. Le righe
dell'INDEX senza file restano senza link, tranne quelle di un progetto che ha già una riga
generata (superate). Nessun link verso un file assente: se ne esce uno, exit 1.

Exit: 0 fatto · 1 invariante violata (link morto, nessuna riga) · 2 uso sbagliato.
"""
from __future__ import annotations

import argparse
import datetime as dt
import difflib
import os
import re
import sys
import tempfile
import unicodedata
from pathlib import Path

RADICE = Path.home() / ".claude" / "data" / "handoffs"
GIORNI_ARCHIVIO = 30
MAX_CELLA = 150
RE_FILE = re.compile(r"^HANDOFF_(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2})\.md$")
RE_LINK = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")
RE_NOME_FILE = re.compile(r"HANDOFF_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}\.md")
VUOTE = {"di", "del", "della", "dello", "dei", "delle", "e", "ed", "a", "al", "da", "in",
         "con", "per", "su", "il", "la", "lo", "le", "i", "gli", "un", "una", "the", "of"}
INTESTAZIONE = "| Progetto | Ultimo handoff | Data | Stato | Prossimo passo |\n|---|---|---|---|---|"


def sezione(testo, nome):
    """Corpo della sezione ## <nome...> (il titolo comincia con nome, maiuscole ignorate)."""
    dentro, out = False, []
    for r in testo.splitlines():
        if r.startswith("## "):
            if dentro:
                break
            dentro = r[3:].strip().lower().startswith(nome.lower())
            continue
        if dentro:
            out.append(r)
    return "\n".join(out)


def parole(testo):
    t = unicodedata.normalize("NFKD", testo.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return [w for w in re.findall(r"[a-z0-9]+", t) if w not in VUOTE]


def filone_esplicito(testo):
    for r in sezione(testo, "Progetto").splitlines():
        m = re.match(r"^\s*-\s*\**Filone\**\s*:\s*(.+)$", r)
        if m:
            return m.group(1).replace("**", "").strip()
    return ""


def chiave(slug, testo):
    """Chiave stabile del filone: vedi la docstring del modulo."""
    p = parole(filone_esplicito(testo))
    return f"{slug}/{'-'.join(p)}" if p and p != [slug] else slug


def elenca(radice):
    """Gli handoff: lista di dict (slug, nome, rel, percorso, data, ora, testo, chiave)."""
    out = []
    for d in sorted(p for p in Path(radice).iterdir() if p.is_dir() and not p.name.startswith(".")):
        for f in sorted(d.iterdir()):
            m = RE_FILE.match(f.name)
            if not m or not f.is_file():
                continue
            testo = f.read_text(encoding="utf-8", errors="replace")
            out.append({"slug": d.name, "nome": f.name, "rel": f"{d.name}/{f.name}", "percorso": str(f),
                        "data": m.group(1), "ora": m.group(2), "testo": testo,
                        "chiave": chiave(d.name, testo)})
    return out


def per_chiave(handoff):
    """{chiave: [handoff dal più recente]}, in ordine di data nel nome."""
    gruppi = {}
    for h in handoff:
        gruppi.setdefault(h["chiave"], []).append(h)
    for g in gruppi.values():
        g.sort(key=lambda h: h["nome"], reverse=True)
    return gruppi


# --- celle -------------------------------------------------------------------------

def celle(riga):
    """Celle di una riga di tabella markdown (rispetta "\\|")."""
    parti = re.split(r"(?<!\\)\|", riga.strip())
    if parti and parti[0] == "":
        parti = parti[1:]
    if parti and parti[-1] == "":
        parti = parti[:-1]
    return [c.strip() for c in parti]


def pulisci(testo, limite=MAX_CELLA):
    t = re.sub(r"\s+", " ", testo or "").strip()
    t = re.sub(r"(?<!\\)\|", r"\\|", t)
    if len(t) > limite:
        taglio = t[:limite]
        if " " in taglio[limite // 2:]:
            taglio = taglio[:taglio.rfind(" ")]
        t = taglio.rstrip(" ,;:—-") + "…"
        if t.count("**") % 2:
            t += "**"
        if t.count("`") % 2:
            t += "`"
    return t or "—"


def stato_handoff(testo):
    for r in sezione(testo, "Progetto").splitlines():
        r = r.replace("**", "")
        for pezzo in r.lstrip("- ").split(" / "):
            m = re.match(r"^\s*Status\s*:?\s*(.+)$", pezzo.strip())
            if m:
                return m.group(1).strip()
    return ""


def prossimo_handoff(testo):
    for r in sezione(testo, "Ripartenza").splitlines():
        m = re.match(r"^\s*\**Prossimo passo\**\s*:\**\s*(.+)$", r.strip())
        if m:
            return m.group(1).strip()
    return ""


def prossimi_passi(testo):
    for r in sezione(testo, "Prossimi passi").splitlines():
        r = re.sub(r"^\s*(?:[-*]|\d+[.)])\s*(?:\[[ xX]\]\s*)?", "", r).strip()
        if r:
            return r
    return ""


# --- INDEX attuale -------------------------------------------------------------------

def slug_etichetta(etichetta):
    t = etichetta.replace("~~", "").replace("**", "").strip().lower()
    return re.split(r"[\s(—]", t, maxsplit=1)[0]


def leggi_index(percorso):
    """Righe dell'INDEX attuale: dict (etichetta, cella, data, stato, prossimo, file)."""
    righe = []
    try:
        testo = Path(percorso).read_text(encoding="utf-8")
    except OSError:
        return righe
    for r in testo.splitlines():
        if not r.startswith("|"):
            continue
        c = celle(r)
        if len(c) < 4 or c[0] in ("Progetto", "#") or set(c[0]) <= set("-: "):
            continue
        etichetta, cella, file_rel = c[0], c[1], ""
        for _, dest in RE_LINK.findall(cella):
            if RE_NOME_FILE.search(dest):
                file_rel = dest
                break
        if not file_rel:
            m = RE_NOME_FILE.search(cella)
            if m:
                file_rel = f"{slug_etichetta(etichetta)}/{m.group(0)}"
        m = re.search(r"\d{4}-\d{2}-\d{2}", c[2])
        righe.append({"etichetta": etichetta, "cella": cella, "data": m.group(0) if m else "",
                      "stato": c[3], "prossimo": c[4] if len(c) > 4 else "", "file": file_rel})
    return righe


def link_extra(cella, radice):
    """I link della cella vecchia che non sono handoff e puntano a file esistenti."""
    return [f"[{t}]({d})" for t, d in RE_LINK.findall(cella)
            if not RE_NOME_FILE.search(d) and (Path(radice) / d).exists()]


def senza_link_morti(cella, radice):
    """Toglie i link verso file assenti, lascia il testo."""
    def sost(m):
        t, d = m.group(1), m.group(2)
        if d.startswith(("http://", "https://")) or (Path(radice) / d).exists():
            return m.group(0)
        return f"{t} (file non più presente)"
    return RE_LINK.sub(sost, cella)


# --- generazione ---------------------------------------------------------------------

def genera(radice, index_path, oggi):
    radice = Path(radice)
    handoff = elenca(radice)
    gruppi = per_chiave(handoff)
    vecchie = leggi_index(index_path)
    per_file = {}
    for v in vecchie:
        if v["file"]:
            per_file.setdefault(v["file"], v)
    esistenti = {h["rel"] for h in handoff}
    ultimi = {g[0]["rel"] for g in gruppi.values()}

    righe, stats = [], {"generate": 0, "riportate": 0, "superate": 0}
    for k, g in gruppi.items():
        h = g[0]
        v = per_file.get(h["rel"])
        if v:
            etichetta = v["etichetta"].replace("~~", "").strip()
        elif "/" in k:
            etichetta = f"{h['slug']} — {pulisci(filone_esplicito(h['testo']), 60)}"
        else:
            etichetta = h["slug"]
        stato = (v["stato"] if v else "") or stato_handoff(h["testo"])
        prossimo = (prossimo_handoff(h["testo"]) or (v["prossimo"] if v else "")
                    or prossimi_passi(h["testo"]))
        cella = " · ".join([f"[{h['nome']}]({h['rel']})"] + (link_extra(v["cella"], radice) if v else []))
        righe.append({"etichetta": pulisci(etichetta, 80), "cella": cella, "data": h["data"],
                      "ora": h["ora"], "stato": pulisci(stato), "prossimo": pulisci(prossimo)})
        stats["generate"] += 1

    slug_generati = {h["slug"] for h in handoff}
    viste = {r["etichetta"] for r in righe}
    for v in vecchie:
        if v["file"] in esistenti:
            if v["file"] not in ultimi:
                stats["superate"] += 1  # punta a un handoff che non è più l'ultimo del suo filone
            continue
        base = v["file"].split("/")[0] if "/" in v["file"] else slug_etichetta(v["etichetta"])
        if base in slug_generati:
            stats["superate"] += 1
            continue
        etichetta = pulisci(v["etichetta"], 80)
        if etichetta in viste:
            continue
        viste.add(etichetta)
        righe.append({"etichetta": etichetta, "cella": pulisci(senza_link_morti(v["cella"], radice), 200),
                      "data": v["data"], "ora": "", "stato": pulisci(v["stato"]),
                      "prossimo": pulisci(v["prossimo"])})
        stats["riportate"] += 1

    limite = (oggi - dt.timedelta(days=GIORNI_ARCHIVIO)).isoformat()
    attive = [r for r in righe if r["data"] and r["data"] >= limite]
    archivio = [r for r in righe if not (r["data"] and r["data"] >= limite)]

    def tabella(rs):
        rs = sorted(rs, key=lambda r: (r["data"], r["ora"], r["etichetta"]), reverse=True)
        return "\n".join(f"| {r['etichetta']} | {r['cella']} | {r['data'] or '—'} | {r['stato']} | {r['prossimo']} |"
                         for r in rs)

    testo = (
        "# Indice degli handoff\n\n"
        "Generato da `bin/index-rigenera.py` a ogni `/fine`, letto da `/inizio`: non correggerlo a mano.\n"
        "Una riga per progetto, o per filone se l'handoff ha la riga \"- Filone:\".\n"
        "Retention: ultimi 5 handoff per filone (`bin/handoff-retention.py`).\n\n"
        f"{INTESTAZIONE}\n{tabella(attive)}\n\n"
        "## Archivio\n\n"
        f"_Righe con l'ultimo handoff più vecchio di {GIORNI_ARCHIVIO} giorni._\n\n"
        f"{INTESTAZIONE}\n{tabella(archivio)}\n"
    )
    stats.update(attive=len(attive), archivio=len(archivio))
    return testo, stats


def link_morti(testo, radice):
    return [d for _, d in RE_LINK.findall(testo)
            if not d.startswith(("http://", "https://", "#")) and not (Path(radice) / d).exists()]


def scrivi_atomico(percorso, testo):
    percorso = Path(percorso)
    fd, tmp = tempfile.mkstemp(prefix=".index-", suffix=".tmp", dir=str(percorso.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(testo)
        os.replace(tmp, str(percorso))
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def main(argv=None):
    ap = argparse.ArgumentParser(description="Rigenera INDEX.md degli handoff.")
    modo = ap.add_mutually_exclusive_group()
    modo.add_argument("--dry-run", action="store_true", help="stampa, non scrive")
    modo.add_argument("--out", metavar="PATH", help="scrive in PATH")
    modo.add_argument("--scrivi", action="store_true", help="sostituisce l'INDEX vero")
    ap.add_argument("--diff", action="store_true", help="stampa il diff con l'INDEX attuale")
    ap.add_argument("--radice", default=str(RADICE))
    ap.add_argument("--index", help="INDEX attuale (default <radice>/INDEX.md)")
    ap.add_argument("--oggi", help="data di riferimento AAAA-MM-GG")
    a = ap.parse_args(argv)
    if not (a.dry_run or a.out or a.scrivi):
        ap.print_usage(sys.stderr)
        print("index-rigenera: scegli --dry-run, --out PATH o --scrivi", file=sys.stderr)
        return 2
    radice = Path(a.radice)
    if not radice.is_dir():
        print(f"index-rigenera: cartella degli handoff assente: {radice}", file=sys.stderr)
        return 2
    index_path = Path(a.index) if a.index else radice / "INDEX.md"
    try:
        oggi = dt.date.fromisoformat(a.oggi) if a.oggi else dt.date.today()
    except ValueError:
        print(f"index-rigenera: data non valida: {a.oggi}", file=sys.stderr)
        return 2

    testo, stats = genera(radice, index_path, oggi)
    morti = link_morti(testo, radice)
    if morti:
        print(f"index-rigenera: LINK MORTO nell'INDEX generato: {', '.join(morti[:5])}", file=sys.stderr)
        return 1
    if stats["attive"] + stats["archivio"] == 0:
        print("index-rigenera: NESSUNA RIGA generata, non scrivo", file=sys.stderr)
        return 1

    if a.diff:
        try:
            attuale = index_path.read_text(encoding="utf-8").splitlines(keepends=True)
        except OSError:
            attuale = []
        sys.stdout.writelines(difflib.unified_diff(attuale, testo.splitlines(keepends=True),
                                                   "INDEX attuale", "INDEX generato", n=0))
    elif a.dry_run:
        sys.stdout.write(testo)
    if a.out:
        scrivi_atomico(a.out, testo)
    elif a.scrivi:
        scrivi_atomico(radice / "INDEX.md", testo)
    print("index-rigenera: {attive} attive, {archivio} in archivio · {generate} dagli handoff, "
          "{riportate} riportate senza file, {superate} vecchie superate".format(**stats), file=sys.stderr)
    return 0


if __name__ == "__main__":
    for flusso in (sys.stdout, sys.stderr):  # su Windows la pipe è in cp1252, Claude legge UTF-8
        try:
            flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
