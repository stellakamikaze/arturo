#!/usr/bin/env node
/* La pagina dei todo in Chrome headless, pilotata con il protocollo DevTools (W13 di test_web.py).

   Uso: node tests/prova_pagina.js REPO PYTHON CHROME
   Exit: 0 tutto bene, 1 un controllo fallisce (la riga «FAIL …» dice quale), 77 la prova non può
   partire (node senza WebSocket, Chrome che non apre la porta di debug).

   Controlla due comportamenti che solo un browser vede:
   - un pannello «Modifica» aperto tiene i campi non salvati quando arriva l'esito di una nota o
     di «Fatto» su un'altra riga, e la nota salvata esce dal suo campo;
   - «Fatto» sulla riga del pannello aperto («Modifica» o «Ho deciso») chiude il pannello, e un
     todo scritto dalla CLI compare alla lettura successiva.
   Nessuna dipendenza: node 18 o successivo, script classico, nessuna rete esterna. */
"use strict";

const { spawn, execFileSync } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");

const [REPO, PYTHON, CHROME] = process.argv.slice(2);
const SALTA = 77;
const FIGLI = [];  // server e Chrome: si chiudono sempre, anche quando la prova supera il tempo

function attendi(ms) { return new Promise((r) => setTimeout(r, ms)); }

async function main() {
  if (!REPO || !PYTHON || !CHROME) { console.log("FAIL uso: node prova_pagina.js REPO PYTHON CHROME"); return 1; }
  if (typeof WebSocket === "undefined") { console.log("SALTA node senza WebSocket"); return SALTA; }
  const base = fs.mkdtempSync(path.join(os.tmpdir(), "arturo-pagina-"));
  const home = path.join(base, "home");
  fs.mkdirSync(home);
  const env = Object.assign({}, process.env, { HOME: home, USERPROFILE: home, ARTURO_OGGI: "2026-10-03",
    PYTHONIOENCODING: "utf-8", PYTHONUNBUFFERED: "1" });
  delete env.ARTURO_TODO;
  delete env.ARTURO_WEB_INATTIVO;
  const cli = (...a) => execFileSync(PYTHON, [path.join(REPO, "bin", "arturo"), "todo", ...a], { env, cwd: home }).toString();
  let srv = null;
  let chrome = null;
  let ws = null;
  try {
    cli("aggiungi", "Uno", "--progetto", "p");
    cli("aggiungi", "Due", "--progetto", "p");
    cli("aggiungi", "Scegliere la sala", "--progetto", "p", "--chi", "decidi");
    cli("aggiungi", "Quattro", "--progetto", "p");

    srv = spawn(PYTHON, [path.join(REPO, "bin", "arturo"), "web", "--non-aprire", "--porta", "0"], { env, cwd: home });
    FIGLI.push(srv);
    const url = await new Promise((risolvi, rifiuta) => {
      let letto = "";
      const limite = setTimeout(() => rifiuta(new Error("arturo web non stampa il link entro 15 s")), 15000);
      srv.stdout.on("data", (d) => {
        letto += d.toString();
        const m = /http:\/\/127\.0\.0\.1:\d+\/\?t=[A-Za-z0-9_-]+/.exec(letto);
        if (m) { clearTimeout(limite); risolvi(m[0]); }
      });
    });

    const profilo = path.join(base, "chrome");
    chrome = spawn(CHROME, ["--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
      // Con una HOME di prova Chrome su macOS chiede il portachiavi e si blocca: il finto portachiavi lo evita.
      "--use-mock-keychain", "--password-store=basic", "--remote-debugging-port=0", "--user-data-dir=" + profilo, "about:blank"], { stdio: "ignore" });
    FIGLI.push(chrome);
    let porta = 0;
    for (let i = 0; i < 100 && !porta; i += 1) {
      try { porta = Number(fs.readFileSync(path.join(profilo, "DevToolsActivePort"), "utf8").split("\n")[0]); } catch (e) { /* non ancora */ }
      if (!porta) { await attendi(100); }
    }
    if (!porta) { console.log("SALTA Chrome non apre la porta di debug"); return SALTA; }
    let pagina = null;
    for (let i = 0; i < 50 && !pagina; i += 1) {
      try { pagina = (await (await fetch(`http://127.0.0.1:${porta}/json`)).json()).find((x) => x.type === "page"); } catch (e) { /* non ancora */ }
      if (!pagina) { await attendi(100); }
    }
    if (!pagina) { console.log("SALTA Chrome non mostra la scheda"); return SALTA; }
    ws = new WebSocket(pagina.webSocketDebuggerUrl);
    await new Promise((risolvi, rifiuta) => {
      const limite = setTimeout(() => rifiuta(new Error("il WebSocket di Chrome non si apre entro 10 s")), 10000);
      ws.addEventListener("open", () => { clearTimeout(limite); risolvi(); });
    });
    let n = 0;
    const attese = new Map();
    ws.addEventListener("message", (e) => {
      const m = JSON.parse(e.data);
      if (m.id && attese.has(m.id)) { attese.get(m.id)(m); attese.delete(m.id); }
    });
    // Ogni comando ha 20 secondi: un Chrome bloccato dà un FAIL con il nome del comando, non un'attesa senza fine.
    const cdp = (method, params) => new Promise((risolvi, rifiuta) => {
      n += 1;
      const id = n;
      const limite = setTimeout(() => { attese.delete(id); rifiuta(new Error("Chrome non risponde a " + method + " entro 20 s")); }, 20000);
      attese.set(id, (m) => { clearTimeout(limite); risolvi(m); });
      ws.send(JSON.stringify({ id, method, params: params || {} }));
    });
    const valuta = async (espressione) => {
      const r = await cdp("Runtime.evaluate", { expression: espressione, awaitPromise: true, returnByValue: true });
      if (r.result && r.result.exceptionDetails) { throw new Error("errore nella pagina: " + JSON.stringify(r.result.exceptionDetails).slice(0, 300)); }
      return r.result && r.result.result ? r.result.result.value : undefined;
    };
    // Aspetta che un'espressione sia vera, fino a `ms`. Torna l'ultimo valore.
    const finche = async (espressione, ms) => {
      const fine = Date.now() + (ms || 5000);
      let v = await valuta(espressione);
      while (!v && Date.now() < fine) { await attendi(100); v = await valuta(espressione); }
      return v;
    };
    const premi = (id, testo) => valuta(`(function () { var b = [...document.querySelectorAll('.pannello:not([hidden]) .todo[data-id="${id}"] .todo-riga button')].find(function (x) { return x.textContent === ${JSON.stringify(testo)}; }); if (b) { b.click(); } return !!b; })()`);
    const titoli = () => valuta(`[...document.querySelectorAll('.pannello:not([hidden]) .todo-titolo')].map(function (x) { return x.textContent; }).join(" | ")`);
    const esito = () => valuta(`document.getElementById("esito").textContent`);
    const leggiOra = () => valuta(`document.activeElement && document.activeElement.blur(); document.dispatchEvent(new Event("visibilitychange")); true`);
    const errori = [];
    const controlla = (vero, testo) => { if (!vero) { errori.push(testo); } };

    await cdp("Page.enable");
    await cdp("Page.navigate", { url });
    controlla(await finche(`!!document.querySelector('.todo[data-id="4"]')`, 10000), "la pagina non mostra i todo");

    // 1. Il pannello tiene i campi non salvati.
    controlla(await premi(1, "Modifica"), "manca «Modifica» su #1");
    controlla(await finche(`!!document.getElementById("m-1-titolo")`), "il pannello di #1 non si apre");
    await valuta(`document.getElementById("m-1-titolo").value = "Uno cambiato"; document.getElementById("m-1-nota").value = "una nota"; document.getElementById("m-1-nota").form.requestSubmit(); true`);
    controlla(await finche(`[...document.querySelectorAll('.todo[data-id="1"] .note li')].some(function (x) { return x.textContent === "una nota"; })`),
      "la nota non compare nel pannello");
    const dopoNota = await valuta(`JSON.stringify([(document.getElementById("m-1-titolo") || {}).value, (document.getElementById("m-1-nota") || {}).value])`);
    controlla(dopoNota === JSON.stringify(["Uno cambiato", ""]), `dopo la nota il pannello ha [titolo, nota] = ${dopoNota}, non ["Uno cambiato", ""]`);
    controlla(await premi(2, "Fatto"), "manca «Fatto» su #2");
    controlla(await finche(`document.getElementById("esito").textContent.indexOf("Chiuso #2") === 0`), `«Fatto» su #2 dà l'esito ${JSON.stringify(await esito())}`);
    const dopoFatto = await valuta(`(document.getElementById("m-1-titolo") || {}).value`);
    controlla(dopoFatto === "Uno cambiato", `dopo «Fatto» su un'altra riga il titolo nel pannello è ${JSON.stringify(dopoFatto)}`);

    // 2. «Fatto» sulla riga del pannello aperto: la lettura successiva arriva nella pagina.
    controlla(await premi(1, "Fatto"), "manca «Fatto» su #1");
    controlla(await finche(`document.getElementById("esito").textContent.indexOf("Chiuso #1") === 0`), `«Fatto» su #1 dà l'esito ${JSON.stringify(await esito())}`);
    cli("aggiungi", "Scritto da Claude", "--progetto", "p");
    await leggiOra();
    controlla(await finche(`document.body.textContent.indexOf("Scritto da Claude") !== -1`),
      `con il pannello «Modifica» chiuso da «Fatto», un todo della CLI non compare: ${await titoli()}`);

    controlla(await premi(3, "Ho deciso"), "manca «Ho deciso» su #3");
    controlla(await finche(`!!document.getElementById("deciso-3")`), "il pannello «Ho deciso» non si apre");
    controlla(await premi(3, "Fatto"), "manca «Fatto» su #3");
    controlla(await finche(`document.getElementById("esito").textContent.indexOf("Chiuso #3") === 0`), `«Fatto» su #3 dà l'esito ${JSON.stringify(await esito())}`);
    cli("aggiungi", "Ancora Claude", "--progetto", "p");
    await leggiOra();
    controlla(await finche(`document.body.textContent.indexOf("Ancora Claude") !== -1`),
      `con il pannello «Ho deciso» chiuso da «Fatto», un todo della CLI non compare: ${await titoli()}`);

    if (errori.length) { errori.forEach((e) => console.log("FAIL " + e)); return 1; }
    console.log("PROVA_PAGINA_OK controlli=2");
    return 0;
  } finally {
    if (ws) { try { ws.close(); } catch (e) { /* già chiuso */ } }
    if (chrome) { chrome.kill(); }
    if (srv) { srv.kill(); }
    await attendi(300);
    try { fs.rmSync(base, { recursive: true, force: true }); } catch (e) { /* Chrome tiene ancora un file */ }
  }
}

// Oltre 120 secondi la prova si ferma da sola e chiude Chrome e il server.
const fermo = setTimeout(() => {
  console.log("FAIL la prova supera 120 s");
  FIGLI.forEach((f) => { try { f.kill(); } catch (e) { /* già chiuso */ } });
  process.exit(1);
}, 120000);
main().then((rc) => { clearTimeout(fermo); process.exit(rc); },
  (e) => { clearTimeout(fermo); console.log("FAIL " + (e && e.message ? e.message : e)); process.exit(1); });
