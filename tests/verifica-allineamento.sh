#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
for tool in bash python3 git node; do
  command -v "$tool" >/dev/null 2>&1 || { echo "FAIL: $tool mancante" >&2; exit 1; }
done
python3 -c 'import yaml' >/dev/null 2>&1 || { echo "FAIL: PyYAML mancante" >&2; exit 1; }
# Un Python fino alla 3.11: lì argparse toglie «--» da `--motivo=--`, e U04 lo prova sulla CLI vera.
PYTHON_VECCHIO=""
for py in python3.8 python3.9 python3.10 python3.11 /usr/bin/python3; do
  if command -v "$py" >/dev/null 2>&1 && "$py" -c 'import sys; sys.exit(0 if (3, 8) <= sys.version_info[:2] <= (3, 11) else 1)' 2>/dev/null; then
    PYTHON_VECCHIO=$(command -v "$py"); break
  fi
done
[[ -n "$PYTHON_VECCHIO" ]] || { echo "FAIL: serve un Python dalla 3.8 alla 3.11 per U04 (il motivo «--» sui Python vecchi)" >&2; exit 1; }
echo "PYTHON_VECCHIO=$PYTHON_VECCHIO"
# Il pannello /dafare si prova con Claude Code vero (validate, test, claude -p): senza, il gate fallisce.
command -v claude >/dev/null 2>&1 || {
  echo "FAIL: claude mancante: il gate prova il pannello /dafare con claude plugin validate, claude plugin test e claude -p" >&2
  exit 1
}

FIXTURE=$(mktemp -d "${TMPDIR:-/tmp}/arturo-allineamento.XXXXXX")
trap 'rm -rf "$FIXTURE"' EXIT
# Su Windows Chrome con uno USERPROFILE di prova non apre la porta di debug (W13): prova_pagina.js
# gli ridà quello vero. Il suo profilo resta comunque nella cartella di prova (--user-data-dir).
export ARTURO_USERPROFILE_VERO="${USERPROFILE:-}"
HOME="$FIXTURE/home"
export HOME USERPROFILE="$HOME" XDG_CACHE_HOME="$FIXTURE/cache" TMPDIR="$FIXTURE/tmp" PYTHONDONTWRITEBYTECODE=1
# W13: nel gate la prova nel browser non salta. Senza Chrome o node 22 il gate è rosso.
export ARTURO_PROVA_BROWSER=obbligatoria
# Il gate non manda mai niente al server vero della telemetria. I banchi M la riaccendono verso un
# server finto su 127.0.0.1.
export ARTURO_TELEMETRIA=0
# I banchi delle guardie in background (session-start.sh) non partono dentro le prove: ogni
# session-start di un banco li lancerebbe in una HOME finta.
export ARTURO_BANCHI_AVVIO=0
mkdir -p "$HOME" "$TMPDIR"
# Nella copia entrano .git e i file che git vede (tracciati e nuovi non ignorati), come in un clone
# pulito con le modifiche in corso. Con `cp -R` entravano anche cache/ e data/ della macchina: il
# 19/10/2026 una coda di telemetria vecchia ha fatto rosso GS06 e un .pyc dello strato tolto I03.
python3 - "$ROOT" "$HOME/.claude" <<'PY'
import os, shutil, stat, subprocess, sys
radice, copia = sys.argv[1:3]
git = os.path.join(radice, ".git")


def socket(cartella, nomi):  # fsmonitor--daemon.ipc: un socket non si copia
    return [n for n in nomi if stat.S_ISSOCK(os.lstat(os.path.join(cartella, n)).st_mode)]


if os.path.isdir(git):
    shutil.copytree(git, os.path.join(copia, ".git"), symlinks=True, ignore=socket)
else:  # worktree: .git è un file che punta alla cartella vera
    os.makedirs(copia, exist_ok=True)
    shutil.copy2(git, os.path.join(copia, ".git"))
elenco = subprocess.run(["git", "-C", radice, "ls-files", "-z", "-co", "--exclude-standard"],
                        capture_output=True, check=True).stdout.decode("utf-8")
for rel in filter(None, elenco.split("\0")):
    origine = os.path.join(radice, rel)
    if not os.path.lexists(origine):  # tracciato ma cancellato nel tree
        continue
    dest = os.path.join(copia, rel)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.copy2(origine, dest, follow_symlinks=False)
PY
REPO="$HOME/.claude"

BANCHI=(
  test-block-dangerous-falsi-positivi.py
  test-web-egress-guard.py
  test_bash_dispatcher_review.py
  test_bash_dispatcher_secrets.py
  test_permissivita_2026_09_08.py
  test_allineamento.py
  test_revisione_high.py
  test_revisione_medium.py
  test_revisione_low.py
  test_completezza.py
  test_prodotto.py
  test_revisione_2026_09_30.py
  test_todo.py
  test_pannello.py
  test_web.py
  test_revisione_ciclo5.py
  test_mod_portati.py
  test_guardie_involucri.py
  test_aggiorna_sicuro.py
  test_aggiorna_copia.py
  test_segnala.py
  test_mod_skill.py
  test_telemetria.py
  test_guardie_minori.py
  test_deriva.py
  test_deriva_allineata.py
  test_personale.py
  test_config_2026_10_15.py
  test_guardie_unite.py
  test_heredoc.py
  test_heredoc_confini.py
  test_gate_commit.py
  test_memoria.py
  test_fine_inizio.py
  test_script.py
  test_guardie_rotte.py
  test_review_struttura.py
  test_aggiorna_indietro.py
  test_diagnosi.py
  test_scheda.py
  test_hook_utf8.py
  test_autoaggiorna.py
  test_aggiorna_firmato.py
  test_igiene.py
  test_guardie_sicurezza.py
  test_segnalazioni_2026_10_19.py
  test_config_2026_10_19.py
  test_telemetria_monitor_2026_10_19.py
  test_telemetria_versione_2026_10_19.py
  test_guardie_uniche_2026_10_19.py
  test_node_assente_2026_10_19.py
  test_guardie_uniche_2026_10_19.py
)
for test in "${BANCHI[@]}"; do
  python3 -B "$REPO/tests/$test" --repo "$REPO"
done

# Il minimo dichiarato è Python 3.8: la CLI e la pagina girano anche con quello. I banchi
# lanciano la CLI con l'interprete che li esegue (sys.executable).
PY38_BANCHI=(test_autoaggiorna.py test_aggiorna_firmato.py test_review_struttura.py test_todo.py test_web.py test_segnala.py test_telemetria.py test_deriva.py test_deriva_allineata.py test_personale.py test_memoria.py test_fine_inizio.py test_script.py test_guardie_unite.py test_heredoc.py test_heredoc_confini.py test_diagnosi.py test_hook_utf8.py test_scheda.py)
PY38=$(command -v python3.8 || true)
if [[ -n "$PY38" ]]; then
  for test in "${PY38_BANCHI[@]}"; do
    "$PY38" -B "$REPO/tests/$test" --repo "$REPO"
  done
else
  echo "NOTA: python3.8 assente, todo e pagina provati solo con $(python3 --version 2>&1)"
fi

# Controprove: ogni riga e' «banco ref [radice]». Il banco gira sulla base `ref` estratta con
# git archive e deve dichiararla discriminante. Con «radice» il banco riceve il repository vero
# e la base se la estrae da solo. Ogni ciclo aggiunge le sue righe in coda.
BASELINE=(
  # Revisioni fino al 29/9/2026: la base e' ee10fc6.
  "test-web-egress-guard.py ee10fc6 radice"
  "test-block-dangerous-falsi-positivi.py ee10fc6"
  "test_bash_dispatcher_review.py ee10fc6"
  "test_bash_dispatcher_secrets.py ee10fc6"
  "test_permissivita_2026_09_08.py ee10fc6"
  "test_allineamento.py ee10fc6"
  "test_revisione_high.py ee10fc6"
  "test_revisione_medium.py ee10fc6"
  "test_revisione_low.py ee10fc6"
  "test_completezza.py ee10fc6"
  "test_prodotto.py ee10fc6"
  # Revisione del 30/9/2026: 86ba137, l'ultimo dev prima delle correzioni.
  "test_revisione_2026_09_30.py 86ba137"
  # Archivio dei todo (3/10/2026): b8eff39, l'ultimo dev prima della CLI.
  "test_todo.py b8eff39"
  # Pannello dei todo (3/10/2026): fc6459f, l'ultimo dev prima del ciclo 1.5 e del pannello.
  "test_pannello.py fc6459f"
  # La pagina web dei todo (3/10/2026): 6ef1c0c, l'ultimo commit prima del ciclo 3.
  "test_web.py 6ef1c0c"
  # La revisione del ciclo 5 (3/10/2026): 81431a2, il commit subito prima delle correzioni. Il banco
  # conta un rosso solo se l'AssertionError comincia con il codice del controllo: un file o un
  # comando assente sulla base non prova niente. Le controprove dei cicli di correzione usano
  # questa regola e il commit subito prima della correzione.
  "test_revisione_ciclo5.py 81431a2"
  # I mod portati dalla config dell'autore (9/10/2026): cddcb10, l'ultimo dev prima del porting.
  "test_mod_portati.py cddcb10"
  # Guardie e forme travestite (9/10/2026): bb19ef9, il main della review.
  "test_guardie_involucri.py bb19ef9"
  # /aggiorna e /inizio che falliscono in modo sicuro (9/10/2026): bb19ef9, l'ultimo dev prima della
  # correzione. Regola del ciclo 5: un rosso conta solo col codice del controllo.
  "test_aggiorna_sicuro.py bb19ef9"
  # /aggiorna nella copia di prova (12/10/2026): 0aee68c, il main su cui si sono rotti i file in uso.
  "test_aggiorna_copia.py 0aee68c"
  # /segnala (13/10/2026): 75c8e23, l'ultimo main prima del comando.
  "test_segnala.py 75c8e23"
  # Telemetria minima e segnalazioni dirette (13/10/2026): db96709, il main di /segnala.
  "test_telemetria.py db96709"
  # I finding minori della review delle guardie (13/10/2026): 69d7365, l'ultimo dev prima delle correzioni.
  "test_guardie_minori.py 69d7365"
  # Arturo convive con la config personale (14/10/2026): f750408, l'ultimo dev prima di deriva e personale/.
  "test_deriva.py f750408"
  "test_personale.py f750408"
  # Revisione della config del 15/10/2026: 842b06f, l'ultimo dev prima delle correzioni.
  "test_config_2026_10_15.py 842b06f"
  # La memoria facoltativa (15/10/2026): cbd8305, l'ultimo dev prima del lotto memoria.
  "test_memoria.py cbd8305"
  # Mod e skill portati dalla config dell'autore (15/10/2026): cbd8305, la base dei lotti.
  "test_mod_skill.py cbd8305"
  # Ciclo di sessione di /fine e /inizio sopra i todo (15/10/2026): cbd8305, l'ultimo dev prima del lotto.
  "test_fine_inizio.py cbd8305"
  # Gli script portati dalla config dell'autore (15/10/2026): cbd8305, l'ultimo dev prima del porting.
  "test_script.py cbd8305"
  # Guardie unite alla config dell'autore (15/10/2026): cbd8305, l'ultimo dev prima del lotto.
  "test_guardie_unite.py cbd8305"
  # Un solo modulo per gli heredoc delle quattro guardie (15/10/2026): 62dfb51, l'ultimo dev prima del modulo.
  "test_heredoc.py 62dfb51"
  # Confini degli heredoc, separazione nella copia di prova, impostazioni (review del 15/10/2026): 7c8e0a0.
  "test_heredoc_confini.py 7c8e0a0"
  # Gate dei commit (banchi dell'autore): il gate di Arturo era gia' allineato in f2c433e,
  # quindi la controprova e' 842b06f, l'ultimo dev prima di quell'allineamento.
  "test_gate_commit.py 842b06f"
  # Finding di struttura della review del 15/10/2026 (#3377): 4515e63, l'ultimo dev prima delle correzioni.
  "test_guardie_rotte.py 4515e63"
  "test_review_struttura.py 4515e63"
  "test_aggiorna_indietro.py 4515e63"
  # Titolo e colore della scheda del terminale (16/10/2026): b0ec3ac, l'ultimo dev prima dell'hook.
  "test_scheda.py b0ec3ac"
  # /diagnosi di progetto (16/10/2026): 5fd0443, l'ultimo dev prima di bin/diagnosi.py.
  "test_diagnosi.py 5fd0443"
  # Hook in UTF-8 anche su Windows (16/10/2026, #3423): b0ec3ac, il main v2026-10-16.2.
  "test_hook_utf8.py b0ec3ac"
  # Arturo si aggiorna da solo, solo con rilasci firmati (16/10/2026, #3477): 5d83592, il main v2026-10-16.4.
  "test_autoaggiorna.py 5d83592"
  # Revisione di sicurezza del 16/10/2026 (#3504-#3507): 93f323e, l'ultimo dev prima delle correzioni.
  "test_aggiorna_firmato.py 93f323e"
  "test_igiene.py 93f323e"
  "test_guardie_sicurezza.py 93f323e"
  # Segnalazioni n. 4 e n. 5 del 19/10/2026: 439a92b, l'ultimo dev prima delle correzioni.
  "test_segnalazioni_2026_10_19.py 439a92b"
  # Revisione della config del 19/10/2026: 439a92b, l'ultimo dev prima delle correzioni.
  "test_config_2026_10_19.py 439a92b"
  # Telemetria di Claude Code accesa, guardie su Monitor e onFailure (19/10/2026): 40b26c2, l'ultimo dev prima.
  "test_telemetria_monitor_2026_10_19.py 40b26c2"
  # La telemetria manda il rilascio installato, senza i commit della persona (19/10/2026, #3613): 0c12a5b.
  "test_telemetria_versione_2026_10_19.py 0c12a5b"
  # Guardie uniche fra Arturo e la config di chi lo mantiene (19/10/2026, #3612): dbaefa1, l'ultimo dev prima.
  "test_guardie_uniche_2026_10_19.py dbaefa1"
  # Arturo senza node: la barra e l'avvio lo dicono (19/10/2026): dbaefa1, l'ultimo dev prima.
  "test_node_assente_2026_10_19.py dbaefa1"
  # Guardie uniche fra Arturo e la config di chi lo mantiene (19/10/2026, #3612): dbaefa1, l'ultimo dev prima.
  "test_guardie_uniche_2026_10_19.py dbaefa1"
)
for riga in "${BASELINE[@]}"; do
  read -r test ref modo <<<"$riga"
  base="$FIXTURE/baseline-$ref"
  if [[ ! -d "$base" ]]; then
    mkdir -p "$base"
    git -C "$ROOT" archive "$ref" | tar -x -C "$base"
  fi
  if [[ "${modo:-}" == radice ]]; then
    python3 -B "$REPO/tests/$test" --repo "$ROOT" --baseline-ref "$ref"
  else
    python3 -B "$REPO/tests/$test" --repo "$base" --baseline-ref "$ref"
  fi
done

# Il server della telemetria (server/logica.js) con un archivio e una posta finti.
node "$REPO/server/test.mjs"
# Le query vere (server/archivio.js) su SQLite in memoria: node:sqlite, Node 22 o successivo.
node --no-warnings "$REPO/server/test-sql.mjs"

shells=0
while IFS= read -r -d '' file; do
  bash -n "$REPO/$file"  # ls-files dà path relativi al repository, non alla cartella corrente
  shells=$((shells + 1))
done < <(git -C "$REPO" ls-files -z -- '*.sh')
[[ $shells -gt 0 ]] || { echo "FAIL: nessun file shell" >&2; exit 1; }

python3 - "$REPO" "$FIXTURE/pycache" <<'PY'
import pathlib
import py_compile
import sys
root = pathlib.Path(sys.argv[1])
cache = pathlib.Path(sys.argv[2])
files = list(root.glob("**/*.py"))
if not files:
    raise SystemExit("FAIL: nessun file Python")
for index, path in enumerate(files):
    py_compile.compile(str(path), cfile=str(cache / f"{index}.pyc"), doraise=True)
print(f"PY_COMPILE={len(files)}")
PY

js=0
while IFS= read -r -d '' file; do
  node --check "$REPO/$file"
  js=$((js + 1))
done < <(git -C "$REPO" ls-files -z -- '*.js' '*.mjs')
[[ $js -gt 0 ]] || { echo "FAIL: nessun file JavaScript" >&2; exit 1; }

bash "$REPO/skills/system-audit/audit.sh" --strict
printf 'PASS: banchi=%s shell=%s js=%s\n' "${#BANCHI[@]}" "$shells" "$js"
