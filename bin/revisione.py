#!/usr/bin/env python3
"""revisione: il motore di /revisione, cioè la revisione di come la persona usa Arturo (17/11/2026).

  python3 ~/.claude/bin/revisione.py estrai [--giorni 30] [--projects DIR] -o CARTELLA
        legge i transcript di Claude Code di questo computer e scrive in CARTELLA l'estratto
        (estratto-1.md, estratto-2.md, ...) e la sintesi (sintesi.md)
  python3 ~/.claude/bin/revisione.py sintesi CARTELLA      stampa la sintesi
  python3 ~/.claude/bin/revisione.py igiene                una riga per ogni controllo che Arturo ha già
  python3 ~/.claude/bin/revisione.py registro              l'ultima revisione: proposte ed esiti
  python3 ~/.claude/bin/revisione.py bozza --da PROPOSTE.json --scelte 1,3 -o BOZZA.md
        la bozza della segnalazione con le sole proposte scelte, nella forma di /segnala
  python3 ~/.claude/bin/revisione.py salva --da PROPOSTE.json [--scelte 1,3] [--esito N=testo]...
        scrive il registro di oggi in ~/.claude/data/revisione/AAAA-MM-GG.md

Lo script estrae e conta. Il giudizio su cosa diventa una proposta lo dà il modello che legge l'estratto
(skills/revisione/SKILL.md). Le promesse di docs/privacy.md ("La revisione") stanno nel codice:
- nessun modello e nessuna rete: lo script non importa socket, urllib o la telemetria;
- dell'uscita dei comandi non si copia niente: dai tool_result restano solo i segnali di attrito
  che Claude Code scrive alla lettera (rifiuto, blocco del classificatore) e il conteggio degli errori;
- l'estratto sta in una cartella temporanea che sceglie chi lancia; il registro sta in
  ~/.claude/data/revisione/ con un .gitignore che lo tiene fuori da ogni repository;
- verso chi mantiene Arturo parte solo la bozza, e solo con /segnala dopo il sì sull'anteprima.

Nasce da ~/.claude/scripts/settimana-transcript.py della config di chi mantiene Arturo, generalizzato.
Banco: tests/test_revisione_2026_11_17.py.
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.append(str(Path(os.path.realpath(__file__)).parent.parent / "hooks"))
sys.path.insert(0, str(Path(os.path.realpath(__file__)).parent))
from radici import radice_arturo, radice_orsa  # noqa: E402
import prova  # noqa: E402

TAGLIO = 500        # caratteri per prompt: basta a capire la richiesta
CORTO = 40          # sotto questa lunghezza un prompt porta la coda del messaggio di Claude prima
CODA = 200          # caratteri di quella coda
PARTE = 120_000     # caratteri per file di estratto: il modello li legge uno alla volta
PROPOSTE_MASSIMO = 20  # il report della persona ne mostra 7 (SKILL.md); il modo di chi mantiene Arturo anche di più
CHI = {"tu": "io, nella mia config", "arturo": "chi mantiene Arturo"}
BOZZA_MASSIMO = 3900  # come VOCE_MASSIMO di bin/segnala.py: oltre, il server taglia
# Testo che Claude Code mette nel turno della persona senza che lei l'abbia scritto (prova del 17/11/2026 su 304
# sessioni: il corpo delle skill caricate, i messaggi fra sessioni con l'id nel tag, le note sulle immagini).
RUMORE = ("<task-notification>", "<cross-session-message>", "<local-command-stdout>",
          "<local-command-caveat>", "<system-reminder", "Caveat: The messages below",
          "<bash-stdout>", "<bash-stderr>", "This session is being continued from a previous conversation",
          "Base directory for this skill:", "Another Claude session sent a message")
IMMAGINE = re.compile(r"\[Image[^\]]*\]\s*")
A_META = re.compile(r"\s*The user sent a new message while you were working:\s*(.*?)\s*"
                    r"(?:This is how Claude Code surfaces messages.*)?$", re.S)
CMD = re.compile(r"<command-name>/?([A-Za-z0-9:_./-]+)</command-name>")
ARGS = re.compile(r"<command-args>(.*?)</command-args>", re.S)
BASH = re.compile(r"<bash-input>(.*?)</bash-input>", re.S)
INCOLLATO = re.compile(r"<pasted_content[^>]*>.*?</pasted_content[^>]*>", re.S)
NEGATO = "Permission for this action was denied by the Claude Code auto mode classifier"
SENZA_VERDETTO = "auto mode classifier gave no verdict"
RIFIUTO = "The user doesn't want to proceed with this tool use"
SALTATI = ("clear", "compact", "model", "exit", "resume")
# Le sessioni di prova (#5877) restano fuori dall'estratto: il marcatore è il nome `prova-` (bin/prova.py).
# Quelle nate prima del marcatore si riconoscono dal primo prompt, se la sessione ha al più PROVA_PROMPT prompt.
PROVA_VECCHIA = re.compile(r"^\s*(rispondi solo\b|sonda usa e getta|prova\b.{0,80}?\b(usa e getta|rispondi solo)\b)",
                           re.I | re.S)
PROVA_PROMPT = 3
# Chi ha causato l'attrito: la persona (ha fermato o detto no) o Claude (un comando fallito). /insights
# di Claude Code li mescola e attribuisce alla persona gli errori di Claude: qui restano separati.
DELLA_PERSONA = ("interrotto", "rifiuto")
# "Senza verdetto" ha due cause con lo stesso inizio di messaggio. Un hook che cambia il comando dopo la
# revisione ("a hook changed", "changed by a hook") è un difetto della config. Il classificatore giù
# ("no verdict (error)", "the response ended before its verdict arrived") è un guasto passeggero del server:
# il 16/11/2026 alle 08:33-08:43 ha fermato insieme due macchine (#5873), e Arturo non lo corregge.
DEL_SISTEMA = ("classificatore", "senza-verdetto", "classificatore-giu")
ETICHETTE = {"prompt": "", "comando": "", "bang": "[!] ", "mod": "[mod] ", "mod-comando": "[mod] ",
             "interrotto": "[interrotto con Esc]", "rifiuto": "[rifiutato] ",
             "classificatore": "[bloccato dal classificatore] ",
             "senza-verdetto": "[senza verdetto, hook dopo la revisione] ",
             "classificatore-giu": "[classificatore giù, guasto del server] "}


def ora_locale(ts: str) -> str:
    try:
        return dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone().strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return ts[:16].replace("T", " ")


def testo_di(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parti = [p.get("text", "") for p in content if isinstance(p, dict) and p.get("type") == "text"]
        return "\n".join(parti) if parti else None
    return None


def corto(s: str, taglio: int = TAGLIO) -> str:
    s = INCOLLATO.sub("[testo incollato]", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= taglio else s[:taglio] + " […]"


def attriti(content) -> tuple:
    """Dai tool_result in errore: i segnali scritti alla lettera da Claude Code, e quanti errori di
    comando (gli id dei tool) restano. Dell'uscita del comando non si tiene niente."""
    segnali, errori = [], []
    if not isinstance(content, list):
        return segnali, errori
    for p in content:
        if not isinstance(p, dict) or p.get("type") != "tool_result" or not p.get("is_error"):
            continue
        c = p.get("content")
        s = (c if isinstance(c, str) else json.dumps(c, ensure_ascii=False)).lstrip()
        if s.startswith(RIFIUTO):
            m = re.search(r"the user said:\s*(.{0,300})", s, re.S)
            segnali.append((p.get("tool_use_id"), "rifiuto", (m.group(1).strip() if m else "")[:300]))
        elif s.startswith(NEGATO):
            m = re.match(r"Reason:\s*(.{0,160}?)(?:\. If you have|\n|$)", s[len(NEGATO):].lstrip(". "), re.S)
            segnali.append((p.get("tool_use_id"), "classificatore", m.group(1).strip() if m else ""))
        elif SENZA_VERDETTO in s[:120]:
            tipo = "senza-verdetto" if "hook" in s[:240] else "classificatore-giu"
            segnali.append((p.get("tool_use_id"), tipo, ""))
        else:
            errori.append(p.get("tool_use_id"))
    return segnali, errori


def leggi_sessione(f: str, da: str) -> dict:
    eventi, skill, errori_tool = [], Counter(), Counter()
    cwd = inizio = ultimo_claude = nome = ""
    ultimo_tool = {}
    with open(f, encoding="utf-8", errors="replace") as righe:
        for line in righe:
            if '"custom-title"' in line or '"agent-name"' in line:
                try:
                    nome = prova.nome_da_record(json.loads(line)) or nome
                except ValueError:
                    pass
                continue
            if '"user"' not in line and '"assistant"' not in line:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            # Solo i turni: un record api-request-blob ha dentro il testo di Claude con role assistant.
            if not isinstance(r, dict) or r.get("type") not in ("user", "assistant") or r.get("isSidechain"):
                continue
            ts = r.get("timestamp", "")
            if ts and ts < da:
                continue
            msg = r.get("message") or {}
            if not isinstance(msg, dict):
                continue
            if r.get("type") == "assistant":
                for p in msg.get("content") or []:
                    if not isinstance(p, dict):
                        continue
                    if p.get("type") == "text" and p.get("text", "").strip():
                        ultimo_claude = p["text"]
                    elif p.get("type") == "tool_use":
                        nome = p.get("name", "")
                        ultimo_tool[p.get("id")] = nome
                        if nome == "Skill":
                            skill[(p.get("input") or {}).get("skill", "?")] += 1
                continue
            cwd = cwd or r.get("cwd", "")
            inizio = inizio or ts
            content = msg.get("content")
            segnali, errori = attriti(content)
            for tid, tipo, detto in segnali:
                eventi.append((ts, tipo, f"{ultimo_tool.get(tid, '')} · {detto}".strip(" ·")))
            for tid in errori:
                errori_tool[ultimo_tool.get(tid) or "?"] += 1
            if r.get("isMeta") or r.get("isCompactSummary") or r.get("entrypoint", "cli") != "cli":
                continue
            t = testo_di(content)
            if not t:
                continue
            meta = A_META.match(t)
            if meta:
                t = meta.group(1)  # un messaggio scritto a metà turno: conta il testo della persona
            t = IMMAGINE.sub("", t)
            if not t.strip():
                continue
            if "[Request interrupted by user" in t:
                eventi.append((ts, "interrotto", ""))
                continue
            mod = (r.get("origin") or {}).get("kind") == "plugin"
            c = CMD.search(t)
            if c:
                if c.group(1) in SALTATI:
                    continue
                a = ARGS.search(t)
                arg = corto(a.group(1)) if a and a.group(1).strip() else ""
                eventi.append((ts, "mod-comando" if mod else "comando", f"/{c.group(1)} {arg}".strip()))
                continue
            b = BASH.search(t)
            if b:
                eventi.append((ts, "bang", corto(b.group(1), 200)))
                continue
            if any(t.lstrip().startswith(x) for x in RUMORE):
                continue
            testo = corto(t)
            if len(testo) < CORTO and ultimo_claude:
                testo += f'  ⟵ dopo Claude: "…{corto(ultimo_claude, 10**6)[-CODA:]}"'
            eventi.append((ts, "mod" if mod else "prompt", testo))
    return {"id": os.path.basename(f)[:-6], "cwd": cwd, "inizio": inizio, "eventi": eventi,
            "skill": skill, "errori": errori_tool, "prova": di_prova(nome, eventi)}


def di_prova(nome: str, eventi: list) -> bool:
    if prova.e_prova(nome):
        return True
    scritti = [e[2] for e in eventi if e[1] == "prompt"]
    return 0 < len(scritti) <= PROVA_PROMPT and bool(PROVA_VECCHIA.match(scritti[0]))


def skill_dei_subagent(f: str, da: str, conta: dict) -> None:
    parti = f.replace("\\", "/").split("/")
    madre = parti[-3] if len(parti) >= 3 else ""
    with open(f, encoding="utf-8", errors="replace") as righe:
        for line in righe:
            if '"name":"Skill"' not in line:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if not isinstance(r, dict) or r.get("timestamp", "") < da:
                continue
            for p in (r.get("message") or {}).get("content") or []:
                if isinstance(p, dict) and p.get("type") == "tool_use" and p.get("name") == "Skill":
                    conta[madre][(p.get("input") or {}).get("skill", "?")] += 1


def chiave_prompt(testo: str) -> str:
    """Due prompt quasi uguali hanno la stessa chiave: minuscole, senza numeri né punteggiatura."""
    t = re.sub(r"⟵ dopo Claude:.*", "", testo.lower())
    t = re.sub(r"[^a-zàèéìòù ]+", " ", t)
    parole = [p for p in t.split() if len(p) > 2]
    return " ".join(parole[:8])


def sessioni_di(projects: Path, giorni: int, saltate: Counter | None = None) -> list:
    """Le sessioni con almeno un prompt, senza quelle di prova: saltate["prova"] le conta."""
    saltate = Counter() if saltate is None else saltate
    lim = time.time() - giorni * 86400
    da = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(lim))
    sessioni, da_sub = [], defaultdict(Counter)
    for f in glob.glob(os.path.join(str(projects), "**", "*.jsonl"), recursive=True):
        try:
            if os.path.getmtime(f) < lim:
                continue
        except OSError:
            continue
        if "subagents" in f.replace("\\", "/").split("/"):
            skill_dei_subagent(f, da, da_sub)
            continue
        if os.path.basename(f).startswith("agent-"):
            continue
        s = leggi_sessione(f, da)
        if s["prova"]:
            saltate["prova"] += 1
        elif any(e[1] in ("prompt", "comando", "bang") for e in s["eventi"]):
            sessioni.append(s)
    sessioni.sort(key=lambda s: s["inizio"])
    for s in sessioni:
        s["sub"] = da_sub.get(s["id"], Counter())
    return sessioni


def sintesi_di(sessioni: list, giorni: int) -> str:
    tot, sk_tot, sk_sess, comandi, err = Counter(), Counter(), Counter(), Counter(), Counter()
    ripetuti = defaultdict(set)
    esempi = {}
    for i, s in enumerate(sessioni, 1):
        for _, tipo, testo in s["eventi"]:
            tot[tipo] += 1
            if tipo == "comando":
                comandi[testo.split()[0]] += 1
            elif tipo == "prompt":
                k = chiave_prompt(testo)
                if len(k.split()) >= 3:
                    ripetuti[k].add(i)
                    esempi.setdefault(k, testo[:120])
        for k, n in s["skill"].items():
            sk_tot[k] += n
            sk_sess[k] += 1
        err.update(s["errori"])
    persona = sum(tot[t] for t in DELLA_PERSONA)
    sistema = sum(tot[t] for t in DEL_SISTEMA)
    righe = [
        f"# Sintesi della revisione · ultimi {giorni} giorni · {len(sessioni)} sessioni",
        f"prompt scritti: {tot['prompt']} · comandi: {tot['comando']} · comandi col !: {tot['bang']}"
        f" · dai mod: {tot['mod'] + tot['mod-comando']}",
        f"attriti della persona: {persona} (interruzioni con Esc {tot['interrotto']}, rifiuti {tot['rifiuto']})",
        f"blocchi del sistema: {sistema} (classificatore {tot['classificatore']}, senza verdetto per un hook "
        f"{tot['senza-verdetto']}, classificatore giù {tot['classificatore-giu']})",
        f"errori di Claude (comandi falliti): {sum(err.values())}"
        + (" · per strumento: " + ", ".join(f"{k} {n}" for k, n in err.most_common(6)) if err else ""),
        "comandi più usati: " + (", ".join(f"{k} {n}" for k, n in comandi.most_common(10)) or "nessuno"),
        "skill caricate (sessioni/caricamenti): " + (", ".join(
            f"{k} {sk_sess[k]}/{n}" for k, n in sk_tot.most_common(10)) or "nessuna"),
    ]
    rip = sorted(((len(v), k) for k, v in ripetuti.items() if len(v) >= 2), reverse=True)[:8]
    righe.append("prompt quasi uguali in più sessioni:" + ("" if rip else " nessuno"))
    for n, k in rip:
        sess = ", ".join(f"S{x}" for x in sorted(ripetuti[k])[:6])
        righe.append(f"- {n} sessioni ({sess}): \"{esempi[k]}\"")
    return "\n".join(righe) + "\n"


def blocchi(sessioni: list) -> list:
    casa = str(Path.home())
    out = []
    for i, s in enumerate(sessioni, 1):
        progetto = s["cwd"].replace(casa, "~") if s["cwd"] else "?"
        righe = [f"## S{i} · {ora_locale(s['inizio'])} · {progetto} · {s['id'][:8]}"]
        if s["skill"]:
            righe.append("skill: " + ", ".join(f"{k}×{n}" for k, n in s["skill"].most_common()))
        if s["sub"]:
            righe.append("skill dai subagent: " + ", ".join(f"{k}×{n}" for k, n in s["sub"].most_common()))
        if s["errori"]:
            righe.append("comandi falliti: " + ", ".join(f"{k}×{n}" for k, n in s["errori"].most_common()))
        for ts, tipo, testo in s["eventi"]:
            righe.append(f"- {ora_locale(ts)[11:]} {ETICHETTE[tipo]}{testo}".rstrip())
        out.append("\n".join(righe) + "\n")
    return out


def estrai(a) -> int:
    projects = Path(a.projects) if a.projects else radice_orsa() / "projects"
    if not projects.is_dir():
        print(f"Nessun transcript in {projects}: Claude Code non ha ancora sessioni su questo computer.")
        return 1
    saltate = Counter()
    sessioni = sessioni_di(projects, a.giorni, saltate)
    uscita = Path(a.output)
    uscita.mkdir(parents=True, exist_ok=True)
    for vecchio in uscita.glob("estratto-*.md"):
        vecchio.unlink()
    sintesi = sintesi_di(sessioni, a.giorni)
    (uscita / "sintesi.md").write_text(sintesi, encoding="utf-8")
    parti, corrente = [], ""
    for b in blocchi(sessioni):
        if corrente and len(corrente) + len(b) > PARTE:
            parti.append(corrente)
            corrente = ""
        corrente += b + "\n"
    if corrente:
        parti.append(corrente)
    for n, testo in enumerate(parti, 1):
        (uscita / f"estratto-{n}.md").write_text(testo, encoding="utf-8")
    print(f"{len(sessioni)} sessioni in {len(parti)} file di estratto: {uscita}/sintesi.md, "
          + ", ".join(f"estratto-{n}.md" for n in range(1, len(parti) + 1))
          + f" · {saltate['prova']} sessioni di prova saltate")
    return 0


def _riga(comando: list, timeout: int = 120) -> tuple:
    try:
        p = subprocess.run(comando, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).strip()
    except (OSError, subprocess.TimeoutExpired) as e:
        return 99, f"non partito: {e}"


def igiene(_a) -> int:
    """I controlli che Arturo ha già, una riga ciascuno: la revisione non li rifà."""
    codice, orsa = radice_arturo(), radice_orsa()
    py = sys.executable
    rc, out = _riga([py, str(codice / "bin" / "personale.py"), "omonimi"])
    omonimi = [r for r in out.splitlines() if r.startswith(("OMONIMO", "DICHIARATO SENZA"))]
    print(f"omonimi: {len(omonimi)} da guardare" + (" · " + " | ".join(r[:120] for r in omonimi[:3]) if omonimi else ""))
    rc, out = _riga([py, str(codice / "bin" / "memoria.py"), "igiene", "--prova", "--json"])
    try:
        m = json.loads(out)
        print("memoria: " + ", ".join(f"{k} {len(v) if isinstance(v, list) else v}" for k, v in m.items()
                                       if isinstance(v, (list, int)) and not isinstance(v, bool))[:300])
    except ValueError:
        print(f"memoria: {out.splitlines()[-1][:200] if out else 'nessuna uscita'}")
    audit = codice / "skills" / "system-audit" / "audit.sh"
    if audit.exists():
        rc, out = _riga(["bash", str(audit)], timeout=180)
        problemi = [r for r in out.splitlines() if r.startswith(("FAIL", "WARN"))]
        print(f"system-audit: {sum(r.startswith('FAIL') for r in problemi)} FAIL, "
              f"{sum(r.startswith('WARN') for r in problemi)} WARN"
              + (" · " + " | ".join(r[:120] for r in problemi[:4]) if problemi else ""))
    try:
        sys.path.insert(0, str(codice / "bin"))
        import todo_store as ts
        todo, _ = ts.carica()
        aperti = [t for t in todo.values() if ts.gruppo(t)]
        fermi = [t for t in aperti if t["stato"] == "fermo"]
        scaduti = [t for t in aperti if (ts.giorni(t) or 0) < 0]
        print(f"todo: {len(aperti)} aperti, {len(fermi)} fermi, {len(scaduti)} scaduti")
    except Exception as e:  # noqa: BLE001 - un registro dei todo rotto non ferma la revisione
        print(f"todo: non letti ({type(e).__name__})")
    md = orsa / "CLAUDE.md"
    if md.exists():
        righe = md.read_text(encoding="utf-8", errors="replace").count("\n")
        print(f"CLAUDE.md: {righe} righe, {md.stat().st_size // 1024} KB")
    return 0


def cartella_registro() -> Path:
    c = radice_orsa() / "data" / "revisione"
    c.mkdir(parents=True, exist_ok=True)
    gi = c / ".gitignore"
    if not gi.exists():
        gi.write_text("# Il registro della revisione cita le parole della persona: resta fuori da ogni repository.\n*\n",
                      encoding="utf-8")
    return c


def registro(_a) -> int:
    c = radice_orsa() / "data" / "revisione"
    vecchi = sorted(c.glob("[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9].md")) if c.is_dir() else []
    if not vecchi:
        print("Prima revisione: nessun registro.")
        return 0
    testo = vecchi[-1].read_text(encoding="utf-8", errors="replace")
    print(f"Ultimo registro: {vecchi[-1].name}")
    rifiutate = [r for r in testo.splitlines() if r.strip().startswith("esito: rifiutata")]
    print(f"proposte rifiutate: {len(rifiutate)} (non si ripropongono senza un fatto nuovo)")
    print(testo)
    return 0


def proposte_da(file: str) -> list:
    dati = json.loads(Path(file).read_text(encoding="utf-8"))
    lista = dati.get("proposte") if isinstance(dati, dict) else dati
    if not isinstance(lista, list) or not lista:
        raise ValueError("il file non ha proposte")
    for n, p in enumerate(lista, 1):
        if not isinstance(p, dict) or not str(p.get("cosa") or "").strip():
            raise ValueError(f"la proposta {n} non dice cosa fare")
    return lista[:PROPOSTE_MASSIMO]


def scelte_di(testo: str, quante: int) -> list:
    if testo.strip().lower() in ("tutte", "tutto", "all"):
        return list(range(1, quante + 1))
    scelte = sorted({int(x) for x in re.findall(r"\d+", testo)})
    fuori = [x for x in scelte if not 1 <= x <= quante]
    if fuori:
        raise ValueError(f"proposte inesistenti: {fuori}")
    return scelte


def bozza(a) -> int:
    try:
        lista = proposte_da(a.da)
        scelte = scelte_di(a.scelte, len(lista))
    except (OSError, ValueError) as e:
        print(f"Errore: {e}", file=sys.stderr)
        return 2
    tue = [n for n in scelte if str(lista[n - 1].get("chi") or "").strip().lower() == "tu"]
    scelte = [n for n in scelte if n not in tue]
    if tue:
        print(f"restano a te, non partono: {', '.join(map(str, tue))}")
    if not scelte:
        print("Nessuna proposta per chi mantiene Arturo: niente da mandare.")
        return 1
    tolte = []
    while True:
        voci = [lista[n - 1] for n in scelte]
        sezioni = []
        for n, p in zip(scelte, voci):
            righe = [f"### {n}. {str(p['cosa']).strip()}"]
            for campo, nome in (("perche", "Perché"), ("prove", "Prove"), ("chi", "Chi agisce")):
                v = p.get(campo)
                if isinstance(v, list):
                    v = "; ".join(str(x) for x in v)
                if campo == "chi":
                    v = CHI.get(str(v or "").strip().lower(), v)
                if v:
                    righe.append(f"**{nome}**: {str(v).strip()}")
            sezioni.append("\n".join(righe))
        breve = (f"La revisione di Arturo sulle mie sessioni ha trovato {len(lista)} proposte: ne mando "
                 f"{len(voci)}, quelle che ho scelto.")
        testo = "### In breve\n" + breve + "\n\n" + "\n\n".join(sezioni) + "\n"
        if len(testo) <= BOZZA_MASSIMO or len(scelte) == 1:
            break
        tolte.append(scelte.pop())  # l'ultima scelta è la meno utile: il report le ordina così
    Path(a.output).write_text(testo, encoding="utf-8")
    print(f"bozza: {a.output} · proposte {', '.join(map(str, scelte))} · {len(testo)} caratteri")
    if tolte:
        print(f"tolte per lunghezza: {', '.join(map(str, tolte))} (oltre {BOZZA_MASSIMO} caratteri)")
    return 0


def salva(a) -> int:
    try:
        lista = proposte_da(a.da)
        scelte = scelte_di(a.scelte or "", len(lista))
    except (OSError, ValueError) as e:
        print(f"Errore: {e}", file=sys.stderr)
        return 2
    esiti = {}
    for e in a.esito or []:
        n, _, testo = e.partition("=")
        if n.strip().isdigit():
            esiti[int(n)] = testo.strip()
    oggi = dt.date.today().isoformat()
    righe = [f"# Revisione del {oggi}", ""]
    for n, p in enumerate(lista, 1):
        esito = esiti.get(n) or ("scelta" if n in scelte else "in attesa")
        prove = p.get("prove")
        if isinstance(prove, list):
            prove = "; ".join(str(x) for x in prove)
        righe += [f"{n}. {str(p['cosa']).strip()}", f"   prove: {str(prove or '').strip()[:400]}",
                  f"   esito: {esito}", ""]
    file = cartella_registro() / f"{oggi}.md"
    file.write_text("\n".join(righe), encoding="utf-8")
    print(f"registro: {file}")
    return 0


def main(argv: list) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(prog="arturo revisione", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    e = sub.add_parser("estrai")
    e.add_argument("--giorni", type=int, default=30)
    e.add_argument("--projects")
    e.add_argument("-o", "--output", required=True)
    s = sub.add_parser("sintesi")
    s.add_argument("cartella")
    sub.add_parser("igiene")
    sub.add_parser("registro")
    b = sub.add_parser("bozza")
    b.add_argument("--da", required=True)
    b.add_argument("--scelte", required=True)
    b.add_argument("-o", "--output", required=True)
    v = sub.add_parser("salva")
    v.add_argument("--da", required=True)
    v.add_argument("--scelte")
    v.add_argument("--esito", action="append")
    a = ap.parse_args(argv)
    if a.cmd == "estrai":
        return estrai(a)
    if a.cmd == "sintesi":
        f = Path(a.cartella) / "sintesi.md"
        if not f.exists():
            print(f"Manca {f}: lancia prima estrai.", file=sys.stderr)
            return 1
        sys.stdout.write(f.read_text(encoding="utf-8"))
        return 0
    if a.cmd in ("igiene", "registro", "bozza", "salva"):
        return {"igiene": igiene, "registro": registro, "bozza": bozza, "salva": salva}[a.cmd](a)
    print(__doc__)
    return 0 if not argv else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
