// Figura 1: Arturo come mobile da carteggio, un cassetto per strato.
// Genera lo snippet SVG (con i cassetti chiusi) e i dati di moto per sito/js/figura-cassettiera.js.
import { writeFileSync } from "node:fs";
import * as k from "/Users/federico/.claude/skills/anatomy/kit/iso-kit.mjs";
import { minify, compatta } from "./minify.mjs";

const OUT = process.argv[2] || "./cassettiera.svg.html";
const W = 640, H = 430;

// Fatti dal README di dev e dal codice (vedi report). Il numero di schede in ogni cassetto è vero.
export const STRATI = [
  { id: "guardie", nome: "Guardie", schede: 23, riga: "23 guardie e automazioni. Prima di un gesto che non si annulla, le guardie chiedono a te." },
  { id: "comandi", nome: "Comandi", schede: 11, riga: "11 comandi con la barra davanti, come /inizio, /fine e /diagnosi." },
  { id: "agenti", nome: "Agenti", schede: 8, riga: "8 subagent con un mestiere solo, come bug-finder, che cerca gli errori nel codice." },
  { id: "skill", nome: "Skill", schede: 7, riga: "7 skill che Claude carica quando servono, come todo per le cose da fare." },
  { id: "memoria", nome: "Memoria e sessioni", schede: 5, riga: "/fine scrive un appunto e /inizio lo rilegge. Restano gli ultimi 5 per progetto." },
  { id: "telemetria", nome: "Telemetria", schede: 16, riga: "16 tipi di evento da un elenco chiuso, mai testi o file. Si spegne con arturo telemetria spegni." },
];

// Mondo: x verso chi guarda (davanti), y verso destra, z in alto.
const X0 = 60;            // piano frontale del corpo
const T = 2.4;            // spessore dei frontali
const Y0 = -110, Y1 = 110;
const ZB = 14;            // sopra lo zoccolo
const DH = 18, GAP = 3;   // altezza cassetto e fessura
const N = STRATI.length;
const ZTOP = ZB + GAP + N * (DH + GAP); // 14+3+126 = 143
const S = 62;             // corsa massima del cassetto
const BODY = 72;          // lunghezza della cassa del cassetto
const az = 33;

const P = k.fitProjection(
  [
    ...k.boxCorners({ x: -66, y: -116, w: 132, d: 232 }, -2, ZTOP + 8),
    [X0 + T + S + 6, Y0, ZB], [X0 + T + S + 6, Y1, ZB], [X0 + T + S + 6, Y1, ZB + DH],
    [-30, 70, ZTOP + 30],
  ],
  W, H, { pad: 22, azimuth: az, elevation: 30 },
);
const at = (p) => k.iso(p, P);
const S_ = (paths, o) => k.solidSvg(paths, o);
const L = (d, o) => k.lineSvg(d, o);
const D = (pts, o) => k.dotsSvg(pts, o);
const poly = (pts, closed = true) => k.pathOf(pts.map(at), closed);
// un rettangolo sul piano x = cost (frontale)
const vrect = (x, y0, y1, z0, z1) => poly([[x, y0, z0], [x, y1, z0], [x, y1, z1], [x, y0, z1]]);

function zoccolo() {
  const out = [];
  const piano = { x: -62, y: -112, w: 124, d: 224, r: 0 };
  out.push(`<path class="iso-halo" d="${k.haloOf(piano, -2, 6, P)}"/>`);
  // quattro piedi a cipolla
  const piedi = k.corners({ x: -58, y: -106, w: 116, d: 212 }, 6).sort((a, b) => k.depthOf([a[0], a[1], 0], P) - k.depthOf([b[0], b[1], 0], P));
  for (const [x, y] of piedi) {
    out.push(S_(k.slabOf({ x: x - 5, y: y - 5, w: 10, d: 10, r: 0 }, -2, 6, P, 1), { tone: "mid", crease: "none" }));
  }
  // zoccolo rientrato con la modanatura
  out.push(S_(k.slabOf({ x: -60, y: -110, w: 120, d: 220, r: 0 }, 4, 6, P, 1, 0.6), { tone: "mid" }));
  out.push(S_(k.slabOf({ x: -62, y: -112, w: 124, d: 224, r: 0 }, 10, 4, P, 1, 0.8), { tone: "mid" }));
  return out.join("");
}

function corpo() {
  const out = [];
  // la cassa: il suo frontale si vede nelle fessure tra i cassetti
  out.push(S_(k.slabOf({ x: -60, y: Y0, w: 120, d: Y1 - Y0, r: 0 }, ZB, ZTOP - ZB, P, 1), { tone: "mid" }));
  // fianchi in rilievo, filo dei frontali
  for (const y of [Y0 - 2, Y1 - 4]) {
    out.push(S_(k.slabOf({ x: -60, y, w: 120 + T, d: 6, r: 0 }, ZB, ZTOP - ZB, P, 1, 0.5), { tone: "mid" }));
  }
  // traversi tra i cassetti: righe sul frontale della cassa
  const rails = [];
  for (let i = 0; i <= N; i++) {
    const z = ZB + i * (DH + GAP) + GAP / 2;
    rails.push(k.segment([X0, Y0 + 4, z], [X0, Y1 - 4, z], P));
  }
  out.push(L(rails.join(""), { tone: "faint" }));
  // pannello del fianco: specchiatura e viti
  const yS = Y1 + 2;
  const fp = poly([[-48, yS, ZB + 12], [52, yS, ZB + 12], [52, yS, ZTOP - 12], [-48, yS, ZTOP - 12]]);
  out.push(L(fp, { tone: "faint" }));
  out.push(D([[-54, ZB + 6], [56, ZB + 6], [-54, ZTOP - 6], [56, ZTOP - 6]].map(([x, z]) => at([x, yS, z])), { size: 0.5 }));
  // la targhetta del costruttore sul fianco, con tre righe di testo
  const tx = -10, tz = ZB + 26;
  out.push(L(poly([[tx - 14, yS, tz - 7], [tx + 14, yS, tz - 7], [tx + 14, yS, tz + 7], [tx - 14, yS, tz + 7]]), { tone: "lo" }));
  out.push(L([3, 0, -3].map((dz) => k.segment([tx - 10, yS, tz + dz], [tx + (dz ? 6 : 10), yS, tz + dz], P)).join(""), { tone: "faint", free: true }));
  out.push(D([[tx - 12, tz], [tx + 12, tz]].map(([x, z]) => at([x, yS, z])), { size: 0.45 }));
  return out.join("");
}

function piano() {
  const out = [];
  out.push(S_(k.slabOf({ x: -64, y: Y0 - 4, w: 64 + X0 + T, d: Y1 - Y0 + 8, r: 0 }, ZTOP, 6, P, 1, 1), { tone: "mid" }));
  out.push(L(k.planOutline({ x: -58, y: Y0 + 2, w: 52 + X0 + T, d: Y1 - Y0 - 4, r: 0 }, ZTOP + 6, P, 1), { tone: "faint" }));
  return out.join("");
}

// sul piano: la carta nautica con la rotta, la bussola, il regolo parallelo
function strumenti() {
  const out = [];
  const z = ZTOP + 6;
  const carta = { x: -46, y: -92, w: 84, d: 112, r: 0 };
  out.push(S_(k.slabOf(carta, z, 0.6, P, 1), { tone: "lo", crease: "none" }));
  // reticolo della carta
  const grid = [];
  for (let gx = carta.x + 12; gx < carta.x + carta.w; gx += 12) grid.push(k.lineOnTop([gx, carta.y], [gx, carta.y + carta.d], z + 0.6, P));
  for (let gy = carta.y + 16; gy < carta.y + carta.d; gy += 16) grid.push(k.lineOnTop([carta.x, gy], [carta.x + carta.w, gy], z + 0.6, P));
  out.push(L(grid.join(""), { tone: "faint" }));
  // la rotta: tre lati che finiscono su punti
  const rotta = [[24, -78], [2, -46], [-14, -6], [-30, 12]];
  out.push(L(k.onTop(rotta, z + 0.6, P), { tone: "mid" }));
  out.push(D(rotta.map(([x, y]) => at([x, y, z + 0.6])), { size: 0.9, tone: "hi" }));
  // il regolo parallelo: due righe e due bracci
  const rz = z + 0.6;
  out.push(S_(k.slabOf({ x: 14, y: -70, w: 7, d: 76, r: 0 }, rz, 2, P, 1, 0.4), { tone: "mid" }));
  out.push(S_(k.slabOf({ x: 28, y: -66, w: 7, d: 76, r: 0 }, rz, 2, P, 1, 0.4), { tone: "mid" }));
  for (const y of [-56, -6]) {
    out.push(S_(k.slabOf({ x: 17, y: y - 2, w: 15, d: 4, r: 0 }, rz + 2, 1, P, 1), { tone: "mid" }));
    out.push(D([at([17.5, y, rz + 3]), at([31.5, y + 4, rz + 3])], { size: 0.5, tone: "hi" }));
  }
  // la bussola sulla carta
  const [cx, cy, cz] = [-22, 66, ZTOP + 6];
  out.push(S_(k.cylinder(cx, cy, 20, cz, 3, P, 20), { tone: "mid" }));
  out.push(S_(k.cylinder(cx, cy, 17.5, cz + 3, 4, P, 20), { tone: "hi", crease: "lo" }));
  const ticks = k.radialTicks(cx, cy, 16, 24, 6, cz + 7, [1.2, 2.6], P);
  out.push(L(ticks.minor, { tone: "lo" }), L(ticks.major, { tone: "mid" }));
  out.push(L(k.ring(cx, cy, 12, cz + 7, P, 20), { tone: "faint" }));
  // l'ago a losanga: la metà nord piena, la metà sud vuota
  const dir = [-0.4, 0.92], nor = [dir[1], -dir[0]];
  const pz = cz + 7.2;
  const punta = (f) => [cx + dir[0] * f, cy + dir[1] * f];
  const lato = (f) => [cx + nor[0] * f, cy + nor[1] * f];
  out.push(`<path class="kn" d="${k.onTop([punta(12), lato(2.6), lato(-2.6)], pz, P, true)}"/>`);
  out.push(L(k.onTop([punta(-10), lato(2.6), punta(12), lato(-2.6)], pz, P, true), { tone: "hi" }));
  out.push(D([at([cx, cy, pz])], { size: 1, tone: "hi" }));
  return out.join("");
}

// Un cassetto: la cassa con le schede (visibile solo fuori dal corpo), il frontale, il porta etichetta, la maniglia.
function cassetto(i) {
  const s = STRATI[i];
  const z0 = ZB + GAP + i * (DH + GAP);
  const z1 = z0 + DH;
  const yA = Y0 + 6, yB = Y1 - 6; // frontale
  const cassa = { x: X0 - BODY, y: yA + 4, w: BODY, d: yB - yA - 8, r: 0 };
  const out = [];
  // la cassa
  out.push(S_(k.slabOf(cassa, z0 + 1.5, DH - 4, P, 1), { tone: "mid" }));
  const zr = z0 + DH - 2.5;
  const vano = { x: cassa.x + 3, y: cassa.y + 3, w: cassa.w - 3, d: cassa.d - 6, r: 0 };
  out.push(`<path class="kv" d="${k.planOutline(vano, zr, P, 1)}"/>`);
  // le schede: una riga per scheda, con il cavaliere ogni tanto
  const lines = [], tabs = [];
  const n = s.schede;
  const passo = (vano.w - 6) / n;
  for (let c = 0; c < n; c++) {
    const x = vano.x + 3 + passo * (c + 0.5);
    lines.push(k.lineOnTop([x, vano.y + 2], [x, vano.y + vano.d - 2], zr - 1, P));
    const ty = vano.y + 10 + ((c * 37) % Math.max(1, vano.d - 30));
    if (c % 2 === 0) tabs.push(poly([[x, ty, zr - 1], [x, ty, zr + 0.6], [x, ty + 9, zr + 0.6], [x, ty + 9, zr - 1]], false));
  }
  out.push(L(lines.join(""), { tone: "lo", className: "fg-scheda" }));
  out.push(L(tabs.join(""), { tone: "mid", className: "fg-scheda" }));
  // il frontale
  const fronte = { x: X0, y: yA, w: T, d: yB - yA, r: 0 };
  out.push(`<g class="fg-fronte">${S_(k.slabOf(fronte, z0, DH, P, 1, 0.5), { tone: "hi", crease: "lo" })}</g>`);
  const xf = X0 + T;
  out.push(L(vrect(xf, yA + 4, yB - 4, z0 + 3, z1 - 3), { tone: "faint" }));
  // porta etichetta a sinistra, con il cartoncino e due ribattini
  const ey0 = yA + 12, ey1 = ey0 + 80;
  out.push(S_(k.extrude([[xf, ey0], [xf + 0.8, ey0], [xf + 0.8, ey1], [xf, ey1]], z0 + 5, DH - 10, P), { tone: "mid", crease: "faint" }));
  out.push(D([at([xf + 0.8, ey0 + 2, z0 + 9]), at([xf + 0.8, ey1 - 2, z0 + 9])], { size: 0.5 }));
  const tm = k.sideMatrix([xf + 0.9, ey1 - 6], z0 + 7.2, P, "right");
  out.push(`<text class="fg-etichetta" transform="${tm}" font-size="5.6">${s.nome}</text>`);
  // maniglia: due colonnine e una barra
  const yc = (yA + yB) / 2 + 40;
  for (const y of [yc - 18, yc + 18]) out.push(S_(k.slabOf({ x: xf, y: y - 1.5, w: 4, d: 3, r: 0 }, z0 + 7.5, 3, P, 1), { tone: "mid", crease: "none" }));
  out.push(S_(k.slabOf({ x: xf + 4, y: yc - 21, w: 2.6, d: 42, r: 0 }, z0 + 7, 4, P, 1), { tone: "hi", crease: "lo" }));
  out.push(D([at([xf + 6.6, yc - 18, z0 + 11]), at([xf + 6.6, yc + 18, z0 + 11])], { size: 0.4, tone: "lo" }));
  // la zona che il cassetto occupa fuori dal corpo: il ritaglio che nasconde la cassa quando è dentro
  const fuori = { x: X0, y: Y0 + 4, w: T + S + 8, d: Y1 - Y0 - 8, r: 0 };
  const clip = k.slabOf(fuori, z0 - 0.5, DH + 1, P, 1).fill;
  return {
    clip: `<clipPath id="fg-c${i}"><path d="${clip}"/></clipPath>`,
    g: `<g clip-path="url(#fg-c${i})"><g class="fg-cassetto" data-strato="${s.id}"${i === 0 ? ` data-aperto="" transform="${k.translateAlong(P, [S, 0, 0])}"` : ""}>${out.join("")}</g></g>`,
  };
}

const cassetti = STRATI.map((_, i) => cassetto(i));
const passo = k.axisVector(P, [S, 0, 0]);

let svg = `<svg class="fg-svg" viewBox="0 0 ${W} ${H}" role="img" aria-labelledby="fg-cassettiera-t fg-cassettiera-d">`
  + `<title id="fg-cassettiera-t">Arturo come un mobile a cassetti</title>`
  + `<desc id="fg-cassettiera-d">Un mobile da carteggio con sei cassetti, uno per strato di Arturo. Guardie: 23 guardie e automazioni. Comandi: 11 comandi con la barra davanti. Agenti: 8 subagent con un mestiere solo. Skill: 7 istruzioni che Claude carica quando servono. Memoria e sessioni: gli appunti di /fine, gli ultimi 5 per progetto. Telemetria: 16 tipi di evento da un elenco chiuso. Sul piano una carta nautica con la rotta, un regolo e una bussola.</desc>`
  + `<defs>${cassetti.map((c) => c.clip).join("")}</defs>`
  + zoccolo() + corpo() + piano() + strumenti()
  + cassetti.map((c) => c.g).join("")
  + `</svg>`;
svg = compatta(minify(svg));
const esc = (t) => t.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;");
const pass = passo.map((v) => Math.round(v * 100) / 100).join(" ");
const html = `<figure class="figura figura--cassettiera" data-figura="cassettiera" data-passo="${pass}">
<div class="figura__piastra">
<p class="figura__testa" aria-hidden="true"><span>Fig. 1</span><span>Sei cassetti, uno per strato</span></p>
${svg}
<div class="figura__piede"><p data-suggerimento>Scegli un cassetto: si apre e dice cosa contiene.</p><p class="figura__lettura" data-lettura aria-live="polite"><strong>${STRATI[0].nome}.</strong> ${esc(STRATI[0].riga)}</p></div>
</div>
<figcaption>
<ul class="fg-strati">${STRATI.map((t, i) => `<li><button type="button" data-strato="${t.id}" data-riga="${esc(t.riga)}" aria-pressed="${i === 0}">${t.nome}</button></li>`).join("")}</ul>
<p>In ogni cassetto ci sono tante schede quante sono le sue parti nel codice: 23 guardie e automazioni, 11 comandi, 8 agenti, 7 skill, 5 appunti, 16 tipi di evento.</p>
</figcaption>
</figure>`;
writeFileSync(OUT, html);
writeFileSync(OUT.replace(/\.svg\.html$/, ".dati.json"), JSON.stringify({ passo: passo.map((v) => Math.round(v * 100) / 100) }));
for (const [n, f] of Object.entries({ zoccolo, corpo, piano, strumenti })) console.log(n, compatta(minify(f())).length);
console.log("cassetti", cassetti.map((c) => compatta(minify(c.g)).length));
console.log("byte svg", svg.length, "html", html.length, "passo", passo);
