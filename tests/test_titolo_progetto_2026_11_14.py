#!/usr/bin/env python3
"""TT01-TT06: il progetto dedotto dal contenuto in hooks/titolo-sessione.py (14/11/2026) e il titolo di partenza (22/11/2026).

Portato dalla copia della config (#6717, 26/11/2026): l'hook del plugin ha ora titolo, sintesi ADESSO e
progetto nella stessa chiamata.

Volta metteva in "Senza progetto" le sessioni aperte con una richiesta libera, e la sessione di Spoleto
nel progetto dello strumento (post-studio). Il modello piccolo che scrive il titolo sceglie ora anche il
progetto fra quelli noti, e volta_sonda.py lo legge.

TT01 la risposta a due righe: "Titolo:" dà il titolo, la risposta di una riga sola vale come prima,
     "Progetto:" dà lo slug solo se è un progetto noto (anche per nome alternativo), "nessuno" niente.
TT02 il primo verdetto vale subito, un cambio solo se il modello lo ripete, un verdetto vuoto non toglie.
TT03 l'hook intero con un claude finto: Stop scrive titolo e progetto, un cambio isolato non passa, il
     secondo uguale sì; UserPromptSubmit di una sessione nuova non perde il progetto.
TT04 gli appunti: il riassunto di una compattazione va a parte e intero fino a RIASSUNTO, la richiesta che
     ha aperto la sessione resta anche quando la trascrizione è più lunga di CODA, l'elenco dei progetti
     arriva al modello e il progetto della cartella no.
TT05 il titolo di partenza (compito) non comincia con la punteggiatura: "/inizio x -- #6357: fare y" dà
     "fare y", non ": fare y" (22/11/2026).
TT06 il prompt chiede le tre righe TITOLO, ADESSO e PROGETTO, e chiedi_progetti() legge bin/progetti.py
     accanto all'hook (`arturo progetti --json`), senza passare da Volta.

--avvelena rompe ogni regola su una copia dell'hook: ogni veleno deve uscire "TTnn ROSSO".
Solo libreria standard. Nessuna chiamata a un modello vero.
"""
from __future__ import annotations

import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(sys.argv[sys.argv.index("--repo") + 1]) if "--repo" in sys.argv else Path(__file__).resolve().parents[1]
HOOK = REPO / "hooks" / "titolo-sessione.py"
PROGETTI = {"progetti": [
    {"slug": "due-mondi-myway", "titolo": "Festival dei Due Mondi", "descrizione": "SMM per il Festival di Spoleto", "alias": ["due-mondi"]},
    {"slug": "post-studio", "titolo": "Post Office", "descrizione": "editor di post", "alias": ["post-office"]},
    {"slug": "herdr-arturo", "titolo": "Volta", "descrizione": "la finestra di Arturo", "alias": ["volta"]},
]}


def carica(percorso: Path, casa: Path):
    spec = importlib.util.spec_from_file_location(f"titolo_{abs(hash(str(percorso)))}", percorso)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.cartella = lambda: casa / "cache" / "titolo"
    return m


def riga(tipo: str, testo: str) -> str:
    if tipo == "user":
        return json.dumps({"type": "user", "message": {"role": "user", "content": testo}})
    return json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": testo}]}})


def tt01(m) -> str | None:
    noti, _ = m.progetti_noti()
    if m.pulito("Titolo: Programmazione dei post\nProgetto: due-mondi-myway\n") != "Programmazione dei post":
        return "TT01 ROSSO: la riga Titolo della risposta a due righe non dà il titolo"
    if m.pulito("Correzione del banco dei test") != "Correzione del banco dei test":
        return "TT01 ROSSO: la risposta di una riga sola non vale più come titolo"
    if m.pulito("Progetto: due-mondi-myway") != "":
        return "TT01 ROSSO: la sola riga Progetto passa per un titolo"
    casi = {"Titolo: x y\nProgetto: due-mondi-myway": "due-mondi-myway", "Titolo: x y\nProgetto: Due-Mondi": "due-mondi-myway",
            "Titolo: x y\nProgetto: `volta`": "herdr-arturo", "Titolo: x y\nProgetto: nessuno": "",
            "Titolo: x y\nProgetto: spoleto-inventato": "", "Titolo: x y": ""}
    for risposta, atteso in casi.items():
        if m.progetto_scelto(risposta, noti) != atteso:
            return f"TT01 ROSSO: {risposta!r} dà {m.progetto_scelto(risposta, noti)!r}, atteso {atteso!r}"
    return None


def tt02(m) -> str | None:
    casi = [({}, "due-mondi-myway", ("due-mondi-myway", "due-mondi-myway")),
            ({"progetto": "post-studio", "candidato": "post-studio"}, "due-mondi-myway", ("post-studio", "due-mondi-myway")),
            ({"progetto": "post-studio", "candidato": "due-mondi-myway"}, "due-mondi-myway", ("due-mondi-myway", "due-mondi-myway")),
            ({"progetto": "post-studio", "candidato": "post-studio"}, "", ("post-studio", "post-studio"))]
    for salvato, verdetto, atteso in casi:
        if m.accetta(salvato, verdetto) != atteso:
            return f"TT02 ROSSO: da {salvato} con {verdetto!r} esce {m.accetta(salvato, verdetto)}, atteso {atteso}"
    return None


def tt03(m, casa: Path) -> str | None:
    bin_ = casa / "bin"
    bin_.mkdir(exist_ok=True)
    corpo = "import os, sys\nsys.stdin.read()\nsys.stdout.write(open(os.environ['TT_RISPOSTA'], encoding='utf-8').read())\n"
    if os.name == "nt":
        # Windows non lancia uno script con lo shebang: which trova claude.cmd, che passa al python vero
        (bin_ / "claude.py").write_text(corpo, encoding="utf-8")
        (bin_ / "claude.cmd").write_text(f'@"{sys.executable}" "%~dp0claude.py" %*\r\n', encoding="utf-8")
    else:
        finto = bin_ / "claude"
        finto.write_text("#!" + sys.executable + "\n" + corpo, encoding="utf-8")
        finto.chmod(0o755)
    risposta = casa / "risposta.txt"
    os.environ.update(PATH=f"{bin_}{os.pathsep}{os.environ.get('PATH', '')}", TT_RISPOSTA=str(risposta), ARTURO_TITOLI_OGNI="0")
    tr = casa / "s1.jsonl"
    f = casa / "cache" / "titolo" / "s1.json"

    def stop(progetto: str, frase: str) -> dict:
        risposta.write_text(f"TITOLO: Lavoro sui post\nADESSO: Scrive i post\nPROGETTO: {progetto}\n", encoding="utf-8")
        with open(tr, "a", encoding="utf-8") as fh:
            fh.write(riga("user", frase) + "\n" + riga("assistant", "fatto") + "\n")
        sys.stdin = io.TextIOWrapper(io.BytesIO(json.dumps({"hook_event_name": "Stop", "session_id": "s1",
                                                              "transcript_path": str(tr)}).encode()), encoding="utf-8")
        m.main()
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}

    if stop("due-mondi-myway", "programma i post del festival").get("progetto") != "due-mondi-myway":
        return f"TT03 ROSSO: il primo Stop non scrive il progetto: {f.read_text(encoding='utf-8') if f.exists() else 'niente'}"
    if stop("post-studio", "correggi l'editor dei post").get("progetto") != "due-mondi-myway":
        return "TT03 ROSSO: un verdetto diverso isolato cambia subito il progetto"
    if stop("post-studio", "correggi ancora l'editor").get("progetto") != "post-studio":
        return "TT03 ROSSO: il verdetto ripetuto non cambia il progetto"
    if stop("nessuno", "va bene cosi grazie mille").get("progetto") != "post-studio":
        return "TT03 ROSSO: nessuno toglie il progetto"
    f2 = casa / "cache" / "titolo" / "s2.json"
    f2.write_text(json.dumps({"progetto": "herdr-arturo", "candidato": "herdr-arturo"}), encoding="utf-8")
    sys.stdin = io.TextIOWrapper(io.BytesIO(json.dumps({"hook_event_name": "UserPromptSubmit", "session_id": "s2",
                                                          "prompt": "sistema la finestra"}).encode()), encoding="utf-8")
    m.main()
    if json.loads(f2.read_text(encoding="utf-8")).get("progetto") != "herdr-arturo":
        return "TT03 ROSSO: il titolo di avvio cancella il progetto"
    return None


def tt04(m, casa: Path) -> str | None:
    tr = casa / "lunga.jsonl"
    riassunto = "This session is being continued from a previous conversation. Summary: " + "Spoleto e Due Mondi. " * 40
    with open(tr, "w", encoding="utf-8") as fh:
        fh.write(riga("user", "ci sono errori in Volta da sistemare subito") + "\n")
        fh.write(riga("assistant", "x" * 5000) + "\n")
        fh.write(riga("user", riassunto) + "\n")
        fh.write(riga("assistant", "ho finito il giro") + "\n")
    m.CODA = 2000  # la richiesta d'apertura resta fuori dalla coda
    a = m.appunti(str(tr), "", "", "- due-mondi-myway: Festival dei Due Mondi")
    if "Richiesta che ha aperto la sessione: ci sono errori in Volta" not in a:
        return f"TT04 ROSSO: la richiesta che ha aperto la sessione si perde oltre CODA: {a[:300]!r}"
    if "Riassunto della conversazione di prima: Spoleto" not in a or "Richiesta della persona: This session" in a:
        return f"TT04 ROSSO: il riassunto di una compattazione non va a parte: {a[:400]!r}"
    if "- due-mondi-myway: Festival dei Due Mondi" not in a:
        return "TT04 ROSSO: l'elenco dei progetti non arriva al modello"
    if len(a) < m.RIASSUNTO:
        return f"TT04 ROSSO: gli appunti tagliano il riassunto: {len(a)} caratteri"
    return None


def tt05(m) -> str | None:
    for prompt, atteso in (("/inizio volta -- #6357: Sistemare il giudice", "Sistemare il giudice"),
                           ("/inizio volta -- --rotazione (#6357): fare y", "fare y"),
                           ("/inizio volta -- --rotazione Step 3: fare y", "Step 3: fare y"),
                           ("#12 - correggere il banco", "correggere il banco")):
        if m.compito(prompt) != atteso:
            return f"TT05 ROSSO: {prompt!r} dà {m.compito(prompt)!r}, atteso {atteso!r}"
    return None


def tt06(m) -> str | None:
    for riga in ("TITOLO:", "ADESSO:", "PROGETTO:"):
        if riga not in m.ISTRUZIONE:
            return f"TT06 ROSSO: il prompt non chiede la riga {riga}"
    if m.due_righe("TITOLO: Lavoro sui post\nADESSO: Scrive i post\nPROGETTO: post-studio") != ("Lavoro sui post", "Scrive i post"):
        return "TT06 ROSSO: la riga PROGETTO rompe titolo e sintesi"
    d = m.chiedi_progetti()
    if not isinstance(d, dict) or not isinstance(d.get("progetti"), list):
        return f"TT06 ROSSO: chiedi_progetti() non legge bin/progetti.py accanto all'hook: {d!r}"[:200]
    return None


def prova(percorso: Path) -> list:
    rossi = []
    vecchio = dict(os.environ)
    with tempfile.TemporaryDirectory(prefix="tt-") as d:
        casa = Path(d)
        (casa / "cache" / "titolo").mkdir(parents=True)
        (casa / "progetti.json").write_text(json.dumps(PROGETTI), encoding="utf-8")
        os.environ["ARTURO_TITOLI_PROGETTI"] = str(casa / "progetti.json")
        os.environ.pop("ARTURO_TITOLO_FIGLIO", None)
        os.environ.pop("ARTURO_TITOLI", None)
        try:
            m = carica(percorso, casa)
            for caso in (lambda: tt01(m), lambda: tt02(m), lambda: tt03(m, casa), lambda: tt04(m, casa), lambda: tt05(m), lambda: tt06(m)):
                try:
                    r = caso()
                except Exception as e:  # noqa: BLE001 - un caso che getta è rosso, col suo motivo
                    r = f"ROSSO per eccezione: {type(e).__name__}: {e}"
                if r:
                    rossi.append(r)
        finally:
            os.environ.clear()
            os.environ.update(vecchio)
    return rossi


VELENI = [
    ("TT01", '    if len(etichettate) == 1:\n        righe = etichettate\n', '    if False:\n        righe = etichettate\n'),
    ("TT01", '            return noti.get(v, "")', '            return v'),
    ("TT02", '    if not verdetto:\n        return prima, candidato\n', ''),
    ("TT02", '    if not prima or verdetto == prima or verdetto == candidato:', '    if True:'),
    ("TT03", '        if progetto:\n            nuovo.update(progetto=progetto, candidato=candidato)\n', ''),
    ("TT03", ',\n                       **{k: salvato[k] for k in ("progetto", "candidato") if k in salvato}})', '})'),
    ("TT04", '            if lungo > CODA:', '            if False:'),
    ("TT04", '            if grezzo.lstrip().startswith(COMPATTATA):', '            if False:'),
    ("TT04", '        pezzi.append("Progetti noti:\\n" + noti)', '        pass'),
    ("TT05", 'accorcia(re.sub(r"^[\\s,;:.·|—–-]+", "", p.split("\\n")[0])', 'accorcia((p.split("\\n")[0])'),
    ("TT06", '    "PROGETTO: <slug oppure nessuno>"', '    "nessuno"'),
    ("TT06", '.parent.parent / "bin" / "progetti.py"', '.parent.parent / "bin" / "progetti-x.py"'),
]


def avvelena() -> int:
    testo = HOOK.read_text(encoding="utf-8")
    morsi = 0
    for codice, vecchio, nuovo in VELENI:
        if testo.count(vecchio) != 1:
            print(f"VELENO {codice} NON SI APPLICA: {vecchio[:60]!r}")
            continue
        with tempfile.TemporaryDirectory(prefix="tt-veleno-") as d:
            shutil.copytree(str(REPO / "hooks"), str(Path(d) / "hooks"))
            shutil.copytree(str(REPO / "bin"), str(Path(d) / "bin"))
            copia = Path(d) / "hooks" / "titolo-sessione.py"
            copia.write_text(testo.replace(vecchio, nuovo), encoding="utf-8")
            rossi = [r for r in prova(copia) if r.startswith(f"{codice} ROSSO")]
        print(f"VELENO {codice} " + (f"ROSSO: {rossi[0][:120]}" if rossi else "NON ATTACCA"))
        morsi += bool(rossi)
    print(f"veleni rossi {morsi}/{len(VELENI)}")
    return 0 if morsi == len(VELENI) else 1


def main() -> int:
    if "--avvelena" in sys.argv:
        return avvelena()
    rossi = prova(HOOK)
    for r in rossi:
        print(r)
    print(f"titolo-progetto: {6 - len(rossi)}/6 casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    raise SystemExit(main())
