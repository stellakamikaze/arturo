#!/usr/bin/env python3
"""Il banco di scelta di una skill di ruolo (strati F6, #4536, docs/strati.md).

Una skill di ruolo serve solo se la sessione la chiama quando tocca, anche senza che la persona la
nomini. Questo banco lo misura sul modello vero: per ogni richiesta di tests/scelta-skill/<skill>.json
apre una sessione `claude -p` e guarda quali skill chiama. Una prova è giusta se la skill viene
chiamata quando `atteso` è true, e non viene chiamata quando è false. La soglia è 9 su 10.

Ogni richiesta gira --giri volte (di serie 3), e conta come giusta solo se è giusta in tutti i giri
(pass^k): per chi non programma conta che la skill parta ogni volta, non una volta su tre. Un solo giro
è rumoroso: Anthropic tratta come rumore una differenza sotto i 3 punti (infrastructure-noise,
5/2/2026), e qui una richiesta vale più di 3 punti. La riga finale dice anche la media per giro, e il
JSON registra modello e versione di Claude Code, perché si confrontano solo giri fatti nelle stesse
condizioni (#6332, 21/11/2026).

La sessione di prova:
- carica Arturo come plugin dalla cartella --plugin (di serie: il pacchetto di questo repository,
  fatto con bin/impacchetta.py in una cartella temporanea), con i suoi hook di avvio e la riga RUOLI;
- non carica le impostazioni dell'utente (--setting-sources project,local), quindi né il plugin
  installato né gli hook della config;
- ha solo il tool Skill, nessun server MCP, nessuna trascrizione salvata, al massimo --turni turni;
- gira in una cartella vuota, con la telemetria spenta.

Costa una sessione per richiesta, a carico dell'abbonamento della persona: non sta nel gate, si lancia
prima di rilasciare una skill di ruolo. Il risultato va in --uscita (JSON), con il conto per prova.

  python3 tests/scelta_skill.py --skill monitor [--modello opus] [--lavori 3] [--giri 3] [--uscita file.json]
  python3 tests/scelta_skill.py --skill monitor --solo 1,21     prova solo quelle (numeri da 1)
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional

RADICE = Path(__file__).resolve().parents[1]
SOGLIA = 0.9
SOLO_AVVIO = ("prompt-master", "arturo:prompt-master")


def nomi_della_skill(skill: str) -> set:
    return {skill, f"arturo:{skill}"}


def impacchetta(cartella: Path) -> Path:
    uscita = cartella / "arturo"
    r = subprocess.run([sys.executable, str(RADICE / "bin" / "impacchetta.py"), "--uscita", str(uscita)],
                       capture_output=True, text=True, encoding="utf-8", timeout=300)
    if r.returncode != 0:
        raise SystemExit(f"impacchetta.py esce {r.returncode}: {r.stdout[-400:]} {r.stderr[-400:]}")
    return uscita


def skill_chiamate(righe: str) -> List[str]:
    """I nomi delle skill chiamate col tool Skill, in ordine, dallo stream-json di claude -p."""
    chiamate = []
    for riga in righe.splitlines():
        try:
            evento = json.loads(riga)
        except ValueError:
            continue
        if evento.get("type") != "assistant":
            continue
        for parte in (evento.get("message") or {}).get("content") or []:
            if isinstance(parte, dict) and parte.get("type") == "tool_use" and parte.get("name") == "Skill":
                nome = (parte.get("input") or {}).get("skill")
                if isinstance(nome, str):
                    chiamate.append(nome.strip().lstrip("/"))
    return chiamate


def skill_caricate(righe: str) -> Optional[List[str]]:
    for riga in righe.splitlines():
        try:
            evento = json.loads(riga)
        except ValueError:
            continue
        if evento.get("type") == "system" and evento.get("subtype") == "init":
            return list(evento.get("skills") or []) + list(evento.get("slash_commands") or [])
    return None


def prova(n: int, voce: Dict, plugin: Path, modello: Optional[str], turni: int, skill: str) -> Dict:
    cartella = Path(tempfile.mkdtemp(prefix="arturo-scelta."))
    comando = ["claude", "-p", voce["prompt"], "--output-format", "stream-json", "--verbose",
               "--tools", "Skill", "--strict-mcp-config", "--no-session-persistence",
               "--max-turns", str(turni), "--setting-sources", "project,local", "--plugin-dir", str(plugin)]
    if modello:
        comando += ["--model", modello]
    env = dict(os.environ, ARTURO_TELEMETRIA="0", ARTURO_AGGIORNAMENTI="manuali")
    env.pop("CLAUDE_ENV_FILE", None)
    inizio = time.time()
    try:
        r = subprocess.run(comando, cwd=cartella, env=env, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=300)
        uscita, errore, codice = r.stdout, r.stderr, r.returncode
    except subprocess.TimeoutExpired as e:
        uscita, errore, codice = (e.stdout or b"").decode("utf-8", "replace") if isinstance(e.stdout, bytes) \
            else (e.stdout or ""), "timeout", -1
    finally:
        shutil.rmtree(cartella, ignore_errors=True)
    chiamate = skill_chiamate(uscita)
    utili = [c for c in chiamate if c not in SOLO_AVVIO]
    chiamata = bool(nomi_della_skill(skill) & set(chiamate))
    esito = {"n": n, "prompt": voce["prompt"], "atteso": voce["atteso"], "chiamate": chiamate,
             "giusta": chiamata == bool(voce["atteso"]), "secondi": round(time.time() - inizio, 1),
             "codice": codice}
    if n == 1 or codice != 0:
        caricate = skill_caricate(uscita)
        esito["skill_caricate"] = caricate
        if codice != 0:
            esito["errore"] = (errore or "")[-300:]
    esito["altre"] = [c for c in utili if c not in nomi_della_skill(skill)]
    return esito


def conta(esiti: List[Dict]) -> Dict:
    """Raccoglie i giri per richiesta: giusta solo se giusta in ogni giro (pass^k), più la media per giro."""
    per_prova: Dict[int, List[bool]] = {}
    for e in esiti:
        per_prova.setdefault(e["n"], []).append(bool(e["giusta"]))
    sempre = sorted(n for n, giri in per_prova.items() if giri and all(giri))
    instabili = sorted(n for n, giri in per_prova.items() if any(giri) and not all(giri))
    totale = len(per_prova)
    giuste_giro = sum(sum(giri) for giri in per_prova.values())
    prove_giro = sum(len(giri) for giri in per_prova.values())
    return {"per_prova": per_prova, "sempre": sempre, "instabili": instabili, "totale": totale,
            "quota": len(sempre) / totale if totale else 0.0,
            "media_giro": giuste_giro / prove_giro if prove_giro else 0.0}


def versione_claude() -> str:
    try:
        r = subprocess.run(["claude", "--version"], capture_output=True, text=True, encoding="utf-8", timeout=30)
        return r.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--skill", required=True)
    parser.add_argument("--modello")
    parser.add_argument("--lavori", type=int, default=3)
    parser.add_argument("--giri", type=int, default=3, help="giri per richiesta; giusta solo se giusta in tutti")
    parser.add_argument("--turni", type=int, default=3)
    parser.add_argument("--plugin", type=Path, help="cartella del plugin; di serie il pacchetto di questo repo")
    parser.add_argument("--solo", help="numeri delle prove, da 1, separati da virgole")
    parser.add_argument("--uscita", type=Path)
    a = parser.parse_args()
    if not shutil.which("claude"):
        print("manca il comando claude nel PATH")
        return 2
    voci = json.loads((RADICE / "tests" / "scelta-skill" / f"{a.skill}.json").read_text(encoding="utf-8"))["prove"]
    scelte = list(enumerate(voci, 1))
    if a.solo:
        numeri = {int(x) for x in a.solo.split(",") if x.strip()}
        scelte = [(n, v) for n, v in scelte if n in numeri]
    temporanea = None
    plugin = a.plugin
    if plugin is None:
        temporanea = Path(tempfile.mkdtemp(prefix="arturo-scelta-plugin."))
        plugin = impacchetta(temporanea)
    giri = max(1, a.giri)
    lavori = [(n, voce) for _ in range(giri) for n, voce in scelte]
    try:
        with ThreadPoolExecutor(max_workers=max(1, a.lavori)) as pool:
            esiti = list(pool.map(lambda c: prova(c[0], c[1], plugin, a.modello, a.turni, a.skill), lavori))
    finally:
        if temporanea:
            shutil.rmtree(temporanea, ignore_errors=True)
    esiti.sort(key=lambda e: e["n"])
    conto = conta(esiti)
    rotte = [e for e in esiti if e["codice"] != 0]
    for n, voce in scelte:
        esiti_n = [e for e in esiti if e["n"] == n]
        giuste_n = sum(e["giusta"] for e in esiti_n)
        segno = "OK " if giuste_n == len(esiti_n) else ("NO " if giuste_n == 0 else f"{giuste_n}/{len(esiti_n)}")
        chiamate = " | ".join(",".join(e["chiamate"]) or "-" for e in esiti_n)
        print(f"{segno:<4}{n:>2} atteso={'sì' if voce['atteso'] else 'no'} chiamate={chiamate}  {voce['prompt'][:70]}")
    print(f"scelta {a.skill}: {len(conto['sempre'])}/{conto['totale']} giuste in tutti i {giri} giri "
          f"({conto['quota']:.0%}), soglia {SOGLIA:.0%}; media per giro {conto['media_giro']:.0%}"
          + (f"; {len(conto['instabili'])} instabili: {','.join(map(str, conto['instabili']))}" if conto["instabili"] else "")
          + (f", {len(rotte)} sessioni uscite con errore" if rotte else ""))
    if a.uscita:
        a.uscita.write_text(json.dumps({"skill": a.skill, "modello": a.modello, "claude": versione_claude(),
                                        "giri": giri, "giuste": len(conto["sempre"]), "totale": conto["totale"],
                                        "media_giro": conto["media_giro"], "instabili": conto["instabili"],
                                        "esiti": esiti}, ensure_ascii=False, indent=2),
                            encoding="utf-8")
    if rotte:
        return 2
    return 0 if conto["quota"] >= SOGLIA else 1


if __name__ == "__main__":
    sys.exit(main())
