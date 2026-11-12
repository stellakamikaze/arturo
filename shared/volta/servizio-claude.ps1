# servizio-claude.ps1: il servizio di Claude di Windows come attività all'accesso (#5208), gemello del
# LaunchAgent di servizi-gui.sh sul Mac.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File servizio-claude.ps1           registra e avvia
#   powershell -NoProfile -ExecutionPolicy Bypass -File servizio-claude.ps1 -Togli    ferma e toglie
#
# Perché. Il servizio che tiene le sessioni in background (claude daemon) parte a tempo dal primo
# claude --bg: muore con chi l'ha avviato (hc exec chiude tutto il suo job) e, nato da ssh, vive nella
# sessione 0, dove i terminali e herdr-core (sessione 1) non lo raggiungono. claude daemon run invece
# resta acceso, e uno a tempo già acceso gli cede il posto riprendendo le sessioni vive. L'attività lo
# avvia a ogni accesso nella sessione grafica, senza finestra (conhost --headless) e senza limite di
# tempo. volta_sonda.py servizio la lancia con schtasks /run quando il servizio manca. Il nome
# dell'attività è scritto anche in installa-herdr.sh e in volta_sonda.py: il banco HZ43 lo tiene uguale.
param([switch]$Togli)
$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}  # hc e ssh leggono UTF-8
$nome = "ArturoServizioClaude"
if ($Togli) {
  Stop-ScheduledTask -TaskName $nome -ErrorAction SilentlyContinue
  Unregister-ScheduledTask -TaskName $nome -Confirm:$false -ErrorAction SilentlyContinue
  "SERVIZIO CLAUDE: attività $nome tolta (il servizio acceso resta fino al prossimo riavvio o a claude daemon stop)"
  exit 0
}
$claude = (Get-Command claude.exe -ErrorAction SilentlyContinue).Source
if (-not $claude) { $claude = Join-Path $env:USERPROFILE ".local\bin\claude.exe" }
if (-not (Test-Path $claude)) { "SERVIZIO CLAUDE NO: claude.exe non c'è in $claude"; exit 1 }
$utente = "$env:USERDOMAIN\$env:USERNAME"
$azione = New-ScheduledTaskAction -Execute "$env:WINDIR\System32\conhost.exe" -Argument "--headless `"$claude`" daemon run" -WorkingDirectory $env:USERPROFILE
$avvio = New-ScheduledTaskTrigger -AtLogOn -User $utente
$chi = New-ScheduledTaskPrincipal -UserId $utente -LogonType Interactive -RunLevel Limited
$regole = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -StartWhenAvailable
Register-ScheduledTask -TaskName $nome -Action $azione -Trigger $avvio -Principal $chi -Settings $regole -Description "Servizio di Claude per le sessioni in background (Arturo, servizio-claude.ps1)" -Force | Out-Null
"SERVIZIO CLAUDE: attività $nome registrata, parte a ogni accesso"
$stato = & $claude daemon status 2>&1 | Out-String
if ($stato -match "control\.sock:\s*reachable") {
  "SERVIZIO CLAUDE: un servizio risponde già: lo lascio acceso, l'attività parte dal prossimo accesso"
} else {
  Start-ScheduledTask -TaskName $nome
  "SERVIZIO CLAUDE: attività avviata"
}
