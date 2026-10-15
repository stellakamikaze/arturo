#!/usr/bin/env python3
"""scrape: legge UNA pagina web e ne tiene solo ciò che serve (markdown, testo, nodi CSS).

Uso:
  scrape <url> [--md|--text|--html|--json] [--full] [--sel CSS] [-o FILE] [-q]

Una sola richiesta HTTP, con un user agent che dichiara cosa è. Niente browser, niente
travestimenti: se il sito blocca (401, 403, 429, pagina di verifica «sei umano?»), lo script lo
dice, esce 3 e consiglia di aprire la pagina nel browser.

Exit: 0 letto · 2 la pagina non c'è o il server è guasto (404, 5xx) · 3 il sito blocca le
richieste automatiche · 4 errore di rete.
"""
import argparse
import json
import sys
import time

USER_AGENT = "Mozilla/5.0 (compatible; scrape/1.0; lettura di una pagina pubblica)"

# Status con cui un sito rifiuta una richiesta automatica.
BLOCCO = {401, 403, 406, 409, 429, 503, 520, 521, 522, 523, 524, 525, 526, 527}

# Frasi delle pagine di verifica anti-bot: un 200 con queste frasi non è la pagina vera.
CHALLENGE = ("just a moment", "checking your browser", "cf-browser-verification",
             "enable javascript and cookies", "attention required", "verifica di sicurezza",
             "verifying you are human", "ddos protection by")

CONSIGLIO = ("Il sito blocca le richieste automatiche. Apri la pagina nel browser "
             "(per esempio con l'estensione Claude in Chrome) e leggila da lì.")


def e_challenge(pagina):
    try:
        testo = pagina.get_all_text()[:5000].lower()
    except Exception:
        testo = ""
    titolo = (pagina.css("title::text").get() or "").lower()
    return any(c in testo or c in titolo for c in CHALLENGE)


def rendi(pagina, formato, selettore, solo_contenuto=True):
    if formato == "md":
        return pagina.markdown(css_selector=selettore, main_content_only=solo_contenuto)
    if selettore:
        nodi = pagina.css(selettore)
        return "\n".join(n.html_content if formato == "html" else n.get_all_text(strip=True)
                         for n in nodi)
    if formato == "text":
        return pagina.get_all_text(strip=True)
    if formato == "html":
        return pagina.html_content
    if formato == "json":
        return json.dumps(pagina.json(), ensure_ascii=False, indent=2)
    return pagina.markdown(main_content_only=solo_contenuto)


def esito(status, challenge):
    """Exit e messaggio per uno status HTTP. (0, "") se la pagina è buona."""
    if status in BLOCCO or (status == 200 and challenge):
        motivo = "pagina di verifica anti-bot" if status == 200 else "status %s" % status
        return 3, "[bloccato: %s] %s" % (motivo, CONSIGLIO)
    if status != 200:
        return 2, "[status %s: la pagina non c'è o il server è guasto. Il browser non cambierebbe l'esito]" % status
    return 0, ""


def main():
    ap = argparse.ArgumentParser(description="Legge una pagina web senza browser.")
    ap.add_argument("url")
    ap.add_argument("--md", dest="formato", action="store_const", const="md",
                    help="markdown del solo contenuto principale (default)")
    ap.add_argument("--text", dest="formato", action="store_const", const="text", help="testo nudo")
    ap.add_argument("--html", dest="formato", action="store_const", const="html", help="HTML grezzo")
    ap.add_argument("--json", dest="formato", action="store_const", const="json", help="risposta JSON")
    ap.add_argument("--sel", help="selettore CSS: estrae solo i nodi che corrispondono")
    ap.add_argument("--full", action="store_true",
                    help="markdown della pagina intera invece del solo contenuto principale")
    ap.add_argument("-o", "--out", help="scrive su file invece che su stdout")
    ap.add_argument("-q", "--quiet", action="store_true", help="niente righe di stato su stderr")
    a = ap.parse_args()
    formato = a.formato or "md"

    import logging
    logging.getLogger("scrapling").setLevel(logging.ERROR if a.quiet else logging.INFO)
    from scrapling.fetchers import Fetcher

    t0 = time.time()
    try:
        # impersonate=None e stealthy_headers=False: niente impronta di un browser, niente referer finto.
        pagina = Fetcher.get(a.url, impersonate=None, stealthy_headers=False,
                             headers={"User-Agent": USER_AGENT}, timeout=30)
    except Exception as ex:
        print("[errore di rete: %s: %s]" % (type(ex).__name__, ex), file=sys.stderr)
        return 4

    rc, messaggio = esito(pagina.status, pagina.status == 200 and e_challenge(pagina))
    if rc:
        print(messaggio, file=sys.stderr)
        return rc

    uscita = rendi(pagina, formato, a.sel, solo_contenuto=not a.full)
    if not a.quiet:
        print("[status %s | %ss | %d KB]" % (pagina.status, round(time.time() - t0, 1), len(uscita) // 1024),
              file=sys.stderr)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(uscita)
        print(a.out)
    else:
        sys.stdout.write(uscita)
    return 0


if __name__ == "__main__":
    sys.exit(main())
