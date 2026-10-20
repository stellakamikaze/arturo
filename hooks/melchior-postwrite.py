#!/usr/bin/env python3
"""Melchior PostToolUse hook.

Intercetta Write/Edit/MultiEdit su ~/.claude/data/memory/*.md e:
1. Auto-aggiorna campo `updated:` a oggi
2. Valida frontmatter v2 (log WARN se campi mancanti non-critici)
2b. Valida che il frontmatter sia YAML PARSABILE — un ': ' in uno scalare non
   quotato o un '#' in una flow sequence lo rendono illeggibile a ogni tool che
   usa PyYAML, senza che nulla se ne accorga (3 occorrenze fra il 18 e il 19/8).
   Questo e' l'unico caso in cui l'hook parla: exit 2 con il motivo, cosi' chi ha
   scritto lo corregge subito invece di lasciare una nota invisibile.
3. Scrive audit entry in ~/.claude/data/memory/.melchior-log.jsonl
4. Smista nella cartella giusta una nota NUOVA scritta nella radice della memoria
   (Write, non Edit), secondo il prefisso del nome (SMISTAMENTO). L'auto-memory
   nativa di Claude Code scrive nella radice: il 19/10/2026 c'erano 22 note sciolte.
   Prefisso sconosciuto o destinazione già occupata: la nota resta dov'è e si logga.

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

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    import melchior_match as _mm
except ImportError:
    _mm = None

MEMORY_DIR = Path.home() / ".claude" / "data" / "memory"
LOG_FILE = MEMORY_DIR / ".melchior-log.jsonl"
V2_CORE = {"name", "description", "type", "entity_type", "updated"}
V2_FULL = V2_CORE | {"answers", "triggers", "sources"}
TODAY = date.today().isoformat()
# prefisso del nome file -> cartella (il primo che combacia vince)
SMISTAMENTO = (
    ("errore-", "errori"),
    ("feedback-", "feedback"),
    ("reference-", "reference"),
    ("progetto-", "progetti"),
    ("persona-", "persone"),
    ("pattern-", "pattern"),
    ("sistema-", "sistemi"),
    ("incidente-", "sistemi"),
)


def smista_nota_radice(path: Path, tool_name: str) -> dict | None:
    """Sposta una nota appena creata nella radice della memoria nella cartella del
    suo prefisso. Ritorna l'evento da loggare, None se non c'è niente da fare."""
    try:
        if tool_name != "Write" or path.parent.resolve() != MEMORY_DIR.resolve():
            return None
        if path.name in ("MEMORY.md", "index.md") or path.name.startswith(("_", ".")):
            return None
        cartella = next((c for pref, c in SMISTAMENTO if path.name.startswith(pref)), None)
        if cartella is None:
            return {"action": "melchior-smistamento-saltato", "file": path.name,
                    "motivo": "prefisso senza cartella"}
        dest = MEMORY_DIR / cartella / path.name
        if dest.exists():
            return {"action": "melchior-smistamento-saltato", "file": path.name,
                    "motivo": f"esiste già {cartella}/{path.name}"}
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
    m = re.match(r"^(---\s*\n)(.*?)(\n---\s*\n?)", text, re.DOTALL)
    if not m:
        return None, "", text
    raw = m.group(2)
    rest = text[m.end():]
    fm = {}
    for line in raw.split("\n"):
        mk = re.match(r"^([a-zA-Z_][\w-]*):\s*(.*)$", line)
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
            r"^(updated:\s*).*$",
            f"updated: {TODAY}",
            raw,
            count=1,
            flags=re.MULTILINE,
        )
    else:
        new_raw = raw.rstrip() + f"\nupdated: {TODAY}"
    new_text = f"---\n{new_raw}\n---\n{rest}"
    return new_text, True


_FM_LINE = re.compile(r"^\s*(?:---\s*|[a-zA-Z_]\w*:.*|-\s+.*)?$")


def looks_like_content_edit(payload: dict) -> bool:
    """True se la scrittura tocca il CORPO della nota, non solo il frontmatter.
    Chi riscrive il contenuto ha riletto i fatti → last_verified bumpa da solo
    (R6: la disciplina manuale di bump aveva conversione ~10%, è morta).
    Write di file intero = sempre contenuto. Edit = contenuto se il new_string
    ha almeno una riga che non sembra frontmatter (key:, lista, ---)."""
    ti = payload.get("tool_input") or {}
    if isinstance(ti.get("content"), str):
        return True
    chunks = []
    if isinstance(ti.get("new_string"), str):
        chunks.append(ti["new_string"])
    for e in ti.get("edits") or []:
        if isinstance(e, dict) and isinstance(e.get("new_string"), str):
            chunks.append(e["new_string"])
    for c in chunks:
        for line in c.split("\n"):
            if line.strip() and not _FM_LINE.match(line):
                return True
    return False


def update_last_verified_field(text: str) -> tuple[str, bool]:
    """Bumpa (o aggiunge) last_verified: TODAY nel frontmatter."""
    fm, raw, rest = parse_frontmatter(text)
    if fm is None:
        return text, False
    current = fm.get("last_verified", "").strip().strip('"\'')
    if current == TODAY:
        return text, False
    if "last_verified" in fm:
        new_raw = re.sub(
            r"^(last_verified:\s*).*$",
            f"last_verified: {TODAY}",
            raw,
            count=1,
            flags=re.MULTILINE,
        )
    else:
        new_raw = raw.rstrip() + f"\nlast_verified: {TODAY}"
    return f"---\n{new_raw}\n---\n{rest}", True


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
    """None se il frontmatter e' YAML valido, altrimenti il motivo in una riga.

    Il parser interno di questo hook e' regex riga-per-riga: legge i campi ma NON
    si accorge se il blocco e' YAML invalido. Chi legge le note dopo (/system-audit memoria,
    autoload, qualunque script con PyYAML) invece non le vede affatto. Quindi qui
    si valida davvero: PyYAML se c'e', altrimenti i due pattern noti che rompono.
    """
    m = re.match(r"^(---\s*\n)(.*?)(\n---\s*\n?)", text, re.DOTALL)
    if not m:
        return None  # nessun frontmatter: non e' il caso di questo check
    raw = m.group(2)
    try:
        import yaml  # presente sul Mac; se manca si cade sull'euristica
    except Exception:
        yaml = None
    if yaml is not None:
        try:
            loaded = yaml.safe_load(raw)
        except Exception as e:
            first = str(e).split("\n")[0].strip()
            return f"YAML non parsabile: {first}"
        if not isinstance(loaded, dict):
            return "il frontmatter non e' una mappa YAML"
        return None
    # --- fallback stdlib: i due pattern misurati in errore-comune-yaml-frontmatter-flow-sequence
    for i, line in enumerate(raw.split("\n"), 2):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        mk = re.match(r"^\s*(?:-\s+)?([a-zA-Z_]\w*):\s*(.*)$", line)
        value = mk.group(2) if mk else (stripped[2:] if stripped.startswith("- ") else None)
        if value is None:
            continue
        v = value.strip()
        if v.startswith("[") and not v.endswith("]"):
            return f"riga {i}: flow sequence aperta e non chiusa"
        if v.startswith("[") and "#" in v:
            return f"riga {i}: '#' dentro una flow sequence commenta il resto della riga"
        if v and v[0] not in "\"'[{|>" and ": " in v:
            return f"riga {i}: ': ' in uno scalare non quotato -> YAML lo legge come mappa"
    return None


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
    lv_bumped = False
    if looks_like_content_edit(payload):
        new_text, lv_bumped = update_last_verified_field(new_text)
    if changed or created_added or lv_bumped:
        try:
            path.write_text(new_text, encoding="utf-8")
            if changed:
                actions.append("updated")
            if created_added:
                actions.append("created")
            if lv_bumped:
                actions.append("last_verified")
        except Exception:
            pass

    parse_err = frontmatter_parse_error(new_text)
    if parse_err:
        log_event({
            "ts": TODAY, "tool": tool_name, "file": path.name,
            "actions": actions, "parse_error": parse_err,
            "action": "melchior-frontmatter-invalido",
        })
        print(
            f"[melchior] frontmatter NON parsabile in {path.name} — {parse_err}\n"
            f"La nota e' scritta ma resta INVISIBILE a /system-audit memoria, all'autoload e a ogni "
            f"tool che usa PyYAML. Quota lo scalare (o chiudi la flow sequence) e riscrivi.",
            file=sys.stderr,
        )
        smistata = smista_nota_radice(path, tool_name)
        if smistata:
            log_event({"ts": TODAY, "tool": tool_name, **smistata})
        return 2

    fm, _, _ = parse_frontmatter(new_text)
    missing_core = sorted(V2_CORE - set((fm or {}).keys()))
    missing_optional = sorted((V2_FULL - V2_CORE) - set((fm or {}).keys()))

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

    smistata = smista_nota_radice(path, tool_name)
    if smistata:
        log_event({"ts": TODAY, "tool": tool_name, **smistata})

    return 0


if __name__ == "__main__":
    # Claude Code scrive e legge in UTF-8. Su Windows la pipe è in cp1252 (16/10/2026).
    for _flusso in (sys.stdout, sys.stderr):
        try:
            _flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
