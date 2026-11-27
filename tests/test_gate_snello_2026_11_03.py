#!/usr/bin/env python3
"""GS01-GS13: il gate snello (3/11/2026), cioè tests/esegui_gate.py che fa girare i lavori del gate in parallelo.

GS01 un lavoro rosso non ferma gli altri: due rossi in liste diverse (un banco e una controprova) escono
     tutti e due nel rapporto, i verdi girano lo stesso e l'esecutore esce 1.
GS02 due worker hanno HOME e TMPDIR diversi: un lavoro che scrive nella sua HOME non si vede dall'altro.
     TEMP e TMP valgono come TMPDIR: su Windows Node, PowerShell e i programmi nativi leggono quelle, e le
     cartelle dei banchi restavano nella Temp vera (9.055 voci su un PC Windows il 22/11/2026, #6443).
GS03 l'ordine segue i tempi dell'ultimo giro (prima i lunghi); senza tempi segue le liste.
GS04 --rossi rifà solo i rossi del giro prima e stampa PARZIALE.
GS05 una controprova verde, al giro dopo con banco, fonti e base uguali, si salta e la riga finale la
     conta; una controprova rossa non entra in cache e si rifà (controprove in cache, 3/11/2026).
GS06 una controprova si rifà se cambia il banco, o un file che il banco importa (le sue fonti).
GS07 --rilascio, e ARTURO_GATE_RILASCIO=1, rifanno tutte le controprove anche in cache.
GS08 --toccati fa girare solo i lavori con una fonte fra i file cambiati e stampa PARZIALE.
GS09 --elenchi (il gate vero): un test_*.py in tests/ fuori dagli elenchi, un banco due volte, uno con --avvelena fuori da
     VELENI e un nome in lista senza file fanno rosso col nome; con gli elenchi completi esce 0 (review del
     7/11/2026, finding 94).
GS10 un banco non eredita ARTURO_CODICE né la cartella bin del codice nel PATH dalla sessione che lancia il
     gate: con Arturo installato come plugin /inizio nella HOME finta si credeva un plugin (10/11/2026, #5206).
GS11 un banco vede i pacchetti del sito utente di chi lancia il gate, anche nella HOME finta: su un Mac il sito
     utente sta sotto la HOME, e PyYAML installato solo lì dava quattro banchi rossi (22/11/2026, #6426). La base
     viene dalla HOME vera che verifica-allineamento.sh passa in ARTURO_GATE_HOME_VERA, e quella variabile non
     arriva al banco. Dove il sito utente non segue la HOME (Windows: APPDATA) il caso è un SALTO.
GS12 con ARTURO_GATE_BASE=<commit> --toccati confronta da quel commit: un cambio già in commit fa girare il suo
     banco, come serve alla CI sul push a dev (revisione del 22/11/2026, A1). Una base che non esiste ferma il
     gate con FAIL, e la variabile non arriva ai banchi.
GS13 .github/workflows/gate.yml fa girare il gate su ubuntu, macos e windows, solo nel repository pubblico, in
     sola lettura e senza segreti: --toccati con ARTURO_GATE_BASE sul push a dev, --rilascio sul tag e a mano.
     Il nome della run dice il modo ("gate rilascio"), perché la firma del rilascio lo cerca. Azioni fissate a
     un commit. Il rilascio gira in 4 parti per sistema (ARTURO_GATE_PARTE), il push su dev in una.

GS14 --parte I/N (24/11/2026): le N parti insieme fanno ogni lavoro una volta sola, anche quelli di --in-fila,
     e due lanci della stessa parte scelgono gli stessi lavori. Una parte fuori da 1..N ferma il gate.
GS15 le parti seguono tests/gate-pesi.json: il lavoro pesante sta da solo nella sua parte. Il controllo degli
     elenchi gira solo nella parte 1: nelle altre un elenco incompleto non fa rosso due volte.

Ogni caso gira su un repository finto con banchi finti, così misura l'esecutore e non i banchi veri.
Con --avvelena girano tre esecutori rotti. Uno ignora il codice d'uscita dei lavori: GS01 e GS04 devono
essere rossi. Uno salta sempre le controprove: rossi GS05, GS06 e GS07. Uno non le salta mai: rosso GS05.
Uno non confronta gli elenchi: rosso GS09. Uno dà a ogni parte tutti i lavori: rossi GS14 e GS15. Uno ignora
i pesi: rosso GS15. Uno confronta gli elenchi in ogni parte: rosso GS15. Uno passa ai banchi l'ambiente intero: rosso GS10. Uno non passa
la base del sito utente: rosso GS11. Uno confronta sempre da HEAD: rosso GS12.

Sulla base 177852f ogni controllo deve fallire con un AssertionError che comincia con il suo codice.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from salti_windows import dichiara  # noqa: E402

GIT_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@example.invalid", "GIT_CONFIG_GLOBAL": os.devnull}
BANCHI = {
    "ok_a.py": "print('PASS a')\n",
    "ok_b.py": "print('PASS b')\n",
    "rosso.py": "import sys\nprint('ROTTO-X')\nsys.exit(1)\n",
    "rosso2.py": "import sys\nprint('ROTTO-Y')\nsys.exit(1)\n",
    "casa.py": (
        "import json, os, sys, time\nfrom pathlib import Path\n"
        "nome = Path(sys.argv[0]).stem\nhome = Path(os.environ['HOME'])\n"
        "(home / f'segno-{nome}').write_text('x')\ntime.sleep(1.5)\n"
        "altri = sorted(p.name for p in home.glob('segno-*') if p.name != f'segno-{nome}')\n"
        "Path(os.environ['GS_OUT'], nome + '.json').write_text(json.dumps("
        "{'home': str(home), 'tmp': os.environ['TMPDIR'], 'temp': os.environ.get('TEMP'), "
        "'tmp2': os.environ.get('TMP'), 'altri': altri}))\n"),
}
BANCHI["casa2.py"] = BANCHI["casa.py"]
BANCHI["ambiente.py"] = (
    "import json, os\nfrom pathlib import Path\n"
    "Path(os.environ['GS_OUT'], 'ambiente.json').write_text(json.dumps("
    "{'codice': os.environ.get('ARTURO_CODICE'), 'path': os.environ.get('PATH', '')}))\n")
BANCHI["sito.py"] = (
    "import json, os\nfrom pathlib import Path\n"
    "try:\n    import gs11_modulo  # noqa: F401\n    visto = True\nexcept ImportError:\n    visto = False\n"
    "Path(os.environ['GS_OUT'], 'sito.json').write_text(json.dumps("
    "{'visto': visto, 'base': os.environ.get('PYTHONUSERBASE'), 'vera': os.environ.get('ARTURO_GATE_HOME_VERA')}))\n")
BANCHI["aiuto.py"] = "VALORE = 1\n"
BANCHI["usa_aiuto.py"] = "import aiuto\nprint('PASS', aiuto.VALORE)\n"
SALTO = "        if not rilascio and x.impronta and impronte.get(x.id) == x.impronta:\n"
VELENI = (
    (("GS01", "GS04"), "        lavoro.rosso = p.returncode != 0\n", "        lavoro.rosso = False\n"),
    (("GS05", "GS06", "GS07"), SALTO, "        if True:\n"),
    (("GS05",), SALTO, "        if False:\n"),
    (("GS09",), "    incompleti = elenchi_incompleti(root, a) if a.elenchi", "    incompleti = [] if a.elenchi"),
    (("GS10",), "        e = dict(ambiente_pulito(), HOME=", "        e = dict(os.environ, HOME="),
    (("GS11",), "        e.update(base_utente())\n", "        pass\n"),
    (("GS12",), '    base = os.environ.get(BASE_TOCCATI, "").strip() or "HEAD"\n', '    base = "HEAD"\n'),
    (("GS14", "GS15"), "        if i == parte - 1:\n", "        if True:\n"),
    (("GS15",), "        carico[i] += pesi.get(x.id, mediana)\n", "        carico[i] += 1.0\n"),
    (("GS15",), "if a.elenchi and parte == 1 and not", "if a.elenchi and not"),
)


class Salto(Exception):
    """Un caso che su questa piattaforma non ha cosa provare: SALTO nel gate, rosso nella controprova."""


class Lab:
    def __init__(self, base: Path, esecutore: Path) -> None:
        self.root = base / "repo"
        (self.root / "tests").mkdir(parents=True)
        (self.root / "tests" / "esegui_gate.py").write_bytes(esecutore.read_bytes())
        for nome, testo in BANCHI.items():
            (self.root / "tests" / nome).write_text(testo, encoding="utf-8")
        env = dict(os.environ, **GIT_ENV)
        for c in (["init", "-q"], ["add", "-A"], ["commit", "-q", "-m", "finto"]):
            subprocess.run(["git", "-C", str(self.root), *c], env=env, check=True, capture_output=True)
        self.base = base
        self.giro = 0

    def esegui(self, *argomenti: str, env: Optional[Dict[str, str]] = None) -> subprocess.CompletedProcess:
        self.giro += 1
        fixture = self.base / f"fixture{self.giro}"
        return subprocess.run([sys.executable, "-B", str(self.root / "tests" / "esegui_gate.py"), "esegui",
                               "--root", str(self.root), "--fixture", str(fixture), *argomenti],
                              capture_output=True, text=True, encoding="utf-8", timeout=300,
                              env=dict(self._ambiente(), **(env or {})))

    @staticmethod
    def _ambiente() -> Dict[str, str]:
        # Il gate del rilascio gira con ARTURO_GATE_RILASCIO=1 e il banco lo ereditava: GS05, che prova il salto
        # delle controprove in cache, diventava rosso proprio nel gate del tag (4/11/2026). Lo decide ogni caso.
        # Lo stesso per ARTURO_GATE_BASE della CI: GS08 e GS12 la decidono da soli.
        return {k: v for k, v in os.environ.items() if k not in ("ARTURO_GATE_RILASCIO", "ARTURO_GATE_BASE")}

    def tempi(self) -> Path:
        return self.root / ".git" / "arturo-gate-tempi.json"

    def scrivi(self, nome: str, testo: str) -> None:
        (self.root / "tests" / nome).write_text(testo, encoding="utf-8")

    def commit(self, messaggio: str) -> str:
        env = dict(os.environ, **GIT_ENV)
        for c in (["add", "-A"], ["commit", "-q", "-m", messaggio]):
            subprocess.run(["git", "-C", str(self.root), *c], env=env, check=True, capture_output=True)
        return subprocess.run(["git", "-C", str(self.root), "rev-parse", "HEAD"], capture_output=True, text=True,
                              check=True).stdout.strip()


def esecutore_di(repo: Path, codice: str) -> Path:
    f = repo / "tests" / "esegui_gate.py"
    assert f.is_file(), f"{codice} manca tests/esegui_gate.py"
    return f


def ordine(uscita: str) -> List[str]:
    return [r.split()[-1] for r in uscita.splitlines() if r.startswith(("OK ", "ROSSO "))]


def test_gs01(esecutore: Path) -> None:
    with tempfile.TemporaryDirectory() as t:
        lab = Lab(Path(t), esecutore)
        r = lab.esegui("--lavori", "2", "--banchi", "ok_a.py", "rosso.py", "--controprove", "rosso2.py HEAD",
                       "--veleni", "ok_b.py")
        out = r.stdout + r.stderr
        assert r.returncode == 1, f"GS01 con due rossi l'esecutore esce {r.returncode}: {out[-400:]}"
        for atteso in ("=== ROSSO banco:rosso.py", "ROTTO-X", "=== ROSSO controprova:rosso2.py@HEAD", "ROTTO-Y"):
            assert atteso in out, f"GS01 il rapporto non dice {atteso!r}: {out[-600:]}"
        fatti = ordine(out)
        assert "banco:ok_a.py" in fatti and "veleno:ok_b.py" in fatti, f"GS01 dopo un rosso i verdi non girano: {fatti}"


def test_gs02(esecutore: Path) -> None:
    with tempfile.TemporaryDirectory() as t:
        lab = Lab(Path(t), esecutore)
        uscite = Path(t) / "uscite"
        uscite.mkdir()
        r = lab.esegui("--lavori", "2", "--banchi", "casa.py", "casa2.py", env={"GS_OUT": str(uscite)})
        assert r.returncode == 0, f"GS02 l'esecutore esce {r.returncode}: {(r.stdout + r.stderr)[-400:]}"
        a, b = (json.loads((uscite / f"{n}.json").read_text(encoding="utf-8")) for n in ("casa", "casa2"))
        assert a["home"] != b["home"] and a["tmp"] != b["tmp"], f"GS02 i due worker condividono HOME o TMPDIR: {a} {b}"
        assert not a["altri"] and not b["altri"], f"GS02 un worker vede i file dell'altro: {a['altri']} {b['altri']}"
        for x in (a, b):
            assert x["temp"] == x["tmp"] and x["tmp2"] == x["tmp"], f"GS02 TEMP o TMP diversi da TMPDIR: {x}"


def test_gs03(esecutore: Path) -> None:
    with tempfile.TemporaryDirectory() as t:
        lab = Lab(Path(t), esecutore)
        r = lab.esegui("--lavori", "1", "--banchi", "ok_a.py", "ok_b.py")
        assert ordine(r.stdout) == ["banco:ok_a.py", "banco:ok_b.py"], f"GS03 senza tempi non segue le liste: {r.stdout!r}"
        lab.tempi().write_text(json.dumps({"banco:ok_a.py": 1, "banco:ok_b.py": 50}), encoding="utf-8")
        r = lab.esegui("--lavori", "1", "--banchi", "ok_a.py", "ok_b.py")
        assert ordine(r.stdout) == ["banco:ok_b.py", "banco:ok_a.py"], f"GS03 il lavoro lungo non parte per primo: {r.stdout!r}"


def test_gs04(esecutore: Path) -> None:
    with tempfile.TemporaryDirectory() as t:
        lab = Lab(Path(t), esecutore)
        liste = ("--lavori", "2", "--banchi", "ok_a.py", "rosso.py", "--controprove", "rosso2.py HEAD")
        lab.esegui(*liste)
        r = lab.esegui("--rossi", *liste)
        fatti = ordine(r.stdout)
        assert sorted(fatti) == ["banco:rosso.py", "controprova:rosso2.py@HEAD"], f"GS04 --rossi non rifà solo i rossi: {fatti}"
        assert "PARZIALE" in r.stdout and r.returncode == 1, f"GS04 --rossi non dice PARZIALE o non esce 1: {r.returncode} {r.stdout[-300:]!r}"


def saltate(uscita: str) -> int:
    for riga in uscita.splitlines():
        if riga.startswith("LAVORI:") and "controprove saltate=" in riga:
            return int(riga.split("controprove saltate=")[1].split()[0])
    return -1


def test_gs05(esecutore: Path) -> None:
    with tempfile.TemporaryDirectory() as t:
        lab = Lab(Path(t), esecutore)
        liste = ("--lavori", "2", "--controprove", "ok_a.py HEAD", "rosso2.py HEAD")
        r = lab.esegui(*liste)
        assert "controprova:ok_a.py@HEAD" in ordine(r.stdout), f"GS05 al primo giro la controprova non gira: {r.stdout!r}"
        r = lab.esegui(*liste)
        fatti = ordine(r.stdout)
        assert "controprova:ok_a.py@HEAD" not in fatti and saltate(r.stdout) == 1, \
            f"GS05 con banco e base uguali la controprova verde non si salta: {fatti} {r.stdout[-300:]!r}"
        assert "controprova:rosso2.py@HEAD" in fatti, f"GS05 una controprova rossa è finita in cache: {fatti}"


def test_gs06(esecutore: Path) -> None:
    with tempfile.TemporaryDirectory() as t:
        lab = Lab(Path(t), esecutore)
        liste = ("--lavori", "2", "--controprove", "ok_a.py HEAD", "usa_aiuto.py HEAD")
        lab.esegui(*liste)
        lab.scrivi("ok_a.py", "print('PASS a, cambiato')\n")
        lab.scrivi("aiuto.py", "VALORE = 2\n")
        r = lab.esegui(*liste)
        fatti = sorted(ordine(r.stdout))
        assert fatti == ["controprova:ok_a.py@HEAD", "controprova:usa_aiuto.py@HEAD"] and saltate(r.stdout) == 0, \
            f"GS06 con banco o fonte cambiati la controprova non si rifà: {fatti} {r.stdout[-300:]!r}"


def test_gs07(esecutore: Path) -> None:
    with tempfile.TemporaryDirectory() as t:
        lab = Lab(Path(t), esecutore)
        liste = ("--lavori", "1", "--controprove", "ok_a.py HEAD", "ok_b.py HEAD")
        lab.esegui(*liste)
        for argomenti, env in ((("--rilascio",), None), ((), {"ARTURO_GATE_RILASCIO": "1"})):
            r = lab.esegui(*argomenti, *liste, env=env)
            fatti = sorted(ordine(r.stdout))
            assert fatti == ["controprova:ok_a.py@HEAD", "controprova:ok_b.py@HEAD"] and saltate(r.stdout) == 0, \
                f"GS07 al rilascio ({argomenti or env}) non girano tutte le controprove: {fatti} {r.stdout[-300:]!r}"


def test_gs08(esecutore: Path) -> None:
    with tempfile.TemporaryDirectory() as t:
        lab = Lab(Path(t), esecutore)
        liste = ("--lavori", "2", "--banchi", "ok_a.py", "ok_b.py", "usa_aiuto.py", "--veleni", "ok_a.py")
        r = lab.esegui("--toccati", *liste)
        assert ordine(r.stdout) == [] and "PARZIALE" in r.stdout and r.returncode == 0, \
            f"GS08 senza file cambiati --toccati fa girare qualcosa: {r.returncode} {r.stdout[-300:]!r}"
        lab.scrivi("aiuto.py", "VALORE = 3\n")
        r = lab.esegui("--toccati", *liste)
        fatti = ordine(r.stdout)
        assert fatti == ["banco:usa_aiuto.py"] and "PARZIALE" in r.stdout, \
            f"GS08 --toccati non tiene solo i lavori del file cambiato: {fatti} {r.stdout[-300:]!r}"




def test_gs09(esecutore: Path) -> None:
    with tempfile.TemporaryDirectory() as t:
        lab = Lab(Path(t), esecutore)
        # Le eccezioni scritte nell'esecutore valgono per file veri: qui ci sono, finti.
        for nome in ("test_gate_run.sh", "test_pattern_segreti_allineati.py", "test_guardie_involucri.py"):
            lab.scrivi(nome, "print('PASS')\n")
        lab.scrivi("test_elencato.py", "print('PASS')\n")
        lab.scrivi("test_nuovo.py", "print('PASS')\n")
        lab.scrivi("test_veleno.py", "import sys\nprint('PASS')\nsys.exit(0 if '--avvelena' in sys.argv else 0)\n")
        base = ["--elenchi", "--banchi", "test_elencato.py", "test_veleno.py", "test_guardie_involucri.py"]
        rosso = lab.esegui(*base, "test_sparito.py", "--veleni", "test_veleno.py", "test_veleno.py")
        tutto = lab.esegui(*base, "test_nuovo.py", "--veleni", "test_veleno.py")
        attesi = ("test_nuovo.py: in tests/ ma in nessun elenco", "test_veleno.py: due volte in VELENI",
                  "test_sparito.py: nelle liste del gate ma non in tests/")
        senza_veleno = lab.esegui(*base, "test_nuovo.py")
        assert "test_veleno.py: ha --avvelena ma non sta in VELENI" in senza_veleno.stdout, \
            f"GS09 un banco con --avvelena fuori da VELENI non si vede: {senza_veleno.stdout[-300:]!r}"
        mancano = [x for x in attesi if x not in rosso.stdout]
        assert rosso.returncode == 1 and not mancano, f"GS09 elenchi incompleti non visti: rc {rosso.returncode}, " \
            f"mancano {mancano}, {rosso.stdout[-300:]!r}"
        assert tutto.returncode == 0 and "elenchi del gate" not in tutto.stdout, \
            f"GS09 elenchi completi danno rosso: rc {tutto.returncode}, {tutto.stdout[-300:]!r}"


def test_gs10(esecutore: Path) -> None:
    with tempfile.TemporaryDirectory() as t:
        lab = Lab(Path(t), esecutore)
        uscite = Path(t) / "uscite"
        uscite.mkdir()
        codice = str(Path(t) / "plugin" / "arturo")
        r = lab.esegui("--banchi", "ambiente.py", env={"GS_OUT": str(uscite), "ARTURO_CODICE": codice,
                                                       "PATH": os.pathsep.join([codice + "/bin", os.environ["PATH"]])})
        assert r.returncode == 0, f"GS10 l'esecutore esce {r.returncode}: {(r.stdout + r.stderr)[-400:]}"
        visto = json.loads((uscite / "ambiente.json").read_text(encoding="utf-8"))
        assert visto["codice"] is None and codice + "/bin" not in visto["path"].split(os.pathsep), \
            f"GS10 il banco eredita ARTURO_CODICE o la sua cartella bin dalla sessione che lancia il gate: {visto}"


def test_gs11(esecutore: Path) -> None:
    with tempfile.TemporaryDirectory() as t:
        casa = Path(t) / "casa-vera"
        casa.mkdir()
        vera = {k: v for k, v in os.environ.items() if k not in ("PYTHONUSERBASE", "PYTHONNOUSERSITE")}
        vera.update(HOME=str(casa), USERPROFILE=str(casa))
        sito = subprocess.run([sys.executable, "-c", "import site; print(site.getusersitepackages())"], env=vera,
                              capture_output=True, text=True, timeout=30).stdout.strip()
        if not sito or casa.resolve() not in Path(sito).resolve().parents:
            raise Salto(f"qui il sito utente non segue la HOME ({sito}): la HOME finta non lo nasconde")
        Path(sito).mkdir(parents=True)
        (Path(sito) / "gs11_modulo.py").write_text("VALORE = 1\n", encoding="utf-8")
        lab = Lab(Path(t), esecutore)
        uscite = Path(t) / "uscite"
        uscite.mkdir()
        # Come nel gate vero: verifica-allineamento.sh ha già spostato HOME nella cartella di prova e passa la HOME
        # vera in ARTURO_GATE_HOME_VERA. PYTHONUSERBASE vuoto vale come assente: conta la base presa da quella.
        finta = Path(t) / "casa-finta"
        finta.mkdir()
        r = lab.esegui("--banchi", "sito.py", env=dict(GS_OUT=str(uscite), HOME=str(finta), USERPROFILE=str(finta),
                                                       ARTURO_GATE_HOME_VERA=str(casa), PYTHONUSERBASE=""))
        assert r.returncode == 0, f"GS11 l'esecutore esce {r.returncode}: {(r.stdout + r.stderr)[-400:]}"
        visto = json.loads((uscite / "sito.json").read_text(encoding="utf-8"))
        assert visto["visto"], f"GS11 nella HOME finta il banco non vede il sito utente di chi lancia il gate: {visto}"
        assert not visto["vera"], f"GS11 la HOME vera arriva al banco: {visto}"


def test_gs12(esecutore: Path) -> None:
    with tempfile.TemporaryDirectory() as t:
        lab = Lab(Path(t), esecutore)
        prima = subprocess.run(["git", "-C", str(lab.root), "rev-parse", "HEAD"], capture_output=True, text=True,
                               check=True).stdout.strip()
        lab.scrivi("aiuto.py", "VALORE = 4\n")
        lab.scrivi("ambiente.py", BANCHI["ambiente.py"].replace("'path'", "'base': os.environ.get('ARTURO_GATE_BASE'), 'path'"))
        lab.commit("cambio in commit")
        uscita = Path(t) / "uscita"
        uscita.mkdir()
        liste = ("--lavori", "1", "--banchi", "ok_a.py", "usa_aiuto.py", "ambiente.py")
        r = lab.esegui("--toccati", *liste, env={"ARTURO_GATE_BASE": prima, "GS_OUT": str(uscita)})
        fatti = sorted(ordine(r.stdout))
        assert fatti == ["banco:ambiente.py", "banco:usa_aiuto.py"] and "PARZIALE" in r.stdout, \
            f"GS12 con ARTURO_GATE_BASE i cambi già in commit non fanno girare il loro banco: {fatti} {r.stdout[-300:]!r}"
        visto = json.loads((uscita / "ambiente.json").read_text(encoding="utf-8"))
        assert visto.get("base") is None, f"GS12 ARTURO_GATE_BASE arriva al banco: {visto.get('base')}"
        r = lab.esegui("--toccati", *liste, env={"ARTURO_GATE_BASE": "0" * 40, "GS_OUT": str(uscita)})
        assert r.returncode != 0 and "FAIL" in (r.stdout + r.stderr) and not ordine(r.stdout), \
            f"GS12 una base che non esiste non ferma il gate: {r.returncode} {(r.stdout + r.stderr)[-300:]!r}"


def test_gs13(esecutore: Path) -> None:
    f = esecutore.resolve().parents[1] / ".github" / "workflows" / "gate.yml"
    assert f.is_file(), "GS13 manca .github/workflows/gate.yml: il gate gira solo sul Mac di chi rilascia"
    testo = f.read_text(encoding="utf-8")
    dati = yaml.safe_load(testo)
    quando = dati.get("on", dati.get(True)) or {}
    push = quando.get("push") or {}
    assert push.get("branches") == ["dev"] and push.get("tags") == ["v*"] and "workflow_dispatch" in quando \
        and "pull_request" not in quando, f"GS13 non parte sul push a dev, sul tag v* e a mano: {quando}"
    assert dati.get("permissions") == {"contents": "read"} and "secrets." not in testo, \
        "GS13 il workflow non è in sola lettura o usa un segreto"
    assert "gate rilascio" in str(dati.get("run-name")) and "gate toccati" in str(dati.get("run-name")), \
        f"GS13 il nome della run non dice il modo: {dati.get('run-name')}"
    lavoro = (dati.get("jobs") or {}).get("gate") or {}
    assert lavoro.get("if") == "github.repository == 'stellakamikaze/arturo'", \
        f"GS13 il gate parte anche fuori dal repository pubblico: {lavoro.get('if')}"
    strategia = lavoro.get("strategy") or {}
    assert strategia.get("fail-fast") is False and sorted((strategia.get("matrix") or {}).get("os") or []) == \
        ["macos-latest", "ubuntu-latest", "windows-latest"], f"GS13 la matrice non ha i tre sistemi: {strategia}"
    parte = str((strategia.get("matrix") or {}).get("parte") or "")
    assert '["1/4","2/4","3/4","4/4"]' in parte and '["1/1"]' in parte and "ref_type == 'branch'" in parte \
        and "ARTURO_GATE_PARTE: ${{ matrix.parte }}" in testo, \
        f"GS13 il rilascio non è diviso in 4 parti per sistema, o la parte non arriva al gate: {parte!r}"
    passi = lavoro.get("steps") or []
    azioni = [p["uses"] for p in passi if "uses" in p]
    assert azioni and all(len(a.split("@")[1].split()[0]) == 40 for a in azioni), f"GS13 azioni non fissate a un commit: {azioni}"
    comandi = "\n".join(p.get("run", "") for p in passi)
    assert "ARTURO_GATE_BASE=$PRIMA" in comandi and "MODO=--toccati" in comandi and "MODO=--rilascio" in comandi \
        and 'bash tests/verifica-allineamento.sh "$MODO"' in comandi, f"GS13 il modo del gate non segue l'evento: {comandi[-600:]}"
    assert "core.autocrlf false" in comandi, "GS13 su Windows il checkout converte gli a capo e bash non legge gli script"


def test_gs14(esecutore: Path) -> None:
    with tempfile.TemporaryDirectory() as t:
        lab = Lab(Path(t), esecutore)
        liste = ("--lavori", "2", "--banchi", "ok_a.py", "ok_b.py", "rosso.py", "usa_aiuto.py",
                 "--in-fila", "casa.py", "casa2.py", "--controprove", "rosso2.py HEAD", "--veleni", "ok_a.py")
        tutti = sorted(ordine(lab.esegui(*liste).stdout))
        parti = [ordine(lab.esegui("--parte", f"{i}/3", *liste).stdout) for i in (1, 2, 3)]
        unione = sorted(x for p in parti for x in p)
        assert len(tutti) == 8 and unione == tutti, f"GS14 le parti non fanno ogni lavoro una volta sola: {parti} contro {tutti}"
        assert all(parti), f"GS14 una parte è vuota con 8 lavori e 3 parti: {parti}"
        di_nuovo = ordine(lab.esegui("--parte", "2/3", *liste).stdout)
        assert sorted(di_nuovo) == sorted(parti[1]), f"GS14 la parte 2 cambia lavori fra due lanci: {parti[1]} {di_nuovo}"
        fuori = lab.esegui("--parte", "4/3", *liste)
        assert fuori.returncode != 0 and not ordine(fuori.stdout), \
            f"GS14 la parte 4/3 non ferma il gate: rc {fuori.returncode} {fuori.stdout[-200:]!r}"


def test_gs15(esecutore: Path) -> None:
    with tempfile.TemporaryDirectory() as t:
        lab = Lab(Path(t), esecutore)
        pesi = {"banco:ok_a.py": 100, "banco:ok_b.py": 10, "banco:usa_aiuto.py": 10, "banco:aiuto.py": 10}
        (lab.root / "tests" / "gate-pesi.json").write_text(json.dumps(pesi), encoding="utf-8")
        liste = ("--banchi", "ok_a.py", "ok_b.py", "usa_aiuto.py", "aiuto.py")
        parti = [sorted(ordine(lab.esegui("--parte", f"{i}/2", *liste).stdout)) for i in (1, 2)]
        assert ["banco:ok_a.py"] in parti, f"GS15 il lavoro pesante non sta da solo nella sua parte: {parti}"
        for nome in ("test_gate_run.sh", "test_pattern_segreti_allineati.py", "test_guardie_involucri.py"):
            lab.scrivi(nome, "print('PASS')\n")
        lab.scrivi("test_nuovo.py", "print('PASS')\n")
        esiti = [lab.esegui("--elenchi", "--parte", f"{i}/2", *liste, "test_guardie_involucri.py") for i in (1, 2)]
        visti = ["test_nuovo.py: in tests/ ma in nessun elenco" in r.stdout for r in esiti]
        assert visti == [True, False] and esiti[1].returncode == 0, \
            f"GS15 il controllo degli elenchi non gira solo nella parte 1: {visti}, rc parte 2 {esiti[1].returncode}"


TESTS = {"GS01": test_gs01, "GS02": test_gs02, "GS03": test_gs03, "GS04": test_gs04, "GS05": test_gs05,
         "GS06": test_gs06, "GS07": test_gs07, "GS08": test_gs08, "GS09": test_gs09, "GS10": test_gs10,
         "GS11": test_gs11, "GS12": test_gs12, "GS13": test_gs13, "GS14": test_gs14, "GS15": test_gs15}


def avvelena(repo: Path) -> None:
    vero = esecutore_di(repo, "VELENO")
    testo = vero.read_text(encoding="utf-8")
    for codici, giusta, rotta in VELENI:
        assert testo.count(giusta) == 1, f"VELENO la riga {giusta.strip()!r} non c'è più: aggiorna VELENI"
        with tempfile.TemporaryDirectory() as t:
            rotto = Path(t) / "esegui_gate.py"
            rotto.write_text(testo.replace(giusta, rotta), encoding="utf-8")
            for codice in codici:
                try:
                    TESTS[codice](rotto)
                except Salto as s:
                    dichiara(f"veleno {codice}", s)
                    continue
                except AssertionError as e:
                    assert str(e).startswith(codice), f"VELENO {codice} rosso per un altro motivo: {e}"
                    print(f"VELENO {codice} ROSSO ({rotta.strip()}): {str(e)[:120]}")
                    continue
                raise AssertionError(f"VELENO {codice} verde con l'esecutore rotto da {rotta.strip()!r}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-ref")
    parser.add_argument("--avvelena", action="store_true")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.avvelena:
        avvelena(repo)
        return 0
    if args.baseline_ref:
        rossi, altro = [], []
        for nome, test in TESTS.items():
            try:
                test(esecutore_di(repo, nome))
            except Salto:
                rossi.append(f"{nome}: salto")
            except AssertionError as e:
                (rossi if str(e).startswith(nome) else altro).append(f"{nome}: {e}")
            except Exception as e:  # noqa: BLE001
                altro.append(f"{nome}: {type(e).__name__} {e}")
        assert not altro and len(rossi) == len(TESTS), \
            "baseline non discriminante: ogni controllo deve fallire col suo codice.\n" + "\n".join(altro + rossi)
        print(f"BASELINE_DISCRIMINANTE={','.join(r.split(':')[0] for r in rossi)}")
        return 0
    for nome, test in TESTS.items():
        try:
            test(esecutore_di(repo, nome))
        except Salto as s:
            dichiara(nome, s)
    print(f"PASS {','.join(TESTS)} controlli={len(TESTS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
