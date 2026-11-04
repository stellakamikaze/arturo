// Rende più corti i path del kit: M/L/Z assoluti con un decimale diventano relativi e impliciti.
const NUM = /-?\d*\.?\d+/g;
const r1 = (v) => {
  let t = (Math.round(v * 10) / 10).toFixed(1).replace(/\.0$/, "");
  if (t === "-0") t = "0";
  return t.replace(/^(-?)0\./, "$1.");
};
const pair = (a, b) => {
  const sa = r1(a), sb = r1(b);
  return sa + (sb.startsWith("-") ? "" : " ") + sb;
};
export function relPath(d) {
  if (!/^[MLZ0-9.\s-]+$/.test(d)) return d;
  const tokens = d.match(/[MLZ]|-?\d*\.?\d+/g);
  let out = "", i = 0, cx = 0, cy = 0, sx = 0, sy = 0, last = "";
  // si lavora con le coordinate arrotondate, così l'errore non si accumula
  const rnd = (v) => Math.round(v * 10) / 10;
  while (i < tokens.length) {
    const t = tokens[i++];
    if (t === "Z") { out += "z"; cx = sx; cy = sy; last = "z"; continue; }
    const x = rnd(+tokens[i++]), y = rnd(+tokens[i++]);
    if (t === "M") {
      out += (out ? "m" : "M") + (out ? pair(x - cx, y - cy) : pair(x, y));
      sx = x; sy = y; last = out.length > 1 + pair(x, y).length ? "m" : "M";
    } else {
      const p = pair(x - cx, y - cy);
      out += (last === "m" || last === "l" ? (p.startsWith("-") ? "" : " ") : "l") + p;
      last = "l";
    }
    cx = x; cy = y;
  }
  return out;
}
export function minify(svg) {
  return svg.replace(/ d="([^"]*)"/g, (_, d) => ` d="${relPath(d)}"`);
}

// Classi corte e prefissate (k*) al posto di quelle del kit: il CSS sta in sito/stile/figure.css.
const TONO = { hi: "k1", mid: "k2", lo: "k3", faint: "k4", lit: "k5" };
export function compatta(svg) {
  return svg
    .replace(/<g class="iso-solid">((?:(?!<\/?g)[\s\S])*)<\/g>/g, "$1")
    .replace(/class="iso-fill"/g, 'class="kf"')
    .replace(/class="iso-shade" data-shade="(\d)"/g, 'class="ks$1"')
    .replace(/class="iso-top"/g, 'class="kt"')
    .replace(/class="iso-line iso-(?:crease|bevel)" data-tone="(\w+)"/g, (_, t) => `class="kl ${TONO[t]}"`)
    .replace(/class="iso-line iso-edge" data-tone="(\w+)"/g, (_, t) => `class="ke ${TONO[t]}"`)
    .replace(/class="iso-line( [\w-]+)?" data-tone="(\w+)"/g, (_, extra, t) => `class="kl ${TONO[t]}${extra || ""}"`)
    .replace(/class="iso-dots" data-tone="(\w+)"/g, (_, t) => `class="kd ${TONO[t]}"`)
    .replace(/class="iso-halo"/g, 'class="kh"')
    .replace(/ data-free="[^"]*"/g, "");
}
