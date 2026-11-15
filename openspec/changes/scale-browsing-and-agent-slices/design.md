## Context

The site is static and served by GitHub Pages: no server-side search, no
content negotiation, no control of response headers. Every list must be a
file. `/datatype/` is one HTML table of all records; `site.js` filters its
rows by `data-*` attributes. Category and country pages use the same table
macro and are small: the largest, `/category/pii`, has 643 rows and 66 KB
compressed.

`/search-index.json` (0.9 MB, 239 KB compressed) holds one entry per record
with the keys `id`, `n`, `d`, `k`, `p`, `s`, `c`, `t`. It was written for the
search page. Since #217 it is described in OpenAPI and in `llms.txt`.

`identify-core.js` already converts the registry's Python regular expressions
to JavaScript and implements the check-digit algorithms. `/identify-index.json`
carries the converted pattern of each record.

## Goals / Non-Goals

**Goals:**

- The size of `/datatype/` does not grow with the number of records.
- An agent can get the records of one country or one category in one request
  of a few hundred kilobytes at most.
- A visitor can test one value against one record on that record's page.

**Non-Goals:**

- A hosted search API or a remote MCP server. Both need hosting outside GitHub
  Pages; see Open Questions.
- A translated interface. Only record names are shown in other languages.
- Changing the content type of `.jsonl` files. GitHub Pages sets it.
- Splitting `/llms-full.txt`. The slices and the Markdown twins cover the same
  need with files that already have a clear shape.
- Removing `/search-index.json`.

## Decisions

**One compact index with readable keys, not a second private one.**

- `/api/v1/datatypes-index.json` is an array with one object per record:
  `id`, `name`, `kind`, `status`, `is_pii`, `categories`, `country`,
  `quality` (the score), `has_regexp`, `doc` (cut to 160 characters), and
  `names` (aliases and translated names) when the record has them.
- The list page needs categories and countries as separate lists, and the
  quality score for sorting; the search index has neither. Adding them under
  more one-letter keys would make the file harder for an agent to read.
- The search page moves to the new index, so the site downloads one index, and
  the browser caches it for both pages.
- `/search-index.json` stays published with its current shape, because it has
  been a documented URL since #217. OpenAPI marks it deprecated.
- Alternative: extend `/search-index.json`. Rejected: its keys would need to
  change meaning (`c` mixes categories and countries), which breaks the shape.

**Slices hold full normalized records.**

- `/api/v1/countries/<CC>.json` and `/api/v1/categories/<id>.json` are arrays
  of the same objects as `/api/v1/datatypes.json`.
- An agent that labels data from one country needs the regular expressions and
  examples, not only names. With index entries it would make one more request
  per record.
- Sizes stay small: the
  largest country slice, RU, has 175 records (350 KB, 64 KB compressed); the
  largest category slice, `pii`, has 643 records (1.1 MB, 139 KB compressed).
- A record with several countries or categories is in each of their slices.
  A record without a country is in no country slice; the index lists it with
  an empty `country`.
- Alternative: slices of index entries. Rejected for the reason above; the
  index itself can be filtered by country in one request.

**The list page: 100 rows in HTML, the rest from the index.**

- The page keeps its URL, its filter form and its query parameters (`q`,
  `category`, `country`, `kind`, `status`, `rules`, `pii`), so existing links
  such as `/datatype/?pii=yes` keep working.
- The first 100 records in id order are rendered in HTML, so the page has
  content before any script runs and search engines see real links. Every
  record page stays reachable from the category and country pages and from the
  sitemap.
- `site.js` loads the index, then filters, sorts and pages in memory and
  renders 100 rows at a time. The filter `rules` needs a flag per record:
  the index entry gets `has_rules`.
- Alternative: static pages `/datatype/page/<n>`. Rejected: filters could not
  work across pages, and 31 more pages would need to be kept in step.
- Alternative: keep one table and virtualize scrolling. Rejected: it still
  ships 2.6 MB of HTML.

**The value test reuses the Identify code and its index.**

- The record page embeds the JavaScript form of the record's own pattern in
  the page (a `data-` attribute), so the test needs no index download.
- `identify-core.js` is loaded on the record page only when the record has a
  pattern or a check-digit algorithm.
- The result states three facts separately: the value matches the pattern or
  not; the check digit is valid, invalid or not applicable; and a reminder
  that a match does not prove the value is real.
- When the pattern cannot be converted to JavaScript, the field is not shown.
  A wrong answer is worse than no tester.

**Native-language names come from `translations`, for the record's `langs`.**

- Under the title the page shows the translated name for each language in the
  record's `langs`, with a `lang` attribute: for `bik`, «Банковский
  идентификационный код». Today 519 records have such a translation.
- Names in other languages stay in the translations table. Showing all of them
  under the title would crowd records that have ten translations.

## Risks / Trade-offs

- **The list needs JavaScript beyond 100 rows.** Today all rows are in the
  HTML. Mitigation: the no-JavaScript note links to the category and country
  pages, which list every record.
- **About 430 more files per build.** They are small; the build writes
  thousands of files already. The manifest lists the index, not each slice.
- **Two indexes for a time.** `/search-index.json` stays until a major
  version removes it; its cost is one extra file in the build.

## Open Questions

- **Remote MCP server.** The MCP server runs only locally (stdio, installed
  from GitHub). A hosted HTTP endpoint would let an agent use the registry
  with no installation, but it needs hosting, a domain and an owner for its
  uptime. This is a decision for the registry owner and is not part of this
  change.
- **Default order of the list.** This design keeps id order. Sorting by
  quality score first would show reviewed records first; it also changes what
  the first 100 HTML rows are after every data change.
