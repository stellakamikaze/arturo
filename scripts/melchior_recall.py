#!/usr/bin/env python3
"""Recall profondo Melchior: BM25 in stdlib sul frontmatter+corpo delle note.
Uso: python3 ~/.claude/scripts/melchior_recall.py "testo" [-n 8] [--json] [--memory-dir DIR]
Lo lancia Claude per giudizio quando l'hook memory-retrieve tace; non è un hook, non ha soglie.
Legge tutte le radici della memoria (hooks/melchior_match.py: data/memory, projects/*/memory,
cartelle aggiunte), oppure la sola --memory-dir. Gira anche a memoria spenta: è un comando a mano.
Lo stesso file vive nella config di chi mantiene Arturo e in Arturo, identico byte per byte.
--controprova: indice degradato (corpo delle note IGNORATO, solo frontmatter: la regressione
che il recall profondo non deve avere, perché è ciò che l'hook fa già) usato SOLO dal banco per
provare che il banco discrimina. Non operativo. Misura del 7/9/2026 sulle 19 coppie difficili:
corpo+frontmatter 9 hit, solo frontmatter 7; idf=1 non discriminava (9 = 9)."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "hooks"))
import melchior_match as mm  # noqa: E402


def tokenize(text):
    """Token della query/documento: LISTA (servono le frequenze), non set."""
    out = []
    for w in re.findall(r"[\w']+", (text or "").lower()):
        w = w.strip("'")
        if len(w) > 2 and w not in mm.STOPWORDS:
            out.append(w)
    return out


class Index:
    def __init__(self, docs, n, avgdl, df, controprova=False):
        self.docs = docs          # lista di dict: name, path, fm, tf, dl
        self.n = n                # numero di documenti
        self.avgdl = avgdl
        self.df = df              # token -> quanti doc lo contengono
        self.controprova = controprova

    def _idf(self, df):
        return math.log(1 + (self.n - df + 0.5) / (df + 0.5))

    def rank(self, text, n=8):
        """BM25 k1=1.5 b=0.75. Ritorna [(score, path, fm, matched)] per score>0,
        ordinati score desc poi name. Query con <2 token distinti: []."""
        q_tokens = tokenize(text)
        if len(set(q_tokens)) < 2:
            return []
        k1, b = 1.5, 0.75
        results = []
        for doc in self.docs:
            score = 0.0
            matched = set()
            dl = doc["dl"]
            tf = doc["tf"]
            # si itera sui token della query CON ripetizioni: un token ripetuto
            # nel prompt pesa qtf volte (somma BM25 standard sulle query terms)
            for t in q_tokens:
                f = tf.get(t, 0)
                if f <= 0:
                    continue
                df = self.df.get(t, 0)
                idf = self._idf(df)
                score += idf * (f * (k1 + 1)) / (f + k1 * (1 - b + b * dl / self.avgdl))
                matched.add(t)
            if score > 0:
                results.append((score, doc["path"], doc["fm"], sorted(matched)))
        results.sort(key=lambda r: (-r[0], r[1].name, str(r[1])))
        return results[:n]


def build(memory_dir=None, controprova=False):
    """Indicizza frontmatter (peso x2) + corpo di ogni nota attiva di tutte le radici,
    o della sola memory_dir. controprova=True ignora il corpo (solo per il banco)."""
    docs = []
    df = {}
    total_dl = 0
    for path, fm, body in mm.iter_notes(memory_dir, want_body=True):
        fmtxt = " ".join(str(mm.campo(fm, k) or "") for k in ("name", "description", "triggers", "answers"))
        if controprova:
            body = ""
        tokens = tokenize(fmtxt + " " + fmtxt + " " + body)
        tf = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1
        for t in tf:
            df[t] = df.get(t, 0) + 1
        docs.append({"name": str(mm.campo(fm, "name") or path.stem), "path": path,
                     "fm": fm, "tf": tf, "dl": len(tokens)})
        total_dl += len(tokens)
    n = len(docs)
    avgdl = (total_dl / n) if n else 1.0
    return Index(docs, n, avgdl, df, controprova=controprova)


def _log_recall(results, memory_dir):
    """Log accessi (stesso formato di log_access in hooks/memory-retrieve.py),
    solo sulle radici vere e mai in controprova. Errori ignorati."""
    try:
        if memory_dir is not None:
            return
        mm.registra_accessi([path for _score, path, _fm, _matched in results], "recall")
    except Exception:
        pass


def _rel(path, memory_dir):
    """Percorso relativo alla --memory-dir, o con ~ davanti sulle radici vere."""
    if memory_dir is None:
        return mm.breve(path)
    try:
        return str(path.relative_to(memory_dir))
    except ValueError:
        return str(path)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Recall profondo Melchior (BM25 stdlib).")
    ap.add_argument("testo", help="testo della query")
    ap.add_argument("-n", type=int, default=8, help="numero massimo di risultati")
    ap.add_argument("--json", action="store_true", help="output JSON")
    ap.add_argument("--memory-dir", default=None, help="una sola cartella (default: tutte le radici)")
    ap.add_argument("--controprova", action="store_true",
                    help="indice degradato (corpo ignorato): solo per il banco, non operativo")
    args = ap.parse_args(argv)

    memory_dir = Path(args.memory_dir) if args.memory_dir else None

    if len(set(tokenize(args.testo))) < 2:
        print("query troppo povera (<2 token)", file=sys.stderr)
        return 0

    index = build(memory_dir, controprova=args.controprova)
    results = index.rank(args.testo, n=args.n)

    if args.json:
        payload = [{
            "score": round(score, 3),
            "name": str(mm.campo(fm, "name") or path.stem),
            "path": _rel(path, memory_dir),
            "type": mm.tipo(fm),
            "matched": matched,
            "description": str(mm.campo(fm, "description") or ""),
        } for score, path, fm, matched in results]
        print(json.dumps(payload, ensure_ascii=False, indent=1))
        if results and not args.controprova:
            _log_recall(results, memory_dir)
        return 0

    if not results:
        print("nessuna nota")
        return 0

    for score, path, fm, matched in results:
        name = str(mm.campo(fm, "name") or path.stem)
        if name.endswith(".md"):
            name = name[:-3]
        tipo = mm.tipo(fm)
        desc = str(mm.campo(fm, "description") or "")[:80]
        print(f"  - {name} [{tipo}] · score {score:.1f} · token: {','.join(matched)} — {desc}")
        print(f"    {_rel(path, memory_dir)}")

    if not args.controprova:
        _log_recall(results, memory_dir)
    return 0


if __name__ == "__main__":
    # Claude Code scrive e legge in UTF-8. Su Windows la pipe è in cp1252 (16/10/2026).
    for _flusso in (sys.stdout, sys.stderr):
        try:
            _flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
