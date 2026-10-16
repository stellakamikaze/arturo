#!/usr/bin/env python3
"""Q01-Q08: mod e skill portati dalla config dell'autore il 15/10/2026.

Q01 il mod apri passa claude plugin validate e claude plugin test, e apre con il programma
predefinito del sistema (open, start, xdg-open), mai con un browser scelto nel codice.
Q02 il mod gws passa validate e test, non nomina account personali né email vere, e rimanda
all'onboarding di docs/onboarding/ invece di ripeterlo.
Q03 cache-fredda porta i segnali «banchi rossi» e «token gws in errore» con i loro test, e non c'è
un cruscotto parallelo.
Q04 nei file nuovi non ci sono nomi, host, percorsi o email personali.
Q05 il catalogo dei tic della scrittura generata è scritto da zero, collegato dalla skill ITS, e
dice perché non copia tropes.fyi.
Q06 gli esempi dello strato (posta, recap, anteprima prima dell'invio) sono marcati da adattare,
restano fuori dal plugin, e l'anteprima legge le regole da un file: senza file restano i controlli
generali, uno strumento che non manda email passa in silenzio, un input rotto non blocca.
Q07 Impeccable è un rimando all'upstream: la nota in docs/ c'è, la skill non è copiata.
Q08 prompt-master non dice più che il brief si mostra anche per una richiesta breve.

Il banco richiede il binario `claude`. Sulla base cbd8305 ogni controllo deve fallire con un
AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable, Dict, List

# Le parole sono spezzate: il controllo di igiene I03 legge anche i test.
PERSONALI = re.compile("|".join(re.escape(a + b) for a, b in (
    ("fede", "rico"), ("nej", "rotti"), ("gani", "mede"), ("bal", "thasar"), ("fur", "ore"), ("/Us", "ers/"),
    ("noco", "db"), ("vault", "warden"), ("ts", ".net"), ("gws-", "uf"), ("gws-", "gmail"), ("gws-", "ss"),
    ("gws-", "ciao"), ("tom", "maso"), ("ele", "na@"), ("fire", "fox"),
)) + r"|\buf-[a-z]|\bUF\b", re.IGNORECASE)
EMAIL = re.compile(r"[\w.+-]+@([\w-]+\.)+[a-z]{2,}", re.IGNORECASE)
NUOVI = ("skills/apri", "skills/gws", "skills/cache-fredda", "skills/italiano-semplificato/references/tic-scrittura-ia.md",
         "templates/strato/esempi", "docs/impeccable.md")
ESEMPI = ("posta", "recap")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def claude() -> str:
    exe = shutil.which("claude")
    assert exe is not None, "Q01 claude mancante: il banco prova i mod con claude plugin validate e claude plugin test"
    return exe


def prova_mod(repo: Path, nome: str, codice: str) -> str:
    cartella = repo / "skills" / nome
    assert (cartella / ".claude-plugin" / "plugin.json").is_file(), f"{codice} manca skills/{nome}"
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
    codice = read(repo / "skills" / "apri" / "hooks" / "apri.ts")
    for parola in ("'open'", "'start'", "'xdg-open'"):
        assert parola in codice, f"Q01 apri non usa {parola} per il suo sistema"
    assert not re.search(r"-a['\"]?\s*,|Chrome|Safari|Edge", codice) and "fire" + "fox" not in codice.lower(), \
        "Q01 apri sceglie un browser invece del programma predefinito"


def test_q02(repo: Path) -> None:
    esito = prova_mod(repo, "gws", "Q02")
    assert "account" in esito and "sintassi" in esito, "Q02 mancano i test di account e sintassi"
    trovati = []
    for f in sorgenti(repo / "skills" / "gws"):
        for m in EMAIL.finditer(read(f)):
            if not m.group(0).lower().endswith(("@example.org", "@example.com")):
                trovati.append(f"{f.name}: {m.group(0)}")
    assert not trovati, f"Q02 email vere nel mod gws: {trovati[:3]}"
    codice = read(repo / "skills" / "gws" / "hooks" / "gws.ts")
    assert "docs/onboarding/gws.md" in codice, "Q02 la nota non rimanda all'onboarding"
    assert "client_secret" not in codice and "-s drive" not in codice, "Q02 il mod ripete l'onboarding"


def test_q03(repo: Path) -> None:
    assert not any((repo / "skills" / n).exists() for n in ("cruscotto", "uf-" + "cruscotto")), "Q03 cruscotto parallelo"
    register = read(repo / "skills" / "cache-fredda" / "hooks" / "register.ts")
    assert "banchi-ultimo-esito.txt" in register and "auth', 'status'" in register, "Q03 cache-fredda non legge banchi e gws"
    esito = prova_mod(repo, "cache-fredda", "Q03")
    for nome in ("banchi rossi >", "token gws in errore >", "solo eccezioni >"):
        assert nome in esito, f"Q03 manca il gruppo di test «{nome[:-2]}»"


def test_q04(repo: Path) -> None:
    mancanti = [n for n in NUOVI if not (repo / n).exists()]
    assert not mancanti, f"Q04 file nuovi assenti: {mancanti}"
    trovati = []
    for n in NUOVI:
        p = repo / n
        for f in (sorgenti(p) if p.is_dir() else [p]):
            for riga, linea in enumerate(read(f).splitlines(), 1):
                if f.name == "plugin.json" and "Nejrotti" in linea:
                    continue
                if PERSONALI.search(linea):
                    trovati.append(f"{f.relative_to(repo)}:{riga}: {linea.strip()[:80]}")
    assert not trovati, "Q04 dati personali: " + "; ".join(trovati[:5])


def test_q05(repo: Path) -> None:
    cat = repo / "skills" / "italiano-semplificato" / "references" / "tic-scrittura-ia.md"
    assert cat.is_file(), "Q05 manca il catalogo dei tic"
    testo = read(cat)
    assert "tropes.fyi" in testo and "licenza" in testo and "scritto da zero" in testo, "Q05 manca la nota su fonte e licenza"
    # Titoli tipici del catalogo d'origine: qui non devono comparire.
    for titolo in ("Avverbi magici", "La scappatoia", "Anafora abusata", "Tricolon"):
        assert titolo not in testo, f"Q05 titolo ripreso dalla fonte: {titolo}"
    assert "references/tic-scrittura-ia.md" in read(repo / "skills" / "italiano-semplificato" / "SKILL.md"), \
        "Q05 la skill ITS non collega il catalogo"


def anteprima(script: Path, radice: Path, dati: object) -> subprocess.CompletedProcess:
    entrata = dati if isinstance(dati, str) else json.dumps(dati)
    return subprocess.run([sys.executable, "-B", str(script)], input=entrata, capture_output=True, text=True,
                          env=dict(os.environ, CLAUDE_PLUGIN_ROOT=str(radice)), timeout=30)


def test_q06(repo: Path) -> None:
    base = repo / "templates" / "strato" / "esempi"
    assert (base / "README.md").is_file(), "Q06 manca templates/strato/esempi"
    assert not (repo / "templates" / "strato" / "plugins" / "strato" / "skills" / "posta").exists(), \
        "Q06 un esempio sta dentro il plugin e si carica da solo"
    for nome in ESEMPI:
        skill = read(base / nome / "SKILL.md")
        assert "ESEMPIO DA ADATTARE" in skill and "disable-model-invocation: true" in skill, f"Q06 {nome} non è marcato come esempio"
    assert "trascrizione intera" in read(base / "recap" / "SKILL.md"), "Q06 recap senza il metodo della trascrizione intera"
    posta = read(base / "posta" / "SKILL.md")
    assert "Bozza" in posta and "Inviata" in posta and "Regola di voce" in posta, "Q06 posta senza il ciclo bozza, inviata, regola"
    script = base / "anteprima-invio" / "anteprima-invio.py"
    codice = read(script)
    assert not EMAIL.search(codice), "Q06 l'anteprima ha indirizzi scritti nel codice"
    with tempfile.TemporaryDirectory() as d:
        radice = Path(d)
        invio = {"tool_name": "mcp__posta__send_message",
                 "tool_input": {"to": ["a@example.org"], "subject": "Ciao", "body": "Costa 1.200 euro, perche' ABC."}}
        (radice / "regole-invio.txt").write_text(
            "copia: capo@example.org\noggetto-nuovo: Studio:\nparola: ABC => per esteso\ncifre-nel-corpo: no\n", encoding="utf-8")
        r = anteprima(script, radice, invio)
        uscita = json.loads(r.stdout)["hookSpecificOutput"]
        motivo = uscita["permissionDecisionReason"]
        assert uscita["permissionDecision"] == "ask", "Q06 l'anteprima non chiede conferma"
        for atteso in ("capo@example.org", "Studio:", "ABC", "cifra", "apostrofo"):
            assert atteso in motivo, f"Q06 l'anteprima non applica la regola «{atteso}»: {motivo}"
        (radice / "regole-invio.txt").unlink()
        r = anteprima(script, radice, invio)
        motivo = json.loads(r.stdout)["hookSpecificOutput"]["permissionDecisionReason"]
        assert "apostrofo" in motivo and "capo@" not in motivo, "Q06 senza file delle regole l'anteprima sbaglia"
        for dati in ({"tool_name": "Bash", "tool_input": {"command": "ls"}},
                     {"tool_name": "mcp__chat__send_message", "tool_input": {"channel_id": "x", "message": "ciao"}}, "rotto"):
            r = anteprima(script, radice, dati)
            assert r.returncode == 0 and r.stdout.strip() == "", f"Q06 l'anteprima interviene dove non deve: {dati}"


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


TESTS: Dict[str, Callable[[Path], None]] = {
    "Q01": test_q01, "Q02": test_q02, "Q03": test_q03, "Q04": test_q04,
    "Q05": test_q05, "Q06": test_q06, "Q07": test_q07, "Q08": test_q08,
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
