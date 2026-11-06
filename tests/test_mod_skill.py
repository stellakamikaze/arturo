#!/usr/bin/env python3
"""Q01-Q11: mod e skill portati dalla config dell'autore il 15/10/2026.

Q01 il mod apri passa claude plugin validate e claude plugin test, e apre con il programma
predefinito del sistema (open, start, xdg-open), mai con un browser scelto nel codice.
Q02 l'aiuto per gws è l'hook hooks/gws-esito.py (dal 3/11/2026, prima il mod skills/gws): il mod non c'è
più, l'hook non nomina email vere e rimanda all'onboarding di docs/onboarding/ invece di ripeterlo. Il
comportamento lo prova MP01-MP03 (tests/test_mod_passo2_2026_11_03.py).
Q03 cache-fredda porta il segnale "token gws in errore" col suo test, niente banchi (3/11/2026), e non c'è
un cruscotto parallelo.
Q04 nei file nuovi non ci sono nomi, host, percorsi o email personali: dal 4/11/2026 anche nella skill humanizer
intera, nel disegno di come è fatto Arturo e negli altri file arrivati con humanizer e con la procedura guidata.
Q05 il catalogo dei tic della scrittura generata è la skill humanizer (da blader/humanizer, MIT, con la
sua LICENSE), collegata dalla skill ITS; il vecchio catalogo di ITS non c'è più (4/11/2026).
Q06 nomi e licenze allineati dopo humanizer (#4721, 4/11/2026): la sezione della voce nel CLAUDE.md ha il
nome che scrive /setup ("Come scrivo"), italiano-semplificato ha la LICENSE di AminBlg/SimpleEnglish, il
README cita le licenze delle tre skill adattate e la copia del disegno in NOVITA.md è uguale all'originale.
Q07 Impeccable è un rimando all'upstream: la nota in docs/ c'è, la skill non è copiata.
Q08 prompt-master non dice più che il brief si mostra anche per una richiesta breve.
Q09 prompt-master e il promemoria di inject-now.sh caricano il corpo una volta per sessione e dopo
una compattazione, non a ogni richiesta (segnalazione n. 17, 27/10/2026).
Q10 Hallmark è un rimando all'upstream come Impeccable (30/10/2026): la nota in docs/ dice da dove
    installarla e come lavora con Impeccable, /setup fase 8c la propone con la regola per CLAUDE.md
    scritta solo dopo il sì, l'audit la conosce, la skill non è copiata.
Q11 shared/regole-interfaccia.md (6/11/2026): tre parti, chi vince, ogni regola col tipo e con una fonte
    che ha un URL, virgolette dritte, e chi fa design ci arriva da agente, metodo e docs (/setup porta a docs/hallmark.md: è al tetto di SR08).

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
NUOVI = ("skills/arturo/hooks/apri", "hooks/gws-esito.py", "skills/arturo/hooks/cache-fredda", "skills/humanizer",
         "docs/impeccable.md", "docs/hallmark.md", "docs/come-e-fatto.md", "docs/diagram-design.md",
         "bin/humanizer-origine.py", "skills/italiano-semplificato/LICENSE", "shared/procedura-guidata.sh")


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
    assert t.returncode == 0 and re.search(r"\b0 fail\b", esito), \
        f"{codice} plugin test di {nome}: rc={t.returncode}\n{rossi_del_test(esito)}"
    return esito


def rossi_del_test(esito: str) -> str:
    """Le righe "(fail)" del plugin test, ognuna col suo errore: la coda dell'uscita taglia il nome del test.

    4/11/2026 (#4748): un TB04 rosso nel gate sotto carico diceva solo "1 fail", e il test non si è più
    ripresentato in 11 giri, anche con il carico a 195. Senza il nome il rosso non si può indagare.
    """
    righe, blocchi, i = esito.splitlines(), [], 0
    while i < len(righe):
        if righe[i].startswith("(fail)"):
            fine = i + 1
            while fine < len(righe) and fine - i <= 12 and not righe[fine].startswith(("(pass)", "(fail)", "(skip)")):
                fine += 1
            blocchi.append("\n".join(r.rstrip() for r in righe[i:fine]).rstrip())
            i = fine
        else:
            i += 1
    if not blocchi:
        return esito[-600:]
    # Il gate mostra le ultime 40 righe del log: i primi due rossi stanno dentro anche col traceback sopra.
    return "\n".join("\n".join(blocchi[:2]).splitlines()[:24])


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
            trovati += [f"{f.relative_to(repo)}: {m.group(0)}" for m in EMAIL.finditer(read(f))
                        if not m.group(0).lower().endswith(("@example.org", "@example.com"))]
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
    # L'origine e la versione inglese (4/11/2026): ORIGINE fissa il commit, originale-en.md è l'originale a quel
    # commit, e SKILL.md nomina lo stesso commit. Dopo `bin/humanizer-origine.py porta` Q05 resta rosso finché
    # l'adattamento italiano non segue.
    voci = dict(r.split(" ", 1) for r in read(repo / "skills" / "humanizer" / "ORIGINE").splitlines() if " " in r)
    assert voci.get("repository", "").endswith("blader/humanizer") and voci.get("commit") and voci.get("versione"), \
        f"Q05 ORIGINE incompleta: {voci}"
    inglese = repo / "skills" / "humanizer" / "references" / "originale-en.md"
    assert inglese.is_file() and f'version: "{voci["versione"]}"' in read(inglese), \
        "Q05 l'originale inglese manca o non è alla versione di ORIGINE"
    assert f"{voci['versione']} ({voci['commit']}" in testo, \
        f"Q05 l'adattamento italiano non nomina versione e commit di ORIGINE ({voci['versione']}, {voci['commit']})"
    assert "personale/humanizer.md" in testo and "Tre modi di scrivere" in testo, \
        "Q05 la skill non legge la voce dall'Orsa o non dice i tre modi di scrivere"


def _disegno(testo: str) -> str:
    return testo.split("```diagramma\n", 1)[1].split("```", 1)[0] if "```diagramma\n" in testo else ""


def test_q06(repo: Path) -> None:
    schema = repo / "shared" / "setup-claude-md.md"
    assert schema.is_file(), "Q06 manca shared/setup-claude-md.md, lo schema del CLAUDE.md di /setup"
    sezione = re.search(r"\*\*(Come scriv\w)\*\*", read(schema))
    assert sezione, "Q06 lo schema del CLAUDE.md di /setup non ha la sezione della voce"
    nome, altro = sezione.group(1), "Come scrivi" if sezione.group(1) == "Come scrivo" else "Come scrivo"
    for rel in ("skills/humanizer/SKILL.md", "skills/humanizer/references/da-dove-viene.md", "README.md",
                "NOVITA.md", "docs/come-e-fatto.md"):
        testo = read(repo / rel) if (repo / rel).is_file() else ""
        assert f'"{altro}"' not in testo, f'Q06 {rel} cerca la sezione "{altro}", /setup scrive "{nome}"'
    assert f'"{nome}"' in read(repo / "skills" / "humanizer" / "SKILL.md"), f'Q06 humanizer non nomina "{nome}"'
    licenza = repo / "skills" / "italiano-semplificato" / "LICENSE"
    assert licenza.is_file() and "AminBlg" in read(licenza), "Q06 manca la nota MIT di AminBlg/SimpleEnglish"
    readme = read(repo / "README.md").split("## Licenza", 1)[-1]
    for rel in ("skills/humanizer/LICENSE", "skills/italiano-semplificato/LICENSE", "skills/prompt-master/LICENSE"):
        assert rel in readme, f"Q06 la sezione Licenza del README non cita {rel}"
    disegno = repo / "docs" / "come-e-fatto.md"
    originale = _disegno(read(disegno)) if disegno.is_file() else ""
    novita = read(repo / "NOVITA.md")
    copia = _disegno(novita[novita.find("docs/come-e-fatto.md"):])
    assert originale and copia == originale, "Q06 la copia del disegno in NOVITA.md non è uguale a docs/come-e-fatto.md"


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


def test_q11(repo: Path) -> None:
    # Federico, 6/11/2026: i processi di design di Arturo seguono regole in più, senza doppioni con le due skill.
    nota = repo / "shared" / "regole-interfaccia.md"
    assert nota.is_file(), "Q11 manca shared/regole-interfaccia.md"
    testo = read(nota)
    for parte in ("## Parte A", "## Parte B", "## Parte C", "## Lasciate fuori", "## Fonti"):
        assert parte in testo, f"Q11 manca la sezione {parte}"
    assert "poi Impeccable e Hallmark, poi questo file" in testo, "Q11 il file non dice chi vince"
    voci = [r for r in testo.split("## Lasciate fuori")[0].splitlines() if r.startswith("- ")]
    assert len(voci) >= 60, f"Q11 le regole sono {len(voci)}"
    sigle = dict(re.findall(r"^- ([\w-]+): .*?(https://\S+)", testo.split("## Fonti")[1], re.M))
    for voce in voci:
        assert re.match(r"- \((fissa|default)\) ", voce), f"Q11 regola senza tipo: {voce[:60]}"
        fonti = re.search(r"\[([^\]]+)\]$", voce)
        assert fonti, f"Q11 regola senza fonte: {voce[:60]}"
        for sigla in fonti.group(1).split(", "):
            assert sigla.split()[0] in sigle or re.fullmatch(r"\d\.\d+\.\d+", sigla), f"Q11 fonte senza URL: {sigla}"
    assert not re.search("[\u201c\u201d\u00ab\u00bb]", testo), "Q11 virgolette non dritte"
    for lettore in ("agents/ui-ux-consultant.md", "shared/metodo.md", "docs/impeccable.md", "docs/hallmark.md",
                    "README.md"):
        assert "regole-interfaccia.md" in read(repo / lettore), f"Q11 {lettore} non porta alle regole"


TESTS: Dict[str, Callable[[Path], None]] = {
    "Q01": test_q01, "Q02": test_q02, "Q03": test_q03, "Q04": test_q04,
    "Q05": test_q05, "Q06": test_q06, "Q07": test_q07, "Q08": test_q08, "Q09": test_q09,
    "Q10": test_q10, "Q11": test_q11,
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
