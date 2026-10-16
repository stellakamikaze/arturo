// Cosa conta il sito, in un posto solo (16/10/2026). Plausible, ospitato da chi mantiene Arturo e
// servito da questo dominio (/js/a.js, /api/e), conta gli eventi senza cookie. I download vanno
// anche al server di Arturo (/api/sito), che ne avvisa Federico su Telegram con un tetto al giorno.
// Esce solo: il nome dell'evento, la pagina, il computer scelto nella guida (Mac o Windows), il
// numero del passo o del comando. Mai quello che la persona scrive nei campi.
(function () {
  var d = document;
  window.plausible = window.plausible || function () { (window.plausible.q = window.plausible.q || []).push(arguments); };

  function pagina() { return location.pathname.toLowerCase().replace(/[^a-z0-9/-]/g, "").slice(0, 41) || "/"; }
  function sistema() { var os = d.documentElement.getAttribute("data-os"); return os === "mac" || os === "win" ? os : ""; }
  function evento(nome, props) { try { window.plausible(nome, { props: props || {} }); } catch (e) { /* il conteggio non ferma la pagina */ } }

  // Un download avvisa una volta per pagina e per tipo: chi copia tre volte lo stesso comando è una persona.
  var giaDetto = {};
  function segnala(tipo) {
    var chiave = tipo + pagina();
    if (giaDetto[chiave]) return;
    giaDetto[chiave] = true;
    var corpo = JSON.stringify({ tipo: tipo, pagina: pagina(), sistema: sistema() });
    try {
      if (navigator.sendBeacon && navigator.sendBeacon("/api/sito", new Blob([corpo], { type: "application/json" }))) return;
    } catch (e) { /* si prova con fetch */ }
    try { fetch("/api/sito", { method: "POST", body: corpo, headers: { "Content-Type": "application/json" }, keepalive: true }); } catch (e) { /* niente */ }
  }

  d.addEventListener("click", function (e) {
    var el = e.target.closest ? e.target.closest("[data-copia], [data-fatta], a[href]") : null;
    if (!el) return;

    // I comandi da copiare. Il comando che scarica Arturo (git clone) è il download.
    if (el.hasAttribute("data-copia")) {
      var id = el.getAttribute("data-copia");
      var pre = d.getElementById(id);
      var download = !!(pre && /git clone https:\/\/github\.com\/stellakamikaze\/arturo/.test(pre.textContent));
      evento("Copia comando", { comando: id, pagina: pagina(), sistema: sistema() || "?" });
      if (download) { evento("Download", { come: "comando", pagina: pagina(), sistema: sistema() || "?" }); segnala("download"); }
      return;
    }

    // I passi della guida segnati come fatti.
    if (el.hasAttribute("data-fatta")) {
      evento("Guida: passo fatto", { passo: el.getAttribute("data-fatta"), pagina: pagina(), sistema: sistema() || "?" });
      return;
    }

    // I link: il repository su GitHub è un download, gli altri siti un link esterno.
    var url;
    try { url = new URL(el.getAttribute("href"), location.href); } catch (err) { return; }
    if (url.origin === location.origin) return;
    if (/^\/stellakamikaze\/arturo\/?$/.test(url.pathname) && url.hostname === "github.com") {
      evento("Download", { come: "github", pagina: pagina(), sistema: sistema() || "?" });
      segnala("github");
    } else {
      evento("Link esterno", { sito: url.hostname, pagina: pagina() });
    }
  }, true);

  // L'iscrizione alla newsletter: il modulo di Ghost in home.
  d.addEventListener("submit", function (e) {
    var f = e.target;
    if (f && f.closest && f.closest("[data-newsletter], .gh-signup-root, [data-members-form]")) evento("Newsletter", { pagina: pagina() });
  }, true);
})();
