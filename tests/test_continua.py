#!/usr/bin/env python3
"""CN01-CN09: hooks/continua.py, la sessione continua da sola quando il passo dopo è di Claude (24/11/2026).

Su Stop l'hook legge l'ultimo testo di Claude (hooks/fine_turno.py, comune con carta-sessione.py) e, se la
fine dice che il passo è di Claude e non chiede niente alla persona, risponde decision "block". Ogni caso
lancia l'hook vero in un processo, con una casa finta (HOME e CLAUDE_CONFIG_DIR).

CN01 il passo mio fa continuare: le forme di PASSO_MIO danno il block col motivo giusto, anche insieme a
     "Niente da fare per te"; il conto e il registro scrivono il giro. Un testo senza passo mio tace, e
     ARTURO_CONTINUA=0 spegne l'hook.
CN02 una domanda finale (chiede()) tace, anche col passo mio.
CN03 una parola di freno tace: invio, password, pagamento, 2FA, firma, sblocco, un comando `!`. Tace anche
     un passo mio rinviato: "appena è accesa", "quando finisce", "alla prossima apertura", "dal 25/11".
CN04 la rotazione tace: una riga "ruoto:", "dopo la rotazione", il tool ruota chiamato nel turno. Il tool
     ruota di un turno di prima non conta.
CN05 il tetto: 3 continuazioni di fila, la quarta tace e il registro dice tetto. stop_hook_active conta.
CN06 un messaggio della persona azzera il conto: `hub.py prompt` toglie il file, e l'hook riparte.
CN07 la trascrizione senza last_assistant_message: conta l'ultimo testo di Claude. Un ingresso rotto o
     senza sessione esce 0 in silenzio.
CN08 lo stato verso Herdr (#6594): dentro Herdr (HC_TERMINAL_ID) il turno che continua manda "working", ogni
     altro turno "done" (niente passo mio, hook spento, ingresso rotto, tetto). Fuori da Herdr e nel figlio di
     titolo-sessione.py non parte niente. Lo Stop di settings.json non ha più `herdr-stato.sh done`, che
     girava in parallelo e segnava fatto anche il turno che continua. L'hook gira su una copia di hooks/ con
     un herdr-stato.sh finto che scrive lo stato in un file.

CN09 la chiusura del turno (#6403): un passo di Claude passato alla persona (/clear e /inizio, la rotazione,
     un messaggio a un'altra sessione), il via chiesto per un lavoro di Claude ("scrivimi vai e parto"), un controllo
     promesso a un'ora ("domattina guardo io") danno un block col loro motivo. Tacciono col secondo Stop
     (stop_hook_active), con un freno o una spesa, col tool ruota nel turno, e il rinvio con un richiamo armato nel
     turno (Monitor, un Bash con run_in_background).

--avvelena rompe ogni regola su una copia di hooks/ ed esce 0 solo se ogni rottura fa rosso i suoi casi.
Il primo veleno è PASSO_MIO sempre vero e nessun filtro (decidi dà sempre "continua"): CN01-CN04 rossi.
Sulla base 067606f (il ramo di hub prima di continua.py) sono tutti rossi: l'hook non c'è.
Solo libreria standard. Nessun modello.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CASI = ["CN01", "CN02", "CN03", "CN04", "CN05", "CN06", "CN07", "CN08", "CN09"]
DISCRIMINANTI = list(CASI)
MOTIVO = ("Il passo dopo è tuo e reversibile: eseguilo ora, nello stesso turno. "
          "Se tocca un freno, fermati e dillo.")
FILE_VELENO = ("continua.py", "fine_turno.py", "hub.py")  # i file che i veleni rompono

PASSO_MIO = [
    "Fatto: i commit sono pubblicati.\n\nNiente da fare per te. Il prossimo passo è mio: lo step C1 del piano, "
    "la misura del peso dell'avvio.",
    "Ho chiuso il primo pezzo.\n\nIl prossimo passo è mio.\n\nNiente da fare per te.",
    "Banchi verdi. Il passo dopo è mio: unisco il ramo su dev.",
    "Prossimo passo: rilancio il banco su Windows (io).",
    "Prossimo passo: io faccio tornare verde il Mac in CI.",
    "Prossimo passo: la misura sui transcript, la faccio io.",
    # Il caso del 24/11: un "quando torna online" in un'altra voce non è un rinvio del passo mio.
    "- **PC Windows:** resta da rifare lì il giro dei banchi quando torna online.\n\n"
    "Niente da fare per te. Il prossimo passo è mio: lo step C1 del piano, la misura del peso dell'avvio.",
]
NIENTE = [
    "Fatto: il banco è verde.\nNiente da fare per te",
    "Ho chiuso il lavoro, il commit è su origin.",
    "Non c'è un altro passo mio su questo filone, quindi non riparto da solo.",
    "Prossimo passo: non lo faccio io, aspetta la revisione del cliente.",
]
DOMANDE = [
    "Il prossimo passo è mio: parto dal banco. Procedo?",
    "Il prossimo passo è mio. Vuoi che parta da A o da B?\n",
    "Il prossimo passo è mio, ma scrivimi **vai** quando hai letto la tabella.",
    "Prossimo passo: faccio io la revoca, poi tu controlli il vault.",
]
FRENI = [
    "Il prossimo passo è mio: invio l'email al cliente con la bozza.",
    "Il prossimo passo è mio, e serve la password del vault.",
    "Il prossimo passo è mio: il pagamento della fattura di novembre.",
    "Il prossimo passo è mio: entro col codice 2FA.",
    "Il prossimo passo è mio: firma il contratto in DocuSign.",
    "Il prossimo passo è mio: tolgo lo sblocco della config.",
    "Il prossimo passo è mio.\n`! bw unlock`",
]
RINVII = [
    "Prossimo passo: io aggiorno il PC Windows appena è acceso.",
    "Prossimo passo: io leggo l'esito del test SMART di disk1 quando finisce.",
    "Prossimo passo: io rileggo il test del disco alla prossima apertura del server.",
    "Prossimo passo: io riconto dal 25/11 quante richieste di permesso restano a te.\nNiente da fare per te.",
]
ROTAZIONI = [
    "Il prossimo passo è mio.\nruoto: step 3 del piano, la misura dell'avvio",
    "Il prossimo passo è mio: lo faccio dopo la rotazione.",
    "Il passo dopo è mio, quindi la sessione riparte da sola col contesto pulito.",
]


def riga(tipo: str, testo: str = "", strumento: str = "") -> str:
    if tipo == "user":
        return json.dumps({"type": "user", "message": {"role": "user", "content": testo}})
    if tipo == "risultato":
        return json.dumps({"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "t1", "content": "ok"}]}})
    if strumento:
        return json.dumps({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "t1", "name": strumento, "input": {}}]}})
    return json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": testo}]}})


class Lab:
    def __init__(self, hooks: Path, casa: Path) -> None:
        self.hooks, self.casa = hooks, casa
        self.orsa = casa / ".claude"
        self.orsa.mkdir(parents=True, exist_ok=True)
        self.env = dict(os.environ)
        for k in ("ARTURO_CONTINUA", "ARTURO_TITOLO_FIGLIO", "ARTURO_HUB_TETTO", "HC_TERMINAL_ID"):
            self.env.pop(k, None)
        self.env.update(HOME=str(casa), USERPROFILE=str(casa), CLAUDE_CONFIG_DIR=str(self.orsa),
                        PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
        tabella = casa / "tabella.json"
        tabella.write_text(json.dumps({"prompt": []}), encoding="utf-8")
        self.env["ARTURO_HUB_TABELLA"] = str(tabella)

    def stop(self, sid: str, testo: str | None = None, trascrizione: Path | None = None, attivo: bool = False,
             grezzo: bytes | None = None, extra_env: dict | None = None):
        evento = {"hook_event_name": "Stop", "session_id": sid, "stop_hook_active": attivo}
        if testo is not None:
            evento["last_assistant_message"] = testo
        if trascrizione is not None:
            evento["transcript_path"] = str(trascrizione)
        env = dict(self.env, **(extra_env or {}))
        dati = grezzo if grezzo is not None else json.dumps(evento).encode("utf-8")
        return subprocess.run([sys.executable, "-B", str(self.hooks / "continua.py")], input=dati, env=env,
                              capture_output=True, timeout=30)

    def prompt(self, sid: str):
        evento = {"hook_event_name": "UserPromptSubmit", "session_id": sid, "prompt": "vai avanti"}
        return subprocess.run([sys.executable, "-B", str(self.hooks / "hub.py"), "prompt"],
                              input=json.dumps(evento).encode("utf-8"), env=self.env, capture_output=True, timeout=60)

    def conto(self, sid: str) -> Path:
        return self.orsa / "cache" / "continua" / sid

    def registro(self) -> list:
        f = self.orsa / "cache" / "continua" / "registro.jsonl"
        if not f.is_file():
            return []
        return [json.loads(r) for r in f.read_text(encoding="utf-8").splitlines() if r.strip()]


def blocca(r) -> bool:
    if r.returncode != 0:
        return False
    try:
        d = json.loads(r.stdout.decode("utf-8") or "{}")
    except ValueError:
        return False
    return d == {"decision": "block", "reason": MOTIVO}


def tace(r) -> bool:
    return r.returncode == 0 and not r.stdout.strip()


def cn01(lab: Lab) -> str | None:
    for i, testo in enumerate(PASSO_MIO):
        r = lab.stop(f"a{i}", testo)
        if not blocca(r):
            return f"CN01 ROSSO: il passo mio non continua: {testo[-60:]!r} -> {r.returncode} {r.stdout[:120]!r}"
    if not lab.conto("a0").is_file() or lab.conto("a0").read_text(encoding="utf-8").strip() != "1":
        return "CN01 ROSSO: il conto della sessione non dice 1 giro"
    if not any(e.get("esito") == "block" and e.get("sid") == "a0" and e.get("giro") == 1 for e in lab.registro()):
        return f"CN01 ROSSO: il block non finisce nel registro: {lab.registro()[:2]}"
    for i, testo in enumerate(NIENTE):
        r = lab.stop(f"n{i}", testo)
        if not tace(r):
            return f"CN01 ROSSO: un testo senza passo mio continua: {testo[-60:]!r}"
        if lab.conto(f"n{i}").exists():
            return "CN01 ROSSO: un testo senza passo mio scrive il conto"
    if not tace(lab.stop("spento", PASSO_MIO[0], extra_env={"ARTURO_CONTINUA": "0"})):
        return "CN01 ROSSO: ARTURO_CONTINUA=0 non spegne l'hook"
    return None


def _tutti_zitti(lab: Lab, codice: str, testi: list, prefisso: str) -> str | None:
    for i, testo in enumerate(testi):
        r = lab.stop(f"{prefisso}{i}", testo)
        if not tace(r):
            return f"{codice} ROSSO: continua su {testo[-70:]!r}"
        if lab.conto(f"{prefisso}{i}").exists():
            return f"{codice} ROSSO: scrive il conto su {testo[-70:]!r}"
    return None


def cn02(lab: Lab) -> str | None:
    return _tutti_zitti(lab, "CN02", DOMANDE, "d")


def cn03(lab: Lab) -> str | None:
    return _tutti_zitti(lab, "CN03", FRENI, "f") or _tutti_zitti(lab, "CN03", RINVII, "v")


def cn04(lab: Lab) -> str | None:
    rosso = _tutti_zitti(lab, "CN04", ROTAZIONI, "r")
    if rosso:
        return rosso
    testo = PASSO_MIO[1]
    tr = lab.casa / "ruota.jsonl"
    tr.write_text("\n".join([riga("user", "fai lo step 2"), riga("assistant", strumento="mcp__arturo__ruota"),
                             riga("risultato"), riga("assistant", testo)]) + "\n", encoding="utf-8")
    if not tace(lab.stop("rt1", testo, trascrizione=tr)):
        return "CN04 ROSSO: continua dopo il tool ruota chiamato nello stesso turno"
    vecchio = lab.casa / "ruota-vecchio.jsonl"
    vecchio.write_text("\n".join([riga("user", "fai lo step 1"), riga("assistant", strumento="mcp__arturo__ruota"),
                                  riga("risultato"), riga("assistant", "ruotato"), riga("user", "ora lo step 2"),
                                  riga("assistant", testo)]) + "\n", encoding="utf-8")
    if not blocca(lab.stop("rt2", testo, trascrizione=vecchio)):
        return "CN04 ROSSO: il tool ruota di un turno di prima ferma la continuazione"
    return None


def cn05(lab: Lab) -> str | None:
    testo = PASSO_MIO[0]
    for giro in range(1, 4):
        r = lab.stop("t5", testo, attivo=giro > 1)
        if not blocca(r):
            return f"CN05 ROSSO: il giro {giro} di 3 non continua"
    r = lab.stop("t5", testo, attivo=True)
    if not tace(r):
        return "CN05 ROSSO: la quarta continuazione di fila non si ferma (stop_hook_active non conta?)"
    if lab.conto("t5").read_text(encoding="utf-8").strip() != "3":
        return f"CN05 ROSSO: il conto dice {lab.conto('t5').read_text(encoding='utf-8')!r}, atteso 3"
    if not any(e.get("esito") == "tetto" and e.get("sid") == "t5" for e in lab.registro()):
        return "CN05 ROSSO: il tetto raggiunto non finisce nel registro"
    return None


def cn06(lab: Lab) -> str | None:
    testo = PASSO_MIO[0]
    for _ in range(3):
        lab.stop("p6", testo)
    if not tace(lab.stop("p6", testo)):
        return "CN06 ROSSO: il tetto non si riempie, il caso non prova l'azzeramento"
    lab.stop("altra", testo)
    r = lab.prompt("p6")
    if r.returncode != 0:
        return f"CN06 ROSSO: hub.py prompt esce {r.returncode}: {r.stderr[:200]!r}"
    if lab.conto("p6").exists():
        return "CN06 ROSSO: il messaggio della persona non azzera il conto (hub.py prompt)"
    if not lab.conto("altra").exists():
        return "CN06 ROSSO: il prompt di una sessione azzera il conto di un'altra"
    if not blocca(lab.stop("p6", testo)):
        return "CN06 ROSSO: dopo il messaggio della persona l'hook non riparte"
    return None


def cn07(lab: Lab) -> str | None:
    tr = lab.casa / "t7.jsonl"
    tr.write_text("\n".join([riga("user", "fai il lavoro"), riga("assistant", "Leggo i file."),
                             riga("assistant", strumento="Bash"), riga("risultato"),
                             riga("assistant", PASSO_MIO[1])]) + "\n", encoding="utf-8")
    if not blocca(lab.stop("s7", trascrizione=tr)):
        return "CN07 ROSSO: senza last_assistant_message l'hook non legge la trascrizione"
    tr2 = lab.casa / "t7b.jsonl"
    tr2.write_text("\n".join([riga("user", "fai il lavoro"), riga("assistant", PASSO_MIO[1]),
                              riga("assistant", "Ho chiuso il lavoro, il commit è su origin.")]) + "\n", encoding="utf-8")
    if not tace(lab.stop("s7b", trascrizione=tr2)):
        return "CN07 ROSSO: conta un testo di Claude che non è l'ultimo"
    if not tace(lab.stop("s7c", grezzo=b"non json")):
        return "CN07 ROSSO: un ingresso rotto non esce 0 in silenzio"
    if not tace(lab.stop("", PASSO_MIO[0])):
        return "CN07 ROSSO: senza sessione l'hook continua"
    if not tace(lab.stop("s7d", trascrizione=lab.casa / "manca.jsonl")):
        return "CN07 ROSSO: una trascrizione che manca non esce 0 in silenzio"
    return None


FINTO = "#!/bin/sh\ncat >/dev/null 2>&1\nprintf '%s\\n' \"$1\" >> \"$HERDR_FINTO\"\n"


def cn08(lab: Lab) -> str | None:
    impostazioni = lab.hooks.parent / "settings.json"
    if impostazioni.is_file():
        stop = json.loads(impostazioni.read_text(encoding="utf-8")).get("hooks", {}).get("Stop", [])
        comandi = [h.get("command", "") for m in stop for h in m.get("hooks", [])]
        if any("herdr-stato" in c for c in comandi):
            return "CN08 ROSSO: lo Stop di settings.json ha ancora herdr-stato.sh, che segna fatto anche il turno che continua"
    copia = lab.casa / "hooks"
    shutil.copytree(str(lab.hooks), str(copia), ignore=shutil.ignore_patterns("__pycache__"))
    (copia / "herdr-stato.sh").write_text(FINTO, encoding="utf-8")
    lab.hooks = copia
    stati = lab.casa / "herdr.txt"
    dentro = {"HC_TERMINAL_ID": "t-cn08", "HERDR_FINTO": str(stati)}

    def nuovi_stati(passo) -> tuple:
        prima = stati.read_text(encoding="utf-8").split() if stati.is_file() else []
        r = passo()
        dopo = stati.read_text(encoding="utf-8").split() if stati.is_file() else []
        return r, dopo[len(prima):]

    r, nuovi = nuovi_stati(lambda: lab.stop("h1", PASSO_MIO[0], extra_env=dentro))
    if not blocca(r) or nuovi != ["working"]:
        return f"CN08 ROSSO: il turno che continua manda a Herdr {nuovi}, atteso ['working'] (block: {blocca(r)})"
    for nome, passo in (
            ("niente passo mio", lambda: lab.stop("h2", NIENTE[0], extra_env=dentro)),
            ("hook spento", lambda: lab.stop("h3", PASSO_MIO[0], extra_env=dict(dentro, ARTURO_CONTINUA="0"))),
            ("ingresso rotto", lambda: lab.stop("h4", grezzo=b"non json", extra_env=dentro))):
        r, nuovi = nuovi_stati(passo)
        if not tace(r) or nuovi != ["done"]:
            return f"CN08 ROSSO: {nome}: Herdr riceve {nuovi}, atteso ['done'] (rc {r.returncode})"
    for _ in range(3):
        lab.stop("h5", PASSO_MIO[0], extra_env=dentro)
    r, nuovi = nuovi_stati(lambda: lab.stop("h5", PASSO_MIO[0], extra_env=dentro))
    if not tace(r) or nuovi != ["done"]:
        return f"CN08 ROSSO: al tetto Herdr riceve {nuovi}, atteso ['done']"
    for nome, env in (("fuori da Herdr", {"HERDR_FINTO": str(stati)}),
                      ("nel figlio di titolo-sessione.py", dict(dentro, ARTURO_TITOLO_FIGLIO="1"))):
        r, nuovi = nuovi_stati(lambda: lab.stop("h6", NIENTE[0], extra_env=env))
        if r.returncode != 0 or nuovi:
            return f"CN08 ROSSO: {nome} l'hook manda a Herdr {nuovi}"
    return None


MOTIVI_CHIUSURA = {
    "passato": "La chiusura passa alla persona un passo tuo",
    "via": "La chiusura chiede il via per un lavoro tuo",
    "rinvio": "Prometti un controllo per più tardi",
}
CHIUSURE = [
    ("passato", "Il contesto è al 65%. Per continuare pulito, scrivi **/clear** e poi **/inizio volta**."),
    ("passato", "Salvo con /fine. Dopo, `/clear` e `/inizio volta` aprono una sessione pulita.\n\nNiente da fare per te."),
    ("passato", "Il gate è verde. Fai tu la rotazione quando vuoi."),
    ("passato", "Prossimo passo: scrivi tu all'altra sessione che il push è fatto."),
    ("via", "Ho letto i dieci rilievi.\n\nScrivimi **vai** e parto con la #16."),
    ("via", "Scrivimi **correggi i dieci** e preparo il piano delle correzioni."),
    ("via", "Il ramo è pronto. Parto se mi scrivi ok."),
    ("rinvio", "Prossimo passo: domattina guardo io il registro delle 07:45 e l'esito del test del disco."),
    ("rinvio", "Il backup è armato. Domattina controllo che la copia notturna abbia girato.\n\nNiente da fare per te."),
    ("rinvio", "Il prossimo passo è mio: il controllo del registro, domattina alle 6:30."),
]
CHIUSURE_ZITTE = [
    "Scrivimi **parti Cristicchi** e avvio la sponsorizzata in dark da 330 euro.",
    "Scrivimi **vai** e invio l'email al cliente.",
    "Il prossimo passo è mio, ma scrivimi **vai** quando hai letto la tabella.",
    "La prossima copia parte quando finisce il test del disco: la leggo alla prossima accensione del server.",
    "Il controllo di Search Console è domani.\n\nNiente da fare per te.",
    "Ho tolto la richiesta di /clear e /inizio quando il passo dopo è mio.",
]


def _trascrizione(lab: Lab, nome: str, testo: str, strumento: dict | None) -> Path:
    righe = [riga("user", "fai il lavoro")]
    if strumento:
        righe += [json.dumps({"type": "assistant", "message": {"content": [dict(type="tool_use", id="t9", **strumento)]}}),
                  riga("risultato")]
    tr = lab.casa / f"{nome}.jsonl"
    tr.write_text("\n".join(righe + [riga("assistant", testo)]) + "\n", encoding="utf-8")
    return tr


def cn09(lab: Lab) -> str | None:
    for i, (forma, testo) in enumerate(CHIUSURE):
        r = lab.stop(f"c9-{i}", testo)
        try:
            d = json.loads(r.stdout.decode("utf-8") or "{}")
        except ValueError:
            d = {}
        if d.get("decision") != "block" or not str(d.get("reason", "")).startswith(MOTIVI_CHIUSURA[forma]):
            return f"CN09 ROSSO: la chiusura {forma} non dà il suo block: {testo[:60]!r} -> {r.stdout[:100]!r}"
        if not tace(lab.stop(f"c9-{i}", testo, attivo=True)):
            return f"CN09 ROSSO: col secondo Stop (stop_hook_active) la chiusura {forma} blocca ancora: {testo[:50]!r}"
    for i, testo in enumerate(CHIUSURE_ZITTE):
        if not tace(lab.stop(f"z9-{i}", testo)):
            return f"CN09 ROSSO: una chiusura giusta dà un block: {testo[:60]!r}"
    rinvio, passato = CHIUSURE[7][1], CHIUSURE[0][1]
    for nome, strumento in (("monitor", {"name": "Monitor", "input": {}}),
                            ("fondo", {"name": "Bash", "input": {"command": "sleep 600; leggi", "run_in_background": True}})):
        if not tace(lab.stop(f"a9-{nome}", rinvio, trascrizione=_trascrizione(lab, nome, rinvio, strumento))):
            return f"CN09 ROSSO: il rinvio con un richiamo armato nel turno ({nome}) dà un block"
    nudo = {"name": "Bash", "input": {"command": "ls"}}
    if tace(lab.stop("a9-nudo", rinvio, trascrizione=_trascrizione(lab, "nudo", rinvio, nudo))):
        return "CN09 ROSSO: un Bash in primo piano vale come richiamo armato"
    ruota = {"name": "mcp__arturo__ruota", "input": {}}
    if not tace(lab.stop("a9-ruota", passato, trascrizione=_trascrizione(lab, "ruota", passato, ruota))):
        return "CN09 ROSSO: /clear e /inizio col tool ruota chiamato nel turno danno un block"
    return None


FUNZIONI = {"CN01": cn01, "CN02": cn02, "CN03": cn03, "CN04": cn04, "CN05": cn05, "CN06": cn06, "CN07": cn07,
            "CN08": cn08, "CN09": cn09}


def prova(hooks: Path) -> list:
    rossi = []
    for codice in CASI:
        with tempfile.TemporaryDirectory(prefix=f"cn-{codice.lower()}-") as d:
            try:
                r = FUNZIONI[codice](Lab(hooks, Path(d)))
            except Exception as e:  # noqa: BLE001 - un caso che getta è rosso, col suo motivo
                r = f"{codice} ROSSO per eccezione: {type(e).__name__}: {e}"
        if r:
            rossi.append(r)
    return rossi


# (casi che devono diventare rossi, file, testo vecchio, testo nuovo)
VELENI = [
    # PASSO_MIO sempre vero e nessun filtro: l'hook continua su ogni turno, come quello di impeccable.
    ({"CN01", "CN02", "CN03", "CN04"}, "continua.py", 'def decidi(testo: str) -> str:\n',
     'def decidi(testo: str) -> str:\n    return "continua"\n'),
    ({"CN01"}, "continua.py", "def passo_mio(fine: str) -> bool:\n    return any(r.search(fine) for r in PASSO_MIO)",
     "def passo_mio(fine: str) -> bool:\n    return True"),
    ({"CN02"}, "continua.py", '    if chiede(testo):\n        return "domanda"\n', ''),
    ({"CN03"}, "continua.py", '    if any(r.search(fine) for r in FRENO):\n        return "freno"\n', ''),
    ({"CN03"}, "continua.py", '    if RINVIO.search(righe_del_passo(fine)):\n        return "rinvio"\n', ''),
    ({"CN01"}, "continua.py", '    if RINVIO.search(righe_del_passo(fine)):\n', '    if RINVIO.search(fine):\n'),
    ({"CN04"}, "continua.py", '    if RUOTO.search(fine):\n        return "rotazione"\n', ''),
    ({"CN04"}, "continua.py", '    if decidi(testo) != "continua" or ruota_nel_turno(strumenti):\n',
     '    if decidi(testo) != "continua":\n'),
    # La chiusura (#6403): ogni forma spenta, il secondo Stop che blocca ancora, spesa e richiamo armato ignorati.
    ({"CN09"}, "continua.py", '    if any(r.search(fine) for r in PASSATO) and not ruota_nel_turno(strumenti):\n',
     '    if False:\n'),
    ({"CN09"}, "continua.py", '    if righe_via and not SPESA.search(righe_via)', '    if False and righe_via'),
    ({"CN09"}, "continua.py", '    if promessa and not armato_nel_turno(strumenti):\n', '    if False:\n'),
    ({"CN09"}, "continua.py", '        difetto = "niente" if attivo else chiusura(testo, strumenti)\n',
     '        difetto = chiusura(testo, strumenti)\n'),
    ({"CN09"}, "continua.py", '    if promessa and not armato_nel_turno(strumenti):\n', '    if promessa:\n'),
    ({"CN09"}, "continua.py", '    if righe_via and not SPESA.search(righe_via)', '    if righe_via'),
    ({"CN09"}, "continua.py", '    if any(r.search(fine) for r in PASSATO) and not ruota_nel_turno(strumenti):\n',
     '    if any(r.search(fine) for r in PASSATO):\n'),
    ({"CN04"}, "continua.py", '        if prompt_vero(d):\n            visti = []\n', '        if prompt_vero(d):\n            pass\n'),
    ({"CN05"}, "continua.py", '    if giri >= TETTO:\n', '    if False:\n'),
    ({"CN05"}, "continua.py", '    giri = leggi_conto(f)\n', '    giri = 0 if attivo else leggi_conto(f)\n'),
    ({"CN06"}, "hub.py", '    if voce == "prompt":\n        _azzera_continua(dati)\n', ''),
    ({"CN07"}, "fine_turno.py",
     '    return str(dati.get("last_assistant_message") or "") or ultimo_testo(str(dati.get("transcript_path") or ""))',
     '    return str(dati.get("last_assistant_message") or "")'),
    ({"CN07"}, "continua.py", "    except Exception:  # noqa: BLE001 - un hook di Stop rotto non deve mai fermare né trattenere la sessione\n        pass\n",
     "    except Exception:\n        raise\n"),
    # Lo stato verso Herdr: sempre done (il difetto di #6594), nessuno stato, anche fuori da Herdr.
    ({"CN08"}, "continua.py", '    herdr("working" if continua else "done")\n', '    herdr("done")\n'),
    ({"CN08"}, "continua.py", '    herdr("working" if continua else "done")\n', ''),
    ({"CN08"}, "continua.py", '    if not os.environ.get("HC_TERMINAL_ID") or os.environ.get("ARTURO_TITOLO_FIGLIO"):\n',
     '    if False:\n'),
]


def avvelena(hooks: Path) -> int:
    testi = {n: (hooks / n).read_text(encoding="utf-8") for n in FILE_VELENO}
    morsi = 0
    for attesi, nome, vecchio, nuovo in VELENI:
        etichetta = ",".join(sorted(attesi))
        if testi[nome].count(vecchio) != 1:
            print(f"VELENO {etichetta} NON SI APPLICA in {nome}: {vecchio[:60]!r}")
            continue
        with tempfile.TemporaryDirectory(prefix="cn-veleno-") as d:
            # Tutta la cartella hooks/: hub.py importa nel_processo.py, che importa evento_bash.py.
            copia = Path(d) / "hooks"
            shutil.copytree(str(hooks), str(copia), ignore=shutil.ignore_patterns("__pycache__"))
            (copia / nome).write_text(testi[nome].replace(vecchio, nuovo), encoding="utf-8")
            rossi = {r.split()[0] for r in prova(copia)}
        mancano = attesi - rossi
        print(f"VELENO {etichetta} ({nome}) " + (f"ROSSO: {sorted(rossi)}" if not mancano else f"NON ATTACCA {sorted(mancano)}"))
        morsi += not mancano
    print(f"veleni rossi {morsi}/{len(VELENI)}")
    if morsi != len(VELENI):
        return 1
    print(f"VELENI_ROSSI={','.join(sorted(set().union(*(a for a, _, _, _ in VELENI))))} veleni={len(VELENI)}")
    return 0


def main() -> int:
    for flusso in (sys.stdout, sys.stderr):
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--avvelena", action="store_true")
    parser.add_argument("--baseline-ref")
    a = parser.parse_args()
    hooks = Path(a.repo).resolve() / "hooks"
    if a.avvelena:
        return avvelena(hooks)
    rossi = prova(hooks)
    if a.baseline_ref:
        codici = [r.split()[0] for r in rossi]
        assert codici == DISCRIMINANTI, f"baseline non discriminante: rossi {codici}, attesi {DISCRIMINANTI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print(r)
    print(f"continua: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
