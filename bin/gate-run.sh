#!/usr/bin/env bash
# gate-run.sh: esegue un gate solo dopo aver provato che il suo veleno è rosso per il motivo giusto.
# Un gate vale solo se boccia una versione rotta apposta (il «veleno») per il motivo atteso.
#
# USO
#   gate-run.sh --poison 'CMD' --expect 'MARCATORE' [--pass 'MARCATORE'] [--source FILE]... -- GATE_CMD [ARG...]
#
#   --poison CMD      comando che esegue il gate sulla versione rotta (stringa, bash -o pipefail -c).
#   --expect MARKER   testo che l'output del veleno deve contenere: il motivo atteso del rosso.
#   --pass MARKER     (facoltativo) testo che l'output del gate vero deve contenere per il verde.
#                     Usalo quando il gate stampa un risultato positivo: il solo exit 0 non basta.
#   --source FILE     (facoltativo, ripetibile) file che il gate legge. Deve esistere e non essere vuoto.
#   -- GATE_CMD       il gate vero, come argv. Per una pipeline passa: bash -o pipefail -c '...'.
#
#   La cartella di lavoro in $TMPDIR si cancella solo sul verde. Su un esito rosso resta,
#   di proposito, per l'ispezione.
#
# ORDINE
#   1. Controlla ogni --source: se manca o è vuota, esce 3.
#   2. Esegue il veleno. Esige exit diverso da 0 E il marcatore --expect nell'output.
#      Veleno verde o rosso senza marcatore: esce 2 (il gate non discrimina).
#   3. Controlla dove ha scritto il veleno. In $VELENO_DIR accetta solo file veleno-*.
#      Nella cartella corrente accetta solo file veleno-* nuovi o modificati. Altrimenti esce 3.
#   4. Esegue il gate vero. Esce 0 se è verde (e trova --pass), 1 se è rosso.
#
#   L'exit code di ogni comando viene scritto su file subito dopo il comando e riletto da lì.
#   Niente pipe e niente PIPESTATUS. Un file di exit vuoto o non numerico: esce 3.
#   Il veleno riceve VELENO_DIR (cartella temporanea nuova): i suoi file vanno lì, con nome veleno-*.
#
# EXIT
#   0 verde · 1 gate rosso · 2 il veleno non boccia per il motivo atteso · 3 guasto del banco o uso sbagliato
#
# LIMITE NOTO
#   Il controllo del punto 3 guarda i file cambiati nella cartella corrente durante il veleno.
#   Se un altro processo scrive lì nello stesso momento, il banco esce 3: lancia da una cartella quieta.

set -u

POISON="" EXPECT="" PASS=""
SOURCES=()

die() { printf 'GATE_RUN: GUASTO %s\n' "$1" >&2; exit 3; }

while (($#)); do
  case "$1" in
    --poison) (($# >= 2)) || die "--poison senza comando"; POISON="$2"; shift 2 ;;
    --expect) (($# >= 2)) || die "--expect senza marcatore"; EXPECT="$2"; shift 2 ;;
    --pass)   (($# >= 2)) || die "--pass senza marcatore"; PASS="$2"; shift 2 ;;
    --source) (($# >= 2)) || die "--source senza file"; SOURCES+=("$2"); shift 2 ;;
    --) shift; break ;;
    -h|--help) sed -n '2,35p' "$0"; exit 0 ;;
    *) die "argomento sconosciuto: $1 (uso: gate-run.sh --poison CMD --expect MARKER -- GATE_CMD)" ;;
  esac
done

[[ -n "$POISON" ]] || die "manca --poison: un gate senza veleno non dichiara verde"
[[ -n "$EXPECT" ]] || die "manca --expect: il rosso del veleno deve avere un motivo"
(($# > 0))        || die "manca il gate vero dopo --"

# esegue un comando e scrive exit code e output su file, senza pipe
run_to_files() { # out rcfile cmd...
  local out="$1" rcf="$2"; shift 2
  "$@" >"$out" 2>&1 </dev/null
  printf '%s\n' "$?" >"$rcf"
}

# legge l'exit code dal file e lo valida
read_rc() { # rcfile etichetta
  local v=""
  [[ -s "$1" ]] && v="$(<"$1")"
  [[ "$v" =~ ^[0-9]+$ ]] || die "exit code perso per $2 (file $1 vuoto o non numerico)"
  printf '%s' "$v"
}

# 1. sorgenti
for s in "${SOURCES[@]+"${SOURCES[@]}"}"; do
  [[ -e "$s" ]] || die "sorgente assente: $s"
  [[ -s "$s" ]] || die "sorgente vuota: $s"
done

WORK="$(mktemp -d "${TMPDIR:-/tmp}/gate-run.XXXXXX")" || die "mktemp fallito"
VELENO_DIR="$WORK/veleno"
mkdir -p "$VELENO_DIR" "$WORK/gate"
STAMP="$WORK/stamp"
: >"$STAMP"
sleep 1  # mtime a grana di secondo: separa i file scritti prima da quelli del veleno

# 2. veleno
VOUT="$VELENO_DIR/veleno-output.txt" VRC="$VELENO_DIR/veleno-rc"
run_to_files "$VOUT" "$VRC" env VELENO_DIR="$VELENO_DIR" bash -o pipefail -c "$POISON"
vrc="$(read_rc "$VRC" veleno)" || exit 3

if [[ "$vrc" == 0 ]]; then
  printf 'GATE_RUN: ROSSO il veleno esce verde (exit 0): il gate non boccia la versione rotta\n'
  printf '  output del veleno: %s\n' "$VOUT"
  exit 2
fi
if ! grep -qF -- "$EXPECT" "$VOUT"; then
  printf 'GATE_RUN: ROSSO il veleno è rosso (exit %s) ma senza il marcatore «%s»: rosso per il motivo sbagliato\n' "$vrc" "$EXPECT"
  printf '  output del veleno: %s\n' "$VOUT"
  exit 2
fi

# 3. dove ha scritto il veleno
stray_dir="$(find "$VELENO_DIR" -type f ! -name 'veleno-*' | head -5)"
[[ -z "$stray_dir" ]] || die "il veleno ha scritto file senza prefisso veleno- in VELENO_DIR: $stray_dir"
stray_cwd="$(find . \( -name .git -o -name node_modules \) -prune -o -type f -newer "$STAMP" ! -name 'veleno-*' -print 2>/dev/null | head -5)"
[[ -z "$stray_cwd" ]] || die "file cambiati nella cartella corrente durante il veleno (solo veleno-* ammessi): $stray_cwd"

# 4. gate vero
GOUT="$WORK/gate/output.txt" GRC="$WORK/gate/rc"
run_to_files "$GOUT" "$GRC" "$@"
grc="$(read_rc "$GRC" gate)" || exit 3

if [[ "$grc" != 0 ]]; then
  printf 'GATE_RUN: ROSSO il gate esce %s (veleno ok: exit %s con «%s»)\n' "$grc" "$vrc" "$EXPECT"
  printf '  output del gate: %s\n' "$GOUT"
  exit 1
fi
if [[ -n "$PASS" ]] && ! grep -qF -- "$PASS" "$GOUT"; then
  printf 'GATE_RUN: ROSSO il gate esce 0 ma senza il marcatore di verde «%s»\n' "$PASS"
  printf '  output del gate: %s\n' "$GOUT"
  exit 1
fi

printf 'GATE_RUN: VERDE veleno rosso (exit %s, «%s»), gate verde\n' "$vrc" "$EXPECT"
rm -rf "$WORK"
exit 0
