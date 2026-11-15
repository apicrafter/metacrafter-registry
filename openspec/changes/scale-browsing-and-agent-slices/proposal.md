## Why

A review of the live site in November 2026 (3,002 records) found that the
registry has outgrown the way it lists records, for people and for agents.
Pull requests #217 and #219 fixed what needed no design. Four problems remain:

- **The list page is too heavy.** `/datatype/` is 2.6 MB of HTML (428 KB
  compressed) with 36,155 DOM nodes. On a slow connection (about 30 KB/s) it
  took 13.6 s to download, and the filters work only after the whole page is
  parsed. The page grows with every record.
- **An agent cannot narrow the data before it downloads it.** The only
  machine-readable lists are the whole registry: `/api/v1/datatypes.json` is
  5.5 MB, `/llms-full.txt` is 1.6 MB. Neither fits a context window. There is
  no file for one country or one category, and the search index uses
  one-letter keys and mixes categories with countries.
- **A record page cannot test a value.** The page shows the regular expression
  and the check-digit algorithm, but a visitor must go to `/identify` and
  search the whole registry to learn whether one value is valid for this type.
- **Translated names are hidden.** 47% of the records have translations, but
  the record page shows them only in a table near the bottom. A reader who
  knows the type as «Банковский идентификационный код» sees only "Russian
  bank identification code (BIK)" in the title.

## What Changes

- A compact index of all records, `/api/v1/datatypes-index.json`, with
  readable keys. The list page, the search page and agents use the same file.
- Slices of the normalized records: `/api/v1/categories/<id>.json` and
  `/api/v1/countries/<CC>.json`.
- A Markdown twin for each country page, `/country/<CC>.md`, like the one
  categories have. `llms.txt` links to these twins instead of the HTML pages.
- `/datatype/` renders the first 100 records in HTML and loads the rest from
  the compact index. Filters, sorting and paging run in the browser. Without
  JavaScript the page links to the category and country pages, which list
  every record.
- A "Test a value" field on each record page that has a regular expression or
  a check-digit algorithm. It runs in the browser; the value is not sent.
- The record page shows the names in the record's own languages under the
  title.

Nothing is **BREAKING**. No existing URL or JSON shape changes.
`/search-index.json` stays published. The URL contract gains the four URL
families above.

## Capabilities

### New Capabilities

- `registry-slices`: the compact index, the per-category and per-country
  slices and the country Markdown twins.
- `scalable-browsing`: the list page that does not grow with the registry, the
  value test and the native-language names on record pages.

### Modified Capabilities

None. The `registry-site`, `registry-api` and `agent-integration` requirements
of `modernize-registry-platform` are not archived yet. This change adds to them
without changing their behaviour.

## Impact

- **Code:** `build.py` (index, slices, the shorter list page), `agents.py`
  (country Markdown, `llms.txt`), `openapi.py`, `contract.py`; templates
  `datatype_list.html` and `datatype.html`; `site.js`, and a small script for
  the value test that reuses `identify-core.js`.
- **Outputs:** about 430 new small files (36 category slices, 198 country
  slices, 198 country Markdown twins, one index). `/datatype/index.html`
  shrinks from 2.6 MB to under 150 KB.
- **Data and schema:** none. No record changes.
- **Dependencies and network:** none.
