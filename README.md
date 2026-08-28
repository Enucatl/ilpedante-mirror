# ilpedante-mirror

Archivio statico di [ilpedante.info](http://ilpedante.info), pubblicato con
Jekyll e GitHub Pages.

I file Markdown e i media disponibili sono versionati: la pubblicazione
non dipende dal sito originale né dagli strumenti Python. Per rigenerare i post
in modo deterministico dallo snapshot CSV:

```
uv sync --extra dev
uv run build_archive
```

Gli articoli vengono letti dallo snapshot live; il comando aggiorna l'intero
archivio a ogni acquisizione.

`_posts/posts.csv.gz` è lo snapshot aggiornato del sito. Per acquisire gli
articoli disponibili dal sito e rigenerare l'archivio:

```
uv run bulk_download https://ilpedante.info/home/loadArticoli
uv run build_archive
```

Per gli aggiornamenti periodici, `bulk_download --incremental` riusa il
contenuto già presente e scarica solo gli articoli nuovi. Continua comunque a
leggere l'elenco completo, ma l'archivio è append-only: gli articoli assenti
dall'elenco vengono conservati. Se il sito non risponde o restituisce un
elenco vuoto, l'acquisizione fallisce senza sovrascrivere lo snapshot. Senza
`--incremental`, vengono riscaricati gli articoli presenti, mantenendo comunque
quelli già archiviati ma assenti dal sito. `build_archive` aggiorna i file
Markdown pubblicati.

## Pubblicazione

In **Settings → Pages**, scegliere **Deploy from a branch**, quindi il branch
`main` e la directory `/(root)`. Il sito sarà disponibile all'indirizzo
<https://enucatl.github.io/ilpedante-mirror/>.

Per verificare localmente:

```
uv run pytest
uv run ruff format --check .
JEKYLL_ENV=production bundle exec jekyll build
```
