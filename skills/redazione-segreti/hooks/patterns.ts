// Pattern presi da ~/.claude/hooks/credential-leak-scanner.py (CREDENTIAL_PATTERNS), con differenze volute:
// - niente pk_(live|test)_ di Stripe: è una chiave pubblicabile, non un segreto;
// - la chiave privata si redige intera fino a END, lo scanner ne vede solo l'intestazione;
// - sk-ant- accetta anche il trattino basso;
// - la stringa di connessione redige solo la password (DB_URL, sotto).
// Dal 3/10/2026 anche lo scanner riconosce OPENSSH e le stringhe mysql/mongodb/redis, come qui.
// Un pattern nuovo nello scanner va valutato anche qui: tests/test_pattern_segreti_allineati.py
// (nel set dei banchi) fallisce se lo scanner ha un tipo che questa lista non mappa.
export const PATTERNS: ReadonlyArray<readonly [RegExp, string]> = [
  [/(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}/g, 'aws-key'],
  [/gh[pousr]_[A-Za-z0-9_]{36,}/g, 'github-token'],
  [/github_pat_[A-Za-z0-9_]{22,}/g, 'github-pat'],
  [/(?:api[_-]?key|apikey|secret[_-]?key)\s*[:=]\s*["']?[A-Za-z0-9\-_]{20,}/gi, 'api-key'],
  [/xox[bporas]-[A-Za-z0-9-]{10,}/g, 'slack-token'],
  [/sk_(?:live|test)_[A-Za-z0-9]{20,}/g, 'stripe-secret'],
  [/supabase[_-]?(?:key|secret|anon)\s*[:=]\s*["']?eyJ[A-Za-z0-9\-_.]+/gi, 'supabase-key'],
  [/eyJ[A-Za-z0-9\-_]{20,}\.eyJ[A-Za-z0-9\-_]{20,}\.[A-Za-z0-9\-_]{20,}/g, 'jwt'],
  [/-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----[\s\S]*?(?:-----END (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----|$)/g, 'private-key'],
  [/sk-ant-[A-Za-z0-9\-_]{20,}/g, 'anthropic-key'],
  [/sk-(?:proj|org)-[A-Za-z0-9\-_]{20,}/g, 'openai-key'],
  [/sk-[A-Za-z0-9]{48,}/g, 'openai-legacy-key'],
  [/\d{8,10}:[A-Za-z0-9_-]{35}/g, 'telegram-token'],
  [/BSA[A-Za-z0-9]{10,}/g, 'brave-key'],
  [/vercel[_-]?token\s*[:=]\s*["']?[A-Za-z0-9]{24,}/gi, 'vercel-token'],
  [/[MN][A-Za-z\d]{23,}\.[\w-]{6}\.[\w-]{27,}/g, 'discord-token'],
  [/AIza[A-Za-z0-9\-_]{35}/g, 'google-api-key'],
  [/(?:password|passwd|secret|token)\s*[:=]\s*["']?[A-Za-z0-9\-_/+]{32,}/gi, 'generic-secret'],
]

// Stringa di connessione: si redige solo la password, utente e host restano leggibili.
export const DB_URL = /(postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis):\/\/([^:\s/@]+):([^@\s]+)@/gi
