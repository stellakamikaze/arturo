import { describe, expect, test } from 'claude-code/testing'

import { riscrivi } from '../hooks/riscrivi'

const MAC = { zsh: true, haTimeout: false }

describe('glob in un\'opzione', () => {
  test('quota il valore non quotato', () => {
    expect(riscrivi('grep -rl foo --include=*.md .', MAC).command).toBe("grep -rl foo --include='*.md' .")
  })
  test('quota più opzioni nello stesso comando', () => {
    expect(riscrivi('rg x --glob=*.ts --iglob=src/*', MAC).command).toBe("rg x --glob='*.ts' --iglob='src/*'")
  })
  test('lascia stare un valore già quotato', () => {
    const c = "grep -r x --include='*.md' ."
    expect(riscrivi(c, MAC).command).toBe(c)
  })
  test('lascia stare un valore misto con virgolette: decide il dispatcher', () => {
    const c = 'grep --include=*"a b".md x'
    expect(riscrivi(c, MAC).command).toBe(c)
  })
  test('lascia stare un heredoc', () => {
    const c = "cat <<'X'\n--include=*.md\nX"
    expect(riscrivi(c, MAC).command).toBe(c)
  })
  test('in bash non tocca niente', () => {
    const c = 'grep --include=*.md x'
    expect(riscrivi(c, { zsh: false, haTimeout: false }).command).toBe(c)
  })
})

describe('timeout', () => {
  test('toglie timeout e alza il timeout del tool', () => {
    const r = riscrivi('timeout 30 curl -s http://server:8080', MAC)
    expect(r.command).toBe('curl -s http://server:8080')
    expect(r.timeoutMs).toBe(35_000)
  })
  test('dopo && e con opzioni', () => {
    const r = riscrivi('cd /tmp && timeout -s KILL 2m ./job.sh', MAC)
    expect(r.command).toBe('cd /tmp && ./job.sh')
    expect(r.timeoutMs).toBe(125_000)
  })
  test('tiene sudo davanti', () => {
    expect(riscrivi('sudo timeout 5 ls', MAC).command).toBe('sudo ls')
  })
  test('ssh: timeout gira sul server, resta', () => {
    const c = 'ssh server timeout 10 docker ps'
    expect(riscrivi(c, MAC).command).toBe(c)
  })
  test('timeout dentro una stringa non è un comando', () => {
    const c = 'echo "timeout 5 x" && git log'
    expect(riscrivi(c, MAC).command).toBe(c)
  })
  test('parola timeout come argomento resta', () => {
    const c = 'grep -n timeout file.sh'
    expect(riscrivi(c, MAC).command).toBe(c)
  })
  test('se timeout esiste (Linux) non tocca', () => {
    const c = 'timeout 30 make'
    expect(riscrivi(c, { zsh: true, haTimeout: true }).command).toBe(c)
  })
  test('timeout seguito da || o da un altro comando: resta al dispatcher', () => {
    for (const c of ['timeout 3 nc -z server 22 || echo giù; git status', 'timeout 5 make; ls', 'timeout 5 make | tail -3']) {
      const r = riscrivi(c, MAC)
      expect(r.command).toBe(c)
      expect(r.fatti.length).toBe(0)
    }
  })
  test('due timeout nello stesso comando: resta al dispatcher', () => {
    const c = 'cd a && timeout 5 x && timeout 9 y'
    expect(riscrivi(c, MAC).command).toBe(c)
  })
  test('non abbassa un timeout del tool già più alto', () => {
    expect(riscrivi('timeout 5 make', { ...MAC, timeoutMs: 300_000 }).timeoutMs).toBe(300_000)
  })
})

test('comando normale passa identico e senza fatti', () => {
  const r = riscrivi('git status --short', MAC)
  expect(r.command).toBe('git status --short')
  expect(r.fatti.length).toBe(0)
})
