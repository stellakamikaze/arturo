/* Arturo web: la pagina dei todo. Script classico, nessuna dipendenza, nessuna rete esterna.
   I dati entrano nella pagina solo con createElement e textContent: un titolo con dentro
   del codice HTML resta testo. Ogni scrittura passa da /api/azione, cioè da todo_store. */
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
  var SCHEDE = ["chi", "progetti", "scadenze"];
  var ESEMPI = ["Mandare il preventivo per la rassegna", "Rileggere il capitolo 3", "Cercare tre fonti per il bando"];
  var NOMI_QUANDO = { "oggi": "Oggi", "settimana": "Questa settimana", "più avanti": "Più avanti" };
  var NOMI_PRIORITA = { alta: "Alta", media: "Media", bassa: "Bassa" };
  var COMANDO = "python3 ~/.claude/bin/arturo web";

  var stato = {
    dati: null,        // {vista, progetti, partenza}: l'ultima lettura disegnata
    testo: "",         // la stessa lettura come JSON, per sapere se è cambiata
    inAttesa: null,    // una lettura arrivata mentre la persona scrive in un pannello
    scheda: "chi",
    progetto: "",
    chiusi: false,
    aperto: null,      // il pannello in linea aperto: {id, tipo: "modifica" | "decidi"}
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
  function dopoGiorni(iso, n) {
    var d = dataDa(iso);
    d.setUTCDate(d.getUTCDate() + n);
    return d;
  }
  function gma(iso) {
    if (!iso) { return ""; }
    var p = iso.split("-");
    return p[2] + "/" + p[1] + "/" + p[0];
  }
  function tondo(titolo) {
    return titolo.charAt(0) + titolo.slice(1).toLowerCase();
  }
  // I nomi di «chi» vengono dai titoli dei gruppi dello store: gruppi, chip, select e radio
  // dicono la stessa cosa con le stesse parole.
  function nomiChi() {
    var nomi = {};
    stato.dati.vista.gruppi.forEach(function (g) { nomi[g.tipo] = tondo(g.titolo); });
    return nomi;
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
    return { vista: dati.vista, progetti: dati.progetti,
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
  }

  // Un pannello aperto resta aperto quando arriva l'esito di un'altra azione (una nota, «Fatto»
  // su un'altra riga). Il ridisegno lo ricostruisce: i campi che la persona ha cambiato e non ha
  // ancora salvato tornano al loro posto. Ogni campo ricorda in data-iniziale il valore disegnato.
  function ricordaCampi() {
    var scritti = {};
    Array.prototype.forEach.call(document.querySelectorAll(".todo-pannello [data-iniziale]"), function (n) {
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
    var righe = Array.prototype.slice.call(document.querySelectorAll(".pannello:not([hidden]) .todo"));
    for (var i = 0; i < righe.length; i += 1) {
      if (righe[i].getAttribute("data-id") === String(id)) {
        var dopo = righe[i + 1] || righe[i - 1];
        return dopo ? dopo.getAttribute("data-id") : null;
      }
    }
    return null;
  }

  function rigaDi(id) {
    return document.querySelector('.pannello:not([hidden]) .todo[data-id="' + String(Number(id)) + '"]');
  }

  function rimettiFuoco(id, ruolo) {
    var riga = rigaDi(id);
    if (!riga) { return false; }
    var bersaglio = (ruolo && riga.querySelector('[data-ruolo="' + ruolo + '"]')) || riga.querySelector("button");
    if (bersaglio) { bersaglio.focus(); }
    return !!bersaglio;
  }

  // Dopo un'azione il fuoco va alla stessa riga, poi alla seguente, poi al titolo del gruppo.
  function fuocoDopo(id, prossimo, ruolo) {
    if (rimettiFuoco(id, ruolo)) { return; }
    if (prossimo && rimettiFuoco(prossimo)) { return; }
    var titolo = document.querySelector(".pannello:not([hidden]) h2");
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

  // --- disegno --------------------------------------------------------------------

  function tuttiAperti() {
    var fuori = [];
    stato.dati.vista.gruppi.forEach(function (g) {
      g.todo.forEach(function (t) { if (!stato.progetto || t.progetto === stato.progetto) { fuori.push(t); } });
    });
    return fuori;
  }
  function tuttiChiusi() {
    if (!stato.chiusi) { return []; }
    return (stato.dati.vista.chiusi_todo || []).filter(function (t) {
      return !stato.progetto || t.progetto === stato.progetto;
    });
  }

  function disegna() {
    var v = stato.dati.vista;
    $("oggi").textContent = dataLunga(v.oggi);
    disegnaProgetti();
    disegnaSintesi();
    disegnaAvvisi(v.avvisi || []);
    disegnaSceltaChi();
    SCHEDE.forEach(function (nome) {
      var pannello = $("pannello-" + nome);
      svuota(pannello);
      if (nome !== stato.scheda) { return; }
      var aperti = tuttiAperti();
      var chiusi = tuttiChiusi();
      if (!aperti.length && !chiusi.length) {
        pannello.appendChild(vuoto());
        return;
      }
      if (nome === "chi") { disegnaChi(pannello, chiusi); }
      else if (nome === "progetti") { disegnaPerProgetto(pannello, aperti, chiusi); }
      else { disegnaAgenda(pannello, aperti, chiusi); }
    });
    // Il todo del pannello aperto non è più nella lista (chiuso con «Fatto», tolto dal filtro):
    // il pannello non c'è più, e le letture successive arrivano di nuovo nella pagina.
    if (stato.aperto && !$("pannello-todo-" + stato.aperto.id)) { stato.aperto = null; }
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
    var filtro = $("filtro-progetto");
    var lista = $("elenco-progetti");
    svuota(lista);
    while (filtro.options.length > 1) { filtro.remove(1); }
    var conPartenza = nomi.indexOf(partenza) === -1 ? nomi.concat([partenza]).sort() : nomi;
    conPartenza.forEach(function (n) { lista.appendChild(el("option", { valore: n })); });
    nomi.forEach(function (n) { filtro.appendChild(el("option", { valore: n, testo: n })); });
    if (stato.progetto && nomi.indexOf(stato.progetto) === -1) { stato.progetto = ""; }
    filtro.value = stato.progetto;
    if (stato.primo) {
      stato.primo = false;
      if (!$("nuovo-progetto").value) { $("nuovo-progetto").value = partenza; }
    }
  }

  function quante(n, una, molte) {
    return n === 1 ? una : n + " " + molte;
  }

  function disegnaSintesi() {
    var aperti = tuttiAperti();
    var tu = aperti.filter(function (t) { return t.gruppo === "tu"; });
    var scaduti = tu.filter(function (t) { return t.giorni !== null && t.giorni < 0; }).length;
    var decidi = aperti.filter(function (t) { return t.gruppo === "decidi"; }).length;
    var io = aperti.filter(function (t) { return t.gruppo === "io"; }).length;
    var frasi = [];
    if (!aperti.length) {
      frasi.push(stato.progetto ? "Niente di aperto in «" + stato.progetto + "»." : "Niente di aperto. Il cielo è sgombro.");
    } else {
      frasi.push(tu.length ? "Tocca a te: " + quante(tu.length, "una cosa.", "cose.") : "Niente tocca a te adesso.");
      if (scaduti) { frasi.push(tu.length === 1 ? "È scaduta." : (scaduti === 1 ? "Una è scaduta." : scaduti + " sono scadute.")); }
      if (decidi) { frasi.push(decidi === 1 ? "Una aspetta una tua scelta." : decidi + " aspettano una tua scelta."); }
      if (io) { frasi.push(io === 1 ? "Claude ne ha in mano una." : "Claude ne ha in mano " + io + "."); }
    }
    $("sintesi").textContent = frasi.join(" ");
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

  function vuoto() {
    var campo = $("nuovo-titolo");
    return el("div", { classe: "vuoto" }, [
      el("h2", { tabindex: "-1", testo: stato.progetto ? "Nessuna cosa da fare aperta in «" + stato.progetto + "»." : "Nessuna cosa da fare aperta." }),
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

  function testaGruppo(titolo, conto, descrizione) {
    return [
      el("div", { classe: "gruppo-testa" }, [
        el("h2", { tabindex: "-1", testo: titolo }),
        conto === null ? null : el("span", { classe: "conto", testo: String(conto) })
      ]),
      descrizione ? el("p", { classe: "gruppo-descr", testo: descrizione }) : null
    ];
  }

  function lista(todo, contesto) {
    return el("ul", { classe: "lista" }, todo.map(function (t) { return riga(t, contesto); }));
  }

  function disegnaChi(pannello, chiusi) {
    stato.dati.vista.gruppi.forEach(function (g) {
      var dentro = g.todo.filter(function (t) { return !stato.progetto || t.progetto === stato.progetto; });
      var sezione = el("section", { classe: "gruppo" }, testaGruppo(tondo(g.titolo), dentro.length, g.descrizione));
      sezione.appendChild(dentro.length ? lista(dentro, { progetto: !stato.progetto })
        : el("p", { classe: "gruppo-vuoto", testo: "Niente qui per ora." }));
      pannello.appendChild(sezione);
    });
    sezioneChiusi(pannello, chiusi, { progetto: !stato.progetto });
  }

  function sezioneChiusi(pannello, chiusi, contesto) {
    if (!chiusi.length) { return; }
    var sezione = el("section", { classe: "gruppo" }, testaGruppo("Chiusi", chiusi.length, "Fatti o scartati. Niente si cancella: puoi riprenderli."));
    sezione.appendChild(lista(chiusi, contesto));
    pannello.appendChild(sezione);
  }

  function conti(c) {
    var pezzi = [c.aperti === 0 ? "nessuno aperto" : quante(c.aperti, "1 aperto", "aperti")];
    if (c.scaduti) { pezzi.push(el("span", { classe: "scaduti", testo: quante(c.scaduti, "1 scaduto", "scaduti") })); }
    if (c.fermi) { pezzi.push(quante(c.fermi, "1 fermo", "fermi")); }
    if (c.chiusi) { pezzi.push(quante(c.chiusi, "1 chiuso", "chiusi")); }
    var figli = [];
    pezzi.forEach(function (p, i) {
      if (i) { figli.push(" · "); }
      figli.push(p);
    });
    return el("p", { classe: "conti" }, figli);
  }

  function disegnaPerProgetto(pannello, aperti, chiusi) {
    var tutti = stato.dati.progetti;
    var partenza = stato.dati.partenza;
    var nomi = Object.keys(tutti).filter(function (n) { return !stato.progetto || n === stato.progetto; });
    nomi.sort(function (a, b) {
      if (a === partenza) { return -1; }
      if (b === partenza) { return 1; }
      return (tutti[b].aperti - tutti[a].aperti) || (a < b ? -1 : 1);
    });
    nomi.forEach(function (nome) {
      var suoi = aperti.filter(function (t) { return t.progetto === nome; });
      var suoiChiusi = chiusi.filter(function (t) { return t.progetto === nome; });
      if (!suoi.length && !suoiChiusi.length) { return; }
      var sezione = el("section", { classe: "gruppo" }, testaGruppo(nome, null, null));
      sezione.appendChild(conti(tutti[nome]));
      sezione.appendChild(lista(suoi.concat(suoiChiusi), { chi: true }));
      pannello.appendChild(sezione);
    });
  }

  function disegnaAgenda(pannello, aperti, chiusi) {
    var oggi = stato.dati.vista.oggi;
    var caselle = [];
    function casella(chiave, titolo, descrizione, classe) {
      var c = { chiave: chiave, titolo: titolo, descrizione: descrizione, classe: classe, todo: [] };
      caselle.push(c);
      return c;
    }
    var scaduti = casella("scaduti", "Scaduti", null, "giorno--scaduti");
    var diOggi = casella("oggi", "Oggi", dataLunga(oggi), "giorno--oggi");
    var giorni = [casella("domani", "Domani", dataBreve(dopoGiorni(oggi, 1)), "")];
    for (var g = 2; g <= 13; g += 1) { giorni.push(casella("g" + g, dataBreve(dopoGiorni(oggi, g)), null, "")); }
    var avanti = casella("avanti", "Più avanti", "Da due settimane in poi.", "");
    var senza = casella("senza", "Senza scadenza", null, "");
    aperti.forEach(function (t) {
      if (t.giorni === null) { senza.todo.push(t); }
      else if (t.giorni < 0) { scaduti.todo.push(t); }
      else if (t.giorni === 0) { diOggi.todo.push(t); }
      else if (t.giorni <= 13) { giorni[t.giorni - 1].todo.push(t); }
      else { avanti.todo.push(t); }
    });
    scaduti.todo.sort(function (a, b) { return a.giorni - b.giorni; });
    avanti.todo.sort(function (a, b) { return a.giorni - b.giorni; });
    var agenda = el("ol", { classe: "agenda" });
    caselle.forEach(function (c) {
      if (!c.todo.length && c.chiave !== "oggi") { return; }
      var testa = el("div", { classe: "giorno-testa" }, [
        el("h2", { tabindex: "-1", testo: c.titolo }),
        c.descrizione ? el("p", { classe: "gruppo-descr", testo: c.descrizione }) : null
      ]);
      var contesto = { progetto: !stato.progetto, scadenza: c.chiave === "scaduti" || c.chiave === "avanti" };
      agenda.appendChild(el("li", { classe: "giorno " + c.classe }, [
        c.chiave === "oggi" ? el("span", { classe: "stella", "aria-hidden": "true" }) : null,
        testa,
        c.todo.length ? lista(c.todo, contesto) : el("p", { classe: "gruppo-vuoto", testo: "Niente scade oggi." })
      ]));
    });
    pannello.appendChild(agenda);
    sezioneChiusi(pannello, chiusi, { progetto: !stato.progetto });
  }

  // --- una riga ---------------------------------------------------------------------

  function dettagli(t, contesto) {
    var pezzi = [];
    var chiuso = t.stato === "fatto" || t.stato === "scartato";
    if (contesto.progetto) { pezzi.push(el("span", { classe: "chip", testo: t.progetto })); }
    if (contesto.chi && !chiuso) {
      var nomi = nomiChi();
      pezzi.push(el("span", { classe: "chip", testo: t.gruppo === "fermo" ? nomi.fermo : nomi[t.chi] }));
    }
    if (chiuso) {
      pezzi.push(el("span", { classe: "esito esito--" + t.stato, testo: t.stato }));
      if (t.motivo) { pezzi.push(el("span", { classe: "dettaglio", testo: t.motivo })); }
    } else {
      if (t.stato === "in corso") { pezzi.push(el("span", { classe: "esito esito--corso", testo: "in corso" })); }
      // Nell'agenda il giorno è già il titolo: la scadenza si ripete solo tra gli scaduti e più avanti.
      if (t.giorni !== null && contesto.scadenza !== false) {
        if (t.giorni < 0) { pezzi.push(el("span", { classe: "esito esito--scaduto", testo: t.scadenza_testo })); }
        else if (t.giorni === 0) { pezzi.push(el("span", { classe: "esito esito--oggi", testo: t.scadenza_testo })); }
        else { pezzi.push(el("span", { testo: t.scadenza_testo + (t.giorni > 1 ? " · " + dataBreve(dataDa(t.scadenza)) : "") })); }
      }
      if (t.quando === "oggi" && t.giorni !== 0) { pezzi.push(el("span", { testo: "per oggi" })); }
      if (t.priorita === "alta") { pezzi.push(el("span", { testo: "priorità alta" })); }
      if (t.perche) { pezzi.push(el("span", { classe: "dettaglio", testo: "perché: " + t.perche })); }
      if (t.stato === "fermo" && t.motivo) { pezzi.push(el("span", { classe: "dettaglio", testo: "fermo: " + t.motivo })); }
      if (t.attende && t.attende.length) {
        pezzi.push(el("span", { testo: "aspetta " + t.attende.map(function (n) { return "#" + n; }).join(", ") }));
      }
    }
    return pezzi.length ? el("p", { classe: "todo-dettagli" }, pezzi) : null;
  }

  function riga(t, contesto) {
    var chiuso = t.stato === "fatto" || t.stato === "scartato";
    var aperto = stato.aperto && stato.aperto.id === t.id ? stato.aperto.tipo : "";
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
    var li = el("li", { classe: "todo" + (chiuso ? " todo--chiuso" : ""), "data-id": t.id }, [
      el("div", { classe: "todo-riga" }, [
        el("div", { classe: "todo-fatto" }, [primo]),
        el("div", { classe: "todo-corpo" }, [
          el("p", { classe: "todo-titolo" }, [el("span", { classe: "numero", testo: "#" + t.id }), t.titolo]),
          dettagli(t, contesto)
        ]),
        azioni
      ])
    ]);
    if (aperto === "decidi") { li.appendChild(pannelloDecidi(t, idPannello)); }
    if (aperto === "modifica") { li.appendChild(pannelloModifica(t, idPannello)); }
    return li;
  }

  function apri(id, tipo) {
    var chiudi = stato.aperto && stato.aperto.id === id && stato.aperto.tipo === tipo;
    stato.aperto = chiudi ? null : { id: id, tipo: tipo };
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
    var bottoni = [];
    if (t.stato === "da fare") {
      bottoni.push(bottone("Segna in corso", "azione--bordo", function () {
        azione({ azione: "inizia", id: t.id, titolo_atteso: t.titolo }, { chiudi: true, ruolo: "modifica" });
      }));
    }
    if (!chiuso && t.stato !== "fermo") {
      bottoni.push(bottone("Ferma", "azione--bordo", function () {
        var motivo = $(idMotivo).value.trim();
        if (!motivo) { errore("Scrivi cosa aspetta il todo, per esempio «aspetto la risposta di Rossi»."); $(idMotivo).focus(); return; }
        azione({ azione: "ferma", id: t.id, titolo_atteso: t.titolo, motivo: motivo }, { chiudi: true, ruolo: "modifica" });
      }));
    }
    if (t.stato === "fermo" || chiuso) {
      bottoni.push(bottone("Riprendi", "azione--bordo", function () {
        azione({ azione: "riprendi", id: t.id, titolo_atteso: t.titolo }, { chiudi: true, ruolo: "modifica" });
      }));
    }
    if (!chiuso) {
      bottoni.push(bottone("Scarta", "azione--bordo", function () {
        azione({ azione: "scarta", id: t.id, titolo_atteso: t.titolo, motivo: $(idMotivo).value.trim() },
          { chiudi: true, ruolo: "modifica" });
      }));
    }
    var statoTesto = "Ora è «" + t.stato + "»" + (t.motivo ? ": " + t.motivo : "") + ".";
    var sezioneStato = el("div", { classe: "pannello-sezione" }, [
      el("h3", { testo: "Stato" }),
      el("p", { classe: "nota-aiuto", testo: statoTesto }),
      chiuso ? null : el("div", { classe: "riga-campo campo" },
        campoTesto(idMotivo, "Motivo, per Ferma e Scarta", "", { maxlength: "200" })),
      el("div", { classe: "pannello-azioni" }, bottoni)
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
    note.addEventListener("submit", function (e) {
      e.preventDefault();
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
    });

    var box = el("div", { classe: "todo-pannello", id: idPannello }, [salva, sezioneStato, note]);
    tastoEsc(box, t.id, "modifica");
    return box;
  }

  function tastoEsc(nodo, id, tipo) {
    nodo.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { e.preventDefault(); chiudiPannello(id, tipo); }
    });
  }

  // --- schede -----------------------------------------------------------------------

  function seleziona(nome, conFuoco) {
    if (SCHEDE.indexOf(nome) === -1) { nome = "chi"; }
    stato.scheda = nome;
    SCHEDE.forEach(function (n) {
      var scheda = $("scheda-" + n);
      var attiva = n === nome;
      scheda.setAttribute("aria-selected", attiva ? "true" : "false");
      scheda.tabIndex = attiva ? 0 : -1;
      $("pannello-" + n).hidden = !attiva;
    });
    if (conFuoco) { $("scheda-" + nome).focus(); }
    try { history.replaceState(null, "", "#" + nome); } catch (e) { /* senza cronologia la scheda resta comunque */ }
    if (stato.dati) {
      stato.aperto = null;
      if (stato.inAttesa) { var nuova = stato.inAttesa; stato.dati = nuova; stato.testo = JSON.stringify(nuova); stato.inAttesa = null; }
      disegna();
    }
  }

  function tastiSchede(e) {
    var i = SCHEDE.indexOf(stato.scheda);
    var nuovo = null;
    if (e.key === "ArrowRight") { nuovo = SCHEDE[(i + 1) % SCHEDE.length]; }
    else if (e.key === "ArrowLeft") { nuovo = SCHEDE[(i + SCHEDE.length - 1) % SCHEDE.length]; }
    else if (e.key === "Home") { nuovo = SCHEDE[0]; }
    else if (e.key === "End") { nuovo = SCHEDE[SCHEDE.length - 1]; }
    if (nuovo) { e.preventDefault(); seleziona(nuovo, true); }
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
    $("filtro-progetto").addEventListener("change", function (e) {
      stato.progetto = e.target.value;
      stato.aperto = null;
      if (stato.dati) { disegna(); }
    });
    $("mostra-chiusi").addEventListener("change", function (e) {
      stato.chiusi = e.target.checked;
      if (stato.dati) { disegna(); }
    });
    SCHEDE.forEach(function (n) {
      $("scheda-" + n).addEventListener("click", function () { seleziona(n, false); });
    });
    document.querySelector('[role="tablist"]').addEventListener("keydown", tastiSchede);
    document.addEventListener("focusout", function () { setTimeout(forseApplica, 0); });
    document.addEventListener("visibilitychange", function () {
      if (!document.hidden && !stato.spento) { leggi(); } else { pianifica(); }
    });
    window.addEventListener("hashchange", function () { seleziona(location.hash.slice(1), false); });
    seleziona(location.hash.slice(1) || "chi", false);
    leggi();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", avvia);
  } else {
    avvia();
  }
}());
