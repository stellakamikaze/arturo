// Il recap del mattino e il riepilogo del lunedì in HTML, con le righe "da fare" che diventano task (5/11/2026, #4810).
// Federico: il recap "deve far capire quanto e come Arturo è usato". Prima era il muro di testo di testoRiepilogo, con
// le righe a zero ("nessuna") più numerose di quelle piene. Qui una riga a zero sparisce, e il suo nome va nel piede.
// Il testo semplice resta in logica.js (testoRiepilogo), con in testa le righe di righeGiorno.
import { LIMITI, task, idCorto, derivaPubblica, derivaInBreve } from "./logica.js";
import { pagina, sezione, tabella, cifre, elenco, paragrafo, codice, crudo, esc } from "./email.js";

const corto = (id) => (id || "").slice(0, 8);
const per = (a, b) => (b ? `${Math.round((100 * a) / b)}%` : "-");
const uno = (n, singolare, plurale) => `${n} ${n === 1 ? singolare : plurale}`;
const media = (x) => (Math.round(x * 10) / 10).toString().replace(".", ",");
const DIECI = 10;
// Il recap conta gli eventi arrivati prima del cron delle 6 UTC (finding 46): il client li manda alla sessione dopo, al
// massimo ogni 6 ore, e le sessioni della sera di solito arrivano il mattino dopo, a recap partito. Il lunedì le conta.
const ARRIVATI = "Conta gli eventi arrivati prima delle 7 (le 8 con l'ora legale): le sessioni della sera spesso arrivano dopo, e le conta il riepilogo del lunedì.";

// Il giorno "2026-11-04" come "4/11".
const breve = (giorno) => `${Number(giorno.slice(8, 10))}/${Number(giorno.slice(5, 7))}`;

// Un'impronta corta e stabile di un elenco: la stessa deriva dà sempre lo stesso task, anche fra giorni e settimane.
function impronta(valori) {
  let h = 5381;
  for (const c of valori.slice().sort().join("|")) h = ((h * 33) ^ c.charCodeAt(0)) >>> 0;
  return h.toString(36);
}

// L'id corto di un'installazione, come lo legge chi mantiene Arturo: i nomi non stanno nel Worker (finding 39).
const chi = (installazione) => codice(idCorto(installazione));

// Le installazioni con una deriva che ostacola: hook spenti, guardie modificate, aggiornamento in conflitto. I valori
// passano dagli elenchi chiusi anche qui: le righe salvate prima del 8/11/2026 avevano le radici aperte (finding 37).
export function ostacoli(deriva) {
  const fuori = [];
  for (const d of deriva || []) {
    const valori = (d.valori || []).map(derivaPubblica);
    const hook = valori.filter((v) => v.startsWith("hook:"));
    const guardie = valori.filter((v) => v.startsWith("file:hooks/"));
    const altri = valori.filter((v) => v.startsWith("file:") && !v.startsWith("file:hooks/"));
    const cosa = [hook.length ? "hook spenti" : "", guardie.length ? "guardie modificate" : "", d.conflitto && altri.length ? "aggiornamento in conflitto" : ""]
      .filter(Boolean);
    if (cosa.length) fuori.push({ installazione: d.installazione, cosa: cosa.join(", "), valori, vista: d.vista === true });
  }
  return fuori;
}

// Le righe da fare, ognuna con il suo task. Le config rotte hanno già il task dalla loro email: qui si ripetono con
// la stessa impronta, così un recap riletto non fa doppioni.
function daFare({ indietro = [], banchi = [], deriva = [], config = [] }, giorno) {
  const righe = [];
  for (const x of indietro) {
    righe.push({ testo: `L'installazione di ${idCorto(x.installazione)} è ferma alla ${x.rilascio} dal ${breve(x.dal)}: serve un /aggiorna a mano per la ${x.nuovo}.`,
      task: task(`indietro:${corto(x.installazione)}:${x.nuovo}`, `Sbloccare l'aggiornamento di ${idCorto(x.installazione)} alla ${x.nuovo}`,
        { note: `Ferma alla ${x.rilascio}, attiva il ${x.ultima}. Il primo passo è chiedere un /aggiorna a mano.` }) });
  }
  for (const x of banchi) {
    righe.push({ testo: `Il banco ${x.valore} è rosso su ${idCorto(x.installazione)} (${x.versione}), dal ${breve(x.dal)}.`,
      task: task(`banco:${corto(x.installazione)}:${x.valore}`, `Riparare il banco ${x.valore} su ${idCorto(x.installazione)}`,
        { note: `Rosso dal ${x.dal} sulla ${x.versione}. Il primo passo è rifarlo girare su quella versione.` }) });
  }
  // La deriva fa un task solo per un'installazione vista in almeno due giorni, e al massimo LIMITI.taskDerivaPerEmail
  // per email (finding 37): un POST di chiunque con un id inventato faceva un task per Claude, uno per id. La nota dice
  // solo nomi degli elenchi chiusi, mai un percorso arrivato dal client.
  const conTask = [];
  const senzaTask = [];
  for (const x of ostacoli(deriva)) (x.vista && conTask.length < LIMITI.taskDerivaPerEmail ? conTask : senzaTask).push(x);
  for (const x of conTask) {
    const differenze = [...new Set(x.valori.map(derivaInBreve))];
    righe.push({ testo: `La config di ${idCorto(x.installazione)} si è allontanata da Arturo: ${x.cosa}.`,
      task: task(`deriva:${corto(x.installazione)}:${impronta(x.valori)}`, `Guardare la deriva di ${idCorto(x.installazione)}: ${x.cosa}`,
        { note: `Differenze: ${differenze.join(", ")}.` }) });
  }
  if (senzaTask.length) {
    righe.push({ testo: `${uno(senzaTask.length, "altra installazione ha", "altre installazioni hanno")} una deriva che ostacola, senza task: ` +
      `${senzaTask.some((x) => !x.vista) ? "viste in un giorno solo, o " : ""}oltre le prime ${LIMITI.taskDerivaPerEmail}.`, task: null });
  }
  for (const x of config) {
    righe.push({ testo: `${uno(x.n, "config rotta", "config rotte")} (${x.valore.replace("rotta-", "")}): il task è nato con la sua email.`, task: null });
  }
  return righe;
}

// Comandi, skill, durata e messaggi sommati su tutte le installazioni del giorno.
function somma(uso, campo) {
  const m = new Map();
  for (const x of uso) for (const v of x[campo] || []) m.set(v.valore, (m.get(v.valore) || 0) + v.n);
  return [...m].map(([valore, n]) => ({ valore, n })).sort((a, b) => b.n - a.n || (a.valore < b.valore ? -1 : 1));
}
const lista = (voci, prefisso = "") => voci.map((v) => `${prefisso}${v.valore} ${v.n}`).join(", ");

function cosaHaUsato(x) {
  const parti = [lista(x.comandi || [], "/"), (x.skill || []).length ? `skill ${lista(x.skill)}` : ""].filter(Boolean);
  const fasce = [(x.durata || []).length ? `durata ${lista(x.durata)}` : "", (x.turni || []).length ? `messaggi ${lista(x.turni)}` : ""].filter(Boolean);
  return `${esc(parti.join(" · ") || "solo sessioni")}${fasce.length ? `<br><span style="color:#59606a;font-size:13px">${esc(fasce.join(" · "))}</span>` : ""}`;
}

// Le guardie in una tabella: bloccate e conferme chieste, le prime dieci, il resto in una riga.
function guardie(bloccate, chieste) {
  const m = new Map();
  for (const x of bloccate || []) m.set(x.valore, { valore: x.valore, bloccato: x.n, chiede: 0, confermata: 0 });
  for (const x of chieste || []) {
    const r = m.get(x.valore) || { valore: x.valore, bloccato: 0, chiede: 0, confermata: 0 };
    r.chiede += Number(x.chiede) || 0;
    r.confermata += Number(x.confermata) || 0;
    m.set(x.valore, r);
  }
  const righe = [...m.values()].sort((a, b) => b.bloccato + b.chiede - (a.bloccato + a.chiede));
  return { righe: righe.slice(0, DIECI), resto: righe.length - Math.min(righe.length, DIECI) };
}

function tabellaGuardie(g) {
  return tabella(["Guardia", "Bloccato", "Chiesto", "Sì"], g.righe.map((x) => [codice(x.valore), x.bloccato, x.chiede,
    x.chiede ? `${x.confermata} (${per(x.confermata, x.chiede)})` : "-"]), { numeriche: [1, 2, 3] }) +
    (g.resto ? paragrafo(`E altre ${g.resto} con meno volte.`, { attenuato: true }) : "");
}

const sezioneDaFare = (righe) => sezione("Da fare", elenco(righe.map((r) => r.testo)),
  { evidenza: true, nota: "Ogni riga è già un task, tranne le config rotte, che lo hanno dalla loro email, e la riga della deriva senza task." });

// Le righe di testo che il recap del mattino mette in testa, sotto il titolo.
export function righeGiorno(r, g, { giorno } = {}) {
  if (!g) return [];
  const fare = daFare({ indietro: g.indietro, banchi: r.banchi, deriva: r.deriva, config: r.config }, giorno);
  const sette = new Map((g.settimana || []).map((x) => [x.installazione, x.giorniAttivi]));
  return [
    `Ieri ${uno(g.uso.length, "installazione ha", "installazioni hanno")} usato Arturo, ${uno(r.sessioni, "sessione", "sessioni")}. ` +
      `Nei 7 giorni prima la media era ${media(g.media.installazioni)} installazioni e ${media(g.media.sessioni)} sessioni al giorno.`,
    ARRIVATI,
    "",
    "Chi l'ha usato (sessioni, giorni attivi su 7, cosa):",
    ...(g.uso.length ? g.uso.map((x) => `  ${idCorto(x.installazione)}  ${x.sessioni} sessioni, ${sette.get(x.installazione) || 1} su 7, ` +
      `${[lista(x.comandi, "/"), (x.skill || []).length ? `skill ${lista(x.skill)}` : ""].filter(Boolean).join(" · ") || "solo sessioni"}`) : ["  nessuna"]),
    ...(fare.length ? ["", "Da fare:", ...fare.map((x) => `  ${x.testo}`)] : []),
    "",
  ];
}

// Il recap del mattino. `g` è archivio.giorno(): senza (un archivio vecchio), restano i numeri di riepilogo().
export function recapGiorno(r, g, { giorno, leggi = "" } = {}) {
  const usate = g ? g.uso : [];
  const quante = g ? usate.length : r.installazioni;
  const fare = daFare({ indietro: g ? g.indietro : [], banchi: r.banchi, deriva: r.deriva, config: r.config }, giorno);
  const sette = new Map(((g && g.settimana) || []).map((x) => [x.installazione, x.giorniAttivi]));
  const vuote = [];
  const se = (cond, nome, fai) => (cond ? fai() : (vuote.push(nome), ""));

  const comandi = g ? [...somma(usate, "comandi").map((x) => ({ ...x, valore: `/${x.valore}` })),
    ...somma(usate, "skill").map((x) => ({ ...x, valore: `skill ${x.valore}` }))].sort((a, b) => b.n - a.n)
    : (r.comandi || []).map((x) => ({ ...x, valore: `/${x.valore}` }));
  const fasce = g ? [somma(usate, "durata").length ? `Durata delle sessioni: ${lista(somma(usate, "durata"))}.` : "",
    somma(usate, "turni").length ? `Messaggi per sessione: ${lista(somma(usate, "turni"))}.` : ""].filter(Boolean) : [];
  const gu = guardie(r.guardie, g ? g.chiede : []);
  const segn = g ? g.segnalazioni : [];
  const link = (n) => (leggi ? `${leggi.replace(/\/+$/, "")}/${Number(n)}` : "");
  const sito = g ? [g.feedback ? uno(g.feedback, "feedback dal modulo", "feedback dal modulo") : "",
    g.download ? uno(g.download, "comando di installazione copiato", "comandi di installazione copiati") : "",
    g.github ? uno(g.github, "visita al repository", "visite al repository") : ""].filter(Boolean) : [];
  const setup = g && (g.setupIniziati || g.setupFiniti);
  const versioni = [(r.versioni || []).map((x) => `${x.valore} (${x.n})`).join(", "), (r.sistemi || []).map((x) => `${x.valore} ${x.n}`).join(", ")]
    .filter(Boolean).join(" · ");

  const blocchi = [
    sezione("In cifre", cifre([{ valore: quante, etichetta: quante === 1 ? "installazione attiva" : "installazioni attive" },
      { valore: r.sessioni, etichetta: r.sessioni === 1 ? "sessione" : "sessioni" },
      { valore: r.segnalazioni, etichetta: r.segnalazioni === 1 ? "segnalazione" : "segnalazioni" }])),
    fare.length ? sezioneDaFare(fare) : "",
    se(usate.length, "chi l'ha usato", () => sezione("Chi l'ha usato", tabella(["Chi", "Sessioni", "Giorni su 7", "Cosa ha usato"],
      usate.map((x) => [crudo(`${chi(x.installazione).html}<br><span style="color:#59606a;font-size:13px">${esc(x.versione)} · ${esc(x.sistema)}</span>`),
        x.sessioni, sette.get(x.installazione) || 1, crudo(cosaHaUsato(x))]), { numeriche: [1, 2] }))),
    se(comandi.length, "comandi e skill", () => sezione("Comandi e skill più usati", tabella(["Cosa", "Volte"],
      comandi.slice(0, DIECI).map((x) => [codice(x.valore), x.n]), { numeriche: [1] }) + fasce.map((f) => paragrafo(f, { attenuato: true })).join(""))),
    se(setup, "setup", () => sezione("Setup", paragrafo(`${uno(g && g.setupIniziati || 0, "installazione ha", "installazioni hanno")} lanciato /setup, ` +
      `${g && g.setupFiniti || 0} ${g && g.setupFiniti === 1 ? "è arrivata" : "sono arrivate"} in fondo.`))),
    se(gu.righe.length, "guardie", () => sezione("Guardie", tabellaGuardie(gu),
      { nota: `"Bloccato" conta solo le installazioni viste in almeno ${LIMITI.giorniGuardie} giorni; "Sì" è quante volte la persona ha confermato.` })),
    se(segn.length || r.segnalazioni, "segnalazioni", () => sezione("Segnalazioni", segn.length
      ? tabella(["Numero", "Tipo", "Stato"], segn.map((x) => [link(x.id) ? crudo(`<a href="${esc(link(x.id))}" style="color:#0b5fff">n. ${Number(x.id)}</a>`) : `n. ${x.id}`,
        x.tipo, x.stato || "ricevuta"]))
      : paragrafo(`${uno(r.segnalazioni, "segnalazione arrivata", "segnalazioni arrivate")}.`))),
    se(sito.length, "sito", () => sezione("Dal sito", paragrafo(`${sito.join(", ")}.`))),
    se((r.aggiorna || []).length, "aggiornamenti", () => sezione("Aggiornamenti", paragrafo((r.aggiorna || []).map((x) => `${x.valore} ${x.n}`).join(", ")))),
    se((r.banchi || []).length, "banchi rossi", () => sezione("Banchi delle guardie rossi", tabella(["Banco", "Dove", "Dal"],
      r.banchi.map((x) => [codice(x.valore), `${idCorto(x.installazione)} · ${x.versione}`, breve(x.dal)])))),
    se(versioni, "versioni", () => sezione("Versioni e sistemi", paragrafo(versioni))),
  ];
  const conti = `Eventi scartati perché fuori elenco: ${r.scartati || 0} · avvisi non partiti: Telegram ${r.telegramKo || 0}, email ${r.emailKo || 0}.`;
  if (!(r.deriva || []).length) vuote.push("deriva");
  if (!(r.config || []).length) vuote.push("config rotte");
  return {
    html: pagina({
      testa: `Arturo · recap del ${breve(giorno)}`,
      titolo: g ? `Ieri ${uno(quante, "installazione ha", "installazioni hanno")} usato Arturo, ${uno(r.sessioni, "sessione", "sessioni")}`
        : `Il giorno ${breve(giorno)}: ${uno(r.installazioni, "installazione attiva", "installazioni attive")}`,
      apertura: g ? `Nei sette giorni prima la media era ${media(g.media.installazioni)} installazioni e ${media(g.media.sessioni)} sessioni al giorno.` : "",
      blocchi,
      piede: [vuote.length ? `Niente da dire su: ${vuote.join(", ")}.` : "", conti, ARRIVATI,
        "Arriva ogni mattina alle 8, se il giorno prima è successo qualcosa."].filter(Boolean),
    }),
    task: fare.map((x) => x.task).filter(Boolean),
  };
}

// Il riepilogo del lunedì, con "Dove migliorare Arturo" in tabelle.
export function recapSettimana(r, { lunedi, domenica } = {}) {
  const m = r.migliorare || {};
  const fare = daFare({ indietro: m.indietro || [], banchi: r.banchi, deriva: r.deriva, config: r.config }, domenica);
  const vuote = [];
  const se = (cond, nome, fai) => (cond ? fai() : (vuote.push(nome), ""));
  const uso = (r.uso || []).filter((x) => x.giorniAttivi > 0).sort((a, b) => b.giorniAttivi - a.giorniAttivi || b.sessioni - a.sessioni);
  const ferme = (r.uso || []).length - uso.length;
  const conferme = (elenco, nome) => {
    const righe = (elenco || []).slice(0, DIECI);
    return righe.length ? tabella([nome, "Chiede", "Sì", "Dove"], righe.map((x) => [codice(x.valore), x.chiede,
      `${x.confermata} (${per(x.confermata, x.chiede)})`, x.installazioni]), { numeriche: [1, 2, 3] }) +
      ((elenco || []).length > DIECI ? paragrafo(`E altre ${elenco.length - DIECI}.`, { attenuato: true }) : "") : "";
  };
  const regole = (m.conferme || []).filter((x) => x.valore.includes(".py."));
  const rit = m.ritenzione || { nuove: 0, soglie: [] };
  const setupTesto = `${uno(m.setupIniziati || 0, "installazione ha", "installazioni hanno")} iniziato /setup, ` +
    `${m.setupFiniti || 0} ${m.setupFiniti === 1 ? "è arrivata" : "sono arrivate"} in fondo, ` +
    `${m.setupMai || 0} nuove non l'hanno mai lanciato.`;
  const versioni = [(r.versioni || []).map((x) => `${x.valore} (${x.n})`).join(", "), (r.sistemi || []).map((x) => `${x.valore} ${x.n}`).join(", ")]
    .filter(Boolean).join(" · ");

  const blocchi = [
    sezione("In cifre", cifre([{ valore: r.installazioni, etichetta: r.installazioni === 1 ? "installazione attiva" : "installazioni attive" },
      { valore: r.sessioni, etichetta: "sessioni" }, { valore: r.segnalazioni, etichetta: "segnalazioni" }])),
    fare.length ? sezioneDaFare(fare) : "",
    se(uso.length, "chi lo usa", () => sezione("Chi lo usa", tabella(["Chi", "Giorni", "Sessioni", "Più usato"],
      uso.map((x) => [crudo(`${chi(x.installazione).html}<br><span style="color:#59606a;font-size:13px">ultimo ${esc(breve(x.ultima))}</span>`),
        x.giorniAttivi, x.sessioni, (x.comandi[0] && `/${x.comandi[0].valore}`) || "-"]),
      { numeriche: [1, 2] }), { nota: ferme ? `${uno(ferme, "installazione è rimasta ferma", "installazioni sono rimaste ferme")} tutta la settimana.` : "" })),
    sezione("Dove migliorare Arturo", paragrafo(setupTesto) +
      ((m.setupFermi || []).length ? paragrafo(`Fermi da più di 3 giorni: ${m.setupFermi.map((x) => `${x.valore} (${x.n})`).join(", ")}.`, { attenuato: true }) : ""),
    { nota: `Ultimi 30 giorni, numeri e non verdetti. Contano le installazioni viste in almeno ${LIMITI.giorniGuardie} giorni, salvo la ritenzione.` }),
    se((m.confermeGuardie || m.conferme || []).length, "conferme delle guardie", () => sezione("Guardie che chiedono conferma",
      conferme(m.confermeGuardie || m.conferme, "Guardia") + (regole.length ? `<div style="height:12px"></div>${conferme(regole, "Regola")}` : ""),
      { nota: "\"Dove\" è il numero di installazioni. Una guardia non si allenta sulla sola base di questi numeri." })),
    se((m.errori || []).length, "guardie che si rompono", () => sezione("Guardie che si rompono", tabella(["Guardia", "Volte", "Dove"],
      (m.errori || []).slice(0, DIECI).map((x) => [codice(x.valore), x.n, x.installazioni]), { numeriche: [1, 2] }))),
    se((m.aggiornaStorti || []).length, "aggiornamenti non applicati", () => sezione("Aggiornamenti non applicati", tabella(["Versione", "Esito", "Volte"],
      (m.aggiornaStorti || []).slice(0, DIECI).map((x) => [x.versione, x.valore, x.n]), { numeriche: [2] }))),
    se(rit.soglie.length, "ritenzione", () => sezione("Ritenzione", tabella(["Viva dopo", "Vive", "Su", "Quota"],
      rit.soglie.map((s) => [`${s.giorni} giorni`, s.vive, s.idonee, per(s.vive, s.idonee)]), { numeriche: [1, 2, 3] }),
    { nota: `${uno(rit.nuove, "installazione nuova", "installazioni nuove")} negli ultimi 7 giorni.` })),
    se((m.claude || []).length, "versioni di Claude Code", () => sezione("Versioni di Claude Code", paragrafo((m.claude || []).map((x) => `${x.valore} (${x.n})`).join(", ")))),
    se((r.comandi || []).length, "comandi", () => sezione("Comandi della settimana", tabella(["Comando", "Volte"],
      r.comandi.slice(0, DIECI).map((x) => [codice(`/${x.valore}`), x.n]), { numeriche: [1] }))),
    se((r.guardie || []).length, "guardie che hanno bloccato", () => sezione("Guardie che hanno bloccato", tabella(["Guardia", "Volte", "Dove"],
      r.guardie.slice(0, DIECI).map((x) => [codice(x.valore), x.n, x.installazioni]), { numeriche: [1, 2] }))),
    se((r.guardieFrequenti || []).length, "guardie frequenti", () => sezione("Guardie frequenti", tabella(["Guardia", "Dove", "Volte"],
      r.guardieFrequenti.map((x) => [codice(x.valore), idCorto(x.installazione), x.n]), { numeriche: [2] }),
    { nota: `Almeno ${LIMITI.guardieFrequenti} blocchi nella settimana sulla stessa installazione.` })),
    se((r.aggiorna || []).length, "esiti di /aggiorna", () => sezione("Esiti di /aggiorna", paragrafo((r.aggiorna || []).map((x) => `${x.valore} ${x.n}`).join(", ")))),
    se((r.banchi || []).length, "banchi rossi", () => sezione("Banchi delle guardie rossi", tabella(["Banco", "Dove", "Dal"],
      (r.banchi || []).map((x) => [codice(x.valore), `${idCorto(x.installazione)} · ${x.versione}`, breve(x.dal)])))),
    se(versioni, "versioni", () => sezione("Versioni e sistemi", paragrafo(versioni))),
  ];
  if (!(r.deriva || []).length) vuote.push("deriva");
  if (!(r.config || []).length) vuote.push("config rotte");
  return {
    html: pagina({
      testa: `Arturo · settimana dal ${breve(lunedi)} al ${breve(domenica)}`,
      titolo: `La settimana di Arturo: ${uno(r.installazioni, "installazione attiva", "installazioni attive")}, ${uno(r.sessioni, "sessione", "sessioni")}`,
      blocchi,
      piede: [vuote.length ? `Niente da dire su: ${vuote.join(", ")}.` : "",
        `Eventi scartati perché fuori elenco: ${r.scartati || 0} · avvisi non partiti: Telegram ${r.telegramKo || 0}, email ${r.emailKo || 0}.`,
        "Arriva ogni lunedì, anche vuoto: se manca, il server è fermo."].filter(Boolean),
    }),
    task: fare.map((x) => x.task).filter(Boolean),
  };
}

