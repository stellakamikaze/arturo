# volta-claude.ps1: il comando claude di Volta Celeste in PowerShell (#5172 passo 3), gemello di volta-claude.sh.
# In un terminale vero la sessione nasce in background (claude --bg) e si apre qui con claude attach:
# così Volta la apre da qualunque macchina anche mentre lavora, e chiudere il terminale non la ferma.
# Il resto passa a claude com'è: i sottocomandi (agents, attach, mcp, ...), -p, --version, e chi lancia
# claude da uno script o da un'altra sessione.
#
# Via di fuga: $env:CLAUDE_QUI = 1, poi claude, apre la sessione qui, interattiva, come prima.
# Nei terminali di Herdr (HC_TERMINAL_ID) la sessione resta interattiva finché Volta non legge lo stato
# delle sessioni in background (passo 4 del piano).
# Una sessione in background prende l'ambiente dal servizio di Claude, non da questa shell.
#
# Lo installa installa-herdr.sh in ~/.config/herdr-app/volta-claude.ps1; il blocco nel profilo di PowerShell
# (nascita.sh) chiama questo file. Il file ha il BOM: Windows PowerShell 5.1 legge senza BOM come ANSI.
# Per i banchi: VOLTA_CLAUDE_BIN (il claude da lanciare), VOLTA_CLAUDE_TTY=1 (fa finta che il terminale sia vero),
# VOLTA_SONDA (la sonda del servizio) e VOLTA_SONDA_PY (il Python che la lancia).

$ErrorActionPreference = 'Continue'
$a = @($args)

# CommandType Application: il comando claude del profilo è una funzione, e chiamerebbe di nuovo questo file.
$bin = $env:VOLTA_CLAUDE_BIN
if (-not $bin) {
  $bin = Get-Command claude -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Source
}
if (-not $bin) {
  [Console]::Error.WriteLine('Volta: non trovo il programma claude. Installa Claude Code, poi riapri il terminale.')
  exit 127
}

function Qui { & $bin @a; exit $LASTEXITCODE }

if ($env:CLAUDE_QUI -eq '1') { Qui }
if ($env:CLAUDECODE) { Qui }
if ($env:HC_TERMINAL_ID) { Qui }
if ($env:VOLTA_CLAUDE_TTY -ne '1') {
  if ([Console]::IsInputRedirected -or [Console]::IsOutputRedirected) { Qui }
}

# I sottocomandi di claude 2.1 (claude --help, Commands) restano com'erano.
$sottocomandi = 'agents', 'attach', 'auth', 'auto-mode', 'config', 'doctor', 'gateway', 'import', 'install', 'logs',
  'mcp', 'migrate-installer', 'plugin', 'plugins', 'purge', 'respawn', 'rm', 'setup-token', 'stop', 'kill',
  'ultrareview', 'update', 'upgrade'
if ($a.Count -gt 0 -and $sottocomandi -ccontains [string]$a[0]) { Qui }

# Le opzioni che non hanno senso in background, o che lo sono già.
# --resume senza id apre la scelta della sessione, che è interattiva; con l'id va in background.
$fuori = '-p', '--print', '-v', '--version', '-h', '--help', '--bg', '--background', '-c', '--continue',
  '--cloud', '--desktop', '--teleport', '--remote-control', '--tmux', '--output-format', '--input-format', '--ide'
$senzaId = $false
foreach ($x in $a) {
  $s = [string]$x
  if ($senzaId) {
    if ($s.StartsWith('-')) { Qui }
    $senzaId = $false
  }
  if ($fuori -ccontains $s -or $fuori -ccontains ($s -split '=', 2)[0]) { Qui }
  if ($s -ceq '-r' -or $s -ceq '--resume') { $senzaId = $true }
}
if ($senzaId) { Qui }

# Prima il servizio di Claude fisso (#5215), con volta_sonda.py del mod come fa Volta prima di ogni nascita:
# senza, claude --bg lo accende a tempo, e muore quando resta senza sessioni. Da ssh no: lì il servizio
# nascerebbe fuori dalla sessione di Windows, senza il login di Claude. Il Python è quello che
# installa-herdr.sh ha scritto in arturo.json (lo Store di Windows mette un python3 finto). Se la sonda
# manca o non riesce, la sessione nasce lo stesso, come prima.
$sonda = $env:VOLTA_SONDA
if (-not $sonda) { $sonda = Join-Path $PSScriptRoot 'mods/arturo/volta_sonda.py' }
$py = $env:VOLTA_SONDA_PY
if (-not $py) {
  try { $py = @((Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'arturo.json') | ConvertFrom-Json).arturo)[0] } catch { $py = $null }
}
if (-not $env:SSH_CONNECTION -and $py -and (Test-Path -LiteralPath $sonda)) {
  $esito = @(& $py $sonda servizio qui 2>&1 | ForEach-Object { "$_" })
  if ($LASTEXITCODE -ne 0) {
    $ultima = ($esito | Select-Object -Last 1)
    if (-not $ultima) { $ultima = "uscita $LASTEXITCODE" }
    if ($ultima.Length -gt 160) { $ultima = $ultima.Substring(0, 160) }
    [Console]::Error.WriteLine("Volta: il servizio di Claude non si accende ($ultima). La sessione nasce lo stesso.")
  }
}

# 2>&1 con ForEach: Windows PowerShell 5.1 avvolge lo stderr di un programma in un errore, qui torna testo.
$uscita = @(& $bin --bg @a 2>&1 | ForEach-Object { "$_" })
$rc = $LASTEXITCODE
$id = $null
foreach ($r in $uscita) {
  if ($r -match 'claude attach ([0-9A-Za-z-]+)') { $id = $Matches[1]; break }
}
if ($rc -ne 0 -or -not $id) {
  if ($rc -eq 0) {
    # È partita ma non ha stampato l'id che conosco: niente seconda sessione, mostro cosa ha detto.
    $uscita | ForEach-Object { Write-Output $_ }
    [Console]::Error.WriteLine('Volta: la sessione è partita in background, ma non ho letto il suo id. claude agents la elenca.')
    exit 0
  }
  # La prima riga che dice perché: "Starting background service" la stampa claude a ogni avvio del servizio.
  $motivo = $uscita | Where-Object { $_ -and $_ -notmatch '^Starting background service' } | Select-Object -First 1
  if (-not $motivo) { $motivo = "uscita $rc" }
  [Console]::Error.WriteLine("Volta: la sessione non parte in background ($motivo). La apro qui, come prima.")
  Qui
}

& $bin attach $id
$rc = $LASTEXITCODE
[Console]::Error.WriteLine("La sessione $id continua in background: claude attach $id la riapre qui.")
exit $rc
