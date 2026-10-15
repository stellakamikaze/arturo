"""Gli heredoc di un comando Bash: dove comincia ognuno, chi ne riceve il corpo, cosa contiene.

Quattro guardie tolgono il corpo degli heredoc che la shell non esegue (block-dangerous,
data-guard, commit-secret-gate, comms-prefilter). Fino al 15/10/2026 ognuna aveva il suo
parser, e le copie divergevano: due non vedevano `cat <<'EOF' | bash`, e tutte leggevano la
here-string `<<<"x"` come un heredoc che inghiotte il resto del comando.

Qui sta il riconoscimento, una volta sola. La regola su cosa togliere resta nella guardia,
scritta come funzione su un `Heredoc`. Un heredoc senza riga di chiusura resta sempre
visibile: la guardia vede il testo intero invece di perderne la coda.
Solo libreria standard, Python 3.8 o successivo.
"""
from __future__ import annotations

import re
from typing import Callable, List, NamedTuple, Optional

# `<<EOF`, `<<-EOF`, `<< 'EOF'`, `<<"EOF"`. Non `<<<`, la here-string, che non ha corpo.
APERTURA = re.compile(r"(?<!<)<<(?!<)-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")
# Programmi che eseguono come shell il corpo che ricevono.
SHELL = frozenset("bash sh zsh fish ksh dash eval source ssh".split())


class Heredoc(NamedTuple):
    prima: str           # la riga di apertura fino a `<<`, dal delimitatore precedente se c'è
    dopo: str            # la riga di apertura dopo il delimitatore, fino al prossimo `<<`
    delimitatore: str
    quotato: bool        # 'EOF' o "EOF": la shell non espande il corpo
    corpo: List[str]
    chiuso: bool         # trovata la riga di chiusura

    def verso_shell(self, nomi=SHELL) -> bool:
        """Il corpo arriva a una shell: `bash <<EOF`, oppure `cat <<'EOF' | bash`.

        Basta un nome di `nomi` come parola ovunque prima di `<<`: meglio un corpo
        controllato per troppo che uno tolto per una shell non vista.
        """
        alternative = "|".join(sorted(nomi))
        if re.search(r"\b(?:%s)\b" % alternative, self.prima):
            return True
        return bool(re.search(r"\|\s*(?:sudo\s+)?(?:%s|xargs)\b" % alternative, self.dopo))

    def espande(self) -> bool:
        """Delimitatore senza virgolette e `$(` o backtick nel corpo: la shell li esegue."""
        testo = "\n".join(self.corpo)
        return not self.quotato and ("$(" in testo or "`" in testo)


def togli(cmd: str, via: Callable[[Heredoc], bool], segnaposto: Optional[str] = None) -> str:
    """`cmd` senza il corpo degli heredoc per cui `via` dice sì.

    Senza `segnaposto` sparisce anche la riga di chiusura. Con il segnaposto il corpo
    diventa quella sola riga e la chiusura resta: il comando conserva la sua forma.
    Un heredoc senza chiusura resta intero, qualunque cosa dica `via`.
    Più heredoc sulla stessa riga (`cmd <<A <<B`) si leggono uno dopo l'altro.
    """
    righe = cmd.split("\n")
    fuori: List[str] = []
    i = 0
    while i < len(righe):
        riga = righe[i]
        fuori.append(riga)
        i += 1
        aperture = list(APERTURA.finditer(riga))
        for n, m in enumerate(aperture):
            inizio = aperture[n - 1].end() if n else 0
            fine = aperture[n + 1].start() if n + 1 < len(aperture) else len(riga)
            corpo: List[str] = []
            while i < len(righe) and righe[i].strip() != m.group(2):
                corpo.append(righe[i])
                i += 1
            chiuso = i < len(righe)
            h = Heredoc(prima=riga[inizio:m.start()], dopo=riga[m.end():fine], delimitatore=m.group(2),
                        quotato=bool(m.group(1)), corpo=corpo, chiuso=chiuso)
            if not chiuso:
                fuori.extend(corpo)
            elif via(h):
                if segnaposto is not None:
                    fuori.extend((segnaposto, righe[i]))
                i += 1
            else:
                fuori.extend(corpo)
                fuori.append(righe[i])
                i += 1
    return "\n".join(fuori)

