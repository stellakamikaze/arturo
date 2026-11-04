// Figure 2 e 3 (skill diagram-design): il percorso di un comando nelle guardie, il ritmo ad anello.
// Scrive guardie.svg.html e ritmo.svg.html, gli snippet da incollare.
import { writeFileSync } from "node:fs";
const DIR = new URL(".", import.meta.url).pathname;
const r = (v) => Math.round(v * 10) / 10;
const esc = (t) => t.replace(/&/g, "&amp;").replace(/</g, "&lt;");

// testo su più righe: [x, y, righe, classe, passo]
const righe = (x, y, lista, cls, passo = 16, anchor) =>
  `<text class="${cls}" x="${x}" y="${y}"${anchor ? ` text-anchor="${anchor}"` : ""}>${lista.map((t, i) => (i ? `<tspan x="${x}" dy="${passo}">${t}</tspan>` : t)).join("")}</text>`;
const box = (x, y, w, h, cls) => `<rect class="fd-box ${cls}" x="${x}" y="${y}" width="${w}" height="${h}" rx="2"/>`;
const freccia = (id) => `<marker id="${id}" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto"><path class="fd-punta" d="M0 0 8 3 0 6z"/></marker>`;

// ---------- Figura 2: il percorso di un comando ----------
function guardie() {
  const W = 400, H = 672, F = "fd-g-f";
  const esiti = [
    { y: 216, nome: "Passa", cls: "passa", righe: ["Nessuna guardia ha da ridire: decidono", "i permessi normali. Succede quasi sempre."] },
    { y: 316, nome: "Chiede a te", cls: "chiede", righe: ["Un gesto che non si annulla, come", "cancellare una cartella: parte col tuo sì."] },
    { y: 416, nome: "Ferma", cls: "blocca", righe: ["Un danno certo, come cancellare il disco", "intero: il comando non parte."] },
  ];
  const segni = {
    passa: (x, y) => `<path class="fd-segno fd-segno--passa" d="M${x - 6} ${y}l4 4 8-9"/>`,
    chiede: (x, y) => `<path class="fd-segno fd-segno--chiede" d="M${x - 4} ${y - 4}a4 4 0 1 1 5 4c-1 .5-1 1.5-1 2.5"/><circle class="fd-chiede" cx="${x}" cy="${y + 6}" r="1.3"/>`,
    blocca: (x, y) => `<path class="fd-segno fd-segno--blocca" d="M${x - 5} ${y - 5}l10 10m0-10-10 10"/>`,
  };
  const linee = [
    // A -> B
    `<path class="fd-linea" d="M200 80V111" marker-end="url(#${F})"/>`,
    // dorsale a sinistra: Passa e Chiede con un ramo, Ferma con il gomito
    `<path class="fd-linea" d="M32 184V448q0 8 8 8H55" marker-end="url(#${F})"/>`,
    `<path class="fd-linea" d="M32 256H55" marker-end="url(#${F})"/>`,
    `<path class="fd-linea" d="M32 356H55" marker-end="url(#${F})"/>`,
    // i due casi limite, tratteggiati, risalgono a destra
    `<path class="fd-linea fd-linea--quieta" d="M352 556H356q8 0 8-8V364q0-8-8-8H353" marker-end="url(#${F})"/>`,
    `<path class="fd-linea fd-linea--quieta" d="M352 628H372q8 0 8-8V264q0-8-8-8H353" marker-end="url(#${F})"/>`,
  ].join("");
  const nodi = [
    box(16, 16, 368, 64, ""),
    `<text class="fd-nome" x="32" y="42">Claude propone un comando</text>`,
    `<text class="fd-riga" x="32" y="64">Per esempio <tspan class="fd-mono">rm -r bozze/</tspan></text>`,
    box(16, 112, 368, 72, "fd-box--guardia"),
    `<text class="fd-nome fd-nome--chiaro" x="32" y="138">La guardia lo legge</text>`,
    righe(32, 158, ["Un solo smistatore chiama le guardie che", "servono, prima che il comando parta."], "fd-riga fd-riga--chiara"),
    `<circle class="fd-punto" cx="32" cy="256" r="3"/><circle class="fd-punto" cx="32" cy="356" r="3"/>`,
    ...esiti.map((e) => box(56, e.y, 296, 80, `fd-box--${e.cls}`) + segni[e.cls](332, e.y + 22) + `<text class="fd-nome" x="72" y="${e.y + 28}">${e.nome}</text>` + righe(72, e.y + 50, e.righe, "fd-riga")),
    `<text class="fd-etichetta" x="56" y="516">Se qualcosa non torna</text>`,
    box(56, 528, 296, 56, "fd-box--quieta"),
    `<text class="fd-nome" x="72" y="552">La guardia si rompe</text>`,
    `<text class="fd-riga" x="72" y="572">Senza una risposta valida, chiede a te.</text>`,
    box(56, 600, 296, 56, "fd-box--quieta"),
    `<text class="fd-nome" x="72" y="624">Comando vuoto o illeggibile</text>`,
    `<text class="fd-riga" x="72" y="644">La guardia tace, decidono i permessi.</text>`,
  ].join("");
  const svg = `<svg class="fd-svg fd-svg--guardie" viewBox="0 0 ${W} ${H}" role="img" aria-labelledby="fd-guardie-t fd-guardie-d">`
    + `<title id="fd-guardie-t">Il percorso di un comando nelle guardie</title>`
    + `<desc id="fd-guardie-d">Claude propone un comando e la guardia lo legge prima che parta. Tre esiti: passa, e decidono i permessi normali; chiede a te, per un gesto che non si annulla; ferma, per un danno certo come cancellare il disco intero. Se la guardia si rompe chiede a te; se il comando è vuoto o illeggibile la guardia tace e decidono i permessi.</desc>`
    + `<defs>${freccia(F)}</defs>${linee}${nodi}</svg>`;
  return `<figure class="figura figura--diagramma figura--guardie">
<div class="figura__piastra">
<p class="figura__testa" aria-hidden="true"><span>Fig. 2</span><span>Il percorso di un comando</span></p>
${svg}
</div>
<figcaption><p>Le guardie leggono ogni comando prima che parta. Quando chiede, ferma o si rompe, una guardia lascia il suo nome nella telemetria, mai il comando.</p></figcaption>
</figure>`;
}

// ---------- Figura 3: il ritmo ad anello ----------
function ritmo() {
  const W = 448, H = 440, C = [224, 220], R = 154, F = "fd-r-f";
  const bw = 136, bh = 68;
  const stazioni = [
    { nome: "/inizio", mono: true, righe: ["rilegge l'appunto,", "propone il lavoro"] },
    { nome: "Il lavoro", righe: ["Claude sui tuoi file,", "le guardie chiedono"] },
    { nome: "/fine", mono: true, righe: ["controlla, salva,", "scrive l'appunto"] },
    { nome: "Chiusura", righe: ["Arturo cerca", "rilasci firmati"] },
  ];
  const N = stazioni.length;
  const centri = stazioni.map((_, k) => {
    const t = (-90 + (k * 360) / N) * Math.PI / 180;
    return [C[0] + R * Math.cos(t), C[1] + R * Math.sin(t)];
  });
  const rett = centri.map(([x, y]) => ({ x: x - bw / 2, y: y - bh / 2, w: bw, h: bh }));
  const ang = ([x, y]) => Math.atan2(y - C[1], x - C[0]);
  // intersezioni cerchio/rettangolo
  function tagli(b) {
    const pts = [];
    for (const xe of [b.x, b.x + b.w]) {
      const d = R * R - (xe - C[0]) ** 2;
      if (d >= 0) for (const s of [1, -1]) { const y = C[1] + s * Math.sqrt(d); if (y >= b.y && y <= b.y + b.h) pts.push([xe, y]); }
    }
    for (const ye of [b.y, b.y + b.h]) {
      const d = R * R - (ye - C[1]) ** 2;
      if (d >= 0) for (const s of [1, -1]) { const x = C[0] + s * Math.sqrt(d); if (x >= b.x && x <= b.x + b.w) pts.push([x, ye]); }
    }
    return pts;
  }
  const norm = (a) => ((a % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI);
  const archi = [];
  for (let k = 0; k < N; k++) {
    const j = (k + 1) % N;
    const tk = ang(centri[k]), tj = ang(centri[j]);
    const uscita = tagli(rett[k]).sort((a, b) => norm(ang(a) - tk) - norm(ang(b) - tk))[0];
    const entrata = tagli(rett[j]).sort((a, b) => norm(tj - ang(a)) - norm(tj - ang(b)))[0];
    const fine = ang(entrata) - 1.2 / R;
    const q = [C[0] + R * Math.cos(fine), C[1] + R * Math.sin(fine)];
    archi.push(`<path class="fd-arco" d="M${r(uscita[0])} ${r(uscita[1])}A${R} ${R} 0 0 1 ${r(q[0])} ${r(q[1])}" marker-end="url(#${F})"/>`);
  }
  const hub = { x: 158, y: 170, w: 132, h: 100 };
  const raggi = [
    // l'appunto -> /inizio (rilegge), /fine -> l'appunto (scrive)
    `<path class="fd-linea fd-linea--quieta" d="M224 ${hub.y}V${rett[0].y + bh + 7}" marker-end="url(#${F})"/>`,
    `<path class="fd-linea fd-linea--quieta" d="M224 ${rett[2].y}V${hub.y + hub.h + 7}" marker-end="url(#${F})"/>`,
  ];
  const etichette = [
    [232, 142, "rilegge"], [232, 308, "scrive"],
  ].map(([x, y, t]) => `<text class="fd-etichetta" x="${x}" y="${y}">${t}</text>`);
  const nodi = stazioni.map((s, k) => {
    const b = rett[k], cx = r(b.x + bw / 2);
    return box(r(b.x), r(b.y), bw, bh, "") + `<text class="fd-nome${s.mono ? " fd-comando" : ""}" x="${cx}" y="${r(b.y + 24)}" text-anchor="middle">${s.nome}</text>` + righe(cx, r(b.y + 42), s.righe, "fd-riga", 15, "middle");
  });
  nodi.push(box(hub.x, hub.y, hub.w, hub.h, "fd-box--guardia"));
  nodi.push(`<text class="fd-nome fd-nome--chiaro" x="224" y="${hub.y + 28}" text-anchor="middle">L'appunto</text>`);
  nodi.push(righe(224, hub.y + 52, ["un file sul tuo", "computer: restano", "gli ultimi 5"], "fd-riga fd-riga--chiara", 15, "middle"));
  const svg = `<svg class="fd-svg fd-svg--ritmo" viewBox="0 0 ${W} ${H}" role="img" aria-labelledby="fd-ritmo-t fd-ritmo-d">`
    + `<title id="fd-ritmo-t">Il ritmo di lavoro con Arturo</title>`
    + `<desc id="fd-ritmo-d">Un anello in quattro tappe: /inizio rilegge l'appunto e propone il lavoro, Claude lavora sui file, /fine controlla, salva e scrive l'appunto, alla chiusura Arturo cerca aggiornamenti firmati. Al centro l'appunto: /fine lo scrive, il giorno dopo /inizio lo rilegge.</desc>`
    + `<defs>${freccia(F)}</defs>${archi.join("")}${raggi.join("")}${etichette.join("")}${nodi.join("")}</svg>`;
  return `<figure class="figura figura--diagramma figura--ritmo">
<div class="figura__piastra">
<p class="figura__testa" aria-hidden="true"><span>Fig. 3</span><span>Il giro di ogni giorno</span></p>
${svg}
</div>
<figcaption><p>Gli appunti sono file di testo sul tuo computer, divisi per progetto. La sessione dopo riparte da lì: <code>/inizio</code> rilegge quelli del progetto che scegli.</p></figcaption>
</figure>`;
}

const g = guardie(), t = ritmo();
writeFileSync(DIR + "guardie.svg.html", g);
writeFileSync(DIR + "ritmo.svg.html", t);
console.log("guardie", g.length, "ritmo", t.length);
