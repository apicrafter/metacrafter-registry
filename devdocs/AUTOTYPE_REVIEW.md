# AutoType benchmark semantic types: review (2026-11-04)

Issue: [apicrafter/metacrafter-registry#39](https://github.com/apicrafter/metacrafter-registry/issues/39).

The issue asks to add the semantic types of the AutoType paper and its
benchmark repository to the registry.

Sources reviewed:

- The paper: Cong Yan and Yeye He, *Auto-Type: Synthesizing Type-Detection
  Logic for Rich Semantic Data Types using Open-source Code*, SIGMOD 2018,
  <https://dl.acm.org/doi/10.1145/3183713.3196888>. A copy is on
  [Microsoft Research](https://www.microsoft.com/en-us/research/uploads/prod/2018/04/Auto-Type.pdf).
  Its Appendix A lists the 112 semantic types of the benchmark.
- The benchmark data: `data_release/` of
  [congy/AutoType](https://github.com/congy/AutoType) at commit
  `600df80b283480dbbda07339a569e24a1835e3ca` (2020-09-24). It is the only
  commit of the repository.

All numbers below were computed from that commit.

## Summary

- The paper names **112 semantic types**. The data release has **142 test
  cases**, one `data_release/<name>.txt` file each, with 5 to 206 distinct
  example values per file. A type with several formats has one test case per
  format, plus one with the formats mixed (section 8.1 of the paper). For
  example, date and time has 27 test cases (`date-R`, `date-chinese`, ...)
  and US address has 7.
- 23 of the paper's types have no test case in the release, for example
  LSID, HL7, NATO stock number, ISTC, IGSN and GeoJSON. See
  [Paper types without a test case](#paper-types-without-a-test-case).
- **Done in this change:**
  - New crosswalk key `mappings.autotype`. It holds test case names, which
    are the file names without `.txt`, such as `isbn` or `date-chinese`. The
    schema rejects other values, such as `isbn.txt`.
    `crosswalk("autotype", ...)` also accepts the file name (`isbn.txt`) and
    its `data_release/` path.
  - 118 of the 142 test cases are mapped to 81 records. A test case maps to
    at most one record (a test checks this).
  - 19 new draft records for benchmark types the registry did not have. See
    [New records](#new-records).
  - The regexp of `idcard` (Chinese Resident Identity Card number) accepted
    8 to 15 digits, so it rejected every current 18-character number. It now
    accepts 18 characters (17 digits and a check digit, 0-9 or X) or the
    older 15 digits. Its description is rewritten.
- **Not done, on purpose:** 24 test cases are not mapped. They are message
  formats, free text, formats without a standard notation, and four unclear
  or mislabelled files. See [Test cases that are not mapped](#test-cases-that-are-not-mapped).

## License

The benchmark is released under the
[Computational Use of Data Agreement v1.0](https://github.com/microsoft/Computational-Use-of-Data-Agreement/blob/master/C-UDA-1.0.md)
(C-UDA). The registry does not copy the benchmark files, and no record uses a
benchmark value as an example; this review quotes a few values to explain the
mapping. The examples of the new records come from specifications, Wikipedia, Wikidata and
the documentation or API of each identifier (the Ensembl IDs were checked
against the Ensembl REST API). Each new record links to its test case file in
the AutoType repository. The numbers in the mapping table were
computed locally from the files.

## What the benchmark is

AutoType searches GitHub for code that parses or validates a type, given a
type name and about 20 example values, and synthesizes a detection function
from it. The benchmark was built to measure the precision and recall of such
detectors. Its types come from a commercial data preparation system. Most of
them are value types: identifiers with check digits (ISBN, IBAN, VIN),
codes (ICD-10, airport codes), notations (SMILES, MGRS) and formats of dates,
phone numbers and addresses. Some are whole messages or documents (SWIFT MT,
FIX, NOTAM, SQL), and a few are free text (book titles, drug names).

The registry and the benchmark meet at the value types. Messages, documents
and free text are not value types with a fixed form, so they are not mapped.

## Mapping (in `mappings.autotype`)

"Values" is the number of distinct non-empty lines in the file. The last
column says how many of them the record's regexp matches, and, for records
with a `checksum`, how many matching values also pass the check digit. A
record without a regexp is mapped by meaning only. Low numbers point at data
problems in the benchmark or at registry regexps to review; see
[Findings in existing records](#findings-in-existing-records).

**Science and health**

| Test case | Values | Registry id | Values the regexp matches |
|---|---|---|---|
| `inchi` | 43 | `inchl` | 41 of 43 |
| `cas` | 10 | `casrn` | 10 of 10 |
| `chemical` | 49 | `molformula` | 49 of 49 |
| `smile` | 16 | `smiles` (new) | no regexp |
| `uniprot` | 20 | `uniprot_id` (new) | 20 of 20 |
| `ensembl` | 17 | `ensembl_id` (new) | 17 of 17 |
| `SNPID_correct` | 169 | `dbsnp_id` (new) | 105 of 169 |
| `dea` | 12 | `usdeanumber` | 12 of 12 |
| `icd9` | 35 | `icd9` (new) | 35 of 35 |
| `ICD10_correct` | 38 | `icd10` | 38 of 38 |

**Finance and commerce**

| Test case | Values | Registry id | Values the regexp matches |
|---|---|---|---|
| `SEDOL` | 14 | `sedol` | 11 of 14 |
| `upc` | 61 | `upc` | no regexp |
| `cusip` | 60 | `cusip` | 60 of 60 |
| `stocksymbol` | 33 | `tickersymbol` | 33 of 33 |
| `routingnumber` | 21 | `abaroutingnum` | 0 of 21 |
| `ean` | 49 | `ean` | 49 of 49 |
| `EAN13_correct` | 55 | `ean` | 54 of 55 |
| `asin` | 66 | `asin` (new) | 66 of 66 |
| `iban` | 48 | `iban` | 48 of 48, 48 pass the check digit |
| `bitcoin` | 20 | `p2pkhaddr` | no regexp |
| `EDIFACT_correct` | 42 | `edifact_message_type` (new) | 42 of 42 |
| `gtin` | 12 | `gtin` | 0 of 12 |
| `creditcard` | 16 | `bankcard` | 16 of 16, 16 pass the check digit |
| `currency` | 15 | `iso4217curcode` | 15 of 15 |
| `currency2` | 14 | `money` | no regexp |
| `currency3` | 14 | `money` | no regexp |
| `SWIFT1_correct` | 21 | `swiftcode` | 21 of 21 |

**Technology**

| Test case | Values | Registry id | Values the regexp matches |
|---|---|---|---|
| `ipv4` | 38 | `ipv4` | no regexp |
| `ipv6` | 40 | `ipv6` | no regexp |
| `url` | 62 | `url` | 62 of 62 |
| `imei` | 20 | `imei` | 20 of 20, 20 pass the check digit |
| `mac` | 38 | `mac_address` | 38 of 38 |
| `md5` | 20 | `md5hash` | 20 of 20 |
| `SHA1_correct` | 83 | `sha1hash` | 83 of 83 |
| `sha256` | 206 | `sha256hash` | 206 of 206 |
| `msisdn` | 13 | `msisdn` | 13 of 13 |
| `httpstatus` | 25 | `http_status_code` (new) | 25 of 25 |
| `useragentstring` | 20 | `user_agent` (new) | no regexp |
| `guid` | 20 | `uuid` | 20 of 20 |

**Transportation**

| Test case | Values | Registry id | Values the regexp matches |
|---|---|---|---|
| `vin` | 40 | `vin` | no regexp |
| `uic` | 10 | `uic_wagon_number` (new) | 7 of 10, 7 pass the check digit |
| `IMO_correct` | 95 | `imonumber` | 94 of 95 |

**Geography**

| Test case | Values | Registry id | Values the regexp matches |
|---|---|---|---|
| `longlat` | 25 | `geopoint` | no regexp |
| `zipcode-correct` | 13 | `uszipcode` | no regexp |
| `ukpost` | 36 | `ukpostalcode` | no regexp |
| `canpost` | 20 | `ca_fsa` (new) | 20 of 20 |
| `mgrs` | 20 | `mgrs` (new) | 20 of 20 |
| `gln` | 33 | `gln` | 33 of 33 |
| `airport` | 21 | `iataairportcode` | 21 of 21 |
| `usstate` | 14 | `usstate` | no regexp |
| `countrycode` | 22 | `countrycode_alpha2` | 22 of 22 |

**Publications**

| Test case | Values | Registry id | Values the regexp matches |
|---|---|---|---|
| `isbn` | 20 | `isbn10` | 20 of 20, 20 pass the check digit |
| `isin` | 62 | `isin` | 62 of 62 |
| `issn` | 73 | `issn` | 72 of 73 |
| `bibcode` | 67 | `bibcode` (new) | 66 of 67 |
| `isan` | 15 | `isan` | 15 of 15 |
| `iswc` | 37 | `iswc` (new) | 37 of 37 |
| `doi` | 26 | `doi` | no regexp |
| `ISRC2_correct` | 50 | `isrc` | 50 of 50 |
| `ismn` | 20 | `ismn` | 20 of 20 |
| `orcid` | 17 | `orcid` | 17 of 17 |
| `lcc` | 42 | `lcc` (new) | 42 of 42 |

**Personal information**

| Test case | Values | Registry id | Values the regexp matches |
|---|---|---|---|
| `phone-3` | 20 | `phone` | 20 of 20 |
| `phone1` | 41 | `nanpphone` | 41 of 41 |
| `phone2` | 32 | `nanpphone` | 32 of 32 |
| `phone-mixed` | 20 | `nanpphone` | 9 of 20 |
| `email` | 20 | `email` | 20 of 20 |
| `name1` | 145 | `person_fullname` | no regexp |
| `us_address` | 48 | `address` | no regexp |
| `usaddress-mixed` | 34 | `address` | no regexp |
| `usaddress1` | 100 | `address` | no regexp |
| `usaddress2` | 83 | `address` | no regexp |
| `usaddress3` | 100 | `address` | no regexp |
| `usaddress4` | 34 | `address` | no regexp |
| `usaddress5` | 34 | `address` | no regexp |
| `austraddr` | 40 | `address` | no regexp |
| `chinaaddr` | 33 | `address` | no regexp |
| `japan address` | 15 | `address` | no regexp |
| `lei` | 14 | `lei` | 14 of 14 |
| `ssn` | 20 | `usssn` | 20 of 20 |
| `ssn - new` | 20 | `usssn` | 20 of 20 |
| `cin` | 20 | `idcard` | 20 of 20 |
| `ein` | 20 | `usein` | 0 of 20 |
| `nhs` | 40 | `uknhsnum` | 40 of 40 |
| `npi` | 82 | `usnpi` | no regexp |

**Other values**

| Test case | Values | Registry id | Values the regexp matches |
|---|---|---|---|
| `hexcolor` | 30 | `hexcolor` | 30 of 30 |
| `rgb` | 45 | `rgbcolor` (new) | 45 of 45 |
| `hsl` | 54 | `hslcolor` (new) | 54 of 54 |
| `unixtime` | 16 | `unixtime` | 16 of 16 |
| `unixback` | 22 | `unixtime` | 22 of 22 |
| `roman` | 19 | `roman_numeral` (new) | 19 of 19 |

**Dates and times**

| Test case | Values | Registry id | Values the regexp matches |
|---|---|---|---|
| `date-R` | 50 | `datetime` | no regexp |
| `date-chinese2` | 30 | `datetime` | no regexp |
| `date-f` | 50 | `datetime` | no regexp |
| `date-g` | 50 | `datetime` | no regexp |
| `date-german` | 30 | `datetime` | no regexp |
| `date-mixed` | 40 | `datetime` | no regexp |
| `date-o` | 50 | `datetime` | no regexp |
| `date-s` | 50 | `datetime` | no regexp |
| `date-spanish` | 30 | `datetime` | no regexp |
| `date-u` | 50 | `datetime` | no regexp |
| `date5` | 18 | `datetime` | no regexp |
| `date6` | 16 | `datetime` | no regexp |
| `date7` | 16 | `datetime` | no regexp |
| `date8` | 10 | `datetime` | no regexp |
| `date9` | 12 | `datetime` | no regexp |
| `date-chinese` | 36 | `date` | no regexp |
| `date-d` | 50 | `date` | no regexp |
| `date-hijri` | 20 | `date` | no regexp |
| `date1` | 7 | `date` | no regexp |
| `date10` | 10 | `date` | no regexp |
| `date2` | 26 | `date` | no regexp |
| `date3` | 15 | `date` | no regexp |
| `date4` | 21 | `date` | no regexp |
| `date-t` | 50 | `time` | no regexp |
| `date-m` | 43 | `monthday` | no regexp |
| `date-y` | 49 | `yearmonth` | no regexp |
| `date11` | 13 | `yearmonth` | no regexp |

Notes on the mapping:

- **Formats of one type map to one record.** All 27 date and time test cases
  map to `datetime`, `date`, `time`, `monthday` or `yearmonth`, by what the
  values hold. The registry describes these types, not each written format.
  The Hijri dates (`date-hijri`) and the BCE dates (`date4`) map to `date`.
- **Partial addresses.** `usaddress1` (city, state, ZIP), `usaddress2` (city,
  state), `usaddress3` (city, ZIP) and `usaddress4` (street line) map to
  `address`, like the full addresses. The registry has no record for these
  parts.
- **Canada postal code.** The paper's type is "Canada postal code", but the
  `canpost` values are only the first three characters, the forward sortation
  area (`K0H`, `T4A`). So `canpost` maps to the new `ca_fsa`. The new
  `ca_postalcode` record describes the full code. metacrafter-rules already
  used the rule key `ca_postalcode`, which had no registry record until now.
- **Duplicates.** Where the registry has two records for one type, the
  mapping uses the stable, more complete one: `abaroutingnum` (not `aba`),
  `swiftcode` (not `bic`), `usnpi` (not `npi`), `uknhsnum` (not
  `nhsnumber`), `hexcolor` (not `colorhextriplet`). See recommendation 4.
- **Bitcoin.** All 20 `bitcoin` values start with 1, so the test case maps to
  `p2pkhaddr` (pay-to-pubkey-hash addresses).
- **`unixback`** holds Unix times with fractional seconds, with spaces as
  thousands separators (`915 148 798.75`). It maps to `unixtime`.

## New records

All are drafts. The "Source of the format" column names where the regexp
comes from. Where a record has no regexp, the type has no form that a regexp
can tell apart from other text.

| Registry id | Test case | Type | Source of the format | Benchmark values matched |
|---|---|---|---|---|
| `smiles` | `smile` | SMILES chemical notation | No regexp (a parser is needed) | |
| `uniprot_id` | `uniprot` | UniProtKB accession | Regular expression in the UniProt help | 20 of 20 |
| `ensembl_id` | `ensembl` | Ensembl gene, transcript or protein ID | Wikidata P594, P704, P705 and identifiers.org | 17 of 17 |
| `dbsnp_id` | `SNPID_correct` | dbSNP RefSNP number (rsID) | `rs` and a number (NCBI) | 105 of 169; the others are bare numbers and `FP...` ids |
| `icd9` | `icd9` | ICD-9 code | Wikidata P493 | 35 of 35 |
| `asin` | `asin` | Amazon Standard Identification Number | Ten letters and digits (Wikipedia) | 66 of 66 |
| `edifact_message_type` | `EDIFACT_correct` | UN/EDIFACT message type | Six uppercase letters (German Wikipedia, EDIFACT) | 42 of 42 |
| `http_status_code` | `httpstatus` | HTTP status code | RFC 9110, section 15 | 25 of 25 |
| `user_agent` | `useragentstring` | HTTP User-Agent string | No regexp (RFC 9110 grammar is too loose) | |
| `uic_wagon_number` | `uic` | UIC wagon number (EVN) | Wikipedia; Luhn check digit | 7 of 10; the others carry operator markings such as `RIV` or `GB-EIL` |
| `ca_fsa` | `canpost` | Canadian forward sortation area | Wikipedia, Postal codes in Canada | 20 of 20 |
| `ca_postalcode` | | Canadian postal code (pattern of `postindex`) | Wikipedia, Postal codes in Canada | |
| `mgrs` | `mgrs` | MGRS coordinate | Wikipedia | 20 of 20 |
| `rgbcolor` | `rgb` | RGB color triplet (pattern of `color`) | CSS Color 4, `rgb()` | 45 of 45 |
| `hslcolor` | `hsl` | HSL color (pattern of `color`) | CSS Color 4, `hsl()` | 54 of 54 |
| `roman_numeral` | `roman` | Roman numeral, 1 to 3999 | Standard subtractive form | 19 of 19 |
| `bibcode` | `bibcode` | ADS bibcode | Wikidata P819, with any letter as qualifier | 66 of 67; the other is URL-encoded (`A%26A`) |
| `iswc` | `iswc` | International Standard Musical Work Code | Wikipedia (ISO 15707) | 37 of 37 |
| `lcc` | `lcc` | Library of Congress Classification number | Wikidata P1149, with a class number required | 42 of 42 |

Notes on the new records:

- **`bibcode`.** The Wikidata format allows only `E`, `L`, `P` and `Q` to
  `Z` in the qualifier column. Real bibcodes of journals with article
  numbers use other letters there, such as `A` in Astronomy & Astrophysics,
  and Physical Review issues use lowercase letters. So the regexp accepts any
  letter.
- **`lcc`.** The Wikidata format also matches one to three letters alone,
  which would match any short uppercase word. The registry's regexp requires
  the class number.
- **`ensembl_id`.** It covers the vertebrate IDs that start with `ENS`, for
  genes, transcripts and proteins, the kinds that Wikidata and
  identifiers.org describe. The Ensembl stable ID page could not be reached
  during this review (HTTP 500), so other feature kinds are left out. The
  record maps to no Wikidata property, because Wikidata has one property per
  feature kind.
- **`smiles`.** Wikidata's format for canonical SMILES (P233) is a character
  set. It matches ordinary words such as `Butane`, so the record has no
  regexp.
- **`iswc`.** The check digit is a weighted sum modulo 10. The registry does
  not implement it as a `checksum` yet: a new algorithm needs both
  `checksums.py` and its JavaScript twin in `identify-core.js`.

## Test cases that are not mapped

| Test case | What it holds | Why it is not mapped |
|---|---|---|
| `FASTA`, `FASTQ` | Sequence records over several lines | File and record formats, not values |
| `SWIFT` | SWIFT MT messages | Multi-line messages |
| `fix` | FIX protocol messages | Messages |
| `notam`, `taf`, `pireps` | Aviation notices, forecasts and pilot reports | Multi-line or free-form messages |
| `ais`, `nmea` | AIS and NMEA 0183 sentences | Messages; see recommendation 3 |
| `sql` | SQL statements | Code |
| `apa`, `apacite`, `iso690` | Bibliographic citations | Free text |
| `booktitles` | Book titles with author names | Free text |
| `drug` | Drug names | Free text; see recommendation 3 |
| `iupac` | Chemical names (`Butane`, `2-methyl propane`) | Free text |
| `cmyk` | CMYK colors as four fractions | No standard written form |
| `utm` | UTM coordinates as easting, northing, zone | No standard written form |
| `daterange1`, `daterange2` | Date ranges in two formats | No record; see recommendation 3 |
| `longlat_dist` | Four numbers per line, two above 90 | Unclear; not coordinates |
| `Health_correct` | Pairs of numbers (`164 116`) | Unclear |
| `SWIFT2_correct` | `01-015513` and similar | Unclear; not SWIFT or BIC codes |
| `ric` | Rating words (`Clear Defensible`) | Mislabelled: not Reuters Instrument Codes |

## Paper types without a test case

Appendix A of the paper lists these types, but the data release has no file
for them, so there is no test case name to map.

| Paper type | Registry record |
|---|---|
| Anatomical Therapeutic Chemical | `atccode` |
| HCPCS code | `cptcode` |
| PubChem ID | `pubchemid` |
| OID number | `oid` |
| International Standard Name Identifier (ISNI) | `isni` |
| Life Science Identifier (LSID), EVMPD, International Code of Zoological Nomenclature, HL7 message, FDA drug code, Active Ingredient Group number, NATO stock number, International Standard Text Code (ISTC), GeoJSON, International Geo Sample Number (IGSN), ONIX, National Bibliography Number (NBN), Electronic Textbook Track Number (ETTN), FEI identifier, HTML, JSON, XML | None; see recommendation 3 |
| Personal Identifiable Information (PII) | None; a class of types, which the registry marks with `is_pii` |

## Findings in existing records

Running the registry's regexps over the benchmark values shows defects in
existing records. They are outside this change and are left for a follow-up:

| Record | Regexp | Problem |
|---|---|---|
| `sedol` | `[0-9.]{7}` | SEDOLs issued since 2004 contain letters (`B03MM40`); 3 of 14 benchmark values fail. Not anchored. |
| `usein` | `[0-9]{9}` | Rejects the usual `NN-NNNNNNN` notation; 0 of 20 benchmark values match. Not anchored. |
| `abaroutingnum` | `[0123678]\d{3}-\d{4}-\d` | Requires dashes; 0 of 21 plain nine-digit routing numbers match. Not anchored. |
| `gtin` | `^01(\d{14})$` | Requires the GS1 application identifier `(01)`, so a bare 14-digit GTIN does not match (0 of 12). This may be intended; the record describes the element string. |
| `issn` | `\d{4}-\d{3}[\dX]\|\d{8}` | A lowercase check character `x` fails (1 of 73). Not anchored. |
| `upc`, `vin`, `uszipcode`, `ukpostalcode`, `usnpi`, `usstate` | none | No regexp, although the formats are well defined (and `upc`, `vin`, `usnpi` have check digits). |

The other differences are benchmark noise: `IMO_correct` contains the word `craine`,
`EAN13_correct` contains a 12-digit UPC, and `phone-mixed` contains vanity
numbers (`1-800-flowers`) and invalid central office codes, which
`nanpphone` rejects on purpose.

## Recommendations and follow-ups

1. **Fix the regexps in the findings table**, starting with `sedol`, `usein`
   and `abaroutingnum`, and anchor them. Add regexps (and check digits, where
   `checksums.py` has them) to `upc`, `vin`, `usnpi`, `uszipcode` and
   `ukpostalcode`.
2. **Use the benchmark as a regression test for metacrafter.** With
   `mappings.autotype`, a script can run metacrafter on each test case file
   and compare the detected type with the mapped registry id. That measures
   metacrafter's recall per type. The C-UDA license allows this
   computational use; the files should be downloaded at test time, not
   committed.
3. **Types still missing** that have a standard written form and could become
   records: NATO stock number (13 digits, `NNNN-NN-NNN-NNNN`), ISTC (16
   hexadecimal characters), LSID (`urn:lsid:...`), NBN (`urn:nbn:...`),
   IGSN, FDA National Drug Code, ISO 8601 date intervals, and NMEA 0183 and
   AIS sentences. Free-text types (drug name, chemical name, citation, book
   title) could be records without a regexp, if metacrafter gets detectors for
   them.
4. **Merge duplicate records.** `aba` and `abaroutingnum`, `bic` and
   `swiftcode`, `npi` and `usnpi`, `nhsnumber` and `uknhsnum`, and
   `colorhextriplet` and `hexcolor` describe the same types. Keep one record of
   each pair and add the other id to its `aliases`. This changes published
   records, so it needs a maintainer decision.
5. **Re-check is unlikely to be needed.** The repository has a single commit
   from 2020.
