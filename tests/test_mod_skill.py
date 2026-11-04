#!/usr/bin/env python3
"""Q01-Q10: mod e skill portati dalla config dell'autore il 15/10/2026.

Q01 il mod apri passa claude plugin validate e claude plugin test, e apre con il programma
predefinito del sistema (open, start, xdg-open), mai con un browser scelto nel codice.
Q02 l'aiuto per gws è l'hook hooks/gws-esito.py (dal 3/11/2026, prima il mod skills/gws): il mod non c'è
più, l'hook non nomina email vere e rimanda all'onboarding di docs/onboarding/ invece di ripeterlo. Il
comportamento lo prova MP01-MP03 (tests/test_mod_passo2_2026_11_03.py).
Q03 cache-fredda porta il segnale "token gws in errore" col suo test, niente banchi (3/11/2026), e non c'è
un cruscotto parallelo.
Q04 nei file nuovi non ci sono nomi, host, percorsi o email personali.
Q05 il catalogo dei tic della scrittura generata è la skill humanizer (da blader/humanizer, MIT, con la
sua LICENSE), collegata dalla skill ITS; il vecchio catalogo di ITS non c'è più (4/11/2026).
Q07 Impeccable è un rimando all'upstream: la nota in docs/ c'è, la skill non è copiata.
Q08 prompt-master non dice più che il brief si mostra anche per una richiesta breve.
Q09 prompt-master e il promemoria di inject-now.sh caricano il corpo una volta per sessione e dopo
una compattazione, non a ogni richiesta (segnalazione n. 17, 27/10/2026).
Q10 Hallmark è un rimando all'upstream come Impeccable (30/10/2026): la nota in docs/ dice da dove
    installarla e come lavora con Impeccable, /setup fase 8c la propone con la regola per CLAUDE.md
    scritta solo dopo il sì, l'audit la conosce, la skill non è copiata.

Il banco richiede il binario `claude`. Sulla base cbd8305 ogni controllo deve fallire con un
AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, Dict, List

# I nomi della config dell'autore: solo le impronte, in tests/igiene.py (#3505). I percorsi assoluti
# di una macchina non sono nomi e restano in chiaro.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import igiene  # noqa: E402

PERCORSO_MACCHINA = re.compile(r"/Users/")


def personali(testo: str) -> List[int]:
    """Le righe con un nome della config dell'autore o un percorso assoluto della sua macchina."""
    righe = [n for n, _ in igiene.trova(testo, igiene.AUTORE)]
    return sorted(set(righe + [n for n, linea in enumerate(testo.splitlines(), 1) if PERCORSO_MACCHINA.search(linea)]))


EMAIL = re.compile(r"[\w.+-]+@([\w-]+\.)+[a-z]{2,}", re.IGNORECASE)
NUOVI = ("skills/arturo/hooks/apri", "hooks/gws-esito.py", "skills/arturo/hooks/cache-fredda", "skills/humanizer/SKILL.md",
         "docs/impeccable.md", "docs/hallmark.md")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def claude() -> str:
    exe = shutil.which("claude")
    assert exe is not None, "Q01 claude mancante: il banco prova i mod con claude plugin validate e claude plugin test"
    return exe


def prova_mod(repo: Path, nome: str, codice: str) -> str:
    # Dal 3/11/2026 (mod passo 3) la parte sta in skills/arturo/hooks/<nome>: validate e test girano sul mod intero.
    cartella = repo / "skills" / "arturo"
    assert (cartella / ".claude-plugin" / "plugin.json").is_file(), f"{codice} manca il mod skills/arturo"
    assert list((cartella / "hooks" / nome).glob("register.ts*")), f"{codice} manca la parte skills/arturo/hooks/{nome}"
    # Claude Code scrive in UTF-8: letto con la codifica di Windows lo stdout diventa None.
    v = subprocess.run([claude(), "plugin", "validate", str(cartella)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=120)
    assert v.returncode == 0, f"{codice} validate di {nome}: rc={v.returncode} {v.stdout[-300:]}{v.stderr[-200:]}"
    t = subprocess.run([claude(), "plugin", "test", str(cartella)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=180)
    esito = t.stdout + t.stderr
    assert t.returncode == 0 and re.search(r"\b0 fail\b", esito), f"{codice} plugin test di {nome}: rc={t.returncode} {esito[-300:]}"
    return esito


def sorgenti(cartella: Path) -> List[Path]:
    return [f for f in sorted(cartella.rglob("*")) if f.is_file() and ".claude-plugin/types" not in f.as_posix()
            and f.name != "tsconfig.json"]


def test_q01(repo: Path) -> None:
    esito = prova_mod(repo, "apri", "Q01")
    assert "programma predefinito" in esito and "(pass)" in esito, "Q01 mancano i test sul programma predefinito"
    codice = read(repo / "skills" / "arturo" / "hooks" / "apri" / "apri.ts")
    for parola in ("'open'", "'start'", "'xdg-open'"):
        assert parola in codice, f"Q01 apri non usa {parola} per il suo sistema"
    assert not re.search(r"-a['\"]?\s*,|Chrome|Safari|Edge", codice) and "firefox" not in codice.lower(), \
        "Q01 apri sceglie un browser invece del programma predefinito"


def test_q02(repo: Path) -> None:
    assert not (repo / "skills" / "gws").exists(), "Q02 il mod skills/gws c'è ancora: l'aiuto per gws è un hook"
    hook = repo / "hooks" / "gws-esito.py"
    assert hook.is_file(), "Q02 manca hooks/gws-esito.py"
    codice = read(hook)
    trovati = [m.group(0) for m in EMAIL.finditer(codice) if not m.group(0).lower().endswith(("@example.org", "@example.com"))]
    assert not trovati, f"Q02 email vere nell'hook gws: {trovati[:3]}"
    assert "docs/onboarding/gws.md" in codice, "Q02 la nota non rimanda all'onboarding"
    assert "client_secret" not in codice and "-s drive" not in codice, "Q02 l'hook ripete l'onboarding"


def test_q03(repo: Path) -> None:
    assert not any("cruscotto" in p.name for p in (repo / "skills").iterdir()), "Q03 cruscotto parallelo"
    parte = repo / "skills" / "arturo" / "hooks" / "cache-fredda"
    assert (parte / "register.ts").is_file(), "Q03 manca la parte skills/arturo/hooks/cache-fredda"
    register = read(parte / "register.ts")
    assert "auth', 'status'" in register, "Q03 cache-fredda non legge gws"
    # Dal 3/11/2026 i banchi rossi non stanno più sotto il prompt: li riceve chi mantiene Arturo.
    cache = read(repo / "skills" / "arturo" / "hooks" / "cache-fredda" / "cache.ts")
    assert "banchi-ultimo-esito.txt" not in register and "leggiBanchi" not in cache, \
        "Q03 cache-fredda mostra ancora i banchi rossi alla persona"
    esito = prova_mod(repo, "cache-fredda", "Q03")
    for nome in ("token gws in errore >", "solo eccezioni >"):
        assert nome in esito, f'Q03 manca il gruppo di test "{nome[:-2]}"'


def test_q04(repo: Path) -> None:
    mancanti = [n for n in NUOVI if not (repo / n).exists()]
    assert not mancanti, f"Q04 file nuovi assenti: {mancanti}"
    trovati = []
    for n in NUOVI:
        p = repo / n
        for f in (sorgenti(p) if p.is_dir() else [p]):
            linee = read(f).splitlines()
            for riga in personali(read(f)):
                if f.name == "plugin.json" and "Nejrotti" in linee[riga - 1]:
                    continue
                trovati.append(f"{f.relative_to(repo)}:{riga}")
    assert not trovati, "Q04 dati personali: " + "; ".join(trovati[:5])


def test_q05(repo: Path) -> None:
    # Dal 4/11/2026 il catalogo dei tic è la skill humanizer, adattata da github.com/blader/humanizer (MIT):
    # la licenza chiede la nota di copyright accanto al testo. Il vecchio catalogo di ITS è uscito, così i
    # cataloghi non sono due.
    skill = repo / "skills" / "humanizer" / "SKILL.md"
    assert skill.is_file(), "Q05 manca la skill humanizer"
    testo = read(skill)
    assert "github.com/blader/humanizer" in testo and "3.1.0" in testo and "MIT" in testo, \
        "Q05 la skill humanizer non dice fonte, versione e licenza"
    licenza = repo / "skills" / "humanizer" / "LICENSE"
    assert licenza.is_file() and "Siqi Chen" in read(licenza), "Q05 manca la nota MIT dell'originale"
    assert not (repo / "skills" / "italiano-semplificato" / "references" / "tic-scrittura-ia.md").exists(), \
        "Q05 il vecchio catalogo dei tic è ancora lì: i cataloghi sarebbero due"
    # Titoli tipici di tropes.fyi, che non dichiara una licenza: qui non devono comparire.
    for titolo in ("Avverbi magici", "La scappatoia", "Anafora abusata", "Tricolon"):
        assert titolo not in testo, f"Q05 titolo ripreso da una fonte senza licenza: {titolo}"
    assert "skills/humanizer/SKILL.md" in read(repo / "skills" / "italiano-semplificato" / "SKILL.md"), \
        "Q05 la skill ITS non rimanda a humanizer"


def test_q07(repo: Path) -> None:
    nota = repo / "docs" / "impeccable.md"
    assert nota.is_file(), "Q07 manca docs/impeccable.md"
    testo = read(nota)
    assert "pbakaus/impeccable" in testo and "npx impeccable install" in testo, "Q07 la nota non dice da dove installarla"
    assert not (repo / "skills" / "impeccable").exists(), "Q07 la skill impeccable è copiata in Arturo"


def test_q08(repo: Path) -> None:
    # Federico, 15/10/2026: il brief c'è su ogni richiesta di lavoro, anche breve (supera il 14/10).
    testo = read(repo / "skills" / "prompt-master" / "SKILL.md")
    importante = testo.split("## Importante", 1)[-1].split("## MODALITÀ PROMPT ESTERNO", 1)[0]
    assert "Il brief c'è sempre" in importante, "Q08 la sezione Importante non dice che il brief c'è sempre"
    assert "chiare e piccole" not in testo and "chiara e piccola non ha brief" not in testo, \
        "Q08 prompt-master esclude ancora le richieste piccole"
    promemoria = read(repo / "hooks" / "inject-now.sh")
    assert "anche piccolo" in promemoria and "chiare e piccole" not in promemoria, \
        "Q08 il promemoria di inject-now esclude ancora le richieste piccole"


def test_q09(repo: Path) -> None:
    # Segnalazione n. 17 (Gigi, 27/10/2026): ogni Skill(prompt-master) rimette il corpo intero nel contesto,
    # anche se la copia di prima c'è ancora. Il brief resta su ogni richiesta, il corpo si carica una volta.
    testo = read(repo / "skills" / "prompt-master" / "SKILL.md")
    importante = testo.split("## Importante", 1)[-1].split("## MODALITÀ PROMPT ESTERNO", 1)[0]
    promemoria = read(repo / "hooks" / "inject-now.sh")
    for nome, t in (("la skill", importante), ("il promemoria di inject-now", promemoria)):
        assert "una volta per sessione" in t and "compattazione" in t, f"Q09 {nome} non dice che il corpo si carica una volta"
    assert "a ogni richiesta di lavoro: il corpo si legge" not in importante, "Q09 la skill chiede ancora di ricaricarsi a ogni richiesta"
    assert "il primo tool è\nSkill(prompt-master)" not in promemoria, "Q09 il promemoria chiede ancora la skill a ogni messaggio"


def test_q10(repo: Path) -> None:
    # Federico, 30/10/2026: hallmark e impeccable lavorano in catena, come nella config dell'autore.
    nota = repo / "docs" / "hallmark.md"
    assert nota.is_file(), "Q10 manca docs/hallmark.md"
    testo = read(nota)
    assert "nutlope/hallmark" in testo and "npx --yes skills add nutlope/hallmark -g -a claude-code --copy -y" in testo, \
        "Q10 la nota non dice da dove installarla"
    assert "impeccable document" in testo and "lock the system" in testo, "Q10 la nota non dice chi scrive DESIGN.md"
    assert "install-hook.mjs" in testo, "Q10 la nota non avvisa dell'hook che scrive in settings.json"
    assert "docs/hallmark.md" in read(repo / "docs" / "impeccable.md"), "Q10 la nota di Impeccable non rimanda a Hallmark"
    setup = read(repo / "commands" / "setup.md")
    fase = setup.split("## FASE 8c", 1)[-1].split("## FASE 8d", 1)[0]
    assert "## La regola per il tuo CLAUDE.md" in testo and "impeccable guida, hallmark costruisce" in testo, \
        "Q10 la nota non porta la regola della catena per CLAUDE.md"
    assert "nutlope/hallmark" in fase and "La regola per il tuo CLAUDE.md" in fase, \
        "Q10 /setup fase 8c non propone Hallmark con la regola della catena"
    regola = fase.split("- Con tutte", 1)[-1].split("\n- ", 1)[0].split("\n## ", 1)[0]
    assert "solo dopo il sì" in regola, "Q10 /setup scrive la regola nel CLAUDE.md senza chiedere"
    assert re.search(r'UPSTREAM = \{[^}]*"hallmark"', read(repo / "skills" / "system-audit" / "audit.sh")), \
        "Q10 l'audit non conosce hallmark come skill dell'upstream"
    assert not (repo / "skills" / "hallmark").exists(), "Q10 la skill hallmark è copiata in Arturo"


TESTS: Dict[str, Callable[[Path], None]] = {
    "Q01": test_q01, "Q02": test_q02, "Q03": test_q03, "Q04": test_q04,
    "Q05": test_q05, "Q07": test_q07, "Q08": test_q08, "Q09": test_q09,
    "Q10": test_q10,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    parser.add_argument("--solo", nargs="+", choices=list(TESTS), help="solo questi controlli (per i veleni)")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.solo:
        for nome in args.solo:
            TESTS[nome](repo)
        print(f"PASS {','.join(args.solo)} controlli={len(args.solo)} (solo)")
        return 0
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
