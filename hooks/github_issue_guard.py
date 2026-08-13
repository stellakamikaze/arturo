#!/usr/bin/env python3
"""
GitHub Issue Content Guard Hook

Impedisce che issue GitHub create tramite Claude Code contengano
riferimenti a "Claude" o "Anthropic".

Blocca:
- MCP tools: mcp__github__create_issue, mcp__github__add_issue_comment, mcp__github__update_issue
- CLI: gh issue create, gh issue edit, gh issue comment
"""
import json
import sys
import re

def check_github_issue_content(text):
    """Verifica se il testo contiene termini proibiti."""
    if not text:
        return False, None

    prohibited_terms = ['claude', 'anthropic']
    text_lower = text.lower()

    for term in prohibited_terms:
        if term in text_lower:
            return True, f"Contenuto contiene '{term}'"

    return False, None

def check_mcp_github_tool(tool_name, tool_input):
    """Controlla MCP GitHub tools."""
    github_tools = [
        'mcp__github__create_issue',
        'mcp__github__add_issue_comment',
        'mcp__github__update_issue'
    ]

    if tool_name not in github_tools:
        return False, None

    fields_to_check = ['title', 'body', 'comment', 'content']

    for field in fields_to_check:
        if field in tool_input:
            has_issue, message = check_github_issue_content(tool_input[field])
            if has_issue:
                return True, f"Issue {field}: {message}"

    return False, None

def check_gh_command(command):
    """Controlla comandi gh CLI (issue e PR)."""
    # Match only when gh is an actual command (start of line or after pipe/chain operators)
    # Avoids false positives on arguments containing "gh issue create" as a string
    gh_pattern = re.compile(
        r'(?:^|&&|\|\|?|;)\s*gh\s+(?:issue|pr)\s+(?:create|edit|comment)\b',
        re.IGNORECASE
    )
    matches = list(gh_pattern.finditer(command))
    if not matches:
        return False, None

    # Cerca termini proibiti solo nel segmento matchato + argomenti successivi
    prohibited_terms = ['claude', 'anthropic']
    for match in matches:
        segment = command[match.start():].lower()
        for term in prohibited_terms:
            if term in segment:
                return True, f"Comando contiene '{term}'"

    return False, None

def suggest_cleaned_command(command):
    """Suggerisce versione pulita del comando."""
    cleaned = re.sub(r'(?i)\b(?:claude|anthropic)\b[^\s]*\s*', '', command)
    cleaned = re.sub(r'(?i).*generated with.*claude.*', '', cleaned)
    cleaned = re.sub(r'(?i)co-authored-by:.*(?:claude|anthropic).*', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def main():
    try:
        input_data = json.load(sys.stdin)
        tool_name = input_data.get('tool_name', '')
        tool_input = input_data.get('tool_input', {})

        # Check MCP GitHub tools
        if tool_name.startswith('mcp__github__'):
            has_issue, message = check_mcp_github_tool(tool_name, tool_input)
            if has_issue:
                print(f"BLOCCATO: {message}")
                print("Le issue GitHub non possono contenere riferimenti a Claude/Anthropic")
                sys.exit(2)

        # Check Bash commands (gh CLI)
        elif tool_name == 'Bash':
            command = tool_input.get('command', '')
            has_issue, message = check_gh_command(command)
            if has_issue:
                print(f"BLOCCATO: {message}")
                print("Le issue GitHub non possono contenere riferimenti a Claude/Anthropic")

                cleaned = suggest_cleaned_command(command)
                if cleaned and cleaned != command:
                    print(f"\nComando suggerito:\n{cleaned}")

                sys.exit(2)

    except Exception:
        sys.exit(0)

if __name__ == '__main__':
    main()
