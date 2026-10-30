#!/usr/bin/env python3
"""Il controllo dell'handoff e la retention per chi tiene i task fuori da Arturo (#4291, F0 L3).

FP01 con hooks/handoff-gate.local (colonna Ticket, Chi "Federico: <categoria>", OFFLINE, archivio
     spento) un handoff della config di Federico è verde; senza il file resta rosso.
FP02 una riga con un "|" non scritto \\| ha più celle dell'intestazione: rosso col conteggio.
FP03 il commento gitleaks dentro la cella dell'ID non conta; dopo l'ultimo "|" è un avviso, non un rosso.
FP04 un'idea "→ memoria" vuole un [[slug]] che sia una nota o una nota in attesa in _in-attesa.md,
     anche con un punto nel nome; senza slug, o con uno slug che non c'è, è rossa.
FP05 la retention con --applica sposta solo ciò che il dry-run ha mostrato: senza dry-run niente, e un
     handoff spinto oltre il keep dopo il dry-run resta (RESTA).
FP06 senza CLAUDE_CODE_SESSION_ID e senza --elenco il dry-run lo dice e --applica non sposta niente.
FP07 l'indice toglie dal filone le parole dello slug, divide una cartella contenitore (hooks/index-contenitori.local)
     per il testo fra parentesi del Nome, e rende testo i link delle celle.
FP08 inventario-sessione.py oltre il suo tetto di tempo esce da solo con 124.
FP09 l'inventario elenca i Google Doc creati con gws e con un tuo script di hooks/inventario.local, senza l'id
     del modello copiato.

Sulla base 0a4f73f (il dev prima di L3) sono rossi tutti i casi.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CASI = ["FP01", "FP02", "FP03", "FP04", "FP05", "FP06", "FP07", "FP08", "FP09"]
BASH = shutil.which("bash") or "bash"
FILE = ["bin/handoff-gate.sh", "bin/handoff-retention.py", "bin/index-rigenera.py", "bin/todo_store.py",
        "bin/handoff_profilo.py", "hooks/melchior_match.py",
        "bin/inventario-sessione.py"]
PROFILO = ("# il profilo della config di Federico\n"
           "colonna-id = Ticket\n"
           "chi = Claude|Federico: (segreto|OTP/2FA|consenso OAuth|pagamento|invio a terzi|direzione|persone|gesto fisico)\n"
           "offline = sì\n"
           "archivio = no\n")
TESTA = ("| # | Ticket | Progetto | Priorità | Task | Status | Descrizione | Chi |\n"
         "|---|--------|----------|----------|------|--------|-------------|-----|\n")


def handoff(righe: str, idee: str = "- Nessuna idea nuova.\n") -> str:
    return ("# Session Handoff - 2026-10-30 20:00\n## Progetto\n- Nome: libro / Branch: main / Status: in progress\n\n"
            f"## Task Pendenti\n{TESTA}{righe}\n## Idee\n{idee}")


class Banco:
    def __init__(self, repo: Path, ref: str | None, tmp: Path):
        self.radice = tmp / "repo"
        for rel in FILE:
            if ref:
                p = subprocess.run(["git", "-C", str(repo), "show", f"{ref}:{rel}"], capture_output=True)
                if p.returncode:
                    continue  # un file nuovo di L3 non c'è nella base
                dati = p.stdout
            else:
                dati = (repo / rel).read_bytes()
            (self.radice / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.radice / rel).write_bytes(dati)
        self.home = tmp / "home"
        self.memoria = self.home / ".claude" / "data" / "memory"
        self.memoria.mkdir(parents=True)
        self.handoffs = tmp / "handoffs"
        self.temp = tmp / "temp"
        self.temp.mkdir()
        self.n = 0
        self.tmp = tmp

    def profilo(self, acceso: bool) -> None:
        f = self.radice / "hooks" / "handoff-gate.local"
        if acceso:
            f.write_text(PROFILO, encoding="utf-8")
        elif f.exists():
            f.unlink()

    def env(self, sessione: str | None = "prova-fp") -> dict:
        e = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home), ARTURO_TODO=str(self.tmp / "eventi.jsonl"),
                 TMPDIR=str(self.temp), TEMP=str(self.temp), TMP=str(self.temp), PYTHONDONTWRITEBYTECODE="1")
        e.pop("CLAUDE_CODE_SESSION_ID", None)
        if sessione:
            e["CLAUDE_CODE_SESSION_ID"] = sessione
        return e

    def gate(self, testo: str) -> subprocess.CompletedProcess:
        self.n += 1
        f = self.tmp / f"HANDOFF_{self.n}.md"
        f.write_text(testo, encoding="utf-8")
        return subprocess.run([BASH, str(self.radice / "bin" / "handoff-gate.sh"), str(f)], capture_output=True,
                              text=True, encoding="utf-8", errors="replace", env=self.env(), timeout=60)

    def retention(self, *argomenti: str, sessione: str | None = "prova-fp") -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-B", str(self.radice / "bin" / "handoff-retention.py"), "libro",
                               "--radice", str(self.handoffs), *argomenti], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", env=self.env(sessione), timeout=60)

    def handoff_libro(self, data: str) -> None:
        f = self.handoffs / "libro" / f"HANDOFF_{data}.md"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(handoff("Nessun task pendente.\n").replace(TESTA, ""), encoding="utf-8")

    def presenti(self) -> list:
        return sorted(p.name for p in (self.handoffs / "libro").glob("HANDOFF_*.md"))


def verde(r: subprocess.CompletedProcess) -> bool:
    return r.returncode == 0 and "GATE HANDOFF: verde" in r.stdout


def prova(b: Banco) -> list:
    rossi = []
    buone = ("| 1 | #4043 | libro | media | Rispondere a Gigi | pending | La bozza è nel thread | Federico: invio a terzi |\n"
             "| 2 | OFFLINE | libro | alta | Rileggere il capitolo | pending | Servono le note | Claude |\n")

    # FP01
    b.profilo(True)
    r1 = b.gate(handoff(buone))
    b.profilo(False)
    r2 = b.gate(handoff(buone))
    if not verde(r1) or verde(r2):
        rossi.append(f"FP01 profilo: con .local rc={r1.returncode} {r1.stdout.strip()[:200]!r}, senza rc={r2.returncode}")

    b.profilo(True)
    # FP02
    r = b.gate(handoff(buone + "| 3 | #12 | libro | bassa | Scegliere fra a | b | pending | d | Claude |\n"))
    r_ok = b.gate(handoff(buone + "| 3 | #12 | libro | bassa | Scegliere fra a \\| b | pending | d | Claude |\n"))
    if r.returncode != 1 or "9 celle invece di 8" not in r.stdout or not verde(r_ok):
        rossi.append(f"FP02 celle: rc={r.returncode} {r.stdout.strip()[:200]!r}, con \\| rc={r_ok.returncode}")

    # FP03
    dentro = "| 3 | #12 <!-- gitleaks:allow (Google Doc ID) --> | libro | bassa | Leggere il doc | pending | d | Claude |\n"
    dopo = "| 3 | #12 | libro | bassa | Leggere il doc | pending | d | Claude | <!-- gitleaks:allow (Google Doc ID) -->\n"
    r1, r2 = b.gate(handoff(buone + dentro)), b.gate(handoff(buone + dopo))
    if not verde(r1) or not verde(r2) or "GATE HANDOFF: avviso:" not in r2.stdout:
        rossi.append(f"FP03 gitleaks: in cella rc={r1.returncode} {r1.stdout.strip()[:160]!r}, "
                     f"dopo rc={r2.returncode} {r2.stdout.strip()[:160]!r}")

    # FP04
    (b.memoria / "pattern").mkdir()
    (b.memoria / "pattern" / "nota-vera.md").write_text("---\nname: nota-vera\n---\n", encoding="utf-8")
    (b.memoria / "_in-attesa.md").write_text("# In attesa\n\n## pattern/nota.attesa.md · 2026-10-30 · libro\n"
                                              "---\nname: nota.attesa\n---\n", encoding="utf-8")
    buone_idee = "- Una regola → memoria [[nota-vera]]\n- Un'altra → memoria [[nota.attesa]]\n- Una terza → #12\n"
    ok = b.gate(handoff(buone, buone_idee))
    senza = b.gate(handoff(buone, "- Una regola → memoria\n"))
    finta = b.gate(handoff(buone, "- Una regola → memoria [[nota-finta]]\n"))
    punto = b.gate(handoff(buone, "- Una regola → memoria [[notaXattesa]]\n"))  # il punto non è un jolly
    if not verde(ok) or senza.returncode != 1 or "senza [[slug]]" not in senza.stdout \
            or finta.returncode != 1 or "[[nota-finta]]" not in finta.stdout or punto.returncode != 1:
        rossi.append(f"FP04 idee: buone rc={ok.returncode} {ok.stdout.strip()[:160]!r}, senza rc={senza.returncode}, "
                     f"finta rc={finta.returncode}, punto rc={punto.returncode}")

    # FP05
    for g in range(1, 7):
        b.handoff_libro(f"2026-10-0{g}_10-00")
    a = b.retention("--applica")
    dopo_a = b.presenti()
    d = b.retention()
    b.handoff_libro("2026-10-07_10-00")  # un'altra sessione chiude dopo il dry-run
    a2 = b.retention("--applica")
    dopo_a2 = b.presenti()
    atteso = [f"HANDOFF_2026-10-0{g}_10-00.md" for g in range(2, 8)]
    if len(dopo_a) != 6 or "AVVISO" not in a.stdout or d.returncode != 0 or dopo_a2 != atteso \
            or "RESTA libro/HANDOFF_2026-10-02_10-00.md" not in a2.stdout:
        rossi.append(f"FP05 elenco: senza dry-run restano {len(dopo_a)}, dopo applica {dopo_a2}, "
                     f"uscita {a2.stdout.strip()[-200:]!r}")

    # FP06
    prima = b.presenti()
    d = b.retention(sessione=None)
    a = b.retention("--applica", sessione=None)
    if "CLAUDE_CODE_SESSION_ID" not in d.stderr + d.stdout or b.presenti() != prima:
        rossi.append(f"FP06 senza sessione: dry-run {d.stderr.strip()[:160]!r}, presenti {b.presenti()}, "
                     f"applica {a.stdout.strip()[-160:]!r}")

    # FP07 indice: filone senza le parole dello slug, cartella contenitore dal .local, link resi testo
    radice = b.tmp / "indice"
    for rel, testo in {
            "libro/HANDOFF_2026-10-10_10-00.md": "## Progetto\n- Nome: libro\n- Filone: libro copertina\n\n"
                                                 "## Ripartenza\nTesto.\nProssimo passo: leggere [la bozza](docs/bozza.md)\n",
            "libro/HANDOFF_2026-10-11_10-00.md": "## Progetto\n- Nome: libro\n- Filone: copertina\n\n"
                                                 "## Ripartenza\nTesto.\nProssimo passo: PASSO-COPERTINA\n",
            "casa/HANDOFF_2026-10-12_10-00.md": "## Progetto\n- Nome: casa (caldaia nuova)\n\n"
                                                "## Ripartenza\nTesto.\nProssimo passo: PASSO-CALDAIA\n",
            "casa/HANDOFF_2026-10-13_10-00.md": "## Progetto\n- Nome: casa (giardino)\n\n"
                                                "## Ripartenza\nTesto.\nProssimo passo: PASSO-GIARDINO\n"}.items():
        (radice / rel).parent.mkdir(parents=True, exist_ok=True)
        (radice / rel).write_text(testo, encoding="utf-8")
    (b.radice / "hooks" / "index-contenitori.local").write_text("# cartelle con filoni scollegati\ncasa\n", encoding="utf-8")
    uscita = b.tmp / "INDEX.md"
    r = subprocess.run([sys.executable, "-B", str(b.radice / "bin" / "index-rigenera.py"), "--out", str(uscita),
                        "--radice", str(radice), "--oggi", "2026-10-20"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=b.env(), timeout=60)
    indice = uscita.read_text(encoding="utf-8") if uscita.exists() else ""
    righe_libro = [x for x in indice.splitlines() if x.startswith("| libro")]
    if r.returncode != 0 or len(righe_libro) != 1 or "PASSO-CALDAIA" not in indice or "PASSO-GIARDINO" not in indice \
            or "](docs/bozza.md)" in indice:
        rossi.append(f"FP07 indice: rc={r.returncode} {r.stderr.strip()[-160:]!r}, righe libro {len(righe_libro)}")

    # FP08 l'inventario si ferma da solo oltre il suo tetto, con 124
    progetti = b.tmp / "progetti" / "p"
    progetti.mkdir(parents=True)
    with open(progetti / "s1.jsonl", "w", encoding="utf-8") as f:
        riga = '{"type": "user", "message": {"content": "' + "x" * 50 + '"}, "timestamp": "2026-10-30T10:00:00Z"}\n'
        f.write(riga * 200000)
    r = subprocess.run([sys.executable, "-B", str(b.radice / "bin" / "inventario-sessione.py"), "--session", "s1",
                        "--projects", str(b.tmp / "progetti")], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env={**b.env(), "INVENTARIO_TIMEOUT": "0.2"}, timeout=120)
    if r.returncode != 124:
        rossi.append(f"FP08 tetto dell'inventario: rc={r.returncode} {r.stderr.strip()[-120:]!r}")

    # FP09 l'inventario vede gli oggetti creati con gws e con uno script elencato in hooks/inventario.local
    modello = "1" + "M" * 32
    nuovo_gws, nuovo_mio = "1" + "G" * 32, "1" + "L" * 32
    (b.radice / "hooks" / "inventario.local").write_text("# i miei script\nGoogle Doc = duplica_modello[.]py\n",
                                                         encoding="utf-8")
    eventi = []
    for n, (cmd, ris) in enumerate((
            ("gws docs documents create --json '{\"title\": \"Nota\"}'", '{"documentId": "' + nuovo_gws + '"}'),
            (f"python3 duplica_modello.py {modello}", f"Creato: https://docs.google.com/document/d/{nuovo_mio}/edit"))):
        eventi.append({"type": "assistant", "timestamp": "2026-10-30T10:00:0%dZ" % n, "cwd": str(b.tmp),
                       "message": {"content": [{"type": "tool_use", "id": f"t{n}", "name": "Bash",
                                                "input": {"command": cmd}}]}})
        eventi.append({"type": "user", "timestamp": "2026-10-30T10:00:0%dZ" % n, "cwd": str(b.tmp),
                       "message": {"content": [{"type": "tool_result", "tool_use_id": f"t{n}", "content": ris}]}})
    (progetti / "s2.jsonl").write_text("".join(json.dumps(e) + "\n" for e in eventi), encoding="utf-8")
    r = subprocess.run([sys.executable, "-B", str(b.radice / "bin" / "inventario-sessione.py"), "--session", "s2",
                        "--projects", str(b.tmp / "progetti"), "--json", "--home", str(b.home)], capture_output=True,
                       text=True, encoding="utf-8", errors="replace", env=b.env(), timeout=120)
    try:
        online = {o.get("id"): o.get("tipo") for o in json.loads(r.stdout).get("online", [])}
    except ValueError:
        online = {}
    if online.get(nuovo_gws) != "Google Doc" or online.get(nuovo_mio) != "Google Doc" or modello in online:
        rossi.append(f"FP09 oggetti online: rc={r.returncode} {online} {r.stderr.strip()[-120:]!r}")
    return rossi


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    argomenti = parser.parse_args()
    repo = Path(argomenti.repo)
    with tempfile.TemporaryDirectory(prefix="arturo-fp-") as tmp:
        rossi = prova(Banco(repo, argomenti.baseline_ref, Path(tmp)))
    if argomenti.baseline_ref:
        codici = [r.split()[0] for r in rossi]
        assert codici == CASI, f"baseline non discriminante: rossi {codici}, attesi {CASI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    print(f"profilo e retention di /fine: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
