# Microsoft Common Data Model (CDM): review (2026-11-04)

Issue: [apicrafter/metacrafter-registry#14](https://github.com/apicrafter/metacrafter-registry/issues/14).

The issue asks two things: review the Common Data Model, and consider
integrating CDM business terms into the registry's semantic types.

Source reviewed: [microsoft/CDM](https://github.com/microsoft/CDM) at commit
`dd21d715e05ebf740a11356c80b5c3b4c38a89c2`, which is also the last push to the
repository (2025-01-22). The schema documents are licensed CC-BY-4.0. All
numbers below were computed from that commit.

## Summary

- CDM models business records: entities such as Account, Contact and Lead, and
  their attributes. The registry models values: what one column means. The two
  meet at one layer, CDM's **meaning traits** (`means.*`). The data type of a
  CDM attribute carries these traits, for example `email` carries
  `means.identity.service.email`.
- **Done in this change:** a new crosswalk key, `mappings.cdm`. It holds CDM
  trait names. 44 traits are mapped to 43 registry records, exact concept
  matches only. `crosswalk("cdm", "means.location.postalCode")` returns
  `postindex`.
- **Not done, on purpose:** importing CDM entities (Account, Lead,
  Opportunity, ...) as registry records. They are business objects, not value
  types. They have no format, no regexp and no examples, and a scanner cannot
  detect them from values. They belong in a business glossary, such as the
  DataHub glossary that the issue mentions. Such a glossary can link its
  attribute terms to registry ids through this crosswalk.
- CDM's own entities apply semantic data types loosely. Do not treat a CDM
  data type as ground truth for a column's content. Metacrafter detection is
  still useful on top of it. See [Data quality in CDM](#data-quality-in-cdm).

## What CDM is

CDM is a library of JSON documents (`*.cdm.json`) and an SDK
(`objectModel/`, for C#, Java, Python and TypeScript) that resolves them. It is
the schema layer behind Dataverse, Dynamics 365, Power Platform dataflows and
the "CDM folders" format in Azure Data Lake.

`schemaDocuments/` has two parts:

1. **Foundations.** `primitives.cdm.json`, `foundations.cdm.json`,
   `meanings.cdm.json` and nine `meanings.<group>.cdm.json` files. They define
   143 data types and about 350 `means.*` traits, in these groups:
   - identity (names, email, phone, IP addresses, ticker symbol, SKU)
   - location (address parts, city, country, latitude, postal code, time zone)
   - demographics (age, birth date, gender, marital status)
   - calendar (year, quarter, month, day of week)
   - measurement (SI units, currency, dates)
   - concepts (`means.idea.*`, which names business ideas such as account or
     campaign)
   - privacy (data categories and allowed uses)
2. **Entities.** About 6,450 entity documents (latest versions only), in these
   folders:
   - `core/`: 5,478, mostly `operationsCommon` (Dynamics 365 Finance and
     Operations) and `applicationCommon` (CRM: Account, Contact, Lead, ...)
   - `Healthcare/`: 489
   - `Marketing/`: 130
   - `CustomerInsightsJourneys/`: 102
   - `FinancialServices/`: 100
   - `Sustainability/`: 91
   - `Retail/`: 57

An attribute has a name, a data type and traits. For example, `Contact` has
the attribute `EMailAddress1` with the data type `email`. The data type
`email` extends `string` and carries the trait `means.identity.service.email`.
A trait is inherited: `dateTime` extends `date`, so it also carries
`means.measurement.date`.

## Why the crosswalk uses trait names

The `cdm` mapping holds trait names, such as `means.identity.service.email`,
and not data type names, such as `email`:

- **Trait names are unique.** Data type names are not: `day` and `year` are
  each defined twice. One definition is a deprecated calendar part in
  `meanings.calendar`. The other is a duration unit in `meanings.measurement`.
- **Traits are the semantic layer.** A data type is a carrier for one meaning
  trait, plus format traits. Several useful meanings have no data type at all,
  for example `means.identity.SKU`, `means.identity.service.twitter`,
  `means.location.continent` and `means.calendar.dayOfWeek`.
- **Resolved schemas list traits.** Resolved entity documents, which the SDK
  produces, list the traits of every attribute. A consumer can read them
  without knowing the data type hierarchy.

To go from a data type to a registry record, take the data type's `means.*`
trait from the table below. An attribute can carry several mapped traits. For
example, an `entityId` key carries `means.identity.entityId` (`id`) and
`is.dataFormat.guid` (`uuid`). The `means.*` trait gives the meaning of the
value and the `is.dataFormat.*` trait gives its format. Both are valid labels.

## Mapping (in `mappings.cdm`)

Only exact concept matches are mapped. A CDM trait maps to at most one
registry record (a test checks this). The data type column is the CDM data
type that carries the trait, if there is one.

| CDM trait | CDM data type | Registry id |
|---|---|---|
| `means.identity.service.email` | `email` | `email` |
| `means.identity.service.phone` | `phone` | `phone` |
| `means.identity.service.twitter` | | `twitter_username` |
| `means.identity.IP4Address` | `IP4Address` | `ipv4` |
| `means.identity.IP6Address` | `IP6Address` | `ipv6` |
| `means.reference.URL` | `url` | `url` |
| `means.reference.language.tag` | `languageTag` | `languagetag` |
| `means.reference.description` | | `description` |
| `means.identity.name` | `name` | `name` |
| `means.identity.company.name` | `companyName` | `orgname` |
| `means.identity.person.firstName` | `firstName` | `person_firstname` |
| `means.identity.person.middleName` | `middleName` | `person_midname` |
| `means.identity.person.lastName` | `lastName` | `person_surname` |
| `means.identity.person.fullName` | `fullName` | `person_fullname` |
| `means.identity.tickerSymbol` | `tickerSymbol` | `tickersymbol` |
| `means.identity.SKU` | | `sku` |
| `means.identity.entityId` | `entityId` | `id` |
| `is.dataFormat.guid` | `guid` | `uuid` |
| `means.userId` | `userId` | `userid` |
| `means.fileName` | `fileName` | `filename` |
| `means.location.address` | `addressLine` | `address` |
| `means.location.city` | `city` | `city` |
| `means.location.country` | `country` | `country` |
| `means.location.continent` | | `continent` |
| `means.location.postalCode` | `postalCode` | `postindex` |
| `means.location.latitude` | `latitude` | `latitude` |
| `means.location.longitude` | `longitude` | `longitude` |
| `means.location.timezone` | `timezone` | `timezone` |
| `means.demographic.age` | `age` | `age` |
| `means.demographic.birthDate` | `birthDate` | `birthday` |
| `means.demographic.gender` | `gender` | `gender` |
| `means.demographic.income` | | `income` |
| `means.measurement.currency` | `currency`, `baseCurrency` | `money` |
| `means.measurement.currency.cost` | | `cost` |
| `means.measurement.currency.price` | | `price` |
| `means.measurement.currencyCode`, `means.measurement.currency.iSOCode` | `currencyCode` | `iso4217curcode` |
| `means.measurement.color` | `colorName` | `color` |
| `means.measurement.date` | `date` (inherited by `dateTime`) | `date` |
| `means.calendar.year` | `year` (calendar, deprecated) | `year` |
| `means.calendar.quarterOfYear` | | `quarter` |
| `means.calendar.monthOfYear` | | `month` |
| `means.calendar.dayOfMonth` | | `dayofmonth` |
| `means.calendar.dayOfWeek` | | `dayofweek` |

Notes on the mapping:

- **Address.** CDM gives `means.location.address` to the full address and,
  through `addressLine`, to each address line (`address1Line1`, ...). The
  registry's `address` is the full address. The more specific traits
  `means.location.address.street.line1..3` are not mapped.
- **Measurement units.** The `year`, `day`, `minute` and `hour` data types in
  `meanings.measurement` are durations, not calendar values. They are not
  mapped.
- **Currency vs money.** The registry's `currency` record is the currency
  itself. CDM's `currency` data type is an amount of money, so it maps to
  `money`. The currency code maps to `iso4217curcode`.

## CDM meanings with no registry equivalent

The registry has no record with the same meaning for these traits. They were
left unmapped rather than mapped to something broader.

| CDM trait | Closest registry records | Note |
|---|---|---|
| `means.location.stateOrProvince`, `means.location.province` | `usstate`, `caprovince`, `province` (CN), `state` (IN), `rusregion` | Only country-specific records exist. A generic parent is missing. |
| `means.location.county` | `uscounty` | Same: only a US record exists. |
| `means.location.region` | `wbregion`, `unm49` | CDM gives no definition; the registry records are specific region lists. |
| `means.location.address.street` (and `line1..3`) | `street` | CDM's street lines include house numbers. The registry's `street` is a street name. |
| `means.location.point` | `geopoint` | CDM gives no definition or format. |
| `means.identity.service.phone.cell`, `.fax` | `phone`, `msisdn` | No mobile or fax phone record. |
| `means.identity.governmentID` | `passport`, national ids | No generic government id. |
| `means.identity.person.prefix`, `.suffix` | | No salutation or name suffix record. |
| `means.identity.barCode` | `ean`, `upc`, `gtin` | The registry records are specific symbologies. |
| `means.identity.title` | `jobtitle`, `dctitle` | Ambiguous in CDM. |
| `means.identity.service.facebook` | | No Facebook account record. |
| `means.demographic.maritalStatus`, `.ethnicity`, `.education` | | No records. |
| `means.reference.URI` | `url` | A URI is broader than a URL. |
| `means.reference.language` | `dclanguage` | No generic language record. |
| `means.content.text.JSON`, `.XML`, `.HTML` | | No content-format records. |
| `means.measurement.time` | `time`, `datetime` | `dateTime` also carries this trait, so it does not mean "time of day". |

`means.idea.*` (81 traits, such as `means.idea.account`), the `privacy.*`
traits and the SI unit traits are out of scope. They describe business
objects, data-handling policies and units, not value types.

## How much of CDM this covers

We sampled the 48 core CRM entities: the 43 entities of
`core/applicationCommon/`, plus Lead, Opportunity, Competitor, Invoice and
Quote from `crmCommon`. They have 2,294 attributes. By data type:

| Share | Attributes | What |
|---|---|---|
| 17% | 388 | A business data type that now maps to a registry record (name, phone, email, URL, address parts, money, person names, ticker symbol). |
| 21% | 478 | `entityId` or `guid` keys, mapped to `id` and `uuid`. |
| 6% | 147 | `dateTime`, mapped to `date` through the inherited trait. |
| 1% | 31 | A semantic data type with no registry equivalent: `stateOrProvince` (13), `county` (9), `language` (6), `governmentId` (2), `phoneFax` (1). |
| 55% | 1,250 | Plain types: `string`, `boolean`, `integer`, `decimal`, option sets (`listLookup`), display text. |

Most of the semantic content of CDM's CRM entities is therefore covered. The
plain `string` attributes are where value-based detection adds the most. For
example, `Account.SIC` is a Standard Industrial Classification code typed as
a plain string.

## Data quality in CDM

The sample shows that CDM's own entities do not apply data types
consistently:

- `Account.timeSpentByMeOnEmailAndMeetings` has the `email` data type.
- `Competitor.stockExchange` has the `tickerSymbol` data type.
- `Address.UTCOffset` has the `timezone` data type. The value is an offset,
  so the registry's `utctimezoneoffset` is the better label.
- `Currency.ISOCurrencyCode` is a plain `string`, not a `currencyCode`.

So the crosswalk gives the type that CDM declares, and that type can be
wrong. Metacrafter's value-based detection is a useful check on top of it.

## Recommendations and follow-ups

1. **Keep CDM entities out of the registry.** "Account" or "Opportunity" is
   not a semantic data type. If a business glossary is needed, build it in a
   catalog (DataHub, OpenMetadata) from the CDM entity documents. Link its
   attribute-level terms to registry ids through `crosswalk("cdm", ...)`.
2. **Add generic parent records for subdivisions:** a first-level
   administrative subdivision (state or province) and a second-level one
   (county). The country-specific records (`usstate`, `caprovince`,
   `uscounty`, ...) would become their children, and the CDM traits
   `means.location.stateOrProvince` and `means.location.county` would map to
   them. This needs a reviewed description, so it is left to a separate
   change.
3. **Field-name hints for metacrafter-rules.** Dataverse exports use CDM
   attribute names such as `emailaddress1`, `telephone1`,
   `address1_postalcode` and `address1_latitude`. Adding these names to the
   field rules of the mapped types in metacrafter-rules would improve
   detection on Dynamics 365 and Dataverse data. That work belongs in the
   metacrafter-rules repository.
4. **Re-check on CDM updates.** The repository has been quiet since January
   2025. If the foundations change, re-run the comparison against the
   `meanings.*.cdm.json` files of the new commit.
