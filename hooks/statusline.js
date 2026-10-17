#!/usr/bin/env node
// Claude Code Statusline
// Shows: model | current task | project@branch* | context usage | quota

const fs = require('fs');
const path = require('path');
const os = require('os');
const child_process = require('child_process');

// --- Nome del modello -------------------------------------------------------
// "Opus 5 (1M context)" -> "Opus5·1M": meno caratteri, stessa famiglia e stessa
// finestra di contesto. Un nome non riconosciuto torna intatto.
function abbreviaModello(nome) {
  try {
    return String(nome)
      .replace(/\s*\((\d+(?:\.\d+)?[MK])\s+context\)/i, '·$1')
      .replace(/^([A-Za-z]+)\s+(\d)/, '$1$2')
      .trim() || String(nome);
  } catch (e) {
    return nome;
  }
}

// --- Segmento git -----------------------------------------------------------
// Il ramo si legge da .git/HEAD: nessun processo, nessuna attesa.
// Il flag di modifiche (*) NON si deduce dalle mtime: la mtime di .git/index si
// muove solo con `git add`, quindi un tree modificato e non staged risulterebbe
// pulito. Serve `git status`, che qui gira in un figlio staccato al massimo ogni
// 15 s e scrive una cache; la statusline legge solo la cache. Qualunque errore:
// niente flag, il ramo resta. La cache sta in cache/, che git ignora.
const CLAUDE_DIR = process.env.CLAUDE_CONFIG_DIR || path.join(os.homedir(), '.claude');
const GIT_CACHE_DIR = path.join(CLAUDE_DIR, 'cache', 'statusline');
const GIT_REFRESH_MIN_S = 15;        // frequenza minima dei tentativi
const GIT_CACHE_MAX_S = 120;         // oltre: flag nascosto, cache troppo vecchia
const GIT_SCRITTURA_MIN_S = 3;       // età minima del .tmp prima di promuoverlo

function gitRamo(gitDir) {
  try {
    const head = fs.readFileSync(path.join(gitDir, 'HEAD'), 'utf8').trim();
    const m = head.match(/^ref:\s*(.+)$/);
    return m ? m[1].replace(/^refs\/heads\//, '') : head.slice(0, 7); // staccata: sha corto
  } catch (e) {
    return '';
  }
}

function gitChiave(root) {
  return require('crypto').createHash('sha1').update(root).digest('hex').slice(0, 12);
}

function gitMtime(p) {
  try { return fs.statSync(p).mtimeMs; } catch (e) { return 0; }
}

// Promuove l'uscita di un `git status` finito e legge lo stato corrente.
// { sporco, fresca } — non solleva mai.
function gitStatoCache(root) {
  try {
    const base = path.join(GIT_CACHE_DIR, `git-${gitChiave(root)}`);
    const tmp = `${base}.tmp`;
    const mTmp = gitMtime(tmp);
    // Il .tmp diventa lo stato solo quando git ha finito di scriverci: prima si
    // leggerebbe un file troncato e ogni refresh spegnerebbe il flag per un attimo.
    if (mTmp && (Date.now() - mTmp) > GIT_SCRITTURA_MIN_S * 1000) {
      try { fs.renameSync(tmp, base); } catch (e) {}
    }
    const st = fs.statSync(base);
    const eta = Math.max(0, (Date.now() - st.mtimeMs) / 1000);
    if (eta > GIT_CACHE_MAX_S) return { sporco: false, fresca: false };
    return { sporco: st.size > 0, fresca: true };
  } catch (e) {
    return { sporco: false, fresca: false };
  }
}

// Un `git status` staccato che scrive direttamente nel .tmp. --no-optional-locks
// impedisce a git di riscrivere l'index sotto le altre sessioni.
function gitRichiediRefresh(root) {
  try {
    const base = path.join(GIT_CACHE_DIR, `git-${gitChiave(root)}`);
    const tmp = `${base}.tmp`;
    const ultimo = Math.max(gitMtime(base), gitMtime(tmp));
    if (ultimo && (Date.now() - ultimo) < GIT_REFRESH_MIN_S * 1000) return;
    fs.mkdirSync(GIT_CACHE_DIR, { recursive: true });
    const fd = fs.openSync(tmp, 'w');
    try {
      const p = child_process.spawn(
        'git',
        ['-C', root, '--no-optional-locks', 'status', '--porcelain'],
        { detached: true, windowsHide: true, stdio: ['ignore', fd, 'ignore'], shell: false }
      );
      p.on('error', () => {});
      p.unref();
    } finally {
      try { fs.closeSync(fd); } catch (e) {}
    }
  } catch (e) {}
}

function gitInfo(dir) {
  try {
    let cur = path.resolve(dir);
    for (let i = 0; i < 40; i += 1) {
      const candidato = path.join(cur, '.git');
      let st = null;
      try { st = fs.statSync(candidato); } catch (e) { st = null; }
      if (st) {
        let gitDir = candidato;
        if (st.isFile()) { // worktree o submodule: .git è un file "gitdir: ..."
          const m = fs.readFileSync(candidato, 'utf8').match(/^gitdir:\s*(.+)$/m);
          if (!m) return null;
          gitDir = path.resolve(cur, m[1].trim());
        }
        const stato = gitStatoCache(cur);
        gitRichiediRefresh(cur);
        return { root: cur, ramo: gitRamo(gitDir), sporco: stato.fresca && stato.sporco };
      }
      const su = path.dirname(cur);
      if (su === cur) return null;
      cur = su;
    }
    return null;
  } catch (e) {
    return null;
  }
}

// --- Aggiornamento di Arturo -----------------------------------------------
// bin/aggiornamenti.py scrive lo stato in session-env/aggiornamento.json. La barra lo legge e, al
// massimo una volta all'ora, lancia un controllo staccato (fetch dei tag): come Claude Code, un
// aggiornamento arrivato mentre lavori si vede qui, e si installa da solo alla chiusura.
const AGG_FILE = path.join(CLAUDE_DIR, 'session-env', 'aggiornamento.json');
const AGG_TENTATIVO = path.join(CLAUDE_DIR, 'session-env', 'aggiornamento-controllo');
const AGG_ORA_S = 3600;

function aggiornamentoSegmento() {
  let stato = {};
  try { stato = JSON.parse(fs.readFileSync(AGG_FILE, 'utf8')) || {}; } catch (e) { stato = {}; }
  try {
    const controllato = Number(stato.controllato || 0) * 1000;
    const tentato = gitMtime(AGG_TENTATIVO);
    if (Date.now() - controllato > AGG_ORA_S * 1000 && (!tentato || Date.now() - tentato > AGG_ORA_S * 1000)) {
      fs.mkdirSync(path.dirname(AGG_TENTATIVO), { recursive: true });
      fs.writeFileSync(AGG_TENTATIVO, '');
      const p = child_process.spawn('python3', [path.join(CLAUDE_DIR, 'bin', 'aggiornamenti.py'), 'controlla'],
        { detached: true, windowsHide: true, stdio: 'ignore', shell: false });
      p.on('error', () => {});
      p.unref();
    }
  } catch (e) {}
  const versione = String(stato.versione || '').replace(/[\x00-\x1f\x7f]/g, '').slice(0, 30);
  if (!versione) return '';
  if (stato.stato === 'pronto') return ` │ \x1b[36m↑ Arturo ${versione} · si installa alla chiusura\x1b[0m`;
  // Una firma che manca o non torna non si scavalca con /aggiorna (17/10/2026, #3504).
  if (stato.compromesso === true) return ` │ \x1b[31m! Arturo ${versione} · possibile compromissione: non aggiornare, segnala a chi mantiene Arturo\x1b[0m`;
  if (stato.stato === 'manuale' || stato.stato === 'bloccato') return ` │ \x1b[33m↑ Arturo ${versione} · serve /aggiorna\x1b[0m`;
  return '';
}

// --- Quota dell'abbonamento ------------------------------------------------
// Arriva già su stdin (`rate_limits`): nessuna lettura, nessun processo.
// Chiavi assenti (prima della prima risposta, o piano senza limiti dichiarati,
// o uso via API) -> segmento vuoto. 5h e 7g sono le due finestre della quota.
function quotaSegmento(rate) {
  try {
    if (!rate || typeof rate !== 'object') return '';
    const leggi = f => {
      const v = rate[f];
      if (!v || typeof v !== 'object') return null;
      const p = v.used_percentage;
      if (typeof p !== 'number' || !Number.isFinite(p)) return null;
      return { pct: Math.max(0, Math.min(100, Math.round(p))), resets: v.resets_at };
    };
    const corta = leggi('five_hour');
    const lunga = leggi('seven_day');
    if (!corta && !lunga) return '';

    const picco = Math.max(corta ? corta.pct : 0, lunga ? lunga.pct : 0);
    const colore = picco >= 90 ? '\x1b[5;31m' : picco >= 75 ? '\x1b[38;5;208m'
      : picco >= 50 ? '\x1b[33m' : '\x1b[32m';
    // L'orario di riazzeramento compare solo quando la finestra stringe davvero:
    // sotto il 75% è un dato che non cambia nessuna decisione.
    const orario = v => {
      if (!v || v.pct < 75 || typeof v.resets !== 'number' || !Number.isFinite(v.resets)) return '';
      const d = new Date(v.resets * 1000);
      if (Number.isNaN(d.getTime())) return '';
      return `⟳${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
    };
    const pezzi = [];
    if (corta) pezzi.push(`5h ${corta.pct}%${orario(corta)}`);
    if (lunga) pezzi.push(`7g ${lunga.pct}%${orario(lunga)}`);
    return ` │ ${colore}quota ${pezzi.join(' · ')}\x1b[0m`;
  } catch (e) {
    return '';
  }
}


// Read JSON from stdin
let input = '';
// Timeout guard: if stdin doesn't close within 3s (e.g. pipe issues on
// Windows/Git Bash), exit silently instead of hanging.
const stdinTimeout = setTimeout(() => process.exit(0), 3000);
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
  clearTimeout(stdinTimeout);
  try {
    const data = JSON.parse(input);
    const model = data.model?.display_name || 'Claude';
    const dir = data.workspace?.current_dir || process.cwd();
    const session = data.session_id || '';
    const remaining = data.context_window?.remaining_percentage;

    // Context window display (shows USED percentage scaled to usable context)
    // Claude Code reserves ~16.5% for autocompact buffer, so usable context
    // is 83.5% of the total window. We normalize to show 100% at that point.
    const AUTO_COMPACT_BUFFER_PCT = 16.5;
    let ctx = '';
    if (remaining != null) {
      // Normalize: subtract buffer from remaining, scale to usable range
      const usableRemaining = Math.max(0, ((remaining - AUTO_COMPACT_BUFFER_PCT) / (100 - AUTO_COMPACT_BUFFER_PCT)) * 100);
      const used = Math.max(0, Math.min(100, Math.round(100 - usableRemaining)));

      // Write context metrics to bridge file for the context-monitor PostToolUse hook.
      // The monitor reads this file to inject agent-facing warnings when context is low.
      // Reject session IDs with path separators or traversal sequences to prevent
      // a malicious session_id from writing files outside the temp directory.
      const sessionSafe = session && !/[/\\]|\.\./.test(session);
      if (sessionSafe) {
        try {
          const bridgePath = path.join(os.tmpdir(), `claude-ctx-${session}.json`);
          const bridgeData = JSON.stringify({
            session_id: session,
            remaining_percentage: remaining,
            used_pct: used,
            timestamp: Math.floor(Date.now() / 1000)
          });
          fs.writeFileSync(bridgePath, bridgeData);
        } catch (e) {
          // Silent fail -- bridge is best-effort, don't break statusline
        }
      }

      // Build progress bar (10 segments)
      const filled = Math.floor(used / 10);
      const bar = '█'.repeat(filled) + '░'.repeat(10 - filled);

      // Color based on usable context thresholds
      if (used < 50) {
        ctx = ` \x1b[32m${bar} ${used}%\x1b[0m`;
      } else if (used < 65) {
        ctx = ` \x1b[33m${bar} ${used}%\x1b[0m`;
      } else if (used < 80) {
        ctx = ` \x1b[38;5;208m${bar} ${used}%\x1b[0m`;
      } else {
        ctx = ` \x1b[5;31m[CRITICO] ${bar} ${used}%\x1b[0m`;
      }
    }

    // Task in corso: i task nativi stanno in tasks/session-<primi 8 caratteri>/<n>.json
    // (misurato il 3/10/2026). Fino al 15/10/2026 il ramo leggeva todos/, che non esiste piu',
    // e il segmento non compariva mai.
    let task = '';
    const homeDir = os.homedir();
    // Respect CLAUDE_CONFIG_DIR for custom config directory setups
    const claudeDir = process.env.CLAUDE_CONFIG_DIR || path.join(homeDir, '.claude');
    const tasksDir = path.join(claudeDir, 'tasks', `session-${session.slice(0, 8)}`);
    if (session && /^[\w-]+$/.test(session) && fs.existsSync(tasksDir)) {
      try {
        for (const f of fs.readdirSync(tasksDir).filter(f => f.endsWith('.json'))) {
          try {
            const t = JSON.parse(fs.readFileSync(path.join(tasksDir, f), 'utf8'));
            if (t.status === 'in_progress') { task = t.activeForm || t.subject || ''; break; }
          } catch (e) {}
        }
      } catch (e) {
        // Silently fail on file system errors - don't break statusline
      }
    }

    // Luogo: nome del repository e ramo (con * se ci sono modifiche), oppure il
    // nome della cartella fuori da un repository.
    const git = gitInfo(dir);
    const progetto = git ? path.basename(git.root) : path.basename(dir);
    const luogo = git && git.ramo
      ? `${progetto}\x1b[0m\x1b[2m@${git.ramo}${git.sporco ? '*' : ''}`
      : progetto;

    // Output
    const quota = quotaSegmento(data.rate_limits) + aggiornamentoSegmento();
    const sigla = abbreviaModello(model);
    if (task) {
      process.stdout.write(`\x1b[2m${sigla}\x1b[0m │ \x1b[1m${task}\x1b[0m │ \x1b[2m${luogo}\x1b[0m${ctx}${quota}`);
    } else {
      process.stdout.write(`\x1b[2m${sigla}\x1b[0m │ \x1b[2m${luogo}\x1b[0m${ctx}${quota}`);
    }
  } catch (e) {
    // Silent fail - don't break statusline on parse errors
  }
});
