export const meta = {
  name: 'config-review',
  description: 'Revisione con più agenti della config ~/.claude: un revisore per area, un verificatore avversario per area, un critico di completezza. Sola lettura.',
  whenToUse: 'Motore della revisione profonda di /system-audit (sezione "Revisione con più agenti"), lanciato via scriptPath dopo review-prep.sh. Non è una skill a sé.',
  phases: [
    { title: 'Revisione', detail: 'un revisore per area' },
    { title: 'Verifica', detail: 'verificatore avversario per area' },
    { title: 'Sintesi', detail: 'critico di completezza' },
  ],
}

// Lezioni dalle revisioni della config da cui nasce Arturo:
// - gli agenti leggono soltanto: ogni ricerca la fa review-prep.sh prima, e qui si leggono i suoi file;
// - il lavoro non committato di altre sessioni non è un reperto da correggere;
// - un verificatore per area prova a SMENTIRE ogni reperto, e corregge le proposte troppo aggressive.
//
// args: { home: '<$HOME>', scratch: '<cartella di review-prep.sh>', dal: 'AAAA-MM-GG', oggi: 'AAAA-MM-GG', aree?: ['permessi', ...] }
// Lo script non vede il filesystem né l'ambiente: la HOME arriva da args, letta da $HOME in bash.

const A = (typeof args === 'string' && args.trim().startsWith('{')) ? JSON.parse(args) : (args || {})
if (!A.scratch) throw new Error('args.scratch richiesto: la cartella scritta da review-prep.sh')
if (!A.home) throw new Error('args.home richiesto: il valore di $HOME (echo "$HOME")')
const S = A.scratch
const C = `${A.home.replace(/\/+$/, '')}/.claude`
const DAL = A.dal || 'le ultime tre settimane'
const OGGI = A.oggi || 'oggi'
log(`args: ${typeof args} · config=${C} · scratch=${S} · dal=${DAL} · aree=${A.aree ? A.aree.join(',') : 'tutte'}`)

const COMMON = `Contesto: la config Claude Code da rivedere sta in ${C} (Arturo, un repository git). Rivedi le modifiche dal ${DAL} al ${OGGI}.
Digest già pronti, leggili per primi: ${S}/config-log.txt (commit con stat), ${S}/touched-files.txt, ${S}/gone-files.txt (file toccati che oggi non esistono), ${S}/git-status.txt (lavoro non committato di ALTRE sessioni: segnalalo, non è un reperto da correggere), ${S}/root-ls.txt, ${S}/tree.txt, ${S}/ignored-root.txt, ${S}/grep-index.txt (righe con credenziali lette a mano, percorsi di una sola macchina, termini scelti dalla persona).
TOOL: usa solo Read. Per cercare, parti da grep-index.txt e tree.txt, poi apri i file con Read. Bash non va usato.
Le righe con "rimosso", "archiviato", "dismesso" sono storia, non fantasmi: è un fantasma solo un riferimento OPERATIVO (codice che lo chiama, regola che lo prescrive, hook che lo carica).
I dati della persona (data/, projects/, personale/, CLAUDE.md) non sono reperti: non citarne il contenuto.
Ogni reperto ha una prova concreta: percorso assoluto e riga, o citazione esatta. Pochi reperti veri valgono più di molti deboli. Sola lettura. Rispondi in italiano.`

const FINDINGS = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string' },
          tipo: { type: 'string', enum: ['igiene', 'pulizia', 'incoerenza', 'rischio', 'ultracode'] },
          titolo: { type: 'string' },
          prova: { type: 'string' },
          proposta: { type: 'string' },
          peso: { type: 'string', enum: ['alto', 'medio', 'basso'] },
          reversibile: { type: 'boolean' },
        },
        required: ['id', 'tipo', 'titolo', 'prova', 'proposta', 'peso', 'reversibile'],
      },
    },
  },
  required: ['findings'],
}
const VERDICTS = {
  type: 'object',
  properties: {
    verdicts: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string' },
          esito: { type: 'string', enum: ['confermato', 'parziale', 'smentito'] },
          motivo: { type: 'string' },
          proposta_corretta: { type: 'string' },
        },
        required: ['id', 'esito', 'motivo'],
      },
    },
  },
  required: ['verdicts'],
}

const TUTTE = [
  { key: 'permessi', prompt: 'AREA: settings.json, autoMode, hooks/. Regole allow/deny/ask morte o contraddittorie, voci autoMode per sistemi che non ci sono più, hook registrati ma assenti o viceversa, variabili di ambiente obsolete, doppioni fra hook e mod.' },
  { key: 'resti', prompt: 'AREA: resti di sistemi dismessi (vedi grep-index.txt) ancora OPERATIVI in bin/, tests/, statusline, skills/, commands/, README.md. Distingui ciò che è solo storia da ciò che è rimasto attivo ma orfano.' },
  { key: 'skill-comandi', prompt: 'AREA: skills/, commands/, agents/. Description che promettono ciò che il corpo non fa, percorsi citati che non esistono (controlla con tree.txt), skill sovrapposte, regole in contraddizione fra skill e comandi.' },
  { key: 'istruzioni', prompt: 'AREA: README.md, docs/, output-styles/, shared/. Righe che descrivono il codice in modo falso, sigle non definite, contraddizioni, impalcature da potare secondo il Test Bitter Lesson (una regola che compensa un limite del modello invece di dare una garanzia).' },
  { key: 'script', prompt: 'AREA: bin/, tools/ e gli script toccati nel periodo, statusline. Codice duplicato fra script e hook, percorsi di una sola macchina, script che nessuno chiama più, comportamenti che cambiano in silenzio.' },
  { key: 'radice', prompt: 'AREA: radice di ~/.claude e .gitignore (root-ls.txt, ignored-root.txt, git-status.txt). File di runtime non ignorati, backup sparsi, cartelle di sistemi dismessi, voci di .gitignore verso cose che non esistono.' },
  { key: 'banchi', prompt: 'AREA: tests/, tests/verifica-allineamento.sh, skills/*/tests/. Banchi su disco fuori dal set del gate, banchi che provano componenti tolti, gate senza caso avvelenato, exit code letti dopo una pipe.' },
  { key: 'workflow', prompt: 'AREA: i workflow (skills/*/*.workflow.js) e le skill che fanno a mano fan-out o verifiche. Trappole note non applicate (args stringa, limiti silenziosi, barriere inutili, cartelle di lavoro condivise fra run), e occasioni concrete per un workflow salvato. tipo=ultracode per le occasioni.' },
]
const AREE = A.aree ? TUTTE.filter(a => A.aree.includes(a.key)) : TUTTE
const saltate = TUTTE.filter(a => !AREE.includes(a)).map(a => a.key)
if (saltate.length) log(`Aree non coperte in questa run: ${saltate.join(', ')}`)

phase('Revisione')
const results = await pipeline(
  AREE,
  a => agent(`${COMMON}\n\n${a.prompt}\n\nRestituisci i reperti (max 12, i più pesanti).`, { label: `rev:${a.key}`, phase: 'Revisione', schema: FINDINGS }),
  (rev, a) => {
    if (!rev) return { area: a.key, findings: [], verdicts: [], fallito: true }
    if (!rev.findings.length) return { area: a.key, findings: [], verdicts: [] }
    return agent(`${COMMON}\n\nSei un verificatore avversario. Per ogni reperto dell'area "${a.key}" apri la prova e cerca di SMENTIRLO: il file esiste? la riga dice quello? il riferimento è operativo o storico? qualcosa lo usa ancora (grep-index.txt, tree.txt)? la proposta romperebbe qualcosa? Nel dubbio: "parziale" col motivo. Correggi le proposte sbagliate o troppo aggressive.\n\nREPERTI:\n${JSON.stringify(rev.findings, null, 1)}`, { label: `ver:${a.key}`, phase: 'Verifica', schema: VERDICTS })
      .then(v => ({ area: a.key, findings: rev.findings, verdicts: v ? v.verdicts : [], verificaFallita: !v }))
  },
)

const valid = results.filter(Boolean)
const areeFallite = AREE.map(a => a.key).filter(k => !valid.some(r => r.area === k) || valid.find(r => r.area === k).fallito)
const nonVerificate = valid.filter(r => r.verificaFallita).map(r => r.area)
if (areeFallite.length) log(`ATTENZIONE: revisore fallito per ${areeFallite.join(', ')}`)
if (nonVerificate.length) log(`ATTENZIONE: verifica fallita per ${nonVerificate.join(', ')}: i loro reperti restano "non-verificato"`)

const merged = valid.flatMap(r => r.findings.map(f => {
  const v = r.verdicts.find(x => x.id === f.id)
  return { area: r.area, ...f, esito: v ? v.esito : 'non-verificato', motivo: v ? v.motivo : '', proposta_corretta: (v && v.proposta_corretta) || '' }
}))
const kept = merged.filter(f => f.esito !== 'smentito')
log(`${merged.length} reperti, ${merged.length - kept.length} smentiti, ${kept.length} tenuti`)

phase('Sintesi')
const critic = await agent(`${COMMON}\n\nSei il critico di completezza. Reperti sopravvissuti:\n${JSON.stringify(kept.map(f => ({ area: f.area, titolo: f.titolo })), null, 1)}\n\nScorri config-log.txt: quali commit o aree NON sono coperti da nessun reperto e meritano un controllo? Controllali tu con Read e restituisci SOLO reperti nuovi con prova (max 8).`, { label: 'critico', phase: 'Sintesi', schema: FINDINGS })

return {
  kept,
  smentiti: merged.filter(f => f.esito === 'smentito').map(f => ({ area: f.area, titolo: f.titolo, motivo: f.motivo })),
  extra: critic ? critic.findings : [],
  copertura: { aree: AREE.map(a => a.key), saltate, areeFallite, nonVerificate, criticoFallito: !critic },
}
