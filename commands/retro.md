---
description: Retrospettiva engineering - analisi commit, pattern di lavoro, metriche
argument-hint: "[7d|14d|30d|24h|compare] (default: 7d)"
allowed-tools: Bash(git:*), Bash(gh:*)
---

# Retrospettiva Engineering

Genera una retrospettiva completa analizzando commit history, pattern di lavoro e metriche di qualità.

## Argomenti

**$ARGUMENTS** (default: 7d)

Formati accettati:
- `/retro` — ultimi 7 giorni
- `/retro 24h` — ultime 24 ore
- `/retro 14d` — ultimi 14 giorni
- `/retro 30d` — ultimi 30 giorni
- `/retro compare` — confronta periodo corrente vs precedente

---

## Step 1: Raccogli Dati

Prima rileva il branch default:
```bash
DEFAULT=$(gh repo view --json defaultBranchRef -q .defaultBranchRef.name 2>/dev/null || echo "main")
git fetch origin $DEFAULT --quiet
git config user.name
```

Esegui **in parallelo**:

```bash
# 1. Commit con statistiche
git log origin/$DEFAULT --since="<window>" --format="%H|%aN|%ae|%ai|%s" --shortstat

# 2. Test vs production LOC
git log origin/$DEFAULT --since="<window>" --format="COMMIT:%H|%aN" --numstat

# 3. Timestamp per session detection
git log origin/$DEFAULT --since="<window>" --format="%at|%aN|%ai|%s" | sort -n

# 4. File hotspot
git log origin/$DEFAULT --since="<window>" --format="" --name-only | grep -v '^$' | sort | uniq -c | sort -rn

# 5. Commit count per autore
git shortlog origin/$DEFAULT --since="<window>" -sn --no-merges
```

---

## Step 2: Obiettivi di Analisi

Dai dati grezzi ricava una lettura onesta del periodo. Non c'è una sequenza
obbligatoria né una lista fissa di metriche: guarda cosa questi commit dicono
davvero e scegli profondità e tagli rilevanti al caso. Le dimensioni sotto sono
le domande utili — coprine quelle che aggiungono segnale, salta quelle piatte.

- **Volume e forma del lavoro**: quanti commit, LOC nette, quota test, contributors,
  giorni attivi. Presenta i numeri che raccontano qualcosa (tabella markdown va bene).
- **Ritmo temporale**: ore di picco, zone morte, pattern bimodale vs continuo,
  cluster notturni. Un istogramma ASCII delle ore aiuta se il pattern è marcato.
- **Sessioni**: raggruppa i commit in sessioni di lavoro (un gap di ~45 min tra
  commit consecutivi è un separatore ragionevole — adattalo se il progetto ha un
  ritmo diverso) e leggi la loro intensità (deep / media / micro), il tempo attivo,
  la densità LOC/ora. Sono stime, trattale come tali.
- **Mix di commit**: distribuzione feat/fix/refactor/test/chore/docs. Una quota fix
  molto alta suggerisce un pattern "ship fast, fix fast" — segnalalo come ipotesi,
  non come verdetto, e solo se i numeri lo reggono.
- **Hotspot e churn**: file toccati ripetutamente, concentrazione in poche directory,
  bilancio test vs produzione. Segnala i churn hotspot che meritano attenzione.
- **Focus vs context-switching**: quanto il lavoro si concentra in un'area vs si
  disperde. Evidenzia il "ship" più significativo del periodo e perché conta.
- **Streak**: giorni consecutivi con almeno un commit, se è un segnale motivante.

```bash
# Streak (giorni consecutivi con commit)
git log origin/$DEFAULT --format="%ad" --date=format:"%Y-%m-%d" | sort -u
```

**Trend**: se esistono retro precedenti, confronta e calcola i delta sulle metriche
che hai scelto di tracciare — le regressioni e i miglioramenti valgono più dei valori
assoluti.

```bash
ls -t .context/retros/*.json 2>/dev/null | head -1
```

---

## Step 3: Salva Snapshot

```bash
mkdir -p .context/retros
```

Salva in `.context/retros/` e aggiungi `.context/` al `.gitignore` se non già presente:

```bash
if ! grep -q "^\.context/" .gitignore 2>/dev/null; then
  echo ".context/" >> .gitignore
fi
```

Salva JSON con schema: date, window, metrics (commits, insertions, deletions, test_ratio, sessions, deep_sessions, loc_per_hour, feat_pct, fix_pct, peak_hour).

---

## Step 4: Narrativa

L'output è una retrospettiva leggibile, non un dump di numeri. Apri con una riga
sintetica "tweetable" che cattura il periodo, poi costruisci la narrativa
intrecciando i segnali che hai trovato. Copertura tipica — adatta ordine e presenza
di ciascuna sezione a ciò che i dati hanno davvero da dire:

```
Settimana del 10 Mar: 47 commit, 3.2k LOC, 38% test, picco: 22:00 | Streak: 32d
```

- Metriche di sintesi e trend vs l'ultima retro (se disponibile)
- Pattern temporali e sessioni — interpretazione, non solo conteggi
- Velocità di shipping — mix commit, disciplina sulla dimensione dei PR
- Segnali di qualità — quota test, hotspot, churn
- Focus e highlight del periodo
- **Cosa è andato bene** — poche cose specifiche, ancorate a commit reali
- **Dove migliorare** — uno-due suggerimenti concreti e azionabili
- **Abitudini per il prossimo periodo** — piccole, pratiche, realistiche

---

## Compare Mode

Quando `/retro compare`:
1. Metriche finestra corrente
2. Metriche finestra precedente (stessa lunghezza)
3. Tabella confronto side-by-side con delta e frecce
4. Narrativa su miglioramenti e regressioni principali

---

## Tono

- Incoraggiante ma onesto
- Specifico e concreto — sempre ancorato a commit reali
- Salta lodi generiche ("bel lavoro!") — dì esattamente cosa era buono
- Miglioramenti come investimento, non critica
- Lunghezza proporzionata al periodo: abbastanza da dire tutto, senza riempitivo
- Tabelle markdown e code block per dati, prosa per narrativa
