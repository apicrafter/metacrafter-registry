# FIBO and the Metacrafter Registry

Analysis for issue [#13](https://github.com/apicrafter/metacrafter-registry/issues/13),
2026-11-04. It covers the three items of the issue:

1. How FIBO defines a business glossary.
2. Whether and how business glossaries and semantic types should be integrated.
3. What changes in the registry's own model ("ontology").

Sources:

- The FIBO repository, [edmcouncil/fibo](https://github.com/edmcouncil/fibo),
  `master` at commit `33a92cd34285d532c158da97bb42add089f135d3` (2026-10-27).
  This includes its `ONTOLOGY_GUIDE.md`. The numbers below come from parsing
  every `*.rdf` file of that commit, except `etc/` and `EXMP/`.
- The DataHub sample business glossary,
  `metadata-ingestion/examples/bootstrap_data/business_glossary.yml` in
  [datahub-project/datahub](https://github.com/datahub-project/datahub). The
  blog post linked from the issue builds on that format.

## 1. How FIBO defines a business glossary

**What it is.** FIBO is a family of OWL 2 DL ontologies for financial
contracts and the parties, instruments, markets and identifiers around them.
The EDM Council maintains it, and the OMG standardizes it. It is published
under the MIT licence. The commit above has 2,767 labelled classes in 11
domains:

| Domain | Classes | Domain | Classes |
|---|---|---|---|
| SEC (securities) | 591 | BE (business entities) | 187 |
| FBC (financial business and commerce) | 500 | LOAN | 180 |
| FND (foundations) | 423 | IND (indicators) | 120 |
| DER (derivatives) | 317 | MD (market data) | 103 |
| BP (business process) | 260 | CAE, ACTUS | 86 |

Every ontology file declares a maturity level:

- 1,977 classes are `Release`: stable, reasoner-checked and part of the
  standard.
- 757 classes are `Provisional`: work in progress.
- 33 classes are `Informative`: kept for reference.

**The glossary is generated from the ontology.** FIBO does not maintain the
glossary as a separate artifact. The guide makes the terminology "just as
important as the underlying logic". It follows ISO 704 and ISO 1087, and every
class, property and individual carries:

- **One label.** It is in American English, lower case except proper names,
  and unique across all of FIBO. Duplicated names are forbidden; a concept
  needed elsewhere is moved up the hierarchy, not copied.
- **One `skos:definition`.** It is written in genus-differentia form ("<parent
  class> that ..."). It must be able to replace the term in a sentence and must
  not be circular. A definition does not repeat what the logical restrictions
  already say, because the glossary is generated from both.
- **Optional extras:**
  - abbreviations (`cmns-av:abbreviation`, for example `IBAN`);
  - synonyms;
  - explanatory and usage notes;
  - examples;
  - the source of the definition (`cmns-av:adaptedFrom`, usually an ISO
    standard or a regulator's glossary).
- **A stable IRI** of the form
  `https://spec.edmcouncil.org/fibo/ontology/<domain>/<module>/<ontology>/<Name>`.
  It resolves to the FIBO Viewer in a browser and to RDF otherwise.

**Concepts, identifiers and code sets are separate classes.** This is the part
that matters most for the registry. Take currencies:

- `Currency` is the concept. The individual `USDollar` is a currency.
- `CurrencyIdentifier` is the code. The individual `USD` is a currency
  identifier. It `identifies` and `denotes` `USDollar`, and it is a member of
  the `ISO4217-CodeSet`.

Identifiers follow the same pattern:

- They specialize the OMG Commons classes `Identifier`, `StructuredIdentifier`
  and `RegisteredIdentifier`.
- Each points to what it identifies. For example, `LegalEntityIdentifier`
  identifies exactly one `LegalPerson`.
- Each points to the scheme that defines it (`isDefinedIn`
  `LegalEntityIdentifierScheme`).

**What FIBO does not have.** FIBO has no value-level detail:

- regular expressions;
- check-digit algorithms;
- examples of valid or invalid values.

Formats appear only in prose, as in "nine-character alphanumeric number". It is
a vocabulary of meaning, not of representation.

**What the registry can borrow:**

- Definitions in genus-differentia form ("identifier that ..."). They are a
  good template for the `doc` of draft records.
- Abbreviations kept apart from the name. The registry puts them into `name`
  today.
- The maturity levels, which correspond to the registry's
  `draft`/`stable`/`deprecated`.
- Citing the defining standard. The registry does this with `links`.

## 2. Business glossaries and semantic types

**They answer different questions.**

| | Registry semantic type | Business glossary term (FIBO, DataHub) |
|---|---|---|
| Describes | a value in a column: what it looks like and how to recognize it | a business concept: what it means and how it relates to other concepts |
| Typical content | regexp, check digit, examples, PII flag, country, detection rules | definition, synonyms, owners, policies, relations |
| Produced by | metacrafter, from field names and values | data stewards, by hand or from a standard |
| Example | `iban`: `^[A-Z]{2}\d{2}...$` with mod-97 | "international bank account identifier" |

**They overlap on identifiers and codes.** For these, a registry type and a
glossary term denote the same thing: an IBAN, an LEI, an ISIN. Outside that
overlap:

- Most FIBO classes are contracts, parties, events and processes. They have
  no column-level format and so no registry counterpart.
- Many registry types have no business-glossary meaning: UUIDs, IP addresses,
  file paths, chemical identifiers.

**The integration is a mapping, not a merge.** Do not import FIBO concepts as
datatypes. Do not turn the registry into a glossary. Link the two where they
coincide; the link then gives a pipeline:

```
column --metacrafter--> registry type --mappings.fibo--> FIBO class --> glossary term
 "acc_iban"              iban                             InternationalBankAccountIdentifier
```

What each party gets:

- metacrafter, or any tool built on the registry, can suggest a glossary term
  for each detected column without a glossary of its own.
- A glossary that uses FIBO can look up how to detect and validate the values
  of its terms.

The FIBO IRI is the natural join key. DataHub's sample glossary already
records FIBO-based terms as `term_source: EXTERNAL`, `source_ref: FIBO`,
`source_url: <FIBO IRI>`.

**Recommendations:**

1. Keep the registry a catalog of value types. Link it to FIBO through
   `mappings.fibo`, and map only exact concept matches, as for the Presidio,
   Google DLP and Purview crosswalks.
2. Publish the links where tools look for them:
   - SKOS `exactMatch` in `/registry.ttl`;
   - JSON-LD `sameAs` on the pages;
   - the record page;
   - the Markdown twin;
   - `crosswalk("fibo", ...)` in the Python API and MCP server.
3. Pin the FIBO version used to check the mappings, so that the build stays
   offline and reproducible.
4. Follow-ups (not in this change):
   - **DataHub glossary export.** Rebuild the DataHub business-glossary export
     as a build output with `source_url` set to the FIBO IRI where a mapping
     exists. `scripts/export.py` still reads the v1 format and does not run on
     v2 data.
   - **Glossary terms in metacrafter.** Let metacrafter report the mapped
     glossary term next to `datatype_url`.
   - **Missing records.** Add records for the FIBO identifiers that the
     registry lacks (section 4).
   - **LCC.** Map country and language codes to OMG LCC, which FIBO uses for
     them.

## 3. What changed in the registry

The change is described in `openspec/changes/add-fibo-mappings/`:

- A new mapping key, `mappings.fibo`. Its value is the FIBO class IRI without
  the `https://spec.edmcouncil.org/fibo/ontology/` prefix, for example
  `FBC/ProductsAndServices/ClientsAndAccounts/InternationalBankAccountIdentifier`.
- A committed term list, `data/vocabularies/fibo.json`. It holds the label,
  definition, abbreviations and maturity of each mapped class, and the FIBO
  commit they come from. `validate` fails on a mapping that is not in the
  list. The check matters because the FIBO server answers 200 for any path, so
  a link check cannot catch a typo.
- A command for contributors:

  ```bash
  metacrafter-registry fibo search <words> --fibo-dir <checkout>   # find a class
  metacrafter-registry fibo update --fibo-dir <checkout>           # pin the mapped classes
  metacrafter-registry fibo check --fibo-dir <checkout>            # compare with a newer FIBO
  ```

- Published outputs:
  - SKOS `exactMatch` and JSON-LD `sameAs` to the FIBO IRI;
  - a FIBO row on the record page, with the FIBO label and a link;
  - the IRI in the Markdown twin;
  - `crosswalk("fibo", <IRI or path>)`.

32 records map to 29 FIBO classes. All 29 classes are `Release`. (Since
2026-11-06, after the records of section 4 were added: 44 records, 41
classes.)

| Registry id | FIBO class | FIBO label |
|---|---|---|
| `iban` | `FBC/ProductsAndServices/ClientsAndAccounts/InternationalBankAccountIdentifier` | international bank account identifier (IBAN) |
| `bankaccount` | `FBC/ProductsAndServices/ClientsAndAccounts/BankAccountIdentifier` | bank account identifier |
| `bic`, `swiftcode` | `FBC/FunctionalEntities/FinancialServicesEntities/BusinessIdentifierCode` | business identifier code (BIC) |
| `aba`, `abaroutingnum` | `FBC/FunctionalEntities/NorthAmericanEntities/USRegulatoryAgencies/RoutingTransitNumber` | routing transit number (RTN) |
| `bankcard` | `LOAN/LoansSpecific/CardAccounts/PrimaryCardAccountNumber` | primary card account number (PAN) |
| `isin` | `SEC/Securities/SecuritiesIdentification/InternationalSecuritiesIdentificationNumber` | international securities identification number (ISIN) |
| `tickersymbol` | `SEC/Securities/SecuritiesIdentification/TickerSymbol` | ticker symbol |
| `cusip` | `SEC/Securities/SecuritiesIdentificationIndividuals/CommitteeOnUniformSecuritiesIdentificationProceduresNumber` | CUSIP number |
| `sedol` | `SEC/Securities/SecuritiesIdentificationIndividuals/StockExchangeDailyOfficialListCode` | SEDOL code |
| `figi` | `SEC/Securities/SecuritiesIdentificationIndividuals/FinancialInstrumentGlobalIdentifier` | financial instrument global identifier (FIGI) |
| `ric` | `SEC/Securities/SecuritiesIdentificationIndividuals/RefinitivInstrumentCode` | Refinitiv instrument code (RIC) |
| `cficode` | `SEC/Securities/SecuritiesClassification/FinancialInstrumentClassificationCode` | financial instrument classification code (CFI code) |
| `miccode` | `FBC/FunctionalEntities/Markets/MarketIdentifier` | market identifier (MIC) |
| `lei` | `BE/LegalEntities/LEIEntities/LegalEntityIdentifier` | legal entity identifier |
| `naicscode` | `FBC/FunctionalEntities/BusinessRegistries/NorthAmericanIndustryClassificationSystemCode` | NAICS code |
| `usein` | `FBC/FunctionalEntities/NorthAmericanEntities/USRegulatoryAgencies/EmployerIdentificationNumber` | employer identification number (EIN) |
| `vatin`, `euvat` | `BE/LegalEntities/FormalBusinessOrganizations/ValueAddedTaxIdentificationNumber` | value-added tax identification number (VATIN) |
| `cabn` | `FBC/FunctionalEntities/NorthAmericanEntities/CARegulatoryAgencies/BusinessNumber` | business number (BN) |
| `cagst` | `FBC/FunctionalEntities/NorthAmericanEntities/CARegulatoryAgencies/GoodsServicesTaxHarmonizedSalesTaxRegistrationNumber` | GST/HST registration number |
| `cacharity` | `FBC/FunctionalEntities/NorthAmericanEntities/CARegulatoryAgencies/RegisteredCharityProgramNumber` | registered charity program number |
| `currency` | `FND/Accounting/CurrencyAmount/Currency` | currency |
| `iso4217curcode` | `FND/Accounting/CurrencyAmount/CurrencyIdentifier` | currency identifier |
| `money` | `FND/Accounting/CurrencyAmount/MonetaryAmount` | monetary amount |
| `price` | `FND/Accounting/CurrencyAmount/Price` | price |
| `passport` | `FND/AgentsAndPeople/People/PassportNumber` | passport number |
| `phone` | `FND/Places/VirtualPlaces/TelephoneNumber` | telephone number |
| `email` | `FND/Places/VirtualPlaces/ElectronicMailAddress` | electronic mail address |
| `postindex` | `FND/Places/Addresses/Postcode` | postcode |
| `address` | `FND/Places/Addresses/PhysicalAddress` | physical address |

For `cagst` and `cacharity`, the FIBO definitions spell out the format: the
business number, `RT` or `RR`, and four digits. The registry regexps encode
the same format.

**Left unmapped on purpose:**

| Records | Reason |
|---|---|
| `uszipcode` | FIBO splits it into `ZIPCode` and `ZIPPlus4Code`; the registry type covers both |
| Country-specific IBANs and bank accounts (`chiban`, `plbankaccount`, ...) | narrower than the FIBO class, so not an exact match |
| `usdriverlic`, `cadriverlic` | FIBO has only a generic `DriversLicenseIdentifier`; the registry has no generic record |
| `usssn`, `usitin`, `usatin` | FIBO has only the generic US `TaxpayerIdentificationNumber` |
| `transaction_id` | FIBO's `TransactionIdentifier` is tied to an account; a payment transaction id is not |
| `duns`, `isicrev4`, country and language codes | not in FIBO; country codes live in OMG LCC |

## 4. FIBO identifiers without a registry record

These `Release` classes have a column-level format, but the registry has no
record for them:

| FIBO class | Standard |
|---|---|
| unique transaction identifier (UTI) | ISO 23897 |
| unique product identifier (UPI) | ISO 4914 |
| unique swap identifier (USI) | CFTC |
| digital token identifier (DTI) | ISO 24165 |
| merchant category code (MCC) | ISO 18245 |
| entity legal form identifier (ELF) | ISO 20275 |
| basic bank account identifier (BBAN) | ISO 13616 |
| CUSIP International Numbering System (CINS) number | |
| Euroclear Clearstream common code | |
| RSSD ID | Federal Reserve |
| FDIC certificate number | |
| issuer identification number (IIN) | ISO/IEC 7812 |
| ZIP+4 code | |

The provisional `UniversalLoanIdentifier` (HMDA) is a candidate too.

Each new record needs its format, examples and check digit verified against
the defining standard; the FIBO definition is not enough. Add them as `draft`
records with a `mappings.fibo` entry.

**Done on 2026-11-06** (task 6.2 of `add-fibo-mappings`): `dti` and
`merchant_category_code` existed and gained the mapping. New draft records:
`unique_transaction_identifier`, `unique_product_identifier`,
`us_unique_swap_identifier`, `elf_code`, `bban`, `cins`, `common_code`,
`us_rssd_id`, `us_fdic_certificate`, `iin` and `us_zip_plus4`. `elf_code` has
no FIBO mapping: FIBO's `EntityLegalForm` is the legal form (a classifier),
not its code. No check digit is enforced: UTI and USI have none, the UPI
check character (ISO 4914 Annex C) and the CINS check digit (the CUSIP
algorithm) have no implementation in `checksums.py` yet.
