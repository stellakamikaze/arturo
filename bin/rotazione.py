#!/usr/bin/env python3
"""arturo rotazione: a che punto del contesto Claude salva la sessione e riparte pulito.

  arturo rotazione          la soglia di oggi e da dove viene
  arturo rotazione N        salva e riparte quando il contesto usato arriva a N% (da MINIMO a MASSIMO)
  arturo rotazione togli    torna alla soglia di Arturo, PREDEFINITA%
  arturo rotazione visto    l'avviso della rotazione nuova è stato detto alla persona: non esce più
  arturo rotazione riga     per session-start.sh: la riga CONTEXT e, finché non è visto, l'avviso

Nasce il 23/11/2026 dalla review della lentezza. Prima /fine --rotazione partiva a ogni compito chiuso:
sul Mac di chi mantiene Arturo 299 volte in 7 giorni, quasi due minuti l'una, più un /inizio dopo ogni
giro. Ora a compito chiuso Claude fa commit, push e chiude il todo, e continua nella stessa sessione. Il
salvataggio e la sessione nuova partono all'avviso CONTEXT WARNING di hooks/context-monitor.js, cioè a
questa soglia, oppure dalle 18 col /fine completo del giorno.

La soglia della persona sta in ~/.claude/personale/rotazione.txt, nell'Orsa: gli aggiornamenti non la
toccano. La variabile CLAUDE_CTX_WARN (percento di contesto rimasto, in settings.json) vince sul file,
come prima. Da MASSIMO in su l'avviso cadrebbe dopo quello CRITICAL (25% rimasto): non si accetta.
Solo libreria standard, Python 3.8 o successivo.
"""
from __future__ import annotations

import datetime as dt
import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple

sys.path.insert(0, str(Path(os.path.realpath(__file__)).parent.parent / "hooks"))
from radici import comando_arturo, radice_orsa  # noqa: E402

sys.path.insert(0, str(Path(os.path.realpath(__file__)).parent))
from disegno import a_capo, barra, riquadro, segno_sotto  # noqa: E402

PREDEFINITA = 50
MINIMO = 30
MASSIMO = 70


def file_soglia() -> Path:
    return radice_orsa() / "personale" / "rotazione.txt"


def file_visto() -> Path:
    return radice_orsa() / "arturo" / "rotazione-avviso-visto"


def numero(testo: str) -> Optional[int]:
    """La soglia scritta dalla persona ("40", "40%"), o None se non è un intero fra MINIMO e MASSIMO."""
    t = (testo or "").strip().rstrip("%").strip()
    if not t.isdigit():
        return None
    n = int(t)
    return n if MINIMO <= n <= MASSIMO else None


def leggi_file() -> Optional[int]:
    """La soglia del file della persona, o None: un file vuoto, rotto o fuori scala vale come nessuna scelta."""
    try:
        righe = file_soglia().read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return None
    prima = next((r for r in righe if r.strip() and not r.lstrip().startswith("#")), "")
    return numero(prima)


def da_ambiente() -> Optional[int]:
    """CLAUDE_CTX_WARN è il percento RIMASTO: la soglia in contesto usato è 100 meno quello."""
    valore = os.environ.get("CLAUDE_CTX_WARN", "").strip()
    try:
        rimasto = float(valore)
    except ValueError:
        return None
    if not 0 < rimasto < 100:
        return None
    return round(100 - rimasto)


def soglia() -> Tuple[int, str]:
    """La soglia in vigore (percento di contesto usato) e da dove viene: ambiente, file o Arturo."""
    n = da_ambiente()
    if n is not None:
        return n, "ambiente"
    n = leggi_file()
    if n is not None:
        return n, "file"
    return PREDEFINITA, "arturo"


def riga_contesto(n: int) -> str:
    return (f"CONTEXT: a compito chiuso con una traccia (commit, file, decisione, todo) Arturo fa commit, push e "
            f"chiude il todo, poi parte col passo dopo nello stesso contesto. /fine --rotazione parte solo dopo "
            f"l'avviso CONTEXT WARNING (contesto oltre il {n}%) o dalle 18. Il tool ruota (mod rotazione) segue "
            f"solo se il passo dopo è tuo. Senza il mod, all'avviso il compito si chiude e si salva con /fine.")


def avviso(n: int) -> str:
    cmd = comando_arturo()
    corpo = riquadro([
        "",
        "   NOVITÀ DI ARTURO",
        "   Il salvataggio automatico della sessione cambia",
        "",
        "---",
        "",
        "   PRIMA     a ogni compito chiuso Claude salvava, apriva",
        "             una sessione nuova e ripartiva con /inizio.",
        "             Quasi due minuti a ogni giro.",
        "",
        "   ADESSO    a compito chiuso fa il commit, chiude il todo",
        "             e continua nella stessa sessione. Salva e",
        f"             riparte pulito oltre il {n}% del contesto,",
        "             oppure dalle 18.",
        "",
        f"   contesto  {barra(n)}  {n}%",
        f"             {segno_sotto(n, 'qui salva')}",
        "",
        "   MEGLIO    meno attese: sul Mac di chi mantiene Arturo",
        "             erano 299 giri in una settimana, circa 9 ore.",
        "             E Claude ricorda il lavoro fatto prima.",
        "",
        "---",
        "",
        "   VUOI UN'ALTRA SOGLIA?   di' a Claude  \"rotazione al 40%\"",
        "",
        f"   da {MINIMO} a {MASSIMO}: più bassa salva più spesso, più alta resta",
        "   di più nella stessa sessione.",
        "",
    ])
    return ("AVVISO DA DARE ALLA PERSONA: nella tua prima risposta di questa sessione, prima di tutto il resto, "
            "mostra questo riquadro così com'è, in un blocco di codice. Poi lancia "
            f"`{cmd} rotazione visto` e non ripeterlo più. Se la persona chiede un'altra soglia, lancia "
            f"`{cmd} rotazione N`; per tornare alla soglia di Arturo, `{cmd} rotazione togli`.\n" + corpo)


def persona_di_prima() -> bool:
    """L'avviso serve a chi usava già Arturo: chi installa adesso parte con la regola nuova (come NOVITA.md)."""
    radice = radice_orsa()
    return (radice / "data" / "setup-fatto").is_file() or (radice / "session-env" / "novita-viste").is_file()


def riga() -> str:
    n, _ = soglia()
    righe = [riga_contesto(n)]
    if not file_visto().exists() and persona_di_prima():
        righe.append(avviso(n))
    return "\n".join(righe)


def scrivi(percorso: Path, testo: str) -> None:
    percorso.parent.mkdir(parents=True, exist_ok=True)
    nuovo = percorso.with_name(percorso.name + ".nuovo")
    nuovo.write_text(testo, encoding="utf-8")
    os.replace(str(nuovo), str(percorso))


def stato() -> str:
    n, fonte = soglia()
    testo = {
        "ambiente": f"rotazione al {n}% del contesto usato, dalla variabile CLAUDE_CTX_WARN={os.environ.get('CLAUDE_CTX_WARN')} "
                    f"(percento rimasto): vince sul file.\nPer usare arturo rotazione N, togli la variabile da settings.json",
        "file": f"rotazione al {n}% del contesto usato, scelta da te in {file_soglia()}",
        "arturo": f"rotazione al {n}% del contesto usato, la soglia di Arturo",
    }[fonte]
    return testo + ". Dalle 18 il /fine del giorno parte anche prima."


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in ("-h", "--help", "aiuto"):
        print(__doc__.split("\n\n")[1])
        return 0
    if not argv:
        print(a_capo(stato()))
        return 0
    if argv == ["riga"]:
        print(riga())
        return 0
    if argv == ["visto"]:
        scrivi(file_visto(), dt.date.today().isoformat() + "\n")
        print("avviso della rotazione: segnato come visto, non esce più")
        return 0
    if argv == ["togli"]:
        try:
            file_soglia().unlink()
        except FileNotFoundError:
            pass
        except OSError as e:
            print(f"non riesco a togliere {file_soglia()}: {e}", file=sys.stderr)
            return 1
        print(stato())
        return 0
    n = numero(" ".join(argv))
    if n is None:
        print(f"la soglia è un numero intero da {MINIMO} a {MASSIMO}: il percento di contesto usato a cui Claude "
              f"salva e riparte (esempio: arturo rotazione 40)", file=sys.stderr)
        return 3
    scrivi(file_soglia(), "# A che percento di contesto usato Claude salva e riparte (arturo rotazione). "
                          f"Gli aggiornamenti non lo toccano.\n{n}\n")
    print(stato() + " Vale dal prossimo comando di Claude, anche in questa sessione.")
    return 0


if __name__ == "__main__":
    for flusso in (sys.stdout, sys.stderr):
        try:
            flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    raise SystemExit(main())
