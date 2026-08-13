#!/usr/bin/env python3
"""
Emoji checker hook for Claude Code.
Detects emojis in edited files and asks Claude to remove them.
"""
import json
import sys
import os
import re

# Emoji pattern to detect any emoji
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002700-\U000027BF"  # dingbats
    "\U0001F900-\U0001F9FF"  # supplemental symbols
    "\U00002600-\U000026FF"  # misc symbols
    "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-A
    "\U00002300-\U000023FF"  # misc technical
    "]+",
    flags=re.UNICODE
)

# Simboli tecnici legittimi in doc/config (tasti macOS, check, warning testuali):
# non sono "emoji decorative" e bloccavano edit validi (falsi positivi).
ALLOWED_SYMBOLS = {
    "⌘",  # cmd
    "⌥",  # option
    "⇧",  # shift
    "⌃",  # ctrl
    "⎋",  # esc
    "⏎",  # return
    "⏵",  # play
    "✓", "✔",  # check
    "✗", "✘",  # cross
    "⚠",  # warning
}

# File di CONTENUTO social dove le emoji SONO contenuto legittimo (bozze caption
# IG/TikTok/LinkedIn/Bluesky): non vanno spogliate.
# L'igiene-emoji resta attiva su tutto il resto (codice sorgente, memory, config, doc).
# Marker: segmenti di path oppure token nel nome file (case-insensitive).
CONTENT_DIR_MARKERS = ("/bozze/", "/captions/", "/caption/", "/social/",
                       "/drafts/", "/didascalie/", "/post/")
CONTENT_NAME_MARKERS = ("caption", "bozza", "didascalia", "-social", "_social",
                        ".social.")


def is_social_content_file(fp: str) -> bool:
    low = fp.replace("\\", "/").lower()
    if any(seg in low for seg in CONTENT_DIR_MARKERS):
        return True
    base = os.path.basename(low)
    return any(tok in base for tok in CONTENT_NAME_MARKERS)


try:
    input_data = json.load(sys.stdin)
    tool_name = input_data.get('tool_name', '')
    tool_input = input_data.get('tool_input', {})

    # MultiEdit has edits[] array, not a single file_path
    file_paths = []
    if tool_name == 'MultiEdit':
        for edit in tool_input.get('edits', []):
            fp = edit.get('file_path', '')
            if fp and os.path.exists(fp):
                file_paths.append(fp)
    else:
        fp = tool_input.get('file_path', '')
        if fp and os.path.exists(fp):
            file_paths.append(fp)

    if not file_paths:
        sys.exit(0)

    file_path = file_paths[0]  # backward compat for skip/read logic below

    # Skip binary and non-text files
    SKIP_EXT = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.ico', '.svg',
                '.pdf', '.woff', '.woff2', '.ttf', '.eot', '.mp3', '.mp4',
                '.zip', '.gz', '.tar', '.lock', '.map'}
    if os.path.splitext(file_path)[1].lower() in SKIP_EXT:
        sys.exit(0)

    for fp in file_paths:
        # Skip binary and non-text files (per-file check for MultiEdit)
        if os.path.splitext(fp)[1].lower() in SKIP_EXT:
            continue

        # Skip file di contenuto social: le emoji sono contenuto, non rumore.
        if is_social_content_file(fp):
            continue

        with open(fp, 'r', encoding='utf-8') as f:
            content = f.read()

        emojis_found = [
            ch for seq in EMOJI_PATTERN.findall(content)
            for ch in seq if ch not in ALLOWED_SYMBOLS
        ]
        if emojis_found:
            sample = ', '.join(emojis_found[:3])
            # PostToolUse hook: feedback a Claude via stderr + exit code 2.
            # (permissionDecision/deny e' sintassi PreToolUse e non si applica
            # a un'azione gia' avvenuta.)
            print(
                f"Emojis found in {fp}: {sample}. "
                "Replace with text equivalents like [X], [OK], [WARNING].",
                file=sys.stderr
            )
            sys.exit(2)

    sys.exit(0)

except Exception:
    sys.exit(0)
