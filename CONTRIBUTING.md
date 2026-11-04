# Contributing to the Metacrafter Registry

Thank you for improving the registry. Every record is one YAML file under
`data/`. The site at https://registry.apicrafter.io and its JSON API are
generated from these files.

## Quick start

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
metacrafter-registry validate     # add -w to list warnings
metacrafter-registry build        # writes dist/ and data/*_latest.json(l)
metacrafter-registry serve        # preview at http://127.0.0.1:8089
pytest -q
```

You can also edit a single file on GitHub: each record page on the site has an
"edit on GitHub" link. CI then validates the change on the pull request.

If you do not want to write YAML, open an issue with a form:
- [Propose a datatype](https://github.com/apicrafter/metacrafter-registry/issues/new?template=new-datatype.yml)
- [Fix a datatype](https://github.com/apicrafter/metacrafter-registry/issues/new?template=fix-datatype.yml)

A maintainer or contributor then turns the issue into a `draft` record.

## Adding or changing a datatype

1. Put the file in `data/datatypes/<COUNTRY>/<category>/<id>.yaml` for a
   country-specific type, or in `data/datatypes/any/<category>/<id>.yaml` for
   a global one.
2. Follow these conventions:
   - `id`: lowercase `[a-z0-9_]`. Country-specific IDs start with the country
     code and an underscore, for example `ru_inn` or `us_ssn`. The file name
     must be `<id>.yaml`.
   - `country`: uppercase ISO 3166-1 alpha-2 codes. A file under
     `datatypes/RU/` must list `RU`.
   - `langs`: ISO 639-1 codes from `data/langs.yaml`. Use `common` for
     language-independent values.
   - `categories`: IDs from `data/categories.yaml`.
   - `is_pii`: `true` or `false`.
   - `status`: `draft` for a new record. A maintainer sets `stable` after
     review. A record is stable only if it has a real description and
     evidence: a regexp, examples or an authoritative link.
   - `regexp`: Python `re` syntax, anchored with `^…$`. Do not use possessive
     quantifiers (`\d+` followed by `+`) or atomic groups (`(?>…)`): older
     Pythons and browsers reject them.
   - `examples`: real-format values. Every example must match the regexp. Do
     not use placeholders such as `1234567890`, and do not use personal data
     of real people.
   - `links`: authoritative sources, such as the standard, the issuing
     authority, Wikipedia or Wikidata. Do not link a generic page, such as the
     country's article.
3. Run `metacrafter-registry validate` and `metacrafter-registry build`.
4. Commit the YAML file **and** the regenerated `data/*_latest.json(l)` files.
   CI fails if they are stale.

A pattern is one representation of a datatype. It sets `semantic_type: <id>`
and inherits the datatype's `categories`, `is_pii` and `classification` unless
it declares them.

The full record contract is in `schema/` (JSON Schema). Empty values are not
allowed: omit a field instead of writing `''` or `[]`. To retire a duplicate,
keep one record and add the old id to its `aliases`. Never delete a published
id.

## What CI checks

The build fails on any of these:
- schema errors
- unknown categories, countries or languages
- duplicate IDs or aliases
- a file name that differs from the ID
- unresolved `semantic_type`, `parent` or tool `supported_types`
- a regexp that does not compile, or that uses non-portable syntax
- an example that does not match its regexp
- a directory that does not match the record's country

Warnings do not fail the build: a regexp that is not anchored, and an example
that looks like a placeholder.

CI also builds the site and checks every internal link. It also checks the
public URL contract: `/datatype/<id>`, `/datatype/<id>.json`,
`/registry.json`, `/tools.json`, `/tool/<id>` and `/api/v1/*`. metacrafter
and stored catalog metadata depend on these URLs, so they must never break.

## Releases and versioning

Data releases use [Semantic Versioning](https://semver.org/):

- **MAJOR**: a published ID is removed without an alias, or a field in the
  legacy JSON (`/registry.json`, `/datatype/<id>.json`) or in `/api/v1/` is
  removed or retyped.
- **MINOR**: new records, new fields or new endpoints.
- **PATCH**: corrections to existing values.

To release, a maintainer bumps `version` in `pyproject.toml`, merges, and
pushes the matching tag, such as `v1.3.0`. The workflow then publishes the
Python package to PyPI through trusted publishing. Before the first release,
configure this once on pypi.org: add a trusted publisher for
`apicrafter/metacrafter-registry`, workflow `release.yml`, environment
`pypi`. The same workflow also publishes a GitHub Release with these files:
- `datatypes.json`, `datatypes.jsonl` and `datatypes.csv`
- `tools.json`
- the reference lists
- `openapi.json`
- the manifest
- the legacy `registry.json`
- a zip of the site
- `SHA256SUMS`

## Larger changes

Changes to the data model, the URL contract or the build go through an
OpenSpec proposal in `openspec/changes/`. See `AGENTS.md`.

## License of contributions

The repository, code and data, is under the
[Apache License 2.0](LICENSE). By section 5 of that license, your contribution
is under the same license unless you state otherwise. There is no contributor
license agreement (CLA): you keep the copyright to your work, and anyone may
use and redistribute the registry under the same terms.

Do not submit material that you may not publish under this license. Quote
other sources only briefly, and link to them.
