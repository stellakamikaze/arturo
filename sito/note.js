// Note di Agentation sulla landing, nello stesso archivio della pagina admin (/admin/ag).
// La barretta appare solo a chi passa da Cloudflare Access: per gli altri /admin/ag non risponde
// e la pagina resta com'è. Una sessione per pagina, così chi annota vede le stesse note.
(async () => {
  try {
    const radice = new URL("/admin/ag", location.origin).href;
    const prova = await fetch(radice + "/health", { credentials: "same-origin", redirect: "manual" });
    if (!prova.ok || !(prova.headers.get("content-type") || "").includes("json")) { return; }
    const [R, RD, AG] = await Promise.all([
      import("https://esm.sh/react@18.3.1"),
      import("https://esm.sh/react-dom@18.3.1/client"),
      import("https://esm.sh/agentation@3.0.2?deps=react@18.3.1,react-dom@18.3.1"),
    ]);
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
