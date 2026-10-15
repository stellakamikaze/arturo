#!/usr/bin/env bash
# PostToolUse (settings.json): se una guardia aveva chiesto conferma per questa chiamata e lo
# strumento è partito, la persona ha detto sì: bin/telemetria.py registra `confermata`.
# Gira a ogni chiamata di strumento, quindi senza attese esce subito, senza avviare Python.
[ -f "$HOME/.claude/session-env/telemetria-attese.json" ] || exit 0
exec python3 "$HOME/.claude/bin/telemetria.py" esito
