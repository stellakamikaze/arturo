#!/usr/bin/env python3
"""Riscrive l'elenco di riserva degli articoli nella home, fra <!-- articoli:inizio --> e <!-- articoli:fine -->.

La home chiede gli articoli alla Content API di Ghost di stellakamikaze.org quando si apre. Se l'API
non risponde resta questo elenco, che va rinfrescato prima di ogni deploy:

  python3 strumenti/articoli.py           riscrive sito/index.html
  python3 strumenti/articoli.py --prova   stampa il blocco senza scrivere

La chiave è quella pubblica della Content API, già nel sorgente di stellakamikaze.org.
Solo libreria standard.
"""
from __future__ import annotations

import html
import json
import re
import sys
import urllib.request
from pathlib import Path

CHIAVE = "56e828183ad14d6cc5739cc75d"
MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre",
        "ottobre", "novembre", "dicembre"]
HOME = Path(__file__).resolve().parent.parent / "sito" / "index.html"


def articoli(tag: str) -> list:
    url = ("https://stellakamikaze.org/ghost/api/content/posts/?key=" + CHIAVE + "&filter=tag:" + tag
           + "&limit=4&fields=title,url,published_at,custom_excerpt,excerpt")
    richiesta = urllib.request.Request(url, headers={"User-Agent": "arturo-landing/1"})
    with urllib.request.urlopen(richiesta, timeout=15) as r:
        return json.load(r)["posts"]


def blocco(tag: str, posts: list) -> str:
    righe = []
    for p in posts:
        anno, mese, giorno = p["published_at"][:10].split("-")
        data = f"{int(giorno)} {MESI[int(mese) - 1]} {anno}"
        testo = (p.get("custom_excerpt") or p.get("excerpt") or "").strip()
        righe.append(f'        <li><a href="{html.escape(p["url"])}"><time datetime="{p["published_at"][:10]}">{data}</time>'
                     f'<strong>{html.escape(p["title"], quote=False)}</strong><span>{html.escape(testo, quote=False)}</span></a></li>')
    return (f'<!-- articoli:inizio -->\n      <ol class="articoli" id="articoli" data-tag="{tag}">\n'
            + "\n".join(righe) + "\n      </ol>\n      <!-- articoli:fine -->")


def main(argomenti: list) -> int:
    testo = HOME.read_text(encoding="utf-8")
    m = re.search(r'<!-- articoli:inizio -->.*?data-tag="([^"]+)".*?<!-- articoli:fine -->', testo, re.S)
    if not m:
        print("Non trovo il blocco degli articoli in sito/index.html", file=sys.stderr)
        return 1
    posts = articoli(m.group(1))
    if len(posts) < 4:
        print(f"L'API ha dato {len(posts)} articoli: lascio l'elenco com'è", file=sys.stderr)
        return 1
    nuovo = blocco(m.group(1), posts)
    if "--prova" in argomenti:
        print(nuovo)
        return 0
    HOME.write_text(testo[:m.start()] + nuovo + testo[m.end():], encoding="utf-8")
    print("Elenco degli articoli aggiornato: " + ", ".join(p["title"] for p in posts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
