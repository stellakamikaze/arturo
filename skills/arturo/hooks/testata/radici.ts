// Dove cercare il repository git di Arturo per leggerne la versione, a partire dalla cartella del mod.
// In Arturo il mod sta in <arturo>/skills/arturo (radiceCodice di parti.ts).
import { radiceCodice } from '../parti'

export function radiciArturo(radiceMod: string, _home: string): string[] {
  return [radiceCodice(radiceMod)]
}
