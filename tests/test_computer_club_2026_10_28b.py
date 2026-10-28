#!/usr/bin/env python3
"""CC06-CC10: il secondo giro sulle domande della terza sera del Computer Club (27/10/2026).

CC06 arturo sessione apre una finestra del terminale con /inizio sul progetto o sul todo, su Mac, Windows
     e Linux, sempre per argv. Il titolo del todo perde virgolette e caratteri che cmd legge; un nome di
     progetto vuoto si rifiuta; senza terminale resta il comando da lanciare a mano. Il pannello /dafare
     lo lancia col tasto o ("clicco e vado avanti").
CC07 arturo segnala stato dice a che punto sono le segnalazioni: in attesa, arrivate, corrette con la
     voce di NOVITA.md che cita "segnalazione n. X" ("quando faccio il segnale cosa succede?").
CC08 una segnalazione partita in differita tiene il suo numero: la copia passa da "in attesa" a "n. X".
CC09 prima di un ultracode il hook del prompt aggiunge costo e quota della finestra di 5 ore.
CC10 /proponi porta una tua skill come proposta, ripulita e dopo il sì; è nei comandi della telemetria,
     del server e nella privacy.

Sulla base 5bdec48 ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys
import time
from pathlib import Path


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def modulo(nome: str, file: str):
    spec = importlib.util.spec_from_file_location(nome, Path(__file__).with_name(file))
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def banco_telemetria():
    return modulo("telemetria_banco", "test_telemetria.py")


def stampa(lab, sistema: str, path: str, *argomenti: str):
    lab.env.update(ARTURO_SISTEMA=sistema, PATH=path)
    r = lab.arturo("sessione", *argomenti, "--stampa")
    assert r.returncode == 0, f"CC06 arturo sessione non risponde su {sistema}: {r.stdout!r} {r.stderr!r}"
    return json.loads(r.stdout)


def test_cc06(repo: Path) -> None:
    lab = banco_telemetria().Lab(repo)
    r = lab.arturo("todo", "aggiungi", 'Montare il "mixer" al 100% ^ poi', "--progetto", "libro")
    assert r.returncode == 0, f"CC06 todo di prova non creato: {r.stderr!r}"
    vuota = lab.dir / "vuota"
    vuota.mkdir()
    finti = lab.dir / "finti"
    finti.mkdir()
    for nome in ("gnome-terminal", "wt"):
        f = finti / nome
        f.write_text("#!/bin/sh\n", encoding="utf-8")
        f.chmod(0o755)

    mac = stampa(lab, "darwin", str(vuota), "--todo", "1")
    assert mac["prompt"] == "/inizio libro -- #1 Montare il mixer al 100 poi", f"CC06 prompt del todo: {mac['prompt']!r}"
    assert mac["argv"][0] == "osascript" and "do script (item 1 of argv)" in mac["argv"], \
        f"CC06 su Mac il comando non passa come argomento: {mac['argv']}"
    assert mac["argv"][-1].endswith("&& claude '/inizio libro -- #1 Montare il mixer al 100 poi'"), \
        f"CC06 su Mac il comando non è quotato: {mac['argv'][-1]!r}"

    win = stampa(lab, "windows", str(vuota), "--todo", "1")
    assert win["argv"][:4] == ["cmd", "/c", "start", ""] and win["argv"][-2:] == ["claude", mac["prompt"]], \
        f"CC06 Windows senza wt: {win['argv']}"
    if os.name != "nt":  # su Windows which("wt") vuole wt.exe: il finto vale solo altrove
        win = stampa(lab, "windows", str(finti), "libro")
        assert win["argv"][0] == "wt" and win["argv"][-1] == "/inizio libro", f"CC06 Windows con wt: {win['argv']}"
        lin = stampa(lab, "linux", str(finti), "libro")
        assert lin["argv"][0] == "gnome-terminal" and lin["argv"][-2:] == ["claude", "/inizio libro"], \
            f"CC06 Linux: {lin['argv']}"
    nessuno = stampa(lab, "linux", str(vuota), "libro")
    assert nessuno["argv"] == [] and "claude '/inizio libro'" in nessuno["a_mano"], \
        f"CC06 senza terminale manca il comando a mano: {nessuno}"
    r = lab.arturo("sessione", "--stampa")
    assert r.returncode == 2, f"CC06 un progetto vuoto non si rifiuta: {r.returncode} {r.stdout!r}"

    pannello = read(repo / "skills" / "dafare" / "hooks" / "register.tsx")
    assert 'hotkey="o"' in pannello and "'sessione'" in pannello, "CC06 il pannello /dafare non ha il tasto o"


def copia(cartella: Path, nome: str, titolo: str, esito: str) -> None:
    cartella.mkdir(parents=True, exist_ok=True)
    (cartella / nome).write_text(f"# {titolo}\n\nData: 2026-10-28 09:00\nCanale: arturo\nEsito: {esito}\n\ntesto",
                                 encoding="utf-8")


def test_cc07(repo: Path) -> None:
    lab = banco_telemetria().Lab(repo)
    cartella = lab.home / ".claude" / "data" / "segnalazioni"
    copia(cartella, "2026-10-25_100000_problema.md", "Avviso doppio",
          "arrivata a chi mantiene Arturo: è la segnalazione n. 15")
    copia(cartella, "2026-10-28_090000_proposta.md", "Idea nuova",
          "arrivata a chi mantiene Arturo: è la segnalazione n. 99")
    copia(cartella, "2026-10-28_093000_problema.md", "Rete giù", "in attesa: parte da sola appena il server risponde")
    (lab.home / ".claude" / "NOVITA.md").write_text(
        "# Novità\n\n## 2026-10-29 — Altro\n\nniente\n\n## 2026-10-27 — Avvisi giusti\n\n"
        "**Da sapere**: lo mostravano le segnalazioni n. 14, 15 e 16.\n", encoding="utf-8")
    r = lab.arturo("segnala", "stato")
    assert r.returncode == 0, f"CC07 segnala stato non risponde: {r.stdout!r} {r.stderr!r}"
    righe = r.stdout.splitlines()
    assert any(x.startswith("n. 15") and "corretta" in x and "2026-10-27" in x for x in righe), \
        f"CC07 la n. 15 non risulta corretta: {righe}"
    assert any(x.startswith("n. 99") and "non è ancora uscita" in x for x in righe), f"CC07 la n. 99: {righe}"
    assert any("Rete giù" in x and "in attesa" in x for x in righe), f"CC07 quella in attesa: {righe}"


def test_cc08(repo: Path) -> None:
    numero = modulo("cc_banco", "test_computer_club_2026_10_28.py")
    lab = banco_telemetria().Lab(repo, numero.ServerNumero(42))
    cartella = lab.home / ".claude" / "data" / "segnalazioni"
    copia(cartella, "2026-10-28_093000_problema.md", "Rete giù", "in attesa: parte da sola appena il server risponde")
    (cartella / "2026-10-28_093000_problema.attesa.json").write_text(
        json.dumps({"tipo": "problema", "titolo": "Rete giù", "testo": "x"}), encoding="utf-8")
    lab.arturo("telemetria", "segnalazioni")
    testo = read(cartella / "2026-10-28_093000_problema.md")
    assert "è la segnalazione n. 42" in testo and "in attesa" not in testo, \
        f"CC08 la copia della segnalazione partita in differita non ha il numero: {testo!r}"
    seg = read(repo / "bin" / "segnala.py")
    assert seg.count("adesso:%Y-%m-%d_%H%M%S") >= 2, "CC08 file in attesa e copia non hanno lo stesso nome"


def test_cc09(repo: Path) -> None:
    lab = banco_telemetria().Lab(repo)
    quota = lab.home / ".claude" / "cache" / "statusline" / "quota.json"
    quota.parent.mkdir(parents=True)
    quota.write_text(json.dumps({"cinque_ore": {"pct": 37, "resets": int(time.time()) + 3600}, "settimana": None}),
                     encoding="utf-8")
    r = lab.hook("inject-now.sh", json.dumps({"prompt": "lancia un ultracode sul repo"}))
    righe = [x for x in r.stdout.splitlines() if x.startswith("ULTRACODE:")]
    assert len(righe) == 1 and "5%" in righe[0] and "al 37%" in righe[0] and "si azzera alle" in righe[0], \
        f"CC09 manca l'avviso prima dell'ultracode: {r.stdout!r}"
    quota.unlink()
    r = lab.hook("inject-now.sh", json.dumps({"prompt": "ULTRACODE"}))
    assert "ULTRACODE:" in r.stdout and "al 37%" not in r.stdout, f"CC09 senza quota: {r.stdout!r}"
    r = lab.hook("inject-now.sh", json.dumps({"prompt": "una revisione normale"}))
    assert "ULTRACODE:" not in r.stdout, "CC09 l'avviso esce anche senza ultracode"


def test_cc10(repo: Path) -> None:
    proponi = repo / "commands" / "proponi.md"
    assert proponi.exists(), "CC10 manca /proponi"
    testo = read(proponi)
    assert re.match(r"---\ndescription: .+\nargument-hint: .+\n---\n", testo), "CC10 frontmatter di /proponi"
    for pezzo in ("prepara --tipo proposta", "invia --canale arturo", "file_di_arturo", "percorsi", "sì"):
        assert pezzo in testo, f"CC10 /proponi non ha {pezzo!r}"
    assert '"proponi"' in read(repo / "bin" / "telemetria.py") and '"proponi"' in read(repo / "server" / "logica.js"), \
        "CC10 proponi non è nei comandi della telemetria e del server"
    assert "/proponi" in read(repo / "docs" / "privacy.md"), "CC10 la privacy non dice cosa esce con /proponi"


TESTS = {"CC06": test_cc06, "CC07": test_cc07, "CC08": test_cc08, "CC09": test_cc09, "CC10": test_cc10}


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
