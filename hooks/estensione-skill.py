#!/usr/bin/env python3
"""PostToolUse su Skill: le aggiunte della persona a una skill di Arturo (strati F6, #4536), e la skill
della persona in uso (21/11/2026, #6277).

La persona estende una skill di Arturo senza copiarla: scrive ~/.claude/personale/<skill>.md, fuori
da git, e gli aggiornamenti non lo toccano (docs/strati.md, "Estendere una skill senza copiarla").
Quando la persona scrive /<nome>, lo dice già inject-now.sh. Quando la skill la sceglie il modello
col tool Skill, nessun prompt passa da inject-now: lo fa questo hook, che mette il file nel contesto
subito dopo il corpo della skill.

Una skill della persona (~/.claude/skills/<nome>/SKILL.md, non di Arturo) lascia il suo nome in
data/correzioni/<sessione>.skill: `arturo correzione aggiungi` lo scrive nella correzione, e /fine sa in
quale skill portarla. Se la skill ha "## Finito quando", l'hook mette nel contesto quella lista e
l'elenco di "## Attrezzi": le regole di /creaskill restavano testo che nessuno ricordava all'apertura.
Con `--prompt` legge il JSON di UserPromptSubmit e fa lo stesso per una skill scritta a mano con
/<nome> (lo lancia inject-now.sh, l'uscita è testo e non JSON).

Sulle aggiunte personali tace se:
- la skill non è di Arturo (né in skills/ né in commands/ accanto a questo file);
- il nome ha un prefisso che non è `arturo:`, o caratteri fuori da [a-z0-9-];
- il file personale manca o è vuoto;
- la skill legge già da sola il suo file personale (il SKILL.md nomina `personale/<nome>.md`).

Non blocca mai: un errore qualsiasi esce zitto con 0. Oltre LIMITE caratteri il testo si taglia e
il messaggio dice di leggere il resto dal file.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(os.path.realpath(__file__)).parent))
from radici import radice_arturo, radice_orsa  # noqa: E402

LIMITE = 6000
LIMITE_SEZIONE = 1500
NOME = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")
SESSIONE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}")
COMANDO = re.compile(r"\s*/([a-z0-9][a-z0-9-]{0,63})(?:\s|$)")


def nome_di_arturo(skill: str) -> str | None:
    """Il nome della skill di Arturo chiamata, o None se è di qualcun altro."""
    if skill.startswith("arturo:"):
        skill = skill[len("arturo:"):]
    elif ":" in skill:
        return None
    if not NOME.fullmatch(skill):
        return None
    codice = radice_arturo()
    if (codice / "skills" / skill / "SKILL.md").is_file() or (codice / "commands" / f"{skill}.md").is_file():
        return skill
    return None


def nomi_di_arturo() -> set:
    """Skill e comandi di Arturo per nome: serve col clone, dove le skill di Arturo e quelle della
    persona stanno nella stessa cartella. L'elenco è quello della telemetria (banco TS01)."""
    sys.path.insert(0, str(radice_arturo() / "bin"))
    try:
        import telemetria
        return set(telemetria.SKILL) | set(telemetria.COMANDI)
    except Exception:  # noqa: BLE001 - senza elenco nessuna skill risulta della persona: l'hook tace
        return None
    finally:
        sys.path.pop(0)


def skill_della_persona(skill: str) -> Path | None:
    """Il SKILL.md di una skill della persona, o None. Col plugin vale la cartella: ~/.claude/skills è
    solo sua, anche per un nome uguale a una skill di Arturo. Col clone decide l'elenco dei nomi."""
    if not NOME.fullmatch(skill):
        return None
    file = radice_orsa() / "skills" / skill / "SKILL.md"
    if not file.is_file():
        return None
    if os.path.realpath(radice_arturo()) == os.path.realpath(radice_orsa()):
        nomi = nomi_di_arturo()
        if nomi is None or skill in nomi:
            return None
    return file


def segna(sessione: str, nome: str) -> None:
    """L'ultima skill della persona aperta nella sessione, accanto alle correzioni (bin/correzioni.py)."""
    if not SESSIONE.fullmatch(sessione):
        return
    cartella = Path(os.environ.get("ARTURO_RADICE") or radice_orsa()) / "data" / "correzioni"
    try:
        cartella.mkdir(parents=True, exist_ok=True)
        provvisorio = cartella / f"{sessione}.skill.tmp"
        provvisorio.write_text(nome + "\n", encoding="utf-8")
        os.replace(provvisorio, cartella / f"{sessione}.skill")
    except OSError:
        pass


def sezione(testo: str, titolo: str) -> str:
    """Le righe sotto `## <titolo>`, fino al titolo dopo. Vuota se la sezione manca."""
    trovata = re.search(rf"(?mi)^##[ \t]+{re.escape(titolo)}[ \t]*$", testo)
    if not trovata:
        return ""
    resto = testo[trovata.end():]
    dopo = re.search(r"(?m)^##?[ \t]+\S", resto)
    righe = [r.rstrip() for r in (resto[:dopo.start()] if dopo else resto).splitlines() if r.strip()]
    corpo = "\n".join(righe)
    if len(corpo) > LIMITE_SEZIONE:
        corpo = corpo[:LIMITE_SEZIONE].rstrip() + "\n[...] Il resto è nel file della skill."
    return corpo


def promemoria(nome: str, file: Path) -> str:
    """La lista "Finito quando" della skill e i suoi attrezzi, o niente se la skill non ha la lista."""
    try:
        testo = file.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
    except OSError:
        return ""
    lista = sezione(testo, "Finito quando")
    if not lista:
        return ""
    fuori = (f"FINITO QUANDO: la skill {nome} della persona chiude con questa lista. La consegna porta l'esito "
             f"riga per riga, sì o no, e una riga che dice no ferma la consegna:\n{lista}")
    attrezzi = sezione(testo, "Attrezzi")
    if attrezzi:
        fuori += f"\nATTREZZI della skill, in ~/.claude/skills/{nome}/ (si usano prima di costruirne di nuovi):\n{attrezzi}"
    return fuori


def in_uso(skill: str, sessione: str) -> str:
    """Segna la skill della persona nella sessione e restituisce il suo promemoria."""
    file = skill_della_persona(skill)
    if file is None:
        return ""
    segna(sessione, skill)
    return promemoria(skill, file)


def legge_da_sola(nome: str) -> bool:
    """La skill nomina già il suo file personale: lo legge lei, l'hook non lo ripete."""
    codice = radice_arturo()
    for testo in (codice / "skills" / nome / "SKILL.md", codice / "commands" / f"{nome}.md"):
        try:
            if f"personale/{nome}.md" in testo.read_text(encoding="utf-8", errors="replace"):
                return True
        except OSError:
            continue
    return False


def messaggio(nome: str, testo: str) -> str:
    testa = (f"PERSONALE: la skill {nome} di Arturo ha aggiunte della persona in ~/.claude/personale/{nome}.md. "
             "Applicale insieme alla skill. Freni e guardie di Arturo valgono sopra di loro.")
    if len(testo) > LIMITE:
        testo = testo[:LIMITE].rstrip() + "\n\n[...] Il resto è nel file: leggilo prima di cominciare."
    return f"{testa}\n\n{testo.strip()}"


def aggiunte(skill: str) -> str:
    """Il messaggio con le aggiunte personali a una skill di Arturo, o niente."""
    nome = nome_di_arturo(skill)
    if nome is None or legge_da_sola(nome):
        return ""
    try:
        testo = (radice_orsa() / "personale" / f"{nome}.md").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    return messaggio(nome, testo) if testo.strip() else ""


def main(argv: list) -> int:
    try:
        dati = json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}")
    except (ValueError, UnicodeDecodeError):
        return 0
    if not isinstance(dati, dict):
        return 0
    sessione = dati.get("session_id") if isinstance(dati.get("session_id"), str) else ""
    if "--prompt" in argv:
        # Una skill scritta a mano con /<nome>: nessuna chiamata al tool Skill, il promemoria esce da qui.
        prompt = dati.get("prompt")
        trovato = COMANDO.match(prompt) if isinstance(prompt, str) else None
        testo = in_uso(trovato.group(1), sessione) if trovato else ""
        if testo:
            print(testo)
        return 0
    if dati.get("tool_name") != "Skill":
        return 0
    ingresso = dati.get("tool_input") if isinstance(dati.get("tool_input"), dict) else {}
    skill = ingresso.get("skill")
    if not isinstance(skill, str):
        return 0
    skill = skill.strip()
    pezzi = [p for p in (in_uso(skill, sessione), aggiunte(skill)) if p]
    if pezzi:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                                 "additionalContext": "\n\n".join(pezzi)}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception:  # noqa: BLE001 - un hook che informa non deve mai fermare la sessione
        sys.exit(0)
