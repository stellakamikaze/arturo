# Come è fatto Arturo, e da cosa dipende

Arturo sta in mezzo fra te e il modello. Sopra c'è la tua Orsa, la parte della configurazione che è
tua; sotto ci sono Claude Code e il modello di Anthropic. Dentro Arturo alcune skill vengono da
progetti aperti di altre persone, adattati e citati; altri progetti Arturo te li consiglia, e li
installi dalla loro fonte. Questa pagina li mette tutti in fila, con chi li aggiorna.

Il disegno ha due assi. I riquadri dicono di chi è ogni parte: tua, di Arturo, di Anthropic. Le righe
numerate dicono cosa fa per te, in sei strati: le fondamenta (1), il lavoro di ogni giorno (2-4) e la
crescita (5-6). Il contratto dei due assi sta in [`strati.md`](strati.md). È l'unico disegno di Arturo:
il README e `strati.md` lo citano senza copiarlo.

```diagramma
  tu
   │  chiedi, correggi, scrivi come scrivi
   ▼
┌─ Orsa ─────────────── ~/.claude, è tua: gli aggiornamenti non la toccano ─┐
│  6 Orsa: CLAUDE.md · personale/<skill>.md · memoria · todo · handoff      │
│  la tua voce: "Come scrivo" nel CLAUDE.md + personale/humanizer.md        │
│  cresce con le correzioni e con le proposte della Scoperta, col tuo sì    │
└──────────────────────────────────┬────────────────────────────────────────┘
                                   │ Arturo la legge e la rispetta
┌─ Arturo ─────────────── lo aggiorna chi lo mantiene, con rilasci firmati ─┐
│  cosa fa per te, dalle fondamenta alla crescita:                          │
│    1 Protezione .......... guardie che chiedono un sì, segreti fermati    │
│    2 Metodo .............. brief, freni, fatto vuol dire verificato       │
│    3 Memoria ............. /inizio, /fine, handoff, todo, Melchior        │
│    4 Collegamenti ........ posta, agenda, documenti, pagine web           │
│    5 Scoperta ............ ti propone cosa automatizzare, con le prove    │
│    sempre: Ingresso (/setup, aggiornamenti) · Misura (banchi, /segnala)   │
│                                                                           │
│  adattati da progetti aperti, dentro Arturo:                              │
│    humanizer ............. ◄── blader/humanizer (MIT)                     │
│    italiano-semplificato . ◄── ASD-STE100 via AminBlg/SimpleEnglish (MIT) │
│    prompt-master ......... ◄── nidhinjs/prompt-master (MIT)               │
│    intervista e deleghe .. ◄── mattpocock/skills (MIT)                    │
│                                                                           │
│  consigliati, li installi dalla loro fonte:                               │
│    Impeccable ............ ◄── pbakaus/impeccable (Apache-2.0)            │
│    Hallmark .............. ◄── Nutlope/hallmark (MIT)                     │
│    diagram-design ........ ◄── cathrynlavery/diagram-design (MIT)         │
│    scrape ................ ◄── D4Vinci/Scrapling (BSD-3)                  │
└──────────────────────────────────┬────────────────────────────────────────┘
                                   │ hook, skill, comandi, permessi
┌─ Claude Code ───────────────────────────────── di Anthropic, a pagamento ─┐
│  il programma nel terminale: legge e scrive i file, lancia i comandi      │
└──────────────────────────────────┬────────────────────────────────────────┘
                                   │ la conversazione esce dal tuo computer
                       il modello (Claude, sui server di Anthropic)
```

## Chi aggiorna cosa

| Progetto | Cosa fa per te | Licenza | Come arriva | Chi lo aggiorna |
|---|---|---|---|---|
| Claude Code | il programma su cui gira tutto | proprietaria, di Anthropic | lo installi tu | Anthropic, da solo |
| Arturo | guardie, metodo, comandi, skill | MIT | `installa.sh`, poi i rilasci firmati | chi mantiene Arturo; si installa da solo alla chiusura della sessione |
| Orsa | le tue istruzioni, la tua voce, la tua memoria | tua | la scrivi tu, con Claude | tu, solo tu |
| humanizer | toglie i tic da IA dalla prosa, seguendo la tua voce | MIT | dentro Arturo, adattato in italiano; l'originale inglese accanto | chi mantiene Arturo segue [blader/humanizer](https://github.com/blader/humanizer) e porta le versioni nuove in inglese e in italiano |
| italiano-semplificato | rende chiaro un testo tecnico | MIT | dentro Arturo | chi mantiene Arturo |
| prompt-master | riscrive la tua richiesta prima del lavoro | MIT | dentro Arturo, riscritto | chi mantiene Arturo, a mano dall'origine |
| mattpocock/skills | le domande a giri, le cose da delegare, la procedura guidata e la rispiegazione | MIT | dentro Arturo, riscritto in prompt-master, `/guidami`, lo stile Conciso e `shared/procedura-guidata.sh` | chi mantiene Arturo, a mano dall'origine |
| Impeccable | design delle interfacce | Apache-2.0 | `/setup`, fase 8c ([`impeccable.md`](impeccable.md)) | `npx impeccable update` |
| Hallmark | pagine nuove che non sembrano generate | MIT | `/setup`, fase 8c ([`hallmark.md`](hallmark.md)) | si reinstalla dalla fonte |
| diagram-design | diagrammi editoriali in HTML e SVG | MIT | dalla fonte ([`diagram-design.md`](diagram-design.md)) | il plugin, con l'aggiornamento automatico acceso |
| scrape | legge una pagina web senza browser | BSD-3 | `/setup`, facoltativo | `tools/scrapling/setup.sh` |

## Scrivere: tre lavori, tre posti

Quando scrivi con Claude entrano tre cose diverse, e ognuna ha il suo posto. Il testo tecnico (un
manuale, un messaggio d'errore, un'istruzione) segue `italiano-semplificato`, che lo rende chiaro.
La prosa (un post, un'email, una proposta) segue la tua voce, che sta nella tua Orsa. `humanizer`
toglie dalla prosa i segni della scrittura da IA, e dove la tua voce e una sua regola litigano vince
la tua voce. Il diagramma sta in `skills/humanizer/SKILL.md`, sezione "Tre modi di scrivere".

La tua voce cresce con l'uso: quando correggi un testo riscritto, Claude ti propone di aggiungere la
correzione a `~/.claude/personale/humanizer.md`, e la scrive solo col tuo sì.
