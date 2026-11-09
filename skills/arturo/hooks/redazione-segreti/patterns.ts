// Pattern presi da ~/.claude/hooks/credential-leak-scanner.py (CREDENTIAL_PATTERNS), con differenze volute:
// - niente pk_(live|test)_ di Stripe: è una chiave pubblicabile, non un segreto;
// - la chiave privata si redige intera fino a END, lo scanner ne vede solo l'intestazione;
// - sk-ant- accetta anche il trattino basso;
// - la stringa di connessione redige solo la password (DB_URL, sotto).
// Dal 3/10/2026 anche lo scanner riconosce OPENSSH e le stringhe mysql/mongodb/redis, come qui.
// Un pattern con un gruppo redige solo il gruppo: nome della chiave e separatore restano leggibili, e
// lo stesso valore dà la stessa sigla in ogni forma (TOKEN=x, "token": "x"). Il nome ammette la
// virgoletta di chiusura del JSON ("password": "…") e la parentesi di un indice (h["token"] = "…")
// (review del 7/11/2026, finding 60 e 70).
// Un pattern nuovo nello scanner va valutato anche qui: tests/test_pattern_segreti_allineati.py
// (nel set dei banchi) fallisce se lo scanner ha un tipo che questa lista non mappa.
export const PATTERNS: ReadonlyArray<readonly [RegExp, string]> = [
  [/(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}/g, 'aws-key'],
  [/gh[pousr]_[A-Za-z0-9_]{36,}/g, 'github-token'],
  [/github_pat_[A-Za-z0-9_]{22,}/g, 'github-pat'],
  [/(?:api[_-]?key|apikey|secret[_-]?key)["']?\]?\s*[:=]\s*["']?([A-Za-z0-9\-_]{20,})/gi, 'api-key'],
  [/xox[bporas]-[A-Za-z0-9-]{10,}/g, 'slack-token'],
  [/sk_(?:live|test)_[A-Za-z0-9]{20,}/g, 'stripe-secret'],
  [/supabase[_-]?(?:key|secret|anon)["']?\s*[:=]\s*["']?(eyJ[A-Za-z0-9\-_.]+)/gi, 'supabase-key'],
  [/eyJ[A-Za-z0-9\-_]{20,}\.eyJ[A-Za-z0-9\-_]{20,}\.[A-Za-z0-9\-_]{20,}/g, 'jwt'],
  [/-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED |PGP )?PRIVATE KEY(?: BLOCK)?-----[\s\S]*?(?:-----END (?:RSA |EC |DSA |OPENSSH |ENCRYPTED |PGP )?PRIVATE KEY(?: BLOCK)?-----|$)/g, 'private-key'],
  [/sk-ant-[A-Za-z0-9\-_]{20,}/g, 'anthropic-key'],
  [/sk-(?:proj|org)-[A-Za-z0-9\-_]{20,}/g, 'openai-key'],
  [/sk-[A-Za-z0-9]{48,}/g, 'openai-legacy-key'],
  [/\d{8,10}:[A-Za-z0-9_-]{35}/g, 'telegram-token'],
  [/BSA[A-Za-z0-9]{10,}/g, 'brave-key'],
  [/vercel[_-]?token["']?\s*[:=]\s*["']?([A-Za-z0-9]{24,})/gi, 'vercel-token'],
  [/[MN][A-Za-z\d]{23,}\.[\w-]{6}\.[\w-]{27,}/g, 'discord-token'],
  [/AIza[A-Za-z0-9\-_]{35}/g, 'google-api-key'],
  // Un valore che comincia con / o . è un percorso (token: /opt/…/app.js, token: ./src/app.js), non un segreto.
  [/(?:password|passwd|secret|token)["']?\]?\s*[:=]\s*["']?(?![./])([A-Za-z0-9\-_/+]{32,})/gi, 'generic-secret'],
  // Intestazione di autorizzazione (curl -v, log HTTP): token opaco di 20 caratteri o più (finding 67).
  [/authorization["']?\s*[:=]\s*["']?(?:bearer|basic|token)\s+([A-Za-z0-9\-_.~+/]{20,}=*)/gi, 'bearer-token'],
]

// Stringa di connessione: si redige solo la password, utente e host restano leggibili. L'utente può
// mancare (redis://:pw@host), e la password arriva all'ultima @ prima dell'host, così una @ dentro la
// password non lascia fuori il resto (review del 7/11/2026, finding 66).
export const DB_URL =
  /(postgres(?:ql)?|mysql|mariadb|mongodb(?:\+srv)?|rediss?|amqps?|https?):\/\/([^:\s/@"'<>]*):([^\s"'<>]+?)@(?=[^\s@/"'<>]*(?:[\s/"'<>?#]|$))/gi
