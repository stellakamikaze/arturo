// Logica pura, provata da tests/gws.test.ts.

// Credenziali mancanti o revocate. Senza questa nota Claude riprova lo stesso comando, o cambia
// account, invece di chiedere il login. Un 403 di scope non è qui: lì il token c'è e manca un permesso.
const GUASTI = ['No credentials provided', 'invalid_grant', 'undecryptable'] as const

export function guasto(testo: string): string | null {
  return GUASTI.find(g => testo.includes(g)) ?? null
}

export type Account = { nome: string; dir: string }

// L'account è la cartella di config di gws: quella scritta nel comando, altrimenti quella della
// sessione (GOOGLE_WORKSPACE_CLI_CONFIG_DIR), altrimenti quella di default di gws (~/.config/gws).
export function account(cmd: string, dirSessione: string | undefined): Account {
  const m = /GOOGLE_WORKSPACE_CLI_CONFIG_DIR=(["']?)([^\s"';]+)\1/.exec(cmd)
  const dir = (m?.[2] ?? dirSessione ?? '').trim() || '~/.config/gws'
  const nome = dir.replace(/[\\/]+$/, '').split(/[\\/]/).pop() || 'gws'
  return { nome, dir }
}

export function nota(acc: Account): string {
  return (
    `\n[gws] L'account ${acc.nome} non ha credenziali valide su questo computer. ` +
    'Non riprovare con un altro account e non cambiare comando. ' +
    `Serve che la persona rifaccia il login: GOOGLE_WORKSPACE_CLI_CONFIG_DIR=${acc.dir} gws auth login ` +
    '(la guida è in ~/.claude/docs/onboarding/gws.md). Diglielo e fermati su gws.'
  )
}

// `gws gmail messages …` non esiste: le risorse di Gmail stanno sotto `users`.
const GMAIL = /((?:^|[;&|\n(])\s*(?:[A-Za-z_]+=\S+\s+)*gws\s+gmail\s+)(messages|threads|drafts|labels|history)\b/g

export function correggiSintassi(cmd: string): string {
  return cmd.replace(GMAIL, '$1users $2')
}
