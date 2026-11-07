## 1. Export

- [x] 1.1 Add the mapping links: `exactMatch` for Bioregistry, FHIR and D3M; `broadMatch` for DPV. Normalize D3M `http://schema.org/` IRIs and deduplicate.
  - `exactMatch` grows from 769 to 991 links; 259 DPV `broadMatch` links.
- [x] 1.2 Add the detection payload: status, PII flag, classification, regexp, checksum, examples, countries, languages, links, deprecation.
- [x] 1.3 Declare top concepts on the scheme and the concepts.
  - 1,464 top concepts: exactly the concepts without `broader`.
- [x] 1.4 Export tools with their supported types, resolving aliases.
  - 51 tools, 3,453 `mcr:supportedType` links.

## 2. Vocabulary and files

- [x] 2.1 Define the `mcr:` terms once and write `/vocab.ttl` and the `/vocab` page from that definition.
- [x] 2.2 Write `/datatype/<id>.ttl` for records and aliases, and link it from record pages.
  - 2,136 files (2,117 records, 19 aliases). Each parses on its own and matches `/registry.ttl`.
- [x] 2.3 Add `vocab.ttl` to the manifest bulk files and the release assets. Add `/datatype/email.ttl` and `/vocab.ttl` to the URL contract check.

## 3. Tests and documentation

- [x] 3.1 Tests: the new links and payload, DPV `broadMatch`, D3M deduplication, top concepts, tools, the per-record and alias files, and that every `mcr:` term used is declared.
- [x] 3.2 Document the new URLs in `README.md`, `about.html` and `llms.txt`.
