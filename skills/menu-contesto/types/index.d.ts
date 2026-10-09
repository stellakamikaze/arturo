export type Contesto = string

declare module 'claude-code' {
  interface PluginState {
    'menu-contesto': { testo: Contesto }
  }
}
