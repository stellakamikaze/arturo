#!/usr/bin/env python3
"""arturo progetti doppioni: le coppie di progetti che sono probabilmente lo stesso progetto.

Uso: arturo progetti doppioni [--json] [--scartate FILE] [--max N]

Legge l'elenco di `arturo progetti` e propone le coppie, col motivo e col progetto che resta. Non scrive
niente. Il calcolo nasce in Volta (doppioni.js, #6188, 21/11/2026) e dal 23/11/2026 (revisione, passo 9)
sta qui: Volta chiama questo verbo e non calcola più nel mod.

--scartate FILE: le coppie che la persona ha scartato, `{"<slug>|<slug>": {"n": N, "quando": ms}}`. `n` conta
i gesti sulla coppia: dispari è scartata, pari è rimessa fra i doppioni. Un numero solo vale `n` 1 (il file
del 21/11). Un file che non si legge come JSON è un errore, non un elenco vuoto: restano le coppie scartate
dentro un file rotto, e la persona le rivedrebbe tutte.

Uscita --json: {versione, coppie: [{chiave, perdente, vincitore, forza, motivo, perche}], avvisi}, dalla coppia
più forte. Al più 40 coppie.
Exit: 0 · 3 uso sbagliato · 4 file delle scartate rotto.
"""
from __future__ import annotations

import json
import os
import re
import sys
import unicodedata
from pathlib import Path

QUI = Path(os.path.realpath(__file__)).parent
sys.path.insert(0, str(QUI))

VERSIONE = 1
# Sotto questa forza una coppia non si mostra. Ogni segno forte vale 3 e basta da solo; i segni deboli valgono 2
# e hanno già dentro la loro condizione.
SOGLIA = 2
MAX = 40  # la revisione si fa a mano, una riga alla volta
RIGA_MIN = 20  # una riga di stato più corta non dice niente: "Fermo." è uguale in dieci progetti
# Le righe che Arturo scrive uguali in ogni progetto non dicono che due progetti sono lo stesso: il prossimo passo
# fisso del salvataggio automatico (bin/salva-automatico.py) cade lo stesso giorno in più progetti (#6742).
RIGHE_FISSE = {"riprendere da qui e chiudere con /fine, che completa questo salvataggio."}


def chiave_coppia(a, b) -> str:
    return "|".join(sorted([str(a or ""), str(b or "")]))


def _piano(x) -> str:
    s = unicodedata.normalize("NFD", str(x or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def _con_scheda(m) -> bool:
    return isinstance(m.get("fonte"), list) and "scheda" in m["fonte"]


def _filoni(m) -> int:
    try:
        return int(m.get("filoni") or 0)
    except (TypeError, ValueError):
        return 0


def _con_handoff(m) -> bool:
    return bool(m.get("handoff")) or _filoni(m) > 0


def _alias(m) -> list:
    a = m.get("alias")
    return [x for x in a if isinstance(x, str) and x] if isinstance(a, list) else []


def guscio(m) -> bool:
    """Un progetto senza scheda e senza handoff: c'è solo come cartella o come voce della fonte dei task.
    Non ha niente da unire, e Arturo rifiuta l'unione."""
    return not _con_scheda(m) and not _con_handoff(m)


def senza_scheda(m) -> bool:
    """Handoff scritti sotto un nome che non ha mai avuto la sua scheda: il segno di un secondo nome."""
    return _con_handoff(m) and not _con_scheda(m)


def distanza(a: str, b: str, tetto: int = 2) -> int:
    """Quante lettere cambiano fra due nomi (inserite, tolte o scambiate), al più `tetto`: oltre, tetto + 1."""
    if abs(len(a) - len(b)) > tetto:
        return tetto + 1
    riga = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        dopo = [i]
        for j in range(1, len(b) + 1):
            dopo.append(min(riga[j] + 1, dopo[j - 1] + 1, riga[j - 1] + (0 if a[i - 1] == b[j - 1] else 1)))
        riga = dopo
    return min(riga[len(b)], tetto + 1)


def segni_doppione(a: dict, b: dict, repo_comuni=frozenset()) -> list:
    """I segni che `a` e `b` sono lo stesso progetto: [{forza, testo, dentro?}], dal più forte. Il testo
    continua la frase "Sembrano doppioni perché…"."""
    sa, sb = str(a.get("slug") or ""), str(b.get("slug") or "")
    if not sa or not sb or sa == sb:
        return []
    segni = []
    aa, ab = _alias(a), _alias(b)
    if sb in aa:
        segni.append({"forza": 3, "testo": f"{sb} è già un nome alternativo di {sa}"})
    elif sa in ab:
        segni.append({"forza": 3, "testo": f"{sa} è già un nome alternativo di {sb}"})
    else:
        comune = next((x for x in aa if x in ab), None)
        if comune:
            segni.append({"forza": 3, "testo": f"hanno lo stesso nome alternativo, {comune}"})
    na, nb = sa.replace("-", ""), sb.replace("-", "")
    pa, pb = [p for p in sa.split("-") if p], [p for p in sb.split("-") if p]

    def dentro(corte, lunghe):
        return len(corte) < len(lunghe) and all(p in lunghe for p in corte)

    if na == nb:
        segni.append({"forza": 3, "testo": "hanno lo stesso nome, scritto in due modi"})
    elif dentro(pa, pb) or dentro(pb, pa):
        corto, lungo = (a, b) if dentro(pa, pb) else (b, a)
        # "uf" sta dentro "sito-uf", ma sono due progetti con la loro scheda: conta solo se uno dei due non ce l'ha
        orfano = lungo if senza_scheda(lungo) else corto if senza_scheda(corto) else None
        altro = corto if orfano is lungo else lungo
        if orfano is not None and _con_scheda(altro):
            segni.append({"forza": 2, "dentro": orfano["slug"],
                          "testo": f"il nome {lungo['slug']} contiene {corto['slug']}, e {orfano['slug']} ha handoff ma non ha la scheda"})
    else:
        # una lettera su un nome di almeno cinque, due su uno di almeno nove: "teleclub" e "telecub", non "eos" e "uf"
        corto = min(len(na), len(nb))
        d = distanza(na, nb)
        # "gara-2026" e "gara-2027" sono due edizioni, non un refuso
        edizioni = re.sub(r"\d", "", na) == re.sub(r"\d", "", nb)
        if not edizioni and ((d == 1 and corto >= 5) or (d == 2 and corto >= 9)):
            segni.append({"forza": 2, "testo": "i nomi cambiano di una lettera" if d == 1 else "i nomi cambiano di due lettere"})
    ta, tb = _piano(a.get("titolo")), _piano(b.get("titolo"))
    if ta and ta == tb and na != nb:
        segni.append({"forza": 3, "testo": f"hanno lo stesso titolo, {str(a['titolo']).strip()}"})
    ra = str(a.get("riga") or "").strip()
    fissa = _piano(ra) in {_piano(x) for x in RIGHE_FISSE}
    if len(ra) >= RIGA_MIN and not fissa and ra == str(b.get("riga") or "").strip() and a.get("data") and a.get("data") == b.get("data"):
        segni.append({"forza": 3, "testo": "hanno la stessa riga di stato, dello stesso giorno"})
    repo = str(a.get("repo") or "").strip()
    if repo and repo not in repo_comuni and repo == str(b.get("repo") or "").strip():
        segni.append({"forza": 3, "testo": f"hanno lo stesso repository, {repo}"})
    return sorted(segni, key=lambda s: -s["forza"])


def vincitore_proposto(a: dict, b: dict) -> dict:
    """Quale dei due resta: {vincitore, perdente, perche}. Vale il primo criterio che li distingue, nell'ordine:
    chi ha già l'altro come nome alternativo, chi ha la scheda, chi ha più filoni, chi ha handoff, il più
    recente, chi ha la cartella, il nome più corto, l'ordine alfabetico."""
    sa, sb = str(a.get("slug") or ""), str(b.get("slug") or "")

    def data(m):
        return str(m.get("data") or "")

    criteri = [
        (int(sb in _alias(a)), int(sa in _alias(b)), f"{sb} è già un suo nome alternativo", f"{sa} è già un suo nome alternativo"),
        (int(_con_scheda(a)), int(_con_scheda(b)), "ha la scheda", "ha la scheda"),
        (_filoni(a), _filoni(b), f"ha più filoni ({_filoni(a)} contro {_filoni(b)})", f"ha più filoni ({_filoni(b)} contro {_filoni(a)})"),
        (int(_con_handoff(a)), int(_con_handoff(b)), "ha gli handoff", "ha gli handoff"),
        (data(a), data(b), "ha l'handoff più recente", "ha l'handoff più recente"),
        (int(bool(a.get("cartella"))), int(bool(b.get("cartella"))), "ha la cartella", "ha la cartella"),
        (-len(sa), -len(sb), "ha il nome più corto", "ha il nome più corto"),
        (sb, sa, "viene prima in ordine alfabetico", "viene prima in ordine alfabetico"),
    ]
    # Gli ultimi due criteri spareggiano soltanto: non fanno da secondo motivo.
    spareggi = 2
    vince_a = None
    motivi = []
    for i, (va, vb, testo_a, testo_b) in enumerate(criteri):
        if va == vb:
            continue
        per_a = va > vb
        if vince_a is None:
            vince_a = per_a
            motivi.append(testo_a if per_a else testo_b)
            continue
        if per_a == vince_a and i < len(criteri) - spareggi:
            motivi.append(testo_a if per_a else testo_b)
            break
    if vince_a is None:
        vince_a = True
    # "ha la scheda e più filoni", non "ha la scheda e ha più filoni"
    if len(motivi) == 2 and motivi[0].startswith("ha ") and motivi[1].startswith("ha "):
        motivi[1] = motivi[1][3:]
    return {"vincitore": sa if vince_a else sb, "perdente": sb if vince_a else sa, "perche": " e ".join(motivi) or "sono pari"}


def doppioni(lista, scartate=None, quante: int = MAX) -> list:
    """Le coppie probabili fra i progetti `lista`, tolte quelle già scartate (`scartate`: {chiave: quando}):
    [{chiave, perdente, vincitore, perche, forza, motivo}], dalla più forte, a pari forza quella toccata più
    di recente. `motivo` porta i due segni più forti."""
    voci = [m for m in (lista if isinstance(lista, list) else []) if isinstance(m, dict) and isinstance(m.get("slug"), str) and m["slug"]]
    via = scartate if isinstance(scartate, dict) else {}
    conta = {}
    for m in voci:
        r = str(m.get("repo") or "").strip()
        if r:
            conta[r] = conta.get(r, 0) + 1
    repo_comuni = {r for r, n in conta.items() if n > 2}
    coppie = []
    for i in range(len(voci)):
        for j in range(i + 1, len(voci)):
            a, b = voci[i], voci[j]
            chiave = chiave_coppia(a["slug"], b["slug"])
            if a["slug"] == b["slug"] or chiave in via:
                continue
            if guscio(a) or guscio(b):
                continue
            segni = segni_doppione(a, b, repo_comuni)
            forza = sum(s["forza"] for s in segni)
            if forza < SOGLIA:
                continue
            recente = sorted([str(a.get("data") or ""), str(b.get("data") or "")])[1]
            # `dentro`: la coppia sta in piedi solo sul nome contenuto, e dice quale dei due è senza scheda
            dentro_ = segni[0].get("dentro") if len(segni) == 1 else None
            coppie.append({"chiave": chiave, **vincitore_proposto(a, b), "forza": forza,
                           "motivo": "; ".join(s["testo"] for s in segni[:2]), "_recente": recente, "_dentro": dentro_})
    # Un nome contenuto è ambiguo quando lega lo stesso progetto a più candidati ("personale" sta in
    # "fiscale-personale" e in "niente-di-personale"), o quando quel progetto ha già una coppia forte con un
    # altro ("herdr-arturo" è volta, non arturo): allora la coppia non si mostra.
    volte, forti = {}, set()
    for c in coppie:
        if c["_dentro"]:
            volte[c["_dentro"]] = volte.get(c["_dentro"], 0) + 1
        else:
            forti.add(c["perdente"])
            forti.add(c["vincitore"])
    coppie = [c for c in coppie if not c["_dentro"] or (volte.get(c["_dentro"]) == 1 and c["_dentro"] not in forti)]
    # forza decrescente, a pari forza la più recente, poi la chiave
    coppie.sort(key=lambda c: c["chiave"])
    coppie.sort(key=lambda c: c["_recente"], reverse=True)
    coppie.sort(key=lambda c: c["forza"], reverse=True)
    return [{k: v for k, v in c.items() if not k.startswith("_")} for c in coppie[:max(0, quante)]]


def leggi_scartate(percorso: str | None) -> dict:
    """{chiave: quando} delle coppie scartate adesso. Un file che non c'è vale vuoto; uno rotto alza ValueError."""
    if not percorso:
        return {}
    f = Path(percorso)
    if not f.exists():
        return {}
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise ValueError(f"{f}: non si legge come JSON ({e})") from e
    if not isinstance(d, dict):
        raise ValueError(f"{f}: non è un oggetto JSON")
    fuori = {}
    for k, v in d.items():
        # un numero solo (il file del 21/11) vale n 1; una voce {n, quando} conta i gesti
        n = v.get("n", 1) if isinstance(v, dict) else 1
        quando = v.get("quando", 0) if isinstance(v, dict) else v
        if isinstance(n, int) and n % 2 == 1:
            fuori[k] = quando
    return fuori


def main(argv: list) -> int:
    if any(a in ("-h", "--help", "aiuto") for a in argv):
        print(__doc__.strip())
        return 0
    json_out, scartate, quante, i = False, None, MAX, 0
    while i < len(argv):
        a = argv[i]
        if a == "--json":
            json_out = True
        elif a in ("--scartate", "--max") and i + 1 < len(argv):
            if a == "--scartate":
                scartate = argv[i + 1]
            else:
                try:
                    quante = int(argv[i + 1])
                except ValueError:
                    print("uso: --max vuole un numero", file=sys.stderr)
                    return 3
            i += 1
        else:
            print("uso: arturo progetti doppioni [--json] [--scartate FILE] [--max N]", file=sys.stderr)
            return 3
        i += 1
    try:
        via = leggi_scartate(scartate)
    except ValueError as e:
        print(f"scartate: {e}", file=sys.stderr)
        return 4
    import progetti
    dati = progetti.elenco()
    coppie = doppioni(dati["progetti"], via, quante)
    if json_out:
        print(json.dumps({"versione": VERSIONE, "coppie": coppie, "avvisi": dati["avvisi"]}, ensure_ascii=False))
        return 0
    for c in coppie:
        print(f"{c['perdente']} → {c['vincitore']} · {c['motivo']} · resta perché {c['perche']}")
    for a in dati["avvisi"]:
        print(f"AVVISO: {a}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    for flusso in (sys.stdout, sys.stderr):  # su Windows la pipe è in cp1252
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
