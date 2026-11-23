"""Chi lancia un hook e su quali strumenti: settings.json e la TABELLA di hooks/hub.py (#6492, 23/11/2026).

Dal 23/11/2026 settings.json lancia hooks/hub.py una volta per evento, e hub lancia nel suo processo gli hook
della sua TABELLA. Un banco che cerca il matcher di un hook in settings.json non lo trova più: lo chiede qui.
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

EVENTI = {"pre": "PreToolUse", "post": "PostToolUse", "postfail": "PostToolUseFailure"}
_VOCE_HUB = re.compile(r"hooks/hub\.py[\"']? (pre|post|postfail)\b")


def tabella(repo: Path) -> dict:
    """La TABELLA di hooks/hub.py del repo, {} senza hub."""
    percorso = repo / "hooks" / "hub.py"
    if not percorso.is_file():
        return {}
    spec = importlib.util.spec_from_file_location(f"hub_{abs(hash(str(repo)))}", percorso)
    modulo = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(repo / "hooks"))
    try:
        spec.loader.exec_module(modulo)
    finally:
        sys.path.remove(str(repo / "hooks"))
    return modulo.TABELLA


def _copre(gruppo: str, strumento: str) -> bool:
    return gruppo in ("", "*") or re.fullmatch(gruppo, strumento) is not None


def voci(repo: Path, evento: str, nome: str) -> list[tuple[str, dict]]:
    """Le coppie (matcher, voce di settings.json) con cui l'hook `nome` (es. "block-dangerous.py") parte su
    `evento` (es. "PreToolUse").

    Una voce di settings.json che nomina l'hook dà il suo matcher. Una riga della TABELLA di hub dà il suo
    matcher, ristretto agli strumenti che la voce di hub per quell'evento copre, e la voce di hub (timeout,
    onFailure).
    """
    s = json.loads((repo / "settings.json").read_text(encoding="utf-8")).get("hooks", {})
    trovati, gruppi_hub = [], {}
    for gruppo in s.get(evento, []):
        for h in gruppo.get("hooks", []):
            c = h.get("command", "")
            m = _VOCE_HUB.search(c)
            if m:
                gruppi_hub.setdefault(m.group(1), []).append((gruppo.get("matcher", ""), h))
            elif nome in c:
                trovati.append((gruppo.get("matcher", ""), h))
    for voce, righe in tabella(repo).items():
        if EVENTI.get(voce) != evento or voce not in gruppi_hub:
            continue
        for riga in righe:
            if riga[2].split("/")[-1] != nome:
                continue
            for gruppo, h in gruppi_hub[voce]:
                strumenti = [t for t in riga[0].split("|") if _copre(gruppo, t)]
                if strumenti:
                    trovati.append(("|".join(strumenti), h))
    return trovati


def matcher(repo: Path, evento: str, nome: str) -> list[str]:
    """I matcher con cui l'hook `nome` parte su `evento`: vedi voci()."""
    return [m for m, _h in voci(repo, evento, nome)]


def file_lanciati(repo: Path) -> set[str]:
    """I file (hooks/x, bin/y) che settings.json lancia, anche attraverso la TABELLA di hub."""
    testo = json.dumps(json.loads((repo / "settings.json").read_text(encoding="utf-8")).get("hooks", {}))
    file = set(re.findall(r"((?:hooks|bin)/[\w.-]+\.(?:py|sh|js))", testo))
    if _VOCE_HUB.search(testo):
        file.update(riga[2] for righe in tabella(repo).values() for riga in righe)
    return file
