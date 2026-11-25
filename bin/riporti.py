"""arturo riporto: il segno dei rami che /fine ha chiuso e che aspettano solo il merge.

Una sessione fissata al worktree non può lanciare git sul tree principale: la guardia di Claude Code
rifiuta il comando. Il passo 3 di shared/fine-worktree.md segna allora il ramo, e il prossimo /inizio
nel tree principale lo vede "chiuso da /fine, da riportare" (bin/contesto.py) e lo riporta.

Fino al 25/11/2026 il segno era `git config branch.<ramo>.arturo-riporta`: la config del repository è
comune a tutti i worktree, e la guardia del worktree rifiuta ogni scrittura lì (segnalazione n. 97,
#6399). Ora il segno sta in ~/.claude/data/riporti.json, fuori da ogni repository: il sandbox dei
comandi lascia scrivere in data/, e la guardia non ha un git da fermare. Lo script legge git, non lo
scrive mai.

  segna RAMO     segna RAMO come chiuso oggi, col commit in cima al ramo. Gira da dentro il worktree
                 o dal tree principale: il repository è lo stesso (git rev-parse --git-common-dir)
  elenco         i rami segnati del repository della cartella in cui sei, ancora validi

Un segno vale finché il ramo esiste e il suo commit in cima è quello segnato. Dopo il merge e
`git branch -d` il ramo sparisce, e il segno con lui; un commit nuovo sul ramo lo rende vecchio
(rilancia segna). I segni vecchi escono dal file al segna successivo, di qualunque repository.

Il file: {"<cartella .git comune>": {"<ramo>": {"data": "aaaa-mm-gg", "commit": "<sha>"}}}.
Solo libreria standard, Python 3.8 o successivo.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
sys.path.append(str(Path(os.path.realpath(__file__)).parent.parent / "hooks"))
from radici import radice_orsa, scrivi_atomico  # noqa: E402
sys.path.insert(0, str(Path(os.path.realpath(__file__)).parent))
import todo_store as ts  # noqa: E402  (oggi(): la data di ARTURO_OGGI nei test)

AIUTO = """arturo riporto: i rami che /fine ha chiuso e che aspettano solo il merge.

  arturo riporto segna RAMO   segna RAMO chiuso oggi (dal worktree o dal tree principale)
  arturo riporto elenco       i rami segnati del repository in cui sei"""


def file_segni() -> Path:
    return Path(os.environ.get("ARTURO_RADICE") or radice_orsa()) / "data" / "riporti.json"


def _git(cartella: Path, *argomenti: str) -> str:
    try:
        r = subprocess.run(["git", "-c", "core.fsmonitor=false", "-C", str(cartella), *argomenti],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15,
                           env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"})
    except (OSError, subprocess.SubprocessError):
        return ""
    return r.stdout.strip() if r.returncode == 0 else ""


def repository(cartella: Path) -> str:
    """La cartella .git comune, assoluta e risolta: la stessa dal worktree e dal tree principale."""
    comune = _git(cartella, "rev-parse", "--git-common-dir")
    if not comune:
        return ""
    percorso = Path(comune)
    if not percorso.is_absolute():
        percorso = Path(cartella) / percorso
    return os.path.normcase(os.path.realpath(percorso))


def _cima(cartella: Path, ramo: str) -> str:
    return _git(cartella, "rev-parse", "--verify", "--quiet", f"refs/heads/{ramo}^{{commit}}")


def _leggi() -> dict:
    try:
        dati = json.loads(file_segni().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return dati if isinstance(dati, dict) else {}


def segnati(cartella: Path) -> dict:
    """{ramo: data} dei segni validi del repository di `cartella`. Non scrive niente."""
    voci = _leggi().get(repository(cartella)) if repository(cartella) else None
    if not isinstance(voci, dict):
        return {}
    validi = {}
    for ramo, segno in voci.items():
        if isinstance(segno, dict) and segno.get("commit") and _cima(cartella, ramo) == segno["commit"]:
            validi[ramo] = str(segno.get("data", ""))
    return validi


def _pulisci(dati: dict) -> dict:
    """Toglie i segni dei rami spariti o con un commit nuovo, e i repository che non esistono più."""
    puliti = {}
    for repo, voci in dati.items():
        if not isinstance(voci, dict) or not Path(repo).is_dir():
            continue
        restano = {r: s for r, s in voci.items()
                   if isinstance(s, dict) and s.get("commit") and _cima(Path(repo), r) == s["commit"]}
        if restano:
            puliti[repo] = restano
    return puliti


def segna(cartella: Path, ramo: str) -> int:
    repo = repository(cartella)
    if not repo:
        print(f"riporto: {cartella} non è dentro un repository git.", file=sys.stderr)
        return 2
    commit = _cima(cartella, ramo)
    if not commit:
        print(f"riporto: il ramo {ramo} non esiste in questo repository.", file=sys.stderr)
        return 2
    dati = _pulisci(_leggi())
    dati.setdefault(repo, {})[ramo] = {"data": ts.oggi().isoformat(), "commit": commit}
    scrivi_atomico(file_segni(), json.dumps(dati, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print(f"Segnato: {ramo} chiuso da /fine il {dati[repo][ramo]['data']} (commit {commit[:7]}). "
          "Lo riporta il prossimo /inizio nel tree principale.")
    return 0


def main(argv: list) -> int:
    if not argv or argv[0] in ("-h", "--help", "aiuto", "help"):
        print(AIUTO)
        return 0
    if argv[0] == "segna" and len(argv) == 2:
        return segna(Path.cwd(), argv[1])
    if argv[0] == "elenco" and len(argv) == 1:
        voci = segnati(Path.cwd())
        for ramo, data in sorted(voci.items()):
            print(f"{ramo} · chiuso da /fine il {data}")
        if not voci:
            print("Nessun ramo segnato in questo repository.")
        return 0
    print(AIUTO, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
