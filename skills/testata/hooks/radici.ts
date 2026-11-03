// Dove cercare il repository git di Arturo per leggerne la versione, a partire dalla cartella del mod.
// In Arturo il mod sta in <arturo>/skills/testata: la radice è due cartelle sopra. Una copia del mod
// fuori da Arturo (la config di chi lo mantiene) cambia solo questo file.
export function radiciArturo(radiceMod: string, _home: string): string[] {
  return [`${radiceMod}/../..`]
}
