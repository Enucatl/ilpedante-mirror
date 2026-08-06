# ilpedante-mirror

Archivio statico di [ilpedante.info](http://ilpedante.info), pubblicato con
Jekyll e GitHub Pages.

I 142 file Markdown e i media disponibili sono versionati: la pubblicazione
non dipende dal sito originale né dagli strumenti Python. Per rigenerare i post
in modo deterministico dallo snapshot CSV:

```
uv sync --extra dev
uv run build_archive
```

Le due acquisizioni aggiuntive del 2025 e la cattura del post satirico sulle
sardine sono conservate in `recovered_source/`; il comando le reimporta senza
dipendere dalla rete.

`_posts/posts.csv.gz` è lo snapshot originale. Il vecchio comando
`bulk_download` resta disponibile solo per documentare il processo con cui lo
snapshot fu creato.

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
