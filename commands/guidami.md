---
description: Guarda gli ultimi handoff e le conversazioni recenti e propone il lavoro che ha senso fare adesso, con il motivo e il primo passo
argument-hint: "[progetto o tema] (opzionale)"
---

# Guidami

Chi ti parla riapre Claude Code e non sa da dove ripartire. Il tuo compito è **proporgli lavoro
vero**: non un riassunto di quello che ha fatto, ma tre o quattro cose che ha senso fare adesso,
ciascuna con il motivo e un primo passo piccolo.

Chi ti parla **potrebbe non essere una persona tecnica**. Niente gergo, niente elenchi di file.

## Argomento

**$ARGUMENTS**

- Se è il nome di un progetto o un tema, guarda solo lì.
- Se è vuoto, guarda tutto quello che trovi e scegli tu su cosa vale la pena tornare.

---

## Passo 1 — Raccogli i segnali

Due fonti, in quest'ordine. Nessuna delle due è obbligatoria: se una manca, lavora con l'altra e
dillo.

**Gli handoff** — le note di chiusura che `/fine` lascia a fine sessione:

```bash
ls -t ~/.claude/data/handoffs/*/HANDOFF_*.md 2>/dev/null | head -8
cat ~/.claude/data/handoffs/INDEX.md 2>/dev/null
```

Leggi i più recenti per intero, non solo il titolo. La tabella `## Task Pendenti`, dove c'è, è il
segnale più forte: è lavoro che una persona ha deciso di lasciare aperto.

**Le conversazioni recenti** — cosa è stato chiesto davvero nelle ultime sessioni:

```bash
python3 - <<'PY'
import json, pathlib, time
base = pathlib.Path.home() / ".claude" / "projects"
files = sorted(base.glob("*/*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)[:6]
for f in files:
    eta = (time.time() - f.stat().st_mtime) / 86400
    richieste = []
    for riga in f.open(encoding="utf-8", errors="replace"):
        try:
            voce = json.loads(riga)
        except ValueError:
            continue
        if voce.get("type") != "user":
            continue
        testo = voce.get("message", {}).get("content")
        # Le stringhe che iniziano con '<' sono promemoria di sistema, non parole dell'utente.
        if isinstance(testo, str) and testo.strip() and not testo.lstrip().startswith("<"):
            richieste.append(" ".join(testo.split())[:160])
    if richieste:
        print(f"\n=== {f.parent.name}  ({eta:.0f} giorni fa, {len(richieste)} richieste)")
        for r in richieste[-6:]:
            print("  -", r)
PY
```

Il nome della cartella è il percorso del progetto con i trattini al posto delle barre: ti dice su
cosa stava lavorando.

## Passo 2 — Scarta quello che è già fatto

Una cosa lasciata aperta in un handoff può essere stata chiusa il giorno dopo. Prima di proporla,
guarda la storia del progetto:

```bash
git -C <cartella-del-progetto> log --oneline -20
```

Se il lavoro è nei commit, non riproporlo. Questo passo è la differenza tra una proposta utile e
una lista che fa perdere tempo.

## Passo 3 — Proponi

Da tre a cinque voci, non di più. Per ognuna, tre righe:

- **Cosa**: l'azione, con un verbo concreto.
- **Perché adesso**: il motivo vero — è fermo da giorni, ne dipende altro, c'è una scadenza, era
  quasi finito. Cita da dove viene («l'handoff del 12 lo lasciava aperto», «l'hai chiesto due
  sessioni fa e non è mai partito»).
- **Primo passo**: una cosa piccola e reversibile, non il progetto intero.

Ordina per quello che sbloccherebbe di più, non per data.

Chiudi con un menu che gli fa scegliere da dove partire, e **se sceglie, parti davvero**: apri il
progetto e fai il primo passo.

---

## Freni

- **Proponi, non eseguire.** Finché non sceglie, non tocchi file e non lanci niente che cambi
  qualcosa. Leggere va bene.
- **Niente proposte inventate.** Ogni voce nasce da un handoff, da una conversazione o dalla storia
  del progetto. Se i segnali sono pochi, proponi due cose e dillo: «ho trovato poco, è tutto qui».
  Riempire la lista per farla sembrare piena è il modo più veloce di rendere inutile questo comando.
- **Se non trovi niente**, dillo in una riga e chiedi su cosa sta lavorando. Non è un errore: vuol
  dire che è la prima volta, o che ha chiuso tutto.
- **Le conversazioni sono materiale privato.** Le leggi per proporre lavoro a chi le ha scritte, non
  le riassumi altrove e non le mandi da nessuna parte.
