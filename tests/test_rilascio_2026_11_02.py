#!/usr/bin/env python3
"""RL01-RL09: i ritocchi prima del rilascio del 2/11/2026.

RL01 /setup sta sotto il tetto di 30 KB dell'audit: la FASE 8d (Lancillotto, solo Mac) vive in
     shared/setup-lancillotto.md, che /setup nomina e che ha ancora il comando d'installazione (#4104).
RL02 i testi seguono i comandi nuovi del 28/10 (#4105): il README conta i comandi come i file di
     commands/ e la rotta come quelli in vetrina, dice l'avviso prima di un ultracode; il pannello
     /dafare non promette che ogni tasto si annulla; segnala.py racconta stato; sessione.py non rimanda
     alla pagina personale e non usa una funzione privata di segnala.
RL03 il tasto o del pannello passa il titolo atteso, e arturo sessione si ferma se il todo con quel
     numero ha un altro titolo (#4106): dopo un merge la sessione partirebbe sul lavoro sbagliato.
RL04 /segnala non vede un segreto nel base64 di un'immagine in linea, come la guardia credenziali
     (#4078); una chiave nel testo la trova ancora.
RL05 l'avvio della sessione mette ~/.claude/bin nel PATH dei comandi di Claude con $CLAUDE_ENV_FILE,
     una riga sola anche dopo due avvii (segnalazione n. 33).
RL06 il promemoria di inject-now dice che una correzione a lavoro iniziato è una riga, come prompt-master
     (segnalazione n. 34).
RL07 la barra in basso mostra il progetto che la scheda ha trovato per la sessione, senza il ramo di
     un altro repository; senza scheda resta la cartella (segnalazione n. 35).
RL08 il ramo resta quando scheda e repository sono lo stesso progetto scritto in due modi: la config
     ("claude-config" e ~/.claude), un nome di cartella con maiuscole e spazi, un worktree (#4262).
RL09 l'avviso di contesto propone /fine come salvataggio a ogni giro, e /clear e /inizio una volta sola
     per sessione: chi usa Arturo spesso continua dopo /fine (#3883).

Sulla base 60b7d8d ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

PAROLE = {9: "Nove", 10: "Dieci", 11: "Undici", 12: "Dodici"}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def test_rl01(repo: Path) -> None:
    setup = repo / "commands" / "setup.md"
    peso = setup.stat().st_size
    assert peso <= 30000, f"RL01 /setup pesa {peso} byte, oltre il tetto di 30000 dell'audit"
    testo = read(setup)
    fase = testo[testo.index("## FASE 8d"):testo.index("## FASE 9")]
    assert "~/.claude/shared/setup-lancillotto.md" in fase, "RL01 la FASE 8d non dice dove leggere la sua procedura"
    parte = read(repo / "shared" / "setup-lancillotto.md")
    assert "gh repo clone stellakamikaze/lancillotto" in parte and "installa.sh" in parte and "Accessibilità" in parte, \
        "RL01 shared/setup-lancillotto.md non ha domanda, controlli e installazione"


def test_rl02(repo: Path) -> None:
    readme = read(repo / "README.md")
    comandi = len(list((repo / "commands").glob("*.md")))
    assert f"**{comandi} slash command**" in readme and f"{comandi} slash command (" in readme, \
        f"RL02 il README non conta {comandi} slash command"
    rotta = readme[readme.index("### La rotta"):]
    rotta = rotta[:rotta.index("\n## ")] if "\n## " in rotta else rotta
    vetrina = len(re.findall(r"^- \*\*`/", rotta, re.MULTILINE))
    assert f"{PAROLE.get(vetrina, vetrina)} comandi, e Arturo" in rotta, \
        f"RL02 la rotta mostra {vetrina} comandi ma il testo ne conta un altro numero"
    riga = next((r for r in readme.splitlines() if r.startswith("- `inject-now.sh`")), "")
    blocco = readme[readme.index(riga):readme.index("- `input-notifier-start.sh`")] if riga else ""
    assert "ultracode" in blocco, "RL02 il README non dice che inject-now avvisa prima di un ultracode"
    pannello = read(repo / "skills" / "dafare" / "hooks" / "register.tsx")
    assert 'Ogni tasto si annulla con "u"' not in pannello, "RL02 il pannello promette che ogni tasto si annulla"
    assert "La CLI dei todo si è fermata" not in pannello, "RL02 un errore di arturo sessione parla della CLI dei todo"
    segnala = read(repo / "bin" / "segnala.py")
    assert "- stato:" in segnala.split('"""', 2)[1], "RL02 la docstring di segnala.py non racconta stato"
    sessione = read(repo / "bin" / "sessione.py")
    assert "dafare personale" not in sessione and "segnala._copia" not in sessione, \
        "RL02 sessione.py rimanda alla pagina personale o usa una funzione privata di segnala"


def test_rl03(repo: Path) -> None:
    pannello = read(repo / "skills" / "dafare" / "hooks" / "register.tsx")
    verbi = read(repo / "skills" / "dafare" / "hooks" / "verbi.mjs")
    # Il parametro lo costruisce solo titolo() di verbi.mjs, come per gli altri tasti (#4175).
    assert "'sessione'" in pannello and "titolo(t)" in pannello.split("async function apriSessione")[-1][:900] \
        and "export function titolo(t)" in verbi and "--titolo-atteso=${t.titolo}" in verbi, \
        "RL03 il tasto o non passa il titolo atteso"
    spec = importlib.util.spec_from_file_location("telemetria_banco", Path(__file__).with_name("test_telemetria.py"))
    assert spec and spec.loader
    banco = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(banco)
    lab = banco.Lab(repo)
    lab.env.update(ARTURO_SISTEMA="linux")
    r = lab.arturo("todo", "aggiungi", "Montare il mixer", "--progetto", "libro")
    assert r.returncode == 0, f"RL03 todo di prova non creato: {r.stderr!r}"
    r = lab.arturo("sessione", "--todo", "1", "--titolo-atteso=Montare il mixer", "--stampa")
    assert r.returncode == 0 and "Montare il mixer" in r.stdout, f"RL03 col titolo giusto non apre: {r.returncode} {r.stderr!r}"
    r = lab.arturo("sessione", "--todo", "1", "--titolo-atteso=Scrivere il capitolo", "--stampa")
    assert r.returncode == 1 and "non è più come" in r.stderr and "/inizio" not in r.stdout, \
        f"RL03 con un altro titolo la sessione parte lo stesso: {r.returncode} {r.stdout!r} {r.stderr!r}"


def test_rl04(repo: Path) -> None:
    chiave = "AKIA" + "ABCDEFGHIJKLMNOP"
    prova = ("import json, sys; sys.path.insert(0, sys.argv[1]); import segnala; "
             "print(json.dumps([segnala.segreti_trovati(t) for t in json.loads(sys.argv[2])]))")
    testi = ["schermata ![x](data:image/png;base64,iVBORw0KGgo" + chiave + "AAAA==) fine", "chiave " + chiave]
    r = subprocess.run([sys.executable, "-B", "-c", prova, str(repo / "bin"), json.dumps(testi)],
                       capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, f"RL04 segnala non si importa: {r.stderr[-300:]}"
    immagine, testo = json.loads(r.stdout.strip().splitlines()[-1])
    assert not immagine, f"RL04 /segnala vede {immagine} nel base64 di un'immagine in linea"
    assert testo, "RL04 /segnala non trova più una chiave scritta nel testo"


def test_rl05(repo: Path) -> None:
    bash = shutil.which("bash") or "bash"
    with tempfile.TemporaryDirectory() as d:
        home = Path(d) / "home"
        shutil.copytree(repo, home / ".claude", ignore=shutil.ignore_patterns(".git", "__pycache__", "cache"))
        ambiente = Path(d) / "ambiente.sh"
        ambiente.write_text("", encoding="utf-8")
        env = {"HOME": str(home), "USERPROFILE": str(home), "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
               "CLAUDE_ENV_FILE": str(ambiente),
               "ARTURO_BANCHI_AVVIO": "0", "ARTURO_TELEMETRIA": "0", "GIT_CONFIG_GLOBAL": "/dev/null",
               "TMPDIR": tempfile.gettempdir()}
        for _ in range(2):
            subprocess.run([bash, str(home / ".claude" / "hooks" / "session-start.sh")], input="{}", text=True,
                           capture_output=True, cwd=d, env=env, timeout=60)
        righe = [r for r in ambiente.read_text(encoding="utf-8").splitlines() if ".claude/bin" in r]
        assert len(righe) == 1, f"RL05 l'avvio non mette ~/.claude/bin nel PATH una volta sola: {righe}"
        trovato = subprocess.run([bash, "-c", f'source "{ambiente}"; command -v arturo'], text=True,
                                 capture_output=True, env=env, timeout=30).stdout.strip()
        assert trovato == str(home / ".claude" / "bin" / "arturo"), f"RL05 arturo non si trova per nome: {trovato!r}"


def test_rl06(repo: Path) -> None:
    promemoria = " ".join(read(repo / "hooks" / "inject-now.sh").split("<<'PROMEMORIA'", 1)[-1].split())
    assert "correzione a lavoro iniziato è una riga" in promemoria and "Brief corretto" in promemoria, \
        "RL06 il promemoria chiede prompt e brief interi anche per una correzione a lavoro iniziato"


def ambiente(home: Path) -> dict:
    """HOME finta per statusline.js. Su Windows node non parte senza SystemRoot e il PATH vero."""
    env = {"HOME": str(home), "USERPROFILE": str(home), "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
           "GIT_CONFIG_GLOBAL": os.devnull}
    if os.name == "nt":
        env.update({k: v for k, v in os.environ.items() if k.upper() in ("SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP")})
    return env


def test_rl07(repo: Path) -> None:
    node = shutil.which("node")
    assert node, "RL07 serve node per provare statusline.js"
    with tempfile.TemporaryDirectory() as d:
        home = Path(d) / "home"
        (home / ".claude" / "cache" / "scheda").mkdir(parents=True)
        (home / ".claude" / "cache" / "scheda" / "s1.json").write_text(
            json.dumps({"stato": "lavoro", "progetto": "amministrazione\x1b]0;x"}), encoding="utf-8")
        altro = Path(d) / "altro"
        altro.mkdir()
        subprocess.run(["git", "init", "-q", "-b", "main", str(altro)], check=True, capture_output=True)
        env = ambiente(home)

        def barra(sessione: str, cartella: Path) -> str:
            dati = {"session_id": sessione, "workspace": {"current_dir": str(cartella)}, "model": {"display_name": "Opus"}}
            r = subprocess.run([node, str(repo / "hooks" / "statusline.js")], input=json.dumps(dati), text=True,
                               encoding="utf-8", capture_output=True, env=env, timeout=30)
            return re.sub(r"\x1b\[[0-9;]*m", "", r.stdout)
        con = barra("s1", altro)
        assert "amministrazione" in con and "@main" not in con and "\x1b]" not in con, \
            f"RL07 la barra non mostra il progetto della scheda, o mostra il ramo di un altro repository: {con!r}"
        assert "altro@main" in barra("s2", altro), "RL07 senza scheda la barra non mostra repository e ramo"


def test_rl08(repo: Path) -> None:
    node = shutil.which("node")
    assert node, "RL08 serve node per provare statusline.js"
    with tempfile.TemporaryDirectory() as d:
        home = Path(d) / "home"
        config = home / ".claude"
        (config / "cache" / "scheda").mkdir(parents=True)
        progetto = Path(d) / "Due Mondi"
        for cartella in (config, progetto):
            subprocess.run(["git", "init", "-q", "-b", "main", str(cartella)], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(cartella), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q",
                            "--allow-empty", "-m", "x"], check=True, capture_output=True)
        copia = Path(d) / "due-mondi-wt"
        subprocess.run(["git", "-C", str(progetto), "worktree", "add", "-q", "-b", "wt", str(copia)],
                       check=True, capture_output=True)
        for sessione, nome in (("c", "claude-config"), ("p", "Due Mondi")):
            (config / "cache" / "scheda" / f"{sessione}.json").write_text(json.dumps({"progetto": nome}), encoding="utf-8")
        env = ambiente(home)

        def barra(sessione: str, cartella: Path) -> str:
            dati = {"session_id": sessione, "workspace": {"current_dir": str(cartella)}, "model": {"display_name": "Opus"}}
            r = subprocess.run([node, str(repo / "hooks" / "statusline.js")], input=json.dumps(dati), text=True,
                               encoding="utf-8", capture_output=True, env=env, timeout=30)
            return re.sub(r"\x1b\[[0-9;]*m", "", r.stdout)

        con = barra("c", config)
        assert "claude-config@main" in con, f"RL08 nella config la barra perde il ramo: {con!r}"
        con = barra("p", progetto)
        assert "Due Mondi@main" in con, f"RL08 una scheda col nome della cartella non trova il suo ramo: {con!r}"
        con = barra("p", copia)
        assert "Due Mondi@wt" in con, f"RL08 da un worktree la barra non riconosce il progetto: {con!r}"


def test_rl09(repo: Path) -> None:
    node = shutil.which("node")
    assert node, "RL09 serve node per provare context-monitor.js"
    with tempfile.TemporaryDirectory() as d:
        env = {**ambiente(Path(d) / "home"), "TMPDIR": d, "TEMP": d, "TMP": d}
        avvisi = []
        for _ in range(7):  # primo avviso, poi 5 giri di attesa, poi il secondo
            (Path(d) / "claude-ctx-s9.json").write_text(json.dumps(
                {"session_id": "s9", "remaining_percentage": 30, "used_pct": 70,
                 "timestamp": int(time.time())}), encoding="utf-8")
            r = subprocess.run([node, str(repo / "hooks" / "context-monitor.js")], input=json.dumps({"session_id": "s9"}),
                               text=True, encoding="utf-8", capture_output=True, env=env, timeout=30)
            if r.stdout.strip():
                avvisi.append(json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"])
        assert len(avvisi) == 2, f"RL09 attesi due avvisi in sette giri, arrivati {len(avvisi)}: {avvisi}"
        assert all("/fine" in a for a in avvisi) and "/clear" in avvisi[0] and "do not repeat" not in avvisi[0], \
            f"RL09 il primo avviso non propone /fine con /clear e /inizio: {avvisi[0]!r}"
        assert "do not repeat" in avvisi[1] and "propose /fine" in avvisi[1], \
            f"RL09 il secondo avviso ripropone /clear e /inizio: {avvisi[1]!r}"


TESTS = {"RL01": test_rl01, "RL02": test_rl02, "RL03": test_rl03, "RL04": test_rl04, "RL05": test_rl05,
         "RL06": test_rl06, "RL07": test_rl07, "RL08": test_rl08, "RL09": test_rl09}


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
