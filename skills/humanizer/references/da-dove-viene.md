# Da dove viene humanizer

Parte della skill `humanizer` (`../SKILL.md`).

Questa skill è l'adattamento italiano di [humanizer](https://github.com/blader/humanizer) di blader,
versione 4.0.0 (commit `b48c832`, 15/11/2026), con licenza MIT: la nota di copyright originale sta in
`../LICENSE`, accanto alla skill. Gli schemi dell'originale vengono da
["Signs of AI writing"](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) di Wikipedia,
curata da WikiProject AI Cleanup.

La versione inglese dell'origine sta in `originale-en.md`, accanto a questo file, e `../ORIGINE` dice a
quale commit. Quando l'origine cambia, chi mantiene Arturo la segue con `bin/humanizer-origine.py`
(`${CLAUDE_PLUGIN_ROOT}/docs/manutenzione.md`).

In Arturo cambiano cinque cose. Gli esempi sono italiani, e alcuni vengono dal catalogo dei tic che
Arturo aveva in `italiano-semplificato` (scritto da zero, ispirato a raccolte pubbliche come
[tropes.fyi](https://tropes.fyi/), che non dichiara una licenza). Il §10 parla di avverbi e aggettivi
a catena, perché le parole composte col trattino dell'originale sono un tic dell'inglese. La voce si
cerca nell'Orsa della persona (`personale/humanizer.md` e la sezione "Come scrivo" del CLAUDE.md
che scrive `/setup`), e cresce con le sue correzioni. La skill sta accanto a `italiano-semplificato`,
con i compiti divisi come dice "Tre modi di scrivere".

La quinta riguarda i fatti. Dalla 4.0.0 l'origine chiede di aggiungere un dettaglio preciso "che sai
vero" dove il testo è generico, e nei suoi esempi del §17 compaiono fatti nuovi. In Arturo resta la
regola della 3.1.0: un fatto, un nome, un numero o una fonte entrano solo se vengono dal testo o dalla
persona. Un dettaglio ricordato dal modello non ha appoggio, e in un testo che la persona firma vale
come un fatto inventato. Per lo stesso motivo il §14 e il §17 parlano ancora di ciò che dice la fonte.
