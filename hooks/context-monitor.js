#!/usr/bin/env node
// Claude Code Context Monitor
// Context Monitor - PostToolUse hook
// Reads context metrics from the statusline bridge file and injects
// warnings when context usage is high. This makes the AGENT aware of
// context limits (the statusline only shows the user).
//
// How it works:
// 1. The statusline hook writes metrics to /tmp/claude-ctx-{session_id}.json
// 2. This hook reads those metrics after each tool use
// 3. When remaining context drops below thresholds, it injects a warning
//    as additionalContext, which the agent sees in its conversation
//
// Thresholds:
//   WARNING  (remaining <= 50%): Agent should wrap up current task (35% until 23/11/2026: the rotation
//            moved from every closed task to half context, so the warning marks the rotation point)
//   CRITICAL (remaining <= 25%): Agent should stop immediately and save state
//
// Debounce: 5 tool uses between warnings to avoid spam
// Severity escalation bypasses debounce (WARNING -> CRITICAL fires immediately)

const fs = require('fs');
const os = require('os');
const path = require('path');

// Thresholds are env-configurable so they don't stay frozen against one model's
// context size. A fixed % misfires as windows grow (35% of 1M = 350k tokens is
// far too eager). Surfacing the metric is the legitimate part (the model can't
// perceive its own remaining context); the exact cutoff is a tunable, not a law.
// Override with CLAUDE_CTX_WARN / CLAUDE_CTX_CRIT (percent remaining).
const WARNING_THRESHOLD = Number(process.env.CLAUDE_CTX_WARN) || 50;  // remaining % to advise wrap-up
const CRITICAL_THRESHOLD = Number(process.env.CLAUDE_CTX_CRIT) || 25; // remaining % to advise stop
const STALE_SECONDS = 60;      // ignore metrics older than 60s
const DEBOUNCE_CALLS = 5;      // min tool uses between warnings

let input = '';
// Timeout guard: if stdin doesn't close within 10s (e.g. pipe issues on
// Windows/Git Bash, or slow Claude Code piping during large outputs),
// exit silently instead of hanging until Claude Code kills the process
// and reports "hook error". See #775, #1162.
const stdinTimeout = setTimeout(() => process.exit(0), 10000);
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
  clearTimeout(stdinTimeout);
  try {
    const data = JSON.parse(input);
    const sessionId = data.session_id;

    if (!sessionId) {
      process.exit(0);
    }

    // Reject session IDs that contain path traversal sequences or path separators.
    // session_id is used to construct file paths in /tmp — an unsanitized value
    // could escape the temp directory and read or write arbitrary files.
    if (/[/\\]|\.\./.test(sessionId)) {
      process.exit(0);
    }

    // A subagent carries the parent's session_id, so it would read the parent's metrics and get the
    // rotation advice meant for the main loop (and run /fine --rotazione mid-task). Its tool calls
    // carry agent_id: stay silent there, and leave the parent's debounce file untouched (review 7/11, finding 48).
    if (data.agent_id) {
      process.exit(0);
    }

    const tmpDir = os.tmpdir();
    const metricsPath = path.join(tmpDir, `claude-ctx-${sessionId}.json`);

    // If no metrics file, this is a fresh session -- exit silently
    if (!fs.existsSync(metricsPath)) {
      process.exit(0);
    }

    const metrics = JSON.parse(fs.readFileSync(metricsPath, 'utf8'));
    const now = Math.floor(Date.now() / 1000);

    // Ignore stale metrics
    if (metrics.timestamp && (now - metrics.timestamp) > STALE_SECONDS) {
      process.exit(0);
    }

    const remaining = metrics.remaining_percentage;
    const usedPct = metrics.used_pct;

    // No warning needed
    if (remaining > WARNING_THRESHOLD) {
      process.exit(0);
    }

    // Debounce: check if we warned recently
    const warnPath = path.join(tmpDir, `claude-ctx-${sessionId}-warned.json`);
    let warnData = { callsSinceWarn: 0, lastLevel: null };
    let firstWarn = true;

    if (fs.existsSync(warnPath)) {
      try {
        warnData = JSON.parse(fs.readFileSync(warnPath, 'utf8'));
        firstWarn = false;
      } catch (e) {
        // Corrupted file, reset
      }
    }

    warnData.callsSinceWarn = (warnData.callsSinceWarn || 0) + 1;

    const isCritical = remaining <= CRITICAL_THRESHOLD;
    const currentLevel = isCritical ? 'critical' : 'warning';

    // Emit immediately on first warning, then debounce subsequent ones
    // Severity escalation (WARNING -> CRITICAL) bypasses debounce
    const severityEscalated = currentLevel === 'critical' && warnData.lastLevel === 'warning';
    if (!firstWarn && warnData.callsSinceWarn < DEBOUNCE_CALLS && !severityEscalated) {
      // Update counter and exit without warning
      fs.writeFileSync(warnPath, JSON.stringify(warnData));
      process.exit(0);
    }

    // Reset debounce counter (the state file is written once, below, with rotazioneProposta)
    warnData.callsSinceWarn = 0;
    warnData.lastLevel = currentLevel;

    // Build advisory warning message (never use imperative commands that
    // override user preferences — see #884).
    // /fine is a save, and the person often keeps working in the same session after it:
    // /clear and /inizio are proposed once per session, not at every warning (#3883).
    const primaRotazione = !warnData.rotazioneProposta;
    warnData.rotazioneProposta = true;
    fs.writeFileSync(warnPath, JSON.stringify(warnData));
    // Con il mod rotazione (tool mcp__<plugin>__ruota, 3/11/2026) il giro è automatico: niente da proporre.
    // Il modello sa se il tool c'è; senza, vale il testo di sempre.
    // 19/11/2026: testo in italiano come il resto di Arturo; via l'alias mcp__rotazione__ruota, superato.
    const conRotazione = 'Se la sessione ha il tool della rotazione (mcp__arturo__ruota, o un altro nome che finisce in __ruota): ' +
      'chiudi lo step in corso, lancia /fine --rotazione, poi chiama quel tool, senza proporre niente alla persona. Altrimenti: ';
    let message;
    if (isCritical) {
      message = `CONTEXT CRITICAL: contesto usato al ${usedPct}%, restano ${remaining}%. ` + conRotazione +
        'proponi /fine alla persona adesso, prima di altro lavoro.';
    } else {
      message = `CONTEXT WARNING: contesto usato al ${usedPct}%, restano ${remaining}%. ` + conRotazione +
        'questa è la soglia della rotazione: finisci il compito in corso, poi proponi /fine ' +
        'alla persona in una riga, come salvataggio. Niente lavoro nuovo complesso. ' +
        (primaRotazione
          ? "Di' una volta che /clear e /inizio aprono una sessione pulita: la persona può continuare qui dopo /fine."
          : '/clear e /inizio sono già stati proposti in questa sessione: non ripeterli.');
    }

    const output = {
      hookSpecificOutput: {
        hookEventName: "PostToolUse",
        additionalContext: message
      }
    };

    process.stdout.write(JSON.stringify(output));
  } catch (e) {
    // Silent fail -- never block tool execution
    process.exit(0);
  }
});
