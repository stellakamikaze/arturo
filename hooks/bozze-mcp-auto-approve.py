#!/usr/bin/env python3
"""PreToolUse (mcp__.*draft.*): una BOZZA creata via MCP non chiede conferma, un invio si'.

L'ask di settings.json `mcp__*__*send*` ferma anche `slack_send_message_draft`, che
crea solo una bozza: il flusso draft-first vuole che la bozza non chieda mai, perché
è il passo in cui la persona legge il testo prima di decidere. Questo hook approva
gli strumenti MCP di qualunque collegamento che preparano una bozza (`create_draft`,
`*_draft`, `update_draft`) e tace su tutto il resto: l'invio di una bozza
(`send_draft`, `drafts_send`), la pubblicazione, la cancellazione e l'inoltro restano
soggetti alle regole di settings.json.

Fail-open: un input che non si legge non riceve nessuna decisione.
"""
import json
import re
import sys

# Lo strumento deve FINIRE con draft/drafts: la bozza è il risultato. La parola
# subito prima dice cosa fa: `create_draft`, `update_draft`, `slack_send_message_draft`
# preparano; `send_draft`, `publish_draft`, `delete_draft` agiscono. Un nome che non
# finisce con draft (`create_draft_and_send`, `drafts_send`) non riceve l'allow.
_FINALE = re.compile(r"(?:^|[_-])([a-z0-9]+)[_-](?:(?:all|the|my)[_-])?drafts?$")
_AGISCE = frozenset("send publish schedule delete trash remove share forward reply post submit dispatch".split())


def e_bozza(nome_tool: str) -> bool:
    if not nome_tool.startswith("mcp__"):
        return False
    strumento = nome_tool.split("__", 2)[-1].lower()
    m = _FINALE.search(strumento)
    return bool(m) and m.group(1) not in _AGISCE


def main() -> int:
    try:
        dati = json.load(sys.stdin)
    except Exception:
        return 0
    nome = dati.get("tool_name") or ""
    if isinstance(nome, str) and e_bozza(nome):
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": "Bozza via MCP (nessun invio): approvata senza conferma.",
        }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
