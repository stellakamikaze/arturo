#!/usr/bin/env python3
"""RP01-RP07: arturo ripartenza scrivi, la ripartenza di /inizio come dati per Volta (17/11/2026, #5910).

/inizio passa l'elenco numerato della ripartenza a bin/ripartenza.py; la sonda di Volta lo legge da
<config>/cache/ripartenza/<sessione>.json e lo mostra come checklist con una nota per riga.

RP01 scrive, da bin/arturo: versione, sid, numeri, id con o senza "#", marca, partenza; un campo
     sconosciuto sparisce.
RP02 tetti: 320 voci diventano VOCI (300), un testo lungo si ferma a TESTO caratteri, e l'uscita dice che 20
     voci non entrano.
RP03 schema rotto: niente filoni, voce senza testo o numero doppio danno exit 2 e nessun file.
RP04 senza sessione esce 0 e non scrive; ARTURO_RIPARTENZA=0 spegne; un sottocomando sbagliato dà 2.
RP05 una ripartenza di più di due giorni si cancella alla scrittura dopo; una recente di un'altra sessione resta.
RP06 la cartella segue CLAUDE_CONFIG_DIR, come la sonda di Volta.
RP07 /inizio: il modello JSON della FASE 5 passa lo schema del comando, e la FASE 6 dice come leggere
     ogni parte del messaggio della checklist.
RP08 senza la cartella di Volta (~/.config/herdr-app) esce 0 e non scrive, e /inizio passa la checklist
     solo se la FASE 1 stampa la riga VOLTA (22/11/2026, rilievo A9).

Con --avvelena ogni controllo riceve una copia del repository rotta nel punto che sorveglia, e deve
fallire col suo codice e il motivo atteso (VELENI). Solo libreria standard. Nessun modello.
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
import time
from pathlib import Path

SID = "0f3c2b1a-1111-2222-3333-444455556666"
BUONO = {
    "progetto": "il-libro", "titolo": "Il libro · branch main", "altro": "via",
    "filoni": [
        {"nome": "Capitolo tre", "voci": [
            {"n": 1, "id": None, "testo": "Rileggere il capitolo", "marca": "Tocca a te"},
            {"n": 2, "id": "#5", "testo": "Mandare la bozza all'editor", "marca": "Faccio io", "sotto": "dal 19/11"},
        ]},
        {"nome": "Copertina", "voci": [{"n": 3, "id": 7, "testo": "Scegliere la proposta", "marca": "Decidi tu"}]},
    ],
    "partenza": {"n": 2, "motivo": "sblocca la rilettura"},
}


class Banco:
    def __init__(self, repo: Path) -> None:
        self.repo = repo
        self.home = Path(tempfile.mkdtemp(prefix="arturo-ripartenza."))
        self.claude = self.home / ".claude"
        self.claude.mkdir()
        (self.home / ".config" / "herdr-app").mkdir(parents=True)

    def lancia(self, dati, *argomenti: str, sid: str = SID, **env_extra: str) -> subprocess.CompletedProcess:
        env = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home), PYTHONDONTWRITEBYTECODE="1")
        for chiave in ("CLAUDE_CODE_SESSION_ID", "ARTURO_RIPARTENZA", "CLAUDE_CONFIG_DIR", "ARTURO_TELEMETRIA"):
            env.pop(chiave, None)
        if sid:
            env["CLAUDE_CODE_SESSION_ID"] = sid
        env.update(env_extra)
        testo = dati if isinstance(dati, str) else json.dumps(dati)
        comando = [sys.executable, str(self.repo / "bin" / "arturo"), "ripartenza", *(argomenti or ("scrivi",))]
        return subprocess.run(comando, env=env, input=testo, capture_output=True, text=True, timeout=60)

    def file(self, sid: str = SID, radice: Path = None) -> Path:
        return (radice or self.claude) / "cache" / "ripartenza" / f"{sid}.json"

    def chiudi(self) -> None:
        shutil.rmtree(self.home, ignore_errors=True)


def test_rp01(b: Banco) -> None:
    r = b.lancia(BUONO)
    assert r.returncode == 0 and b.file().exists(), f"RP01 exit {r.returncode}, file assente: {r.stderr.strip()}"
    d = json.loads(b.file().read_text(encoding="utf-8"))
    voci = [v for f in d["filoni"] for v in f["voci"]]
    assert d.get("versione") == 1 and d.get("sid") == SID and "altro" not in d, f"RP01 testata sbagliata: {sorted(d)}"
    assert [v["n"] for v in voci] == [1, 2, 3] and [v["id"] for v in voci] == [None, 5, 7], f"RP01 numeri: {voci}"
    assert voci[1]["sotto"] == "dal 19/11" and d.get("partenza") == {"n": 2, "motivo": "sblocca la rilettura"}, \
        f"RP01 sotto o partenza: {d.get('partenza')}"
    assert isinstance(d.get("quando"), (int, float)) and "3 voci" in r.stdout, f"RP01 uscita: {r.stdout!r}"


def test_rp02(b: Banco) -> None:
    molte = {"filoni": [{"nome": "x", "voci": [{"n": i, "testo": "t" * 500} for i in range(1, 321)]}]}
    r = b.lancia(molte)
    assert r.returncode == 0, f"RP02 exit {r.returncode}: {r.stderr.strip()}"
    voci = json.loads(b.file().read_text(encoding="utf-8"))["filoni"][0]["voci"]
    assert len(voci) == 300, f"RP02 tetto voci: {len(voci)}"
    assert len(voci[0]["testo"]) == 300, f"RP02 tetto testo: {len(voci[0]['testo'])}"
    assert "20 voci oltre il tetto" in r.stdout, f"RP02 voci tagliate non dette: {r.stdout.strip()[-200:]}"


def test_rp03(b: Banco) -> None:
    rotti = (({"filoni": []}, "filoni"),
             ({"filoni": [{"voci": [{"n": 1, "testo": "  "}]}]}, "testo"),
             ({"filoni": [{"voci": [{"n": 1, "testo": "a"}, {"n": 1, "testo": "b"}]}]}, "numero doppio"),
             ("non json", "json"))
    for dati, cosa in rotti:
        r = b.lancia(dati)
        assert r.returncode == 2 and "schema rotto" in r.stderr, f"RP03 {cosa} accettato: exit {r.returncode}"
        assert not b.file().exists(), f"RP03 {cosa}: file scritto con uno schema rotto"


def test_rp04(b: Banco) -> None:
    r = b.lancia(BUONO, sid="")
    cartella = b.claude / "cache" / "ripartenza"
    assert r.returncode == 0 and not (cartella.exists() and any(cartella.iterdir())), \
        f"RP04 senza sessione ha scritto: exit {r.returncode}"
    r = b.lancia(BUONO, ARTURO_RIPARTENZA="0")
    assert r.returncode == 0 and not b.file().exists(), "RP04 ARTURO_RIPARTENZA=0 non spegne"
    r = b.lancia(BUONO, "leggi")
    assert r.returncode == 2 and not b.file().exists(), f"RP04 sottocomando sbagliato: exit {r.returncode}"


def test_rp05(b: Banco) -> None:
    vecchia, recente = b.file("a" * 12), b.file("b" * 12)
    vecchia.parent.mkdir(parents=True)
    for f in (vecchia, recente):
        f.write_text("{}", encoding="utf-8")
    tre_giorni_fa = time.time() - 3 * 86400
    os.utime(str(vecchia), (tre_giorni_fa, tre_giorni_fa))
    r = b.lancia(BUONO)
    assert r.returncode == 0, f"RP05 exit {r.returncode}"
    assert not vecchia.exists(), "RP05 la ripartenza vecchia di tre giorni è rimasta"
    assert recente.exists() and b.file().exists(), "RP05 cancellata una ripartenza recente"


def test_rp06(b: Banco) -> None:
    altrove = b.home / "config-altrove"
    r = b.lancia(BUONO, CLAUDE_CONFIG_DIR=str(altrove))
    assert r.returncode == 0 and b.file(radice=altrove).exists() and not b.file().exists(), \
        "RP06 la cartella non segue CLAUDE_CONFIG_DIR"


def test_rp07(b: Banco) -> None:
    testo = (b.repo / "commands" / "inizio.md").read_text(encoding="utf-8")
    m = re.search(r"python3 ~/\.claude/bin/arturo ripartenza scrivi <<'RIPARTENZA'\n(.*?)\n\s*RIPARTENZA\n", testo, re.S)
    assert m, "RP07 /inizio non lancia il comando arturo ripartenza scrivi"
    r = b.lancia(m.group(1))
    assert r.returncode == 0 and b.file().exists(), f"RP07 il modello di /inizio non passa lo schema: {r.stderr.strip()}"
    # Dal 27/11/2026 la FASE 6 di /inizio sta in shared/inizio-risposta.md (segnalazione 109).
    fase6 = testo.split("## FASE 6", 1)[-1] + ((b.repo / "shared" / "inizio-risposta.md").read_text(encoding="utf-8") if (b.repo / "shared" / "inizio-risposta.md").exists() else "")
    for parola, gesto in (("Già fatto", "todo fatto"), ("Scartati", "todo scarta"), ("Rimandati", '--quando "più avanti"'),
                          ("A\n  Claude", "--chi io"), ("A me", "--chi tu")):
        assert parola in fase6 and gesto in fase6, f"RP07 la FASE 6 non dice come leggere {parola!r}"


def test_rp08(b: Banco) -> None:
    shutil.rmtree(b.home / ".config" / "herdr-app")
    r = b.lancia(BUONO)
    cartella = b.claude / "cache" / "ripartenza"
    assert r.returncode == 0 and not (cartella.exists() and any(cartella.iterdir())), \
        f"RP08 senza Volta ha scritto la checklist: exit {r.returncode}"
    testo = (b.repo / "commands" / "inizio.md").read_text(encoding="utf-8")
    assert "[solo se la FASE 1 stampa `VOLTA`]" in testo, "RP08 /inizio passa la checklist anche senza Volta"
    contesto = (b.repo / "bin" / "contesto.py").read_text(encoding="utf-8")
    assert '"VOLTA: ' in contesto, "RP08 il contesto non stampa la riga VOLTA"


CASI = (("RP01", test_rp01), ("RP02", test_rp02), ("RP03", test_rp03), ("RP04", test_rp04),
        ("RP05", test_rp05), ("RP06", test_rp06), ("RP07", test_rp07), ("RP08", test_rp08))

VELENI = (
    ("RP01", [("bin/ripartenza.py", '    if isinstance(v, str) and v.lstrip("#").isdigit():\n'
               '        return int(v.lstrip("#"))\n', "")], "exit"),
    ("RP02", [("bin/ripartenza.py", "if contate >= VOCI:", "if False:")], "tetto voci"),
    ("RP03", [("bin/ripartenza.py", "if n in visti:", "if False:")], "numero doppio"),
    ("RP04", [("bin/ripartenza.py", "if not SID.match(sid):", "if False:")], "senza sessione"),
    ("RP05", [("bin/ripartenza.py", "if adesso - f.stat().st_mtime > VECCHIA:", "if False:")], "vecchia"),
    ("RP06", [("bin/ripartenza.py", 'return radice_orsa() / "cache" / "ripartenza"',
               'return Path.home() / ".claude" / "cache" / "ripartenza"')], "CLAUDE_CONFIG_DIR"),
    ("RP07", [("commands/inizio.md", "python3 ~/.claude/bin/arturo ripartenza scrivi <<'RIPARTENZA'",
               "python3 ~/.claude/scripts/ripartenza-scrivi.py <<'RIPARTENZA'")], "non lancia"),
    ("RP08", [("bin/ripartenza.py", "    if not volta_presente():\n", "    if False:\n")], "senza Volta"),
)


def avvelena(repo: Path) -> int:
    assert len(VELENI) == len(CASI), f"veleni {len(VELENI)} per {len(CASI)} controlli"
    casi = dict(CASI)
    inerti = []
    for codice, modifiche, motivo in VELENI:
        copia = Path(tempfile.mkdtemp(prefix="arturo-veleno-ripartenza."))
        b = None
        try:
            for cartella in ("bin", "hooks", "commands"):
                shutil.copytree(repo / cartella, copia / cartella)
            for file, vecchio, nuovo in modifiche:
                bersaglio = copia / file
                testo = bersaglio.read_text(encoding="utf-8").replace("\r\n", "\n")
                assert testo.count(vecchio) == 1, f"veleno {codice}: il punto da rompere non c'è più in {file}"
                bersaglio.write_bytes(testo.replace(vecchio, nuovo).encode("utf-8"))
            b = Banco(copia)
            try:
                casi[codice](b)
                inerti.append(f"{codice}: verde con il veleno")
            except AssertionError as e:
                if not (str(e).startswith(codice) and motivo in str(e)):
                    inerti.append(f"{codice}: rosso col motivo sbagliato: {e}")
                else:
                    print(f"VELENO {codice} ROSSO: {str(e)[:120]}")
        finally:
            if b is not None:
                b.chiudi()
            shutil.rmtree(copia, ignore_errors=True)
    assert not inerti, "veleni che non attaccano:\n" + "\n".join(inerti)
    print(f"VELENI_ROSSI={','.join(v[0] for v in VELENI)} veleni={len(VELENI)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    parser.add_argument("--avvelena", action="store_true")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.avvelena:
        return avvelena(repo)
    errori = []
    for codice, caso in CASI:
        b = Banco(repo)
        try:
            caso(b)
        except AssertionError as e:
            errori.append(str(e))
        finally:
            b.chiudi()
    if args.baseline_ref:
        # la controprova: sulla base senza il comando ogni caso deve essere rosso
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
    raise SystemExit(main())
