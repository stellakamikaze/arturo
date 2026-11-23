#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
# Una sessione di Claude col plugin esporta ARTURO_CODICE in ogni comando: i banchi lo erediterebbero e
# crederebbero di girare col plugin anche nelle installazioni a clone (10/11/2026). Chi lo vuole lo mette lui.
# Esce anche la sua cartella bin dal PATH: un banco che chiama `arturo` per nome (hooks/inject-now.sh, i
# comandi) proverebbe il codice del plugin installato, non questo repository (#5206).
if [[ -n "${ARTURO_CODICE:-}" ]]; then
  PATH=$(printf '%s' "$PATH" | tr ':' '\n' | { grep -vxF -e "${ARTURO_CODICE%/}/bin" -e "${ARTURO_CODICE%/}/bin/" || true; } | paste -sd: -)
  export PATH
fi
unset ARTURO_CODICE CLAUDE_PLUGIN_ROOT CLAUDE_ENV_FILE
# --rossi rifà solo i lavori rossi dell'ultimo giro (tests/esegui_gate.py); --toccati fa girare solo i
# lavori con una fonte fra i file cambiati. Servono a chi corregge, e stampano PARZIALE perché un
# rilascio vuole un giro completo verde (docs/manutenzione.md). Le controprove con banco, fonti e base
# uguali all'ultima verde si saltano: --rilascio, o ARTURO_GATE_RILASCIO=1, le rifà tutte.
PARZIALE_MODO=""
RILASCIO=""
for arg in "$@"; do
  case "$arg" in
    --rossi|--toccati) PARZIALE_MODO=$arg ;;
    --rilascio) RILASCIO=--rilascio ;;
    *) echo "FAIL: argomento sconosciuto $arg (--rossi, --toccati, --rilascio)" >&2; exit 2 ;;
  esac
done
[[ "${ARTURO_GATE_RILASCIO:-}" == 1 ]] && RILASCIO=--rilascio
for tool in bash python3 git node; do
  command -v "$tool" >/dev/null 2>&1 || { echo "FAIL: $tool mancante" >&2; exit 1; }
done
python3 -c 'import yaml' >/dev/null 2>&1 || { echo "FAIL: PyYAML mancante" >&2; exit 1; }
# Un Python fino alla 3.11: lì argparse toglie "--" da `--motivo=--`, e U04 lo prova sulla CLI vera.
PYTHON_VECCHIO=""
for py in python3.8 python3.9 python3.10 python3.11 /usr/bin/python3; do
  if command -v "$py" >/dev/null 2>&1 && "$py" -c 'import sys; sys.exit(0 if (3, 8) <= sys.version_info[:2] <= (3, 11) else 1)' 2>/dev/null; then
    PYTHON_VECCHIO=$(command -v "$py"); break
  fi
done
[[ -n "$PYTHON_VECCHIO" ]] || { echo "FAIL: serve un Python dalla 3.8 alla 3.11 per U04 (il motivo \"--\" sui Python vecchi)" >&2; exit 1; }
echo "PYTHON_VECCHIO=$PYTHON_VECCHIO"
# Il minimo dichiarato, Python 3.8 (PY38_BANCHI più sotto). Senza python3.8 nel PATH vale quello di uv
# (uv python install 3.8): si cerca qui, prima che HOME diventi quella di prova.
PY38=$(command -v python3.8 || true)
[[ -n "$PY38" ]] || ! command -v uv >/dev/null 2>&1 || PY38=$(uv python find 3.8 2>/dev/null || true)
# Il pannello /dafare si prova con Claude Code vero (validate, test, claude -p): senza, il gate fallisce.
command -v claude >/dev/null 2>&1 || {
  echo "FAIL: claude mancante: il gate prova il pannello /dafare con claude plugin validate, claude plugin test e claude -p" >&2
  exit 1
}

# Un solo gate completo per macchina (#4360): due gate insieme si pestano e danno rossi che da soli
# passano. Il lucchetto si prende prima di cambiare HOME e TMPDIR, così due gate vedono lo stesso.
# shellcheck source=../bin/gate-lucchetto.sh
source "$ROOT/bin/gate-lucchetto.sh"
gate_lucchetto_prendi "${ARTURO_GATE_LUCCHETTO:-${TMPDIR:-/tmp}/arturo-gate.lucchetto}" \
  "$ROOT ($(git -C "$ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?'))" || exit 1
trap gate_lucchetto_lascia EXIT
trap 'exit 130' INT TERM

FIXTURE=$(mktemp -d "${TMPDIR:-/tmp}/arturo-allineamento.XXXXXX")
trap 'rm -rf "$FIXTURE"; gate_lucchetto_lascia' EXIT
# Su Windows Chrome con uno USERPROFILE di prova non apre la porta di debug (W13): prova_pagina.js
# gli ridà quello vero. Il suo profilo resta comunque nella cartella di prova (--user-data-dir).
export ARTURO_USERPROFILE_VERO="${USERPROFILE:-}"
# tests/esegui_gate.py ne ricava il sito utente di Python, che su un Mac sta sotto la HOME e nella HOME
# finta sparirebbe: con PyYAML installato solo lì quattro banchi uscivano rossi (22/11/2026, #6426, GS11).
export ARTURO_GATE_HOME_VERA="$HOME"
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
# Un controllo che Windows non permette di provare (link simbolici senza la Modalità sviluppatore,
# #4383) esce come SALTO col suo codice: tests/salti_windows.py lo scrive qui, e l'esito lo conta.
export ARTURO_SALTI="$FIXTURE/salti.txt"
: > "$ARTURO_SALTI"
mkdir -p "$HOME" "$TMPDIR"
# La copia del repository per la coda del gate (sintassi, audit): la stessa che ogni worker di
# tests/esegui_gate.py si fa per i banchi, coi soli file che git vede (19/10/2026, GS06 e I03).
python3 -B "$ROOT/tests/esegui_gate.py" copia "$ROOT" "$HOME/.claude"
REPO="$HOME/.claude"

BANCHI=(
  test_ritratto_2026_11_01.py
  # Il contesto del progetto e la sintesi della testata di Volta (12/11/2026, TC01-TC06).
  test_testata_contesto_2026_11_12.py
  test_setup_ritratto_2026_11_01.py
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
  test_heredoc_backtick.py
  test_lotto_2026_10_20.py
  test_falsi_allarmi_2026_10_20.py
  test_conflitto_telemetria_2026_10_20.py
  test_argv_lista_2026_10_21.py
  test_moduli_2026_10_21.py
  test_unisci_settings_2026_10_22.py
  test_setup_invito_2026_10_23.py
  test_reinstalla_2026_10_23.py
  test_copie_2026_10_23.py
  test_telemetria_f1_2026_10_24.py
  test_archivi_aggiorna_2026_10_26.py
  test_segnalazioni_2026_10_27.py
  test_computer_club_2026_10_28.py
  test_computer_club_2026_10_28b.py
  test_rilascio_2026_11_02.py
  test_dispatcher_locale_2026_10_30.py
  test_protect_locale_2026_10_30.py
  test_hook_sessione_2026_10_30.py
  test_sync_merge_2026_10_30.py
  test_fine_profilo_2026_10_30.py
  test_fine_coda_2026_10_30.py
  test_fonte_task_2026_10_30.py
  test_progetti_memoria_2026_11_11.py
  # arturo progetti rinomina: un progetto cambia nome in un passo, il nome vecchio resta valido (proposta n. 90, #6095).
  test_rinomina_2026_11_19.py
  # arturo progetti unisci: due progetti doppioni diventano uno, con copia di sicurezza prima (#6187).
  test_unisci_2026_11_20.py
  # arturo progetti elimina e nuovo (22/11/2026, #6432): Miscellanea, il rifiuto dei nomi presi, il JSON per Volta (EL01-).
  test_elimina_nuovo_2026_11_22.py
  test_strati_2026_11_02.py
  test_impacchetta_2026_11_03.py
  test_lavoro_proprio_2026_10_31.py
  test_gate_lucchetto_2026_10_31.py
  test_revisione_2026_11_01.py
  test_segnalazioni_2026_11_02.py
  test_monitor_ponti_2026_11_02.py
  test_monitor_giro_2026_11_03.py
  test_viste_allineate_2026_11_03.py
  test_gws_token_health.py
  test_telemetria_fase2_2026_11_03.py
  test_telemetria_copia_fuori_2026_11_03.py
  test_amend_2026_11_03.py
  test_testata_banchi_2026_11_03.py
  test_rotazione_2026_11_03.py
  test_segnalazioni_2026_11_03.py
  test_segnalazioni_2026_11_04.py
  test_gate_snello_2026_11_03.py
  test_mod_passo2_2026_11_03.py
  test_claude_md_conferma_2026_11_03.py
  test_scansione_fallita_2026_11_03.py
  test_scansione_causa_2026_11_21.py
  test_regola_tre_guardie_2026_11_21.py
  test_finestre_windows_2026_11_04.py
  test_sportello_2026_11_04.py
  # Il contatto di chi segnala (10/11/2026): arturo contatto, prepara e invia, domanda una volta.
  test_contatto_2026_11_10.py
  # Le segnalazioni partono da sole (11/11/2026): manda, interruttore, tetto, avviso una volta.
  test_segnala_auto_2026_11_11.py
  # Gli script si leggono col bash 3.2 del Mac (10/11/2026, segnalazione n. 68).
  test_bash32_2026_11_10.py
  test_humanizer_origine.py
  # Percorsi fra virgolette e alla maniera di Windows nelle guardie (9/11/2026, #5096).
  test_guardie_virgolette_2026_11_09.py
  # Le forme che le guardie leggevano prima del lotto L2 del 7/11 (10/11/2026, #5097).
  test_guardie_regressioni_l2_2026_11_10.py
  # Un solo lettore dei comandi e un solo elenco dei percorsi protetti nelle guardie (10/11/2026, #5122).
  test_guardie_split_unico_2026_11_10.py
  # Il ramo memoria non approva scritture fuori zona, e lo sblocco della config chiede (11/11/2026, #5261).
  test_guardie_memoria_sblocco_2026_11_11.py
  # Le guardie vedono scritture sulla config, heredoc eseguiti e comandi fra virgolette (11/11/2026, #5262).
  test_guardie_cieche_2026_11_11.py
  # Le conferme che non proteggono niente, dal ripasso dei transcript dei 7 giorni (20/11/2026).
  test_attrito_2026_11_20.py
  # I banchi all'avvio giudicano solo i file di Arturo, non gli hook personali (20/11/2026, #5383).
  test_banchi_file_personali_2026_11_20.py
  # La base di Arturo si sceglie solo in deriva.py --base, anche per banchi-avvio.sh (21/11/2026, #6216).
  test_base_arturo_2026_11_21.py
  # Difetti minori su Windows della review del 9/11: servizi di Claude, appunti, wt, codifica (10/11/2026, #5102).
  test_windows_minori_2026_11_10.py
  # /revisione: estratto dei transcript senza l'uscita dei comandi, attriti separati, bozza e registro (17/11/2026).
  test_revisione_2026_11_17.py
  # Le sessioni di prova marcate dal nome prova-: /fine non salva e le elimina (17/11/2026, #5877).
  test_prova_2026_11_17.py
  # La Scoperta v1 dalle versioni dei file (14/11/2026, passo S7, #5615).
  test_scoperta_2026_11_14.py
  # Lo storico delle chat: zip letto senza estrarlo, filtri del ritratto, solo l'indice su disco (15/11/2026, #5700).
  test_storico_2026_11_15.py
  # L'intervista che continua: una domanda al giorno da /inizio, la risposta in memoria col sì (15/11/2026, #5709).
  test_intervista_2026_11_15.py
  # Il fascicolo di un progetto: esporta senza segreti, importa coi testi altrui come dati (15/11/2026, #5710).
  test_fascicolo_2026_11_15.py
  # Gli spazi proposti col segnale, una volta sola, e il nome scelto per Arturo (16/11/2026, Fase F1 e F3, #5711).
  test_spazi_2026_11_16.py
  # Le forme della Scoperta (automazione, sintesi, pagina) e i lavori dello storico che tornano (16/11/2026, Fase D, #5702).
  test_scoperta_forme_2026_11_16.py
  # arturo progetti, portato da herdr: l'elenco dei progetti dalla memoria, per Volta (M3, #5672).
  test_progetti_memoria_2026_11_11.py
  # arturo progetti rinomina: un progetto cambia nome in un passo, il nome vecchio resta valido (proposta n. 90, #6095).
  test_rinomina_2026_11_19.py
  # arturo progetti unisci: due progetti doppioni diventano uno, con copia di sicurezza prima (#6187).
  test_unisci_2026_11_20.py
  # arturo progetti elimina e nuovo (22/11/2026, #6432): Miscellanea, il rifiuto dei nomi presi, il JSON per Volta (EL01-).
  test_elimina_nuovo_2026_11_22.py
  # Il file di sessione ha un solo padrone (C1, 23/11/2026): ogni rottura di scheda_file.py o del verbo fa rosso il suo caso SE.
  test_scheda_file.py
  # La carta di una sessione per la Coda di Volta, ora in Arturo (passo 9, 23/11/2026, #6422).
  test_carta_sessione.py
  # Il salvataggio automatico di una sessione chiusa senza /fine (M4, #5672).
  test_salva_automatico.py
  # Gli eventi della memoria nella telemetria: memoria, richiamo, salvataggio, inizio (M7, #5672).
  test_telemetria_memoria_2026_11_15.py
  # La barra trova node col PATH minimo di ssh, come nelle sessioni che Volta apre su un'altra macchina (15/11/2026).
  test_statusline_path_2026_11_15.py
  # /monitor impara dalle correzioni: segnali, mittenti, regole, sezioni, annullo (17/11/2026).
  test_monitor_impara_2026_11_17.py
  # Il giro quotidiano di /monitor: impronta dei todo, raccolta senza doppioni, cursori, lettore (20/11/2026, #4538).
  test_monitor_giorno_2026_11_20.py
  # La ripartenza di /inizio come dati per la checklist di Volta (17/11/2026, #5910).
  test_ripartenza_2026_11_17.py
  # I testi pubblici dicono cosa c'è nel rilascio (revisione del 22/11/2026, A3 A9 A10, #6418).
  test_testi_pubblici.py
  # L'aspetto della persona in personale/aspetto.json: scheda, barra, /dafare, DERIVA (proposta n. 73, #5432).
  test_aspetto_2026_11_18.py
  # La sandbox di Claude Code come opzione della persona, spenta di default (19/11/2026, #6098).
  test_sandbox_2026_11_19.py
  # Le skill di ruolo (20/11/2026, strati F6, #4536): aggiunte personali col tool Skill e mappa dei ruoli.
  test_ruoli_2026_11_20.py
  # Lo sportello lato client (20/11/2026, #4793): modo log, copie degli ultimi lotti, arturo telemetria dimentica.
  test_telemetria_log_dimentica_2026_11_20.py
  # Le righe per percorso di protect_claude_md.local: stringono, non allentano (21/11/2026, #6278).
  test_protect_percorso_2026_11_21.py
  # Una chiave letta con un glob o con le graffe su cartella e nome arriva alle guardie (21/11/2026, #6279).
  test_glob_segreti_2026_11_21.py
  # Gli aggiramenti delle guardie della revisione del 20/11, rilievi S4-S10 e S13 (21/11/2026, #6259).
  test_aggiramenti_2026_11_21.py
  # Un programma nascosto alle guardie con una parola pericolosa chiede conferma (22/11/2026, #6323).
  test_programmi_nascosti_2026_11_22.py
  # curl e wget in una lista python letterale sono un programma visibile per codice-nascosto (22/11/2026, #6353).
  test_lista_letterale_2026_11_22.py
  # Le guardie di Bash più veloci con gli stessi giudizi: parole lineari, un python3 solo, bytecode (22/11/2026, #6327).
  test_parole_veloci_2026_11_22.py
  # Il pre-filtro del dispatcher di Bash in Python, lineare, e il limite a 1.000.000 di caratteri (22/11/2026, #6327).
  test_prefiltro_python_2026_11_22.py
  # La verifica dei rilasci accetta solo firme SSH (21/11/2026, #6258, rilievo S1 della revisione del 20/11).
  test_firme_ssh_2026_11_21.py
  # Commit e push della coda di /fine passano dal controllo dei segreti (21/11/2026, #6249, rilievi A2 e A3).
  test_fine_coda_segreti_2026_11_21.py
  # Con git -C la guardia dei segreti legge solo i file del git add, e il -C vale solo per il suo git (22/11/2026, #6289).
  test_pathspec_c_2026_11_22.py
  # Il campo if sugli hook che non c'entrano col comando: gws-esito e block-dangerous dopo (22/11/2026, #6327).
  test_hook_if_2026_11_22.py
  # Un /fine su una sessione già chiusa si ferma prima del modello (22/11/2026, #6274, segnalazioni n. 79, 87 e 93).
  test_fine_gia_chiusa_2026_11_22.py
  # L'avviso del sync della config parte solo per i file fuori da data/ e solo a chi li ha toccati (22/11/2026, #6275).
  test_fine_avvisi_2026_11_22.py
  # arturo contesto legge git mentre la fonte esterna dei todo risponde (22/11/2026, #6317).
  test_parallelo_2026_11_22.py
  # Le letture della FASE 4 di /inizio partono insieme con arturo apertura (22/11/2026, #6368).
  test_apertura_2026_11_22.py
  # I bug medi A4-A10 della revisione del 20/11 (22/11/2026, #6250): lucchetto della coda, salvataggio dopo un
  # /fine a metà, sblocchi fuori dai progetti, a capo Windows, /arturo:fine, pulizia plugin, cause del pull.
  test_revisione_medi_2026_11_22.py
  # I bug bassi 11-21 della revisione del 20/11 (22/11/2026, #6389): stash con lo stage, CLAUDE.md nella pulizia,
  # falso ripristino, lucchetto dei todo, hook della memoria, unisci e migra con ritorno, handoff automatici,
  # temporanei unici, home con spazi, conferme della telemetria.
  test_revisione_bassi_2026_11_22.py
  # I dati di transito sul ramo sync (23/11/2026, #6424, D5): giro, lucchetto, minuto, segreti, merge union, coda.
  test_sync_transito.py
  # Un processo per evento: hooks/hub.py lancia insieme gli hook Python e ne fonde le uscite (23/11/2026, #6492).
  test_hub.py
)
# Sotto carico questi danno rossi che da soli passano (T22, SM04: il motivo del lucchetto, #4360) o
# aprono il browser: girano dopo i lavori in parallelo, uno alla volta.
IN_FILA=(
  test_todo.py
  test_catena_2026_11_03.py
  test_pannello.py
  test_web.py
  test_revisione_ciclo5.py
  test_schede_mac_2026_10_29.py
  # Strati F3 (5/11/2026, #4533): la CLI vera di Claude Code installa e aggiorna il plugin in sandbox.
  test_fiducia_2026_11_05.py
  # Strati F4 (5/11/2026, #4534): arturo migra dal clone al plugin, con la CLI vera e il ritorno indietro.
  test_migra_2026_11_05.py
  # Strati F5 (5/11/2026, #4535): le skill omonime della persona si dichiarano in personale/sostituzioni.txt.
  test_sostituzioni_2026_11_05.py
  # #4874 (6/11/2026): col plugin le regole di /setup che il CLAUDE.md ripete si elencano e si tolgono a richiesta.
  test_regole_doppie_2026_11_06.py
  # #4860 (6/11/2026): col plugin avvio e barra dicono che c'è un rilascio nuovo.
  test_avviso_plugin_2026_11_06.py
  # Col plugin la chiusura installa il rilascio firmato (10/11/2026): misura un'attesa, gira in fila.
  test_chiusura_plugin_2026_11_10.py
  # #5880 (17/11/2026): senza chiave SSH su GitHub install e update ripiegano su HTTPS; la regola autoMode.
  test_aggiorna_https_2026_11_17.py
  # Review del 7/11/2026, lotto L2 (#4972): le guardie, dal dispatcher vero.
  test_revisione_2026_11_07.py
  # Il tetto di 25 secondi per le guardie (22/11/2026, #6363): misura decine di secondi, gira in fila.
  test_tetto_guardie_2026_11_22.py
  # Le guardie in tempo lineare sui comandi ripetuti (22/11/2026, #6363): misura i tempi, gira in fila.
  test_guardie_lineari_2026_11_22.py
  # Il tetto di 7,5 secondi per l'avvio e il fetch staccato (22/11/2026, #6370): misura secondi, gira in fila.
  test_avvio_tetto_2026_11_22.py
  # Il dispatcher di Bash in Python dentro hub (23/11/2026, #6492): DP02 misura il tetto di 25 s, gira in fila.
  test_dispatcher.py
)

# Il minimo dichiarato è Python 3.8: la CLI e la pagina girano anche con quello. I banchi
# lanciano la CLI con l'interprete che li esegue (sys.executable).
PY38_BANCHI=(test_autoaggiorna.py test_aggiorna_firmato.py test_review_struttura.py test_todo.py test_web.py test_segnala.py test_telemetria.py test_deriva.py test_deriva_allineata.py test_personale.py test_memoria.py test_fine_inizio.py test_script.py test_guardie_unite.py test_heredoc.py test_heredoc_confini.py test_diagnosi.py test_hook_utf8.py test_scheda.py test_schede_mac_2026_10_29.py test_ritratto_2026_11_01.py test_setup_ritratto_2026_11_01.py test_telemetria_fase2_2026_11_03.py test_amend_2026_11_03.py test_sportello_2026_11_04.py test_contatto_2026_11_10.py test_bash32_2026_11_10.py test_progetti_memoria_2026_11_11.py test_rinomina_2026_11_19.py test_unisci_2026_11_20.py test_scheda_file.py test_carta_sessione.py test_storico_2026_11_15.py test_intervista_2026_11_15.py test_fascicolo_2026_11_15.py test_spazi_2026_11_16.py test_scoperta_forme_2026_11_16.py test_ripartenza_2026_11_17.py test_telemetria_log_dimentica_2026_11_20.py test_fine_gia_chiusa_2026_11_22.py test_fine_avvisi_2026_11_22.py)
if [[ -z "$PY38" && -n "$RILASCIO" ]]; then
  # Un rilascio prova il minimo dichiarato: senza 3.8 i suoi banchi salterebbero in silenzio (review del
  # 7/11/2026, finding 91).
  echo "FAIL: il gate del rilascio vuole python3.8 per i ${#PY38_BANCHI[@]} banchi del minimo dichiarato: uv python install 3.8" >&2
  exit 1
fi
[[ -n "$PY38" ]] || echo "NOTA: python3.8 assente, todo e pagina provati solo con $(python3 --version 2>&1)"

# Controprove: ogni riga e' "banco ref [radice]". Il banco gira sulla base `ref` estratta con
# git archive e deve dichiararla discriminante. Con "radice" il banco riceve il repository vero
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
  # Il profilo del Terminale di macOS senza processo nel titolo (29/10/2026): 3b1e66f, prima di bin/schede_mac.py.
  "test_schede_mac_2026_10_29.py 3b1e66f"
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
  # Backtick negli heredoc (#3584): 3211b74, l'ultimo dev prima di 439a92b.
  "test_heredoc_backtick.py 3211b74"
  # Lotto del 20/10/2026 (#3632 #3552 #3596 #3587 #3594 #3595 #3524 #3525 #3637): 0936b4c, l'ultimo dev prima.
  "test_lotto_2026_10_20.py 0936b4c"
  # Falsi allarmi delle guardie su mktemp e json.load (20/10/2026, #3700): 3184831, l'ultimo dev prima.
  "test_falsi_allarmi_2026_10_20.py 3184831"
  # Il conflitto di un aggiornamento dice quale file blocca (20/10/2026, #3589): 3184831, l'ultimo dev prima.
  "test_conflitto_telemetria_2026_10_20.py 3184831"
  # Arturo usa Melchior, la memoria della config di chi lo mantiene (20/10/2026): aabe7fa, l'ultimo dev prima.
  "test_memoria.py aabe7fa"
  # Un invio con curl in una lista di argomenti python chiede (21/10/2026, #3645): 6e0b36b, l'ultimo dev prima.
  "test_argv_lista_2026_10_21.py 6e0b36b"
  # Un modulo python non conta come dominio esterno (21/10/2026, #3720): d0a5ce6, l'ultimo dev prima.
  "test_moduli_2026_10_21.py d0a5ce6"
  # L'aggiornamento unisce settings.json come JSON (22/10/2026): dbb37e7, il main v2026-10-22.
  "test_unisci_settings_2026_10_22.py dbb37e7"
  # L'avvio invita a finire /setup (23/10/2026): f4ae0aa, l'ultimo dev prima.
  "test_setup_invito_2026_10_23.py f4ae0aa"
  # La reinstallazione riporta memoria, todo e scelte della persona (#3825): f4ae0aa, la regressione.
  "test_reinstalla_2026_10_23.py f4ae0aa"
  # Le copie dello stesso testo (cancellazione, lista del ripristino) restano uguali (#3852): f4ae0aa.
  "test_copie_2026_10_23.py f4ae0aa"
  # Telemetria F1, lato client: numeri veri e fughe chiuse (24/10/2026): 8c7b6f7, il dev prima della fase.
  "test_telemetria_f1_2026_10_24.py 8c7b6f7"
  # Gli archivi della persona non fermano l'aggiornamento (segnalazione n. 14): 7337350, il dev prima.
  "test_archivi_aggiorna_2026_10_26.py 7337350"
  # Segnalazioni n. 15 e n. 16 del 26/10/2026 (heredoc nel worktree, sudo col prefisso !) e codice
  # nel messaggio di /segnala quando il server non accetta (27/10/2026): 32a574e, il dev prima.
  "test_segnalazioni_2026_10_27.py 32a574e"
  # Segnalazioni n. 36-38, 40 e 41 (classificatore della modalità auto: comando con !, sblocco alla
  # persona, brew, LaunchAgent fuori da iCloud, cartella fuori sessione, /chrome), 2/11/2026: 8b141c0.
  "test_segnalazioni_2026_11_02.py 8b141c0"
  # Le domande della sera del Computer Club del 27/10/2026 (quota in parole, /guidami con la quota, concetti,
  # numero della segnalazione, /setup che presenta /dafare): 443b191, il dev prima.
  "test_computer_club_2026_10_28.py 443b191"
  # Il secondo giro (/dafare apre una sessione, /segnala stato, il numero delle segnalazioni in differita,
  # l'avviso prima di un ultracode, /proponi): 5bdec48, il dev prima.
  "test_computer_club_2026_10_28b.py 5bdec48"
  # I ritocchi prima del rilascio del 2/11/2026 (/setup sotto 30 KB, testi dei comandi nuovi, titolo
  # atteso del tasto o): 60b7d8d, il dev prima.
  "test_rilascio_2026_11_02.py 60b7d8d"
  # Migrazione della config di Federico, F0 L1-L2 (30/10/2026): guardie e protect personali da .local,
  # sblocchi per sessione, sync che tiene i merge. 749e18d, il dev prima; i banchi leggono la base con git show.
  "test_dispatcher_locale_2026_10_30.py 749e18d radice"
  "test_protect_locale_2026_10_30.py 749e18d radice"
  "test_hook_sessione_2026_10_30.py 749e18d radice"
  "test_sync_merge_2026_10_30.py 749e18d radice"
  # F0 L3 (30/10/2026): profilo degli handoff, celle, gitleaks, idee in memoria, retention con elenco.
  "test_fine_profilo_2026_10_30.py 0a4f73f radice"
  "test_fine_coda_2026_10_30.py 875109c radice"
  # F0 L4 (30/10/2026): la fonte dei task da bin/fonte-task.local e gli argomenti di /inizio su stdin.
  "test_fonte_task_2026_10_30.py ba61272 radice"
  # Strati F1 (2/11/2026): guardie, avvio e telemetria trovano il codice fuori da ~/.claude. 94db031, il dev prima.
  "test_strati_2026_11_02.py 94db031 radice"
  # Strati F2 (3/11/2026): il plugin generato dal repository. c247fed, il dev prima del generatore.
  "test_impacchetta_2026_11_03.py c247fed"
  # Un solo gate completo per macchina (31/10/2026, #4360): 5122a03, il dev prima del lucchetto.
  "test_gate_lucchetto_2026_10_31.py 5122a03 radice"
  # /monitor in Arturo, Fase 1 (2/11/2026): i ponti della persona. 2fe4037, il dev prima di bin/monitor.
  "test_monitor_ponti_2026_11_02.py 2fe4037"
  # Telemetria fase 2 (3/11/2026, #4540): durata, turni e skill alla chiusura. c5536a7, il dev prima.
  "test_telemetria_fase2_2026_11_03.py c5536a7"
  # Testata di Arturo e banchi silenziosi (3/11/2026): c247fed, il dev prima.
  "test_testata_banchi_2026_11_03.py c247fed"
  # Rotazione automatica della sessione (3/11/2026): fine leggero e marca di /inizio. bf394ad, il dev
  # prima della rotazione.
  "test_rotazione_2026_11_03.py bf394ad radice"
  # Segnalazioni n. 45 e n. 46 (3/11/2026): zsh come bash da $CLAUDE_ENV_FILE, nessun mod
  # che cambia il comando (riscrivi-bash uscito col passo 2 dei mod), /inizio che controlla da dove
  # parte la copia separata. 9c6a0e6, il ramo prima.
  "test_segnalazioni_2026_11_03.py 9c6a0e6"
  # Segnalazione n. 51 (4/11/2026, #4768): agente ripreso fuori dalla sua copia separata.
  # c9ee540, il dev prima.
  "test_segnalazioni_2026_11_04.py c9ee540"
  # Il gate snello (3/11/2026): tests/esegui_gate.py in parallelo, tutti i rossi in un giro, --rossi.
  # 177852f, il ramo prima.
  "test_gate_snello_2026_11_03.py 177852f"
  # Passo 2 dei mod (3/11/2026, #4619): escono riscrivi-bash e gws, l'hook gws-esito.py e il dispatcher che legge il
  # marcatore dell'avvio. 08d09cf, il dev prima.
  "test_mod_passo2_2026_11_03.py 08d09cf"
  # Una conferma sola per il CLAUDE.md (3/11/2026, #4473): f99d781, il commit padre.
  "test_claude_md_conferma_2026_11_03.py f99d781"
  # La scansione dei segreti dice perché non parte (4/11/2026, #4472): e2106f0, il dev prima.
  "test_scansione_fallita_2026_11_03.py e2106f0"
  # La scansione dei segreti che non parte registra la causa (21/11/2026, #5761): e794f3e, il dev prima.
  "test_scansione_causa_2026_11_21.py e794f3e"
  # exfil-guard, comms-guard e data-guard dicono la regola che chiede (21/11/2026, #5762): d4c7fa4, il dev prima.
  "test_regola_tre_guardie_2026_11_21.py d4c7fa4"
  # La catena dei todo e la riga di stato (3/11/2026, #3888): acb4a39, il dev prima.
  "test_catena_2026_11_03.py acb4a39"
  # Le tre viste dei todo allineate (3/11/2026, #3868): su acb4a39 la pagina non ha dopo.
  "test_viste_allineate_2026_11_03.py acb4a39"
  # La telemetria tace da una copia fuori dalla config (3/11/2026): 9248ea9, il dev prima.
  "test_telemetria_copia_fuori_2026_11_03.py 9248ea9"
  # /monitor in Arturo, primo avvio (3/11/2026, #4538): fonti scelte, schema delle righe, fingerprint e
  # cursori generici. 9248ea9, il dev prima.
  "test_monitor_giro_2026_11_03.py 9248ea9"
  # Lanci staccati senza finestre su Windows (4/11/2026): efaa296, il dev prima.
  "test_finestre_windows_2026_11_04.py efaa296"
  # Lo sportello delle segnalazioni (4/11/2026, #3925): ricevuta, pacchetto, redazione, risposta. fa14218, il dev prima.
  "test_sportello_2026_11_04.py fa14218"
  # Il contatto di chi segnala (10/11/2026): arturo contatto non c'è. 3954f1d, il dev prima.
  "test_contatto_2026_11_10.py 3954f1d"
  # Le segnalazioni automatiche (11/11/2026): manda e l'interruttore non ci sono. 8709365, il dev prima.
  "test_segnala_auto_2026_11_11.py 8709365"
  # Il heredoc dentro <(...) di audit.sh (10/11/2026, n. 68): a7c5162, il dev prima.
  "test_bash32_2026_11_10.py a7c5162"
  # Strati F3 (5/11/2026, #4533): MANIFEST firmato, catalogo con lo sha, /aggiorna che verifica il tag.
  # 809868a, il dev prima.
  "test_fiducia_2026_11_05.py 809868a"
  # Strati F4 (5/11/2026, #4534): arturo migra non c'è. 53450c6, il dev prima.
  "test_migra_2026_11_05.py 53450c6"
  # Strati F5 (5/11/2026, #4535): il comando omonimi non c'è. e87ce62, il dev prima.
  "test_sostituzioni_2026_11_05.py e87ce62"
  # La barra col PATH di ssh (15/11/2026): il comando non allarga il PATH. 8f62532, il dev prima.
  "test_statusline_path_2026_11_15.py 8f62532"
  # #4874 (6/11/2026): il comando regole-doppie non c'è. 3b5e6c3, il dev prima.
  "test_regole_doppie_2026_11_06.py 3b5e6c3"
  # #4860 (6/11/2026): col plugin stato e controlla tacciono. 3b5e6c3, il dev prima.
  "test_avviso_plugin_2026_11_06.py 3b5e6c3"
  # Col plugin la chiusura non lancia niente e applica non fa niente (10/11/2026). 62786fd, il dev prima.
  "test_chiusura_plugin_2026_11_10.py 62786fd"
  # #5880 (17/11/2026): niente ripiego HTTPS e niente regola sull'aggiornatore. 8e287e4, il dev prima.
  "test_aggiorna_https_2026_11_17.py 8e287e4"
  # #5102 (10/11/2026): i quattro difetti minori su Windows. 3f12336, il dev prima.
  "test_windows_minori_2026_11_10.py 3f12336"
  # /revisione (17/11/2026): 8117411, il dev prima.
  "test_revisione_2026_11_17.py 8117411"
  # #5877 (17/11/2026): le sessioni di prova. 22e5935, il dev prima.
  "test_prova_2026_11_17.py 22e5935"
  # /monitor impara (17/11/2026): impara.py non c'è. e0ec624, il dev prima.
  "test_monitor_impara_2026_11_17.py e0ec624"
  # Il giro di /monitor (20/11/2026, #4538): giro.py, posta_gws.py e --chiave non ci sono. fc03145, il dev prima.
  "test_monitor_giorno_2026_11_20.py fc03145"
  # La ripartenza per Volta (17/11/2026, #5910): il comando arturo ripartenza non c'è. b70d1d0, il dev prima.
  "test_ripartenza_2026_11_17.py b70d1d0"
  # L'aspetto (18/11/2026, proposta n. 73): aspetto_valori.py e arturo aspetto non ci sono. 58e0435, il dev prima.
  "test_aspetto_2026_11_18.py 58e0435"
  # La sandbox opzionale (19/11/2026): bin/sandbox.py e arturo sandbox non ci sono. f500fc1, il dev prima.
  "test_sandbox_2026_11_19.py f500fc1"
  # Le skill di ruolo (20/11/2026): estensione-skill.py e bin/ruoli.py non ci sono. 0c1daea, il dev prima.
  "test_ruoli_2026_11_20.py 0c1daea"
  # Lo sportello lato client (20/11/2026, #4793): modo log e dimentica non ci sono. 0cc681e, il dev prima.
  "test_telemetria_log_dimentica_2026_11_20.py 0cc681e"
  # Un hook personale non fa rosso il banco UTF-8 all'avvio (20/11/2026, #5383). 4801ee0, il dev prima.
  "test_banchi_file_personali_2026_11_20.py 4801ee0"
  # La base scelta due volte (21/11/2026, #6216): deriva.py non ha --base e il .sh ha la sua copia. cecf8fc, il dev prima.
  "test_base_arturo_2026_11_21.py cecf8fc"
  # Le righe per percorso del .local (21/11/2026, #6278): la guardia non le legge. 9641c7c, il dev prima.
  "test_protect_percorso_2026_11_21.py 9641c7c radice"
  # I glob e le graffe sui segreti della home (21/11/2026, #6279): cd, graffe e .npmrc tacciono. e794f3e, il dev prima.
  "test_glob_segreti_2026_11_21.py e794f3e radice"
  # Gli aggiramenti della revisione del 20/11 (21/11/2026, #6259): 89 forme passano mute. 02808d8, il dev prima.
  "test_aggiramenti_2026_11_21.py 02808d8 radice"
  # I programmi nascosti alle guardie (22/11/2026, #6323): le 11 forme passano mute. 0e37768, il dev prima.
  "test_programmi_nascosti_2026_11_22.py 0e37768 radice"
  # Le guardie veloci (22/11/2026, #6327, #5347): parole ed evento_bash.py non ci sono, block-dangerous oltre 8 s.
  # 663bcba, il dev prima.
  "test_parole_veloci_2026_11_22.py 663bcba"
  # Il pre-filtro in Python (22/11/2026, #6327): il modulo non c'è e il limite è 100.000. 5fdb286, il dev prima.
  "test_prefiltro_python_2026_11_22.py 5fdb286"
  # La lista letterale (22/11/2026, #6353): codice-nascosto chiede sul GET di curl in subprocess.run. f69db25, il dev prima.
  "test_lista_letterale_2026_11_22.py f69db25"
  # Un tag firmato PGP passa dal portachiavi della persona (21/11/2026, #6258). ff920f0, il dev prima.
  "test_firme_ssh_2026_11_21.py ff920f0"
  # La coda di /fine committa e spinge senza guardia dei segreti (21/11/2026, #6249). 6132caf, il dev prima.
  "test_fine_coda_segreti_2026_11_21.py 6132caf radice"
  # Con git -C la guardia legge tutti i file nuovi, e il -C sposta il repository dei comandi dopo (#6289). de04b3b, il dev prima.
  "test_pathspec_c_2026_11_22.py de04b3b"
  # Il campo if sugli hook (22/11/2026, #6327): gws-esito e block-dangerous dopo partono a ogni Bash. a1f5927, il dev prima.
  "test_hook_if_2026_11_22.py a1f5927"
  # Il /fine su una sessione già chiusa (22/11/2026, #6274): ogni giro del mod partiva. b54e244, il dev prima.
  "test_fine_gia_chiusa_2026_11_22.py b54e244"
  # L'avviso del sync della config a ogni sessione viva (22/11/2026, #6275). e1a03e6, il dev prima.
  "test_fine_avvisi_2026_11_22.py e1a03e6 radice"
  # Le guardie senza tetto di tempo (22/11/2026, #6363): l'hook va oltre i 30 secondi su curl ripetuti. e1a03e6, il dev prima.
  "test_tetto_guardie_2026_11_22.py e1a03e6"
  # Git e la fonte esterna dei todo in fila in arturo contesto (22/11/2026, #6317). 300567c, il dev prima.
  "test_parallelo_2026_11_22.py 300567c radice"
  # Senza arturo apertura le letture della FASE 4 vanno in fila (22/11/2026, #6368). 2120b4d, il dev prima.
  "test_apertura_2026_11_22.py 2120b4d radice"
  # Le guardie che ripartono da ogni curl, gws o find (22/11/2026, #6363). d631aa5, il dev prima.
  "test_guardie_lineari_2026_11_22.py d631aa5"
  # L'avvio annullato al timeout su Windows e il fetch che muore con lui (22/11/2026, #6370). e57fe9f, il dev prima.
  "test_avvio_tetto_2026_11_22.py e57fe9f"
  # I bug medi A4-A10 della revisione del 20/11 (22/11/2026, #6250): rossi tutti e sette. d0f56af, il dev prima.
  "test_revisione_medi_2026_11_22.py d0f56af"
  # I bug bassi 11-21 della revisione del 20/11 (22/11/2026, #6389): rossi tutti e undici. 1e84201, il dev prima.
  "test_revisione_bassi_2026_11_22.py 1e84201"
  # I testi pubblici (22/11/2026, #6418): roadmap sui rami, frase di /inizia/, Volta nel metodo. 40d4e4a, il dev prima.
  "test_testi_pubblici.py 40d4e4a"
  # I dati di transito sul ramo sync (23/11/2026, #6424): senza bin/sync_transito.py rossi tutti e dodici. 88a5f8d, il dev prima.
  "test_sync_transito.py 88a5f8d"
  # hooks/hub.py (23/11/2026, #6492): senza hub rossi tutti e otto. 9cbb926, il dev prima.
  "test_hub.py 9cbb926"
  # Il dispatcher in Python dentro hub (23/11/2026, #6492): su hub senza dispatcher rossi tutti e sette. bcb3907, il ramo prima.
  "test_dispatcher.py bcb3907"
)

# I veleni dei banchi che li hanno: una copia del repository rotta nel punto sorvegliato deve far
# fallire il controllo col suo codice e il motivo atteso (test_memoria.py Y08-Y12, 20/10/2026).
# Le conferme su lavoro proprio (31/10/2026): con le guardie di 15eb18d ogni gruppo LP deve essere rosso.
# git commit --amend sul commit di un'altra sessione (3/11/2026, #4187): con le guardie di c4ae5a4 ogni gruppo AM è rosso.
# Il ritratto di /setup (1/11/2026): senza esclusioni .env e chiavi escono; ogni regola di 2b/2c tolta
# da setup.md fa rosso; un installatore che sposta ~/.claude fa rosso CP02.
# I buchi della review del 1/11/2026: con le guardie di e80e43d ogni gruppo RV deve essere rosso.
# Il controllo dei token gws all'avvio (1/11/2026): un timeout che vale "ok" o un refresh lanciato male
# devono far rossi GT01 e GT05.
# La rotazione della sessione (3/11/2026): ogni copia rotta (retention col fine leggero, segno, marca
# non tagliata, riga sempre accesa, marca prima di " -- ") fa rosso il caso RT che la sorveglia.
VELENI=(
  test_memoria.py
  test_lavoro_proprio_2026_10_31.py
  test_amend_2026_11_03.py
  test_ritratto_2026_11_01.py
  test_setup_ritratto_2026_11_01.py
  test_copie_2026_10_23.py
  test_revisione_2026_11_01.py
  test_gws_token_health.py
  test_impacchetta_2026_11_03.py
  test_rotazione_2026_11_03.py
  test_gate_snello_2026_11_03.py
  test_viste_allineate_2026_11_03.py
  test_monitor_giro_2026_11_03.py
  # humanizer agganciato all'origine (4/11/2026): un controlla che non confronta fa rosso HO01.
  test_humanizer_origine.py
  # Strati F3 (5/11/2026): senza la verifica del tag Claude Code installa un tag non firmato (FD06).
  test_fiducia_2026_11_05.py
  # Strati F4 (5/11/2026): una migrazione che non torna indietro da sola lascia il plugin installato (MG06).
  test_migra_2026_11_05.py
  # Strati F5 (5/11/2026): un omonimo non dichiarato che non si nomina sparisce in silenzio (SO01).
  test_sostituzioni_2026_11_05.py
  # #4874 (6/11/2026): un --togli che non scrive lascia le regole doppie (RD02).
  test_regole_doppie_2026_11_06.py
  # #4860 (6/11/2026): una barra che lancia controlla da ~/.claude/bin col plugin non controlla mai (AV04).
  test_avviso_plugin_2026_11_06.py
  # Chiusura col plugin (10/11/2026): senza il ramo plugin di session-end.sh la chiusura non installa niente (PC03).
  test_chiusura_plugin_2026_11_10.py
  # #5880 (17/11/2026): un ripiego solo sul catalogo lascia install senza chiave SSH fallito (AH01).
  test_aggiorna_https_2026_11_17.py
  # Review del 7/11/2026, lotto L2 (#4972): con le guardie di e441828 ogni gruppo RW è rosso.
  test_revisione_2026_11_07.py
  # Review del 7/11/2026, lotto L9: una radice in più in deriva.py fa rosso A02 (finding 94).
  test_deriva_allineata.py
  # #5096 (9/11/2026): con le guardie di ce1cafc ogni gruppo GV, salvo i falsi positivi di GV08, è rosso.
  test_guardie_virgolette_2026_11_09.py
  # #5097 (10/11/2026): con le guardie di 73c6bf1 ogni gruppo LR è rosso, anche i blocchi falsi di LR02.
  test_guardie_regressioni_l2_2026_11_10.py
  # #5122 (10/11/2026): con le guardie di a2f90a5 ogni gruppo SU è rosso, SU06 perché la tabella manca.
  test_guardie_split_unico_2026_11_10.py
  # #5261 (11/11/2026): con le guardie di 7a8bb69 ogni gruppo MS è rosso.
  test_guardie_memoria_sblocco_2026_11_11.py
  # #5262 (11/11/2026): con le guardie di b68e732 ogni gruppo GC è rosso.
  test_guardie_cieche_2026_11_11.py
  # Ripasso dei permessi (20/11/2026): con le guardie di 0c1daea ogni gruppo AT è rosso.
  test_attrito_2026_11_20.py
  # #5102 (10/11/2026): ogni correzione tolta fa rosso il suo caso WM.
  test_windows_minori_2026_11_10.py
  # Il contesto del progetto e la testata (12/11/2026): ogni rottura fa rosso il suo caso TC.
  test_testata_contesto_2026_11_12.py
  # arturo progetti (11/11/2026): ogni rottura di bin/progetti.py fa rosso il suo caso PM.
  test_progetti_memoria_2026_11_11.py
  # arturo progetti rinomina (#6095): ogni rottura di rinomina.py o di contesto.py fa rosso il suo caso RN.
  test_rinomina_2026_11_19.py
  # arturo progetti unisci (#6187): ogni rottura di unisci.py fa rosso il suo caso UN.
  test_unisci_2026_11_20.py
  # arturo progetti elimina e nuovo (22/11/2026, #6432): Miscellanea, il rifiuto dei nomi presi, il JSON per Volta (EL01-).
  test_elimina_nuovo_2026_11_22.py
  # /revisione (17/11/2026): ogni riga tolta fa rosso il suo caso RV.
  test_revisione_2026_11_17.py
  # #5877 (17/11/2026): ogni riga tolta fa rosso il suo caso PV.
  test_prova_2026_11_17.py
  # Il contatto (10/11/2026): senza il contatto nel corpo, nell'impronta o nell'avvio, CT03, CT05 e CT07 sono rossi.
  test_contatto_2026_11_10.py
  # Le segnalazioni automatiche (11/11/2026): ogni filtro tolto da manda fa rosso il suo caso SA.
  test_segnala_auto_2026_11_11.py
  # n. 68: il heredoc rimesso dentro <(...) fa rossi BS01 e, sul Mac, BS02.
  test_bash32_2026_11_10.py
  # La Scoperta (14/11/2026): ogni veleno di scoperta.py e dell'hook fa rosso il suo caso SC.
  test_scoperta_2026_11_14.py
  # Lo storico delle chat (15/11/2026): ogni rottura di storico.py, del comando o dei testi fa rosso il suo caso ST.
  test_storico_2026_11_15.py
  # L'intervista (15/11/2026): ogni rottura di intervista.py, di contesto.py o dei testi fa rosso il suo caso IV.
  test_intervista_2026_11_15.py
  # Il fascicolo (15/11/2026): ogni rottura di fascicolo.py, del comando o dei testi fa rosso il suo caso FA.
  test_fascicolo_2026_11_15.py
  # Gli spazi e il nome (16/11/2026): ogni rottura di spazi.py, nome.py, contesto.py, dell'avvio o dei testi fa rosso il suo caso SP.
  test_spazi_2026_11_16.py
  # Le forme della Scoperta (16/11/2026): ogni rottura di scoperta_forme.py, scoperta.py o /fine fa rosso il suo caso SF.
  test_scoperta_forme_2026_11_16.py
  # arturo progetti (M3, #5672): ogni rottura di bin/progetti.py fa rosso il suo caso PM.
  test_progetti_memoria_2026_11_11.py
  # arturo progetti rinomina (#6095): ogni rottura di rinomina.py o di contesto.py fa rosso il suo caso RN.
  test_rinomina_2026_11_19.py
  # arturo progetti unisci (#6187): ogni rottura di unisci.py fa rosso il suo caso UN.
  test_unisci_2026_11_20.py
  # arturo progetti elimina e nuovo (22/11/2026, #6432): Miscellanea, il rifiuto dei nomi presi, il JSON per Volta (EL01-).
  test_elimina_nuovo_2026_11_22.py
  # Il file di sessione (C1): ogni rottura di scheda_file.py o di arturo sessione fa rosso il suo caso SE.
  test_scheda_file.py
  # La carta di sessione (#6422): ogni rottura di carta-sessione.py fa rosso il suo caso CS.
  test_carta_sessione.py
  # Il salvataggio automatico (M4, #5672): ogni rottura di salva-automatico.py, dell'hook o di contesto.py fa rosso il suo caso SV.
  test_salva_automatico.py
  # La telemetria della memoria (M7, #5672): ogni rottura di telemetria.py, inject-now.sh o salva-automatico.py fa rosso il suo caso TM.
  test_telemetria_memoria_2026_11_15.py
  # /monitor impara (17/11/2026): ogni rottura di impara.py (soglie, sempre, modo proposta, annullo) fa rosso il suo caso IM.
  test_monitor_impara_2026_11_17.py
  # Il giro di /monitor (#4538): impronta doppia, ponte a nome d'altri, visto ignorato, cursore su fonte troncata, testo nascosto.
  test_monitor_giorno_2026_11_20.py
  # La ripartenza (17/11/2026, #5910): ogni rottura di ripartenza.py o del passo di /inizio fa rosso il suo caso RP.
  test_ripartenza_2026_11_17.py
  # Lo sportello (#4793): un modo log che manda, una cartella che non si pota, un id che resta dopo dimentica.
  test_telemetria_log_dimentica_2026_11_20.py
  # Il /fine su una sessione già chiusa (#6274): ogni rottura di fine-gia-chiusa.py o di inject-now.sh fa rosso il suo caso FG.
  test_fine_gia_chiusa_2026_11_22.py
  # Gli avvisi di /fine (#6275): ogni rottura dell'anteprima in fine-coda.py fa rosso il suo caso FA.
  test_fine_avvisi_2026_11_22.py
  # I testi pubblici (#6418): ogni rottura di roadmap, README, metodo o disegno fa rosso il suo caso TP.
  test_testi_pubblici.py
)

# Banchi, controprove e veleni girano in parallelo e tutti, anche dopo un rosso: un giro dice ogni rosso
# (3/11/2026: 22 minuti in fila su un Mac, cinque giri per il rilascio 0.2.0). ARTURO_GATE_LAVORI
# sceglie quanti worker; il default è metà dei core, al massimo 4.
ESITO=0
python3 -B "$ROOT/tests/esegui_gate.py" esegui --root "$ROOT" --fixture "$FIXTURE/lavori" $PARZIALE_MODO $RILASCIO \
  ${ARTURO_GATE_LAVORI:+--lavori "$ARTURO_GATE_LAVORI"} --py38 "$PY38" --elenchi \
  --banchi "${BANCHI[@]}" --in-fila "${IN_FILA[@]}" --banchi-py38 "${PY38_BANCHI[@]}" \
  --controprove "${BASELINE[@]}" --veleni "${VELENI[@]}" || ESITO=$?
if [[ -n "$PARZIALE_MODO" ]]; then
  echo "PARZIALE ($PARZIALE_MODO): fatti solo una parte dei lavori; per un rilascio serve un giro completo"
  exit "$ESITO"
fi

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
  case "$file" in
    *.workflow.js)
      # Uno script del tool Workflow gira come corpo di una funzione async: "export const meta",
      # await e return stanno al primo livello. node --check lo legge avvolto allo stesso modo.
      avvolto="$FIXTURE/workflow-check.js"
      { echo '(async () => {'; sed 's/^export const meta/const meta/' "$REPO/$file"; echo '})()'; } > "$avvolto"
      node --check "$avvolto" || { echo "FAIL: $file non è un workflow valido" >&2; exit 1; }
      ;;
    shared/volta/mods/*.js)
      # I mod di Herdr sono moduli ES (import da "gpui-kit" e "herdr"): node li legge come .mjs.
      cp "$REPO/$file" "$FIXTURE/herdr-mod-check.mjs"
      node --check "$FIXTURE/herdr-mod-check.mjs" || { echo "FAIL: $file non è un modulo valido" >&2; exit 1; }
      ;;
    *) node --check "$REPO/$file" ;;
  esac
  js=$((js + 1))
done < <(git -C "$REPO" ls-files -z -- '*.js' '*.mjs')
[[ $js -gt 0 ]] || { echo "FAIL: nessun file JavaScript" >&2; exit 1; }

bash "$REPO/skills/system-audit/audit.sh" --strict
salti=$(grep -c . "$ARTURO_SALTI" || true)
py38=0
[[ -z "$PY38" ]] || py38=${#PY38_BANCHI[@]}
# PASS solo col giro verde: chi legge l'ultima riga di stdout senza stderr vedeva PASS anche sui rossi
# (review del 7/11/2026, finding 90).
riepilogo=$(printf 'banchi=%s shell=%s js=%s salti=%s py38=%s' "$(( ${#BANCHI[@]} + ${#IN_FILA[@]} ))" "$shells" "$js" \
  "$salti" "$py38")
[[ "$salti" == 0 ]] || sed 's/^/  /' "$ARTURO_SALTI"
if [[ "$ESITO" != 0 ]]; then
  echo "FAIL: lavori rossi, elencati sopra (=== ROSSO); $riepilogo"
  echo "FAIL: lavori rossi, elencati sopra (=== ROSSO)" >&2
  exit "$ESITO"
fi
echo "PASS: $riepilogo"
