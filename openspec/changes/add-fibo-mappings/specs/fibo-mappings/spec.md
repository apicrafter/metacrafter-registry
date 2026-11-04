## Purpose

Links registry datatypes to classes of FIBO, the Financial Industry Business
Ontology. Business glossaries built on FIBO can then find how to detect a term's
values, and metacrafter results can be tied to glossary terms.

## ADDED Requirements

### Requirement: FIBO mapping key
A record MAY declare `mappings.fibo` as one FIBO class or a list of FIBO classes. A class SHALL be written as its IRI without the prefix `https://spec.edmcouncil.org/fibo/ontology/` and SHALL match `^[A-Z]+/([A-Za-z0-9-]+/)+[A-Za-z0-9]+$`.

#### Scenario: Class path
- **WHEN** record `iban` has `mappings: {fibo: FBC/ProductsAndServices/ClientsAndAccounts/InternationalBankAccountIdentifier}` and that class is pinned
- **THEN** validation passes

#### Scenario: Full IRI given
- **WHEN** a record has `mappings.fibo` set to `https://spec.edmcouncil.org/fibo/ontology/FBC/ProductsAndServices/ClientsAndAccounts/InternationalBankAccountIdentifier`
- **THEN** schema validation fails for `mappings.fibo`

### Requirement: Pinned FIBO term list
The repository SHALL contain `data/vocabularies/fibo.json`. The file SHALL hold the FIBO commit it was read from, FIBO's licence notice, and, for every mapped class, its English label and its maturity level. It SHALL also hold the definition and abbreviations where FIBO gives them.

Validation SHALL fail when a `mappings.fibo` class is not in the file. Validation SHALL warn when a mapped class is not at maturity `Release`, and when the file holds a class that no record maps to.

#### Scenario: Misspelled class
- **WHEN** a record maps to `FND/Places/VirtualPlaces/ElectronicMailAdress` and the file has no such class
- **THEN** validation fails and names the record, the class, and the command that updates the file

#### Scenario: Update from a FIBO checkout
- **WHEN** a contributor runs `metacrafter-registry fibo update --fibo-dir <checkout>`
- **THEN** the file is rewritten with exactly the mapped classes, read from that checkout, and the command fails without writing if a mapped class is not a labelled class there

#### Scenario: Newer FIBO release
- **WHEN** `metacrafter-registry fibo check --fibo-dir <checkout>` runs against a FIBO commit whose labels or definitions of mapped classes differ from the file
- **THEN** the command exits non-zero

### Requirement: FIBO links in published outputs
For every class in a record's `mappings.fibo`, the build SHALL publish the class IRI (the prefix followed by the path):

- as a `skos:exactMatch` of the record's concept in `/registry.ttl`
- in the JSON-LD `sameAs` of the record page
- as a link labelled with the FIBO label on the record page
- in the Markdown twin

`/api/v1/` records SHALL carry `mappings.fibo` unchanged.

#### Scenario: SKOS export
- **WHEN** record `iban` maps to `FBC/ProductsAndServices/ClientsAndAccounts/InternationalBankAccountIdentifier`
- **THEN** `/registry.ttl` contains `<…/datatype/iban> skos:exactMatch <https://spec.edmcouncil.org/fibo/ontology/FBC/ProductsAndServices/ClientsAndAccounts/InternationalBankAccountIdentifier>`

### Requirement: FIBO crosswalk
`crosswalk("fibo", value)` in the Python API and in the MCP server SHALL return the records mapped to the class. `value` SHALL be accepted as either the class path or its full IRI.

#### Scenario: Lookup by IRI
- **WHEN** a client calls `crosswalk("fibo", "https://spec.edmcouncil.org/fibo/ontology/FBC/FunctionalEntities/FinancialServicesEntities/BusinessIdentifierCode")`
- **THEN** it receives the records `bic` and `swiftcode`
