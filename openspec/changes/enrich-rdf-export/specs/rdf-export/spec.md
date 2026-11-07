## Purpose

This capability defines what the registry's RDF exports contain: the SKOS
concept scheme `/registry.ttl`, the per-record Turtle files and the registry
vocabulary.

## ADDED Requirements

### Requirement: Mapping links
Each datatype and pattern in `/registry.ttl` SHALL link to the concepts that its mappings name:

- `skos:exactMatch` for `wikidata` (`http://www.wikidata.org/entity/<id>`), `schema_org`, `fibo`, `bioregistry` (`https://bioregistry.io/registry/<prefix>`), `fhir` (the system URI as given) and `d3m`;
- `skos:broadMatch` for `dpv`, with `pd:` expanded to `https://w3id.org/dpv/pd#`.

A D3M URI under `http://schema.org/` SHALL be published as the `https://schema.org/` IRI. A concept SHALL NOT have two match links to the same IRI.

#### Scenario: Bioregistry and FHIR
- **WHEN** record `usssn` has `mappings.fhir: http://hl7.org/fhir/sid/us-ssn`
- **THEN** `/registry.ttl` contains `<…/datatype/usssn> skos:exactMatch <http://hl7.org/fhir/sid/us-ssn>`

#### Scenario: DPV category
- **WHEN** record `usssn` has `mappings.dpv: pd:OfficialID`
- **THEN** `/registry.ttl` contains `<…/datatype/usssn> skos:broadMatch <https://w3id.org/dpv/pd#OfficialID>` and no `exactMatch` to that IRI

### Requirement: Detection payload
Each concept SHALL carry the record's detection facts:

- `mcr:status` with the record status, and `mcr:isPII` as an `xsd:boolean`;
- `mcr:classification`, `mcr:regexp` and `mcr:checksum` when the record has them;
- `skos:example` for each example that is not marked `valid: false`;
- `dcterms:spatial` with the registry country page `/country/<CC>` for each country;
- `dcterms:language` with `http://id.loc.gov/vocabulary/iso639-1/<code>` for each language except `common`;
- `rdfs:seeAlso` for each link;
- `owl:deprecated true` when the status is `deprecated`, and `dcterms:isReplacedBy` for `replaced_by`.

The regular expression SHALL be published as the exact string of the record.

#### Scenario: Regular expression and examples
- **WHEN** record `email` has a regexp and positive examples
- **THEN** its concept has an `mcr:regexp` literal equal to the record's regexp, and a `skos:example` for each positive example

#### Scenario: Negative example
- **WHEN** an example is marked `valid: false`
- **THEN** it does not appear as a `skos:example`

### Requirement: Top concepts
Every concept with no `skos:broader` SHALL be a top concept of the scheme: `skos:topConceptOf` on the concept and `skos:hasTopConcept` on the scheme. No concept with a `skos:broader` SHALL be a top concept.

#### Scenario: Pattern is not a top concept
- **WHEN** pattern `uspassport` has `semantic_type: passport`
- **THEN** `uspassport` is not a top concept, and `passport` is one if it has no parent

### Requirement: Tools
Each tool SHALL be an `mcr:Tool` at `/tool/<id>` with an English `rdfs:label`, a `dcterms:description`, `foaf:homepage` when it has a website, and `mcr:supportedType` for each supported datatype. A supported type given as an alias SHALL link to the record that the alias resolves to.

#### Scenario: Tool support
- **WHEN** tool `presidio` lists `email` in `supported_types`
- **THEN** `/registry.ttl` contains `<…/tool/presidio> mcr:supportedType <…/datatype/email>`

### Requirement: Registry vocabulary
The site SHALL serve the registry vocabulary as an OWL ontology in Turtle at `/vocab.ttl`, with namespace `https://registry.apicrafter.io/vocab#`. Every `mcr:` term used by any export SHALL be declared there with an `rdfs:label` and an `rdfs:comment`. The site SHALL serve an HTML page at `/vocab` with an anchor for each term. Terms SHALL be added, never removed or renamed.

#### Scenario: Declared terms
- **WHEN** `/registry.ttl` uses a predicate or class in the `mcr:` namespace
- **THEN** `/vocab.ttl` declares it, and `/vocab` has an element with that term's name as its `id`

### Requirement: Per-record Turtle
The site SHALL serve `/datatype/<id>.ttl` for every datatype, pattern and alias. It SHALL parse on its own and contain the same triples about the concept as `/registry.ttl`. An alias file SHALL describe the record the alias resolves to. Each record page SHALL link to the file with `<link rel="alternate" type="text/turtle">`.

#### Scenario: Record file
- **WHEN** a client requests `/datatype/email.ttl`
- **THEN** it receives Turtle with the media type `text/turtle` that describes `<…/datatype/email>` as a `skos:Concept`

#### Scenario: Alias file
- **WHEN** a client requests `/datatype/ssn.ttl`
- **THEN** it receives the Turtle description of `<…/datatype/usssn>`
