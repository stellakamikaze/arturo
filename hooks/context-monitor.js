#!/usr/bin/env node
// Context Monitor, guscio (#6492, B5, 23/11/2026).
// La logica sta in context-monitor.py, che in settings.json gira dentro `hooks/hub.py post` senza un processo
// node a ogni Bash, Edit e Write. Questo file resta per le config che chiamano ancora
// `node ~/.claude/hooks/context-monitor.js`: passa l'evento a Python e ne copia l'uscita.
// Soglie, attesa fra due avvisi e testi: vedi context-monitor.py.

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const pezzi = [];
// Se stdin non si chiude entro 10 s (pipe di Windows o Git Bash), esce in silenzio (#775, #1162).
const stdinTimeout = setTimeout(() => process.exit(0), 10000);
process.stdin.on('data', chunk => pezzi.push(chunk));
process.stdin.on('end', () => {
  clearTimeout(stdinTimeout);
  const script = path.join(__dirname, 'context-monitor.py');
  if (!fs.existsSync(script)) process.exit(0);
  const interpreti = process.platform === 'win32' ? ['python', 'py', 'python3'] : ['python3', 'python'];
  for (const exe of interpreti) {
    const r = spawnSync(exe, [script], { input: Buffer.concat(pezzi), timeout: 8000 });
    if (r.error) continue;
    if (r.stdout && r.stdout.length) process.stdout.write(r.stdout);
    break;
  }
  process.exit(0);  // mai fermare uno strumento
});
