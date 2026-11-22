#!/usr/bin/env python3
"""TP01-TP05: i testi pubblici di Arturo dicono cosa c'è nel rilascio (revisione del 22/11/2026, A3, A9, A10, #6418).

TP01 ROADMAP.md: nessuno "Stato:" dice "su dev", "su un ramo di sviluppo" o "col prossimo rilascio". Lo stato
     si legge dal contenuto del rilascio firmato: il 22/11 storico, intervista e fascicolo risultavano "su un
     ramo di sviluppo" ed erano nel plugin dalla 0.2.16. Un "uscito nella 0.2.X" nomina una versione esistente
     nella testa di "Uscito di recente" o prima.
TP02 La frase d'ingresso del README e di /setup è quella del sito e di INIZIA.md (#6091): il link di GitHub,
     ramo landing-v2. La pagina /inizia/ è una copia e non è l'ancora di fiducia.
TP03 Volta non trapela: l'aiuto di `arturo spazi` non la nomina (bin/spazi.py dice che Volta non è uno spazio),
     il metodo non la nomina, e le voci di NOVITA su Volta dicono che è una prova di chi mantiene Arturo.
TP04 docs/come-e-fatto.md mostra il mod e lo Sportello (server/), con la riga in tabella e il rimando a
     privacy.md; la copia del disegno in testa a NOVITA è uguale (lo controlla anche Q06 di test_mod_skill.py).
TP05 la ripresa da sola: la voce della roadmap dice che per gli utenti di Arturo è da fare, finché la logica
     sta solo in Volta (A3, D3).
TP06 il README installa il plugin (D2, passo 5b): la sezione Installazione dà i due comandi del plugin e non ha più
     il clone in ~/.claude, il blocco B= né il remote da rinominare.
TP07 chi usa più computer ha i suoi passi: docs/migrazione.md ha la sezione "Con più computer" col pull e lo script
     d'installazione, e i due messaggi di bin/migra.py rimandano lì invece di "si fa a mano".
TP08 lo spegnimento della copia ha una data in ROADMAP: la voce del passaggio la dice, e "Da decidere" la porta
     col task che la conferma (#5270).

Con --avvelena ogni controllo riceve una copia del repository rotta nel punto che sorveglia, e deve fallire
col suo codice e il motivo atteso (VELENI). Con --baseline-ref la controprova: sulla base ogni caso è rosso.
Solo libreria standard, Python 3.8 o successivo. Nessun modello.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

FRASE = "Installa Arturo: https://github.com/stellakamikaze/arturo/blob/landing-v2/INIZIA.md"
RAMI = re.compile(r"su dev\b|ramo di sviluppo|prossimo rilascio", re.I)
BETA = "Volta è una prova di chi mantiene Arturo"


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8").replace("\r\n", "\n") if p.is_file() else ""


def stati(roadmap: str) -> list:
    return [r for r in roadmap.splitlines() if r.startswith("Stato:")]


def test_tp01(repo: Path) -> None:
    roadmap = read(repo / "ROADMAP.md")
    righe = stati(roadmap)
    assert righe, "TP01 la roadmap non ha righe Stato"
    sui_rami = [r[:80] for r in righe if RAMI.search(r)]
    assert not sui_rami, f"TP01 uno Stato parla dei rami, non del rilascio: {sui_rami[0]}"
    uscite = roadmap.split("## Uscito di recente", 1)[-1]
    versioni = set(re.findall(r"versione (0\.\d+\.\d+)", uscite))
    citate = set(re.findall(r"uscit[oaie] nella (0\.\d+\.\d+)", "\n".join(righe)))
    ignote = sorted(citate - versioni - {v for v in citate if tuple(map(int, v.split("."))) <= (0, 2, 4)})
    assert not ignote, f"TP01 uno Stato cita una versione che Uscito di recente non elenca: {ignote}"


def test_tp02(repo: Path) -> None:
    readme = read(repo / "README.md")
    assert FRASE in readme, "TP02 il README non usa la frase di INIZIA.md (#6091)"
    assert "arturo.stellakamikaze.org/inizia/" not in readme, "TP02 il README incolla ancora la pagina /inizia/"
    setup = read(repo / "commands" / "setup.md")
    assert FRASE in setup, "TP02 /setup rimanda a un'altra frase d'ingresso"


def test_tp03(repo: Path) -> None:
    arturo = read(repo / "bin" / "arturo")
    riga = next((r for r in arturo.splitlines() if r.strip().startswith('"spazi":')), "")
    assert riga and "Volta" not in riga, "TP03 l'aiuto di arturo spazi nomina Volta come spazio"
    metodo = read(repo / "shared" / "metodo.md")
    assert "Volta" not in metodo, "TP03 il metodo di ogni persona nomina Volta"
    novita = read(repo / "NOVITA.md")
    voci = re.split(r"\n(?=## \d{4}-\d{2}-\d{2})", novita)
    senza = [v.splitlines()[0][3:60] for v in voci
             if re.match(r"## \d{4}-\d{2}-\d{2} — In Volta|## 2026-11-17 — (La ripartenza di /inizio diventa|Claude apre)", v)
             and BETA not in v]
    assert not senza, f"TP03 una voce di NOVITA su Volta non dice che è una prova: {senza[0]}"


def disegno(testo: str) -> str:
    return testo.split("```diagramma\n", 1)[1].split("```", 1)[0] if "```diagramma\n" in testo else ""


def test_tp04(repo: Path) -> None:
    pagina = read(repo / "docs" / "come-e-fatto.md")
    figura = disegno(pagina)
    assert "Sportello di Arturo" in figura and "server/" in figura, "TP04 il disegno non mostra lo Sportello (server/)"
    assert "il mod" in figura and "redazione dei segreti" in figura, "TP04 il disegno non mostra il mod"
    tabella = pagina.split("## Chi aggiorna cosa", 1)[-1]
    riga = next((r for r in tabella.splitlines() if r.startswith("| Sportello di Arturo")), "")
    assert "privacy.md" in riga, "TP04 la tabella non ha la riga dello Sportello col rimando a privacy.md"
    novita = read(repo / "NOVITA.md")
    copia = disegno(novita[novita.find("docs/come-e-fatto.md"):])
    assert copia == figura, "TP04 la copia del disegno in testa a NOVITA non è uguale a docs/come-e-fatto.md"


def test_tp05(repo: Path) -> None:
    roadmap = read(repo / "ROADMAP.md")
    voce = roadmap.split("{#ripresa}", 1)[-1].split("\n### ", 1)[0]
    stato = next((r for r in voce.splitlines() if r.startswith("Stato:")), "")
    assert "da fare per chi usa Arturo" in stato, "TP05 la voce della ripresa non dice che per gli utenti è da fare"


def sezione(testo: str, titolo: str) -> str:
    """Il testo di una sezione markdown che comincia con `titolo`, fino al titolo dello stesso livello dopo."""
    m = re.search(r"^(#+) " + re.escape(titolo) + r".*?$(.*?)(?=^\1 |\Z)", testo, re.M | re.S)
    return m.group(2) if m else ""


def test_tp06(repo: Path) -> None:
    inst = sezione(read(repo / "README.md"), "Installazione")
    assert inst, "TP06 il README non ha la sezione Installazione"
    for riga in ("claude plugin marketplace add stellakamikaze/arturo#catalogo", "claude plugin install arturo@arturo"):
        assert riga in inst, f"TP06 il README non installa il plugin: manca {riga}"
    for vecchio in ("git clone", 'B="$HOME/.claude-backup-', "remote rename origin upstream", "riporta-tuoi.sh"):
        assert vecchio not in inst, f"TP06 il README installa ancora il clone: {vecchio}"


def test_tp07(repo: Path) -> None:
    piu = sezione(read(repo / "docs" / "migrazione.md"), "Con più computer")
    assert piu, "TP07 docs/migrazione.md non ha la sezione Con più computer"
    for riga in ("git -C ~/.claude pull --ff-only", "curl -fsSL https://arturo.stellakamikaze.org/installa.sh | bash",
                 "arturo migra --unica-macchina"):
        assert riga in piu, f"TP07 i passi per più computer non dicono {riga}"
    migra = read(repo / "bin" / "migra.py")
    assert "si fa a mano" not in migra, "TP07 bin/migra.py dice ancora che con più computer si fa a mano"
    assert migra.count("docs/migrazione.md, sezione Con più computer") == 2, \
        "TP07 i messaggi di bin/migra.py non rimandano ai passi per più computer"


def test_tp08(repo: Path) -> None:
    roadmap = read(repo / "ROADMAP.md")
    voce = sezione(roadmap, "Il passaggio al plugin per chi usa già Arturo")
    data = re.search(r"\b\d{1,2} (gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|"
                     r"novembre|dicembre) 20\d\d\b", voce)
    assert data and "spegnimento della copia" in voce, "TP08 la voce del passaggio non dà la data di spegnimento della copia"
    decidere = sezione(roadmap, "Da decidere")
    riga = next((r for r in decidere.splitlines() if data.group(0) in r), "")
    assert "#5270" in riga, "TP08 Da decidere non porta la data di spegnimento col task che la conferma"


CASI = (("TP01", test_tp01), ("TP02", test_tp02), ("TP03", test_tp03), ("TP04", test_tp04), ("TP05", test_tp05),
        ("TP06", test_tp06), ("TP07", test_tp07), ("TP08", test_tp08))

VELENI = (
    ("TP01", [("ROADMAP.md", "Stato: uscito nella 0.2.4.", "Stato: in corso, su dev.")], "parla dei rami"),
    ("TP02", [("README.md", "incolla questa frase: `" + FRASE, "incolla questa frase: `Installa Arturo: "
               "https://arturo.stellakamikaze.org/inizia/")], "/inizia/"),
    ("TP03", [("shared/metodo.md", "`/fine` non le scrive l'handoff e la elimina",
               "Volta la elimina alla chiusura, `/fine` non le scrive l'handoff")], "metodo"),
    ("TP04", [("docs/come-e-fatto.md", "┌─ Sportello di Arturo", "┌─ Server di Arturo")], "Sportello"),
    ("TP05", [("ROADMAP.md", "Stato: da fare per chi usa Arturo.", "Stato: in corso.")], "ripresa"),
    ("TP06", [("README.md", "claude plugin install arturo@arturo", "git clone https://github.com/stellakamikaze/arturo.git")],
     "installa"),
    ("TP07", [("bin/migra.py", "docs/migrazione.md, sezione Con più computer", "si fa a mano")], "più computer"),
    ("TP08", [("ROADMAP.md", "<!-- task: #5270 -->", "")], "Da decidere"),
)

FILE = ("ROADMAP.md", "README.md", "NOVITA.md", "bin/arturo", "shared/metodo.md", "commands/setup.md",
        "docs/come-e-fatto.md", "docs/migrazione.md", "bin/migra.py")


def copia_di(repo: Path) -> Path:
    copia = Path(tempfile.mkdtemp(prefix="arturo-testi-pubblici."))
    for rel in FILE:
        (copia / rel).parent.mkdir(parents=True, exist_ok=True)
        if (repo / rel).is_file():
            shutil.copy2(repo / rel, copia / rel)
    return copia


def avvelena(repo: Path) -> int:
    assert len(VELENI) == len(CASI), f"veleni {len(VELENI)} per {len(CASI)} controlli"
    casi = dict(CASI)
    inerti = []
    for codice, modifiche, motivo in VELENI:
        copia = copia_di(repo)
        try:
            for rel, vecchio, nuovo in modifiche:
                testo = read(copia / rel)
                assert testo.count(vecchio) >= 1, f"veleno {codice}: il punto da rompere non c'è più in {rel}"
                (copia / rel).write_bytes(testo.replace(vecchio, nuovo, 1).encode("utf-8"))
            try:
                casi[codice](copia)
                inerti.append(f"{codice}: verde con il veleno")
            except AssertionError as e:
                if not (str(e).startswith(codice) and motivo in str(e)):
                    inerti.append(f"{codice}: rosso col motivo sbagliato: {e}")
                else:
                    print(f"VELENO {codice} ROSSO: {str(e)[:120]}")
        finally:
            shutil.rmtree(copia, ignore_errors=True)
    assert not inerti, "veleni che non attaccano:\n" + "\n".join(inerti)
    print(f"VELENI_ROSSI={','.join(v[0] for v in VELENI)} veleni={len(VELENI)}")
    return 0


def base(repo: Path, ref: str) -> Path:
    copia = Path(tempfile.mkdtemp(prefix="arturo-testi-pubblici-base."))
    for rel in FILE:
        r = subprocess.run(["git", "-C", str(repo), "show", f"{ref}:{rel}"], capture_output=True)
        if r.returncode == 0:
            (copia / rel).parent.mkdir(parents=True, exist_ok=True)
            (copia / rel).write_bytes(r.stdout)
    return copia


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    parser.add_argument("--avvelena", action="store_true")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.avvelena:
        return avvelena(repo)
    radice = base(repo, args.baseline_ref) if args.baseline_ref else repo
    errori = []
    try:
        for codice, caso in CASI:
            try:
                caso(radice)
            except AssertionError as e:
                errori.append(str(e))
    finally:
        if args.baseline_ref:
            shutil.rmtree(radice, ignore_errors=True)
    if args.baseline_ref:
        codici = sorted({e.split()[0] for e in errori})
        attesi = [c for c, _ in CASI]
        assert codici == attesi, f"baseline non discriminante: rossi {codici}, attesi {attesi}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for e in errori:
        print("KO", e)
    if errori:
        return 1
    print(f"PASS {','.join(c for c, _ in CASI)} controlli={len(CASI)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
