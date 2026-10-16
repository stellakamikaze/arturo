#!/bin/bash
# Prova di aggiornamento come un utente, prima di ogni rilascio su main (docs/manutenzione.md, passo 3).
#
#   bash tests/prova-aggiornamento.sh <tag di partenza> [ref da rilasciare, di default HEAD]
#
# Un utente alla versione <tag>, con una sua riga aggiunta a /inizio e committata, riceve il ref
# da rilasciare come se fosse già su main, con lo stesso bin/aggiorna-applica.sh di /aggiorna.
# Tutto in una HOME finta clonata da questo repository, senza rete: la ~/.claude vera non si
# tocca (HOME e USERPROFILE spostate, config git globale finta), e da una HOME temporanea la
# telemetria non parte. Exit 0 se ogni controllo passa, 1 altrimenti. Nato il 16/10/2026 da una
# prova fatta a mano prima del rilascio (#3409).
set -u
PARTENZA="${1:?uso: bash tests/prova-aggiornamento.sh <tag di partenza> [ref da rilasciare]}"
ROOT=$(cd "$(dirname "$0")/.." && pwd)
RILASCIO=$(git -C "$ROOT" rev-parse --verify -q "${2:-HEAD}^{commit}") || { echo "FAIL: ref sconosciuto: ${2:-HEAD}"; exit 1; }
git -C "$ROOT" rev-parse --verify -q "$PARTENZA^{commit}" >/dev/null || { echo "FAIL: tag sconosciuto: $PARTENZA"; exit 1; }
VERA="$HOME/.claude"
VERA_HEAD=$(git -C "$VERA" rev-parse -q HEAD 2>/dev/null || echo "nessuna")

H=$(mktemp -d "${TMPDIR:-/tmp}/utente-arturo.XXXX")
trap 'rm -rf "$H"' EXIT
# ARTURO_BANCHI_AVVIO=0: l'avvio lancerebbe i banchi in background, ancora vivi quando la HOME finta si cancella.
export HOME="$H" USERPROFILE="$H" GIT_CONFIG_GLOBAL="$H/.gitconfig" GIT_CONFIG_NOSYSTEM=1 ARTURO_TELEMETRIA=0 \
  ARTURO_BANCHI_AVVIO=0
git config --global user.name "utente prova" && git config --global user.email "prova@example.invalid"
git config --global core.autocrlf false

KO=0
controlla() {  # controlla <descrizione> <esito 0/1>
  if [ "$2" = 0 ]; then echo "PASS $1"; else echo "FAIL $1"; KO=$((KO + 1)); fi
}

git clone -q "$ROOT" "$H/.claude" || { echo "FAIL: clone di $ROOT"; exit 1; }
cd "$H/.claude" || exit 1
git checkout -q -B main "$PARTENZA" && git branch -q -u origin/main main 2>/dev/null
echo "== partenza: $PARTENZA ($(git rev-parse --short HEAD)), rilascio: $(git rev-parse --short "$RILASCIO")"
mkdir -p session-env && grep '^## ' NOVITA.md | sed 's/^## //' > session-env/novita-viste   # ha letto le sue novità
NOTA="Nota mia: per i miei progetti uso sempre Vue."
printf '\n%s\n' "$NOTA" >> commands/inizio.md
git commit -qam "mia modifica a /inizio"
git update-ref refs/remotes/origin/main "$RILASCIO"   # come dopo il rilascio su main

echo "== applico il rilascio"
APPLICA=$(mktemp "$H/applica.XXXX.sh")
git show "$RILASCIO:bin/aggiorna-applica.sh" > "$APPLICA"
bash "$APPLICA" "$H/.claude" rebase origin/main > "$H/applica.log" 2>&1
RC=$?
tail -6 "$H/applica.log"
controlla "aggiorna-applica.sh esce 0 (rc=$RC)" "$([ $RC = 0 ] && echo 0 || echo 1)"

echo "== esito"
controlla "il rilascio è nella storia dell'utente" "$(git merge-base --is-ancestor "$RILASCIO" HEAD && echo 0 || echo 1)"
controlla "la riga della persona non si perde (in commands/ o in personale/)" \
  "$(grep -qF "$NOTA" commands/inizio.md personale/inizio.md 2>/dev/null && echo 0 || echo 1)"
DIVERSI=$(git diff --name-only "$RILASCIO" -- bin hooks skills agents shared settings.json | tr '\n' ' ')
controlla "bin, hooks, skills, agents, shared e settings.json come nel rilascio${DIVERSI:+ (diversi: $DIVERSI)}" \
  "$([ -z "$DIVERSI" ] && echo 0 || echo 1)"
TOLTI=$(git diff --name-only --diff-filter=D "$PARTENZA" "$RILASCIO" | while read -r f; do [ -e "$f" ] && echo "$f"; done | tr '\n' ' ')
controlla "i file tolti dal rilascio spariscono${TOLTI:+ (restano: $TOLTI)}" "$([ -z "$TOLTI" ] && echo 0 || echo 1)"
controlla "settings.json è JSON valido" "$(python3 -c "import json; json.load(open('settings.json', encoding='utf-8'))" 2>/dev/null && echo 0 || echo 1)"
SPORCHI=$(git status --porcelain | grep -vc '^??')
controlla "nessun file tracciato lasciato modificato ($SPORCHI)" "$([ "$SPORCHI" = 0 ] && echo 0 || echo 1)"
NUOVE=$(git diff "$PARTENZA" "$RILASCIO" -- NOVITA.md | grep -c '^+## ')
if [ "$NUOVE" -gt 0 ]; then
  bash hooks/session-start.sh </dev/null > "$H/avvio.log" 2>/dev/null
  controlla "l'avvio annuncia le $NUOVE novità nuove" "$(grep -qi "novit" "$H/avvio.log" && echo 0 || echo 1)"
fi
cd "$ROOT" || exit 1
# Un commit di un'altra sessione sulla config vera, durante la prova, darebbe un falso FAIL.
controlla "la config vera non ha commit nuovi" \
  "$([ "$(git -C "$VERA" rev-parse -q HEAD 2>/dev/null || echo nessuna)" = "$VERA_HEAD" ] && echo 0 || echo 1)"

echo "== $KO controlli falliti"
[ "$KO" = 0 ]
