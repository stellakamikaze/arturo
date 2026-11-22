#!/usr/bin/env python3
"""PreToolUse(Bash) hook: gate operazioni gh CLI distruttive/sensibili.

Invocato dal dispatcher quando il comando contiene `gh ` (anche in catena).
Blocca operazioni distruttive GitHub prima dell'esecuzione.

- exit 2 (blocco duro): repo delete (anche deleteRepository via GraphQL),
  secret/variable set|delete, release delete, gh api con -X/--method
  DELETE|PUT|PATCH, gh auth token|logout.
- ask (conferma): pr merge, workflow run, run rerun (reversibili ma outward);
  gh api che scrive: mutazioni GraphQL, query GraphQL lette da file (effetto non
  leggibile), POST espliciti o impliciti (-f/-F/--field/--raw-field/--input
  senza -X GET).
Fail-open su parsing.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
import signal


def _t(s, f):
    sys.exit(0)


if hasattr(signal, "SIGALRM"):
    signal.signal(signal.SIGALRM, _t)


def _dopo(testa: str, classe: str = r'[^|;&\n]') -> str:
    """`\\btesta\\b` e la corsa di `classe` che la segue, ferma dove la testa ricomincia (#6363, 22/11/2026): con
    `gh api ` ripetuto re.search ripartiva da ogni gh e correva fino in fondo. Il risultato non cambia: se la regex
    parte da un `gh api`, parte anche dall'ultimo prima di quello che cerca (banco LG06)."""
    parola = r'\b' + testa + r'\b'
    return parola + r'(?:(?!' + parola + r')' + classe + r')*'


BLOCK = [
    (r'\bgh\s+repo\s+delete\b', "eliminazione di un repository GitHub"),
    (_dopo(r'gh\s+api', '[^|]') + r'\bdeleteRepository\b', "eliminazione di un repository GitHub via GraphQL"),
    (r'\bgh\s+secret\s+(set|delete|remove)\b', "modifica/rimozione di secret GitHub"),
    (r'\bgh\s+variable\s+(set|delete|remove)\b', "modifica/rimozione di variabili GitHub"),
    (r'\bgh\s+release\s+delete\b', "eliminazione di una release"),
    (r'\bgh\s+auth\s+(token|logout)\b', "esposizione token / logout gh"),
    # 21/11/2026 (#6259, S6): `gh auth status --show-token` (o -t) stampa lo stesso token di `gh auth token`.
    (_dopo(r'gh\s+auth\s+status') + r'\s(?:--show-token\b|-[a-zA-Z]*t\b)', "esposizione token / logout gh"),
    (_dopo(r'gh\s+api', '[^|]') + r'(-X|--method)\s*=?\s*(DELETE|PUT|PATCH)\b', "chiamata API GitHub mutante (DELETE/PUT/PATCH)"),
]
ASK = [
    (r'\bgh\s+pr\s+merge\b', "merge di una PR"),
    (r'\bgh\s+workflow\s+run\b', "avvio di un workflow CI"),
    (r'\bgh\s+run\s+rerun\b', "ri-esecuzione di un run CI"),
    # 21/11/2026 (#6259, rilievi S7 e S8 della revisione del 20/11).
    # Un alias nasconde il comando vero: `gh alias set x 'repo delete'` e poi `gh x` (vedi _con_alias).
    (r'\bgh\s+alias\s+(set|import)\b', "alias di gh, che nasconde il comando vero"),
    (r'\bgh\s+repo\s+(archive|rename)\b', "archiviazione o cambio di nome di un repository"),
    (_dopo(r'gh\s+repo\s+edit') + r'--visibility\b', "cambio di visibilità di un repository"),
    (_dopo(r'gh\s+repo\s+create') + r'--public\b', "creazione di un repository pubblico"),
    (r'\bgh\s+(ssh-key|gpg-key)\s+(add|delete)\b', "chiave d'accesso dell'account GitHub"),
    (r'\bgh\s+repo\s+deploy-key\s+(add|delete)\b', "chiave d'accesso di un repository"),
    (_dopo(r'gh\s+gist\s+create') + r'\s(?:--public\b|-[a-zA-Z]*p\b)', "gist pubblico"),
    (_dopo(r'gh\s+gist\s+edit') + r'--public\b', "gist pubblico"),
    # Un commento è un testo che altri leggono a nome della persona: come un invio.
    (r'\bgh\s+(issue|pr)\s+comment\b', "commento pubblico su una issue o una PR"),
    (r'\bgh\s+pr\s+review\b', "review pubblica di una PR"),
]

# 21/11/2026 (#6259, S7): curl, wget e httpie verso api.github.com fanno le stesse chiamate di `gh api`.
# La regex dice la regola; la legge in tempo lineare _chiamate_api_github (#6363).
_API_GITHUB =re.compile(r'\b(?:curl|wget|http|https|xh)\b(?:[^|;&\n"\']|"[^"\n]*"|\'[^\'\n]*\')*api\.github\.com'
                         r'(?:[^|;&\n"\']|"[^"\n]*"|\'[^\'\n]*\')*', re.IGNORECASE)
_API_METODO = re.compile(r'(?:^|\s)(?:-X\s*|--request(?:\s+|=)|--method(?:\s+|=))["\']?(\$?\{?[A-Za-z_]\w*)')
_API_CORPO = re.compile(r'(?:^|\s)(?:-d|--data(?:-raw|-binary|-urlencode)?|--json|-F|--form|-T|--upload-file|'
                        r'--post-data|--post-file|--body-data|--body-file)(?:\s|=|$)')


_API_TESTA = re.compile(r'\b(?:curl|wget|http|https|xh)\b', re.IGNORECASE)
_API_PEZZO = re.compile(r'[^|;&\n"\']+|"[^"\n]*"|\'[^\'\n]*\'')
_API_HOST = re.compile(r'api\.github\.com', re.IGNORECASE)


def _chiamate_api_github(intero: str) -> list:
    """I tratti di `_API_GITHUB.finditer(intero)`, in tempo lineare (#6363, 22/11/2026).

    Dopo il programma la regex legge pezzi senza `|;&` e a capo, o fra virgolette intere: il cammino è uno solo, e
    api.github.com conta solo in un pezzo fuori dalle virgolette. Il tratto va dal programma alla fine del cammino.
    finditer ripartiva da ogni curl e rifaceva il cammino fino in fondo: 90.000 caratteri di `curl ` ripetuto erano
    21 secondi. Qui un cammino che arriva in un punto già percorso da un cammino senza host si ferma: da lì il resto
    è lo stesso, e non ha l'host (banco LG05 in tests/test_guardie_lineari_2026_11_22.py)."""
    n = len(intero)
    segno = {}  # punto di confine -> fine del cammino senza host che ci è passato
    tratti, ripresa = [], 0
    for t in _API_TESTA.finditer(intero):
        if t.start() < ripresa:
            continue
        p, host, punti, fine = t.end(), False, [], None
        while True:
            if p in segno:
                fine = segno[p]
                break
            m = _API_PEZZO.match(intero, p)
            if not m:
                punti.append(p)
                fine = p
                break
            if intero[p] in "\"'":
                punti.append(p)
            else:
                # Ogni carattere di un pezzo senza virgolette è un confine: un altro cammino può entrarci.
                punti.extend(range(p, m.end()))
                host = host or bool(_API_HOST.search(intero, p, m.end()))
            p = m.end()
        if host:
            tratti.append(intero[t.start():fine])
            ripresa = fine
        else:
            for q in punti:
                segno.setdefault(q, fine)
    return tratti


def _api_github_diretta(intero: str):
    """(blocco, motivo) per una chiamata diretta all'API di GitHub che scrive, altrimenti None."""
    for seg in _chiamate_api_github(intero):
        metodo = _API_METODO.search(seg)
        verbo = metodo.group(1).upper() if metodo else ("POST" if _API_CORPO.search(seg) else "GET")
        if re.match(r'^https?\b', seg, re.IGNORECASE) or re.match(r'^xh\b', seg, re.IGNORECASE):
            parola = re.search(r'\s(GET|POST|PUT|PATCH|DELETE)\s', seg)  # httpie: `http DELETE url`
            verbo = parola.group(1) if parola else verbo
        if verbo in ("DELETE", "PUT", "PATCH"):
            return True, "chiamata API GitHub mutante (DELETE/PUT/PATCH) senza gh"
        if verbo.startswith("$"):
            return False, "chiamata all'API di GitHub con il metodo in una variabile: non si legge cosa fa"
        if verbo == "POST":
            return False, "chiamata API GitHub POST senza gh"
    return None


_GH_COMANDI = frozenset(
    "alias api attestation auth browse cache codespace completion config extension gist gpg-key issue label org "
    "pr project release repo ruleset run search secret ssh-key status variable workflow help version co".split())


def _alias_di_gh() -> dict:
    """Gli alias della persona, da ~/.config/gh/config.yml: `nome: espansione` sotto `aliases:`."""
    cartella = os.environ.get("GH_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".config", "gh")
    alias, dentro = {}, False
    try:
        with open(os.path.join(cartella, "config.yml"), encoding="utf-8", errors="replace") as f:
            for riga in f:
                if re.match(r"^aliases:\s*$", riga):
                    dentro = True
                    continue
                if dentro:
                    m = re.match(r"^\s+([\w-]+):\s*(.*?)\s*$", riga)
                    if not m:
                        if riga.strip() and not riga.startswith((" ", "\t", "#")):
                            break
                        continue
                    alias[m.group(1)] = m.group(2).strip("'\"")
    except OSError:
        pass
    return alias


def _con_alias(cmd: str) -> str:
    """Le righe `gh …` con gli alias della persona sciolti: `gh cancella o/r` con `cancella: repo delete`
    diventa `gh repo delete o/r`. Un alias di shell (`!…`) diventa una riga che la guardia non conosce."""
    righe = cmd.split("\n")
    if not any(len(r.split()) > 1 and r.split()[1] not in _GH_COMANDI for r in righe):
        return cmd
    alias = _alias_di_gh()
    fuori = []
    for riga in righe:
        parole = riga.split()
        if len(parole) > 1 and parole[0] == "gh" and parole[1] in alias:
            valore = alias[parole[1]]
            fuori.append("gh alias-di-shell " + valore if valore.startswith("!")
                         else "gh " + valore + " " + " ".join(parole[2:]))
        else:
            fuori.append(riga)
    return "\n".join(fuori)


_ESEGUE_TESTO = re.compile(r"\b(?:exec\w*|spawn\w*|system|popen|subprocess|child_process|run|call|check_output|"
                           r"eval|Function)\s*\(|child_process|subprocess|os\.system|shell\s*=\s*True")


def _testo_gh(cmd: str, pulito: bool = False) -> str:
    """Le sole invocazioni di gh, una per riga, lette come programmi (review del 7/11/2026, finding 10):
    un grep o un argomento in prosa che cita un sottocomando di gh non lo lancia. Contano gh dentro
    sh -c, eval, xargs e nelle sostituzioni $( ) e backtick, anche fra virgolette
    (`curl -H "Authorization: $(gh auth token)"`). Senza forma_comando.py vale il testo intero."""
    try:
        spec = importlib.util.spec_from_file_location(
            "forma_comando", os.path.join(os.path.dirname(os.path.abspath(__file__)), "forma_comando.py"))
        fc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fc)
    except Exception:
        return cmd
    # $( ) e backtick dentro un heredoc quotato verso python o node sono testo: la shell non li espande, e
    # il codice markdown di una nota (`gh workflow run x.yml`) non lancia gh (20/11/2026, 2 conferme in 7 giorni).
    # ruby, perl e php eseguono il backtick: per loro il corpo resta. Vale solo per le conferme (`pulito`): i blocchi
    # duri leggono sempre il testo intero, e un corpo che esegue programmi (execSync, os.system, subprocess) resta
    # visibile, perché passa la stringa a una shell (revisione del 20/11/2026: `gh repo delete` passava).
    sorgente = cmd
    if not pulito:
        sorgente = None
    try:
        if sorgente is None:
            raise ValueError("testo intero")
        spec_hd = importlib.util.spec_from_file_location(
            "heredoc_gh", os.path.join(os.path.dirname(os.path.abspath(__file__)), "heredoc.py"))
        hd = importlib.util.module_from_spec(spec_hd)
        spec_hd.loader.exec_module(hd)
        sorgente = hd.togli(cmd, lambda h: h.quotato and h.certo and h.consumatore in hd.INTERPRETI
                            and h.consumatore not in hd._BACKTICK_ESEGUE
                            and not _ESEGUE_TESTO.search("\n".join(h.corpo)))
    except Exception:
        sorgente = cmd
    testi = [cmd] + re.findall(r"\$\(([^()]*)\)", sorgente) + re.findall(r"`([^`]*)`", sorgente)
    righe = []
    for testo in testi:
        for nome, args in fc.programmi(testo):
            if nome == "xargs":
                resto = fc.xargs_resto(args)
                nome, args = (fc._nome(resto[0]), resto[1:]) if resto else ("", [])
            if nome == "gh":
                righe.append("gh " + " ".join(args))
    return "\n".join(righe)


def _api_write(cmd: str) -> str | None:
    """Motivo per chiedere conferma su un `gh api` che scrive, altrimenti None."""
    for match in re.finditer(r'\bgh\s+api\b[^|;&\n]*', cmd, re.IGNORECASE):
        seg = match.group(0)
        if re.search(r'\bgh\s+api\s+graphql\b', seg, re.IGNORECASE):
            if re.search(r'\bmutation\b', seg, re.IGNORECASE):
                return "mutazione GraphQL GitHub"
            if re.search(r'(?:^|\s)--input(?:\s|=|$)|=@', seg):
                return "query GraphQL letta da file: effetto non verificabile"
            continue
        # 21/11/2026 (#6259, S7): `-X $METODO` non si legge, e contava come GET.
        if re.search(r'(?:^|\s)(?:-X|--method)(?:\s+|=)?["\']?[$`]', seg):
            return "chiamata API GitHub con il metodo in una variabile: non si legge cosa fa"
        method = re.search(r'(?:^|\s)(?:-X|--method)(?:\s+|=)?([A-Za-z]+)', seg)
        body = re.search(r'(?:^|\s)(?:-f|-F|--field|--raw-field|--input)(?:\s|=|$)', seg)
        verb = method.group(1).upper() if method else ("POST" if body else "GET")
        if verb == "POST":
            return "chiamata API GitHub POST (anche implicita con -f/-F/--input)"
    return None


def main() -> int:
    try:
        if hasattr(signal, "SIGALRM"):
            signal.alarm(8)
        data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        if hasattr(signal, "SIGALRM"):
            signal.alarm(0)
    except Exception:
        return 0
    if data.get("tool_name") not in ("Bash", "Monitor"):  # Monitor lancia comandi shell (19/10/2026)
        return 0
    cmd = (data.get("tool_input") or {}).get("command", "")
    if not isinstance(cmd, str) or not cmd:
        return 0
    intero = cmd
    cmd = _con_alias(_testo_gh(intero))
    diretta = _api_github_diretta(intero)
    if diretta and diretta[0]:
        sys.stderr.write(f"Bloccato: {diretta[1]}. Operazione irreversibile/sensibile: "
                         "eseguila manualmente in un terminale se è intenzionale.\n")
        return 2

    for pat, why in BLOCK:
        if re.search(pat, cmd, re.IGNORECASE):
            sys.stderr.write(
                f"Bloccato: {why}. Operazione irreversibile/sensibile: "
                "eseguila manualmente in un terminale se è intenzionale.\n"
            )
            return 2

    cmd = _con_alias(_testo_gh(intero, pulito=True))
    reasons = [why for pat, why in ASK if re.search(pat, cmd, re.IGNORECASE)]
    if re.search(r'^gh alias-di-shell\b', cmd, re.MULTILINE):
        reasons.append("alias di gh che lancia un comando di shell")
    if diretta:
        reasons.append(diretta[1])
    api_write = _api_write(cmd)
    if api_write:
        reasons.append(api_write)
    if reasons:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                # Tutte le ragioni, non solo la prima: chi legge il motivo (un attenuatore, la persona) vede anche le
                # altre operazioni dello stesso comando (revisione del 20/11/2026).
                "permissionDecisionReason": f"Operazione gh: {'; '.join(dict.fromkeys(reasons))}. Conferma.",
            }
        }))
        return 0

    return 0


if __name__ == "__main__":
    # Claude Code scrive e legge in UTF-8. Su Windows la pipe è in cp1252 (16/10/2026).
    for _flusso in (sys.stdout, sys.stderr):
        try:
            _flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
