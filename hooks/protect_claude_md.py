#!/usr/bin/env python3
"""Hook PreToolUse (Edit/MultiEdit/Write/NotebookEdit): protegge file critici.

Tre categorie, ognuna con un unlock per-sessione distinto, più il resto di ~/.claude:

  Persistenza (codice che parte da solo, fuori da Claude Code):
    .git/hooks/** di qualunque repository
    ~/Library/LaunchAgents/** (macOS)
    ~/.config/systemd/user/** e ~/.config/autostart/** (Linux)
    -> unlock: touch ~/.claude/system-unlock-{session_id}

  CLAUDE.md e CLAUDE.local.md (qualsiasi cartella; il .local dal 10/11/2026, #5159)
    -> chiede conferma (ask) a ogni modifica: un popup solo (3/11/2026, #4473). Prima era
       deny con istruzioni, e una modifica costava la domanda in chat più il popup dell'unlock.
       L'unlock touch ~/.claude/claude-md-unlock-{session_id} è la scorciatoia per una serie di
       modifiche: finché c'è, ogni modifica della sessione passa senza popup.
    Sul CLAUDE.md globale avvisa quando il file, dopo la modifica, supera il
    budget di righe (ARTURO_CLAUDE_MD_RIGHE, default 200).

  Config e hook di Claude Code:
    ~/.claude/settings.json, settings.local.json, .claude.json
    ~/.claude/hooks/**, ~/.claude/plugins/cache/** e plugins/marketplaces/** (il codice dei plugin
    installati, col plugin anche le guardie di Arturo)
    ~/.claude/firme/**, bin/aggiornamenti.py, bin/aggiorna-applica.sh (l'aggiornamento automatico:
    chi li cambia fa installare da solo codice non firmato)
    ~/.claude/arturo/radice (col plugin, la barra in basso esegue il codice della cartella che nomina;
    lo scrive solo l'avvio, 4/11/2026, #4567)
    ~/.claude/arturo/*.local (le preferenze della persona, comprese quelle delle guardie: strati F1, #4531)
    -> unlock: touch ~/.claude/config-unlock-{session_id}

Motivo della categoria config/hook: senza questo, sotto defaultMode auto o acceptEdits
un'iniezione può riscrivere settings.json o disattivare un hook via tool Edit/Write
senza alcun prompt, neutralizzando ogni altra guardia. Il vettore shell
(sed -i, >, cp...) è coperto separatamente da block-dangerous.py.

Per persistenza e config l'unlock (deny + istruzioni, non hard-deny in settings.json) preserva
le modifiche legittime: chiedi conferma all'utente, crea il touch file, riprova.

I file di unlock stessi (qualsiasi nome con "unlock" sotto ~/.claude) chiedono
sempre conferma anche via Edit/Write: un marker scritto dall'assistente senza una
decisione dell'utente sbloccherebbe da solo le tre categorie. Il vettore shell
(touch) chiede conferma in block-dangerous.py.

La categoria persistenza viene prima delle altre: un git hook o un servizio
di avvio esegue codice a ogni commit o a ogni login, senza che nessuno lo chieda.
Il vettore shell (echo >, cp, tee...) su questi percorsi chiede conferma in
block-dangerous.py.

~/.claude/arturo/protect_claude_md.local (dal 30/10/2026; vale ancora il vecchio hooks/) cambia la decisione di sei categorie: i due
CLAUDE.md, i settings della radice, la config, il resto di ~/.claude (dot-claude) e le cartelle .claude dei
progetti (dot-claude-progetto). Persistenza,
file di unlock, firme/, gli script dell'aggiornamento e i .local restano col default. Il vocabolario
sta accanto a _locale().

Fail-closed: errore di parsing = blocca per sicurezza.
"""
import json
import sys
import os
import re


def _emit(kind, reason):
    json.dump({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": kind,
            "permissionDecisionReason": reason,
        }
    }, sys.stdout)


# Budget di righe del CLAUDE.md globale: oltre, le istruzioni si diluiscono e
# costano contesto a ogni sessione. Si cambia con la variabile d'ambiente.
BUDGET_RIGHE_DEFAULT = 200


def _budget():
    try:
        return max(1, int(os.environ.get('ARTURO_CLAUDE_MD_RIGHE', BUDGET_RIGHE_DEFAULT)))
    except ValueError:
        return BUDGET_RIGHE_DEFAULT


def _righe_dopo(path, ti):
    """Numero di righe del file come sarà dopo Write, Edit o MultiEdit."""
    return len(_testo_dopo(path, ti).splitlines())


def _ferma_json_rotto(rp, ti):
    """Un settings*.json che diventerebbe JSON non valido si ferma, anche con l'unlock o con allow."""
    try:
        json.loads(_testo_dopo(rp, ti))
    except (ValueError, OSError) as e:
        _emit("deny", f"{os.path.basename(rp)} non sarebbe JSON valido dopo la modifica ({e}). "
              "Un settings rotto spegne deny e hook: correggi la modifica e riprova.")
        sys.exit(0)


def _testo_dopo(path, ti):
    """Il file come sarà dopo Write, Edit o MultiEdit."""
    if isinstance(ti.get('content'), str):
        testo = ti['content']
    else:
        with open(path, encoding='utf-8') as fh:
            testo = fh.read()
        modifiche = ti.get('edits') if isinstance(ti.get('edits'), list) else [ti]
        for m in modifiche:
            vecchio, nuovo = m.get('old_string'), m.get('new_string')
            if isinstance(vecchio, str) and isinstance(nuovo, str) and vecchio:
                testo = testo.replace(vecchio, nuovo) if m.get('replace_all') else testo.replace(vecchio, nuovo, 1)
    return testo


def _avviso_budget(rp, claude_dir, ti):
    """Avviso da aggiungere alla decisione se il CLAUDE.md globale supera il budget."""
    if rp != os.path.join(claude_dir, 'CLAUDE.md'):
        return ""
    try:
        n = _righe_dopo(rp, ti)
    except Exception:
        return ""
    budget = _budget()
    if n <= budget:
        return ""
    return (f" ATTENZIONE: dopo questa modifica il CLAUDE.md globale avra' {n} righe, "
            f"oltre il budget di {budget}. Se aggiungi una regola, togline o accorciane "
            "un'altra nella stessa modifica.")


# ~/.claude/arturo/protect_claude_md.local (30/10/2026, #4291): chi installa Arturo può cambiare la decisione di
# alcune categorie senza toccare questo file. Righe `<decisione> <categoria>`, `#` per i commenti.
# Decisioni: allow, ask, deny. Categorie:
#   claude-md-globale   ~/.claude/CLAUDE.md e ~/.claude/CLAUDE.local.md
#   claude-md-progetto  ogni altro CLAUDE.md o CLAUDE.local.md già esistente (crearne uno chiede sempre)
#   settings-radice     ~/.claude/settings*.json e ~/.claude/.claude.json (la validità JSON resta)
#   config              hooks/** e i settings*.json nelle sottocartelle di ~/.claude
#   dot-claude          ogni altro file sotto ~/.claude
#   dot-claude-progetto i file dentro una cartella .claude di un progetto, settings di progetto compresi
# Restano fuori, sempre col default di Arturo: percorsi di avvio automatico, file di sblocco, firme/,
# gli script dell'aggiornamento e i file .local (arturo/*.local e hooks/*.local), che altrimenti potrebbero
# allentare sé stessi.
# Un file illeggibile o una riga fuori vocabolario valgono come assenti.
DECISIONI_LOCALI = {'allow', 'ask', 'deny'}
CATEGORIE_LOCALI = {'claude-md-globale', 'claude-md-progetto', 'settings-radice', 'config', 'dot-claude',
                    'dot-claude-progetto'}


def _preferenza(nome):
    """~/.claude/arturo/<nome>, o il vecchio ~/.claude/hooks/<nome> finché il nuovo manca (strati F1, #4531).
    La guardia non importa radici.py: un import fallito la spegnerebbe, perché un errore diverso
    dall'uscita 2 non blocca. Legge la home vera, la stessa su cui giudica i percorsi."""
    claude = os.path.expanduser('~/.claude')
    nuovo = os.path.join(claude, 'arturo', nome)
    vecchio = os.path.join(claude, 'hooks', nome)
    return vecchio if not os.path.exists(nuovo) and os.path.exists(vecchio) else nuovo


def _locale():
    """Le decisioni di protect_claude_md.local, per categoria."""
    scelte = {}
    try:
        with open(_preferenza('protect_claude_md.local'), encoding='utf-8') as fh:
            for riga in fh:
                parti = riga.split('#', 1)[0].split()
                if len(parti) == 2 and parti[0] in DECISIONI_LOCALI and parti[1] in CATEGORIE_LOCALI:
                    scelte[parti[1]] = parti[0]
    except OSError:
        return {}
    return scelte


def _emetti_locale(categoria, avviso="", chiede=None):
    """Se il .local decide la categoria, emette la sua decisione ed esce. Un ask passa dalla telemetria."""
    decisione = _locale().get(categoria)
    if decisione:
        if decisione == 'ask' and chiede:
            chiede()
        _emit(decisione, f"{categoria}: decisione di protect_claude_md.local." + avviso)
        sys.exit(0)


def _persistenza(rp):
    """True se il path installa codice che parte da solo: git hook o servizio di avvio. Su macOS e Windows
    il confronto ignora le maiuscole, come il disco (~/library/launchagents, finding 11)."""
    piega = (lambda s: s.casefold()) if sys.platform in ('darwin', 'win32') else (lambda s: s)
    rp = piega(rp)
    if (os.sep + '.git' + os.sep + 'hooks' + os.sep) in rp or rp.endswith(os.sep + '.git' + os.sep + 'hooks'):
        return True
    for radice in ('~/Library/LaunchAgents', '~/.config/systemd/user', '~/.config/autostart'):
        r = piega(os.path.realpath(os.path.expanduser(radice)))
        if rp == r or rp.startswith(r + os.sep):
            return True
    return False


def _mod_di(rp, claude_dir):
    """La cartella del mod (un .claude-plugin/plugin.json sopra il file) dentro ~/.claude, o "" se il file non è
    di un mod. Un file nella cartella hooks/ di un mod è protetto come gli hook di Arturo (segnalazione n. 63)."""
    cartella = os.path.dirname(rp)
    while cartella.startswith(claude_dir + os.sep):
        if os.path.isfile(os.path.join(cartella, '.claude-plugin', 'plugin.json')):
            return cartella
        cartella = os.path.dirname(cartella)
    return ''


def _testo_mod(rp, mod, claude_dir, safe_id):
    """Il blocco detto per un mod della persona: perché vale anche lì, e in un passo solo cosa fare (9/11/2026,
    segnalazione n. 63: il testo generico faceva pensare a una cosa rischiosa, e il caricamento arrivava dopo)."""
    nome = os.path.basename(mod)
    dove = '~/.claude/' + os.path.relpath(mod, claude_dir).replace(os.sep, '/')
    testo = (f"È un file di un mod della persona ({nome}, {os.path.basename(rp)}): l'hook di un mod gira dentro Claude "
             "Code e può approvare da solo qualunque comando, quindi anche un mod nuovo e legittimo vuole il suo sì. "
             f"Per procedere: 1) dille che si tratta del suo mod {nome} e chiedi conferma. 2) dopo il sì fagli lanciare: "
             f"! touch ~/.claude/config-unlock-{safe_id} (lo sblocco resta all'utente) 3) riprova la modifica.")
    rel = os.path.relpath(mod, claude_dir).replace(os.sep, '/')
    if not rel.startswith(('dev-mods/', 'skills/')):
        testo += (f" Nello stesso messaggio dille anche come caricarlo: la cartella {dove} va aggiunta a "
                  "CLAUDE_CODE_PLUGIN_DIRS in ~/.zshrc, con un comando ! che prepari tu: Claude non può scrivere ~/.zshrc.")
    return testo


def main():
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        tool = data.get('tool_name', '')
        if tool not in ('Edit', 'MultiEdit', 'Write', 'NotebookEdit'):
            sys.exit(0)

        ti = data.get('tool_input') or {}
        file_path = ti.get('file_path') or ti.get('notebook_path') or ''
        if not file_path:
            sys.exit(0)

        def chiede():
            """Telemetria di Arturo: questa guardia chiede conferma. Solo il nome e l'id della chiamata."""
            try:
                import importlib.util
                f = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'bin', 'telemetria.py')
                uso = data.get('tool_use_id')
                if os.path.exists(f) and isinstance(uso, str):
                    spec = importlib.util.spec_from_file_location('telemetria', f)
                    t = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(t)
                    t.chiede('protect_claude_md.py', uso)
            except Exception:  # noqa: BLE001 - la telemetria non ferma mai una guardia
                pass

        # Su Windows Git Bash scrive il disco come `/c/Users/...`: per realpath è `C:\c\Users`, fuori da ~/.claude
        # (review del 9/11/2026, #5096). La stessa riscrittura di _resolve in block-dangerous.py.
        if os.name == 'nt':
            file_path = re.sub(r'^/([a-zA-Z])(?=/|$)', lambda m: m.group(1).upper() + ':', file_path)
        rp = os.path.realpath(os.path.expanduser(file_path))
        base = os.path.basename(rp).upper()
        claude_dir = os.path.realpath(os.path.expanduser('~/.claude'))

        session_id = data.get('session_id', '')
        safe_id = re.sub(r'[^a-zA-Z0-9_-]', '_', session_id)
        home_claude = os.path.expanduser('~/.claude')

        def unlocked(token):
            # Solo un file vero sblocca: una cartella o un link col nome giusto si creano con comandi che
            # le guardie della shell possono non vedere (review del 10/11/2026, #5261).
            p = os.path.join(home_claude, f'{token}-{safe_id}')
            return os.path.isfile(p) and not os.path.islink(p)

        # Su macOS e Windows il disco ignora le maiuscole: ~/.CLAUDE/settings.json è la config. Il confronto
        # si fa in minuscolo, e il percorso si riscrive con la radice vera (review del 7/11/2026, finding 11).
        piega = sys.platform in ('darwin', 'win32')
        if piega and (rp.casefold() == claude_dir.casefold() or rp.casefold().startswith(claude_dir.casefold() + os.sep)):
            rp = claude_dir + rp[len(claude_dir):]
        under_claude = (rp == claude_dir or rp.startswith(claude_dir + os.sep))

        # Categoria 0: file di unlock -> sempre una decisione dell'utente
        if under_claude and 'UNLOCK' in base:
            chiede()
            _emit("ask", (
                f"File di unlock ({os.path.basename(rp)}): toglierebbe la conferma "
                "sui CLAUDE.md, o la protezione di config/hook o dei percorsi di avvio automatico. "
                "Conferma solo se l'hai chiesto tu."
            ))
            sys.exit(0)

        # Categoria 1: persistenza (git hook, servizi di avvio) -> prima di tutto
        if _persistenza(rp):
            if unlocked('system-unlock'):
                _emit("allow", "percorso di avvio automatico sbloccato da conferma utente")
                sys.exit(0)
            _emit("deny", (
                f"Percorso di avvio automatico protetto ({rp}): un git hook o un servizio "
                "di avvio esegue codice da solo, a ogni commit o a ogni accesso. "
                "Per procedere: 1) chiedi conferma esplicita all'utente. "
                f"2) dopo il sì fagli lanciare: ! touch ~/.claude/system-unlock-{safe_id} "
                "(lo sblocco resta all'utente: in modalità auto il classificatore ferma il touch "
                "lanciato da Claude) 3) riprova la modifica."
            ))
            sys.exit(0)

        # Categoria 2: CLAUDE.md e CLAUDE.local.md (ovunque). Il .local sono istruzioni come l'altro, e la shell
        # le chiedeva già (block-dangerous, PERCORSI_PROTETTI): via Edit e Write passavano (#5159, 10/11/2026).
        if base in ('CLAUDE.MD', 'CLAUDE.LOCAL.MD'):
            avviso = _avviso_budget(rp, claude_dir, ti)
            if tool == 'Write' and not os.path.exists(rp):
                chiede()
                _emit("ask", (
                    f"Stai creando un {os.path.basename(rp)} nuovo in {os.path.dirname(rp)}: sono istruzioni "
                    "che Claude seguira' ogni volta che lavora in questa cartella. "
                    "Conferma se l'hai chiesto tu." + avviso
                ))
                sys.exit(0)
            if unlocked('claude-md-unlock'):
                _emit("allow", "CLAUDE.md sbloccato da conferma utente." + avviso)
                sys.exit(0)
            _emetti_locale('claude-md-globale' if os.path.dirname(rp) == claude_dir
                           else 'claude-md-progetto', avviso, chiede)
            # Una conferma sola per modifica (3/11/2026, #4473): il popup è la conferma. Il deny con
            # istruzioni costava due o tre sì (domanda in chat, popup dell'unlock, a volte la shell).
            chiede()
            _emit("ask", (
                f"Modifica di {rp}: sono le istruzioni che Claude segue in questa cartella. "
                "Conferma se l'hai chiesta tu." + avviso
            ))
            sys.exit(0)

        # Categoria 3: config/hook di Claude Code
        relativo = os.path.relpath(rp, claude_dir).replace(os.sep, '/') if under_claude else ''
        if piega:
            relativo = relativo.casefold()
        # L'ancora dei rilasci (finding 11): fiducia.py verifica ogni aggiornamento con questa chiave, e se manca
        # vale quella della copia da verificare.
        ancore = ('bin/aggiornamenti.py', 'bin/aggiorna-applica.sh', 'arturo/radice', 'arturo/rilasci.allowed_signers',
                  'plugins/installed_plugins.json', 'plugins/known_marketplaces.json')
        is_config = under_claude and (
            re.match(r'SETTINGS.*\.JSON$', base) is not None
            or base == '.CLAUDE.JSON'
            or ('/' + relativo).startswith('/hooks/') or relativo == 'hooks'
            or (os.sep + 'hooks' + os.sep) in rp
            or rp.endswith(os.sep + 'hooks')
            or relativo == 'firme' or relativo.startswith('firme/')
            or relativo in ancore
            # Tutta bin: gli hook eseguono telemetria.py, telemetria-esito.sh, correzioni.py (#5262, n. 5).
            or relativo == 'bin' or relativo.startswith('bin/')
            or (relativo.startswith('arturo/') and relativo.endswith('.local'))
            or relativo.startswith(('plugins/cache/', 'plugins/marketplaces/'))
        )
        if is_config:
            # Un settings*.json che diventerebbe JSON non valido si ferma anche con l'unlock: un
            # settings rotto spegne deny e hook alla ricarica successiva (dalla config dell'autore,
            # 20/10/2026).
            if re.match(r'SETTINGS.*\.JSON$', base) is not None:
                _ferma_json_rotto(rp, ti)
            if unlocked('config-unlock'):
                _emit("allow", "config/hook Claude Code sbloccati da conferma utente")
                sys.exit(0)
            # Il codice dei plugin installati (col plugin, anche le guardie di Arturo): il .local
            # della persona non lo apre, come firme/ (docs/strati.md, 3/11/2026).
            intoccabile = (relativo == 'firme' or relativo.startswith('firme/')
                           or relativo.startswith(('plugins/cache/', 'plugins/marketplaces/'))
                           or relativo in ancore
                           or (relativo.startswith(('hooks/', 'arturo/')) and relativo.endswith('.local')))
            if not intoccabile:
                in_radice = os.path.dirname(rp) == claude_dir
                _emetti_locale('settings-radice' if in_radice and (re.match(r'SETTINGS.*\.JSON$', base)
                                                                    or base == '.CLAUDE.JSON') else 'config',
                               chiede=chiede)
            mod = _mod_di(rp, claude_dir)
            if mod and not intoccabile:
                _emit("deny", _testo_mod(rp, mod, claude_dir, safe_id))
                sys.exit(0)
            _emit("deny", (
                f"File di config/hook di Claude Code protetto ({os.path.basename(rp)}). "
                "Modificarlo può disattivare le guardie di sicurezza. Per procedere: "
                "1) chiedi conferma esplicita all'utente. "
                f"2) dopo il sì fagli lanciare: ! touch ~/.claude/config-unlock-{safe_id} "
                "(lo sblocco resta all'utente: in modalità auto il classificatore ferma il touch "
                "lanciato da Claude) 3) riprova la modifica."
            ))
            sys.exit(0)

        # Categoria 4: il resto di ~/.claude decide il flusso normale dei permessi, o il .local.
        if under_claude:
            _emetti_locale('dot-claude', chiede=chiede)

        # Categoria 5: una cartella .claude dentro un progetto (settings di progetto, worktree, agenti).
        # Claude Code chiede a ogni scrittura lì; senza .local la decisione resta sua (5/11/2026, #4535).
        # Vale solo fuori dalla config: ~/.claude ha le sue categorie, e una riga sui progetti non deve
        # aprire personale/session-start.sh, che parte a ogni avvio. Lo stesso per CLAUDE_CONFIG_DIR.
        config_altrove = os.path.realpath(os.environ.get('CLAUDE_CONFIG_DIR') or claude_dir)
        if (not under_claude and rp != config_altrove and not rp.startswith(config_altrove + os.sep)
                and (os.sep + '.claude' + os.sep) in rp):
            if re.match(r'SETTINGS.*\.JSON$', base) is not None:
                _ferma_json_rotto(rp, ti)
            _emetti_locale('dot-claude-progetto', chiede=chiede)

        sys.exit(0)

    except Exception as e:
        print(f"protect_claude_md: errore interno ({e}), modifica bloccata per sicurezza", file=sys.stderr)
        sys.exit(2)


if __name__ == '__main__':
    # Claude Code scrive e legge in UTF-8. Su Windows la pipe è in cp1252 (16/10/2026).
    for _flusso in (sys.stdout, sys.stderr):
        try:
            _flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    main()
