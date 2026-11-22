# Arturo: il ramo del sito

Questo ramo porta il sito di Arturo, [arturo.stellakamikaze.org](https://arturo.stellakamikaze.org), e niente altro. Il codice di Arturo sta nel ramo `main` (i rilasci firmati) e nel ramo `dev` (il lavoro in corso).

## Installare Arturo

Installa Claude Code, scrivi `claude` e incolla questa frase:

`Installa Arturo: https://github.com/stellakamikaze/arturo/blob/landing-v2/INIZIA.md`

Claude installa Arturo come plugin e ti chiede un sì prima di ogni passo. [INIZIA.md](INIZIA.md) è la copia di riferimento dei passi: la pagina /inizia/ del sito ne è una copia.

## Cosa c'è qui

- `sito/`: le pagine servite, con `sito/installa.sh`, lo script che installa il plugin da un rilascio firmato.
- `strumenti/`: i generatori delle pagine (novità, roadmap, idee) e `pubblica.sh`, che porta `sito/` sul server.
- `server/`: la config di nginx del sito.
- `INIZIA.md`: i passi d'installazione che Claude Code legge.
- `PRODUCT.md` e `DESIGN.md`: chi usa il sito e come è disegnato.
- `tests/`: i banchi del sito (`test_inizia.py`, `test_installa.py`, `test_roadmap.py`) e il controllo d'igiene del repository pubblico.

Prima di un push lancia i tre banchi del sito: `python3 tests/test_inizia.py`, `python3 tests/test_installa.py`, `python3 tests/test_roadmap.py`. Un push su questo ramo e la pubblicazione con `strumenti/pubblica.sh` vanno fatti di seguito: lo script che il sito serve e quello di GitHub devono restare uguali.

## Licenza

MIT, come il resto di Arturo: vedi [LICENSE](LICENSE).
