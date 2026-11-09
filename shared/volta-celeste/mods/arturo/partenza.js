// Da dove partire: il todo da cui ripartire e i passi legati che lo seguono.
// I dati li calcola Arturo (blocco "progetti" della vista: da_dove e catena). Qui si cercano solo i
// titoli nei gruppi. Modulo senza import di Herdr, così il banco lo prova con node (HZ10).

const POI_MAX = 3;

// vista: la vista di `arturo todo --progetto X --json`. fatti: i numeri segnati fatti in questo giro.
// Restituisce { todo, motivo, poi: [todo...] } oppure null.
export function partenza(vista, fatti = new Set()) {
  const per_id = new Map();
  for (const g of vista?.gruppi ?? []) for (const t of g.todo ?? []) per_id.set(t.id, t);
  const p = (vista?.progetti ?? []).find((x) => x?.da_dove) ?? null;
  if (!p) return null;
  const todo = per_id.get(p.da_dove.id);
  if (!todo || fatti.has(todo.id)) return null;
  const catena = Array.isArray(p.catena) ? p.catena : [];
  const qui = catena.indexOf(todo.id);
  const poi = qui < 0 ? [] : catena.slice(qui + 1)
    .map((id) => per_id.get(id)).filter((t) => t && !fatti.has(t.id)).slice(0, POI_MAX);
  return { todo, motivo: p.da_dove.motivo || "", poi };
}
