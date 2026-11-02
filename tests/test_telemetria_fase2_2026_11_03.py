#!/usr/bin/env python3
"""Telemetria fase 2: durata, turni e skill della sessione, accesi per tutti (3/11/2026, #4540).

Federico, 2/11/2026: "voglio sapere se le persone lo stanno usando, quanto e come". La fase 1 contava le
sessioni; questa dice come sono andate. Alla chiusura hooks/session-end.sh passa il JSON dell'hook a
`telemetria.py fine`, che legge il transcript sul computer e registra solo fasce e nomi di Arturo.

TS01 l'elenco SKILL del client coincide con skills/ del repository e con SKILL di server/logica.js.
TS02 un transcript di 40 minuti con tre messaggi della persona dà durata 30m-2h, turni 2-5 e le skill
     todo (digitata con la barra), prompt-master e altro (una skill della persona): nessun testo, nessun nome
     della persona in coda. Non contano come messaggi i risultati degli strumenti, i messaggi meta, l'uscita
     di un comando locale, il messaggio di un'altra sessione e quelli dei subagent.
TS03 la stessa sessione chiusa due volte si conta una volta; una sessione senza messaggi della persona e una
     con la telemetria spenta non registrano niente; un JSON senza transcript non rompe niente.
TS04 hooks/session-end.sh fuori da un progetto lancia la telemetria della chiusura: gli eventi arrivano in coda.
TS05 la promessa cambia (8) e l'avviso della prima sessione nomina durata, messaggi e skill.

Ogni caso gira con la HOME finta di test_telemetria.py: niente parte verso il server vero.
Sulla base c5536a7 ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
import time
from pathlib import Path


def _carica(nome: str, file: str):
    spec = importlib.util.spec_from_file_location(nome, Path(__file__).with_name(file))
    assert spec and spec.loader
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


_m = _carica("banco_telemetria", "test_telemetria.py")
_copia = _carica("aggiorna_copia", "test_aggiorna_copia.py")
_sicuro = _copia._sicuro
Lab, BASH, read = _m.Lab, _m.BASH, _m.read


def coppie(lab) -> list:
    return [(e["evento"], e["valore"]) for e in lab.coda()]


def _riga(tipo: str, minuto: int, contenuto, **altro) -> str:
    ruolo = "user" if tipo == "user" else "assistant"
    d = {"type": tipo, "timestamp": f"2026-11-03T10:{minuto:02d}:00.000Z", "message": {"role": ruolo, "content": contenuto}}
    d.update(altro)
    return json.dumps(d)


def transcript(lab, nome: str = "sessione.jsonl", righe=None) -> Path:
    if righe is None:
        righe = [
            json.dumps({"type": "mode", "mode": "auto"}),
            _riga("user", 0, "<command-message>todo</command-message>\n<command-name>/todo</command-name>"),
            _riga("assistant", 1, [{"type": "tool_use", "id": "t1", "name": "Skill", "input": {"skill": "prompt-master"}}]),
            _riga("user", 1, [{"type": "tool_result", "tool_use_id": "t1", "content": "ok"}]),
            _riga("user", 2, [{"type": "text", "text": "Base directory for this skill: cliente-rossi"}], isMeta=True),
            _riga("user", 5, "prepara il preventivo per Rossi"),
            _riga("assistant", 6, [{"type": "tool_use", "id": "t2", "name": "Skill", "input": {"skill": "cliente-rossi"}}]),
            _riga("user", 7, "<local-command-stdout>fatto</local-command-stdout>"),
            _riga("user", 8, "Another Claude session sent a message: ciao"),
            _riga("user", 9, "un subagent che scrive", isSidechain=True),
            _riga("user", 30, [{"type": "text", "text": "va bene, chiudi"}, {"type": "image", "source": {}}]),
            _riga("assistant", 40, [{"type": "text", "text": "Fatto."}]),
        ]
    f = lab.dir / nome
    f.write_text("\n".join(righe) + "\n", encoding="utf-8")
    return f


def fine(lab, dati: dict) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-B", str(lab.repo / "bin" / "telemetria.py"), "fine"],
                          input=json.dumps(dati), capture_output=True, text=True, encoding="utf-8",
                          errors="replace", env=lab.env, timeout=60)


def _elenco_py(repo: Path, nome: str):
    m = re.search(nome + r" = frozenset\(\{(.*?)\}\)", read(repo / "bin" / "telemetria.py"), re.S)
    return set(re.findall(r'"([a-z0-9-]+)"', m.group(1))) if m else None


def _elenco_js(repo: Path, nome: str):
    m = re.search(r"export const " + nome + r" = \[(.*?)\];", read(repo / "server" / "logica.js"), re.S)
    return set(re.findall(r'"([a-z0-9-]+)"', m.group(1))) if m else None


def test_ts01(repo: Path) -> None:
    # Tutte le cartelle di skills/, anche quelle dei mod senza SKILL.md (apri, dafare): lo stesso elenco della deriva.
    cartelle = {p.name for p in (repo / "skills").iterdir() if p.is_dir()}
    client, server = _elenco_py(repo, "SKILL"), _elenco_js(repo, "SKILL")
    assert client == cartelle, f"TS01 SKILL di bin/telemetria.py non coincide con skills/: {client} != {sorted(cartelle)}"
    assert server == cartelle, f"TS01 SKILL di server/logica.js non coincide con skills/: {server} != {sorted(cartelle)}"


def test_ts02(repo: Path) -> None:
    lab = Lab(repo)
    fine(lab, {"session_id": "s-uno", "transcript_path": str(transcript(lab)), "reason": "exit"})
    attese = [("durata", "30m-2h"), ("turni", "2-5"), ("skill", "todo"), ("skill", "prompt-master"), ("skill", "altro")]
    assert coppie(lab) == attese, f"TS02 la chiusura non registra durata, turni e skill attesi: {coppie(lab)} != {attese}"
    testo = json.dumps(lab.coda())
    for parola in ("rossi", "preventivo", "chiudi", "s-uno", "sessione.jsonl"):
        assert parola not in testo.lower(), f"TS02 dal transcript esce {parola!r}: {testo}"


def test_ts03(repo: Path) -> None:
    lab = Lab(repo)
    dati = {"session_id": "s-due", "transcript_path": str(transcript(lab))}
    fine(lab, dati)
    fine(lab, dati)
    assert len(lab.coda()) == 5, f"TS03 la stessa sessione chiusa due volte si conta due volte: {coppie(lab)}"
    vuota = transcript(lab, "vuota.jsonl", [_riga("user", 0, "<command-name>/clear</command-name>"),
                                           _riga("assistant", 1, [{"type": "text", "text": "ok"}])])
    fine(lab, {"session_id": "s-vuota", "transcript_path": str(vuota)})
    r = fine(lab, {"session_id": "s-senza"})
    assert r.returncode == 0 and len(lab.coda()) == 5, f"TS03 una sessione senza messaggi registra qualcosa: {coppie(lab)}"
    spenta = Lab(repo, ARTURO_TELEMETRIA="0")
    fine(spenta, {"session_id": "s-tre", "transcript_path": str(transcript(spenta))})
    assert spenta.coda() == [], f"TS03 con la telemetria spenta la chiusura registra: {coppie(spenta)}"
    assert "sessioni_chiuse" in lab.stato(), "TS03 lo stato non ricorda le sessioni già contate"


def test_ts04(repo: Path) -> None:
    # Gli aggiornamenti manuali: la chiusura non lancia aggiornamenti.py nella HOME finta.
    lab = Lab(repo, ARTURO_AGGIORNAMENTI="manuali")
    dati = {"session_id": "s-hook", "transcript_path": str(transcript(lab)), "reason": "exit",
            "hook_event_name": "SessionEnd", "cwd": str(lab.dir)}
    r = lab.hook("session-end.sh", json.dumps(dati))
    fine_attesa = time.time() + 20
    while time.time() < fine_attesa and len(lab.coda()) < 5:
        time.sleep(0.2)
    assert r.returncode == 0, f"TS04 session-end.sh esce con {r.returncode}: {r.stderr}"
    assert ("turni", "2-5") in coppie(lab), f"TS04 session-end.sh non lancia la telemetria della chiusura: {coppie(lab)}"


def test_ts05(repo: Path) -> None:
    m = re.search(r"^PROMESSA = (\d+)", read(repo / "bin" / "telemetria.py"), re.M)
    assert m and int(m.group(1)) >= 8, "TS05 la promessa non cambia: l'avviso dei dati nuovi non torna a chi l'aveva letto"
    lab = Lab(repo)
    r = subprocess.run([sys.executable, "-B", str(repo / "bin" / "telemetria.py"), "avvio"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=lab.env, timeout=60)
    for parola in ("durata", "messaggi", "skill"):
        assert parola in r.stdout, f"TS05 l'avviso della prima sessione non nomina {parola}: {r.stdout}"


TESTS = {"TS01": test_ts01, "TS02": test_ts02, "TS03": test_ts03, "TS04": test_ts04, "TS05": test_ts05}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    parser.add_argument("--solo", help="codici separati da virgola")
    args = parser.parse_args()
    repo = args.repo.resolve()
    scelti = {k: v for k, v in TESTS.items() if not args.solo or k in args.solo.split(",")}
    if args.baseline_ref:
        rossi, altro = _sicuro.baseline(scelti, repo)
        assert not altro and rossi == list(scelti), \
            "baseline non discriminante: ogni controllo deve fallire col suo codice.\n" + "\n".join(altro)
        print(f"BASELINE_DISCRIMINANTE={','.join(rossi)}")
        return 0
    for test in scelti.values():
        test(repo)
    print(f"PASS {','.join(scelti)} controlli={len(scelti)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
