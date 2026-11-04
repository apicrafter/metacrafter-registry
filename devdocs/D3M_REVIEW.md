# D3M Metadata semantic types: review (2026-11-04)

Issue: [apicrafter/metacrafter-registry#45](https://github.com/apicrafter/metacrafter-registry/issues/45).

The issue asks to add the data types of the D3M Metadata registry,
<https://metadata.datadrivendiscovery.org/>, to the registry.

Source reviewed: the list of semantic types in
`d3m/metadata/schemas/v0/definitions.json` (`definitions.semantic_types`) of
[datadrivendiscovery/d3m](https://gitlab.com/datadrivendiscovery/d3m) at
commit `244d5529c3ca856281edc6abc0884d8ccb8071d9`. This is the head of the
`devel` branch (2022-05-05). The repository is licensed Apache-2.0. The pages
under `https://metadata.datadrivendiscovery.org/types/` are generated from this
file by `site/build_site_types.py`, and they match it. All numbers below were
computed from that commit.

## Summary

- D3M defines **90 semantic types**. 72 are D3M URIs
  (`https://metadata.datadrivendiscovery.org/types/<Name>`). 18 are
  Schema.org URIs that D3M reuses, written with `http://`
  (`http://schema.org/email`).
- In D3M metadata, a column lists several semantic types at once: a
  structural type (`http://schema.org/Integer`), one or more roles
  (`.../types/Attribute`, `.../types/PrimaryKey`) and sometimes a value type
  (`http://schema.org/email`). Only the value types say what a value means.
  They are 12 of the 90 types.
- **Done in this change:**
  - The crosswalk key `mappings.d3m` now holds D3M semantic type URIs, as D3M
    metadata writes them. The schema rejects other values, such as a bare name
    like `FileName`.
  - 13 D3M types are mapped to 12 registry records, exact concept matches
    only. `crosswalk("d3m", "http://schema.org/email")` returns `email`. The
    lookup also accepts `https://schema.org/...` and a bare type name, such
    as `FileName`.
  - One new record, the pattern `nanpphone` (North American phone number),
    for D3M's `AmericanPhoneNumber`. The registry had no record for it. It is
    a draft.
- **Not done, on purpose:** importing the other 77 types as registry records.
  They are column roles, dataset structure, hyper-parameters, media objects,
  data-state markers and storage types, not value types. See
  [What D3M types are](#what-d3m-types-are).

## What D3M types are

D3M (Data-Driven Discovery of Models) was a DARPA program on automated
machine learning. Its core package, `d3m`, describes datasets, pipelines and
primitives with JSON metadata. The semantic types tell an AutoML system how to
use a column. The 90 types fall into these groups:

| Group | Types | Examples | Registry records? |
|---|---|---|---|
| Column roles (`ColumnRole` and its descendants) | 41 | `Attribute`, `Target`, `PrimaryKey`, `GroupingKey`, `EdgeSource`, `Score`, `Time`, `Location`, `BoundingPolygon` | No. A role says how a column is used, not what it holds. A `PrimaryKey` column can hold emails or tax numbers. |
| Hyper-parameter types | 7 | `HyperParameter`, `TuningParameter`, `ControlParameter` | No. They describe primitive parameters, not data. |
| Dataset structure and resources | 11 | `Table`, `Timeseries`, `Graph`, `EdgeList`, `DatasetResource`, `TabularColumn`, `FilesCollection` | No. They describe containers, not values. |
| Media objects | 4 | `http://schema.org/ImageObject`, `.../VideoObject`, `.../AudioObject`, `Speech` | No. The value is a file, not a text value a scanner can match. |
| Data-state markers | 3 | `MissingData`, `InvalidData`, `UnknownType` | No. |
| Statistical and tokenization hints | 4 | `CategoricalData`, `OrdinalData`, `TokenizableByPunctuation` | No. `CategoricalData` matches the registry's `classification: categorical` field, not a record. |
| Structural (storage) types | 8 | `http://schema.org/Text`, `.../Integer`, `.../Float`, `.../Boolean`, `.../DateTime`, `FloatVector`, `JSON`, `GeoJSON` | `Boolean` and `DateTime` match records. The others are storage types. |
| Value types | 12 | `FileName`, `AmericanPhoneNumber`, `http://schema.org/email`, `.../City`, `.../postalCode` | Yes: 11 are mapped, `State` has no matching record. |

## Mapping (in `mappings.d3m`)

Only exact concept matches are mapped. A D3M type maps to at most one registry
record (a test checks this). The description column is D3M's own definition,
shortened.

| D3M semantic type | D3M definition | Registry id |
|---|---|---|
| `http://schema.org/email` | an email address | `email` |
| `http://schema.org/URL` | a URL | `url` |
| `http://schema.org/address` | an address, broadly defined | `address` |
| `http://schema.org/City` | a city, US or foreign | `city` |
| `http://schema.org/Country` | a country | `country` |
| `http://schema.org/addressCountry` | a country code | `country` |
| `http://schema.org/postalCode` | a US postal code | `uszipcode` |
| `http://schema.org/latitude` | a latitude | `latitude` |
| `http://schema.org/longitude` | a longitude | `longitude` |
| `http://schema.org/Boolean` | a boolean | `boolean` |
| `http://schema.org/DateTime` | a timestamp | `datetime` |
| `https://metadata.datadrivendiscovery.org/types/FileName` | a filename | `filename` |
| `https://metadata.datadrivendiscovery.org/types/AmericanPhoneNumber` | an American style phone number, such as `(310)822-1511` or `1-310-822-1511` | `nanpphone` (new) |

Notes on the mapping:

- **Postal code.** D3M reuses Schema.org's `postalCode`, but defines it as a
  US postal code. The mapping follows D3M's definition, so the type maps to
  `uszipcode` and not to `postindex`. `uszipcode` is a pattern of
  `postindex`, so a consumer that wants the generic type can follow
  `semantic_type`.
- **Country code.** D3M's `addressCountry` is "a country code" and does not
  say which code system it uses. The registry's `country` record is defined as
  "country code or name". The code systems are its patterns
  (`countrycode_alpha2`, `countrycode_alpha3`, `countrycode_num`). So both
  `Country` and `addressCountry` map to `country`.
- **Phone number.** `nanpphone` is a pattern of `phone`. It inherits the
  categories and `is_pii: true`. Its regexp follows the format in Wikipedia's
  North American Numbering Plan article: area code and central office code
  start with 2-9, with an optional leading `1` or `+1`. The regexp matches
  both of D3M's examples. Its `country` lists only US and CA, because
  `data/countries.yaml` does not list the other NANP members (Caribbean and
  Pacific territories such as JM, BS or PR). The record is a draft until
  someone reviews it.
- **Links.** `filename` already linked to its D3M page. `nanpphone` links to
  the `AmericanPhoneNumber` page. The other mapped types are Schema.org URIs,
  so they get no D3M link.

## D3M types with no registry equivalent

| D3M semantic type | Closest registry records | Note |
|---|---|---|
| `http://schema.org/State` ("a state, could be US or foreign") | `usstate`, `mxstate`, `caprovince`, `province` (CN), `state` (IN), `rusregion` | Only country-specific records exist. See recommendation 1. |
| `http://schema.org/Integer`, `.../Float` | `numeric` | `numeric` ("any integer or float number") is broader. |
| `http://schema.org/Text` | | A storage type. Any text column has it. |
| `JSON`, `GeoJSON` | | No records. See recommendation 2. |
| `FloatVector` | | A storage type for embeddings and features. |
| `BoundingPolygon`, `LocationPolygon` | `geopoint` | Roles in D3M. The registry has no geometry or polygon record. |
| `Time` (role) | `datetime`, `date`, `time` | A role: the column is the time axis. The values can be dates, timestamps or integers. |
| `PrimaryKey`, `UniqueKey` (roles) | `id` | Roles: any identifier can be a key. The registry's `classification: identifier` is the closest field. |

## Recommendations and follow-ups

1. **Make a generic first-level subdivision record.** D3M's `State` and CDM's
   `means.location.stateOrProvince` (see `devdocs/CDM_REVIEW.md`) both need a
   generic "state or province" record. metacrafter-rules already uses the
   rule key `state` for the states of AU, BR, IN and MX, and in its
   Portuguese-language rules (`pt/pt_geo.yaml`). In the registry,
   however, the id `state` is "Indian state by known name" (IN). Two options:
   - Broaden `state` to the generic meaning, and add an Indian pattern of it.
   - Add a new generic record and make `state` and the other country records
     its children.

   Either option changes the meaning of a published id or adds a near
   duplicate, so it needs a maintainer decision. It is not done here.
2. **JSON and GeoJSON.** They could become records, for example `json` and
   `geojson` (RFC 7946), in a `files` or `geo` category. Python `re` cannot
   match JSON, so these records would have no regexp, and detection would need
   a parser. Add them only if metacrafter gets such a detector.
3. **NANP countries.** If the registry should list every NANP member in
   `nanpphone.country`, first add the missing territories to
   `data/countries.yaml`.
4. **Re-check is unlikely to be needed.** The D3M program has ended. The
   repository has had no new commits on `devel` since May 2022.
