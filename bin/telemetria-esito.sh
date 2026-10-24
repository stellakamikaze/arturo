#!/usr/bin/env bash
# PostToolUse e PostToolUseFailure (settings.json): se una guardia aveva chiesto conferma per questa
# chiamata e lo strumento è partito, la persona ha detto sì: bin/telemetria.py registra `confermata`.
# Dal 24/10/2026 anche su Monitor e dopo uno strumento fallito: Claude Code lancia PostToolUseFailure
# solo quando la chiamata, già permessa, va in errore (un no alla conferma non lo lancia), e il suo
# stdin ha lo stesso tool_use_id. Il resto dello stdin (error, is_interrupt) non si legge.
# Gira a ogni chiamata di strumento, quindi senza attese esce subito, senza avviare Python.
[ -f "$HOME/.claude/session-env/telemetria-attese.json" ] || exit 0
exec python3 "$HOME/.claude/bin/telemetria.py" esito
