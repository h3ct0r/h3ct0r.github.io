# h3ct0r.github.io

Personal academic website of Héctor Azpúrua, built with Jekyll (al-folio theme) and deployed to GitHub Pages by `.github/workflows/pages.yml` on every push to `master`.

## Run locally

```bash
bundle install
bundle exec jekyll serve
```

## Update from Lattes

Publications, students, awards, patents and service are generated from a Lattes CV export (XML):

```bash
python3 bin/lattes_import.py path/to/lattes.xml
```

This rewrites `_bibliography/*.bib`, `_data/lattes.yml`, `_data/group.yml` and `_data/cv.yml`. Re-running it with the same export changes nothing.

- **Selected papers, awards, project tags, venue badges and English translations** are set in the tables at the top of `bin/lattes_import.py`.
- **Links added by hand** to a `.bib` entry (`pdf`, `code`, `html`, `preview`, ...) are kept on re-import.
- **Papers that are not in Lattes** can be added to a `.bib` file with `manual = {true}`; the importer keeps them as written.
- **Crossref metadata** for entries with a DOI is cached in `bin/crossref_cache.json`. Use `--offline` to skip the network, or `--refresh-crossref` to re-download.

Hand-written content lives in `_pages/` (About, Research, Group, CV, PhD), `_projects/` (one page per research project) and `_news/`.
