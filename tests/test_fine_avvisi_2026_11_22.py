#!/usr/bin/env python3
"""bin/fine-coda.py --avvisi: l'avviso della FASE 9 di /fine parte solo quando serve (#6275, segnalazione n. 94).

Il 20/11/2026, con quattro sessioni aperte, /fine ha avvisato tutte le sessioni vive che il commit di sync avrebbe
preso i loro file della config, anche senza file da salvare e anche a chi non li aveva toccati.

FA01 solo file sotto data/ (handoff, memoria) da salvare: exit 3, "nessun file", nessuna riga AVVISA anche se
     una sessione viva ha scritto quei file.
FA02 un file di Arturo fuori da data/ modificato, scritto con Edit da una sessione viva: exit 0, una riga
     AVVISA col nome della sessione e il file.
FA03 lo stesso file, ma la sessione viva ha toccato un altro file e quella che l'ha scritto è chiusa (pid
     morto): exit 3, nessun avviso.
FA04 il file l'ha scritto solo la sessione che chiude (CLAUDE_CODE_SESSION_ID): exit 3, nessun avviso.
FA05 una sessione viva nomina il file in un comando di Bash con ~/.claude/...: exit 0, riga AVVISA.
FA06 dopo l'anteprima l'indice vero resta com'era (niente in stage) e la copia dell'indice non resta in .git.
FA07 remote non privato: un file nuovo in hooks/, scritto da una sessione viva e visibile in git status, non
     entra nel commit di sync (è della persona), quindi niente avviso (exit 3). Le regole sono quelle del
     passo 6, non quelle di git status.

Sulla base e1a03e6 --avvisi non esiste (exit 5): rossi tutti i casi. Con --avvelena ogni rottura di VELENI
(pid sempre vivo, sessione propria inclusa, comando di Bash non letto, anteprima da git status invece che dal
passo 6) fa rosso il suo caso.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

QUI = Path(__file__).resolve().parent
CASI = ["FA01", "FA02", "FA03", "FA04", "FA05", "FA06", "FA07"]
FILE_ARTURO = "bin/index-rigenera.py"


def banco_coda():
    spec = importlib.util.spec_from_file_location("banco_fine_coda", QUI / "test_fine_coda_2026_10_30.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


FC = banco_coda()


class Avvisi:
    def __init__(self, lab):
        self.lab = lab
        self.cc = lab.tmp / "cc"
        (self.cc / "sessions").mkdir(parents=True)
        lab.ambiente["FINE_CODA_SESSIONI"] = str(self.cc / "sessions")

    def sessione(self, sid, nome, pid, usi, cwd=None):
        """Una sessione con il file in sessions/ e una trascrizione con gli usi dei tool [(tool, input)]."""
        cwd = str(cwd or self.lab.tmp)
        (self.cc / "sessions" / f"{pid}.json").write_text(
            json.dumps({"pid": pid, "sessionId": sid, "name": nome, "cwd": cwd}), encoding="utf-8")
        cartella = self.cc / "projects" / cwd.replace("/", "-").replace("\\", "-").replace(":", "-")
        cartella.mkdir(parents=True, exist_ok=True)
        righe = [json.dumps({"type": "user", "message": {"content": "ciao"}})]
        for tool, entrata in usi:
            righe.append(json.dumps({"type": "assistant", "message": {"content": [
                {"type": "text", "text": "faccio"}, {"type": "tool_use", "name": tool, "input": entrata}]}}))
        (cartella / f"{sid}.jsonl").write_text("\n".join(righe) + "\n", encoding="utf-8")

    def avvisi(self):
        return subprocess.run([sys.executable, "-B", str(self.lab.cl / "bin" / "fine-coda.py"), "--avvisi"],
                              capture_output=True, text=True, encoding="utf-8", errors="replace",
                              env=self.lab.ambiente, timeout=120)

    def modifica_arturo(self):
        f = self.lab.cl / FILE_ARTURO
        f.write_text(f.read_text(encoding="utf-8") + "# modificato\n", encoding="utf-8")
        return f


def pid_morto():
    p = subprocess.Popen([sys.executable, "-c", "pass"])
    p.wait()
    return p.pid


VIVO = os.getpid()


def esito(r):
    return f"rc={r.returncode} {(r.stdout + r.stderr).strip()[-220:]!r}"


def fa01(lab):
    a = Avvisi(lab)
    lab.handoff()
    nota = lab.scrivi("data/memory/pattern/nota.md", "---\nname: nota\n---\n")
    a.sessione("s-vive-1", "libro scrive", VIVO, [("Write", {"file_path": str(nota)})])
    r = a.avvisi()
    if r.returncode != 3 or "nessun file" not in r.stdout or "AVVISA" in r.stdout:
        return esito(r)


def fa02(lab):
    a = Avvisi(lab)
    f = a.modifica_arturo()
    a.sessione("s-vive-2", "guardie al lavoro", VIVO, [("Edit", {"file_path": str(f), "old_string": "a"})])
    r = a.avvisi()
    if r.returncode != 0 or "AVVISA guardie al lavoro (sessione s-vive-2)" not in r.stdout \
            or FILE_ARTURO not in r.stdout:
        return esito(r)


def fa03(lab):
    a = Avvisi(lab)
    f = a.modifica_arturo()
    a.sessione("s-vive-3", "altro lavoro", VIVO, [("Edit", {"file_path": str(lab.cl / "README-altro.md")})])
    a.sessione("s-morta-3", "chiusa ieri", pid_morto(), [("Edit", {"file_path": str(f)})])
    r = a.avvisi()
    if r.returncode != 3 or "AVVISA" in r.stdout or "nessuna altra sessione" not in r.stdout:
        return esito(r)


def fa04(lab):
    a = Avvisi(lab)
    f = a.modifica_arturo()
    a.sessione(lab.ambiente["CLAUDE_CODE_SESSION_ID"], "io che chiudo", VIVO, [("Write", {"file_path": str(f)})])
    r = a.avvisi()
    if r.returncode != 3 or "AVVISA" in r.stdout:
        return esito(r)


def fa05(lab):
    a = Avvisi(lab)
    a.modifica_arturo()
    a.sessione("s-vive-5", "", VIVO, [("Bash", {"command": f"sed -i '' 's/a/b/' ~/.claude/{FILE_ARTURO}"})])
    r = a.avvisi()
    if r.returncode != 0 or "AVVISA senza nome (sessione s-vive-5)" not in r.stdout:
        return esito(r)


def fa06(lab):
    a = Avvisi(lab)
    a.modifica_arturo()
    lab.scrivi("hooks/nuovo.py", "# nuovo\n")
    r = a.avvisi()
    in_stage = lab.git(lab.cl, "diff", "--cached", "--name-only").split()
    copie = [p.name for p in (lab.cl / ".git").iterdir() if p.name.startswith("index.fine-avvisi")]
    if r.returncode not in (0, 3) or "nessun file" in r.stdout or in_stage or copie:
        return f"{esito(r)} in stage {in_stage} copie {copie}"


def fa07(lab):
    a = Avvisi(lab)
    f = lab.scrivi("hooks/mio.py", "# mio\n")
    a.sessione("s-vive-7", "regole", VIVO, [("Write", {"file_path": str(f)})])
    r = a.avvisi()
    stato = lab.git(lab.cl, "status", "--porcelain", "--", "hooks/mio.py")
    if r.returncode != 3 or "AVVISA" in r.stdout or "nessun file" not in r.stdout or "hooks/mio.py" not in stato:
        return f"{esito(r)} stato {stato.strip()!r}"


def prova(repo, ref):
    rossi = []
    for codice, fn, k in (("FA01", fa01, {}), ("FA02", fa02, {}), ("FA03", fa03, {}), ("FA04", fa04, {}),
                          ("FA05", fa05, {}), ("FA06", fa06, {}), ("FA07", fa07, {"visibilita": "PUBLIC"})):
        e = FC.con_lab(repo, ref, fn, **k)
        if e:
            rossi.append(f"{codice} {e}")
    return rossi


# Ogni veleno rompe in bin/fine-coda.py il punto che il suo caso sorveglia.
VELENI = {
    "FA03": ("    if os.name == \"nt\":\n        return _viva_windows(pid)\n    try:", "    return True\n    try:"),
    "FA04": ("sid == mia or ", ""),
    "FA05": ("                    for ago, r in aghi.items():", "                    for ago, r in {}.items():"),
    "FA07": ("        if aggiungi_per_percorso()[\"falliti\"]:\n            return None\n"
             "        rc, out, _ = git(\"diff\", \"--cached\", \"--name-only\", \"--no-renames\", \"-z\")",
             "        rc, out, _ = git(\"ls-files\", \"-z\", \"-m\", \"-o\", \"--exclude-standard\")"),
}


def avvelena(repo):
    inerti = []
    for caso, (vecchio, rotto) in VELENI.items():
        with tempfile.TemporaryDirectory(prefix="arturo-fa-") as tmp:
            copia = Path(tmp) / "repo"
            for rel in FC.FILE:
                if (repo / rel).is_file():
                    (copia / rel).parent.mkdir(parents=True, exist_ok=True)
                    (copia / rel).write_bytes((repo / rel).read_bytes())
            f = copia / "bin" / "fine-coda.py"
            testo = f.read_text(encoding="utf-8")
            if testo.count(vecchio) != 1:
                inerti.append(f"{caso}: il punto da rompere compare {testo.count(vecchio)} volte")
                continue
            f.write_text(testo.replace(vecchio, rotto), encoding="utf-8")
            if not any(r.startswith(caso + " ") for r in prova(copia, None)):
                inerti.append(f"{caso}: la rottura non lo fa rosso")
    assert not inerti, "veleni che non attaccano:\n" + "\n".join(inerti)
    print(f"VELENI_ROSSI={','.join(VELENI)} veleni={len(VELENI)}")
    return 0


def main():
    for flusso in (sys.stdout, sys.stderr):  # su Windows la pipe è in cp1252
        if hasattr(flusso, "reconfigure"):
            flusso.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(QUI.parent))
    parser.add_argument("--avvelena", action="store_true")
    parser.add_argument("--baseline-ref")
    argomenti = parser.parse_args()
    if argomenti.avvelena:
        return avvelena(Path(argomenti.repo))
    rossi = prova(Path(argomenti.repo), argomenti.baseline_ref)
    if argomenti.baseline_ref:
        codici = [r.split()[0] for r in rossi]
        assert codici == CASI, f"baseline non discriminante: rossi {codici}, attesi {CASI}"
        print(f"BASELINE_DISCRIMINANTE={','.join(codici)}")
        return 0
    for r in rossi:
        print("ROSSO", r)
    print(f"avvisi di /fine: {len(CASI) - len(rossi)}/{len(CASI)} casi verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
