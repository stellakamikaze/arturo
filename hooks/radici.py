"""Le due radici di Arturo: dove sta il codice e dove stanno i dati della persona (strati F1, #4531).

Col clone le due radici coincidono: tutto sta in ~/.claude. Col plugin il codice sta nella cache dei
plugin e ~/.claude resta l'Orsa, la cartella della persona (docs/strati.md). Uno script che cerca il
proprio codice in ~/.claude/bin o ~/.claude/hooks funziona solo col clone: passa da qui.

  radice_arturo()   la cartella del codice: quella sopra questo file (hooks/..), in tutti e due i layout.
  radice_orsa()     la cartella della persona: CLAUDE_CONFIG_DIR se c'è, altrimenti ~/.claude.
  comando_arturo()  "python3 ~/.claude/bin/arturo" col clone, il percorso vero col plugin: per i
                    messaggi che dicono alla persona quale comando lanciare.
  file_locale(nome) una preferenza della persona (*.local): ~/.claude/arturo/<nome>, o il vecchio
                    percorso dato come ripiego finché la persona non l'ha spostata.

Da bin/ si importa con sys.path.insert(0, <bin>/../hooks). Solo libreria standard, Python 3.8 o
successivo.
"""
from __future__ import annotations

import os
from pathlib import Path


def radice_arturo() -> Path:
    """La cartella del codice di Arturo. Si calcola dal file, non dall'ambiente: ARTURO_CODICE e
    CLAUDE_PLUGIN_ROOT possono indicare un'altra copia (un banco, un secondo plugin), il file no."""
    return Path(os.path.realpath(__file__)).parent.parent


def radice_orsa() -> Path:
    """La cartella della persona, la stessa che usa Claude Code."""
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")


def _corto(percorso: Path) -> str:
    """Il percorso con ~ al posto della home, come la persona lo scriverebbe."""
    testo = str(percorso)
    for casa in (str(Path.home()), os.path.realpath(Path.home())):
        if testo == casa or testo.startswith(casa + os.sep):
            return "~" + testo[len(casa):].replace(os.sep, "/")
    return testo


def comando_arturo() -> str:
    """Il comando da far lanciare alla persona, col percorso vero di bin/arturo."""
    return "python3 " + _corto(radice_arturo() / "bin" / "arturo")


def file_locale(nome: str, vecchio: Path | None = None) -> Path:
    """Dove sta la preferenza `nome`: ~/.claude/arturo/<nome>. Se lì manca e il vecchio percorso
    esiste, vale il vecchio: le preferenze scritte prima degli strati restano valide."""
    nuovo = radice_orsa() / "arturo" / nome
    if not nuovo.exists() and vecchio is not None and vecchio.exists():
        return vecchio
    return nuovo
