# diagram-design: i diagrammi, dall'upstream

Arturo non porta una skill per i diagrammi. Se ti servono schemi di architettura, flussi, linee del
tempo o mappe da mettere in un documento o in una presentazione, ti consigliamo **diagram-design**,
una skill pubblica di Cathryn Lavery: [github.com/cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design),
licenza MIT. Arturo non la copia: la installi dall'upstream, così ricevi le sue versioni nuove senza
aspettare Arturo.

## Cosa fa

- Disegna un diagramma come pagina HTML con l'SVG dentro, in uno stile editoriale coerente: più di
  quaranta tipi, dai flussi alle linee del tempo, dagli schemi di architettura alle mappe.
- Importa un diagramma già fatto con draw.io, Mermaid o Excalidraw.
- Esporta in PNG o SVG, da mettere in un documento o in una slide.

## Come si installa

Come plugin di Claude Code, in una sessione:

```
/plugin marketplace add cathrynlavery/diagram-design
/plugin install diagram-design@diagram-design
```

Poi scrivi `/plugin`, apri **Marketplaces**, scegli **diagram-design** e accendi **Enable
auto-update**: Claude Code tiene spento l'aggiornamento automatico per i marketplace di terzi, e
senza questo passo resti alla versione installata.

In alternativa, nel terminale: `npx skills add cathrynlavery/diagram-design`. Così la skill si
aggiorna solo quando rilanci il comando.

## Da sapere

Le versioni ufficiali escono solo da quel repository. Il file `PRIVACY.md` dell'upstream dice cosa la
skill manda in rete.
