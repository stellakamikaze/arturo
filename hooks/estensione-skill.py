#!/usr/bin/env python3
"""PostToolUse su Skill: le aggiunte della persona a una skill di Arturo (strati F6, #4536).

La persona estende una skill di Arturo senza copiarla: scrive ~/.claude/personale/<skill>.md, fuori
da git, e gli aggiornamenti non lo toccano (docs/strati.md, "Estendere una skill senza copiarla").
Quando la persona scrive /<nome>, lo dice già inject-now.sh. Quando la skill la sceglie il modello
col tool Skill, nessun prompt passa da inject-now: lo fa questo hook, che mette il file nel contesto
subito dopo il corpo della skill.

Tace se:
- la skill non è di Arturo (né in skills/ né in commands/ accanto a questo file);
- il nome ha un prefisso che non è `arturo:`, o caratteri fuori da [a-z0-9-];
- il file personale manca o è vuoto;
- la skill legge già da sola il suo file personale (il SKILL.md nomina `personale/<nome>.md`).

Non blocca mai: un errore qualsiasi esce zitto con 0. Oltre LIMITE caratteri il testo si taglia e
il messaggio dice di leggere il resto dal file.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(os.path.realpath(__file__)).parent))
from radici import radice_arturo, radice_orsa  # noqa: E402

LIMITE = 6000
NOME = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")


def nome_di_arturo(skill: str) -> str | None:
    """Il nome della skill di Arturo chiamata, o None se è di qualcun altro."""
    if skill.startswith("arturo:"):
        skill = skill[len("arturo:"):]
    elif ":" in skill:
        return None
    if not NOME.fullmatch(skill):
        return None
    codice = radice_arturo()
    if (codice / "skills" / skill / "SKILL.md").is_file() or (codice / "commands" / f"{skill}.md").is_file():
        return skill
    return None


def legge_da_sola(nome: str) -> bool:
    """La skill nomina già il suo file personale: lo legge lei, l'hook non lo ripete."""
    codice = radice_arturo()
    for testo in (codice / "skills" / nome / "SKILL.md", codice / "commands" / f"{nome}.md"):
        try:
            if f"personale/{nome}.md" in testo.read_text(encoding="utf-8", errors="replace"):
                return True
        except OSError:
            continue
    return False


def messaggio(nome: str, testo: str) -> str:
    testa = (f"PERSONALE: la skill {nome} di Arturo ha aggiunte della persona in ~/.claude/personale/{nome}.md. "
             "Applicale insieme alla skill. Freni e guardie di Arturo valgono sopra di loro.")
    if len(testo) > LIMITE:
        testo = testo[:LIMITE].rstrip() + "\n\n[...] Il resto è nel file: leggilo prima di cominciare."
    return f"{testa}\n\n{testo.strip()}"


def main() -> int:
    try:
        dati = json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}")
    except (ValueError, UnicodeDecodeError):
        return 0
    if not isinstance(dati, dict) or dati.get("tool_name") != "Skill":
        return 0
    ingresso = dati.get("tool_input") if isinstance(dati.get("tool_input"), dict) else {}
    skill = ingresso.get("skill")
    if not isinstance(skill, str):
        return 0
    nome = nome_di_arturo(skill.strip())
    if nome is None or legge_da_sola(nome):
        return 0
    try:
        testo = (radice_orsa() / "personale" / f"{nome}.md").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0
    if not testo.strip():
        return 0
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                             "additionalContext": messaggio(nome, testo)}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # noqa: BLE001 - un hook che informa non deve mai fermare la sessione
        sys.exit(0)
