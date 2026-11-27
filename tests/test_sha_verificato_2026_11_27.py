#!/usr/bin/env python3
"""SV01-SV06: la copia del plugin installata fuori da /aggiorna si verifica (#6791, rilievo S2 della revisione del 20/11).

`claude plugin update` e il pannello /plugin installano lo sha scritto nel catalogo senza guardare il tag. Prima di
questo banco /aggiorna diceva "GIÀ AGGIORNATO" a ogni copia con lo sha del catalogo: il tag non si verificava mai.
Ora Arturo segna in session-env/plugin-verificato.json lo sha che ha verificato, e una copia diversa si verifica.

SV01 tag non firmato, copia messa da claude plugin update col MANIFEST firmato: `plugin` dà "possibile
     compromissione" (uscita 3) e lo stato lo dice, invece di "GIÀ AGGIORNATO";
SV02 il catalogo riporta indietro a un rilascio firmato più vecchio dell'ultimo verificato: uscita 3;
SV03 tag firmato giusto, copia messa fuori da /aggiorna: "GIÀ AGGIORNATO", e lo sha resta segnato;
SV04 l'avvio dice in una riga che la copia non è verificata se lo sha segnato è un altro; tace se è lo stesso e
     se il file non c'è ancora (la prima apertura con questa versione);
SV05 il controllo dell'ora (`controlla --subito`) fa lo stesso: tag non firmato = stato compromesso, anche al
     controllo dopo; tag firmato = sha segnato e stato aggiornato;
SV06 un aggiornamento riuscito di /aggiorna segna lo sha nuovo, e l'avvio dopo tace.

Rilasci, chiavi e CLI finta sono quelli di test_fiducia_2026_11_05.py: niente rete, niente CLI vera. Sulla base
26d2e4b (main prima di #6791 S2) sono tutti rossi. Con --avvelena una copia del repository rotta in un punto alla
volta deve far fallire il caso che lo sorveglia.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

CASI = ["SV01", "SV02", "SV03", "SV04", "SV05", "SV06"]
DISCRIMINANTI = list(CASI)

_spec = importlib.util.spec_from_file_location("fd", str(Path(__file__).resolve().parent / "test_fiducia_2026_11_05.py"))
fd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fd)

AVVISO = "non è passata dalla verifica della firma"


def orsa_con(r, tmp: Path, copia: Path, versione: str, sha: str, verificato: dict | None) -> dict:
    """L'Orsa di prova: catalogo, copia installata, stato appena controllato e, se c'è, lo sha già verificato."""
    orsa = r.orsa
    (orsa / "plugins").mkdir(exist_ok=True)
    (orsa / "plugins" / "known_marketplaces.json").write_text(
        json.dumps({"arturo": {"installLocation": str(r.catalogo)}}), encoding="utf-8")
    (orsa / "plugins" / "installed_plugins.json").write_text(json.dumps({"plugins": {"arturo@arturo": [
        {"scope": "user", "installPath": str(copia), "version": versione, "gitCommitSha": sha}]}}), encoding="utf-8")
    (orsa / "session-env").mkdir(exist_ok=True)
    (orsa / "session-env" / "aggiornamento.json").write_text(json.dumps({
        "stato": "aggiornato", "plugin": True, "controllato": time.time(), "riuscito": time.time()}), encoding="utf-8")
    if verificato is not None:
        (orsa / "session-env" / "plugin-verificato.json").write_text(json.dumps(verificato), encoding="utf-8")
    fd.modulo_fiducia(r.repo).fissa_ancora(copia, orsa)
    # manuali: l'avvio non lancia il controllo staccato, che resterebbe vivo dopo il banco.
    return dict(r.env, ARTURO_CLAUDE=str(fd.cli_finta(tmp, fd.CLAUDE_FINTO)), ARTURO_AGGIORNAMENTI="manuali")


def lancia(copia: Path, env: dict, *argomenti):
    p = fd.esegui([sys.executable, copia / "bin" / "aggiornamenti.py", *argomenti], env=env)
    return p, (p.stdout + p.stderr).strip()


def letto(orsa: Path, nome: str) -> dict:
    try:
        return json.loads((orsa / "session-env" / nome).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def un_rilascio(repo: Path, tmp: Path, chiavi: dict, nome: str, firma: str | None, versione: str = "0.4.0"):
    base = tmp / nome
    base.mkdir()
    r = fd.Rilasci(repo, base, chiavi)
    sha = r.rilascio(versione, firma)
    r.indica(f"plugin-v{versione}", sha)
    privata, firmatari = chiavi["rilasci"]
    copia = fd.copia_plugin(repo, base / "cache" / versione, versione, firmatari, privata)
    return r, sha, copia


def caso_sv01(repo: Path, tmp: Path, chiavi: dict) -> list:
    r, sha, copia = un_rilascio(repo, tmp, chiavi, "sv01", None)
    env = orsa_con(r, tmp, copia, "0.4.0", sha, None)
    p, uscita = lancia(copia, env, "plugin")
    stato = letto(r.orsa, "aggiornamento.json")
    if p.returncode != 3 or "POSSIBILE COMPROMISSIONE" not in uscita or not stato.get("compromesso"):
        return [f"SV01 tag non firmato già installato: rc {p.returncode}, stato {stato.get('stato')!r}, {uscita[-200:]!r}"]
    return []


def caso_sv02(repo: Path, tmp: Path, chiavi: dict) -> list:
    base = tmp / "sv02"
    base.mkdir()
    r = fd.Rilasci(repo, base, chiavi)
    sha3 = r.rilascio("0.3.0", "rilasci")
    sha4 = r.rilascio("0.4.0", "rilasci")
    privata, firmatari = chiavi["rilasci"]
    # Il catalogo torna al rilascio firmato 0.3.0, e claude plugin update l'ha già installato.
    git_tag = fd.git(r.pub, "checkout", "-q", "plugin-v0.3.0")
    r.indica("plugin-v0.3.0", sha3)
    copia = fd.copia_plugin(repo, base / "cache" / "0.3.0", "0.3.0", firmatari, privata)
    env = orsa_con(r, tmp, copia, "0.3.0", sha3, {"sha": sha4, "tag": "plugin-v0.4.0", "versione": "0.4.0"})
    p, uscita = lancia(copia, env, "plugin")
    if p.returncode != 3 or "più vecchia dell'ultimo rilascio verificato" not in uscita:
        return [f"SV02 rilascio firmato più vecchio: rc {p.returncode}/{git_tag.returncode}, {uscita[-200:]!r}"]
    return []


def caso_sv03(repo: Path, tmp: Path, chiavi: dict) -> list:
    r, sha, copia = un_rilascio(repo, tmp, chiavi, "sv03", "rilasci")
    env = orsa_con(r, tmp, copia, "0.4.0", sha, None)
    p, uscita = lancia(copia, env, "plugin")
    segnato = letto(r.orsa, "plugin-verificato.json")
    if p.returncode != 0 or "GIÀ AGGIORNATO" not in uscita or segnato.get("sha") != sha \
            or segnato.get("versione") != "0.4.0":
        return [f"SV03 tag firmato giusto: rc {p.returncode}, segnato {str(segnato.get('sha'))[:12]}, {uscita[-200:]!r}"]
    return []


def caso_sv04(repo: Path, tmp: Path, chiavi: dict) -> list:
    rossi = []
    for variante, verificato, atteso in (("altro", {"sha": "e" * 40, "versione": "0.4.0"}, True),
                                         ("stesso", None, False), ("senza", None, False)):
        r, sha, copia = un_rilascio(repo, tmp, chiavi, f"sv04-{variante}", "rilasci")
        if variante == "stesso":
            verificato = {"sha": sha, "versione": "0.4.0"}
        env = orsa_con(r, tmp, copia, "0.4.0", sha, verificato)
        p, uscita = lancia(copia, env, "stato")
        if (AVVISO in p.stdout) != atteso or p.returncode != 0:
            rossi.append(f"SV04 avvio con lo sha verificato {variante}: rc {p.returncode}, avviso {AVVISO in p.stdout}, "
                         f"{uscita[-160:]!r}")
    return rossi


def caso_sv05(repo: Path, tmp: Path, chiavi: dict) -> list:
    rossi = []
    r, sha, copia = un_rilascio(repo, tmp, chiavi, "sv05-no", None)
    env = orsa_con(r, tmp, copia, "0.4.0", sha, {"sha": "e" * 40, "versione": "0.3.0"})
    for giro in (1, 2):
        p, uscita = lancia(copia, env, "controlla", "--subito")
        stato = letto(r.orsa, "aggiornamento.json")
        if not stato.get("compromesso"):
            rossi.append(f"SV05 controllo {giro} con tag non firmato: stato {stato!r}, {uscita[-160:]!r}")
            break
    r, sha, copia = un_rilascio(repo, tmp, chiavi, "sv05-si", "rilasci")
    env = orsa_con(r, tmp, copia, "0.4.0", sha, {"sha": "e" * 40, "versione": "0.3.0"})
    p, uscita = lancia(copia, env, "controlla", "--subito")
    stato, segnato = letto(r.orsa, "aggiornamento.json"), letto(r.orsa, "plugin-verificato.json")
    if stato.get("compromesso") or stato.get("stato") != "aggiornato" or segnato.get("sha") != sha:
        rossi.append(f"SV05 controllo con tag firmato: stato {stato.get('stato')!r}, segnato "
                     f"{str(segnato.get('sha'))[:12]}, {uscita[-160:]!r}")
    return rossi


def caso_sv06(repo: Path, tmp: Path, chiavi: dict) -> list:
    base = tmp / "sv06"
    base.mkdir()
    r = fd.Rilasci(repo, base, chiavi)
    privata, firmatari = chiavi["rilasci"]
    sha3 = r.rilascio("0.3.0", "rilasci")
    prima = fd.copia_plugin(repo, base / "cache" / "0.3.0", "0.3.0", firmatari, privata)
    sha4 = r.rilascio("0.4.0", "rilasci")
    r.indica("plugin-v0.4.0", sha4)
    nuova = fd.copia_plugin(repo, base / "cache" / "0.4.0", "0.4.0", firmatari, privata)
    env = orsa_con(r, tmp, prima, "0.3.0", sha3, {"sha": sha3, "tag": "plugin-v0.3.0", "versione": "0.3.0"})
    env["FINTO_INSTALLA"] = json.dumps({"path": str(nuova), "version": "0.4.0", "sha": sha4})
    p, uscita = lancia(prima, env, "plugin")
    segnato = letto(r.orsa, "plugin-verificato.json")
    dopo, _ = lancia(nuova, env, "stato")
    if p.returncode != 0 or not p.stdout.startswith("APPLICATO") or segnato.get("sha") != sha4 or AVVISO in dopo.stdout:
        return [f"SV06 aggiornamento riuscito: rc {p.returncode}, segnato {str(segnato.get('sha'))[:12]}, avvio dopo "
                f"{dopo.stdout.strip()[:80]!r}, {uscita[-160:]!r}"]
    return []


def prova(repo: Path, solo: str | None = None) -> list:
    rossi = []
    with tempfile.TemporaryDirectory(prefix="sha-verificato.") as t:
        tmp = Path(os.path.realpath(t))
        chiavi = {n: fd.chiave(tmp, n) for n in ("rilasci", "altra")}
        for codice, fn in (("SV01", caso_sv01), ("SV02", caso_sv02), ("SV03", caso_sv03), ("SV04", caso_sv04),
                           ("SV05", caso_sv05), ("SV06", caso_sv06)):
            if solo in (None, codice):
                try:
                    rossi += fn(repo, tmp, chiavi)
                except Exception as errore:  # noqa: BLE001 - sulla base il file dello sha non c'è
                    rossi.append(f"{codice} errore: {type(errore).__name__}: {str(errore)[:160]}")
    return rossi


# (caso, file, testo giusto, testo rotto): ogni veleno toglie la riga che il caso sorveglia.
VELENI = [
    ("SV01", "bin/aggiornamenti.py", "        rc_copia, motivo = verifica_installata(radice(), orsa)\n",
     '        rc_copia, motivo = 0, ""\n'),
    ("SV02", "bin/aggiornamenti.py", "        if rc == 0 and numero(tag) < numero(ultimo):", "        if False:"),
    ("SV03", "bin/aggiornamenti.py", "    if rc == 0:\n        segna_verificato(r, sha, tag)", "    if False:\n        pass"),
    ("SV04", "bin/aggiornamenti.py", '    if nuova_copia and leggi(file_verificato(r)).get("sha")',
     '    if False and leggi(file_verificato(r)).get("sha")'),
    ("SV05", "bin/aggiornamenti.py", '    rc_copia, motivo_copia = verifica_installata(r, orsa) if not estranea else (0, "")',
     '    rc_copia, motivo_copia = 0, ""'),
    ("SV06", "bin/aggiornamenti.py", "    segna_verificato(radice(), sha, tag)\n    segna_aggiornato", "    segna_aggiornato"),
]


def avvelena(repo: Path) -> int:
    esiti = []
    for caso, rel, giusto, rotto in VELENI:
        with tempfile.TemporaryDirectory() as tmp:
            copia = Path(tmp) / "repo"
            shutil.copytree(repo, copia, ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules", "tests"))
            testo = (copia / rel).read_text(encoding="utf-8")
            assert testo.count(giusto) == 1, f"veleno {caso}: il testo da rompere non c'è più in {rel}"
            (copia / rel).write_text(testo.replace(giusto, rotto), encoding="utf-8")
            rossi = prova(copia, solo=caso)
            codici = [r.split()[0] for r in rossi]
            if caso not in codici:
                print(f"VELENO {caso} NON ATTACCA: rossi {codici}")
                return 1
            print(f"VELENO {caso} ROSSO: {next(r for r in rossi if r.startswith(caso))[:120]}")
            esiti.append(caso)
    print(f"VELENI_ROSSI={','.join(esiti)} veleni={len(VELENI)}")
    return 0 if len(esiti) == len(VELENI) else 1


def main() -> int:
    for flusso in (sys.stdout, sys.stderr):  # su Windows l'uscita è cp1252 e un rosso con un accento cade (#4987)
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    parser.add_argument("--avvelena", action="store_true")
    argomenti = parser.parse_args()
    if argomenti.avvelena:
        return avvelena(Path(argomenti.repo))
    rossi = prova(Path(argomenti.repo))
    if argomenti.baseline_ref:
        codici = sorted({r.split()[0] for r in rossi})
        assert codici == DISCRIMINANTI, f"baseline non discriminante: rossi {codici}, attesi {DISCRIMINANTI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    verdi = len(CASI) - len({r.split()[0] for r in rossi})
    print(f"sha verificato: {verdi}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
