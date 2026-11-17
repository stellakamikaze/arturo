#!/usr/bin/env python3
"""RV01-RV09: /revisione, la revisione di come la persona usa Arturo (17/11/2026).

RV01 l'estratto tiene prompt, slash, Esc, rifiuti e blocchi del classificatore, segna [mod] i prompt dei mod, tiene
     il testo di un messaggio scritto a metà turno, e salta isMeta, sidechain, notifiche, i record api-request-blob,
     il corpo delle skill caricate, i messaggi fra sessioni e le note sulle immagini (prova del 17/11/2026);
RV02 dell'uscita dei comandi non copia niente, neanche da un comando fallito con un segreto finto;
RV03 la sintesi separa gli attriti della persona (Esc, rifiuti) dagli errori di Claude (comandi falliti);
RV04 la bozza porta solo le proposte scelte e lascia fuori quelle della persona ("chi": "tu"); prepara di
     /segnala toglie dall'anteprima l'email e il percorso della home;
RV05 prepara accetta --origine revisione e la scrive nel file pronto; il server la conosce;
RV06 il passo 0 della skill dice SVILUPPATORE solo se c'è ~/.claude/personale/revisione-sviluppatore.md;
RV07 salva scrive il registro con un .gitignore che lo tiene fuori dai repository, con tutte le proposte anche
     oltre le 7 del report della persona, e registro conta le rifiutate;
RV08 la skill ha name, description e when_to_use, i sottocomandi che cita esistono, la telemetria la conta;
RV09 un "senza verdetto" per un hook e un classificatore giù ("no verdict (error)") restano due segnali
     diversi: la raffica del 16/11/2026 era un guasto del server, non un hook (#5873);
RV10 le sessioni di prova restano fuori dall'estratto: quella col nome prova- (bin/prova.py, anche dopo un
     cambio di nome) e quella nata prima del marcatore, dal primo prompt; una vera che comincia con
     "Rispondi solo" e continua resta dentro, e estrai dice quante ne ha saltate (#5877).

Senza rete né Claude: transcript finti in una HOME di prova. Sulla base 8117411 (il dev prima) sono tutti rossi,
ognuno col suo codice. --avvelena: ogni veleno toglie la riga che il suo caso sorveglia.
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

CASI = ["RV01", "RV02", "RV03", "RV04", "RV05", "RV06", "RV07", "RV08", "RV09", "RV10"]
SEGRETO = "sk-prova-NONDEVEUSCIRE-4242"


def riga(**d) -> str:
    base = {"timestamp": "2099-01-01T10:00:00.000Z", "cwd": "/tmp/progetto-prova", "entrypoint": "cli"}
    base.update(d)
    return json.dumps(base, ensure_ascii=False)


def utente(testo, **kw):
    return riga(type="user", message={"role": "user", "content": testo}, **kw)


def assistente(contenuto, **kw):
    return riga(type="assistant", message={"role": "assistant", "content": contenuto}, **kw)


def risultato(tid, testo, errore):
    return riga(type="user", message={"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": tid, "content": testo, "is_error": errore}]})


def transcript() -> str:
    righe = [
        utente("prepara il preventivo per il cliente come la volta scorsa"),
        assistente([{"type": "text", "text": "Preparo il preventivo."},
                    {"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "ls"}}]),
        risultato("t1", f"file.txt token={SEGRETO}", False),
        assistente([{"type": "tool_use", "id": "t2", "name": "Bash", "input": {"command": "cat x"}}]),
        risultato("t2", f"cat: x: No such file {SEGRETO}", True),
        assistente([{"type": "tool_use", "id": "t3", "name": "Edit", "input": {"file_path": "/tmp/a"}}]),
        risultato("t3", "The user doesn't want to proceed with this tool use. The tool use was rejected. "
                        "To tell you how to proceed, the user said: usa il file giusto", True),
        assistente([{"type": "tool_use", "id": "t4", "name": "Bash", "input": {"command": "rm -rf x"}}]),
        risultato("t4", "Permission for this action was denied by the Claude Code auto mode classifier. "
                        "Reason: cancella file fuori dal progetto", True),
        utente([{"type": "text", "text": "[Request interrupted by user]"}]),
        utente("<command-message>fine</command-message>\n<command-name>/fine</command-name>\n<command-args>salva</command-args>"),
        utente("NOTA-META-NON-DEVE-USCIRE", isMeta=True),
        utente("PROMPT-SIDECHAIN-NON-DEVE-USCIRE", isSidechain=True),
        utente("<task-notification>NOTIFICA-NON-DEVE-USCIRE</task-notification>"),
        utente("prompt scritto dal mod di rotazione", origin={"kind": "plugin"}),
        # Prova del 17/11/2026 su 304 sessioni vere: testo che non è della persona, entrato come prompt.
        riga(type="api-request-blob", message={"role": "assistant", "content": [
            {"type": "text", "text": "BLOB-DI-CLAUDE-NON-DEVE-USCIRE"}]}),
        utente("Base directory for this skill: /x/skills/prova\n\nCORPO-SKILL-NON-DEVE-USCIRE"),
        utente('<system-reminder id="891e064b">\nAnother Claude session sent a message: SESSIONE-NON-DEVE-USCIRE\n</system-reminder>'),
        utente("The user sent a new message while you were working:\naggiungi anche il totale del mese\n\n"
               "This is how Claude Code surfaces messages the user sends mid-turn"),
        # #5873: le due cause del "senza verdetto", coi testi veri di Claude Code (transcript del 3/11 e del 16/11).
        assistente([{"type": "tool_use", "id": "t5", "name": "Bash", "input": {"command": "ls *.md"}}]),
        risultato("t5", "The server-side auto mode classifier gave no verdict for Bash: a hook changed this call's "
                        "input after auto mode reviewed it, so the review does not cover what would run.", True),
        assistente([{"type": "tool_use", "id": "t6", "name": "Bash", "input": {"command": "pwd"}}]),
        risultato("t6", "The server-side auto mode classifier gave no verdict (error), so auto mode cannot determine "
                        "the safety of Bash. This is a transient failure of the check, not a judgment about the action",
                  True),
        assistente([{"type": "tool_use", "id": "t7", "name": "Edit", "input": {"file_path": "/tmp/b"}}]),
        risultato("t7", "The server-side auto mode classifier gave no verdict (the response ended before its verdict "
                        "arrived), so auto mode cannot determine the safety of Edit.", True),
        utente([{"type": "text", "text": "[Image: original 3201x1800, displayed at 2576x1449.] guarda lo screenshot della pagina"}]),
    ]
    return "\n".join(righe) + "\n"


def sessioni_di_prova() -> dict:
    """#5877: una sessione col nome prova- (anche rinominata dopo), una di prova nata prima del marcatore, e una
    vera che comincia con "Rispondi solo" ma continua: le prime due fuori dall'estratto, la terza dentro."""
    return {
        "bbbbbbbb-2222.jsonl": [
            json.dumps({"type": "custom-title", "customTitle": "altro-nome", "sessionId": "bbbbbbbb-2222"}),
            utente("PROMPT-DI-PROVA-MARCATA: scrivi un paragrafo sul mare"),
            json.dumps({"type": "agent-name", "agentName": "prova-5877", "sessionId": "bbbbbbbb-2222"}),
        ],
        "cccccccc-3333.jsonl": [utente("Rispondi solo: PROVA-VECCHIA-NON-DEVE-USCIRE")],
        "dddddddd-4444.jsonl": [utente("Rispondi solo sì o no: il preventivo SESSIONE-VERA-RESTA è partito?"),
                                utente("allora mandalo"), utente("aggiungi il cliente in copia"),
                                utente("e salva la bozza")],
    }


def esegui(argv, env, cwd=None):
    try:
        p = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
                           env=env, cwd=cwd)
        return p.returncode, p.stdout + p.stderr
    except (OSError, subprocess.TimeoutExpired) as e:
        return 99, str(e)


def leggi(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace") if p.is_file() else ""


def prova(repo: Path, solo: str = "") -> list:
    rossi = []
    script = repo / "bin" / "revisione.py"
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        casa = tmp / "casa"
        orsa = casa / ".claude"
        (orsa / "projects" / "-tmp-progetto-prova").mkdir(parents=True)
        (orsa / "projects" / "-tmp-progetto-prova" / "aaaaaaaa-1111.jsonl").write_text(transcript(), encoding="utf-8")
        for nome, righe in sessioni_di_prova().items():
            (orsa / "projects" / "-tmp-progetto-prova" / nome).write_text("\n".join(righe) + "\n", encoding="utf-8")
        env = {**os.environ, "HOME": str(casa), "USERPROFILE": str(casa), "CLAUDE_CONFIG_DIR": str(orsa),
               "ARTURO_TELEMETRIA": "0", "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"}
        env.pop("ARTURO_RADICE", None)
        out = tmp / "estratto"
        rc, testo = esegui([sys.executable, str(script), "estrai", "--giorni", "36500", "-o", str(out)], env)
        estratto = "".join(leggi(f) for f in sorted(out.glob("estratto-*.md"))) if out.is_dir() else ""
        sintesi = leggi(out / "sintesi.md")

        if not solo or solo == "RV01":
            attesi = ("prepara il preventivo", "/fine salva", "[interrotto con Esc]", "[rifiutato]",
                      "usa il file giusto", "[bloccato dal classificatore]", "[mod] prompt scritto dal mod",
                      "aggiungi anche il totale del mese", "guarda lo screenshot della pagina")
            vietati = ("NOTA-META", "PROMPT-SIDECHAIN", "NOTIFICA-NON", "BLOB-DI-CLAUDE", "CORPO-SKILL", "SESSIONE-NON",
                       "This is how Claude Code", "[Image")
            mancano = [a for a in attesi if a not in estratto]
            entrati = [v for v in vietati if v in estratto]
            if rc != 0 or mancano or entrati:
                rossi.append(f"RV01 estratto: rc {rc}, mancano {mancano}, entrati {entrati} · {testo[-200:]!r}")
        if not solo or solo == "RV10":
            fuori = [v for v in ("PROMPT-DI-PROVA-MARCATA", "PROVA-VECCHIA-NON") if v in estratto]
            if rc != 0 or fuori or "SESSIONE-VERA-RESTA" not in estratto or "2 sessioni di prova saltate" not in testo:
                rossi.append(f"RV10 sessioni di prova: rc {rc}, entrate {fuori}, vera "
                             f"{'SESSIONE-VERA-RESTA' in estratto} · {testo[-160:]!r}")
        if not solo or solo == "RV02":
            if rc != 0 or not estratto or SEGRETO in estratto or SEGRETO in sintesi:
                rossi.append(f"RV02 uscita dei comandi copiata o estratto vuoto: rc {rc}, "
                             f"segreto {'dentro' if SEGRETO in estratto + sintesi else 'fuori'}")
        if not solo or solo == "RV03":
            ok = ("attriti della persona: 2" in sintesi and "errori di Claude (comandi falliti): 1" in sintesi
                  and "classificatore 1" in sintesi)
            if not ok:
                rossi.append(f"RV03 sintesi: {sintesi[:400]!r}")

        if not solo or solo == "RV09":
            ok = (estratto.count("[senza verdetto, hook dopo la revisione]") == 1
                  and estratto.count("[classificatore giù, guasto del server]") == 2
                  and "senza verdetto per un hook 1, classificatore giù 2" in sintesi
                  and "blocchi del sistema: 4" in sintesi)
            if not ok:
                rossi.append(f"RV09 hook e classificatore giù: {sintesi[:500]!r}")

        proposte = tmp / "proposte.json"
        proposte.write_text(json.dumps({"proposte": [
            {"cosa": "Far partire da sola la skill dei preventivi", "prove": ["S1: \"come la volta scorsa\""], "chi": "arturo"},
            {"cosa": "Togliere la nota doppia", "prove": ["igiene"], "chi": "tu"},
            {"cosa": f"Scrivere a mario.rossi@example.com da {casa}/lavoro", "prove": ["S1"], "chi": "arturo"},
            {"cosa": "Proposta non scelta", "prove": ["S1"], "chi": "arturo"}]
            # Il modo di chi mantiene Arturo ne ha anche 13 (prima revisione del 17/11/2026): il registro le tiene tutte.
            + [{"cosa": f"Proposta in più {k}", "prove": ["S1"], "chi": "arturo"} for k in range(5, 14)]}), encoding="utf-8")
        bozza = tmp / "bozza.md"
        if not solo or solo in ("RV04", "RV05"):
            rcb, tb = esegui([sys.executable, str(script), "bozza", "--da", str(proposte), "--scelte", "1 2 3",
                              "-o", str(bozza)], env)
            corpo = leggi(bozza)
            rcp, tp = esegui([sys.executable, str(repo / "bin" / "arturo"), "segnala", "prepara", "--tipo", "proposta",
                              "--titolo", "Revisione: prova", "--file", str(bozza), "--origine", "revisione",
                              "--pacchetto", "nessuna", "--senza-contatto"], env)
            pronta = Path(str(bozza) + ".pronta.json")
            dati = json.loads(leggi(pronta) or "{}")
            if not solo or solo == "RV04":
                ok = (rcb == 0 and "skill dei preventivi" in corpo and "nota doppia" not in corpo
                      and "non scelta" not in corpo and rcp == 0 and "[email]" in tp and "mario.rossi" not in tp
                      and str(casa) not in tp)
                if not ok:
                    rossi.append(f"RV04 bozza e anteprima: rc {rcb}/{rcp}, bozza {corpo[:300]!r}, anteprima {tp[-300:]!r}")
            if not solo or solo == "RV05":
                server = leggi(repo / "server" / "logica.js")
                m = re.search(r"export const ORIGINI = \[([^\]]*)\]", server)
                if dati.get("origine") != "revisione" or not m or '"revisione"' not in m.group(1):
                    rossi.append(f"RV05 origine revisione: pronta {dati.get('origine')!r}, server "
                                 f"{m.group(1) if m else 'senza ORIGINI'!r}, prepara {tp[-160:]!r}")

        skill = leggi(repo / "skills" / "revisione" / "SKILL.md")
        if not solo or solo == "RV06":
            m = re.search(r"## 0\..*?```bash\n(.*?)```", skill, re.S)
            esiti = []
            if m:
                for con in (False, True):
                    pers = orsa / "personale"
                    pers.mkdir(exist_ok=True)
                    f = pers / "revisione-sviluppatore.md"
                    if con:
                        f.write_text("prova\n", encoding="utf-8")
                    elif f.exists():
                        f.unlink()
                    esiti.append(esegui(["bash", "-c", m.group(1)], env)[1].strip())
            if esiti != ["PERSONA", "SVILUPPATORE"]:
                rossi.append(f"RV06 passo 0 della skill: {esiti!r}")
        if not solo or solo == "RV07":
            rcs, ts_ = esegui([sys.executable, str(script), "salva", "--da", str(proposte), "--scelte", "1",
                               "--esito", "3=rifiutata: non serve"], env)
            reg = orsa / "data" / "revisione"
            gi = leggi(reg / ".gitignore")
            rcr, tr = esegui([sys.executable, str(script), "registro"], env)
            ok = (rcs == 0 and gi.strip().endswith("*") and "proposte rifiutate: 1" in tr and "esito: scelta" in tr
                  and "esito: in attesa" in tr and tr.count("esito:") == 13)
            if not ok:
                rossi.append(f"RV07 registro: rc {rcs}/{rcr}, gitignore {gi!r}, {tr[:300]!r}")
        if not solo or solo == "RV08":
            front = skill.split("---")[1] if skill.startswith("---") else ""
            campi = all(re.search(rf"^{c}:", front, re.M) for c in ("description", "when_to_use"))
            nome = re.search(r"^name:\s*revisione\s*$", front, re.M)
            citati = set(re.findall(r"\$A revisione (\w+)", skill))
            sorgente = leggi(script)
            mancanti = [c for c in citati if f'add_parser("{c}")' not in sorgente]
            tele = re.search(r"SKILL = frozenset\(\{(.*?)\}\)", leggi(repo / "bin" / "telemetria.py"), re.S)
            if not (campi and nome and citati and not mancanti and tele and '"revisione"' in tele.group(1)):
                rossi.append(f"RV08 skill: frontmatter {bool(campi and nome)}, citati {sorted(citati)}, "
                             f"mancanti {mancanti}, telemetria {bool(tele and 'revisione' in tele.group(1))}")
    return rossi


# (caso, file, testo giusto, testo rotto)
VELENI = [
    ("RV01", "bin/revisione.py", 'or r.get("type") not in ("user", "assistant") or r.get("isSidechain"):',
     'or r.get("isSidechain"):'),
    ("RV01", "bin/revisione.py", '"Base directory for this skill:", ', ""),
    ("RV01", "bin/revisione.py", "                t = meta.group(1)", "                pass"),
    ("RV02", "bin/revisione.py", '            errori.append(p.get("tool_use_id"))',
     '            segnali.append((p.get("tool_use_id"), "rifiuto", s[:300]))'),
    ("RV03", "bin/revisione.py", 'DELLA_PERSONA = ("interrotto", "rifiuto")', 'DELLA_PERSONA = ("interrotto",)'),
    ("RV04", "bin/revisione.py", "    scelte = [n for n in scelte if n not in tue]", "    scelte = list(scelte)"),
    ("RV05", "bin/segnala.py", 'ORIGINI = ("segnala", "avvio", "fine", "revisione")', 'ORIGINI = ("segnala", "avvio", "fine")'),
    ("RV06", "skills/revisione/SKILL.md", "test -f ~/.claude/personale/revisione-sviluppatore.md",
     "test -f ~/.claude/personale/altro.md"),
    ("RV07", "bin/revisione.py", 'r.strip().startswith("esito: rifiutata")', 'r.strip().startswith("esito: no")'),
    ("RV08", "skills/revisione/SKILL.md", "name: revisione\n", "name: rev\n"),
    ("RV07", "bin/revisione.py", "PROPOSTE_MASSIMO = 20", "PROPOSTE_MASSIMO = 7"),
    ("RV09", "bin/revisione.py", 'tipo = "senza-verdetto" if "hook" in s[:240] else "classificatore-giu"',
     'tipo = "senza-verdetto"'),
    ("RV10", "bin/revisione.py", '            saltate["prova"] += 1\n        elif any(', "            pass\n        if any("),
    ("RV10", "bin/prova.py", 'MARCATO = re.compile(r"^\\s*prova-", re.I)', 'MARCATO = re.compile(r"^\\s*xprova-", re.I)'),
    ("RV10", "bin/revisione.py", "PROVA_PROMPT = 3", "PROVA_PROMPT = 9"),
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
            if not rossi or not rossi[0].startswith(caso):
                print(f"VELENO {caso} NON ATTACCA ({rel}): {rossi[:1]}")
                return 1
            print(f"VELENO {caso} ROSSO: {rossi[0][:120]}")
            esiti.append(caso)
    print(f"VELENI_ROSSI={','.join(esiti)} veleni={len(VELENI)}")
    return 0 if len(esiti) == len(VELENI) else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--baseline-ref")
    parser.add_argument("--avvelena", action="store_true")
    a = parser.parse_args()
    repo = Path(a.repo).resolve()
    if a.avvelena:
        return avvelena(repo)
    rossi = prova(repo)
    if a.baseline_ref:
        codici = sorted({r.split()[0] for r in rossi})
        assert codici == CASI, f"baseline non discriminante: rossi {codici}, attesi {CASI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    verdi = len([c for c in CASI if c not in {r.split()[0] for r in rossi}])
    print(f"revisione: {verdi}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
