#!/usr/bin/env python3
"""CC01-CC05: le domande della terza sera del Computer Club (27/10/2026), fatte a voce da chi usava
Arturo da una settimana.

CC01 la barra in basso dice la quota in parole ("5 ore", "settimana"): chi leggeva "5h 84%" lo prendeva
     per la settimana. L'orario di azzeramento delle 5 ore si vede sempre, quello della settimana solo
     da 75%. L'ultima quota letta resta in cache/statusline/quota.json, mai in data/.
CC02 /guidami legge la quota dal file che la barra scrive ("ho token e tempo, cosa facciamo?").
CC03 la skill concetti spiega l'harness, contesto e memoria, git e GitHub, branch e fork, aggiornamenti, subagent,
     ultracode, le due finestre della quota e il sì a una conferma, ognuno con "In Arturo:". Il README
     conta le skill come le cartelle con SKILL.md.
CC04 /segnala dice il numero che il server assegna ("quando faccio il segnale cosa succede?").
CC05 il riepilogo di /setup presenta /dafare, la quota e il suono dell'attesa; NOVITA ha la voce del 28/10.

Dal 4/11/2026, gli strumenti presi da mattpocock/skills per chi non sa cosa chiedere, dentro i flussi
che ci sono già e senza comandi nuovi:
CC06 prompt-master fa l'intervista a giri sulle idee ancora da decidere (consiglio sotto ogni domanda,
     "sì a tutto"); /guidami cerca le richieste che tornano uguali e ne scrive la scheda da delegare.
CC07 la procedura guidata dello stile Conciso: lo script salva la chiave senza mostrarla, in un file 0600 che un
     secondo giro rilegge uguale anche con virgolette e $, copia il file scaricato, cita la licenza MIT;
     lo stile e la guida Google la usano, mai col prefisso !.
CC08 lo stile Conciso rispiega da capo quando la persona scrive "non ho capito".

Sulla base 443b191 ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import atexit
import http.server
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from salti_windows import dichiara  # noqa: E402

NODE = shutil.which("node") or "node"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def banco_telemetria():
    spec = importlib.util.spec_from_file_location("telemetria_banco", Path(__file__).with_name("test_telemetria.py"))
    assert spec and spec.loader
    banco = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(banco)
    return banco


def barra(repo: Path, home: Path, rate: dict) -> str:
    dati = {"model": {"display_name": "Opus 5"}, "workspace": {"current_dir": str(home)}, "rate_limits": rate}
    env = {"HOME": str(home), "USERPROFILE": str(home), "PATH": os.environ.get("PATH", "")}
    if os.name == "nt":
        env["SYSTEMROOT"] = os.environ.get("SYSTEMROOT", r"C:\Windows")
    p = subprocess.run([NODE, str(repo / "hooks" / "statusline.js")], input=json.dumps(dati), text=True,
                       encoding="utf-8", capture_output=True, env=env, timeout=30, check=False)
    return re.sub(r"\x1b\[[0-9;]*m", "", p.stdout)


def test_cc01(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as d:
        home = Path(d)
        (home / ".claude").mkdir()
        r = barra(repo, home, {"five_hour": {"used_percentage": 23.4, "resets_at": 1793170800},
                               "seven_day": {"used_percentage": 12, "resets_at": 1793430000}})
        assert "5 ore 23%" in r and "settimana 12%" in r, f"CC01 la quota non è in parole: {r!r}"
        assert re.search(r"5 ore 23%, si azzera alle \d\d:\d\d", r), f"CC01 sotto il 75% l'orario delle 5 ore sparisce: {r!r}"
        assert "settimana 12%," not in r, f"CC01 l'orario della settimana compare sotto il 75%: {r!r}"
        r = barra(repo, home, {"five_hour": {"used_percentage": 10}, "seven_day": {"used_percentage": 80,
                                                                                    "resets_at": 1793430000}})
        assert re.search(r"settimana 80%, si azzera \w{3} \d\d:\d\d", r), f"CC01 da 75% la settimana non dice quando: {r!r}"
        f = home / ".claude" / "cache" / "statusline" / "quota.json"
        assert f.exists(), "CC01 la barra non salva la quota per /guidami"
        q = json.loads(read(f))
        assert q["cinque_ore"]["pct"] == 10 and q["settimana"] == {"pct": 80, "resets": 1793430000}, f"CC01 quota salvata: {q}"
        assert not (home / ".claude" / "data").exists(), "CC01 la barra scrive in data/"


def test_cc02(repo: Path) -> None:
    guidami = read(repo / "commands" / "guidami.md")
    assert "cache\" / \"statusline\" / \"quota.json" in guidami, "CC02 /guidami non legge la quota salvata dalla barra"
    assert "si azzera" in guidami and "lavori lunghi" in guidami, "CC02 /guidami non usa la quota per scegliere il lavoro"


def test_cc03(repo: Path) -> None:
    f = repo / "skills" / "concetti" / "SKILL.md"
    assert f.exists(), "CC03 manca la skill concetti"
    testo = read(f)
    m = re.match(r"---\n(.*?)\n---\n", testo, re.S)
    assert m and re.search(r"^name: concetti$", m.group(1), re.M) and "when_to_use:" in m.group(1), \
        "CC03 il frontmatter della skill concetti non è valido"
    voci = re.findall(r"^\*\*(.+?)\*\*", testo[m.end():], re.M)
    attese = ["Harness.", "Contesto e memoria.", "Git e GitHub.", "Branch e fork.", "Le tue modifiche e gli aggiornamenti.",
              "Subagent e modelli più economici.", "Ultracode.", "Le due finestre della quota.", "Dire sì a una conferma."]
    assert voci == attese, f"CC03 le voci della skill concetti sono {voci}"
    assert len(re.findall(r"^In Arturo:", testo, re.M)) == len(attese), "CC03 una voce non dice dove trovi la cosa in Arturo"
    skill = len(list((repo / "skills").glob("*/SKILL.md")))
    readme = read(repo / "README.md")
    assert f"**{skill} skill**" in readme and f"{skill} skill (+ regole" in readme, \
        f"CC03 il README non conta {skill} skill"


class ServerNumero:
    """Come il Server di test_telemetria.py, ma risponde 201 col numero, come server/logica.js."""

    def __init__(self, numero: int):
        self.richieste = []
        fuori = self

        class Gestore(http.server.BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                corpo = self.rfile.read(int(self.headers.get("content-length", 0)))
                fuori.richieste.append((self.path, json.loads(corpo)))
                risposta = json.dumps({"numero": numero, "email": True}).encode("utf-8")
                self.send_response(201)
                self.send_header("content-type", "application/json")
                self.end_headers()
                self.wfile.write(risposta)

            def log_message(self, *_):
                pass

        self.http = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Gestore)
        threading.Thread(target=self.http.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.http.server_address[1]}"
        atexit.register(self.http.shutdown)


def test_cc04(repo: Path) -> None:
    banco = banco_telemetria()
    lab = banco.Lab(repo, ServerNumero(42))
    bozza = lab.dir / "bozza.md"
    bozza.write_text("La barra dice 5h e non capisco.", encoding="utf-8")
    r = lab.arturo("segnala", "prepara", "--tipo", "problema", "--titolo", "quota", "--file", str(bozza))
    pronta = next(x for x in r.stdout.splitlines() if x.startswith("PRONTA: "))[8:]
    r = lab.arturo("segnala", "invia", "--canale", "arturo", "--file", pronta)
    assert r.returncode == 0 and "è la segnalazione n. 42" in r.stdout, \
        f"CC04 /segnala non dice il numero: {r.stdout!r} {r.stderr!r}"
    copie = list((lab.home / ".claude" / "data" / "segnalazioni").glob("*_problema.md"))
    assert copie and "n. 42" in read(copie[0]), "CC04 la copia della segnalazione non tiene il numero"
    assert "è la segnalazione n." in read(repo / "commands" / "segnala.md"), "CC04 /segnala non dice di riferire il numero"


def test_cc05(repo: Path) -> None:
    setup = read(repo / "commands" / "setup.md")
    riepilogo = setup[setup.index("## Riepilogo finale"):]
    for parola in ("/dafare", "quota", "suona"):
        assert parola in riepilogo, f"CC05 il riepilogo di /setup non presenta {parola}"
    novita = read(repo / "NOVITA.md")
    # Una voce del 28/10 sul Computer Club, non per forza la prima: lo stesso giorno ne possono uscire altre.
    voci = [m.start() for m in re.finditer(r"^## 2026-10-28", novita, re.M)]
    assert any("Computer Club" in novita[v:v + 400] for v in voci), "CC05 NOVITA non racconta le domande del Computer Club"


def test_cc06(repo: Path) -> None:
    pm = repo / "skills" / "prompt-master" / "SKILL.md"
    testo = read(pm)
    assert "l'intervista a giri" in testo, "CC06 prompt-master non fa l'intervista a giri sulle idee da decidere"
    for parola in ("Consiglio:", "sì a tutto", "subagent", "aspetta il sì"):
        assert parola in testo, f"CC06 l'intervista di prompt-master non dice {parola!r}"
    guidami = read(repo / "commands" / "guidami.md")
    for parola in ("rifà sempre uguale", "Cosa la fa partire", "Dove chiede a te", "Cosa ti mostra", "/creaskill"):
        assert parola in guidami, f"CC06 /guidami non propone le cose ripetute da delegare: manca {parola!r}"
    assert 'chiedi su cosa sta lavorando' not in guidami, "CC06 /guidami chiede ancora \"su cosa lavori\" a chi non ha segnali"


def test_cc07(repo: Path) -> None:
    script = repo / "shared" / "procedura-guidata.sh"
    assert script.exists(), "CC07 manca shared/procedura-guidata.sh"
    testa = read(script)[:3000]
    assert "mattpocock/skills" in testa and "MIT" in testa, "CC07 la procedura guidata non cita l'origine e la licenza"
    assert "osascript" in testa and "Git Bash" in testa, "CC07 la procedura guidata non dice come aprirla nel Terminale"
    stile = " ".join(read(repo / "output-styles" / "conciso.md").split())
    assert "procedura-guidata.sh" in stile and "mai col prefisso `!`" in stile, "CC07 lo stile Conciso non usa la procedura guidata nel Terminale"
    assert "procedura-guidata.sh" in read(repo / "docs" / "onboarding" / "gws.md"), "CC07 la guida Google non usa la procedura guidata"
    bash = shutil.which("bash")
    assert bash, "CC07 bash non trovato"
    segreto = "s3gr'eto $HOME \"x\""
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        finti = d / "bin"
        finti.mkdir()
        browser = finti / "wslview"  # il primo che lo script prova: nessun browser vero si apre
        browser.write_text(f"#!/bin/sh\necho \"$1\" >> '{(d / 'aperti').as_posix()}'\n", encoding="utf-8")
        browser.chmod(0o755)
        (d / "scaricato.json").write_text("{}", encoding="utf-8")
        prova = read(script).replace(
            "\nfine\n}",
            f'\ncopia_file "{(d / "scaricato.json").as_posix()}" "{(d / "conf" / "client_secret.json").as_posix()}"\nfine\n}}',
        )
        (d / "prova.sh").write_text(prova, encoding="utf-8")
        env = {**os.environ, "ENV_FILE": (d / "env").as_posix(), "PATH": str(finti) + os.pathsep + os.environ.get("PATH", "")}
        giri = []
        for ingresso in (f"\n{segreto}\n", "\n\n"):  # il secondo giro tiene il valore salvato con Invio
            r = subprocess.run([bash, (d / "prova.sh").as_posix()], input=ingresso, capture_output=True,
                               text=True, encoding="utf-8", env=env, timeout=60)
            assert r.returncode == 0, f"CC07 la procedura guidata esce con {r.returncode}: {r.stderr[-400:]!r}"
            assert segreto not in r.stdout and "s3gr" not in r.stdout, "CC07 la procedura guidata mostra la chiave incollata"
            giri.append(read(d / "env"))
        assert giri[0] == giri[1], f"CC07 il secondo giro cambia la chiave salvata: {giri!r}"
        letto = subprocess.run([bash, "-c", f'. "{(d / "env").as_posix()}" && printf %s "$CHIAVE_SERVIZIO"'],
                               capture_output=True, text=True, encoding="utf-8", timeout=30).stdout
        assert letto == segreto, f"CC07 la chiave salvata non torna uguale: {letto!r}"
        assert (d / "conf" / "client_secret.json").exists(), "CC07 copia_file non copia il file scaricato"
        assert "example.com" in read(d / "aperti"), "CC07 la procedura guidata non apre la pagina"
        if os.name == "nt":
            dichiara("CC07", "i permessi 0600 non si provano su Windows")
        else:
            for f in (d / "env", d / "conf" / "client_secret.json"):
                assert (f.stat().st_mode & 0o777) == 0o600, f"CC07 {f.name} è leggibile da altri: {oct(f.stat().st_mode)}"


def test_cc08(repo: Path) -> None:
    stile = read(repo / "output-styles" / "conciso.md")
    assert "## Quando la persona non ha capito" in stile, "CC08 lo stile Conciso non rispiega quando la persona non ha capito"
    sezione = stile[stile.index("## Quando la persona non ha capito"):]
    sezione = sezione[:sezione.index("\n## ", 5)]
    for parola in ("non ho capito", "italiano-semplificato", "una riga di contesto", "Non ripeterlo"):
        assert parola in sezione, f"CC08 la rispiegazione non dice {parola!r}"


TESTS = {"CC01": test_cc01, "CC02": test_cc02, "CC03": test_cc03, "CC04": test_cc04, "CC05": test_cc05,
         "CC06": test_cc06, "CC07": test_cc07, "CC08": test_cc08}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.baseline_ref:
        rossi, altro = [], []
        for nome, test in TESTS.items():
            try:
                test(repo)
            except AssertionError as e:
                (rossi if str(e).startswith(nome) else altro).append(f"{nome}: {e}")
            except Exception as e:  # noqa: BLE001
                altro.append(f"{nome}: {type(e).__name__} {e}")
        assert not altro and len(rossi) == len(TESTS), \
            "baseline non discriminante: ogni controllo deve fallire col suo codice.\n" + "\n".join(altro + rossi)
        print(f"BASELINE_DISCRIMINANTE={','.join(r.split(':')[0] for r in rossi)}")
        return 0
    for test in TESTS.values():
        test(repo)
    print(f"PASS {','.join(TESTS)} controlli={len(TESTS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
