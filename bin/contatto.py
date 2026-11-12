"""arturo contatto: il nome e l'email che la persona dà agli sviluppatori di Arturo (10/11/2026).

Servono a ricontattarla quando manda una segnalazione: per chiederle un dettaglio o dirle che il problema è
risolto. Sono facoltativi e li dà la persona, una volta, dopo aver letto TESTO. Partono solo con le segnalazioni
del canale arturo (bin/segnala.py), mai con la telemetria: questo modulo non importa telemetria, e telemetria
legge di qui solo se la domanda è già stata fatta.

Il file è ~/.claude/data/contatto.json, leggibile solo dalla persona (0600), accanto alle ricevute delle
segnalazioni: la reinstallazione riporta data/ intera.

    arturo contatto                                  il contatto salvato, o che non c'è
    arturo contatto imposta --email E [--nome N]     lo salva (l'email è obbligatoria, il nome no)
    arturo contatto togli                            lo cancella da questo computer
    arturo contatto no                               la persona non vuole darlo: la domanda non torna
    arturo contatto testo                            il testo della domanda, da far leggere alla persona
    arturo contatto chiesto                          esce 0 se la domanda ha già una risposta, 3 se no

Solo libreria standard, Python 3.8 o successivo.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(os.path.realpath(__file__)).parent))
import todo_store as ts  # noqa: E402
sys.path.append(str(Path(os.path.realpath(__file__)).parent.parent / "hooks"))
from radici import radice_orsa  # noqa: E402

# La versione del testo che la persona ha letto. Se il testo cambia in ciò che promette, sale di uno.
CONSENSO = 1
TESTO = ("Vuoi lasciare agli sviluppatori di Arturo un nome e un'email? Ci servono per contattarti quando mandi "
         "una segnalazione, per chiederti un dettaglio o dirti che il problema è risolto. Partono solo con le "
         "segnalazioni, mai con i dati d'uso. Puoi cambiarli o toglierli quando vuoi con `arturo contatto`.")
# Gli stessi controlli del server (server/logica.js, validaContatto): quello che passa qui, lì si salva.
RE_EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
RE_CONTROLLO = re.compile(r"[\x00-\x1f\x7f]")
NOME_MASSIMO = 80
EMAIL_MASSIMO = 200

AIUTO = "arturo contatto: il nome e l'email per gli sviluppatori di Arturo.\n\n" + "\n".join(
    riga for riga in (__doc__ or "").splitlines() if riga.startswith("    arturo contatto"))


def file_contatto() -> Path:
    return radice_orsa() / "data" / "contatto.json"


def _leggi() -> dict:
    """Un file assente o rotto vale {}: la domanda torna, niente parte."""
    try:
        grezzo = json.loads(file_contatto().read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        return {}
    return grezzo if isinstance(grezzo, dict) else {}


def errore_contatto(nome: str, email: str) -> str:
    """Il motivo per cui il contatto non vale, o "" se vale."""
    if not email or len(email) > EMAIL_MASSIMO or not RE_EMAIL.match(email):
        return "l'email non sembra un indirizzo valido"
    if len(nome) > NOME_MASSIMO:
        return f"il nome supera {NOME_MASSIMO} caratteri"
    if RE_CONTROLLO.search(nome):
        return "il nome contiene un a capo o un carattere di controllo"
    return ""


def contatto():
    """{"nome", "email"} se la persona l'ha dato e vale, altrimenti None."""
    dati = _leggi()
    nome = dati.get("nome").strip() if isinstance(dati.get("nome"), str) else ""
    email = dati.get("email").strip() if isinstance(dati.get("email"), str) else ""
    if errore_contatto(nome, email):
        return None
    return {"nome": nome, "email": email}


def chiesto() -> bool:
    """Vero se la persona ha risposto alla domanda, col sì (un contatto) o col no."""
    dati = _leggi()
    return contatto() is not None or isinstance(dati.get("rifiutato"), str)


def _scrivi(dati: dict) -> None:
    percorso = file_contatto()
    with ts.Lucchetto(percorso):
        ts.scrivi_json_atomico(percorso, dati)
    try:
        os.chmod(percorso, 0o600)
    except OSError:
        pass


def imposta(nome: str, email: str) -> str:
    nome, email = (nome or "").strip(), (email or "").strip()
    errore = errore_contatto(nome, email)
    if errore:
        return errore
    _scrivi({"nome": nome, "email": email, "data": ts.oggi().isoformat(), "consenso": CONSENSO})
    return ""


def togli() -> None:
    """Nome ed email se ne vanno dal file. Resta la sola data del no, così la domanda non torna."""
    rifiuta()


def rifiuta() -> None:
    _scrivi({"rifiutato": ts.oggi().isoformat(), "consenso": CONSENSO})


def riga_domanda() -> str:
    """La riga per Claude quando la domanda non ha ancora risposta: avvio e /segnala la stampano."""
    return ("CONTATTO: la persona non ha ancora detto se vuole lasciare un nome e un'email agli sviluppatori di Arturo. "
            f"Chiediglielo una volta, con queste parole: \"{TESTO}\" Con un sì: arturo contatto imposta --nome "
            "\"<nome>\" --email \"<email>\". Con un no: arturo contatto no.")


def riga_avvio() -> str:
    """Una volta sola per installazione: la riga di avvio non torna, anche se la persona non risponde.
    La domanda la ripetono /setup e /segnala, finché non c'è una risposta."""
    dati = _leggi()
    if chiesto() or isinstance(dati.get("avvisato"), str):
        return ""
    try:
        _scrivi(dict(dati, avvisato=ts.oggi().isoformat()))
    except OSError:
        return ""
    return riga_domanda()


def _descrivi(c) -> str:
    if not c:
        return ""
    return f"{c['nome']} <{c['email']}>" if c["nome"] else c["email"]


def main(argv: list) -> int:
    if argv and argv[0] in ("-h", "--help", "aiuto", "help"):
        print(AIUTO)
        return 0
    comando, resto = (argv[0], argv[1:]) if argv else ("mostra", [])
    if comando == "mostra" and not resto:
        c = contatto()
        if c:
            print(f"Contatto per gli sviluppatori di Arturo: {_descrivi(c)}\n"
                  "Parte solo con le segnalazioni. Si toglie con: arturo contatto togli")
        elif isinstance(_leggi().get("rifiutato"), str):
            print("Nessun contatto: hai scelto di non lasciarlo. Le segnalazioni partono senza.")
        else:
            print("Nessun contatto salvato. Le segnalazioni partono senza.")
        return 0
    if comando == "imposta":
        opz, i = {}, 0
        while i < len(resto):
            chiave = resto[i]
            if "=" in chiave and chiave.split("=", 1)[0] in ("--nome", "--email"):
                k, v = chiave.split("=", 1)
                opz[k] = v
                i += 1
            elif chiave in ("--nome", "--email") and i + 1 < len(resto):
                opz[chiave] = resto[i + 1]
                i += 2
            else:
                print(f"Errore: opzione sconosciuta o senza valore: \"{chiave}\"\n\n{AIUTO}", file=sys.stderr)
                return 2
        errore = imposta(opz.get("--nome", ""), opz.get("--email", ""))
        if errore:
            print(f"Errore: {errore}. Niente è stato salvato.", file=sys.stderr)
            return 2
        print(f"Salvato: {_descrivi(contatto())}. Parte con le prossime segnalazioni, "
              "e gli sviluppatori di Arturo lo usano solo per risponderti.")
        return 0
    if comando == "togli" and not resto:
        togli()
        print("Contatto tolto da questo computer. Le segnalazioni già partite lo tengono sul server: "
              "si cancella col ritiro della segnalazione (arturo segnala ritira N).")
        return 0
    if comando == "no" and not resto:
        rifiuta()
        print("Va bene: nessun contatto, e la domanda non torna. Se cambi idea: arturo contatto imposta.")
        return 0
    if comando == "testo" and not resto:
        print(TESTO)
        return 0
    if comando == "chiesto" and not resto:
        return 0 if chiesto() else 3
    print(f"Errore: comando sconosciuto: \"{' '.join(argv)}\"\n\n{AIUTO}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
