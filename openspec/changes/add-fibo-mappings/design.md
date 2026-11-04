## Context

Records already carry typed `mappings` to Wikidata, Schema.org, DPV,
Presidio, Google DLP, Purview, D3M and Sherlock. The build stays offline:

- metacrafter-rules coverage is pinned in a committed summary,
  `data/coverage/metacrafter-rules.json`;
- the SKOS export emits `exactMatch` for mappings that have a resolvable URI.

FIBO identifies classes by IRIs such as
`https://spec.edmcouncil.org/fibo/ontology/FBC/ProductsAndServices/ClientsAndAccounts/InternationalBankAccountIdentifier`.
The server returns HTTP 200 for any path under `/fibo/ontology/`, including
misspelled ones, so a link check cannot validate a mapping.

## Goals / Non-Goals

**Goals:**

- Typo-proof FIBO mappings, validated without network access.
- FIBO links in every linked-data output that already carries mappings.
- A contributor workflow that does not require reading RDF by hand.

**Non-Goals:**

- Importing FIBO concepts as datatypes, or publishing the FIBO hierarchy.
- Typed match strength (`closeMatch`, `broadMatch`). Only exact concept
  matches are mapped, as for the other crosswalks.
- A DataHub business-glossary export. It is a follow-up; see
  `devdocs/FIBO_ANALYSIS.md`.

## Decisions

**Value format: the IRI path after `/fibo/ontology/`.**

- This follows the rule "an id, never a URL" that applies to every mapping.
- The value is unambiguous, and it maps to the IRI by a fixed prefix.
- Rejected: FIBO prefixed names (`fibo-fbc-pas-caa:...`). They need a prefix
  table to resolve.
- Rejected: bare local names. FIBO keeps names unique only in released
  ontologies, so a local name can be ambiguous.
- `crosswalk` accepts either the full IRI or the path, because callers
  usually hold the IRI.

**Pinned term list instead of the whole ontology.**

- `data/vocabularies/fibo.json` holds only the mapped classes, about 12 KB.
- `fibo update` rebuilds it from a checkout and refuses mappings that FIBO
  lacks, as `coverage update` does for the rules.
- Rejected: committing all 2,767 classes. That is about 1 MB of data that the
  build would not use.
- Rejected: fetching FIBO during the build. That breaks offline and
  reproducible builds.
- The list quotes FIBO labels and definitions, so it carries FIBO's MIT
  licence notice in `source.license`.

**Validation levels.**

- An unknown class is an error.
- A pinned class that is not `Release` is a warning, because provisional
  content may change.
- A pinned class that no record uses is a warning, because the list is stale.

**Parser.**

- The scanner reads the RDF/XML files with the standard library XML parser.
  FIBO uses internal DTD entities, which that parser expands.
- A class is often declared in several files. The file that gives it an
  English `rdfs:label` is taken as its definition.
- This adds no RDF dependency.

**Publication.**

- FIBO IRIs join Wikidata and Schema.org in SKOS `exactMatch` and JSON-LD
  `sameAs`.
- The record page shows the FIBO label and abbreviations, linked to the IRI.
  The definition is shown as a tooltip.

## Risks / Trade-offs

- [FIBO renames or deprecates a class] → `fibo check --fibo-dir <newer
  checkout>` reports any difference from the pinned list. Updating the pin is
  a reviewed change.
- [A mapping is semantically too loose] → Map only when the FIBO definition
  and the registry record denote the same kind of value. The analysis lists
  the near-misses that were left out on purpose.
- [The FIBO RDF/XML layout changes] → The scanner relies only on
  `owl:Class`, `rdfs:label`, `skos:definition` and the maturity annotation, all
  of which the ontology guide requires.
