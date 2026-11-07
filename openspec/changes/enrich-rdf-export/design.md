## Context

`/registry.ttl` is written by `agents.skos_turtle` as plain text, without a
runtime RDF dependency. It holds one `skos:Concept` per datatype and pattern,
one `skos:Collection` per category, and `exactMatch` links for the Wikidata,
Schema.org and FIBO mappings. The site is static (GitHub Pages), so every RDF
resource must be a file, and an IRI resolves only if a file or page exists at
that path.

## Goals / Non-Goals

**Goals:**

- Everything a record says about recognizing a value is available as RDF.
- Every mapping that names an IRI is linked, with a match strength that is
  true for all records that use it.
- Every IRI the export mints resolves on the site.

**Non-Goals:**

- A graph database or a SPARQL endpoint (#49, closed).
- OWL axioms on datatypes, or reasoning. The vocabulary is declared in OWL so
  that tools can read it, but datatypes stay SKOS concepts.
- SHACL shapes. See "Regular expressions" below.
- Content negotiation on `/datatype/<id>`. GitHub Pages cannot do it; the
  HTML page links to the Turtle file instead.

## Decisions

**Wikidata and Schema.org properties keep `skos:exactMatch`.**

- 465 of the 469 Wikidata mappings are properties, and all Schema.org mappings
  are properties. The review in #49 suggested `closeMatch` for them.
- Most of these are external-identifier properties: the property denotes the
  identifier scheme that the registry record describes. Bioregistry, the
  closest peer registry, links its prefixes to such properties with
  `skos:exactMatch` (for example `chebi` to `wikidata:P683`).
- Changing the predicate would also break queries written against the current
  export. Rejected.

**DPV links use `skos:broadMatch`.**

- The `dpv` mappings name 27 personal-data categories for 259 records:
  `pd:OfficialID` alone covers 158. A category is broader than a value format,
  so `exactMatch` would be false for most records.
- `pd:X` expands to `https://w3id.org/dpv/pd#X`.

**Other IRIs.**

- Bioregistry: `https://bioregistry.io/registry/<prefix>`, the IRI Bioregistry
  itself uses for a resource. `exactMatch`: a mapping is made only when both
  sides denote the same identifier.
- FHIR: the `Identifier.system` URI as is, including `urn:` URIs. `exactMatch`,
  for the same reason. These URIs need not resolve; they are identifiers.
- D3M: `http://schema.org/` types are rewritten to `https://schema.org/` and
  deduplicated with the Schema.org links. Other D3M URIs are used as is.
- `presidio`, `google_dlp`, `purview`, `stdnum` and the other mapping kinds
  hold labels or codes, not IRIs, and stay out of the RDF.

**A small registry vocabulary.**

- Namespace `https://registry.apicrafter.io/vocab#`, prefix `mcr:`.
  `/vocab.ttl` holds its OWL declaration and `/vocab` is an HTML page with an
  anchor per term, so every term IRI resolves.
- Terms: `mcr:regexp`, `mcr:checksum`, `mcr:isPII`, `mcr:classification`,
  `mcr:status`, `mcr:Tool` and `mcr:supportedType`.
- Standard terms are used wherever one fits:
  - positive examples: `skos:example`;
  - links: `rdfs:seeAlso`;
  - countries: `dcterms:spatial`, pointing at the registry's own country page
    (`/country/<CC>`);
  - languages: `dcterms:language`, pointing at the Library of Congress ISO
    639-1 IRI (`http://id.loc.gov/vocabulary/iso639-1/<code>`); `common` is
    not a language and is left out;
  - deprecation: `owl:deprecated true` and `dcterms:isReplacedBy`.
- Negative examples are not exported. They are test data for the regexp, not
  facts about the concept.

**Regular expressions are plain literals, not SHACL or XSD patterns.**

- Registry regexps use Python `re` syntax and are anchored with `^…$`.
  `sh:pattern` uses XPath regular expressions and `xsd:pattern` uses XML
  Schema ones. Their syntax differs (lookarounds, anchors, inline flags), so
  publishing a Python pattern under those predicates would claim a
  compatibility that does not hold.
- `mcr:regexp` documents its syntax instead.

**Aliases stay `skos:altLabel`.**

- The review noted that aliases are former ids without a language tag. Most
  are working names (`guid`, `md5`, `ssn`, `eui48`), and all of them still
  resolve as ids. A plain literal is valid SKOS, so the triples stay as they
  are.

**Per-record Turtle.**

- `/datatype/<id>.ttl` holds the prefixes and the record's concept
  description, the same triples as in `/registry.ttl`.
- An alias gets a copy of its record's file, like the legacy
  `/datatype/<alias>.json`.

## Risks / Trade-offs

- `/registry.ttl` grows from 1.4 MB to about 2.5 MB. It is still small for a
  triple store and for the release asset.
- `mcr:` terms are a new public vocabulary. Terms are added, never removed or
  renamed, as for the JSON shapes.
