/* Arturo web: il tavolo dei progetti. Script classico, nessuna dipendenza, nessuna rete esterna.
   I dati entrano nella pagina solo con createElement e textContent: un titolo con dentro
   del codice HTML resta testo. Ogni scrittura passa da /api/azione, cioè da todo_store.
   Tre viste, scelte dall'indirizzo: il tavolo (#/), un progetto (#/progetto/NOME) e il
   dettaglio di un todo dentro il suo progetto (#/progetto/NOME/ID). */
(function () {
  "use strict";

  var meta = document.querySelector('meta[name="arturo-token"]');
  var TOKEN = meta ? meta.getAttribute("content") : "";
  var OGNI_VISIBILE = 20000;   // ms tra due letture a scheda visibile
  var OGNI_NASCOSTA = 300000;  // a scheda nascosta: tiene acceso il server, che si spegne dopo 30 minuti
  var GIORNI = ["domenica", "lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato"];
  var GIORNI_BREVI = ["dom", "lun", "mar", "mer", "gio", "ven", "sab"];
  var MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto",
    "settembre", "ottobre", "novembre", "dicembre"];
  var MESI_BREVI = ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"];
  var ESEMPI = ["Mandare il preventivo per la rassegna", "Rileggere il capitolo 3", "Cercare tre fonti per il bando"];
  var NOMI_QUANDO = { "oggi": "Oggi", "settimana": "Questa settimana", "più avanti": "Più avanti" };
  var NOMI_PRIORITA = { alta: "Alta", media: "Media", bassa: "Bassa" };
  var NOMI_CAMPI = { titolo: "titolo", progetto: "progetto", scadenza: "scadenza", chi: "chi agisce",
    perche: "perché", priorita: "priorità", quando: "quando" };
  var ORDINE_GRUPPI = ["tu", "decidi", "io", "fermo"];
  var IN_VISTA = 3;            // i task che un foglio mostra dopo il prossimo passo
  var COMANDO = "python3 ~/.claude/bin/arturo web";

  var stato = {
    dati: null,        // {vista, progetti, da_dove, percorso, partenza}: l'ultima lettura disegnata
    testo: "",         // la stessa lettura come JSON, per sapere se è cambiata
    inAttesa: null,    // una lettura arrivata mentre la persona scrive in un pannello
    rotta: { tipo: "tavolo", progetto: "", todo: null },
    scheda: null,      // il dettaglio letto da /api/todo: {id, todo} oppure {id, errore}
    aperto: null,      // il pannello in linea aperto: {id, tipo: "modifica" | "decidi"}
    apriDopo: null,    // il pannello da aprire appena cambia la vista («Ho deciso» dal tavolo)
    daFoglio: null,    // il nome del foglio appena cliccato: passa nel titolo della pagina del progetto
    annulla: null,
    occupato: false,   // una richiesta di scrittura in corso
    spento: false,
    timer: 0,
    primo: true
  };

  function $(id) { return document.getElementById(id); }

  // --- costruzione del DOM --------------------------------------------------------

  function el(tag, opzioni, figli) {
    var nodo = document.createElement(tag);
    var chiavi = opzioni ? Object.keys(opzioni) : [];
    chiavi.forEach(function (k) {
      var v = opzioni[k];
      if (v === null || v === undefined || v === false) { return; }
      if (k === "classe") { nodo.className = v; }
      else if (k === "testo") { nodo.textContent = v; }
      else if (k === "valore") { nodo.value = v; }
      else if (k === "su") { nodo.addEventListener("click", v); }
      else { nodo.setAttribute(k, v === true ? "" : String(v)); }
    });
    (figli || []).forEach(function (f) {
      if (f === null || f === undefined || f === false) { return; }
      nodo.appendChild(typeof f === "string" ? document.createTextNode(f) : f);
    });
    return nodo;
  }

  function svuota(nodo) {
    while (nodo.firstChild) { nodo.removeChild(nodo.firstChild); }
  }

  function bottone(testo, classe, su, altro) {
    var o = { type: "button", classe: "azione " + classe, su: su };
    Object.keys(altro || {}).forEach(function (k) { o[k] = altro[k]; });
    return el("button", o, [testo]);
  }

  // --- date: oggi viene dal server (ARTURO_OGGI), non dall'orologio del browser ---

  function dataDa(iso) {
    var p = iso.split("-");
    return new Date(Date.UTC(Number(p[0]), Number(p[1]) - 1, Number(p[2])));
  }
  function dataLunga(iso) {
    var d = dataDa(iso);
    return GIORNI[d.getUTCDay()] + " " + d.getUTCDate() + " " + MESI[d.getUTCMonth()];
  }
  function dataBreve(d) {
    return GIORNI_BREVI[d.getUTCDay()] + " " + d.getUTCDate() + " " + MESI_BREVI[d.getUTCMonth()];
  }
  function gma(iso) {
    if (!iso) { return ""; }
    var p = iso.split("-");
    return p[2] + "/" + p[1] + "/" + p[0];
  }
  // L'ora di un evento della storia: quella del computer della persona, come nella CLI.
  function momento(ts) {
    var d = new Date(ts);
    if (isNaN(d.getTime())) { return ""; }
    var mm = d.getMinutes();
    return d.getDate() + " " + MESI_BREVI[d.getMonth()] + ", " + d.getHours() + ":" + (mm < 10 ? "0" : "") + mm;
  }
  function tondo(titolo) {
    return titolo.charAt(0) + titolo.slice(1).toLowerCase();
  }
  // I nomi di «chi» vengono dai titoli dei gruppi dello store: gruppi, segni, select e radio
  // dicono la stessa cosa con le stesse parole.
  function nomiChi() {
    var nomi = {};
    stato.dati.vista.gruppi.forEach(function (g) { nomi[g.tipo] = tondo(g.titolo); });
    return nomi;
  }
  function quante(n, una, molte) {
    return n === 1 ? una : n + " " + molte;
  }

  // --- rete -----------------------------------------------------------------------

  function chiama(metodo, percorso, corpo) {
    var opzioni = { method: metodo, headers: { "X-Arturo-Token": TOKEN }, cache: "no-store", credentials: "same-origin" };
    if (corpo !== undefined) {
      opzioni.headers["Content-Type"] = "application/json";
      opzioni.body = JSON.stringify(corpo);
    }
    return fetch(percorso, opzioni).then(function (r) {
      return r.text().then(function (testo) {
        var dati = null;
        try { dati = JSON.parse(testo); } catch (e) { dati = null; }
        return { ok: r.ok, codice: r.status, dati: dati };
      });
    });
  }

  function pianifica() {
    clearTimeout(stato.timer);
    if (stato.spento) { return; }
    stato.timer = setTimeout(leggi, document.hidden ? OGNI_NASCOSTA : OGNI_VISIBILE);
  }

  function leggi() {
    return chiama("GET", "/api/vista").then(function (r) {
      if (!r.ok || !r.dati || !r.dati.vista) { disconnesso(); return; }
      if (stato.allarme === "rete") { pulisciAllarme(); }
      ricevi(r.dati, false);
    }).catch(function () { disconnesso(); }).then(pianifica);
  }

  function lettura(dati) {
    return { vista: dati.vista, progetti: dati.progetti, da_dove: dati.da_dove || null, percorso: dati.percorso || null,
      partenza: dati.partenza || (stato.dati ? stato.dati.partenza : "generale") };
  }

  function ricevi(dati, forza) {
    var nuova = lettura(dati);
    var testo = JSON.stringify(nuova);
    if (!forza && testo === stato.testo) { return; }
    if (!forza && occupato()) { stato.inAttesa = nuova; return; }
    applica(nuova, testo);
  }

  // La persona sta scrivendo: un ridisegno le toglierebbe il testo dalle mani.
  function occupato() {
    if (stato.aperto) { return true; }
    var a = document.activeElement;
    return !!(a && a.closest && a.closest(".pannello") && /^(INPUT|SELECT|TEXTAREA)$/.test(a.tagName));
  }

  function forseApplica() {
    if (stato.inAttesa && !occupato()) {
      var nuova = stato.inAttesa;
      applica(nuova, JSON.stringify(nuova));
    }
  }

  function applica(dati, testo) {
    stato.dati = dati;
    stato.testo = testo;
    stato.inAttesa = null;
    var fuoco = ricordaFuoco();
    var scritti = ricordaCampi();
    disegna();
    rimettiCampi(scritti);
    if (fuoco) { rimettiFuoco(fuoco.id, fuoco.ruolo); }
    // Il dettaglio aperto ha una storia che cambia con ogni scrittura: si rilegge.
    if (stato.rotta.todo) { leggiScheda(stato.rotta.todo); }
  }

  // Un pannello aperto resta aperto quando arriva l'esito di un'altra azione (una nota, «Fatto»
  // su un'altra riga). Il ridisegno lo ricostruisce: i campi che la persona ha cambiato e non ha
  // ancora salvato tornano al loro posto. Ogni campo ricorda in data-iniziale il valore disegnato.
  function ricordaCampi() {
    var scritti = {};
    Array.prototype.forEach.call(document.querySelectorAll(".todo-pannello [data-iniziale], .dettaglio [data-iniziale]"), function (n) {
      if (n.id && n.value !== n.getAttribute("data-iniziale")) { scritti[n.id] = n.value; }
    });
    return scritti;
  }
  function rimettiCampi(scritti) {
    Object.keys(scritti).forEach(function (id) {
      var n = $(id);
      if (n) { n.value = scritti[id]; }
    });
  }

  // --- avvisi e barra dell'ultima azione ------------------------------------------

  function allarme(tipo, righe) {
    var box = $("allarme");
    svuota(box);
    stato.allarme = tipo;
    righe.forEach(function (r) { box.appendChild(r); });
  }
  function pulisciAllarme() {
    stato.allarme = "";
    svuota($("allarme"));
  }
  function disconnesso() {
    if (stato.spento || stato.allarme === "rete") { return; }
    allarme("rete", [
      el("p", { testo: "La pagina non raggiunge più Arturo." }),
      el("p", {}, ["Chiedi a Claude di riaprire la pagina dei todo, oppure scrivi nel terminale: ",
        el("code", { testo: COMANDO })])
    ]);
  }
  function errore(testo) {
    allarme("errore", [el("p", { testo: testo })]);
  }

  function mostraEsito(testo, annulla) {
    stato.annulla = annulla || null;
    $("esito").textContent = testo;
    $("annulla").hidden = !stato.annulla;
    $("ultima").classList.add("attiva");
  }

  // --- azioni ---------------------------------------------------------------------

  function azione(corpo, opzioni) {
    opzioni = opzioni || {};
    if (stato.occupato || stato.spento) { return Promise.resolve(false); }
    stato.occupato = true;
    var prossimo = corpo.id ? prossimaRiga(corpo.id) : null;
    return chiama("POST", "/api/azione", corpo).then(function (r) {
      if (r.codice === 409 && r.dati && r.dati.vista) {
        stato.aperto = null;
        // Un Annulla rifiutato perché il todo è cambiato non si ripete: il bottone sparisce.
        if (opzioni.annullo) { stato.annulla = null; $("annulla").hidden = true; }
        errore(r.dati.errore);
        ricevi(r.dati, true);
        return false;
      }
      if (!r.ok || !r.dati || !r.dati.vista) {
        errore(r.dati && r.dati.errore ? r.dati.errore : "La richiesta non è andata a buon fine. Riprova.");
        return false;
      }
      pulisciAllarme();
      if (opzioni.chiudi) { stato.aperto = null; }
      if (opzioni.prima) { opzioni.prima(r.dati); }
      mostraEsito((opzioni.annullo ? "Annullato. " : "") + r.dati.messaggio, opzioni.annullo ? null : r.dati.annulla);
      ricevi(r.dati, true);
      if (opzioni.fuoco !== false && corpo.id) { fuocoDopo(r.dati.id || corpo.id, prossimo, opzioni.ruolo); }
      return true;
    }).catch(function () {
      disconnesso();
      return false;
    }).then(function (esito) {
      stato.occupato = false;
      return esito;
    });
  }

  function prossimaRiga(id) {
    var righe = Array.prototype.slice.call(document.querySelectorAll(".pannello .todo"));
    for (var i = 0; i < righe.length; i += 1) {
      if (righe[i].getAttribute("data-id") === String(id)) {
        var dopo = righe[i + 1] || righe[i - 1];
        return dopo ? dopo.getAttribute("data-id") : null;
      }
    }
    return null;
  }

  function rigaDi(id) {
    return document.querySelector('.pannello .todo[data-id="' + String(Number(id)) + '"]');
  }

  function rimettiFuoco(id, ruolo) {
    var riga = rigaDi(id);
    if (!riga) { return false; }
    var bersaglio = (ruolo && riga.querySelector('[data-ruolo="' + ruolo + '"]')) || riga.querySelector("button");
    if (bersaglio) { bersaglio.focus(); }
    return !!bersaglio;
  }

  // Dopo un'azione il fuoco va alla stessa riga, poi alla seguente, poi al titolo della vista.
  function fuocoDopo(id, prossimo, ruolo) {
    if (rimettiFuoco(id, ruolo)) { return; }
    if (prossimo && rimettiFuoco(prossimo)) { return; }
    var titolo = document.querySelector(".pannello h2") || $("titolo");
    if (titolo) { titolo.focus(); }
  }

  function ricordaFuoco() {
    var a = document.activeElement;
    if (!a || !a.closest) { return null; }
    var riga = a.closest(".todo");
    if (!riga) { return null; }
    return { id: riga.getAttribute("data-id"), ruolo: a.getAttribute("data-ruolo") };
  }

  function annulla() {
    var corpo = stato.annulla;
    if (!corpo) { return; }
    azione(corpo, { annullo: true, chiudi: true });
  }

  function spegni() {
    chiama("POST", "/api/spegni", {}).then(function (r) {
      if (!r.ok) { errore(r.dati && r.dati.errore ? r.dati.errore : "La pagina non si è spenta. Riprova."); return; }
      stato.spento = true;
      clearTimeout(stato.timer);
      Array.prototype.forEach.call(document.querySelectorAll("main button, main input, main select, main textarea, #spegni, #annulla"),
        function (n) { n.disabled = true; });
      allarme("spenta", [
        el("p", { testo: "La pagina è spenta. Puoi chiudere questa scheda." }),
        el("p", {}, ["Per riaprirla chiedi a Claude, oppure scrivi nel terminale: ", el("code", { testo: COMANDO })])
      ]);
    }).catch(function () { disconnesso(); });
  }

  // --- rotte ------------------------------------------------------------------------

  function indirizzo(progetto, id) {
    if (!progetto) { return "#/"; }
    return "#/progetto/" + encodeURIComponent(progetto) + (id ? "/" + id : "");
  }

  function leggiRotta() {
    var h = location.hash || "";
    var m = /^#\/progetto\/([^/]+)(?:\/(\d+))?$/.exec(h);
    if (!m) { return { tipo: "tavolo", progetto: "", todo: null }; }
    var nome;
    try { nome = decodeURIComponent(m[1]); } catch (e) { return { tipo: "tavolo", progetto: "", todo: null }; }
    return { tipo: "progetto", progetto: nome, todo: m[2] ? Number(m[2]) : null };
  }

  function vai(progetto, id) {
    var nuovo = indirizzo(progetto, id);
    if (location.hash === nuovo) { cambiaRotta(); } else { location.hash = nuovo; }
  }

  // Il cambio di vista: dissolvenza se il browser la sa fare e la persona non chiede meno movimento.
  function cambiaRotta() {
    var prima = stato.rotta;
    var dopo = leggiRotta();
    var cambiaVista = prima.tipo !== dopo.tipo || prima.progetto !== dopo.progetto;
    stato.rotta = dopo;
    stato.aperto = stato.apriDopo;
    stato.apriDopo = null;
    if (stato.inAttesa) { var nuova = stato.inAttesa; stato.dati = nuova; stato.testo = JSON.stringify(nuova); stato.inAttesa = null; }
    if (!dopo.todo) { stato.scheda = null; }
    var titolo = $("titolo");
    var ponte = null;  // il nome del foglio che passa nel titolo, o il titolo che torna nel suo foglio
    if (cambiaVista && dopo.tipo === "progetto" && stato.daFoglio && stato.daFoglio.getAttribute("data-progetto") === dopo.progetto) {
      titolo.style.viewTransitionName = "none";
      stato.daFoglio.style.viewTransitionName = "titolo";
    }
    stato.daFoglio = null;
    var fai = function () {
      titolo.style.viewTransitionName = "";
      if (stato.dati) { disegna(); }
      if (cambiaVista && dopo.tipo === "tavolo" && prima.tipo === "progetto") {
        ponte = document.querySelector('.foglio-nome a[data-progetto="' + CSS.escape(prima.progetto) + '"]');
        if (ponte) { titolo.style.viewTransitionName = "none"; ponte.style.viewTransitionName = "titolo"; }
      }
      if (dopo.todo) { leggiScheda(dopo.todo, true); }
      if (!cambiaVista) { return; }
      window.scrollTo(0, 0);
      var riga = stato.aperto ? rigaDi(stato.aperto.id) : null;
      var campo = riga ? riga.querySelector(".todo-pannello input") : null;
      if (campo) { campo.focus(); } else { $("titolo").focus({ preventScroll: true }); }
    };
    var calmo = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var pulisci = function () { titolo.style.viewTransitionName = ""; if (ponte) { ponte.style.viewTransitionName = ""; } };
    if (cambiaVista && document.startViewTransition && !calmo && stato.dati) {
      document.startViewTransition(fai).finished.then(pulisci, pulisci);
    } else { fai(); pulisci(); }
  }

  // --- disegno ----------------------------------------------------------------------

  function aperti() {
    var fuori = [];
    stato.dati.vista.gruppi.forEach(function (g) { g.todo.forEach(function (t) { fuori.push(t); }); });
    return fuori;
  }
  function chiusi() {
    return stato.dati.vista.chiusi_todo || [];
  }
  function perId(id) {
    var tutti = aperti().concat(chiusi());
    for (var i = 0; i < tutti.length; i += 1) { if (tutti[i].id === id) { return tutti[i]; } }
    return null;
  }

  function disegna() {
    var v = stato.dati.vista;
    $("oggi").textContent = dataLunga(v.oggi);
    disegnaPercorso();
    disegnaProgetti();
    disegnaAvvisi(v.avvisi || []);
    disegnaSceltaChi();
    var r = stato.rotta;
    if (r.tipo === "progetto" && !stato.dati.progetti[r.progetto] && r.progetto !== stato.dati.partenza) {
      // Il progetto non esiste più (rinominato, o un link vecchio): si torna al tavolo.
      stato.rotta = { tipo: "tavolo", progetto: "", todo: null };
      try { history.replaceState(null, "", "#/"); } catch (e) { /* senza cronologia la vista cambia lo stesso */ }
      r = stato.rotta;
    }
    // Un todo che passa tra aperti e chiusi cambia lista: il suo pannello non lo segue.
    if (stato.aperto && (!perId(stato.aperto.id) || chiusoOra(stato.aperto.id) !== !!stato.aperto.chiuso)) { stato.aperto = null; }
    var vista = $("vista");
    svuota(vista);
    svuota($("davanti"));
    $("briciole").hidden = r.tipo === "tavolo";
    if (r.tipo === "tavolo") { disegnaTavolo(vista); } else { disegnaProgetto(vista, r.progetto); }
    // Il todo del pannello aperto non è più nella vista (chiuso con «Fatto», spostato di progetto):
    // il pannello non c'è più, e le letture successive arrivano di nuovo nella pagina.
    if (stato.aperto && !$("pannello-todo-" + stato.aperto.id)) { stato.aperto = null; }
  }

  function disegnaPercorso() {
    var p = stato.dati.percorso;
    var riga = $("percorso");
    svuota(riga);
    riga.hidden = !p;
    if (!p) { return; }
    var punti = el("span", { classe: "percorso-punti", "aria-hidden": "true" });
    for (var i = 1; i <= p.totale; i += 1) {
      punti.appendChild(el("span", { classe: i < p.tappa ? "punto punto--fatto" : (i === p.tappa ? "punto stella" : "punto") }));
    }
    riga.appendChild(punti);
    riga.appendChild(el("span", { testo: p.tappa
      ? "Percorso: tappa " + p.tappa + " di " + p.totale + ", " + p.nome
      : "Percorso: all'inizio, la prima tappa è Osserva" }));
  }

  function disegnaSceltaChi() {
    var nomi = nomiChi();
    Array.prototype.forEach.call(document.querySelectorAll("[data-chi]"), function (n) {
      var nome = nomi[n.getAttribute("data-chi")];
      if (nome) { n.textContent = nome; }
    });
  }

  function disegnaProgetti() {
    var nomi = Object.keys(stato.dati.progetti).sort();
    var partenza = stato.dati.partenza;
    var lista = $("elenco-progetti");
    svuota(lista);
    var conPartenza = nomi.indexOf(partenza) === -1 ? nomi.concat([partenza]).sort() : nomi;
    conPartenza.forEach(function (n) { lista.appendChild(el("option", { valore: n })); });
    var campo = $("nuovo-progetto");
    var r = stato.rotta;
    if (r.tipo === "progetto") {
      // Nella pagina di un progetto, quello che si aggiunge va lì.
      if (campo.getAttribute("data-rotta") !== r.progetto) { campo.value = r.progetto; campo.setAttribute("data-rotta", r.progetto); }
      $("aggiunta-etichetta").textContent = "Cosa c'è da fare in «" + r.progetto + "»?";
    } else {
      if (campo.hasAttribute("data-rotta") || stato.primo) { campo.value = partenza; campo.removeAttribute("data-rotta"); }
      $("aggiunta-etichetta").textContent = "Cosa c'è da fare?";
    }
    stato.primo = false;
  }

  function disegnaAvvisi(avvisi) {
    var box = $("avvisi");
    svuota(box);
    box.hidden = !avvisi.length;
    if (!avvisi.length) { return; }
    // Gli avvisi non sono tutti righe illeggibili: anche una rinumerazione dopo un merge è un avviso.
    box.appendChild(el("p", { testo: avvisi.length === 1
      ? "L'archivio dei todo segnala una cosa. Il resto funziona."
      : "L'archivio dei todo segnala " + avvisi.length + " cose. Il resto funziona." }));
    box.appendChild(el("ul", {}, avvisi.map(function (a) { return el("li", { testo: a }); })));
  }

  // La sintesi in testata fa anche da legenda: ogni frase porta il segno del suo «chi».
  function sintesi(lista, dove) {
    var nodo = $("sintesi");
    svuota(nodo);
    var tu = lista.filter(function (t) { return t.gruppo === "tu"; });
    var scaduti = lista.filter(function (t) { return t.giorni !== null && t.giorni < 0; }).length;
    var decidi = lista.filter(function (t) { return t.gruppo === "decidi"; }).length;
    var io = lista.filter(function (t) { return t.gruppo === "io"; }).length;
    var frasi = [];
    if (!lista.length) {
      frasi.push([null, dove ? "Niente di aperto in «" + dove + "»." : "Niente di aperto. Il cielo è sgombro."]);
    } else {
      frasi.push(["tu", tu.length ? "Tocca a te: " + quante(tu.length, "una cosa.", "cose.") : "Niente tocca a te adesso."]);
      if (decidi) { frasi.push(["decidi", decidi === 1 ? "Una aspetta una tua scelta." : decidi + " aspettano una tua scelta."]); }
      if (io) { frasi.push(["io", io === 1 ? "Claude ne ha in mano una." : "Claude ne ha in mano " + io + "."]); }
      if (scaduti) { frasi.push([null, scaduti === 1 ? "Una è scaduta." : scaduti + " sono scadute."]); }
    }
    frasi.forEach(function (f) {
      nodo.appendChild(el("span", { classe: "frase" }, [f[0] ? segnoSolo(f[0]) : null, f[1]]));
    });
  }

  function vuoto(dove) {
    var campo = $("nuovo-titolo");
    return el("div", { classe: "vuoto" }, [
      el("h2", { tabindex: "-1", testo: dove ? "Nessuna cosa da fare aperta in «" + dove + "»." : "Il tavolo è sgombro." }),
      el("p", { testo: "Scrivi in alto la prima cosa da fare. Per esempio:" }),
      el("div", { classe: "esempi" }, ESEMPI.map(function (testo) {
        return bottone(testo, "azione--bordo", function () {
          campo.value = testo;
          campo.focus();
          campo.setSelectionRange(testo.length, testo.length);
        });
      })),
      el("p", { classe: "dirlo", testo: "Puoi anche dirlo a Claude: «ricordami di…»." })
    ]);
  }

  // Il segno di chi agisce: la stessa forma nel tavolo, nel progetto e nel dettaglio.
  function segno(t, conNome) {
    var nomi = nomiChi();
    var tipo = t.gruppo || "chiuso";
    var nome = t.gruppo ? nomi[t.gruppo] : (t.stato === "fatto" ? "Fatto" : "Scartato");
    return el("span", { classe: "segno segno--" + tipo, title: conNome ? null : nome },
      [conNome ? nome : el("span", { classe: "vis-sr", testo: nome })]);
  }

  // Il segno senza nome a schermo: nella sintesi la frase accanto dice già chi è.
  function segnoSolo(gruppo) {
    return el("span", { classe: "segno segno--" + gruppo, "aria-hidden": "true" });
  }

  // --- il tavolo ----------------------------------------------------------------------

  function disegnaTavolo(vista) {
    $("titolo").textContent = "I tuoi progetti";
    document.title = "I tuoi progetti · Arturo";
    var tutti = aperti();
    sintesi(tutti, "");
    if (!tutti.length && !chiusi().length) { vista.appendChild(vuoto("")); return; }
    $("davanti").appendChild(daDove());
    var tavolo = el("ul", { classe: "tavolo", "aria-label": "I progetti" });
    ordinaProgetti().forEach(function (nome) { tavolo.appendChild(foglio(nome)); });
    vista.appendChild(tavolo);
    var finiti = chiusi();
    if (finiti.length) {
      vista.appendChild(el("details", { classe: "chiusi" }, [
        el("summary", { testo: "Chiusi di recente · " + finiti.length }),
        el("ul", { classe: "lista" }, finiti.slice(0, 8).map(function (t) { return riga(t, { progetto: true }); }))
      ]));
    }
  }

  // Prima i progetti dove qualcosa chiede una persona, poi quelli in mano a Claude.
  // «generale» chiude il tavolo: è il cassetto, non un progetto.
  function ordinaProgetti() {
    var conti = stato.dati.progetti;
    var tutti = aperti();
    function peso(nome) {
      var suoi = tutti.filter(function (t) { return t.progetto === nome; });
      var persona = suoi.filter(function (t) { return t.gruppo === "tu" || t.gruppo === "decidi"; }).length;
      return [nome === "generale" ? 1 : 0, persona ? 0 : 1, -(conti[nome].scaduti || 0), -persona, -conti[nome].aperti];
    }
    return Object.keys(conti).filter(function (n) { return n.charAt(0) !== "_"; }).sort(function (a, b) {
      var pa = peso(a), pb = peso(b);
      for (var i = 0; i < pa.length; i += 1) { if (pa[i] !== pb[i]) { return pa[i] - pb[i]; } }
      return a < b ? -1 : 1;
    });
  }

  function daDove() {
    var d = stato.dati.da_dove;
    var t = d ? perId(d.id) : null;
    if (!t) {
      return el("section", { classe: "da-dove da-dove--vuoto", "aria-labelledby": "da-dove-titolo" }, [
        el("h2", { id: "da-dove-titolo", tabindex: "-1" }, [el("span", { classe: "da-dove-etichetta", testo: "Da dove partirei" }), "Niente da fare per te"]),
        el("p", { classe: "da-dove-motivo", testo: "Quello che resta è in mano a Claude, oppure aspetta qualcosa." })
      ]);
    }
    var azioni = [
      bottone("Fatto", "azione--piena bottone-fatto", function () {
        azione({ azione: "fatto", id: t.id, titolo_atteso: t.titolo }, { fuoco: false });
      }, { "aria-label": "Fatto: " + t.titolo }),
      t.gruppo === "decidi" ? bottone("Ho deciso", "azione--bordo", function () {
        stato.apriDopo = { id: t.id, tipo: "decidi" };
        vai(t.progetto, null);
      }) : null,
      el("a", { classe: "azione azione--testo", href: indirizzo(t.progetto, t.id), testo: "Apri" })
    ];
    return el("section", { classe: "da-dove", "aria-labelledby": "da-dove-titolo" }, [
      el("div", { classe: "da-dove-corpo" }, [
        el("h2", { id: "da-dove-titolo", tabindex: "-1" }, [el("span", { classe: "da-dove-etichetta", testo: "Da dove partirei" }), t.titolo]),
        el("p", { classe: "da-dove-motivo" }, [
          segno(t, true),
          el("span", { testo: d.motivo }),
          el("a", { href: indirizzo(t.progetto, null), testo: t.progetto })
        ])
      ]),
      el("div", { classe: "da-dove-azioni" }, azioni)
    ]);
  }

  // Quello che una riga del foglio deve dire da sé: scaduto, in attesa, fermo.
  function segnali(t) {
    var fuori = [];
    if (t.giorni !== null && t.giorni < 0) { fuori.push(el("span", { classe: "foglio-segnale foglio-segnale--passato", testo: t.scadenza_testo })); }
    if (t.attende && t.attende.length) { fuori.push(el("span", { classe: "foglio-segnale", testo: "aspetta " + t.attende.map(function (n) { return "#" + n; }).join(", ") })); }
    if (t.gruppo === "fermo" && t.motivo) { fuori.push(el("span", { classe: "foglio-segnale", testo: "fermo: " + t.motivo })); }
    return fuori;
  }

  function foglio(nome) {
    var c = stato.dati.progetti[nome];
    var suoi = aperti().filter(function (t) { return t.progetto === nome; });
    suoi.sort(function (a, b) { return ORDINE_GRUPPI.indexOf(a.gruppo) - ORDINE_GRUPPI.indexOf(b.gruppo); });
    var persona = suoi.some(function (t) { return t.gruppo === "tu" || t.gruppo === "decidi"; });
    // Il prossimo passo non aspetta nessuno: la stessa esclusione di «Da dove partirei».
    var liberi = suoi.filter(function (t) { return t.gruppo !== "fermo" && !(t.attende || []).length; });
    var primo = liberi[0] || suoi.filter(function (t) { return t.gruppo !== "fermo"; })[0] || null;
    var altri = suoi.filter(function (t) { return t !== primo; });
    var scadenze = suoi.filter(function (t) { return t.giorni !== null; }).sort(function (a, b) { return a.giorni - b.giorni; });
    var vicina = scadenze[0] || null;

    var conti = [];
    ORDINE_GRUPPI.forEach(function (g) {
      var n = suoi.filter(function (t) { return t.gruppo === g; }).length;
      if (n) { conti.push(el("li", { classe: "conto-chi" }, [segno({ gruppo: g }, false), el("span", { testo: String(n) })])); }
    });

    var corpo = [
      el("h2", { classe: "foglio-nome" }, [el("a", { href: indirizzo(nome, null), testo: nome, "data-progetto": nome,
        su: function (e) { stato.daFoglio = e.currentTarget; } })]),
      primo ? el("p", { classe: "foglio-prossimo" }, [
        segno(primo, false),
        el("span", {}, [el("a", { href: indirizzo(nome, primo.id), testo: primo.titolo })].concat(segnali(primo)))
      ]) : el("p", { classe: "foglio-quieto", testo: suoi.length ? "Tutto fermo: aspetta qualcosa." : "Niente di aperto." }),
      altri.length ? el("ul", { classe: "foglio-altri" }, altri.slice(0, IN_VISTA).map(function (t) {
        return el("li", {}, [segno(t, false), el("span", {}, [el("a", { href: indirizzo(nome, t.id), testo: t.titolo })].concat(segnali(t)))]);
      }).concat(altri.length > IN_VISTA ? [el("li", { classe: "foglio-ancora" }, [
        el("a", { href: indirizzo(nome, null), testo: "e altri " + (altri.length - IN_VISTA) })])] : [])) : null,
      el("div", { classe: "foglio-piede" }, [
        conti.length ? el("ul", { classe: "foglio-conti", "aria-label": "Chi agisce" }, conti) : null,
        vicina ? el("span", { classe: "foglio-scadenza" + (vicina.giorni < 0 ? " foglio-scadenza--passata" : ""),
          testo: vicina.scadenza_testo }) : (c.chiusi ? el("span", { classe: "foglio-scadenza", testo: quante(c.chiusi, "1 chiuso", "chiusi") }) : null)
      ])
    ];
    return el("li", { classe: "foglio" + (persona ? "" : " foglio--dietro") }, corpo);
  }

  // --- un progetto ----------------------------------------------------------------------

  function disegnaProgetto(vista, nome) {
    $("titolo").textContent = nome;
    document.title = nome + " · Arturo";
    var suoi = aperti().filter(function (t) { return t.progetto === nome; });
    sintesi(suoi, nome);
    var r = stato.rotta;
    var lista = el("div", { classe: "progetto-lista" });
    if (!suoi.length) {
      lista.appendChild(vuoto(nome));
    } else {
      stato.dati.vista.gruppi.forEach(function (g) {
        var dentro = g.todo.filter(function (t) { return t.progetto === nome; });
        if (!dentro.length) { return; }
        lista.appendChild(el("section", { classe: "gruppo" }, [
          el("div", { classe: "gruppo-testa" }, [
            segno({ gruppo: g.tipo }, false),
            el("h2", { tabindex: "-1", testo: tondo(g.titolo) }),
            el("span", { classe: "conto", testo: String(dentro.length) })
          ]),
          el("p", { classe: "gruppo-descr", testo: g.descrizione }),
          el("ul", { classe: "lista" }, dentro.map(function (t) { return riga(t, {}); }))
        ]));
      });
    }
    var finiti = chiusi().filter(function (t) { return t.progetto === nome; });
    if (finiti.length) {
      lista.appendChild(el("details", { classe: "chiusi" }, [
        el("summary", { testo: "Chiusi · " + finiti.length }),
        el("p", { classe: "gruppo-descr", testo: "Fatti o scartati. Niente si cancella: puoi riprenderli." }),
        el("ul", { classe: "lista" }, finiti.map(function (t) { return riga(t, {}); }))
      ]));
    }
    var layout = el("div", { classe: "progetto" + (r.todo ? " progetto--dettaglio" : "") }, [lista]);
    if (r.todo) { layout.appendChild(el("aside", { classe: "dettaglio", id: "dettaglio", "aria-label": "Dettaglio del todo #" + r.todo, tabindex: "-1" }, schedaCorpo())); }
    vista.appendChild(layout);
  }

  // --- una riga ---------------------------------------------------------------------

  function dettagli(t, contesto) {
    var pezzi = [];
    var chiuso = t.stato === "fatto" || t.stato === "scartato";
    if (contesto.progetto) { pezzi.push(el("span", { classe: "chip", testo: t.progetto })); }
    if (chiuso) {
      pezzi.push(el("span", { classe: "esito esito--" + t.stato, testo: t.stato }));
      if (t.motivo) { pezzi.push(el("span", { classe: "dettaglio-testo", testo: t.motivo })); }
    } else {
      if (t.stato === "in corso") { pezzi.push(el("span", { classe: "esito esito--corso", testo: "in corso" })); }
      if (t.giorni !== null) {
        if (t.giorni < 0) { pezzi.push(el("span", { classe: "esito esito--scaduto", testo: t.scadenza_testo })); }
        else if (t.giorni === 0) { pezzi.push(el("span", { classe: "esito esito--oggi", testo: t.scadenza_testo })); }
        else { pezzi.push(el("span", { testo: t.scadenza_testo + (t.giorni > 1 ? " · " + dataBreve(dataDa(t.scadenza)) : "") })); }
      }
      if (t.quando === "oggi" && t.giorni !== 0) { pezzi.push(el("span", { testo: "per oggi" })); }
      if (t.priorita === "alta") { pezzi.push(el("span", { testo: "priorità alta" })); }
      if (t.perche) { pezzi.push(el("span", { classe: "dettaglio-testo", testo: "perché: " + t.perche })); }
      if (t.stato === "fermo" && t.motivo) { pezzi.push(el("span", { classe: "dettaglio-testo", testo: "fermo: " + t.motivo })); }
      if (t.attende && t.attende.length) {
        pezzi.push(el("span", { testo: "aspetta " + t.attende.map(function (n) { return "#" + n; }).join(", ") }));
      }
    }
    if (t.note && t.note.length) { pezzi.push(el("span", { testo: quante(t.note.length, "1 nota", "note") })); }
    return pezzi.length ? el("p", { classe: "todo-dettagli" }, pezzi) : null;
  }

  function riga(t, contesto) {
    var chiuso = t.stato === "fatto" || t.stato === "scartato";
    var aperto = stato.aperto && stato.aperto.id === t.id ? stato.aperto.tipo : "";
    var scelto = stato.rotta.todo === t.id;
    var idPannello = "pannello-todo-" + t.id;
    var primo = chiuso
      ? bottone("Riprendi", "azione--bordo bottone-riprendi", function () {
        azione({ azione: "riprendi", id: t.id, titolo_atteso: t.titolo }, { ruolo: "riprendi" });
      }, { "data-ruolo": "riprendi", "aria-label": "Riprendi: " + t.titolo })
      : bottone("Fatto", "azione--bordo bottone-fatto", function () {
        azione({ azione: "fatto", id: t.id, titolo_atteso: t.titolo }, { ruolo: "fatto" });
      }, { "data-ruolo": "fatto", "aria-label": "Fatto: " + t.titolo });
    var azioni = el("div", { classe: "todo-azioni" }, [
      t.gruppo === "decidi" ? bottone("Ho deciso", "azione--testo", function () { apri(t.id, "decidi"); },
        { "data-ruolo": "decidi", "aria-expanded": aperto === "decidi" ? "true" : "false", "aria-controls": idPannello }) : null,
      bottone("Modifica", "azione--testo", function () { apri(t.id, "modifica"); },
        { "data-ruolo": "modifica", "aria-expanded": aperto === "modifica" ? "true" : "false", "aria-controls": idPannello })
    ]);
    var li = el("li", { classe: "todo" + (chiuso ? " todo--chiuso" : "") + (scelto ? " todo--scelto" : ""), "data-id": t.id }, [
      el("div", { classe: "todo-riga" }, [
        el("div", { classe: "todo-fatto" }, [primo]),
        el("div", { classe: "todo-corpo" }, [
          el("p", { classe: "todo-titolo" }, [
            el("span", { classe: "numero", testo: "#" + t.id }),
            el("a", { href: indirizzo(t.progetto, scelto ? null : t.id), "aria-current": scelto ? "true" : null,
              "data-ruolo": "apri", testo: t.titolo })
          ]),
          dettagli(t, contesto)
        ]),
        azioni
      ])
    ]);
    if (aperto === "decidi") { li.appendChild(pannelloDecidi(t, idPannello)); }
    if (aperto === "modifica") { li.appendChild(pannelloModifica(t, idPannello)); }
    return li;
  }

  function chiusoOra(id) {
    var t = perId(id);
    return !!t && (t.stato === "fatto" || t.stato === "scartato");
  }

  function apri(id, tipo) {
    var chiudi = stato.aperto && stato.aperto.id === id && stato.aperto.tipo === tipo;
    stato.aperto = chiudi ? null : { id: id, tipo: tipo, chiuso: chiusoOra(id) };
    if (chiudi && stato.inAttesa) {
      var nuova = stato.inAttesa;
      stato.dati = nuova;
      stato.testo = JSON.stringify(nuova);
      stato.inAttesa = null;
    }
    disegna();
    var riga = rigaDi(id);
    if (!riga) { return; }
    if (chiudi) { rimettiFuoco(id, tipo); return; }
    var primo = riga.querySelector(".todo-pannello input, .todo-pannello select");
    if (primo) { primo.focus(); }
  }

  function chiudiPannello(id, tipo) {
    if (stato.aperto) { apri(stato.aperto.id, stato.aperto.tipo); } else { rimettiFuoco(id, tipo); }
  }

  function campoTesto(id, etichetta, valore, altro) {
    var o = { id: id, type: "text", valore: valore || "", autocomplete: "off", "data-iniziale": valore || "" };
    Object.keys(altro || {}).forEach(function (k) { o[k] = altro[k]; });
    return [el("label", { "for": id, testo: etichetta }), el("input", o)];
  }

  function scelta(id, etichetta, valori, nomi, attuale) {
    return [el("label", { "for": id, testo: etichetta }),
      el("select", { id: id, "data-iniziale": attuale }, valori.map(function (v) {
        return el("option", { valore: v, testo: nomi[v], selected: v === attuale });
      }))];
  }

  function pannelloDecidi(t, idPannello) {
    var idCampo = "deciso-" + t.id;
    var form = el("form", { classe: "todo-pannello", id: idPannello, novalidate: true }, [
      el("div", { classe: "campo" }, campoTesto(idCampo, "Cosa hai deciso?", "", { maxlength: "500" })),
      el("p", { classe: "nota-aiuto", testo: "La scelta resta nelle note del todo, poi il lavoro passa a Claude." }),
      el("div", { classe: "pannello-azioni" }, [
        el("button", { type: "submit", classe: "azione azione--piena", testo: "Passa a Claude" }),
        bottone("Chiudi", "azione--testo", function () { chiudiPannello(t.id, "decidi"); })
      ])
    ]);
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var testo = $(idCampo).value.trim();
      if (!testo) { errore("Scrivi cosa hai deciso, per esempio «va bene il piano B»."); $(idCampo).focus(); return; }
      azione({ azione: "deciso", id: t.id, titolo_atteso: t.titolo, testo: testo }, { chiudi: true });
    });
    tastoEsc(form, t.id, "decidi");
    return form;
  }

  function pannelloModifica(t, idPannello) {
    var p = "m-" + t.id + "-";
    var chiuso = t.stato === "fatto" || t.stato === "scartato";
    var salva = el("form", { novalidate: true }, [
      el("div", { classe: "campi" }, [
        el("div", { classe: "campo campo--largo" }, campoTesto(p + "titolo", "Titolo", t.titolo, { maxlength: "300" })),
        el("div", { classe: "campo" }, campoTesto(p + "progetto", "Progetto", t.progetto, { list: "elenco-progetti", maxlength: "80" })),
        el("div", { classe: "campo" }, campoTesto(p + "scadenza", "Scadenza (vuota la toglie)", gma(t.scadenza),
          { placeholder: "venerdì, 10/10, domani", maxlength: "40" })),
        el("div", { classe: "campo" }, scelta(p + "chi", "Chi agisce", ["tu", "decidi", "io"], nomiChi(), t.chi)),
        el("div", { classe: "campo" }, scelta(p + "priorita", "Priorità", ["alta", "media", "bassa"], NOMI_PRIORITA, t.priorita)),
        el("div", { classe: "campo" }, scelta(p + "quando", "Quando", ["oggi", "settimana", "più avanti"], NOMI_QUANDO, t.quando)),
        el("div", { classe: "campo campo--largo" }, campoTesto(p + "perche", "Perché tocca a te", t.perche || "", { maxlength: "200" }))
      ]),
      el("div", { classe: "pannello-azioni" }, [
        el("button", { type: "submit", classe: "azione azione--piena", testo: "Salva" }),
        bottone("Chiudi", "azione--testo", function () { chiudiPannello(t.id, "modifica"); })
      ])
    ]);
    salva.addEventListener("submit", function (e) {
      e.preventDefault();
      var campi = {};
      var prima = { titolo: t.titolo, progetto: t.progetto, scadenza: gma(t.scadenza), chi: t.chi,
        priorita: t.priorita, quando: t.quando, perche: t.perche || "" };
      Object.keys(prima).forEach(function (k) {
        var valore = $(p + k).value.trim();
        if (valore !== prima[k]) { campi[k] = valore; }
      });
      if (!Object.keys(campi).length) { chiudiPannello(t.id, "modifica"); mostraEsito("Niente da salvare: il todo #" + t.id + " è come prima.", null); return; }
      azione({ azione: "modifica", id: t.id, titolo_atteso: t.titolo, campi: campi }, { chiudi: true, ruolo: "modifica" });
    });

    var idMotivo = p + "motivo";
    var sezioneStato = el("div", { classe: "pannello-sezione" }, [
      el("h3", { testo: "Stato" }),
      el("p", { classe: "nota-aiuto", testo: "Ora è «" + t.stato + "»" + (t.motivo ? ": " + t.motivo : "") + "." }),
      chiuso ? null : el("div", { classe: "riga-campo campo" },
        campoTesto(idMotivo, "Motivo, per Ferma e Scarta", "", { maxlength: "200" })),
      el("div", { classe: "pannello-azioni" }, bottoniStato(t, function () { var c = $(idMotivo); return c ? c.value.trim() : ""; },
        function () { if ($(idMotivo)) { $(idMotivo).focus(); } }))
    ]);

    var idNota = p + "nota";
    var note = el("form", { classe: "pannello-sezione", novalidate: true }, [
      el("h3", { testo: "Note" }),
      t.note.length ? el("ul", { classe: "note" }, t.note.map(function (n) { return el("li", { testo: n }); })) : null,
      el("div", { classe: "riga-campo campo" }, [
        el("label", { "for": idNota, testo: "Aggiungi una nota" }),
        el("textarea", { id: idNota, rows: "2", maxlength: "1000", "data-iniziale": "" })
      ]),
      el("p", { classe: "nota-aiuto", testo: "Le note restano nella storia del todo: non si annullano." }),
      el("div", { classe: "pannello-azioni" }, [el("button", { type: "submit", classe: "azione azione--bordo", testo: "Aggiungi la nota" })])
    ]);
    note.addEventListener("submit", function (e) { e.preventDefault(); salvaNota(t, idNota); });

    var box = el("div", { classe: "todo-pannello", id: idPannello }, [salva, sezioneStato, note]);
    tastoEsc(box, t.id, "modifica");
    return box;
  }

  // I passaggi di stato, gli stessi nel pannello «Modifica» e nel dettaglio.
  function bottoniStato(t, motivo, fuocoMotivo) {
    var chiuso = t.stato === "fatto" || t.stato === "scartato";
    var bottoni = [];
    if (t.stato === "da fare") {
      bottoni.push(bottone("Segna in corso", "azione--bordo", function () {
        azione({ azione: "inizia", id: t.id, titolo_atteso: t.titolo }, { chiudi: true, ruolo: "modifica" });
      }));
    }
    if (!chiuso && t.stato !== "fermo") {
      bottoni.push(bottone("Ferma", "azione--bordo", function () {
        var m = motivo();
        if (!m) { errore("Scrivi cosa aspetta il todo, per esempio «aspetto la risposta di Rossi»."); fuocoMotivo(); return; }
        azione({ azione: "ferma", id: t.id, titolo_atteso: t.titolo, motivo: m }, { chiudi: true, ruolo: "modifica" });
      }));
    }
    if (t.stato === "fermo" || chiuso) {
      bottoni.push(bottone("Riprendi", "azione--bordo", function () {
        azione({ azione: "riprendi", id: t.id, titolo_atteso: t.titolo }, { chiudi: true, ruolo: "modifica" });
      }));
    }
    if (!chiuso) {
      bottoni.push(bottone("Scarta", "azione--bordo", function () {
        azione({ azione: "scarta", id: t.id, titolo_atteso: t.titolo, motivo: motivo() }, { chiudi: true, ruolo: "modifica" });
      }));
    }
    return bottoni;
  }

  function salvaNota(t, idNota) {
    var testo = $(idNota).value.trim();
    if (!testo) { errore("La nota è vuota: scrivi qualcosa prima di aggiungerla."); $(idNota).focus(); return; }
    // La nota salvata esce dal campo prima del ridisegno, che rimette solo i campi non salvati.
    azione({ azione: "nota", id: t.id, titolo_atteso: t.titolo, testo: testo }, {
      fuoco: false,
      prima: function () { var campo = $(idNota); if (campo) { campo.value = ""; } }
    }).then(function (ok) {
      var campo = $(idNota);
      if (ok && campo) { campo.focus(); }
    });
  }

  function tastoEsc(nodo, id, tipo) {
    nodo.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { e.preventDefault(); chiudiPannello(id, tipo); }
    });
  }

  // --- il dettaglio di un todo ------------------------------------------------------

  function leggiScheda(id, fuoco) {
    return chiama("GET", "/api/todo?id=" + encodeURIComponent(id)).then(function (r) {
      if (stato.rotta.todo !== id) { return; }
      stato.scheda = r.ok && r.dati && r.dati.todo ? { id: id, todo: r.dati.todo }
        : { id: id, errore: r.dati && r.dati.errore ? r.dati.errore : "Questo todo non si apre: forse è stato rinumerato. Torna al progetto." };
      var box = $("dettaglio");
      if (!box) { return; }
      var scritti = ricordaCampi();
      svuota(box);
      schedaCorpo().forEach(function (n) { if (n) { box.appendChild(n); } });
      rimettiCampi(scritti);
      if (fuoco) { box.focus({ preventScroll: true }); if (window.matchMedia("(max-width: 900px)").matches) { box.scrollIntoView({ block: "start" }); } }
    }).catch(function () { disconnesso(); });
  }

  function chiudiDettaglio() {
    return el("a", { classe: "dettaglio-chiudi", href: indirizzo(stato.rotta.progetto, null), testo: "Chiudi il dettaglio" });
  }

  function schedaCorpo() {
    var s = stato.scheda;
    if (!s || s.id !== stato.rotta.todo) {
      return [el("p", { classe: "nota-aiuto", testo: "Leggo il todo #" + stato.rotta.todo + "…" })];
    }
    if (s.errore) {
      return [chiudiDettaglio(), el("p", { classe: "dettaglio-errore", testo: s.errore })];
    }
    var t = s.todo;
    var chiuso = t.stato === "fatto" || t.stato === "scartato";
    var campi = [
      ["Chi agisce", t.gruppo ? segno(t, true) : null],
      ["Stato", t.stato + (t.motivo ? ": " + t.motivo : "")],
      ["Scadenza", t.scadenza ? gma(t.scadenza) + " · " + t.scadenza_testo : null],
      ["Priorità", NOMI_PRIORITA[t.priorita] || t.priorita],
      ["Quando", NOMI_QUANDO[t.quando] || t.quando],
      ["Perché tocca a te", t.perche],
      ["Progetto", t.progetto]
    ].filter(function (c) { return c[1]; });
    var dl = el("dl", { classe: "dettaglio-campi" });
    campi.forEach(function (c) {
      dl.appendChild(el("dt", { testo: c[0] }));
      dl.appendChild(el("dd", {}, [c[1]]));
    });
    function collegati(etichetta, numeri) {
      if (!numeri || !numeri.length) { return null; }
      return el("p", { classe: "dettaglio-legami" }, [etichetta + " "].concat(numeri.map(function (n, i) {
        var altro = perId(n);
        return el("span", {}, [i ? ", " : "", el("a", { href: indirizzo(altro ? altro.progetto : t.progetto, n),
          testo: "#" + n + (altro ? " " + altro.titolo : "") })]);
      })));
    }
    var idNota = "d-" + t.id + "-nota";
    var formNota = el("form", { classe: "dettaglio-nota", novalidate: true }, [
      el("label", { "for": idNota, testo: "Aggiungi una nota" }),
      el("textarea", { id: idNota, rows: "2", maxlength: "1000", "data-iniziale": "" }),
      el("div", { classe: "pannello-azioni" }, [el("button", { type: "submit", classe: "azione azione--bordo", testo: "Aggiungi la nota" })])
    ]);
    formNota.addEventListener("submit", function (e) { e.preventDefault(); salvaNota(t, idNota); });
    var idMotivo = "d-" + t.id + "-motivo";
    function passa(nome) {
      return function () { azione({ azione: nome, id: t.id, titolo_atteso: t.titolo }, { fuoco: false }); };
    }
    var primarie = chiuso ? [bottone("Riprendi", "azione--piena", passa("riprendi"))] : [
      bottone("Fatto", "azione--piena bottone-fatto", passa("fatto")),
      t.gruppo === "decidi" ? bottone("Ho deciso", "azione--bordo", function () { apri(t.id, "decidi"); }) : null,
      t.gruppo !== "decidi" && t.stato === "da fare" ? bottone("Segna in corso", "azione--bordo", passa("inizia")) : null,
      t.stato === "fermo" ? bottone("Riprendi", "azione--bordo", passa("riprendi")) : null
    ];
    // Ferma e Scarta chiedono un motivo: il campo compare solo quando la persona li sceglie.
    var motivo = null, conferma = null, scelta = "";
    function chiedi(tipo) {
      return function () {
        scelta = tipo;
        motivo.hidden = false;
        motivo.querySelector("label").textContent = tipo === "ferma" ? "Cosa aspetta?" : "Perché lo scarti? (facoltativo)";
        conferma.textContent = tipo === "ferma" ? "Ferma il todo" : "Scarta il todo";
        $(idMotivo).focus();
      };
    }
    if (!chiuso) {
      conferma = bottone("Ferma il todo", "azione--bordo", function () {
        var m = $(idMotivo).value.trim();
        if (scelta === "ferma" && !m) { errore("Scrivi cosa aspetta il todo, per esempio «aspetto la risposta di Rossi»."); $(idMotivo).focus(); return; }
        azione({ azione: scelta, id: t.id, titolo_atteso: t.titolo, motivo: m }, { fuoco: false });
      });
      motivo = el("div", { classe: "campo dettaglio-motivo", hidden: true }, campoTesto(idMotivo, "Cosa aspetta?", "", { maxlength: "200" })
        .concat([el("div", { classe: "pannello-azioni" }, [conferma])]));
    }
    var secondarie = chiuso ? [] : [
      t.stato !== "fermo" ? bottone("Ferma", "azione--testo", chiedi("ferma")) : null,
      bottone("Scarta", "azione--testo", chiedi("scarta"))
    ];
    return [
      chiudiDettaglio(),
      el("h2", { classe: "dettaglio-titolo" }, [el("span", { classe: "numero", testo: "#" + t.id }), t.titolo]),
      dl,
      collegati("Aspetta", t.attende),
      collegati("Sblocca", t.sblocca),
      el("div", { classe: "pannello-azioni dettaglio-azioni" }, primarie),
      secondarie.length ? el("div", { classe: "dettaglio-secondarie" }, secondarie) : null,
      motivo,
      el("section", { classe: "dettaglio-sezione", "aria-label": "Note" }, [
        el("h3", { testo: "Note" }),
        t.note_datate.length ? el("ul", { classe: "note" }, t.note_datate.map(function (n) {
          return el("li", {}, [el("span", { classe: "momento", testo: momento(n.ts) }), n.testo]);
        })) : el("p", { classe: "nota-aiuto", testo: "Ancora nessuna nota." }),
        formNota
      ]),
      el("section", { classe: "dettaglio-sezione", "aria-label": "Storia" }, [
        el("h3", { testo: "Storia" }),
        el("ol", { classe: "storia" }, t.storia.slice().reverse().map(function (e) {
          return el("li", { classe: e.dati && e.dati.annullo ? "storia--annullo" : null }, [
            el("span", { classe: "momento", testo: momento(e.ts) }), passo(e)]);
        }))
      ])
    ];
  }

  // Un evento della storia in parole, come lo direbbe la persona.
  function passo(e) {
    var d = e.dati || {};
    var coda = d.annullo ? " (annulla il passo prima)" : "";
    if (e.tipo === "crea") { return "Creato"; }
    if (e.tipo === "nota") { return "Nota: " + (d.testo || ""); }
    if (e.tipo === "stato") { return "Stato: " + d.stato + (d.motivo ? ", " + d.motivo : "") + coda; }
    if (e.tipo === "dopo") {
      if (d.aggiungi !== undefined) { return "Aspetta #" + d.aggiungi; }
      return "Non aspetta più #" + d.togli;
    }
    if (e.tipo === "modifica") {
      var nomi = nomiChi();
      var pezzi = Object.keys(d).filter(function (k) { return k !== "annullo"; }).map(function (k) {
        var v = d[k];
        if (k === "chi") { v = nomi[v] || v; }
        if (k === "scadenza") { v = v ? gma(v) : "nessuna"; }
        return (NOMI_CAMPI[k] || k) + " → " + v;
      });
      return "Cambiato: " + pezzi.join(", ") + coda;
    }
    return e.tipo;
  }

  // --- avvio ------------------------------------------------------------------------

  function aggiungi(e) {
    e.preventDefault();
    var campo = $("nuovo-titolo");
    var titolo = campo.value.trim();
    if (!titolo) { errore("Scrivi cosa c'è da fare, poi premi Aggiungi."); campo.focus(); return; }
    var chi = document.querySelector('input[name="chi"]:checked');
    var campi = { titolo: titolo, progetto: $("nuovo-progetto").value.trim(), chi: chi ? chi.value : "tu",
      priorita: $("nuova-priorita").value };
    var scadenza = $("nuova-scadenza").value.trim();
    if (scadenza) { campi.scadenza = scadenza; }
    azione({ azione: "aggiungi", campi: campi }, {
      prima: function () { campo.value = ""; $("nuova-scadenza").value = ""; }
    }).then(function () { campo.focus(); });
  }

  function avvia() {
    $("aggiunta").addEventListener("submit", aggiungi);
    $("annulla").addEventListener("click", annulla);
    $("spegni").addEventListener("click", spegni);
    document.addEventListener("focusout", function () { setTimeout(forseApplica, 0); });
    document.addEventListener("visibilitychange", function () {
      if (!document.hidden && !stato.spento) { leggi(); } else { pianifica(); }
    });
    document.addEventListener("keydown", function (e) {
      // Esc chiude il dettaglio, se nessun pannello in linea lo chiede prima.
      if (e.key === "Escape" && stato.rotta.todo && !stato.aperto && !e.defaultPrevented) { vai(stato.rotta.progetto, null); }
    });
    window.addEventListener("hashchange", cambiaRotta);
    stato.rotta = leggiRotta();
    leggi().then(function () { if (stato.rotta.todo) { leggiScheda(stato.rotta.todo); } });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", avvia);
  } else {
    avvia();
  }
}());
