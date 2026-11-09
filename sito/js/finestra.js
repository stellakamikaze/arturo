// Lo script della pagina /finestra/: le otto schede da sfogliare e le scene dentro ciascuna (9/11/2026).
// Fuori dall'HTML per la CSP. Senza script il binario scorre lo stesso e ogni scena mostra il suo stato
// finito: lo script la riporta all'inizio e la rende cliccabile.
(function () {
  "use strict";
  var d = document;
  var calmo = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var attendi = function (ms) { return new Promise(function (ok) { setTimeout(ok, calmo ? 0 : ms); }); };
  var $ = function (sel, dove) { return (dove || d).querySelector(sel); };
  var $$ = function (sel, dove) { return Array.prototype.slice.call((dove || d).querySelectorAll(sel)); };

  function riga(dove, classe, testo, html) {
    var p = d.createElement("p");
    if (classe) p.className = classe;
    p.classList.add("entra");
    if (html) p.innerHTML = html; else p.textContent = testo;
    dove.appendChild(p);
    return p;
  }
  function pulsanti(dove, voci, scelta) {
    dove.innerHTML = "";
    voci.forEach(function (v) {
      var b = d.createElement("button");
      b.type = "button";
      b.textContent = v.testo;
      b.addEventListener("click", function () { scelta(v); });
      dove.appendChild(b);
    });
    dove.hidden = voci.length === 0;
  }
  function stato(el, classe, testo) {
    if (!el) return;
    el.classList.remove("lavora", "aspetta");
    if (classe) el.classList.add(classe);
    var span = el.querySelector("span");
    (span || el).textContent = testo;
  }

  // ---------- il binario ----------
  var binario = $("#binario");
  if (!binario) return;
  var schede = $$(".scheda", binario);
  var conta = $("#conta"), guida = $("#guida-schede");
  var indietro = $("#indietro"), avanti = $("#avanti");
  var passi = $$(".passi-schede button");
  var qui = 0;
  conta.hidden = false;
  guida.hidden = false;

  function vai(n) {
    n = Math.max(0, Math.min(schede.length - 1, n));
    binario.scrollTo({ left: n * binario.clientWidth, behavior: calmo ? "auto" : "smooth" });
  }
  function aggiorna() {
    var n = Math.round(binario.scrollLeft / Math.max(1, binario.clientWidth));
    if (n === qui && conta.textContent) return;
    qui = n;
    conta.textContent = (n + 1) + " di " + schede.length;
    passi.forEach(function (b, i) { b.setAttribute("aria-current", i === n ? "true" : "false"); });
    indietro.disabled = n === 0;
    avanti.disabled = n === schede.length - 1;
  }
  var inAttesa = false;
  binario.addEventListener("scroll", function () {
    if (inAttesa) return;
    inAttesa = true;
    requestAnimationFrame(function () { inAttesa = false; aggiorna(); });
  }, { passive: true });
  // Al cambio di misura la scheda la rimette a posto lo scroll-snap del browser.
  indietro.addEventListener("click", function () { vai(qui - 1); });
  avanti.addEventListener("click", function () { vai(qui + 1); });
  passi.forEach(function (b) { b.addEventListener("click", function () { vai(+b.getAttribute("data-a")); }); });
  binario.addEventListener("keydown", function (e) {
    if (e.target.closest("input, textarea")) return;
    if (e.key === "ArrowRight") { e.preventDefault(); vai(qui + 1); }
    if (e.key === "ArrowLeft") { e.preventDefault(); vai(qui - 1); }
  });
  conta.textContent = "";
  aggiorna();

  // ---------- 1. le domande ----------
  (function () {
    var s = $('[data-scena="domande"]');
    if (!s) return;
    var righe = $(".dialogo__righe", s), risposte = $(".risposte", s);
    $$("[data-dove]", s).forEach(function (b) {
      b.addEventListener("click", function () {
        var term = b.getAttribute("data-dove") === "term";
        s.classList.toggle("dialogo--term", term);
        s.classList.toggle("dialogo--chat", !term);
        $$("[data-dove]", s).forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
      });
    });
    var COSE = {
      "Ricette della nonna": [{ testo: "Scegliere le foto per il primo capitolo", chi: "tu" }, { testo: "Rimpicciolire le foto, sono enormi", chi: "io" }],
      "Negozio bici": [{ testo: "Fotografare le bici nuove", chi: "tu" }, { testo: "Mettere i prezzi nuovi nel sito", chi: "io" }],
      "Tesi magistrale": [{ testo: "Finire il capitolo 3", chi: "tu" }, { testo: "Sistemare la bibliografia", chi: "io" }]
    };
    function inizio() {
      righe.innerHTML = "";
      riga(righe, "", "Su cosa lavori in questo periodo? Dimmi le cose che porti avanti, anche quelle piccole.");
      pulsanti(risposte, [
        { testo: "Un libro di ricette con mia nonna", nome: "Ricette della nonna" },
        { testo: "Il sito del negozio di bici", nome: "Negozio bici" },
        { testo: "La tesi di magistrale", nome: "Tesi magistrale" }
      ], progetto);
    }
    async function progetto(v) {
      pulsanti(risposte, [], null);
      riga(righe, "persona", v.testo + ".");
      await attendi(500);
      riga(righe, "", "Ne faccio un progetto, \"" + v.nome + "\". Cosa devi fare entro venerdì?");
      pulsanti(risposte, COSE[v.nome], cosa);
    }
    async function cosa(v) {
      pulsanti(risposte, [], null);
      riga(righe, "persona", v.testo + ".");
      await attendi(500);
      riga(righe, "", v.chi === "tu"
        ? "Segno \"" + v.testo + "\" fra le cose che toccano a te. Lo ritrovi nella finestra, a destra, e la prossima volta si riparte da lì."
        : "Questo lo faccio io: lo segno sotto \"Ci pensa Claude\". Nella finestra vedi quando ci lavoro, e mi fermo a chiederti prima di cancellare o mandare qualcosa.");
      pulsanti(risposte, [{ testo: "Ricomincia" }], inizio);
    }
    inizio();
  })();

  // ---------- 2. i progetti ----------
  (function () {
    var s = $('[data-scena="progetti"]');
    if (!s) return;
    var NUMERI = ["Nessun progetto nuovo", "Un progetto nuovo", "Due progetti nuovi", "Tre progetti nuovi", "Quattro progetti nuovi"];
    var conto = $(".cartelle__conta", s);
    function conta() {
      var n = $$('.cartella button[aria-pressed="true"]', s).length;
      conto.textContent = NUMERI[n] + (n ? " nella barra a sinistra." : ": la barra resta vuota finché non ne scegli uno.");
    }
    $$(".cartella button", s).forEach(function (b) {
      b.addEventListener("click", function () {
        var si = b.getAttribute("aria-pressed") !== "true";
        b.setAttribute("aria-pressed", si ? "true" : "false");
        b.textContent = si ? "Sì" : "No";
        conta();
      });
    });
  })();

  // ---------- 3. le cose da fare ----------
  (function () {
    var s = $('[data-scena="todo"]');
    if (!s) return;
    $$("[data-vista]", s).forEach(function (b) {
      b.addEventListener("click", function () {
        var v = b.getAttribute("data-vista");
        $$("[data-vista]", s).forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
        $$("[data-vista-di]", s).forEach(function (x) { x.hidden = x.getAttribute("data-vista-di") !== v; });
      });
    });
  })();

  // ---------- 4. la finestra ----------
  (function () {
    var s = $('[data-scena="finestra"]');
    if (!s) return;
    var P = {
      ricette: { titolo: "Ricette della nonna", piede: ["lavora", "Claude sta lavorando"],
        term: [["tu", "riduci le foto del primo capitolo"], ["fa", "Legge 42 foto in Ricette nonna/capitolo-1"], ["fa", "Riduce a 1600 pixel, copia in capitolo-1/web"], ["", "Fatto per 18 foto su 42. Continuo con le altre."]],
        todo: [["Tocca a te", "tu", [["Scegliere le foto del primo capitolo", ""]]], ["Ci pensa Claude", "", [["Ridurre le foto a 1600 pixel", "Claude ci sta lavorando", "lavora"]]]] },
      negozio: { titolo: "Negozio bici", piede: ["", "Conversazione chiusa"],
        term: [["", "Ieri ho preparato due versioni del sito, una verde e una blu, in Negozio bici/sito/prove."], ["", "Quando hai scelto, metto i prezzi nuovi in quella giusta."]],
        todo: [["Decidi tu, poi fa Claude", "", [["Scegliere fra i due colori del sito", "le due prove sono pronte"]]], ["Ci pensa Claude", "", [["Mettere i prezzi nuovi nel sito", "aspetta la tua scelta"]]]] },
      tesi: { titolo: "Tesi magistrale", piede: ["", "Conversazione chiusa"],
        term: [["", "Ho riletto il capitolo 3: ho segnato in rosso dodici frasi da sistemare e due citazioni senza fonte."]],
        todo: [["Tocca a te", "tu", [["Sistemare le dodici frasi segnate", "scadenza venerdì"]]], ["Ci pensa Claude", "", [["Trovare la fonte delle due citazioni", ""]]]] }
    };
    var term = $('[data-campo="term"]', s), piede = $('[data-campo="piede"]', s), elenco = $('[data-campo="dafare"]', s);
    $$(".hw__progetto", s).forEach(function (b) {
      b.addEventListener("click", function () {
        var p = P[b.getAttribute("data-progetto")];
        $$(".hw__progetto", s).forEach(function (x) { x.setAttribute("aria-current", x === b ? "true" : "false"); });
        $('[data-campo="titolo"]', s).textContent = p.titolo;
        $('[data-campo="nome"]', s).textContent = p.titolo;
        term.innerHTML = "";
        p.term.forEach(function (r) { riga(term, r[0], r[1]); });
        stato(piede, p.piede[0], p.piede[1]);
        elenco.innerHTML = "";
        p.todo.forEach(function (g) {
          var h = d.createElement("p");
          h.className = "hw__gruppo" + (g[1] === "tu" ? " hw__gruppo--tu" : "");
          h.textContent = g[0];
          elenco.appendChild(h);
          g[2].forEach(function (t) {
            var r = d.createElement("div");
            r.className = "todo entra";
            r.innerHTML = '<span class="todo__casella" aria-hidden="true"></span><span class="todo__titolo"></span>' + (t[1] ? '<span class="todo__stato"></span>' : "");
            r.querySelector(".todo__titolo").textContent = t[0];
            if (t[1]) { r.querySelector(".todo__stato").textContent = t[1]; if (t[2]) r.querySelector(".todo__stato").classList.add(t[2]); }
            elenco.appendChild(r);
          });
        });
      });
    });
  })();

  // ---------- 5. spunta, oppure cambia chi lo fa ----------
  (function () {
    var s = $('[data-scena="dafare"]');
    if (!s) return;
    var avviso = $(".avviso", s), tempo = 0;
    var NOMI = { tu: "Tu", io: "Claude", decidi: "Decidi tu, poi Claude" };
    function di(testo) {
      avviso.textContent = testo;
      avviso.hidden = false;
      clearTimeout(tempo);
      tempo = setTimeout(function () { avviso.hidden = true; }, 2600);
    }
    function chiudiMenu(t) {
      var m = $(".menu-todo", t), b = $("[data-altro]", t);
      if (m) m.hidden = true;
      if (b) b.setAttribute("aria-expanded", "false");
    }
    function menu(t) {
      var chi = t.getAttribute("data-chi");
      $$("[data-chi-nuovo]", t).forEach(function (b) { b.remove(); });
      var dopo = $(".menu-todo span", t);
      Object.keys(NOMI).filter(function (k) { return k !== chi; }).reverse().forEach(function (k) {
        var b = d.createElement("button");
        b.type = "button";
        b.setAttribute("data-chi-nuovo", k);
        b.textContent = NOMI[k];
        dopo.after(b);
      });
    }
    s.addEventListener("click", function (e) {
      var t = e.target.closest(".todo");
      if (!t) return;
      var titolo = $(".todo__titolo", t).textContent;
      if (e.target.closest(".todo__casella")) {
        var fatto = t.classList.toggle("todo--fatto");
        e.target.closest(".todo__casella").setAttribute("aria-label", (fatto ? "Rimetti da fare: " : "Segna fatto: ") + titolo);
        di(fatto ? "Fatto: " + titolo : "Di nuovo da fare: " + titolo);
        return;
      }
      if (e.target.closest("[data-altro]")) {
        var m = $(".menu-todo", t), aperto = m.hidden;
        $$(".todo", s).forEach(chiudiMenu);
        if (aperto) { menu(t); m.hidden = false; e.target.closest("[data-altro]").setAttribute("aria-expanded", "true"); m.querySelector("button").focus(); }
        return;
      }
      var nuovo = e.target.closest("[data-chi-nuovo]");
      if (nuovo) {
        var chi = nuovo.getAttribute("data-chi-nuovo");
        var testa = $('[data-gruppo="' + chi + '"]', s), dove = testa;
        while (dove.nextElementSibling && dove.nextElementSibling.classList.contains("todo")) dove = dove.nextElementSibling;
        t.setAttribute("data-chi", chi);
        chiudiMenu(t);
        dove.after(t);
        di("Ora lo fa: " + NOMI[chi]);
        $("[data-altro]", t).focus();
        return;
      }
      var quando = e.target.closest("[data-quando]");
      if (quando) {
        var st = $(".todo__stato", t);
        if (!st) { st = d.createElement("span"); st.className = "todo__stato"; $(".todo__titolo", t).after(st); }
        st.textContent = quando.getAttribute("data-quando");
        chiudiMenu(t);
        di("Spostato a: " + quando.getAttribute("data-quando"));
        $("[data-altro]", t).focus();
      }
    });
    s.addEventListener("keydown", function (e) {
      if (e.key !== "Escape") return;
      var t = e.target.closest(".todo");
      if (t) { chiudiMenu(t); $("[data-altro]", t).focus(); }
    });
  })();

  // ---------- 6. Lavoraci ----------
  (function () {
    var s = $('[data-scena="lavoraci"]');
    if (!s) return;
    var term = $('[data-campo="term"]', s), piede = $('[data-campo="piede"]', s), riga_ = $('[data-campo="riga"]', s);
    var st = $('[data-campo="stato"]', s), lavoraci = $("[data-lavoraci]", s), risposte = $(".risposte", s);
    function inizio() {
      s.classList.remove("hw--aspetta");
      term.innerHTML = "";
      riga(term, "fa", "Conversazione aperta, in attesa");
      stato(piede, "", "Conversazione aperta");
      stato(riga_, "", "Conversazione aperta, Claude aspetta");
      st.textContent = "";
      st.className = "todo__stato";
      lavoraci.hidden = false;
      pulsanti(risposte, [], null);
    }
    lavoraci.addEventListener("click", async function () {
      lavoraci.hidden = true;
      term.innerHTML = "";
      stato(st, "lavora", "Claude ci sta lavorando");
      stato(riga_, "lavora", "Claude sta lavorando");
      stato(piede, "lavora", "Claude sta lavorando");
      riga(term, "tu", "Lavoriamo sul todo: Ridurre le foto a 1600 pixel");
      await attendi(700);
      riga(term, "fa", "Legge 42 foto in Ricette nonna/capitolo-1");
      await attendi(700);
      riga(term, "fa", "Riduce a 1600 pixel, copia in capitolo-1/web");
      await attendi(900);
      riga(term, "chiede", "", "<b>Claude ti chiede</b>Tre foto sono storte. Le raddrizzo io o le lasci come sono?");
      s.classList.add("hw--aspetta");
      stato(st, "aspetta", "Claude ti aspetta");
      stato(riga_, "aspetta", "Claude ti aspetta");
      stato(piede, "aspetta", "Claude ti aspetta");
      pulsanti(risposte, [{ testo: "Raddrizzale tu" }, { testo: "Lasciale così" }], async function (v) {
        pulsanti(risposte, [], null);
        s.classList.remove("hw--aspetta");
        riga(term, "tu", v.testo.toLowerCase());
        stato(st, "lavora", "Claude ci sta lavorando");
        stato(riga_, "lavora", "Claude sta lavorando");
        stato(piede, "lavora", "Claude sta lavorando");
        await attendi(700);
        if (v.testo === "Raddrizzale tu") riga(term, "fa", "Raddrizza 3 foto");
        riga(term, "", "Fatto: le 42 foto sono in capitolo-1/web. La cosa da fare resta in corso finché non scrivi /fine.");
        stato(st, "", "In corso finché non scrivi /fine");
        stato(riga_, "", "Claude ha finito");
        stato(piede, "", "Claude ha finito");
        pulsanti(risposte, [{ testo: "Ricomincia" }], inizio);
      });
    });
    inizio();
  })();

  // ---------- 7. chiudi pure la finestra ----------
  (function () {
    var s = $('[data-scena="chiudi"]');
    if (!s) return;
    var hw = $(".hw", s), chiusa = $(".chiusa", s), dock = $('[data-campo="dock"]', s);
    var term = $('[data-campo="term"]', s), piede = $('[data-campo="piede"]', s), riga_ = $('[data-campo="riga"]', s);
    var risposte = $(".risposte", s), chiudi = $("[data-chiudi]", s), giro = 0;
    function inizio() {
      giro++;
      chiusa.hidden = true;
      hw.hidden = false;
      term.innerHTML = "";
      riga(term, "fa", "Riduce a 1600 pixel, copia in capitolo-1/web");
      riga(term, "", "Fatto per 18 foto su 42. Continuo con le altre.");
      stato(piede, "lavora", "Claude sta lavorando");
      stato(riga_, "lavora", "Claude sta lavorando");
      chiudi.hidden = false;
      pulsanti(risposte, [], null);
    }
    chiudi.addEventListener("click", async function () {
      var questo = giro;
      hw.hidden = true;
      chiusa.hidden = false;
      dock.textContent = "La finestra è chiusa. Claude sta ancora riducendo le foto.";
      $("[data-riapri]", s).focus();
      await attendi(2200);
      if (questo === giro && !chiusa.hidden) dock.textContent = "Claude ha finito mentre la finestra era chiusa. Riaprila: ritrovi la conversazione con quello che ha fatto.";
    });
    $("[data-riapri]", s).addEventListener("click", function () {
      chiusa.hidden = true;
      hw.hidden = false;
      chiudi.hidden = true;
      riga(term, "", "Ho ridotto tutte le 42 foto. Sono in capitolo-1/web.");
      stato(piede, "", "Claude ha finito");
      stato(riga_, "", "Claude ha finito");
      pulsanti(risposte, [{ testo: "Scrivi /fine" }], async function () {
        pulsanti(risposte, [], null);
        riga(term, "tu", "/fine");
        await attendi(700);
        riga(term, "fa", "Salva il punto: domani si parte dalla scelta delle foto");
        await attendi(500);
        riga(term, "chiuso", "Chiuso: Ridurre le foto a 1600 pixel");
        stato(piede, "", "Conversazione aperta");
        stato(riga_, "", "1 cosa tocca a te");
        pulsanti(risposte, [{ testo: "Ricomincia" }], inizio);
      });
    });
    inizio();
  })();
})();
