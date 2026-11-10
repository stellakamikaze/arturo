#!/usr/bin/env python3
"""RI01: reinstallare Arturo sopra un Arturo riporta quello che è della persona (#3825, 23/10/2026).

Il 22/10 (f4ae0aa), allineando /setup al README, è sparito il ciclo che riportava la memoria dalla
~/.claude messa da parte. Ma una ~/.claude di Arturo ha fuori da git molto altro della persona:
CLAUDE.md, personale/, i todo, le scelte. Fra le scelte c'è la telemetria spenta, che una
reinstallazione riaccendeva senza dirlo.

RI01 il blocco d'installazione del README, eseguito in una HOME usa e getta con un Arturo già usato,
     riporta CLAUDE.md, personale/, memoria, todo, segnalazioni, il segno di /setup, la scelta sugli
     aggiornamenti, lo stato della telemetria e degli inviti, e git non li vede. Dal 4/11 (#3842) riporta
     anche gli handoff, ogni file .local e le skill, i comandi e gli agenti che Arturo non ha mai avuto;
     un comando e una skill che Arturo ha tolto restano nella copia. Il settings.json
     vecchio resta nel backup: quello è di Arturo.

Sulla base f4ae0aa il controllo deve fallire con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

BASH = shutil.which("bash") or "bash"

# percorso dentro ~/.claude -> contenuto, nella ~/.claude di un Arturo già usato
DELLA_PERSONA = {
    "CLAUDE.md": "# Gunnar\nSono Carla.\n",
    "settings.local.json": "{\"x\": 1}\n",
    "personale/session-start.sh": "echo mio\n",
    "hooks/hosts-interni.local": "nas.casa\n",
    "data/memory/nota.md": "---\nname: nota\n---\nmia\n",
    "data/memoria/stato.json": "{\"accesa\": true}\n",
    "data/todo/todo.json": "{}\n",
    "data/segnalazioni/1.json": "{}\n",
    "data/setup-fatto": "2026-10-19\n",
    "data/aggiornamenti.json": "{\"modo\": \"manuali\"}\n",
    "session-env/telemetria.json": "{\"id\": \"aaaabbbb-cccc\", \"spenta\": true}\n",
    "session-env/segnala.json": "{\"pausa\": \"sempre\"}\n",
    # Lo sportello (4/11/2026): senza le ricevute la persona non legge più le risposte né ritira.
    "data/segnalazioni/ricevute.json": "{\"7\": \"0123456789abcdef0123456789abcdef\"}\n",
    "session-env/novita-viste": "2026-10-22\n",
    # #3842 (2/11/2026): tutti i file personali, anche quelli che la lista fissa non nomina
    "hooks/gws-account.local": "uf\n",
    "hooks/emoji-ovunque.local": "1\n",
    "hooks/melchior-stopword.local": "anche\n",
    "hooks/futuro-mio.local": "un .local che nessuna lista conosce\n",
    "skills/system-audit/review-termini.local": "termine\n",
    "data/handoffs/libro/HANDOFF_2026-11-01_10-00.md": "# Session Handoff\n",
    "skills/mia-ricetta/SKILL.md": "---\nname: mia-ricetta\n---\nfatta con /creaskill\n",
    "commands/mio-comando.md": "il mio comando\n",
    "agents/mio-agente.md": "il mio agente\n",
}

# Un comando e una skill che Arturo ha avuto e poi tolto: la reinstallazione non li riporta.
TOLTI = {"commands/discovery.md": "vecchio comando di Arturo\n", "skills/apri/SKILL.md": "vecchia skill di Arturo\n"}
# I file della persona che git può vedere come nuovi: /fine li salva nel clone.
NUOVI_PER_GIT = ("data/handoffs/", "skills/mia-ricetta/", "commands/mio-comando.md", "agents/mio-agente.md",
                 "hooks/futuro-mio.local")


def env_di(home: Path) -> dict:
    return {"HOME": str(home), "USERPROFILE": str(home), "PATH": os.environ.get("PATH", ""),
            "PYTHONDONTWRITEBYTECODE": "1", "GIT_CONFIG_GLOBAL": "/dev/null", "ARTURO_TELEMETRIA": "0",
            "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def sorgente(repo: Path, radice: Path) -> Path:
    """Un repository da clonare: il repo stesso, o per una copia senza storia (controprova) un repo nuovo."""
    if (repo / ".git").exists():
        return repo
    copia = radice / "sorgente"
    shutil.copytree(repo, copia)
    env = env_di(radice)
    for comando in (["init", "-q"], ["add", "-A"], ["commit", "-q", "-m", "base"]):
        subprocess.run(["git", "-C", str(copia), *comando], check=True, capture_output=True, env=env)
    return copia


def test_ri01(repo: Path) -> None:
    readme = (repo / "README.md").read_text(encoding="utf-8")
    blocco = re.search(r"```bash\n(B=\"\$HOME/\.claude-backup.*?)```", readme, re.S)
    assert blocco, "RI01 il README non ha il blocco d'installazione"
    with tempfile.TemporaryDirectory() as d:
        radice = Path(d)
        home = radice / "home"
        vecchia = home / ".claude"
        for nome, testo in {**DELLA_PERSONA, **TOLTI}.items():
            (vecchia / nome).parent.mkdir(parents=True, exist_ok=True)
            (vecchia / nome).write_text(testo, encoding="utf-8")
        (vecchia / "settings.json").write_text("{\"vecchio\": true}\n", encoding="utf-8")
        script = blocco.group(1).replace("https://github.com/stellakamikaze/arturo.git", sorgente(repo, radice).as_posix())
        r = subprocess.run([BASH, "-c", script], capture_output=True, text=True, timeout=180, env=env_di(home),
                           check=False)
        nuova = home / ".claude"
        assert (nuova / "bin").is_dir(), f"RI01 il clone non è avvenuto: {r.stderr[-300:]}"
        mancano = [n for n, t in DELLA_PERSONA.items()
                   if not (nuova / n).is_file() or (nuova / n).read_text(encoding="utf-8") != t]
        assert not mancano, f"RI01 la reinstallazione non riporta: {', '.join(mancano)}"
        # In una copia senza storia (controprova) Arturo non ha mai avuto niente: il controllo vale sul repo.
        tornati = [n for n in TOLTI if (nuova / n).exists()] if (repo / ".git").exists() else []
        assert not tornati, f"RI01 la reinstallazione riporta file che Arturo ha tolto: {', '.join(tornati)}"
        assert "vecchio" not in (nuova / "settings.json").read_text(encoding="utf-8"), \
            "RI01 il settings.json vecchio ha preso il posto di quello di Arturo"
        sporchi = subprocess.run(["git", "-C", str(nuova), "status", "--porcelain", "--untracked-files=all"], capture_output=True, text=True,
                                 env=env_di(home), check=False).stdout.strip()
        visti = [r for r in sporchi.splitlines()
                 if not (r.startswith("?? ") and r[3:].strip('"').startswith(NUOVI_PER_GIT + tuple(TOLTI)))]
        assert not visti, f"RI01 git vede i file della persona: {visti[:5]}"


TESTS = {"RI01": test_ri01}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.baseline_ref:
        rossi, altro = [], []
        for nome, test in TESTS.items():
            try:
                test(repo)
            except AssertionError as e:
                (rossi if str(e).startswith(nome) else altro).append(f"{nome}: {e}")
        assert not altro and len(rossi) == len(TESTS), \
            "baseline non discriminante: ogni controllo deve fallire col suo codice.\n" + "\n".join(altro + rossi)
        print(f"BASELINE_DISCRIMINANTE={','.join(r.split(':')[0] for r in rossi)}")
        return 0
    for test in TESTS.values():
        test(repo)
    print(f"PASS {','.join(TESTS)} controlli={len(TESTS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
