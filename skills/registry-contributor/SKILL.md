---
name: registry-contributor
description: Add or improve a record in the Metacrafter Registry repository (data/datatypes/*.yaml) so that it passes validation - new national identifiers, regexps, examples, check digits, translations, merging duplicates. Use when working in the metacrafter-registry repository on datatype, pattern or tool YAML files.
---

# Contribute to the Metacrafter Registry

Each record is one YAML file. The contract is in `schema/datatype.schema.json`,
`schema/pattern.schema.json` and `schema/tool.schema.json`. Set up once:

```bash
pip install -e ".[dev]"
```

## Add a datatype

1. **Check that it is not already there:**
   ```bash
   metacrafter-registry report --json | grep -i <word>
   ```
   Also search `data/datatypes/` for the name, and look in `aliases`.
2. **Place the file.** Use `data/datatypes/<CC>/<category>/<id>.yaml` for a
   national type (`CC` is uppercase ISO 3166-1, and the record must list it in
   `country`). Use `data/datatypes/any/<category>/<id>.yaml` for a global one.
   The file name must equal the `id`.
3. **Write the record:**
   ```yaml
   id: pl_pesel                # [a-z0-9_]; new national ids start with <cc>_
   name: Polish PESEL number
   status: draft               # stable only after a human review
   doc: >-                     # your own words, not pasted from Wikipedia
     National identification number of Poland ...
   categories: [pii, persons]  # ids from data/categories.yaml
   country: [PL]
   langs: [pl]                 # ISO 639-1, or common
   is_pii: true
   classification: identifier
   regexp: '^\d{11}$'          # Python re, anchored, no possessive quantifiers
   examples:
   - value: '...'              # string; format-valid; never a real person's data
     description: ...
   - value: '...'
     valid: false              # negative example: must not match
   links:
   - type: wikipedia
     url: https://en.wikipedia.org/wiki/PESEL
   ```
4. **Validate and build:**
   ```bash
   metacrafter-registry validate
   metacrafter-registry build
   pytest -q
   ```
   Commit the YAML file together with the regenerated `data/*_latest.json(l)`.

## Rules

- **Never invent facts.** Do not write a regexp, check-digit rule, Wikidata id
  or example unless you verified it in an authoritative source: a standard, an
  issuing authority, Wikipedia or Wikidata. If you cannot verify a field,
  leave it out.
- **Examples:**
  - Use documentation or test values. Never use real people's data, and never
    use placeholders like `1234567890`.
  - Every positive example must match the regexp.
  - With `checksum`, every positive example must also pass the check digit.
    Known algorithms are `luhn`, `iban_mod97`, `gtin`, `isbn10`, `isbn13`,
    `ru_inn`, `ru_snils`, `ru_ogrn`, `fr_nir`, `at_uid`, `bg_vat`, `no_fnr`,
    `it_codicefiscale`, `it_iva`, `fi_hetu` and `es_dni`
    (`src/metacrafter_registry/checksums.py`).
  - Compute check digits with code. Do not do it by hand.
- **Status:**
  - Keep `status: draft` unless the record has a real description and
    evidence (a regexp, examples or an authoritative link) that you checked.
  - Tell the user which fields you are unsure about.
- **IDs:**
  - Never rename or delete a published id.
  - To merge a duplicate, keep the better record, add the other id to its
    `aliases`, move tool `supported_types` references, and delete the other
    file. The old id keeps resolving.
- **Patterns:** a pattern sets `semantic_type: <datatype id>` and inherits
  `categories`, `is_pii` and `classification` unless it overrides them.
- **No empty values:** omit a field rather than writing `''` or `[]`.

## Improve existing records

Find the records that need work most:

```bash
metacrafter-registry report --status draft --limit 30
```

Each record lists the missing elements: description, regexp, examples,
negative example, source link, mapping, translation. Fill only what you can
verify, then run `validate` and `build` again.
