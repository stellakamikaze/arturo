#!/usr/bin/env python3
"""HI01-HI06: il campo `if` sugli hook che non c'entrano col comando (22/11/2026, #6327).

Il campo `if` di un hook (code.claude.com/docs/en/hooks, "Common fields") evita di far partire il processo
quando la regola non corrisponde. Misura su eventi tipici, casa finta: `block-dangerous.py dopo` costa 77 ms a
ogni Bash, `gws-esito.py` 36-49 ms su PreToolUse, PostToolUse e PostToolUseFailure. Tutti e due escono subito
se il comando non contiene la loro parola ("commit", "gws"): con `if` il processo non parte.

La sonda dal vivo su Claude Code 2.1.330 (claude -p, hook di prova) ha deciso la forma delle regole:
`Bash(git *)` non scatta su `env git status` e su `bash -c 'git commit'`; `Bash(*commit*)` e `Bash(*gws*)`
scattano su ogni sottocomando che contiene la parola, anche dentro `$()` e dopo `command`. Le regole su Edit
non scattano su Write: per questo typecheck-after-edit resta senza `if` (servirebbero dieci voci).

HI01 ogni `if` sta su un evento di tool: su SessionStart, Stop e gli altri un hook con `if` non parte mai.
HI02 gws-esito (le tre voci) ha `Bash(*gws*)`, block-dangerous dopo ha `Bash(*commit*)`.
HI03 ogni `Bash(*parola*)` è largo almeno quanto il filtro dell'hook: il sorgente esce con `"parola" not in`.
HI04 le guardie non hanno `if`: il filtro è best-effort, e un comando che Claude Code non sa dividere deve
     passare comunque dalla guardia.
HI05 hooks/hooks.json del plugin (bin/impacchetta.py) porta gli stessi `if`.
HI06 gli hook col filtro, su un comando che la regola lascia passare senza la parola (`echo $(date)`), tacciono.

Dal 23/11/2026 (#6492) questi hook girano dentro hooks/hub.py, e la parola della TABELLA di hub fa il lavoro
di `if`: vale come `Bash(*parola*)` sulla voce di hub del suo evento. HI02-HI05 leggono le due fonti.

Sulla base a1f5927 (dev prima della modifica) sono rossi HI02 e HI05.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

CASI = ["HI01", "HI02", "HI03", "HI04", "HI05", "HI06"]
DISCRIMINANTI = ["HI02", "HI05"]
EVENTI_TOOL = {"PreToolUse", "PostToolUse", "PostToolUseFailure", "PermissionRequest", "PermissionDenied"}
ATTESI = {
    ("PreToolUse", "hooks/gws-esito.py"): "Bash(*gws*)",
    ("PostToolUse", "hooks/gws-esito.py"): "Bash(*gws*)",
    ("PostToolUseFailure", "hooks/gws-esito.py"): "Bash(*gws*)",
    ("PostToolUse", "hooks/block-dangerous.py dopo"): "Bash(*commit*)",
}
GUARDIE = ("bash-dispatcher.sh", "dispatcher.py", "protect_claude_md.py", "web-egress-guard.py", "credential-leak-scanner.py",
           "prompt-injection-scanner.py", "memory-write-scanner.py", "agente-worktree.py")


def _voci(hooks: dict):
    for evento, gruppi in hooks.items():
        for gruppo in gruppi:
            for hook in gruppo.get("hooks", []):
                yield evento, hook


def _chiave(comando: str) -> str:
    # Nel plugin il percorso sta fra virgolette: `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/x.py" dopo`.
    m = re.search(r"(hooks/[^\s\"']+)[\"']?( dopo)?", comando)
    return (m.group(1) + (m.group(2) or "")) if m else comando


VOCI_HUB = {"pre": "PreToolUse", "post": "PostToolUse", "postfail": "PostToolUseFailure", "prompt": "UserPromptSubmit"}


def _con_if(hooks: dict) -> dict:
    return {(evento, _chiave(h.get("command", ""))): h["if"] for evento, h in _voci(hooks) if "if" in h}


def _tabella_hub(repo: Path) -> list:
    """Le righe di hooks/hub.py come (evento, chiave, parola), solo per le voci cablate in `hooks`."""
    f = repo / "hooks" / "hub.py"
    if not f.is_file():
        return []
    spec = importlib.util.spec_from_file_location("hub_hi", f)
    hub = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(repo / "hooks"))
    try:
        spec.loader.exec_module(hub)
    finally:
        sys.path.remove(str(repo / "hooks"))
    return [(VOCI_HUB[voce], file + (" " + " ".join(argomenti) if argomenti else ""), parola)
            for voce, righe in hub.TABELLA.items() for _m, parola, file, argomenti, _t, _c in righe]


def _cablate(hooks: dict) -> set:
    """Gli eventi dove una voce lancia hooks/hub.py <voce>."""
    fuori = set()
    for evento, h in _voci(hooks):
        m = re.search(r"hooks/hub\.py[\"']? (pre|post|postfail|prompt)\b", h.get("command", ""))
        if m and VOCI_HUB[m.group(1)] == evento:
            fuori.add(evento)
    return fuori


def _con_filtro(repo: Path, hooks: dict) -> dict:
    """`if` di settings più la parola delle righe di hub sugli eventi dove hub è cablato."""
    tutti = _con_if(hooks)
    cablate = _cablate(hooks)
    for evento, chiave, parola in _tabella_hub(repo):
        if parola and evento in cablate:
            tutti.setdefault((evento, chiave), f"Bash(*{parola}*)")
    return tutti


def prova(repo: Path) -> list[str]:
    rossi = []
    hooks = json.loads((repo / "settings.json").read_text(encoding="utf-8")).get("hooks", {})
    con_if = _con_filtro(repo, hooks)

    fuori = [f"{e} {k}" for (e, k) in con_if if e not in EVENTI_TOOL]
    if fuori:
        rossi.append(f"HI01 if su un evento che non è di tool, l'hook non parte mai: {fuori}")

    sbagli = [f"{k[0]} {k[1]}: atteso {v}, trovato {con_if.get(k)}" for k, v in ATTESI.items() if con_if.get(k) != v]
    if sbagli:
        rossi.append("HI02 " + "; ".join(sbagli))

    stretti = []
    for (evento, chiave), regola in con_if.items():
        # "a|b" è la parola di hub con più fonti (#5601): una delle due basta.
        m = re.fullmatch(r"Bash\(\*([A-Za-z0-9_-]+(?:\|[A-Za-z0-9_-]+)*)\*\)", regola)
        sorgente = repo / chiave.split()[0]
        if not m or not sorgente.is_file():
            stretti.append(f"{evento} {chiave}: regola {regola} non della forma Bash(*parola*) o hook mancante")
            continue
        testo = sorgente.read_text(encoding="utf-8")
        parole = m.group(1).split("|")
        if len(parole) == 1 and f'"{parole[0]}" not in' not in testo:
            stretti.append(f"{evento} {chiave}: il sorgente non esce con \"{parole[0]}\" not in")
        elif len(parole) > 1 and ("not any(p in command for p in " not in testo
                                  or any(f'"{p}"' not in testo for p in parole)):
            # Con più parole il sorgente esce con `not any(p in command for p in NOMI)` e ha ogni nome;
            # l'allineamento esatto dei nomi lo prova IB06 di test_injection_scanner.py.
            stretti.append(f"{evento} {chiave}: il sorgente non esce senza una di {parole}")
    if stretti:
        rossi.append("HI03 " + "; ".join(stretti))

    guardie = [f"{e} {h.get('command')}" for e, h in _voci(hooks) if "if" in h
               and (any(g in h.get("command", "") for g in GUARDIE)
                    or ("block-dangerous.py" in h.get("command", "") and " dopo" not in h.get("command", "")))]
    # Lo scanner delle injection su Bash (#5601) avvisa sull'output di una fonte esterna, non ferma il comando:
    # la parola di hub è il suo stesso prefiltro, e su WebFetch e MCP non vale (IB05).
    guardie += [f"{e} {k} (hub, parola {p})" for e, k, p in _tabella_hub(repo) if p
                and k != "hooks/prompt-injection-scanner.py"
                and (any(g in k for g in GUARDIE) or (k == "hooks/block-dangerous.py"))]
    if guardie:
        rossi.append(f"HI04 guardie con if, best-effort: {guardie}")

    spec = importlib.util.spec_from_file_location("impacchetta_hi", repo / "bin" / "impacchetta.py")
    modulo = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(repo / "bin"))
    try:
        spec.loader.exec_module(modulo)
        plugin = _con_filtro(repo, modulo.hooks_json({"hooks": hooks})["hooks"])
    finally:
        sys.path.remove(str(repo / "bin"))
    mancano = [f"{k[0]} {k[1]}" for k, v in ATTESI.items() if plugin.get(k) != v]
    if mancano:
        rossi.append(f"HI05 hooks.json del plugin senza il campo if: {mancano}")

    rumorosi = []
    env = dict(os.environ, ARTURO_TELEMETRIA="0", PYTHONDONTWRITEBYTECODE="1")
    for evento, script, argomenti in (("PreToolUse", "gws-esito.py", []), ("PostToolUse", "gws-esito.py", []),
                                      ("PostToolUse", "block-dangerous.py", ["dopo"])):
        dati = {"session_id": "hi06", "hook_event_name": evento, "tool_name": "Bash", "cwd": str(repo),
                "tool_input": {"command": "echo $(date)"}, "tool_response": {"stdout": "x", "stderr": ""}}
        p = subprocess.run([sys.executable, str(repo / "hooks" / script), *argomenti], input=json.dumps(dati),
                           capture_output=True, text=True, timeout=30, env=env)
        if p.returncode != 0 or p.stdout.strip():
            rumorosi.append(f"{evento} {script}: rc={p.returncode} stdout={p.stdout.strip()[:80]!r}")
    if rumorosi:
        rossi.append("HI06 " + "; ".join(rumorosi))
    return sorted(rossi)


def main() -> int:
    for flusso in (sys.stdout, sys.stderr):
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    a = parser.parse_args()
    rossi = prova(Path(a.repo).resolve())
    if a.baseline_ref:
        codici = [r.split()[0] for r in rossi]
        assert codici == DISCRIMINANTI, f"baseline non discriminante: rossi {codici}, attesi {DISCRIMINANTI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    print(f"campo if sugli hook: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
