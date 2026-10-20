#!/usr/bin/env python3
"""S01-S09: /segnala, il canale con cui chi usa Arturo manda problemi, idee e integrazioni.

Ogni caso gira con una HOME finta e con comandi finti nel PATH (open, xdg-open, pbcopy, xclip,
wl-copy, gh) che scrivono su file cosa hanno ricevuto. Niente parte davvero.
Sulla base 75c8e23, prima di /segnala, ogni controllo deve fallire per conto suo.
"""
from __future__ import annotations

import argparse
import atexit
import datetime as dt
import json
import os
import shutil
import re
import subprocess
import sys
import tempfile
import urllib.parse
from pathlib import Path

# Su Windows "bash" per nome è quello di WSL: si prende il bash del PATH (Git Bash).
BASH = shutil.which("bash") or "bash"

FINTI = {
    "open": 'printf "%s\\n" "$1" >> "$LOG_FINTI/apri"',
    "xdg-open": 'printf "%s\\n" "$1" >> "$LOG_FINTI/apri"',
    "pbcopy": 'cat > "$LOG_FINTI/appunti"',
    "xclip": 'cat > "$LOG_FINTI/appunti"',
    "wl-copy": 'cat > "$LOG_FINTI/appunti"',
    "gh": 'printf "%s\\n" "$@" > "$LOG_FINTI/gh"; '
          'for a in "$@"; do [ "$prossimo" = 1 ] && cp "$a" "$LOG_FINTI/gh-corpo"; '
          '[ "$a" = "--body-file" ] && prossimo=1 || prossimo=0; done; '
          'echo "https://github.com/stellakamikaze/arturo/issues/999"',
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class Lab:
    def __init__(self, repo: Path):
        self.repo = repo
        self.dir = Path(tempfile.mkdtemp(prefix="arturo-s."))
        atexit.register(shutil.rmtree, self.dir, True)
        self.home = self.dir / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.log = self.dir / "log"
        self.log.mkdir()
        finti = self.dir / "finti"
        finti.mkdir()
        for nome, corpo in FINTI.items():
            f = finti / nome
            f.write_text("#!/bin/sh\n" + corpo + "\n", encoding="utf-8")
            f.chmod(0o755)
        self.env = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home), LOG_FINTI=str(self.log),
                        PATH=f"{finti}{os.pathsep}{os.environ.get('PATH', '')}")
        self.env.pop("ARTURO_OGGI", None)

    def arturo(self, *argomenti: str, oggi: str | None = None) -> subprocess.CompletedProcess:
        env = dict(self.env, **({"ARTURO_OGGI": oggi} if oggi else {}))
        return subprocess.run([sys.executable, "-B", str(self.repo / "bin" / "arturo"), "segnala", *argomenti],
                              capture_output=True, text=True, env=env, timeout=60)

    def bozza(self, testo: str) -> Path:
        f = self.dir / "bozza.md"
        f.write_text(testo, encoding="utf-8")
        return f

    def pronta(self, tipo: str = "problema", titolo: str = "fine si ferma", testo: str = "Il commit non parte.") -> Path:
        r = self.arturo("prepara", "--tipo", tipo, "--titolo", titolo, "--file", str(self.bozza(testo)))
        assert r.returncode == 0, f"prepara non riuscito: {r.stderr!r}"
        riga = next(x for x in r.stdout.splitlines() if x.startswith("PRONTA: "))
        return Path(riga[len("PRONTA: "):])

    def stato(self) -> dict:
        return json.loads(read(self.home / ".claude" / "session-env" / "segnala.json"))


def test_s01(repo: Path) -> None:
    lab = Lab(repo)
    testo = f"Facevo /fine in {lab.home}/progetti/libro e in /Users/mario/x\nErrore: boom"
    r = lab.arturo("prepara", "--tipo", "problema", "--titolo", "fine si ferma", "--file", str(lab.bozza(testo)))
    assert r.returncode == 0, f"S01 prepara: {r.returncode} {r.stderr!r}"
    pronta = json.loads(read(Path(next(x for x in r.stdout.splitlines() if x.startswith("PRONTA: "))[8:])))
    assert pronta["titolo"] == "[problema] fine si ferma", f"S01 titolo senza il tipo: {pronta['titolo']!r}"
    assert str(lab.home) not in pronta["testo"] and "/Users/mario" not in pronta["testo"], \
        f"S01 una cartella personale resta nel testo: {pronta['testo']!r}"
    assert "~/progetti/libro" in pronta["testo"], "S01 la cartella non diventa ~"


def test_s02(repo: Path) -> None:
    lab = Lab(repo)
    finto = "ghp_" + "a1B2c3D4e5" * 4
    r = lab.arturo("prepara", "--tipo", "problema", "--titolo", "x", "--file", str(lab.bozza(f"token {finto}")))
    assert r.returncode == 3, f"S02 un segreto nella bozza non ferma prepara: {r.returncode}"
    assert finto not in r.stdout + r.stderr, "S02 prepara stampa il segreto che ha trovato"
    assert not list(lab.dir.glob("*.pronta.json")), "S02 il file pronto esiste lo stesso"
    # Il file pronto cambiato dopo prepara: invia ripete il controllo.
    pronta = lab.pronta()
    dati = json.loads(read(pronta))
    dati["testo"] += f"\n{finto}"
    pronta.write_text(json.dumps(dati), encoding="utf-8")
    r = lab.arturo("invia", "--canale", "gh", "--file", str(pronta))
    assert r.returncode == 3 and not (lab.log / "gh").exists(), "S02 invia manda un testo con un segreto"


def test_s03(repo: Path) -> None:
    lab = Lab(repo)
    assert lab.arturo("chiedi", oggi="2026-10-13").returncode == 0, "S03 la prima domanda non arriva"
    assert lab.arturo("chiedi", oggi="2026-10-13").returncode == 3, "S03 la domanda arriva due volte nello stesso giorno"
    assert lab.arturo("chiedi", oggi="2026-10-19").returncode == 3, "S03 la domanda torna prima di 7 giorni"
    assert lab.arturo("chiedi", oggi="2026-10-21").returncode == 0, "S03 dopo 8 giorni la domanda non torna"
    # Una segnalazione appena mandata vale come domanda fatta.
    lab2 = Lab(repo)
    assert lab2.arturo("invia", "--canale", "email", "--file", str(lab2.pronta())).returncode == 0
    assert lab2.arturo("chiedi").returncode == 3, "S03 la domanda arriva subito dopo una segnalazione"


def test_s04(repo: Path) -> None:
    lab = Lab(repo)

    def avvio() -> str:
        return subprocess.run([BASH, str(repo / "hooks" / "session-start.sh")], capture_output=True, text=True,
                              env=lab.env, cwd=str(lab.dir), stdin=subprocess.DEVNULL, timeout=60).stdout
    assert "SEGNALA:" in avvio(), "S04 l'avvio non invita a segnalare"
    assert lab.arturo("basta").returncode == 0
    assert lab.arturo("chiedi").returncode == 3, "S04 dopo basta la domanda di /fine arriva lo stesso"
    assert "SEGNALA:" not in avvio(), "S04 dopo basta l'avvio invita lo stesso"
    assert lab.arturo("riprendi").returncode == 0
    assert "SEGNALA:" in avvio(), "S04 dopo riprendi l'invito non torna"
    assert lab.arturo("chiedi").returncode == 0, "S04 dopo riprendi la domanda non torna"


def test_s05(repo: Path) -> None:
    lab = Lab(repo)
    r = lab.arturo("invia", "--canale", "email", "--file", str(lab.pronta()))
    assert r.returncode == 0, f"S05 invia email: {r.stderr!r}"
    assert "federico@stellakamikaze.org" in r.stdout, "S05 l'indirizzo non è stampato"
    assert "Il commit non parte." in read(lab.log / "appunti"), "S05 il testo non è negli appunti"
    assert not (lab.log / "apri").exists(), "S05 il canale email apre qualcosa: deve solo copiare"
    assert not re.search(r"[\"']mailto:", read(repo / "bin" / "segnala.py")), \
        "S05 segnala.py costruisce un mailto:, su cui comms-guard chiede conferma"
    copie = list((lab.home / ".claude" / "data" / "segnalazioni").glob("*_problema.md"))
    assert len(copie) == 1 and "Canale: email" in read(copie[0]), "S05 la copia locale manca"
    assert lab.stato()["canale"] == "email" and lab.stato()["inviata"], "S05 lo stato non registra l'invio"


def test_s06(repo: Path) -> None:
    lab = Lab(repo)
    r = lab.arturo("invia", "--canale", "web", "--file", str(lab.pronta()))
    assert r.returncode == 0, f"S06 invia web: {r.stderr!r}"
    url = read(lab.log / "apri").strip()
    q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    assert url.startswith("https://github.com/stellakamikaze/arturo/issues/new?"), f"S06 URL sbagliato: {url[:80]}"
    assert q.get("title") == ["[problema] fine si ferma"] and "Il commit non parte." in q.get("body", [""])[0], \
        f"S06 titolo o testo non arrivano nella pagina: {q}"
    lab2 = Lab(repo)
    lungo = "riga lunga di log " * 600
    r = lab2.arturo("invia", "--canale", "web", "--file", str(lab2.pronta(testo=lungo)))
    q = urllib.parse.parse_qs(urllib.parse.urlparse(read(lab2.log / "apri").strip()).query)
    assert r.returncode == 0 and "body" not in q and q.get("title"), "S06 un testo lungo finisce nell'URL"
    assert "riga lunga di log" in read(lab2.log / "appunti"), "S06 il testo lungo non è negli appunti"


def test_s07(repo: Path) -> None:
    lab = Lab(repo)
    r = lab.arturo("invia", "--canale", "gh", "--file", str(lab.pronta(tipo="integrazione", titolo="Notion")))
    assert r.returncode == 0, f"S07 invia gh: {r.stderr!r}"
    argomenti = read(lab.log / "gh").splitlines()
    assert argomenti[:2] == ["issue", "create"] and "stellakamikaze/arturo" in argomenti, f"S07 gh: {argomenti}"
    assert "[integrazione] Notion" in argomenti and "--body-file" in argomenti, f"S07 gh: {argomenti}"
    assert "Il commit non parte." in read(lab.log / "gh-corpo"), "S07 il corpo della issue non è il testo preparato"
    assert "issues/999" in r.stdout, "S07 il link della issue non è stampato"


def test_s08(repo: Path) -> None:
    fine = read(repo / "commands" / "fine.md")
    assert "arturo\" segnala chiedi" in fine, "S08 /fine non chiede la domanda della settimana"
    # 20/10/2026: la chiusura di /fine è una riga tecnica, non più una tabella: la segnalazione è una sua voce.
    chiusura = fine.split("## Chiusura", 1)[1] if "## Chiusura" in fine else ""
    assert "| Segnalazione" in fine or "segnalazione:" in chiusura, "S08 la chiusura di /fine non dice la segnalazione"
    assert "/segnala" in read(repo / "commands" / "setup.md"), "S08 /setup non presenta /segnala"
    assert "/segnala" in read(repo / "README.md"), "S08 il README non cita /segnala"
    assert "federico@stellakamikaze.org" in read(repo / "bin" / "segnala.py"), "S08 l'indirizzo email manca"
    assert (repo / ".github" / "ISSUE_TEMPLATE" / "integrazione.yml").exists(), "S08 manca il modello integrazione"
    assert "data/segnalazioni/" in read(repo / ".gitignore"), "S08 le copie delle segnalazioni entrano in git"


def test_s09(repo: Path) -> None:
    # Lo stato scritto dalla prima versione del 13/10 non ha "versione": il canale manuale decade.
    lab = Lab(repo)
    f = lab.home / ".claude" / "session-env" / "segnala.json"
    f.parent.mkdir(parents=True)
    f.write_text(json.dumps({"domanda": "2026-10-13", "inviata": "2026-10-13", "canale": "web", "pausa": None}),
                 encoding="utf-8")
    r = lab.arturo("canale")
    assert (r.returncode, r.stdout.strip()) == (3, "nessuno"), f"S09 resta il canale manuale della prima versione: {r.stdout!r}"
    assert lab.arturo("canale", "email").returncode == 0
    assert lab.arturo("canale").stdout.strip() == "email", "S09 un canale scelto dopo l'aggiornamento non resta"
    assert lab.stato()["versione"] == 2 and lab.stato()["inviata"] == "2026-10-13", "S09 lo stato perde dati"
    f.write_text(json.dumps({"canale": "arturo"}), encoding="utf-8")
    assert lab.arturo("canale").stdout.strip() == "arturo", "S09 il canale diretto non resta"


TESTS = {"S01": test_s01, "S02": test_s02, "S03": test_s03, "S04": test_s04,
         "S05": test_s05, "S06": test_s06, "S07": test_s07, "S08": test_s08, "S09": test_s09}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    args = parser.parse_args()
    repo = args.repo.resolve()
    # Su Windows i finti in bash non partono: /segnala troverebbe gh.exe, clip e il browser veri.
    # Il 16/10/2026 S07 ha aperto una issue vera su stellakamikaze/arturo. Ogni controllo che
    # lancia "invia" gira solo su macOS e Linux, anche sulla base.
    saltati = ["S02", "S03", "S05", "S06", "S07"] if os.name == "nt" else []
    scelti = {k: v for k, v in TESTS.items() if k not in saltati}
    if args.baseline_ref:
        failed = []
        for name, test in scelti.items():
            try:
                test(repo)
            except (AssertionError, OSError, ValueError, KeyError, StopIteration, json.JSONDecodeError,
                    subprocess.SubprocessError):
                failed.append(name)
        assert failed == list(scelti), f"baseline non discriminante: falliscono solo {failed} su {list(scelti)}"
        print(f"BASELINE_DISCRIMINANTE={','.join(failed)}")
        return 0
    for test in scelti.values():
        test(repo)
    if saltati:
        print(f"SALTA {','.join(saltati)} su Windows: appunti e browser veri, senza finti")
    print(f"PASS {','.join(scelti)} controlli={len(scelti)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
