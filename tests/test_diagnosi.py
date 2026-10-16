#!/usr/bin/env python3
"""D01-D12: arturo diagnosi, i due controlli di /diagnosi su un progetto intero (16/10/2026).

D01 percorsi: un percorso degli handoff che non esiste più stampa «MANCA: … (da HANDOFF_…)» ed esce 1.
D02 percorsi: tutti presenti, «OK n presenti, 0 mancanti» ed exit 0.
D03 percorsi: URL, link e destini che non sono file («resta», «scarto», «link») non contano.
D04 percorsi: ~ si espande nella HOME, anche tra backtick.
D05 percorsi: legge anche la sezione «Materiali» del CLAUDE.md del progetto, coi percorsi relativi.
D06 progetto inesistente: exit 2 con NON TROVATO, per entrambi i sottocomandi; senza nome fuori
    dalla cartella dei progetti, exit 2.
D07 uso sbagliato: sottocomando o opzione sconosciuti, exit 3.
D08 materiali: un file in Download col nome del progetto e uno in Scrivania citato da un handoff
    compaiono con un destino; un file estraneo no.
D09 materiali: nella cartella del progetto compare il file non tracciato, non quello ignorato né
    quello già committato; un file tracciato sopra 20 MB compare con destino «resta».
D10 nessun file viene spostato, cancellato o modificato da percorsi e materiali.
D11 --json: uscita strutturata coi campi dichiarati; senza nome vale la cartella in cui sei.
D12 «arturo» elenca diagnosi nell'aiuto.
D13 fuori dai backtick il percorso finisce al primo «, », « (», « — », « → » o spazio: la prosa dopo
    non entra nel percorso (falsi MANCA su due handoff veri, 16/10/2026). Tra backtick valgono gli spazi.

Ogni controllo fallisce con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

GIT_ENV = {
    "GIT_AUTHOR_NAME": "prova", "GIT_AUTHOR_EMAIL": "prova@example.invalid",
    "GIT_COMMITTER_NAME": "prova", "GIT_COMMITTER_EMAIL": "prova@example.invalid",
    "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0",
}


class Lab:
    """Una HOME finta: HOME e USERPROFILE spostati insieme, la cartella dei progetti e gli handoff."""

    def __init__(self, repo: Path, tmp: Path):
        self.repo, self.tmp = repo, tmp
        self.home = tmp / "home"
        self.progetti = self.home / "Documents" / "ClaudeCode"
        self.handoffs = self.home / ".claude" / "data" / "handoffs"
        for d in (self.progetti, self.handoffs, self.home / "Downloads", self.home / "Desktop"):
            d.mkdir(parents=True)

    def env(self) -> dict:
        e = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home), ARTURO_TODO=str(self.tmp / "eventi.jsonl"),
                 ARTURO_TELEMETRIA="0", PYTHONDONTWRITEBYTECODE="1", **GIT_ENV)
        e.pop("PROJECTS_BASE", None)
        return e

    def run(self, argv: list, cwd: Path | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(argv, cwd=str(cwd or self.home), env=self.env(), capture_output=True,
                              text=True, encoding="utf-8", timeout=120)

    def arturo(self, *argomenti: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
        return self.run([sys.executable, "-B", str(self.repo / "bin" / "arturo"), *argomenti], cwd=cwd)

    def git(self, cartella: Path, *argomenti: str) -> None:
        r = self.run(["git", "-C", str(cartella), *argomenti])
        assert r.returncode == 0, f"preparazione: git {argomenti}: {r.stderr}"

    def handoff(self, progetto: str, nome: str, materiali: str, altro: str = "") -> Path:
        d = self.handoffs / progetto
        d.mkdir(parents=True, exist_ok=True)
        f = d / nome
        f.write_text(f"# Session Handoff\n\n## Progetto\n- Nome: {progetto}\n\n{altro}"
                     f"## File e materiali\n{materiali}\n## Task Pendenti\n- niente\n", encoding="utf-8")
        return f

    def file(self, path: Path, testo: str = "x") -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(testo, encoding="utf-8")
        return path


def con_lab(repo: Path, prova) -> None:
    assert (repo / "bin" / "diagnosi.py").is_file(), "{codice} manca bin/diagnosi.py"
    with tempfile.TemporaryDirectory(prefix="arturo-diagnosi-") as tmp:
        prova(Lab(repo, Path(tmp)))


def esito(r: subprocess.CompletedProcess) -> str:
    return f"exit {r.returncode}\n{r.stdout}{r.stderr}"


def progetto_libro(lab: Lab) -> Path:
    cartella = lab.progetti / "libro"
    cartella.mkdir()
    return cartella


def caso(codice: str):
    """Riscrive il messaggio di preparazione col codice del controllo."""
    def avvolgi(f):
        def prova(repo: Path) -> None:
            try:
                con_lab(repo, f)
            except AssertionError as e:
                testo = str(e).replace("{codice}", codice)
                raise AssertionError(testo if testo.startswith(codice) else f"{codice} {testo}") from None
        return prova
    return avvolgi


# --- percorsi ------------------------------------------------------------------------------------

@caso("D01")
def test_d01(lab: Lab) -> None:
    progetto_libro(lab)
    c = lab.file(lab.home / "Documents" / "bozza.pdf")
    sparito = lab.home / "Documents" / "sparito.pdf"
    lab.handoff("libro", "HANDOFF_2026-10-15_10-00.md", f"- Bozza → {c}\n- Copertina → {sparito}\n")
    r = lab.arturo("diagnosi", "percorsi", "libro")
    assert r.returncode == 1, f"D01 un percorso sparito non dà exit 1: {esito(r)}"
    assert f"MANCA: {sparito} (da HANDOFF_2026-10-15_10-00.md)" in r.stdout, f"D01 manca la riga MANCA: {esito(r)}"
    assert "OK 1 presenti, 1 mancanti" in r.stdout, f"D01 conti sbagliati: {esito(r)}"
    assert f"MANCA: {c}" not in r.stdout, f"D01 un file presente risulta mancante: {esito(r)}"


@caso("D02")
def test_d02(lab: Lab) -> None:
    progetto_libro(lab)
    a = lab.file(lab.home / "Documents" / "uno.pdf")
    b = lab.file(lab.home / "Documents" / "Due file" / "due.docx")
    lab.handoff("libro", "HANDOFF_2026-10-14_10-00.md", f"- Primo → {a}\n- Secondo → `{b}`\n")
    lab.handoff("libro", "HANDOFF_2026-10-15_10-00.md", f"- Primo, di nuovo → {a}\n")
    r = lab.arturo("diagnosi", "percorsi", "libro")
    assert r.returncode == 0 and "OK 2 presenti, 0 mancanti" in r.stdout and "MANCA" not in r.stdout, \
        f"D02 tutto presente non dà OK ed exit 0: {esito(r)}"


@caso("D03")
def test_d03(lab: Lab) -> None:
    progetto_libro(lab)
    lab.handoff("libro", "HANDOFF_2026-10-15_10-00.md",
                "- Cartella condivisa → https://example.invalid/cartella/abc\n"
                "- Pagina → `https://example.invalid/pagina`\n"
                "- Video pesante → resta dov'è: ~/Video/girato.mov\n"
                "- Prove di stampa → scarto\n"
                "- Documento online → link: https://example.invalid/doc\n"
                "- Mappa → [mappa](/non/esiste/mappa.pdf)\n"
                "- Script → repo libro (commit abc1234)\n")
    r = lab.arturo("diagnosi", "percorsi", "libro")
    assert r.returncode == 0 and "OK 0 presenti, 0 mancanti" in r.stdout and "MANCA" not in r.stdout, \
        f"D03 URL, link o destini non-file contati come percorsi: {esito(r)}"


@caso("D04")
def test_d04(lab: Lab) -> None:
    progetto_libro(lab)
    lab.file(lab.home / "Documents" / "materiali" / "foto.jpg")
    lab.handoff("libro", "HANDOFF_2026-10-15_10-00.md",
                "- Foto → ~/Documents/materiali/foto.jpg\n"
                "- Indice → `~/Documents/materiali/indice.pdf`\n")
    r = lab.arturo("diagnosi", "percorsi", "libro")
    assert "MANCA: ~/Documents/materiali/foto.jpg" not in r.stdout, f"D04 ~ non espanso: {esito(r)}"
    assert r.returncode == 1 and "MANCA: ~/Documents/materiali/indice.pdf (da HANDOFF_2026-10-15_10-00.md)" in r.stdout \
        and "OK 1 presenti, 1 mancanti" in r.stdout, f"D04 ~ tra backtick non espanso: {esito(r)}"


@caso("D05")
def test_d05(lab: Lab) -> None:
    cartella = progetto_libro(lab)
    lab.file(cartella / "dati" / "elenco.csv")
    lab.file(cartella / "CLAUDE.md",
             "# Libro\n\n## Comandi\n- `npm test` e `/fine`\n- `dati/fuori-sezione.csv`\n\n"
             "## Materiali\n- Elenco dei capitoli: `dati/elenco.csv`\n- Archivio scansioni → ~/Archivio/scansioni\n"
             "- Usa /fine a fine giornata\n\n## Altro\n- `dati/assente-altrove.csv`\n")
    r = lab.arturo("diagnosi", "percorsi", "libro")
    assert r.returncode == 1 and "MANCA: ~/Archivio/scansioni (da CLAUDE.md)" in r.stdout, \
        f"D05 la sezione Materiali del CLAUDE.md non è letta: {esito(r)}"
    assert "OK 1 presenti, 1 mancanti" in r.stdout, f"D05 conti sbagliati o righe fuori sezione lette: {esito(r)}"


@caso("D06")
def test_d06(lab: Lab) -> None:
    progetto_libro(lab)
    for sotto in ("percorsi", "materiali"):
        r = lab.arturo("diagnosi", sotto, "inesistente")
        assert r.returncode == 2 and "NON TROVATO" in r.stdout, f"D06 {sotto}: progetto inesistente non dà exit 2: {esito(r)}"
    r = lab.arturo("diagnosi", "percorsi", cwd=lab.home)
    assert r.returncode == 2 and "NON TROVATO" in r.stdout, f"D06 senza nome fuori dai progetti non dà exit 2: {esito(r)}"


@caso("D07")
def test_d07(lab: Lab) -> None:
    progetto_libro(lab)
    for argomenti in (("diagnosi", "boh", "libro"), ("diagnosi", "percorsi", "libro", "--strano"), ("diagnosi",)):
        r = lab.arturo(*argomenti)
        assert r.returncode == 3, f"D07 {' '.join(argomenti)} non dà exit 3: {esito(r)}"


# --- materiali -----------------------------------------------------------------------------------

@caso("D08")
def test_d08(lab: Lab) -> None:
    progetto_libro(lab)
    nel_nome = lab.file(lab.home / "Downloads" / "Libro_contratto firmato.pdf")
    citato = lab.file(lab.home / "Desktop" / "scaletta-capitoli.docx")
    estraneo = lab.file(lab.home / "Downloads" / "bolletta.pdf")
    simile = lab.file(lab.home / "Downloads" / "libroteca.pdf")
    lab.handoff("libro", "HANDOFF_2026-10-15_10-00.md", "- niente\n",
                altro="## Ripartenza\nRileggere scaletta-capitoli.docx sulla Scrivania.\n\n")
    r = lab.arturo("diagnosi", "materiali", "libro")
    assert r.returncode == 0, f"D08 materiali non esce 0: {esito(r)}"
    righe = r.stdout.splitlines()
    riga_nome = next((x for x in righe if nel_nome.name in x), "")
    riga_citato = next((x for x in righe if citato.name in x), "")
    assert riga_nome.strip().startswith("archivia") and "col nome del progetto" in riga_nome, \
        f"D08 il file in Download col nome del progetto non compare con un destino: {esito(r)}"
    assert riga_citato.strip().startswith("archivia") and "citato per nome" in riga_citato, \
        f"D08 il file citato dall'handoff non compare: {esito(r)}"
    assert estraneo.name not in r.stdout and simile.name not in r.stdout, f"D08 compare un file estraneo: {esito(r)}"


@caso("D09")
def test_d09(lab: Lab) -> None:
    cartella = progetto_libro(lab)
    lab.git(cartella, "init", "-q")
    lab.file(cartella / ".gitignore", "build/\n")
    lab.file(cartella / "capitolo1.md", "# Uno\n")
    with open(cartella / "audio.wav", "wb") as f:
        f.write(b"\0" * (21 * 1024 * 1024))
    lab.git(cartella, "add", "-A")
    lab.git(cartella, "commit", "-q", "-m", "inizio")
    lab.file(cartella / "note" / "appunti.md", "nuovi")
    lab.file(cartella / "build" / "uscita.pdf")
    r = lab.arturo("diagnosi", "materiali", "libro")
    assert r.returncode == 0, f"D09 materiali non esce 0: {esito(r)}"
    riga = next((x for x in r.stdout.splitlines() if "appunti.md" in x), "")
    assert riga.strip().startswith("repo") and "non tracciato" in riga, f"D09 il file non tracciato non compare: {esito(r)}"
    assert "uscita.pdf" not in r.stdout and "capitolo1.md" not in r.stdout, \
        f"D09 compare un file ignorato o già committato: {esito(r)}"
    pesante = next((x for x in r.stdout.splitlines() if "audio.wav" in x), "")
    assert pesante.strip().startswith("resta") and "sopra 20 MB" in pesante, \
        f"D09 il file tracciato sopra 20 MB non compare con destino resta: {esito(r)}"


def fotografia(radice: Path) -> dict:
    out = {}
    for d, _, files in os.walk(radice):
        if ".git" in Path(d).parts:
            continue
        for x in files:
            p = Path(d) / x
            st = p.stat()
            out[str(p)] = (st.st_size, st.st_mtime_ns)
    return out


@caso("D10")
def test_d10(lab: Lab) -> None:
    cartella = progetto_libro(lab)
    lab.git(cartella, "init", "-q")
    lab.file(cartella / "nuovo.txt")
    lab.file(lab.home / "Downloads" / "libro-bozza.pdf")
    lab.file(lab.home / "Desktop" / "libro.zip")
    lab.handoff("libro", "HANDOFF_2026-10-15_10-00.md", f"- Bozza → {lab.home / 'Downloads' / 'libro-bozza.pdf'}\n"
                f"- Altro → {lab.home / 'Documents' / 'via.pdf'}\n")
    prima = fotografia(lab.home)
    for sotto in ("percorsi", "materiali"):
        for extra in ((), ("--json",)):
            lab.arturo("diagnosi", sotto, "libro", *extra)
    dopo = fotografia(lab.home)
    assert prima == dopo, f"D10 diagnosi ha toccato dei file: {sorted(set(prima) ^ set(dopo))}"


@caso("D11")
def test_d11(lab: Lab) -> None:
    cartella = progetto_libro(lab)
    lab.file(lab.home / "Downloads" / "libro-bozza.pdf")
    sparito = lab.home / "via.pdf"
    lab.handoff("libro", "HANDOFF_2026-10-15_10-00.md", f"- Altro → {sparito}\n")
    sotto = cartella / "capitoli"
    sotto.mkdir()
    r = lab.arturo("diagnosi", "percorsi", "--json", cwd=sotto)
    try:
        dati = json.loads(r.stdout)
    except ValueError:
        raise AssertionError(f"D11 percorsi --json non è JSON: {esito(r)}") from None
    assert r.returncode == 1 and dati["progetto"] == "libro" and dati["mancanti"][0]["assoluto"] == str(sparito) \
        and dati["mancanti"][0]["da"] == "HANDOFF_2026-10-15_10-00.md" and dati["presenti"] == [], \
        f"D11 percorsi --json senza nome dalla sottocartella: {esito(r)}"
    r = lab.arturo("diagnosi", "materiali", "libro", "--json")
    try:
        dati = json.loads(r.stdout)
    except ValueError:
        raise AssertionError(f"D11 materiali --json non è JSON: {esito(r)}") from None
    voce = next((v for v in dati["file"] if v["path"].endswith("libro-bozza.pdf")), None)
    assert r.returncode == 0 and voce and voce["destino"] in ("repo", "archivia", "resta", "scarto") \
        and voce["motivo"] and voce["origine"], f"D11 materiali --json: {esito(r)}"


@caso("D12")
def test_d12(lab: Lab) -> None:
    r = lab.arturo()
    assert r.returncode == 0 and "arturo diagnosi" in r.stdout, f"D12 l'aiuto di arturo non elenca diagnosi: {esito(r)}"
    r = lab.arturo("diagnosi", "--help")
    assert r.returncode == 0 and "percorsi" in r.stdout and "materiali" in r.stdout, f"D12 aiuto di diagnosi: {esito(r)}"


@caso("D13")
def test_d13(lab: Lab) -> None:
    progetto_libro(lab)
    (lab.home / ".claude" / "skills" / "tasks").mkdir(parents=True)
    lab.file(lab.home / "Documents" / "Il Libro" / "bozza.pdf")
    lab.handoff("libro", "HANDOFF_2026-10-15_10-00.md",
                "- mappa.json → ~/.claude/skills/tasks, commessa libro, nel sync della config.\n"
                "- Porting nella config → ~/.claude, commit ef0d5957.\n"
                "- Bozza → `~/Documents/Il Libro/bozza.pdf`, versione 2\n"
                "- Copie → ~/Archivio/copie (del 15/10) — da rifare\n"
                "- Appunti → ~/Archivio/appunti → poi nel repo\n"
                "- Scaletta → ~/Documents/Il Libro/scaletta.pdf\n")
    r = lab.arturo("diagnosi", "percorsi", "libro")
    mancanti = sorted(x for x in r.stdout.splitlines() if x.startswith("MANCA: "))
    attesi = sorted(f"MANCA: ~/{p} (da HANDOFF_2026-10-15_10-00.md)"
                    for p in ("Archivio/copie", "Archivio/appunti", "Documents/Il"))
    assert r.returncode == 1 and mancanti == attesi and "OK 3 presenti, 3 mancanti" in r.stdout, \
        f"D13 fuori dai backtick il percorso non finisce a «, », « (», « — », « → » o allo spazio: {esito(r)}"


TESTS = {"D01": test_d01, "D02": test_d02, "D03": test_d03, "D04": test_d04, "D05": test_d05, "D06": test_d06,
         "D07": test_d07, "D08": test_d08, "D09": test_d09, "D10": test_d10, "D11": test_d11, "D12": test_d12,
         "D13": test_d13}


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
    for flusso in (sys.stdout, sys.stderr):  # su Windows la pipe è in cp1252: i messaggi hanno gli accenti
        try:
            flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    raise SystemExit(main())
