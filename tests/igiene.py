#!/usr/bin/env python3
"""I03: nel repository pubblico non compaiono i nomi della config privata dell'autore (17/10/2026, #3505).

Fino al 16/10/2026 i nomi stavano nei test spezzati in due ("xx", "yy"): le due metà erano leggibili, e
bastava rimetterle insieme. Qui ci sono solo le impronte sha256 dei termini normalizzati. Nessun nome e
nessuna sua metà resta in chiaro, neanche in questo file.

Un termine si normalizza così: NFKC, i confusabili comuni (cirillico e greco che sembrano latino)
portati al latino, minuscole, e via tutto ciò che non è una lettera o una cifra. Il testo si legge a
gettoni: i tratti di lettere e cifre, spezzati anche fra minuscola e maiuscola e fra lettera e cifra.
Ogni finestra di gettoni consecutivi, unita, si confronta con le impronte. Così il controllo regge al
punto in mezzo, all'a capo dopo un trattino, al carattere invisibile, al cirillico e allo spazio.

Si controllano il contenuto e il percorso di ogni file del repository, e i messaggi dei commit
dell'intervallo che si pubblica: per default i commit che nessun remoto conosce ancora.

  python3 tests/igiene.py --repo . [--intervallo A..B]
  python3 tests/igiene.py --impronta < termine.txt     l'impronta di un termine nuovo, letto da stdin

Un termine nuovo entra solo come impronta, in uno degli elenchi qui sotto: il termine in chiaro non va
scritto in nessun file del repository, né sulla riga di comando.

Esce con 0 se è pulito, con 1 se trova qualcosa. Il rapporto dice dove e l'inizio dell'impronta, mai il
termine: un log pubblico (GitHub Actions) non lo ripete. Solo libreria standard, Python 3.8 o successivo.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

# I confusabili più comuni: lettere cirilliche e greche che a occhio sono latine.
CONFUSABILI = str.maketrans({
    "а": "a", "в": "b", "е": "e", "ё": "e", "к": "k", "м": "m", "н": "h", "о": "o", "р": "p", "с": "c", "т": "t",
    "у": "y", "х": "x", "ѕ": "s", "і": "i", "ї": "i", "ј": "j", "ԁ": "d", "ԛ": "q", "ԝ": "w", "ɡ": "g", "һ": "h",
    "ӏ": "l", "ո": "n", "ս": "u",
    "А": "A", "В": "B", "Е": "E", "Ё": "E", "К": "K", "М": "M", "Н": "H", "О": "O", "Р": "P", "С": "C", "Т": "T",
    "У": "Y", "Х": "X", "Ѕ": "S", "І": "I", "Ї": "I", "Ј": "J", "Ԛ": "Q", "Ԝ": "W",
    "α": "a", "ε": "e", "ι": "i", "κ": "k", "ν": "v", "ο": "o", "ρ": "p", "τ": "t", "υ": "u", "χ": "x",
    "Α": "A", "Β": "B", "Ε": "E", "Ζ": "Z", "Η": "H", "Ι": "I", "Κ": "K", "Μ": "M", "Ν": "N", "Ο": "O", "Ρ": "P",
    "Τ": "T", "Υ": "Y", "Χ": "X",
})
MASSIMO = 24  # caratteri: nessun termine normalizzato è più lungo
_TRATTO = re.compile(r"[^\W_]+")
_CONFINE = re.compile(r"(?<=[a-z])(?=[A-Z])|(?<=[^\W\d_])(?=\d)|(?<=\d)(?=[^\W\d_])")

# I nomi della config dell'autore e dei suoi servizi: in nessun file, percorso o messaggio di commit.
# Dal 20/10/2026 il nome della memoria (Melchior) non è più fra questi: Arturo usa la stessa memoria
# della config, con gli stessi file (hooks/melchior_match.py). Resta in FINE: /fine non lo nomina.
GLOBALE = frozenset((
    "2055c47117d5b5e12671b864e7c3b42633d03115cd43dda6c6af38a4e734e0c9",
    "238195c30e42765ff5a88b6d855b207dd34958d602d05a94327338cbabb89b1f",
    "2bf548d8056029c73e6e28132d19a3a277a49daf32b1c1ba7b0b7fc7e78bf5cd",
    "2f968f650a0ddcb1aff098dd009f7a161c247710277f77de40d9192006a546f3",
    "42885d9347f0ea78e7d0a2cd4762abe1a5673ac241af632b283c602b1b61f604",
    "636c4c36231a1a8fdbb701b65180832f12c8a5b11eb6788af990ae3304de6152",
    "657cd4d68c6a6e51740f32894b11446e720096f954c4faa6b7bdb708e4b8e215",
    "67f2d22514622d1be30c14ee9f3cb104503a159a33a656ca91a1953aa9616429",
    "9b26c65fe33bf161eea7edd9f1e361783a2ee985b8d5036ddc5b6029f957cd0d",
    "a80c03a36280a2d3b7cf58396e853c93c8ab5c52fef47fbaabff3bb09a319d88",
    "a998e1435e5b2c69883a2864415916ab5d95659864ab13be1748ec8a1cecb0d8",
    "ce5d15cebdd978a2f8bd164613a609fca32c6e0161a83199c2162429a09790b8",
    "d307be7d14339b3cc82cdfce1a991e744551113c287c48501569d82b7a4a64e1",
    "ec8f69a31cf186ac13ebc131ed2c602c8af6b9270235b1329d7ca47e6e98e679",
))
# Termini che, con le due parti staccate da uno spazio, sono un comando pubblico e lecito (una CLI col
# suo sottocomando): contano solo uniti, anche da un punto, un trattino o un carattere invisibile.
UNITI_SOLO = frozenset((
    "a998e1435e5b2c69883a2864415916ab5d95659864ab13be1748ec8a1cecb0d8",
))
# In più, per i mod e le skill portati dalla config dell'autore (test_mod_skill.py, Q04): le persone,
# le macchine e gli account.
AUTORE = frozenset((
    "0b8ba6f88c10056cd2ccca572dc2cfa1f9b5a7bd1500dd1593d755effabeb4c5",
    "0ce93c9606f0685bf60e051265891d256381f639d05c0aec67c84eec49d33cc1",
    "16e5f60f207a1a0073451c35a9d315d17fdc17d7fab66449b00cdfaadc8b249e",
    "1a9f445a124c9e63a407e54ff13bc4c2cd05068d174e34eaec7ab1a06acc71ed",
    "2f968f650a0ddcb1aff098dd009f7a161c247710277f77de40d9192006a546f3",
    "42885d9347f0ea78e7d0a2cd4762abe1a5673ac241af632b283c602b1b61f604",
    "4843e3251481eb031344d09bf797ccc8b21eafd3b02c7377ba5c72fd1250d27c",
    "8faa5f1589ae2a5e1845e7cb2f913d8ca301decb3f8dd543a79248d2efe548be",
    "a80c03a36280a2d3b7cf58396e853c93c8ab5c52fef47fbaabff3bb09a319d88",
    "a998e1435e5b2c69883a2864415916ab5d95659864ab13be1748ec8a1cecb0d8",
    "c10e16860a91658071ffa19458d439999cc60e5a95bc1d045787c0d80ce99145",
    "cd71fa4239dac4232ed0f85d682be555798551f732d1cf655f65f86884121fe4",
    "cdee64b7f3cee407e52c7ca5c6aebea8c0504f9a299aca66b205cfd8775392b3",
    "ce055f86c0723d63ae415eeaa0beb821718d1032d147f3f46f631c0de3d2c703",
    "ec8f69a31cf186ac13ebc131ed2c602c8af6b9270235b1329d7ca47e6e98e679",
    "ff5844775d0f0efb0509128746c666c17623f7ac702460ef7d164907d30b498c",
))
# Il pannello /dafare (test_pannello.py, U06).
PANNELLO = frozenset((
    "1450afdceec1946e8291244c60a72009aba077b7ef627414b907762c505538b8",
    "238195c30e42765ff5a88b6d855b207dd34958d602d05a94327338cbabb89b1f",
    "42885d9347f0ea78e7d0a2cd4762abe1a5673ac241af632b283c602b1b61f604",
    "cd71fa4239dac4232ed0f85d682be555798551f732d1cf655f65f86884121fe4",
    "ec8f69a31cf186ac13ebc131ed2c602c8af6b9270235b1329d7ca47e6e98e679",
))
# /fine non nomina gli strumenti della config dell'autore (test_fine_inizio.py, F08).
FINE = frozenset((
    "0a557ec4275bc1d93c8959c5432ac475a2653dc38bb457815a2a5c50ff4d09b2",
    "1450afdceec1946e8291244c60a72009aba077b7ef627414b907762c505538b8",
    "42885d9347f0ea78e7d0a2cd4762abe1a5673ac241af632b283c602b1b61f604",
    "c84ae2ab912bc26b22e566d70ca7cc102ff40bcece20ff0a811d161a1abaaabe",
))


def normalizza(testo: str) -> str:
    t = unicodedata.normalize("NFKC", testo).translate(CONFUSABILI).lower()
    return "".join(c for c in t if c.isalnum())


def impronta(termine: str) -> str:
    return hashlib.sha256(normalizza(termine).encode("utf-8")).hexdigest()


def gettoni(testo: str) -> List[Tuple[str, int, str]]:
    """(gettone, riga, separatore prima) per ogni tratto di lettere e cifre, spezzato anche fra
    minuscola e maiuscola e fra lettera e cifra. Il separatore è il testo fra il gettone di prima e
    questo: vuoto dentro un tratto, uno spazio, un punto, un a capo, un carattere invisibile."""
    t = unicodedata.normalize("NFKC", testo).translate(CONFUSABILI)
    fuori, riga, fine = [], 1, 0
    for m in _TRATTO.finditer(t):
        separatore = t[fine:m.start()]
        riga += separatore.count("\n")
        for pezzo in _CONFINE.split(m.group()):
            if pezzo:
                fuori.append((pezzo.lower(), riga, separatore))
                separatore = ""
        fine = m.end()
    return fuori


def trova(testo: str, impronte: Iterable[str]) -> List[Tuple[int, str]]:
    """(riga, inizio dell'impronta) per ogni finestra di gettoni che, unita, è uno dei termini. Per i
    termini di UNITI_SOLO una finestra con uno spazio o un a capo fra i gettoni non conta."""
    cercate = frozenset(impronte)
    g = gettoni(testo)
    trovati = []
    for i in range(len(g)):
        unito, spazio = "", False
        for j in range(i, len(g)):
            unito += g[j][0]
            if len(unito) > MASSIMO:
                break
            if j > i and any(c.isspace() for c in g[j][2]):
                spazio = True
            h = hashlib.sha256(unito.encode("utf-8")).hexdigest()
            if h in cercate and not (spazio and h in UNITI_SOLO):
                trovati.append((g[i][1], h[:12]))
                break
    return trovati


def _git(repo: Path, *argomenti: str) -> bytes:
    return subprocess.run(["git", "-C", str(repo), *argomenti], capture_output=True, check=True, timeout=60).stdout


def messaggi(repo: Path, intervallo: Optional[str]) -> List[Tuple[str, str]]:
    """(commit, messaggio) dell'intervallo. Senza intervallo: i commit che nessun remoto conosce."""
    selezione = [intervallo] if intervallo else ["HEAD", "--not", "--remotes"]
    uscita = _git(repo, "log", "--format=%h%x00%B%x00", *selezione).decode("utf-8", "replace")
    parti = uscita.split("\0")
    return [(parti[k].strip(), parti[k + 1]) for k in range(0, len(parti) - 1, 2)]


def file_del_repository(repo: Path) -> List[str]:
    """I file che git pubblicherebbe. Fuori da un repository git (una base estratta con git archive)
    tutti i file della cartella."""
    if (repo / ".git").exists():
        elenco = _git(repo, "ls-files", "--cached", "--others", "--exclude-standard", "-z").decode("utf-8", "replace")
        return [x for x in elenco.split("\0") if x]
    return sorted(p.relative_to(repo).as_posix() for p in repo.rglob("*") if p.is_file())


def controlla(repo: Path, intervallo: Optional[str] = None, impronte: Iterable[str] = GLOBALE) -> List[str]:
    """Contenuto e percorso dei file, e messaggi dei commit dell'intervallo (solo in un repository git)."""
    impronte = frozenset(impronte)
    if intervallo and not (repo / ".git").exists():
        raise SystemExit(f"I03 igiene: {repo} non è un repository git, l'intervallo {intervallo} non si controlla")
    problemi = []
    for nome in file_del_repository(repo):
        for _, h in trova(nome, impronte):
            problemi.append(f"percorso {nome} ({h})")
        f = repo / nome
        if not f.is_file():
            continue
        for riga, h in trova(f.read_text(encoding="utf-8", errors="replace"), impronte):
            problemi.append(f"{nome}:{riga} ({h})")
    for commit, testo in (messaggi(repo, intervallo) if (repo / ".git").exists() else []):
        for riga, h in trova(testo, impronte):
            problemi.append(f"commit {commit}, riga {riga} del messaggio ({h})")
    return problemi


def main() -> int:
    parser = argparse.ArgumentParser(description="Igiene del repository pubblico (I03)")
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--intervallo", help="i commit da controllare, per esempio A..B; di default quelli non ancora su un remoto")
    parser.add_argument("--impronta", action="store_true", help="stampa l'impronta del termine letto da stdin")
    args = parser.parse_args()
    for flusso in (sys.stdin, sys.stdout, sys.stderr):
        try:
            flusso.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    if args.impronta:
        print(impronta(sys.stdin.read().strip()))
        return 0
    problemi = controlla(args.repo.resolve(), args.intervallo)
    if problemi:
        print("I03 igiene: nomi della config privata nel repository pubblico:\n  " + "\n  ".join(problemi), file=sys.stderr)
        return 1
    print("I03 igiene: pulito")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
