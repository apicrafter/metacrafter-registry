## 1. Research

- [x] 1.1 Review FIBO's glossary approach and the integration of glossaries with semantic types. Record the result in `devdocs/FIBO_ANALYSIS.md`.
  - The review used FIBO `master` at commit `33a92cd` (2026-10-27): 2,767 labelled classes, of which 1,977 are `Release`.

## 2. Data model and validation

- [x] 2.1 Add `mappings.fibo` (a class path or a list of them) to `schema/datatype.schema.json` and to the OpenAPI record schema.
- [x] 2.2 Add `fibo.py`: the IRI helpers, the RDF/XML class scanner, and building and loading `data/vocabularies/fibo.json`.
- [x] 2.3 Add the validation gate:
  - an unknown class is an error;
  - a non-`Release` class is a warning;
  - an unused pinned class is a warning.
- [x] 2.4 Add `metacrafter-registry fibo update|check|search --fibo-dir <checkout>`.
- [x] 2.5 In CI, check out FIBO at the ref pinned in `data/vocabularies/fibo.json` and run `fibo check`. A hand-edited term list then fails CI.

## 3. Publication

- [x] 3.1 Publish the FIBO IRIs:
  - SKOS `exactMatch` in `/registry.ttl`;
  - JSON-LD `sameAs`;
  - a FIBO row on the record page, with the label, abbreviations and a definition tooltip;
  - the IRI in the Markdown twin.
- [x] 3.2 `crosswalk("fibo", path or IRI)` in the Python API. Update the MCP tool description.

## 4. Data

- [x] 4.1 Map 32 records to 29 `Release` FIBO classes. Map only exact concept matches; each was checked against the FIBO definition.
- [x] 4.2 Pin the classes with `fibo update`, at FIBO commit `33a92cd`, and regenerate `data/*_latest.json(l)`.

## 5. Tests and documentation

- [x] 5.1 Add tests:
  - scanner;
  - schema rejection of a full IRI;
  - unknown class;
  - update, check and the unused-class warning;
  - the repository pins exactly its mapped classes;
  - crosswalk;
  - HTML, JSON-LD, Markdown and SKOS output.
- [x] 5.2 Document `mappings.fibo` and the `fibo` command in `README.md`, `AGENTS.md` and the agent skills.

## 6. Follow-ups (separate changes)

- [ ] 6.1 Add a DataHub business-glossary export as a build output, with `source_url` set to the FIBO IRI. It replaces `scripts/export.py`, which still reads the v1 format.
- [ ] 6.2 Add draft records for the FIBO identifiers that the registry lacks: UTI, UPI, USI, DTI, MCC, ELF, BBAN, CINS, Common Code, RSSD ID, FDIC certificate number, IIN and ZIP+4. Verify each format against its standard first.
