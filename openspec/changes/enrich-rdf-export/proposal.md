## Why

Issue #49 asked to move the registry into a graph database with a formal
RDF/OWL ontology. It was closed as superseded: the `modernize-registry-platform`
design keeps YAML in git as the source of truth and publishes a SKOS export,
`/registry.ttl`, instead.

A review of that export, recorded in the closing comment of #49, found that it
carries only the taxonomy:

- `skos:exactMatch` covers 3 of the 18 mapping kinds (`wikidata`,
  `schema_org`, `fibo`). The `bioregistry`, `fhir`, `d3m` and `dpv` mappings
  name IRIs but are not exported.
- The detection payload is missing: `regexp`, `examples`, `is_pii`,
  `classification`, `checksum`, `country`, `langs`, `links`, `status` and
  `replaced_by`. Tools are missing too.
- The concept scheme declares no top concepts, although 1,464 concepts have no
  `broader`.
- There is no RDF for a single record. GitHub Pages cannot negotiate content
  types, so `/datatype/<id>` always returns HTML.

A triple store that loads `/registry.ttl` today can browse the hierarchy, but
cannot find which concept a value matches or which tools detect it.

## What Changes

- More mapping links in `/registry.ttl`:
  - `skos:exactMatch` to Bioregistry resources, FHIR identifier systems and
    D3M semantic types;
  - `skos:broadMatch` to DPV personal-data categories. They are categories:
    `pd:OfficialID` alone covers 158 records.
- The detection payload as RDF:
  - standard terms where one fits: `skos:example`, `rdfs:seeAlso`,
    `dcterms:spatial`, `dcterms:language`, `owl:deprecated`,
    `dcterms:isReplacedBy`;
  - a small registry vocabulary for the rest: regular expression, check-digit
    algorithm, PII flag, classification, status, tools and the types they
    support.
- The vocabulary is published as an OWL ontology at `/vocab.ttl`, with a
  human-readable page at `/vocab`.
- Top concepts: `skos:hasTopConcept` and `skos:topConceptOf` for every concept
  that has no `broader`.
- Tools in `/registry.ttl`, linked to the concepts they support.
- One Turtle file per record, `/datatype/<id>.ttl`, also for aliases. Record
  pages link to it with `<link rel="alternate" type="text/turtle">`.

The existing triples are kept, so nothing is **BREAKING**. The URL contract
only gains `/datatype/<id>.ttl`, `/vocab` and `/vocab.ttl`.

## Capabilities

### New Capabilities

- `rdf-export`: the content of the RDF exports, the registry vocabulary and
  the per-record Turtle files.

### Modified Capabilities

None. The linked-data requirement of `modernize-registry-platform` is not
archived yet. This change adds to it without changing its behaviour.

## Impact

- **Code:** `agents.py` (Turtle emitters and the vocabulary), `build.py`
  (new files, manifest), `contract.py`; templates `datatype.html`,
  `about.html` and a new `vocab.html`.
- **Outputs:** `/registry.ttl` grows; new `/vocab.ttl`, `/vocab` and
  `/datatype/<id>.ttl`. The release attaches `vocab.ttl`.
- **Data and schema:** none. No record changes.
- **Dependencies and network:** none. The Turtle is still written without a
  runtime dependency; tests parse it with `rdflib`.
