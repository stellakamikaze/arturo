#!/usr/bin/env python3
"""Le skill della persona e le due sezioni di /creaskill: "Finito quando" e "Attrezzi" (21/11/2026, #6277).

  python3 ~/.claude/bin/skill_sezioni.py elenco          una riga per fatto, per /system-audit:
                                                         SKILL|<quante>, SENZA|<nome>, ATTREZZO|<nome>|<file>
  python3 ~/.claude/bin/skill_sezioni.py stato <nome>    per /creaskill: ASSENTE, ARTURO, COMPLETA oppure
                                                         MANCA|<sezioni che mancano, con la virgola>

Una skill nata prima del 20/11/2026 non ha le due sezioni e funziona lo stesso: qui non c'è mai un errore,
solo il conto. `/system-audit` ne fa un WARN, `arturo revisione igiene` una riga, `/creaskill <nome>` le
aggiunge dopo il sì della persona.

Una skill è della persona se sta in ~/.claude/skills/<nome>/SKILL.md e non è di Arturo. Col plugin la
cartella è solo sua. Col clone le skill di Arturo stanno nella stessa cartella: decide l'elenco di
bin/telemetria.py, come in hooks/estensione-skill.py. Restano fuori i mod (.claude-plugin), le cartelle
nascoste, shared, synced e le skill che la persona installa dal loro autore.
Banco: skills/system-audit/tests/banco-gate.sh, RV11 in tests/test_revisione_2026_11_17.py.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

sys.path.append(str(Path(os.path.realpath(__file__)).parent.parent / "hooks"))
sys.path.insert(0, str(Path(os.path.realpath(__file__)).parent))
from radici import radice_arturo, radice_orsa  # noqa: E402

SEZIONI = ("Finito quando", "Attrezzi")
NOME = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")
# Skill che la persona installa dall'autore (/setup fase 8c): non le ha scritte lei, non si toccano.
UPSTREAM = {"impeccable", "hallmark", "diagram-design"}
FUORI = {"shared", "synced"}
# Un attrezzo è un file: un nome con l'estensione, anche con un percorso davanti.
FILE = re.compile(r"(?<![\w./~-])((?:~/|/|\./)?(?:[\w.-]+/)*[\w-][\w.-]*\.[A-Za-z][A-Za-z0-9]{0,5})(?![\w/-])")


def nomi_di_arturo() -> set:
    try:
        import telemetria
        return set(telemetria.SKILL) | set(telemetria.COMANDI)
    except Exception:  # noqa: BLE001 - senza elenco nessuna skill risulta della persona: il controllo tace
        return None


def sezione(testo: str, titolo: str) -> str | None:
    """Le righe sotto `## <titolo>` fino al titolo dopo. None se il titolo manca."""
    trovata = re.search(rf"(?mi)^##[ \t]+{re.escape(titolo)}[ \t]*$", testo)
    if not trovata:
        return None
    resto = testo[trovata.end():]
    dopo = re.search(r"(?m)^##?[ \t]+\S", resto)
    return "\n".join(r.rstrip() for r in (resto[:dopo.start()] if dopo else resto).splitlines() if r.strip())


def di_arturo(nome: str, orsa: Path, codice: Path) -> bool:
    """Col clone decide l'elenco dei nomi. Col plugin ~/.claude/skills è della persona."""
    if os.path.realpath(codice) != os.path.realpath(orsa):
        return False
    nomi = nomi_di_arturo()
    return nomi is None or nome in nomi


def skill_della_persona(orsa: Path, codice: Path) -> list:
    """[(nome, SKILL.md)] in ordine di nome."""
    cartella = orsa / "skills"
    trovate = []
    try:
        voci = sorted(cartella.iterdir())
    except OSError:
        return trovate
    for d in voci:
        nome = d.name
        if not d.is_dir() or nome.startswith(".") or nome in FUORI or nome in UPSTREAM:
            continue
        if (d / ".claude-plugin").exists() or not (d / "SKILL.md").is_file():
            continue
        if di_arturo(nome, orsa, codice):
            continue
        trovate.append((nome, d / "SKILL.md"))
    return trovate


def leggi(file: Path) -> str:
    try:
        return file.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
    except OSError:
        return ""


def mancanti(testo: str) -> list:
    """Le sezioni che la skill non ha. "Finito quando" vuota vale come assente: non c'è niente da controllare."""
    fuori = []
    for titolo in SEZIONI:
        corpo = sezione(testo, titolo)
        if corpo is None or (titolo == "Finito quando" and not corpo.strip()):
            fuori.append(titolo)
    return fuori


def attrezzi_assenti(testo: str, cartella: Path) -> list:
    """I file citati in "Attrezzi" che non ci sono. Un percorso relativo parte dalla cartella della skill."""
    corpo = sezione(testo, "Attrezzi") or ""
    assenti = []
    for riga in corpo.splitlines():
        if "://" in riga:
            riga = re.sub(r"\S+://\S+", " ", riga)
        # Prima i nomi fra backtick: sono quelli che la riga dichiara. Senza backtick, i nomi con l'estensione.
        pezzi = [p for blocco in re.findall(r"`([^`]+)`", riga) for p in blocco.split()] or [riga]
        for pezzo in pezzi:
            for nome in FILE.findall(pezzo):
                file = Path(os.path.expanduser(nome))
                if not file.is_absolute():
                    file = cartella / file
                if not file.exists() and nome not in assenti:
                    assenti.append(nome)
    return assenti


def conto(orsa: Path | None = None, codice: Path | None = None) -> dict:
    """{"skill": [nomi], "senza": [nomi senza Finito quando], "attrezzi": [(nome, file assente)]}."""
    orsa, codice = orsa or radice_orsa(), codice or radice_arturo()
    esito = {"skill": [], "senza": [], "attrezzi": []}
    for nome, file in skill_della_persona(orsa, codice):
        testo = leggi(file)
        esito["skill"].append(nome)
        if "Finito quando" in mancanti(testo):
            esito["senza"].append(nome)
        esito["attrezzi"] += [(nome, a) for a in attrezzi_assenti(testo, file.parent)]
    return esito


def stato(nome: str, orsa: Path | None = None, codice: Path | None = None) -> str:
    orsa, codice = orsa or radice_orsa(), codice or radice_arturo()
    if not NOME.fullmatch(nome):
        return "ASSENTE"
    file = orsa / "skills" / nome / "SKILL.md"
    suo = (codice / "skills" / nome / "SKILL.md").is_file() or (codice / "commands" / f"{nome}.md").is_file()
    if suo and (di_arturo(nome, orsa, codice) or not file.is_file()):
        return "ARTURO"
    if not file.is_file():
        return "ASSENTE"
    manca = mancanti(leggi(file))
    return "MANCA|" + ", ".join(manca) if manca else "COMPLETA"


def main(argv: list) -> int:
    if argv[:1] == ["elenco"] and len(argv) == 1:
        c = conto()
        print(f"SKILL|{len(c['skill'])}")
        for nome in c["senza"]:
            print(f"SENZA|{nome}")
        for nome, file in c["attrezzi"]:
            print(f"ATTREZZO|{nome}|{file}")
        return 0
    if argv[:1] == ["stato"] and len(argv) == 2:
        print(stato(argv[1].strip().lstrip("/")))
        return 0
    print(__doc__.strip().split("\n\n")[1], file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
