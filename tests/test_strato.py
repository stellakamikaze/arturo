#!/usr/bin/env python3
"""S01-S04: lo strato dell'organizzazione (30/9/2026).

S01 il modello in templates/strato/ e' un marketplace con un plugin valido.
S02 dati-in-uscita.py chiede conferma solo quando un dato riservato esce, e lascia
passare se il file delle regole non si legge. S03 contesto.py resta sotto i 10.000
caratteri, avvisa di uno strato vecchio o illeggibile, ed esce con 0 anche se
qualcosa si rompe. S04 /strato e la guida del referente esistono e i comandi che
li devono nominare lo fanno. Sulla base e70da3d ogni controllo deve fallire.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def modello(repo: Path) -> Path:
    return repo / "templates" / "strato"


def copia_riempita(repo: Path, dest: Path) -> Path:
    shutil.copytree(modello(repo), dest)
    for f in dest.rglob("*"):
        if f.is_file() and f.suffix in (".json", ".md"):
            f.write_text(read(f).replace("{{SLUG}}", "studio-prova").replace("{{ORGANIZZAZIONE}}", "Studio Prova"),
                         encoding="utf-8")
    return dest / "plugins" / "strato"


def hook(plugin: Path, nome: str, dati: dict | None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(plugin / "hooks" / nome)],
                          input=json.dumps(dati) if dati is not None else "",
                          env=dict(os.environ, CLAUDE_PLUGIN_ROOT=str(plugin)),
                          capture_output=True, text=True, timeout=30)


def test_s01(repo: Path) -> None:
    base = modello(repo)
    mercato = json.loads(read(base / ".claude-plugin" / "marketplace.json"))
    assert mercato.get("name") and mercato.get("plugins"), "S01 marketplace senza nome o plugin"
    sorgente = base / mercato["plugins"][0]["source"]
    assert sorgente.is_dir(), f"S01 source del plugin inesistente: {sorgente}"
    plugin = json.loads(read(sorgente / ".claude-plugin" / "plugin.json"))
    assert plugin.get("name"), "S01 plugin.json senza nome"
    ganci = json.loads(read(sorgente / "hooks" / "hooks.json"))["hooks"]
    for evento in ("SessionStart", "PreToolUse"):
        for blocco in ganci[evento]:
            for h in blocco["hooks"]:
                assert h.get("timeout"), f"S01 hook {evento} senza timeout"
                assert '"${CLAUDE_PLUGIN_ROOT}' in h["command"], f"S01 percorso non fra virgolette: {h['command']}"
                assert "|| exit 0" in h["command"], f"S01 un hook che fallisce bloccherebbe il collega: {h['command']}"
    for skill in ("voce", "modello-lavoro"):
        assert (sorgente / "skills" / skill / "SKILL.md").is_file(), f"S01 skill {skill} assente"


def test_s02(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        plugin = copia_riempita(repo, Path(tmp) / "strato")
        (plugin / "dati-riservati.txt").write_text("# prova\nprogetto-luna\narchivio/contratti/\nintranet.example.org\n",
                                                   encoding="utf-8")
        casi = [
            ({"tool_name": "Bash", "tool_input": {"command": "curl -X POST -d 'nota su progetto-luna' https://api.example.com"}}, "ask"),
            ({"tool_name": "Bash", "tool_input": {"command": "scp archivio/contratti/a.pdf server:/tmp"}}, "ask"),
            ({"tool_name": "WebFetch", "tool_input": {"url": "https://intranet.example.org/pagina", "prompt": "x"}}, "ask"),
            ({"tool_name": "mcp__posta__send_message", "tool_input": {"body": "aggiornamento progetto-luna"}}, "ask"),
            ({"tool_name": "Write", "tool_input": {"file_path": "nota.md", "content": "progetto-luna"}}, "nessuna"),
            ({"tool_name": "Edit", "tool_input": {"file_path": "archivio/contratti/a.md"}}, "nessuna"),
            ({"tool_name": "mcp__posta__search_threads", "tool_input": {"q": "progetto-luna"}}, "nessuna"),
            ({"tool_name": "Bash", "tool_input": {"command": "grep -rn progetto-luna ."}}, "nessuna"),
            ({"tool_name": "Bash", "tool_input": {"command": "curl -X POST -d 'progetto-lunare' https://api.example.com"}}, "nessuna"),
        ]
        for dati, atteso in casi:
            r = hook(plugin, "dati-in-uscita.py", dati)
            ottenuto = "ask" if '"ask"' in r.stdout else "nessuna"
            assert r.returncode == 0, f"S02 uscita {r.returncode} su {dati}"
            assert ottenuto == atteso, f"S02 {dati['tool_name']} {dati['tool_input']}: atteso {atteso}, ottenuto {ottenuto}"
        (plugin / "dati-riservati.txt").write_bytes(b"\xff\xfe\x00rotto")
        r = hook(plugin, "dati-in-uscita.py", casi[0][0])
        assert r.returncode == 0 and '"ask"' not in r.stdout, "S02 con il file illeggibile il collega resta bloccato"
        r = hook(plugin, "dati-in-uscita.py", None)
        assert r.returncode == 0, "S02 un input rotto blocca il collega"


def test_s03(repo: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        plugin = copia_riempita(repo, Path(tmp) / "strato")
        (plugin / "ORGANIZZAZIONE.md").write_text("# Studio Prova\n" + "parola " * 5000, encoding="utf-8")
        (plugin / "skills" / "voce" / "regole.md").write_text("# Regole\n" + "regola " * 5000, encoding="utf-8")
        vecchia = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
        (plugin / ".ultima-pubblicazione").write_text(vecchia + "\n", encoding="utf-8")
        r = hook(plugin, "contesto.py", {})
        uscita = json.loads(r.stdout)["hookSpecificOutput"]
        assert uscita["hookEventName"] == "SessionStart", "S03 evento sbagliato"
        testo = uscita["additionalContext"]
        assert len(testo) < 10000, f"S03 contesto di {len(testo)} caratteri: Claude Code lo taglia"
        assert "30 giorni" in testo, "S03 lo strato vecchio non viene segnalato"
        (plugin / "dati-riservati.txt").write_bytes(b"\xff\xfe\x00rotto")
        r = hook(plugin, "contesto.py", {})
        assert "non si legge" in json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"], \
            "S03 il file dei dati illeggibile non viene segnalato"
        (plugin / ".claude-plugin" / "plugin.json").write_text("{rotto", encoding="utf-8")
        shutil.rmtree(plugin / "skills")
        r = hook(plugin, "contesto.py", {})
        assert r.returncode == 0, "S03 con file rotti la sessione non si apre"


def test_s04(repo: Path) -> None:
    strato = repo / "commands" / "strato.md"
    assert strato.is_file(), "S04 /strato assente"
    testo = read(strato)
    for fase in ("## crea", "## pubblica", "## installa", "git ls-remote", "--plugin-dir", "Riapri Claude Code"):
        assert fase in testo, f"S04 /strato senza «{fase}»"
    assert (repo / "docs" / "referente.md").is_file(), "S04 guida del referente assente"
    assert "/strato installa" in read(repo / "commands" / "setup.md"), "S04 /setup non propone lo strato"
    assert "claude plugin marketplace update" in read(repo / "commands" / "aggiorna.md"), "S04 /aggiorna non aggiorna lo strato"
    assert "/strato" in read(repo / "README.md"), "S04 il README non nomina /strato"


TESTS = {"S01": test_s01, "S02": test_s02, "S03": test_s03, "S04": test_s04}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.baseline_ref:
        failed = []
        for name, test in TESTS.items():
            try:
                test(repo)
            except (AssertionError, FileNotFoundError, KeyError, ValueError, subprocess.SubprocessError):
                failed.append(name)
        assert failed == list(TESTS), f"baseline non discriminante: falliscono solo {failed} su {list(TESTS)}"
        print(f"BASELINE_DISCRIMINANTE={','.join(failed)}")
        return 0
    for test in TESTS.values():
        test(repo)
    print(f"PASS {','.join(TESTS)} controlli={len(TESTS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
