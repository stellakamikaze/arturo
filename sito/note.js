// Note di Agentation sulla landing, nello stesso archivio della pagina admin (/admin/ag).
// La barretta appare solo a chi passa da Cloudflare Access: per gli altri /admin/ag non risponde
// e la pagina resta com'è. Una sessione per pagina, così chi annota vede le stesse note.
(async () => {
  try {
    const radice = new URL("/admin/ag", location.origin).href;
    const prova = await fetch(radice + "/health", { credentials: "same-origin", redirect: "manual" });
    if (!prova.ok || !(prova.headers.get("content-type") || "").includes("json")) { return; }
    // React e Agentation stanno sul sito (vendor/note-vendor-1.js), non più su esm.sh: chi passa da
    // Access ha i poteri dell'admin, e su questa origine gira solo codice nostro (16/10/2026).
    // La pagina admin ne tiene una copia identica (static/note-vendor-1.js): si aggiornano insieme.
    const { R, RD, AG } = await import(new URL("vendor/note-vendor-1.js", import.meta.url).href);
    if (document.getElementById("note-radice")) { return; }
    const nodo = document.createElement("div");
    nodo.id = "note-radice";
    document.body.appendChild(nodo);
    const pagina = location.pathname.replace(/^\/+|\/+$/g, "").replace(/\//g, "--") || "home";
    RD.createRoot(nodo).render(R.createElement(AG.Agentation, {
      endpoint: radice,
      sessionId: "p-landing-" + pagina,
    }));
  } catch (e) {
    console.warn("[arturo] barretta delle note non caricata:", e);
  }
})();
