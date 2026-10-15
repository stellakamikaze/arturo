"""Gli heredoc di un comando Bash: dove comincia ognuno, chi ne riceve il corpo, cosa contiene.

Quattro guardie tolgono il corpo degli heredoc che nessuno esegue (block-dangerous, data-guard,
commit-secret-gate, comms-prefilter). Il testo che una guardia toglie è testo che non controlla:
un confine letto male nasconde un comando che la shell esegue. Per questo qui la regola è una sola.
Un corpo si può togliere solo se tutto è certo:
- l'apertura `<<` sta fuori da virgolette e commenti, e il delimitatore si legge intero;
- la chiusura è la riga identica al delimitatore (con `<<-`, preceduta solo da tab);
- il corpo va a un programma noto, non passa in una pipe, non sta dentro `$( )` o backtick,
  e il file in cui lo si scrive non viene eseguito dopo nello stesso comando.
Nel dubbio il corpo resta, e con lui tutto il resto del comando.

La regola su quale programma basta (un lettore come cat, o anche un interprete come python)
resta nella guardia, scritta come funzione su un `Heredoc`.
Solo libreria standard, Python 3.8 o successivo.
"""
from __future__ import annotations

import os
import re
from typing import Callable, List, NamedTuple, Optional, Tuple

# Programmi che leggono il corpo come dati e non eseguono niente.
LETTORI = frozenset("cat tee grep rg jq sort head tail wc patch diff git cut tr uniq less more column".split())
# Interpreti che eseguono il corpo come codice loro, non come shell.
INTERPRETI = frozenset("python python3 node ruby perl php".split())
# Parole che stanno davanti al programma senza esserlo, e involucri che eseguono il comando dopo.
_DAVANTI = frozenset("! { then do else elif if while until time".split())
_INVOLUCRI = frozenset("command builtin exec nohup nice env caffeinate".split())
# Codice di un interprete che lancia programmi: quel corpo resta visibile.
_ESEGUE = re.compile(r"subprocess|os\.system|os\.exec|os\.spawn|os\.popen|pty\.spawn|popen|child_process|"
                     r"\bsystem\s*\(|\bexec\s*\(|\beval\s*\(|`", re.IGNORECASE)
_ESECUTORI = (r"(?:^|[\s;&|(])(?:sudo\s+)?(?:\S*/)?(?:bash|sh|zsh|dash|ksh|fish|source|\.|python3?|node|perl|ruby|php|"
              r"exec|eval|chmod|xargs)(?=\s)")
_FINE_PAROLA = set(" \t;&|<>()")
_REDIREZIONE = re.compile(r">>?\s*([^\s;&|<>()]+)")


class Heredoc(NamedTuple):
    consumatore: str     # il programma che riceve il corpo, senza percorso; "" se non si sa
    delimitatore: str
    quotato: bool        # 'EOF', "EOF" o \EOF: la shell non espande il corpo
    corpo: List[str]
    certo: bool          # il corpo va solo al consumatore, e nessuno lo esegue dopo

    def espande(self) -> bool:
        """Delimitatore senza virgolette e `$(` o backtick nel corpo: la shell li esegue."""
        testo = "\n".join(self.corpo)
        return not self.quotato and ("$(" in testo or "`" in testo)

    def inerte(self) -> bool:
        """Il corpo va a un lettore (cat, tee, grep...) e nessuno lo esegue."""
        return self.certo and self.consumatore in LETTORI and not self.espande()

    def codice_inerte(self) -> bool:
        """Il corpo è codice di un interprete (python, node...) che non lancia programmi."""
        return (self.certo and self.consumatore in INTERPRETI and not self.espande()
                and not _ESEGUE.search("\n".join(self.corpo)))


class _Apertura(NamedTuple):
    inizio: int          # posizione di `<<` nella riga
    fine: int            # posizione dopo il delimitatore
    delimitatore: str
    quotato: bool
    tab: bool            # `<<-`: la chiusura può avere tab davanti
    segmento: int        # dove comincia il comando semplice che contiene `<<`
    annidato: bool       # dentro `$( )` o backtick


class _Stato:
    def __init__(self) -> None:
        self.apice = False
        self.doppio = False
        self.backtick = False
        self.sostituzioni = 0


def _delimitatore(riga: str, k: int) -> Tuple[str, bool, int]:
    """La parola del delimitatore da k: (delimitatore senza virgolette, quotato, posizione dopo)."""
    parola, quotato = [], False
    while k < len(riga) and riga[k] not in _FINE_PAROLA:
        c = riga[k]
        if c in "'\"":
            fine = riga.find(c, k + 1)
            if fine < 0:
                return "", True, len(riga)
            parola.append(riga[k + 1:fine])
            quotato, k = True, fine + 1
        elif c == "\\" and k + 1 < len(riga):
            parola.append(riga[k + 1])
            quotato, k = True, k + 2
        else:
            parola.append(c)
            k += 1
    return "".join(parola), quotato, k


def _scandisci(riga: str, stato: _Stato) -> Tuple[List[_Apertura], bool]:
    """Le aperture di heredoc della riga, fuori da virgolette e commenti. Vero = riga incerta."""
    aperture: List[_Apertura] = []
    segmento, k, n = 0, 0, len(riga)
    while k < n:
        c = riga[k]
        if stato.apice:
            stato.apice = c != "'"
            k += 1
            continue
        if c == "\\":
            k += 2
            continue
        if stato.doppio:
            if c == '"':
                stato.doppio = False
            elif c == "$" and riga.startswith("$(", k):
                stato.sostituzioni += 1
                k += 1
            elif c == "`":
                stato.backtick = not stato.backtick
            k += 1
            continue
        if c == "'":
            stato.apice = True
        elif c == '"':
            stato.doppio = True
        elif c == "#" and (k == 0 or riga[k - 1] in " \t;&|()"):
            break  # commento: il resto della riga non è comando
        elif c == "`":
            stato.backtick = not stato.backtick
            segmento = k + 1
        elif riga.startswith("$(", k):
            stato.sostituzioni += 1
            segmento = k + 2
            k += 2
            continue
        elif c == ")" and stato.sostituzioni:
            stato.sostituzioni -= 1
        elif c in ";|&({":
            segmento = k + 1
        elif riga.startswith("<<<", k):
            k += 3
            continue
        elif riga.startswith("<<", k):
            j = k + 2
            tab = j < n and riga[j] == "-"
            j += 1 if tab else 0
            while j < n and riga[j] in " \t":
                j += 1
            delim, quotato, dopo = _delimitatore(riga, j)
            if not delim or "$" in delim or "`" in delim:
                return aperture, True
            aperture.append(_Apertura(k, dopo, delim, quotato, tab, segmento,
                                      bool(stato.sostituzioni or stato.backtick)))
            k = dopo
            continue
        k += 1
    if stato.apice or stato.doppio:
        return aperture, bool(aperture)  # un heredoc su una riga con virgolette aperte: incerto
    return aperture, False


def _consumatore(testo: str) -> str:
    parole = [p for p in re.split(r"\s+", testo.strip()) if p]
    while parole and (parole[0] in _DAVANTI or re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", parole[0])):
        parole.pop(0)
    while parole and os.path.basename(parole[0]) in _INVOLUCRI:
        parole.pop(0)
        while parole and (parole[0].startswith("-") or re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", parole[0])):
            parole.pop(0)
    return os.path.basename(parole[0].lstrip("\\")) if parole else ""


def _bersagli(testo: str) -> List[str]:
    """I file in cui il comando scrive: redirezioni e argomenti di tee."""
    trovati = [m.group(1) for m in _REDIREZIONE.finditer(testo)]
    parole = testo.split()
    if parole and os.path.basename(parole[0]) == "tee":
        trovati += [p for p in parole[1:] if not p.startswith("-") and not p.startswith("<")]
    return [t.strip("'\"") for t in trovati if t.strip("'\"") not in ("/dev/null", "-", "")]


def _eseguito_dopo(prima: str, dopo: str, resto_riga: str, righe_dopo: List[str]) -> bool:
    """Il file in cui il comando scrive il corpo ricompare più avanti: `cat > x.sh <<'EOF' ... bash x.sh`.

    Il resto della riga di apertura si guarda senza la redirezione stessa.
    """
    bersagli = _bersagli(prima + " " + dopo)
    if not bersagli:
        return False
    resto = _REDIREZIONE.sub(" ", dopo, count=1) + "\n" + resto_riga + "\n" + "\n".join(righe_dopo)
    for b in bersagli:
        for nome in {b, os.path.basename(b)}:
            if not nome:
                continue
            parola = r"(?:\./)?" + re.escape(nome) + r"(?![\w.-])"
            # Dato a un esecutore (`bash x.sh`, `source x`, `python3 x.py`, `chmod +x x`), o lanciato
            # come comando (`./x.sh`). `git add x.sh` o `cat x.sh` non lo eseguono.
            if re.search(_ESECUTORI + r"[^\n;&|]*?(?<![\w./-])" + parola, resto) or \
                    re.search(r"(?:^|[;&|(]|\n)\s*" + parola, resto):
                return True
    return False


def togli(cmd: str, via: Callable[[Heredoc], bool], segnaposto: Optional[str] = None) -> str:
    """`cmd` senza il corpo degli heredoc per cui `via` dice sì.

    Senza `segnaposto` sparisce anche la riga di chiusura. Con il segnaposto il corpo diventa
    quella sola riga e la chiusura resta: il comando conserva la sua forma. Un heredoc senza
    chiusura, o una riga che non si legge con certezza, lasciano intero tutto il resto.
    """
    righe = cmd.split("\n")
    fuori: List[str] = []
    stato = _Stato()
    i = 0
    while i < len(righe):
        riga = righe[i]
        fuori.append(riga)
        i += 1
        aperture, incerta = _scandisci(riga, stato)
        if incerta or (aperture and riga.rstrip().endswith("\\")):
            fuori.extend(righe[i:])
            break
        for n, ap in enumerate(aperture):
            corpo: List[str] = []
            while i < len(righe) and not (righe[i] == ap.delimitatore or
                                          (ap.tab and righe[i].lstrip("\t") == ap.delimitatore)):
                corpo.append(righe[i])
                i += 1
            if i >= len(righe):  # senza chiusura: la shell legge fino in fondo, la guardia vede tutto
                fuori.extend(corpo)
                break
            chiusura = righe[i]
            i += 1
            prossima = aperture[n + 1].inizio if n + 1 < len(aperture) else len(riga)
            dopo = riga[ap.fine:prossima]
            seguito = righe[i].lstrip() if i < len(righe) else ""
            certo = not (ap.annidato
                         or re.search(r"(^|[^|])\|(?!\|)", dopo)
                         or riga.rstrip().endswith(("|", "&&", "||"))
                         or seguito.startswith(("|", ")", "&&", "||"))
                         or _eseguito_dopo(riga[ap.segmento:ap.inizio], dopo, riga[prossima:], righe[i:]))
            h = Heredoc(_consumatore(riga[ap.segmento:ap.inizio]), ap.delimitatore, ap.quotato, corpo, certo)
            if via(h):
                if segnaposto is not None:
                    fuori.extend((segnaposto, chiusura))
            else:
                fuori.extend(corpo)
                fuori.append(chiusura)
    return "\n".join(fuori)


def fuori_virgolette(testo: str, pos: int) -> bool:
    """Vero se la posizione `pos` di `testo` sta fuori da apici e doppi apici."""
    apice = doppio = False
    k = 0
    while k < pos:
        c = testo[k]
        if apice:
            apice = c != "'"
        elif c == "\\":
            k += 1
        elif doppio:
            doppio = c != '"'
        elif c == "'":
            apice = True
        elif c == '"':
            doppio = True
        k += 1
    return not apice and not doppio
