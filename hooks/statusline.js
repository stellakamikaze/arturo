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
    // Fuori da Arturo (nessun bin/aggiornamenti.py) non lancia niente, e senza stato il segmento tace.
    if (fs.existsSync(path.join(CLAUDE_DIR, 'bin', 'aggiornamenti.py')) && Date.now() - controllato > AGG_ORA_S * 1000 && (!tentato || Date.now() - tentato > AGG_ORA_S * 1000)) {
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
  if (stato.non_verificabile === true) return ` │ \x1b[33m↑ Arturo ${versione} · aggiorna git e OpenSSH per installarlo\x1b[0m`;
  if (stato.stato === 'manuale' || stato.stato === 'bloccato') return ` │ \x1b[33m↑ Arturo ${versione} · serve /aggiorna\x1b[0m`;
  return '';
}

// --- Quota dell'abbonamento ------------------------------------------------
// Arriva già su stdin (`rate_limits`): nessuna lettura, nessun processo.
// Chiavi assenti (prima della prima risposta, o piano senza limiti dichiarati,
// o uso via API) -> segmento vuoto. Le due finestre della quota si dicono in
// parole, "5 ore" e "settimana": alla sera del Computer Club del 27/10/2026 chi
// leggeva "5h 84%" lo prendeva per la quota della settimana.
const QUOTA_FILE = path.join(GIT_CACHE_DIR, 'quota.json');
const GIORNI = ['dom', 'lun', 'mar', 'mer', 'gio', 'ven', 'sab'];

function hhmm(d) {
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
}

// L'ultima quota vista, per /guidami: sa quanto resta e quando si azzera senza
// chiederlo alla persona. Si scrive solo quando cambia, con rename atomico; sta
// in cache/, che git ignora e gli aggiornamenti non toccano.
function salvaQuota(corta, lunga) {
  try {
    const dati = JSON.stringify({ cinque_ore: corta, settimana: lunga });
    let prima = '';
    try { prima = fs.readFileSync(QUOTA_FILE, 'utf8'); } catch (e) {}
    if (prima === dati) return;
    fs.mkdirSync(GIT_CACHE_DIR, { recursive: true });
    const tmp = `${QUOTA_FILE}.${process.pid}.tmp`;
    fs.writeFileSync(tmp, dati);
    fs.renameSync(tmp, QUOTA_FILE);
  } catch (e) {
    // La barra non si ferma per un file di appoggio
  }
}

function quotaSegmento(rate) {
  try {
    if (!rate || typeof rate !== 'object') return '';
    const leggi = f => {
      const v = rate[f];
      if (!v || typeof v !== 'object') return null;
      const p = v.used_percentage;
      if (typeof p !== 'number' || !Number.isFinite(p)) return null;
      const r = typeof v.resets_at === 'number' && Number.isFinite(v.resets_at) ? v.resets_at : null;
      return { pct: Math.max(0, Math.min(100, Math.round(p))), resets: r };
    };
    const corta = leggi('five_hour');
    const lunga = leggi('seven_day');
    if (!corta && !lunga) return '';
    salvaQuota(corta, lunga);

    const picco = Math.max(corta ? corta.pct : 0, lunga ? lunga.pct : 0);
    const colore = picco >= 90 ? '\x1b[5;31m' : picco >= 75 ? '\x1b[38;5;208m'
      : picco >= 50 ? '\x1b[33m' : '\x1b[32m';
    // L'orario di azzeramento delle 5 ore si vede sempre: dice quanto tempo resta
    // per usare quello che avanza. Quello della settimana solo da 75%, col giorno.
    const azzera = (v, conGiorno) => {
      if (!v || v.resets === null) return '';
      const d = new Date(v.resets * 1000);
      if (Number.isNaN(d.getTime())) return '';
      return `, si azzera ${conGiorno ? GIORNI[d.getDay()] + ' ' : 'alle '}${hhmm(d)}`;
    };
    const pezzi = [];
    if (corta) pezzi.push(`5 ore ${corta.pct}%${azzera(corta, false)}`);
    if (lunga) pezzi.push(`settimana ${lunga.pct}%${lunga.pct >= 75 ? azzera(lunga, true) : ''}`);
    return ` │ ${colore}quota ${pezzi.join(' · ')}\x1b[0m`;
  } catch (e) {
    return '';
  }
}


// Lo slug di una cartella, come lo calcolano /inizio e /fine.
function slug(nome) {
  return String(nome).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
}

// Il progetto che scheda-terminale.py ha salvato per la sessione in cache/scheda/<sessione>.json.
// Fuori i caratteri di controllo: il nome finisce dentro le sequenze della barra.
function progettoScheda(sessione) {
  const id = String(sessione || '').replace(/[^\w-]/g, '').slice(0, 64);
  if (!id) return '';
  try {
    const s = JSON.parse(fs.readFileSync(path.join(CLAUDE_DIR, 'cache', 'scheda', id + '.json'), 'utf8'));
    return typeof s.progetto === 'string' ? s.progetto.replace(/[\x00-\x1f\x7f-\x9f]/g, '').slice(0, 40) : '';
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

    // Context usato, scala GREZZA (100 - remaining): una scala sola per statusline,
    // context-monitor e la regola della rotazione al ~65% (3/10/2026; in Arturo dal 20/10/2026).
    // Prima la barra normalizzava sul context utile (tolto il 16,5% di autocompact) e
    // mostrava ~7 punti in più di quanto dicesse la regola.
    let ctx = '';
    if (remaining != null) {
      const used = Math.max(0, Math.min(100, Math.round(100 - remaining)));

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

      // Soglie: 55 giallo, 65 arancio (rotazione), 80 critico
      if (used < 55) {
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

    // Luogo: il progetto che la scheda del terminale ha trovato per questa sessione (/inizio, un alias
    // che lancia arturo contesto, i file scritti), poi il repository e infine la cartella
    // (segnalazione n. 35, 29/10/2026). Il ramo, con * se ci sono modifiche, solo se il repository è
    // quel progetto: aperta dalla home, la sessione non mostra il ramo di un altro repository.
    const git = gitInfo(dir);
    const daCartella = git ? path.basename(git.root) : path.basename(dir);
    const scheda = progettoScheda(session);
    const progetto = scheda || daCartella;
    const luogo = git && git.ramo && (!scheda || slug(daCartella) === scheda)
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
