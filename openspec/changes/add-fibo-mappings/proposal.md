## Why

Issue #13 asks how the registry relates to FIBO, the Financial Industry
Business Ontology, and to the business glossaries built on it, such as
DataHub's. The analysis is in `devdocs/FIBO_ANALYSIS.md`.

FIBO and the registry describe the same financial identifiers and codes from
two sides:

- FIBO gives their business meaning.
- The registry tells how to recognize their values.

Nothing links the two today. So a column that metacrafter labels `iban`
cannot be tied to the FIBO term that a glossary uses.

## What Changes

- A new optional mapping key, `mappings.fibo`. It holds one FIBO class, or a
  list of them. A class is given as its IRI without the
  `https://spec.edmcouncil.org/fibo/ontology/` prefix.
- A committed FIBO term list, `data/vocabularies/fibo.json`:
  - It holds the label, definition, abbreviations and maturity of every mapped
    class.
  - It records the FIBO commit those values come from, and FIBO's MIT licence
    notice.
  - Validation fails on a mapping that the list does not contain.
- A new command, `metacrafter-registry fibo update|check|search --fibo-dir
  <checkout>`. It pins the mapped classes, compares them with another FIBO
  version, and helps contributors find a class.
- FIBO links in the published outputs:
  - a SKOS `exactMatch` in `/registry.ttl`;
  - a JSON-LD `sameAs` on record pages;
  - a FIBO row on record pages;
  - the IRI in the Markdown twins;
  - `crosswalk("fibo", ...)` in the Python API and the MCP server. It accepts
    a full IRI as well as a path.
- 32 records gain verified FIBO mappings, to 29 `Release` classes.

The JSON shapes only gain an optional key, so nothing is **BREAKING**.

## Capabilities

### New Capabilities

- `fibo-mappings`: the mapping of registry records to FIBO classes, its
  validation and its publication.

### Modified Capabilities

None. The typed-mappings and linked-data requirements of
`modernize-registry-platform` are not archived yet. This change adds to them
without changing their behaviour.

## Impact

- **Schema:** `schema/datatype.schema.json`, `mappings.fibo`.
- **Data:**
  - `data/vocabularies/fibo.json`, new;
  - 32 records;
  - the regenerated `data/datatypes_latest.json(l)`.
- **Code:**
  - `fibo.py`, new;
  - `validate.py`, `cli.py`, `model.py`, `agents.py`, `build.py`, `client.py`,
    `mcp_server.py`, `openapi.py`;
  - the datatype page template.
- **CI:** `ci.yml` checks out FIBO at the pinned commit and runs `fibo check`.
- **Dependencies and network:** none at build time. Only `fibo update`,
  `fibo check` and `fibo search` need a FIBO checkout.
