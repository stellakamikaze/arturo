#!/usr/bin/env python3
"""Melchior PostToolUse hook.

Intercetta Write/Edit/MultiEdit su ~/.claude/data/memory/*.md e:
1. Auto-aggiorna campo `updated:` a oggi
2. Confronta il frontmatter con lo schema di docs/memoria.md (name, description, type, anche
   dentro `metadata:`) e logga i campi che mancano. Non blocca niente.
2b. Valida che il frontmatter sia YAML PARSABILE con melchior_match.problemi_frontmatter, l'unico
   controllo della forma — un ': ' in uno scalare non quotato o un '#' in una flow sequence lo
   rendono illeggibile a ogni tool che usa PyYAML (3 occorrenze fra il 18 e il 19/8/2026).
   L'hook e' asincrono: exit 2 e stderr non arrivano a Claude. Il motivo va in
   additionalContext (JSON su stdout), che arriva al turno dopo (review 7/11/2026).
3. Scrive audit entry in ~/.claude/data/memory/.melchior-log.jsonl
4. Smista nella cartella giusta una nota NUOVA scritta nella radice della memoria
   (Write, non Edit), secondo il suo `type` (melchior_match.cartella_nuova: user in profilo/,
   feedback in feedback/, project in progetti/, reference in reference/). Un prefisso del nome
   della memoria di chi mantiene Arturo (`errore-`, `persona-`, ...) vale prima del type.
   L'auto-memory nativa di Claude Code scrive nella radice: il 19/10/2026 c'erano 22 note sciolte.
   Né type né prefisso, o destinazione già occupata: la nota resta dov'è e si logga.
   Claude riceve il percorso nuovo, o l'invito a fondere le due note omonime.

Agisce SOLO dentro ~/.claude/data/memory (percorso reale). Le note delle altre radici di
melchior_match (~/.claude/projects/*/memory, le cartelle aggiunte) non si toccano mai: niente
date aggiunte, niente spostamenti, niente controllo. Sono della persona o di Claude Code, e
restano come sono. Memoria spenta (melchior_match.memoria_accesa): esce subito.

Non-blocking: se qualcosa fallisce, esci 0 silenziosamente.
Input JSON da stdin (schema Claude Code hooks).
Zero dipendenze (stdlib).
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import date
from pathlib import Path
sys.path.append(str(Path(os.path.realpath(__file__)).parent))
from radici import radice_orsa  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    import melchior_match as _mm
except ImportError:
    _mm = None

MEMORY_DIR = radice_orsa() / "data" / "memory"
LOG_FILE = MEMORY_DIR / ".melchior-log.jsonl"
FACOLTATIVI = ("alias", "cartella", "triggers")
TODAY = date.today().isoformat()


def smista_nota_radice(path: Path, tool_name: str, fm: dict | None) -> dict | None:
    """Sposta una nota appena creata nella radice della memoria nella cartella del suo type
    (o del suo prefisso). Ritorna l'evento da loggare, None se non c'è niente da fare."""
    try:
        if _mm is None or tool_name != "Write" or path.parent.resolve() != MEMORY_DIR.resolve():
            return None
        if path.name in ("MEMORY.md", "index.md") or path.name.startswith(("_", ".")):
            return None
        cartella = _mm.cartella_nuova(path.name, fm)
        if cartella is None:
            return {"action": "melchior-smistamento-saltato", "file": path.name,
                    "motivo": "né type né prefisso dicono la cartella"}
        dest = MEMORY_DIR / cartella / path.name
        if dest.exists():
            return {"action": "melchior-smistamento-saltato", "file": path.name,
                    "motivo": f"esiste già {cartella}/{path.name}", "dest": f"{cartella}/{path.name}"}
        dest.parent.mkdir(parents=True, exist_ok=True)
        path.rename(dest)
        return {"action": "melchior-smistata", "file": path.name, "dest": f"{cartella}/{path.name}"}
    except Exception as e:
        return {"action": "melchior-smistamento-errore", "file": path.name, "errore": str(e)[:200]}


def log_event(entry: dict) -> None:
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def extract_path(payload: dict) -> str | None:
    # Claude Code hooks payload: tool_input.file_path per Edit/Write
    tool_input = payload.get("tool_input") or {}
    return tool_input.get("file_path")


def is_memory_file(path_str: str) -> bool:
    if not path_str:
        return False
    try:
        p = Path(path_str).resolve()
        md = MEMORY_DIR.resolve()
        if md not in p.parents:
            return False
        rel_parts = p.relative_to(md).parts
        if "_archive" in rel_parts:
            return False
        return p.suffix == ".md" and p.name != "MEMORY.md"
    except Exception:
        return False


def parse_frontmatter(text: str) -> tuple[dict | None, str, str]:
    """Ritorna (fm_dict | None, raw_fm_block, rest)."""
    # [ \t]* e non \s*: \s* passa l'a capo e mangia righe vuote e rientro del corpo (review 7/11, finding 50).
    m = re.match(r"^(---[ \t]*\n)(.*?)(\n---[ \t]*\n?)", text, re.DOTALL)
    if not m:
        return None, "", text
    raw = m.group(2)
    rest = text[m.end():]
    fm = {}
    for line in raw.split("\n"):
        mk = re.match(r"^([a-zA-Z_][\w-]*):[ \t]*(.*)$", line)
        if mk:
            fm[mk.group(1)] = mk.group(2).strip()
    return fm, raw, rest


def update_updated_field(text: str) -> tuple[str, bool]:
    """Se frontmatter esiste e `updated:` != TODAY, lo aggiorna. Ritorna (nuovo_testo, changed)."""
    fm, raw, rest = parse_frontmatter(text)
    if fm is None:
        return text, False
    current = fm.get("updated", "").strip().strip('"\'')
    if current == TODAY:
        return text, False
    if "updated" in fm:
        new_raw = re.sub(
            r"^updated:[ \t]*.*$",  # un "updated:" vuoto non si prende la riga dopo (finding 50)
            f"updated: {TODAY}",
            raw,
            count=1,
            flags=re.MULTILINE,
        )
    else:
        new_raw = raw.rstrip() + f"\nupdated: {TODAY}"
    new_text = f"---\n{new_raw}\n---\n{rest}"
    return new_text, True


def ensure_created_field(text: str) -> tuple[str, bool]:
    """Se il frontmatter esiste e manca `created:`, lo aggiunge = TODAY (immutabile).
    Non tocca mai un created gia' presente. Serve alle note NUOVE: la freschezza
    si basa su last_verified||created, non su updated (auto-bumpato a ogni edit)."""
    fm, raw, rest = parse_frontmatter(text)
    if fm is None or "created" in fm:
        return text, False
    new_raw = raw.rstrip() + f"\ncreated: {TODAY}"
    return f"---\n{new_raw}\n---\n{rest}", True



def frontmatter_parse_error(text: str) -> str | None:
    """None se il frontmatter si legge come YAML, altrimenti il primo motivo grave in una riga.
    Il controllo è uno solo, melchior_match.problemi_frontmatter: lo stesso di
    `arturo memoria controlla`. Chi legge le note con PyYAML non vede una nota rotta."""
    if _mm is None:
        return None
    gravi = [motivo for grave, motivo in _mm.problemi_frontmatter(text) if grave]
    return gravi[0] if gravi else None


def main() -> int:
    if _mm is not None and not _mm.memoria_accesa():
        return 0
    try:
        raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
        if not raw.strip():
            return 0
        payload = json.loads(raw)
    except Exception:
        return 0

    path_str = extract_path(payload)
    if not is_memory_file(path_str or ""):
        return 0

    path = Path(path_str)
    if not path.exists():
        return 0

    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return 0

    tool_name = payload.get("tool_name", "?")
    actions = []

    new_text, changed = update_updated_field(text)
    new_text, created_added = ensure_created_field(new_text)
    # v3-10 (24/10/2026): last_verified non si aggiorna più a ogni modifica. Dichiara
    # "l'ho guardata contro il mondo" e lo scrive solo chi ha fatto una sonda o una
    # rilettura di giudizio (R9). Una modifica di forma non è una verifica.
    if changed or created_added:
        try:
            path.write_text(new_text, encoding="utf-8")
            if changed:
                actions.append("updated")
            if created_added:
                actions.append("created")
        except Exception:
            pass

    # L'hook è asincrono: exit 2 e stderr non arrivano a Claude, additionalContext sì, al turno dopo
    # (review del 7/11/2026, finding 51 e 52).
    avvisi = []
    parse_err = frontmatter_parse_error(new_text)
    if parse_err:
        log_event({
            "ts": TODAY, "tool": tool_name, "file": path.name,
            "actions": actions, "parse_error": parse_err,
            "action": "melchior-frontmatter-invalido",
        })
        avvisi.append(
            f"[melchior] il frontmatter di {path.name} non è YAML valido: {parse_err}. La nota è scritta, "
            f"ma chi legge il frontmatter come YAML non la vede. Metti lo scalare fra virgolette "
            f"(o chiudi la lista fra quadre) e riscrivila."
        )

    fm = _mm.frontmatter(new_text)[0] if _mm is not None else None
    if _mm is not None:
        missing_core = [k for k in _mm.CAMPI_RICHIESTI if not _mm.campo(fm, k)]
        missing_optional = [k for k in FACOLTATIVI if not _mm.campo(fm, k)]
    else:
        missing_core, missing_optional = [], []

    if actions or missing_core or missing_optional:
        log_event({
            "ts": TODAY,
            "tool": tool_name,
            "file": path.name,
            "actions": actions,
            "missing_core": missing_core,
            "missing_optional": missing_optional,
            "action": "melchior-auto-postwrite",
        })

    smistata = smista_nota_radice(path, tool_name, fm)
    if smistata:
        log_event({"ts": TODAY, "tool": tool_name, **smistata})
        avviso = avviso_smistamento(path, smistata)
        if avviso:
            avvisi.append(avviso)

    if avvisi:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                                 "additionalContext": "\n".join(avvisi)}}, ensure_ascii=False))
    return 0


def avviso_smistamento(path: Path, evento: dict) -> str | None:
    """Claude tiene il percorso che ha scritto: gli si dice dove è finita la nota, o perché è rimasta."""
    if evento.get("action") == "melchior-smistata":
        return (f"[melchior] la nota {path.name} è stata spostata in {MEMORY_DIR / evento['dest']}: "
                f"per correggerla usa quel percorso.")
    motivo = str(evento.get("motivo", ""))
    if motivo.startswith("esiste già") and evento.get("dest"):
        return (f"[melchior] {path.name} resta nella radice della memoria perché {motivo}: ora ci sono due note "
                f"con lo stesso nome. Fondi questa in {MEMORY_DIR / evento['dest']} "
                f"e cancella la copia nella radice.")
    return None


if __name__ == "__main__":
    # Claude Code scrive e legge in UTF-8. Su Windows la pipe è in cp1252 (16/10/2026).
    for _flusso in (sys.stdout, sys.stderr):
        try:
            _flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
