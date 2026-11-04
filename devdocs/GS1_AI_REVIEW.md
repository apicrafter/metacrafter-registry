# GS1 Application Identifiers: review (2026-11-04)

Issue: [apicrafter/metacrafter-registry#20](https://github.com/apicrafter/metacrafter-registry/issues/20).

The issue asks to add the identifiers among the GS1 Application Identifiers
(AIs) to the registry, with a name, a description, the format and a regular
expression. It notes that not every AI is an identifier: many describe a
trade item (a weight, a date, an address). In 2022 the `gs1` category and two
records were added: `gtin` (AI 01) and `gtin02` (AI 02). `sssc` (AI 00) also
existed.

Sources:

- **GS1 Application Identifiers vocabulary**,
  <https://ref.gs1.org/ai/GS1_Application_Identifiers.jsonld>, version 1.2,
  last modified 2026-01-26, licensed Apache-2.0. It lists **541 AIs**; the
  issue counted 517 in 2022. For each AI it gives the description, the data
  title, the format string (`N3+N13`), a regular expression, the components,
  the GS1 Digital Link role and the AIs it requires or excludes. All numbers
  below were computed from this file.
- **GS1 Barcode Syntax Dictionary**,
  [gs1/gs1-syntax-dictionary](https://github.com/gs1/gs1-syntax-dictionary)
  (Apache-2.0), and the linters of
  [gs1/gs1-syntax-engine](https://github.com/gs1/gs1-syntax-engine). They say
  which components carry a GS1 check digit (`csum`), a check character pair
  (`csumalpha`) or a GS1 Company Prefix (`gcppos1`: the first four characters
  are digits, because the shortest GS1 Company Prefix has four).

## Summary

- **New crosswalk key `mappings.gs1_ai`.** It holds GS1 AIs as GS1 writes them
  (`01`, `414`, `8003`). Each AI maps to at most one record (a test checks
  this). `crosswalk("gs1_ai", ...)` also accepts the AI in parentheses, as
  printed under a barcode (`(8003)`), and its `https://ref.gs1.org/ai/` IRI.
  Record pages link each AI to its GS1 page.
- **All 26 identification-key AIs and 8 of the 9 key qualifiers are
  imported**, as one record per AI (34 AIs). 31 records are new; `sssc`,
  `gtin` and `gtin02` gained the mapping, examples and, for `sssc`, a fix.
- **11 new records for the bare GS1 keys** that the registry lacked: `gdti`,
  `gcn`, `ginc`, `gsin`, `grai`, `giai`, `gsrn`, `cpid`, `gmn`, `hidri`,
  `itip`. `gln` already existed.
- **4 AIs that carry a non-GS1 identifier map to existing records:** 8007 to
  `iban`, 8040 and 8041 to `imei`, 716 to `it_aic`.
- **Two check-digit algorithms:** `gs1_mod10` (the GS1 check digit of a
  numeric key of any length) and `gs1_checkpair` (the check character pair of
  the GMN and the HIDRI). The JavaScript of the `/identify` page has both.
- **Fixes:** the `sssc` regexp was `^00(d{18})$` (a literal `d`) and its
  description was Wikipedia's text; `gln` had an unanchored regexp.
- **Not imported: 503 AIs**, see [Not imported](#not-imported).

42 records are new, all `status: draft`.

| Group | AIs | Imported | Mapped to existing records | Not imported |
|---|---|---|---|---|
| GS1 identification keys | 26 | 26 | 0 | 0 |
| Key qualifiers (GS1 Digital Link) | 9 | 8 | 0 | 1 |
| Identifiers carried as data attributes | 47 | 0 | 4 | 43 |
| Dates and times | 14 | 0 | 0 | 14 |
| Measures and counts | 322 | 0 | 0 | 322 |
| Amounts, prices and coupon values | 52 | 0 | 0 | 52 |
| Delivery, return and transport data | 30 | 0 | 0 | 30 |
| Countries and regions of origin or processing | 6 | 0 | 0 | 6 |
| Data about a person | 10 | 0 | 0 | 10 |
| Other product attributes and codes | 15 | 0 | 0 | 15 |
| Internal and mutually agreed data | 10 | 0 | 0 | 10 |
| **Total** | **541** | **34** | **4** | **503** |

## Which AIs are identifiers

The review uses GS1's own classification rather than a judgment per AI:

- **Identification keys (26 AIs).** The vocabulary marks the component of 24
  AIs as a GS1 key: GTIN (01, 02, 03), SSCC (00), GDTI (253), GCN (255),
  GINC (401), GSIN (402), GLN (410 to 417), GIAI (8004 and 7023 for an
  assembly), GRAI (8003), CPID (8010), GMN (8013), HIDRI (8014) and GSRN
  (8017, 8018). The two ITIP AIs (8006, 8026) are added: their value is a GTIN
  with a piece number, and 8006 is a GS1 Digital Link primary key.
- **Key qualifiers (9 AIs).** GS1 Digital Link lists the AIs that may follow a
  primary key in a URI: batch/lot (10), serial number (21), consumer product
  variant (22), TPX (235), GLN extension (254), 7040, CPID serial (8011),
  SRIN (8019) and payment slip reference (8020). With their key they identify
  one batch, one item or one place.
- **Everything else is a data attribute.** Most data attributes describe an
  item: dates, weights, prices, addresses. 47 of them carry an identifier, but
  not a GS1 one: an IBAN, an IMEI, a national drug code, a purchase order
  number. Four of these match existing records and are mapped. The others are
  candidates for later work (see [Follow-ups](#follow-ups-not-done-here)).

## How the records are modelled

**One record per AI, holding the element string.** As in `gtin` and `gtin02`,
the record of an AI describes the element string: the AI digits followed by
the data field (`4149528765000017`). This is what a barcode scanner returns
for one field, and the AI prefix tells AI 410 from AI 411 although both carry
a GLN. New ids are `gs1_ai_<AI>` (`gs1_ai_8003`), so they sort together and a
client can derive them. The published ids `sssc`, `gtin` and `gtin02` stay.

**Bare keys are separate records.** A column of a dataset usually holds the
bare key (`9528765000017`), not the element string. So each GS1 key has its
own record (`gdti`, `grai`, ...; `gln` already existed). Where such a record
exists, the element string is a **pattern** of it (`gs1_ai_8003` has
`semantic_type: grai`; `gs1_ai_410` to `gs1_ai_417` have `semantic_type:
gln`). Where it does not, the element string is a **datatype**, as `gtin02`
already was: `gs1_ai_03` and the qualifiers `gs1_ai_10`, `gs1_ai_21`, ...

**Regular expressions** follow the GS1 Barcode Syntax Dictionary, which is
stricter than the vocabulary's regex in two ways:

- the GS1 Company Prefix: the GINC, GIAI, CPID, GMN and HIDRI start with at
  least four digits;
- the check character pair: the last two characters of the GMN and the HIDRI
  are from GS1 character set 32.

Character set 82 is written as GS1 writes it: `[!%-?A-Z_a-z\x22]`. The
ITIP regexp rejects a piece number or total of `00`; that the piece number
does not exceed the total is only in the description. The HIDRI needs a
character that is not a digit (`hasnondigit`), written as the lookahead
`(?=.*[^0-9])`.

**Check digits.** `gs1_mod10` is used by `gsin`, `gsrn`, `gln` and `sssc`.
Leading zeros do not change the GS1 check digit, so the SSCC element string
(`00` followed by the SSCC) passes as a whole. The element strings of other
AIs do not, so their patterns have no `checksum`. The GDTI, GCN and GRAI carry
the check digit in position 13, before an optional serial component, and the
ITIP in position 14, before the piece numbers. The registry checks a check
digit only at the end of a value, so these records have no `checksum`.
`gs1_checkpair` follows `lint_csumalpha.c` of the GS1 Barcode Syntax Engine.
The tests run its test values.

**Examples** are synthetic. They use the GS1 Prefix 952, which GS1 reserves
for demonstrations and examples, and GS1's example GTIN `09506000134352`. The
GMN example `1987654Ad4X4bL5ttr2310c2K` is a test value of the GS1 linter.
Check digits and check pairs were computed with the registry's own
algorithms. Each record has a negative example.

**Personal data.** A GSRN identifies a person's relationship with a service
provider, such as a patient or a loyalty scheme member. `gsrn` therefore has
`is_pii: true` and the `pii` category, and the patterns for AIs 8017 and 8018
inherit them. The other keys identify things, places or documents.

**Links.** Each record links to the GS1 page of its AI
(`https://ref.gs1.org/ai/<AI>`). The bare keys also link to the GS1 General
Specifications. Wikipedia is linked only where it has an article on the
concept (lot number, serial number). Its "Global Returnable Asset
Identifier", "Global Individual Asset Identifier" and "Global Document Type
Identifier" pages redirect to the general GS1 article.

## The `gs1_ai` crosswalk

`mappings.gs1_ai` names the AIs that a record represents. An AI maps to the
record of its element string when the registry has one. Otherwise it maps to
the record of the value that the AI carries: AI 8007 maps to `iban`, because
the registry has no record for the `8007...` element string. A decoder of
GS1 barcodes can use it in two steps:

1. split a GS1-128 or DataMatrix message, or a GS1 Digital Link URI, into
   AIs;
2. look each AI up with `crosswalk("gs1_ai", ai)` and follow `semantic_type`
   to the bare value's record.

```python
from metacrafter_registry import Registry

reg = Registry.load()
[r["id"] for r in reg.crosswalk("gs1_ai", "(414)")]  # ['gs1_ai_414']; semantic_type gln
[r["id"] for r in reg.crosswalk("gs1_ai", "8007")]  # ['iban']
```

## Judgment calls

- **Element strings and bare values.** `gtin`, `gtin02` and `sssc` describe
  element strings (`01` + GTIN), while
  [metacrafter-rules](https://github.com/apicrafter/metacrafter-rules) uses
  the key `gtin` for bare GTIN-8, -12, -13 and -14 values as well as for the
  AI 01 element string, and `sssc` for both forms of the SSCC. This review keeps the published records as they are and does not add
  a bare GTIN or SSCC record. See [Follow-ups](#follow-ups-not-done-here).
- **Role GLNs are patterns of `gln`.** AIs 410 to 417 differ in the role of
  the place or party (ship to, bill to, ...). The value is a GLN in each case,
  so each is a pattern of `gln` rather than a datatype of its own.
- **7040 is not imported.** The vocabulary gives only its format (a digit,
  two characters and an importer index) and its data title "UIC+EXT". Its
  meaning needs the GS1 General Specifications; a record without a meaning
  would not help.
- **8043 (Physical SIM number) is not mapped to `iccid`.** The vocabulary
  does not say that the value is an ICCID, and its format (18 digits and an
  optional 1 or 2 more) differs from the registry's `iccid` (19 or 20 digits).
- **`gln` gains `checksum: gs1_mod10` and an anchored regexp.** Its two real
  examples pass the check digit.

## Follow-ups (not done here)

- **Bare GTIN and SSCC.** A bare `gtin` would fit metacrafter-rules, but the
  id `gtin` is the element string of AI 01. A new id (for example
  `gtin_value`) with `gtin` as parent, or a change to the meaning of `gtin`,
  needs a maintainer decision. The same applies to `sssc`, which also
  misspells SSCC.
- **National identifiers carried by AIs:** NATO Stock Number (7001) and the
  National Healthcare Reimbursement Numbers: Germany PZN (710), France CIP
  (711), Spain CN (712), Brazil DRN (713), Portugal AIM (714), US NDC (715)
  and Costa Rica (717). Each needs a record researched from its issuing
  authority. Once a record exists, the AI can be added to its
  `mappings.gs1_ai`.
- **SIM identifiers:** the embedded SIM number (8042, 32 digits) and the
  physical SIM number (8043), once their relation to the EID and the ICCID is
  checked.
- **A GS1 element-string parser** in the registry client, which splits a
  scanned message into AIs and returns registry types. The vocabulary gives
  everything needed: formats, separators and fixed lengths.

## Mapping table (all 541 AIs)

Generated from the GS1 vocabulary (version 1.2). A range such as
`3100`–`3105` collects consecutive AIs with the same description. In the
measure and amount AIs, the last digit is the position of the decimal point.
### Imported: GS1 identification keys and key qualifiers

| AI | GS1 description | Format | Record | Bare value |
|---|---|---|---|---|
| `00` | Serial Shipping Container Code (SSCC) | `N2+N18` | `sssc` |  |
| `01` | Global Trade Item Number (GTIN) | `N2+N14` | `gtin` |  |
| `02` | Global Trade Item Number (GTIN) of contained trade items | `N2+N14` | `gtin02` |  |
| `03` | Identification of a Made-to-Order (MtO) trade item (GTIN) | `N2+N14` | `gs1_ai_03` |  |
| `10` | Batch or lot number | `N2+X..20` | `gs1_ai_10` |  |
| `21` | Serial number | `N2+X..20` | `gs1_ai_21` |  |
| `22` | Consumer product variant | `N2+X..20` | `gs1_ai_22` |  |
| `235` | Third Party Controlled, Serialised Extension of Global Trade Item Number (GTIN) (TPX) | `N3+X..28` | `gs1_ai_235` |  |
| `253` | Global Document Type Identifier (GDTI) | `N3+N13[+X..17]` | `gs1_ai_253` | `gdti` |
| `254` | Global Location Number (GLN) extension component | `N3+X..20` | `gs1_ai_254` |  |
| `255` | Global Coupon Number (GCN) | `N3+N13[+N..12]` | `gs1_ai_255` | `gcn` |
| `401` | Global Identification Number for Consignment (GINC) | `N3+X..30` | `gs1_ai_401` | `ginc` |
| `402` | Global Shipment Identification Number (GSIN) | `N3+N17` | `gs1_ai_402` | `gsin` |
| `410` | Ship to / Deliver to Global Location Number (GLN) | `N3+N13` | `gs1_ai_410` | `gln` |
| `411` | Bill to / Invoice to Global Location Number (GLN) | `N3+N13` | `gs1_ai_411` | `gln` |
| `412` | Purchased from Global Location Number (GLN) | `N3+N13` | `gs1_ai_412` | `gln` |
| `413` | Ship for / Deliver for - Forward to Global Location Number (GLN) | `N3+N13` | `gs1_ai_413` | `gln` |
| `414` | Identification of a physical location - Global Location Number (GLN) | `N3+N13` | `gs1_ai_414` | `gln` |
| `415` | Global Location Number (GLN) of the invoicing party | `N3+N13` | `gs1_ai_415` | `gln` |
| `416` | Global Location Number (GLN) of the production or service location | `N3+N13` | `gs1_ai_416` | `gln` |
| `417` | Party Global Location Number (GLN) | `N3+N13` | `gs1_ai_417` | `gln` |
| `7023` | Global Individual Asset Identifier (GIAI) of an assembly | `N4+X..30` | `gs1_ai_7023` | `giai` |
| `8003` | Global Returnable Asset Identifier (GRAI) | `N4+N14[+X..16]` | `gs1_ai_8003` | `grai` |
| `8004` | Global Individual Asset Identifier (GIAI) | `N4+X..30` | `gs1_ai_8004` | `giai` |
| `8006` | Identification of an individual trade item piece (ITIP) | `N4+N14+N2+N2` | `gs1_ai_8006` | `itip` |
| `8010` | Component/Part Identifier (CPID) | `N4+Y..30` | `gs1_ai_8010` | `cpid` |
| `8011` | Component/Part Identifier serial number (CPID SERIAL) | `N4+N..12` | `gs1_ai_8011` |  |
| `8013` | Global Model Number (GMN) | `N4+X..25` | `gs1_ai_8013` | `gmn` |
| `8014` | Highly Individualised Device Registration Identifier (HIDRI) | `N4+X..25` | `gs1_ai_8014` | `hidri` |
| `8017` | Global Service Relation Number (GSRN) to identify the relationship between an organisation offering services and the provider of services | `N4+N18` | `gs1_ai_8017` | `gsrn` |
| `8018` | Global Service Relation Number (GSRN) to identify the relationship between an organisation offering services and the recipient of services | `N4+N18` | `gs1_ai_8018` | `gsrn` |
| `8019` | Service Relation Instance Number (SRIN) | `N4+N..10` | `gs1_ai_8019` |  |
| `8020` | Payment slip reference number | `N4+X..25` | `gs1_ai_8020` |  |
| `8026` | Identification of pieces of a trade item (ITIP) contained in a logistic unit | `N4+N14+N2+N2` | `gs1_ai_8026` | `itip` |

### Mapped to existing records

| AI | GS1 description | Format | Record |
|---|---|---|---|
| `716` | National Healthcare Reimbursement Number (NHRN) - Italy AIC | `N3+X..20` | `it_aic` |
| `8007` | International Bank Account Number (IBAN) | `N4+X..34` | `iban` |
| `8040` | Internatinal Mobile Equipment Identity (IMEI) | `N4+N15` | `imei` |
| `8041` | Internatinal Mobile Equipment Identity 2 (IMEI2) | `N4+N15` | `imei` |

### Not imported

Key qualifiers: `7040`

#### Identifiers carried as data attributes (43 AIs)

| AI | GS1 description | Format |
|---|---|---|
| `240` | Additional product identification assigned by the manufacturer | `N3+X..30` |
| `241` | Customer part number | `N3+X..30` |
| `243` | Packaging component number | `N3+X..20` |
| `250` | Secondary serial number | `N3+X..30` |
| `251` | Reference to source entity | `N3+X..30` |
| `400` | Customers purchase order number | `N3+X..30` |
| `403` | Routing code | `N3+X..30` |
| `7001` | NATO Stock Number (NSN) | `N4+N13` |
| `7020` | Refurbishment lot ID | `N4+X..20` |
| `7030`–`7039` | Number of processor with three-digit ISO country code | `N4+N3+X..27` |
| `710` | National Healthcare Reimbursement Number (NHRN) - Germany PZN | `N3+X..20` |
| `711` | National Healthcare Reimbursement Number (NHRN) - France CIP | `N3+X..20` |
| `712` | National Healthcare Reimbursement Number (NHRN) - Spain CN | `N3+X..20` |
| `713` | National Healthcare Reimbursement Number (NHRN) - Brasil DRN | `N3+X..20` |
| `714` | National Healthcare Reimbursement Number (NHRN) - Portugal AIM | `N3+X..20` |
| `715` | National Healthcare Reimbursement Number (NHRN) - United States of America NDC | `N3+X..20` |
| `717` | National Healthcare Reimbursement Number (NHRN) - Costa Rica Sanitary Register Number | `N3+X..20` |
| `7230`–`7239` | Certification Reference | `N4+X2+X..28` |
| `7240` | Protocol ID | `N4+X..20` |
| `7242` | Version Control Number (VCN) | `N4+X..25` |
| `8002` | Cellular mobile telephone identifier | `N4+X..20` |
| `8042` | Embedded SIM number | `N4+N32` |
| `8043` | Physical SIM number | `N4+N18+[N1..N2]` |
| `8110` | Coupon code identification for use in North America | `N4+X..70` |
| `8112` | Positive offer file coupon code identification for use in North America | `N4+X..70` |

#### Dates and times (14 AIs)

| AI | GS1 description | Format |
|---|---|---|
| `11` | Production date (YYMMDD) | `N2+N6` |
| `12` | Due date (YYMMDD) | `N2+N6` |
| `13` | Packaging date (YYMMDD) | `N2+N6` |
| `15` | Best before date (YYMMDD) | `N2+N6` |
| `16` | Sell by date (YYMMDD) | `N2+N6` |
| `17` | Expiration date (YYMMDD) | `N2+N6` |
| `4324` | Not before delivery date time (YYMMDDhhmm) | `N4+N10` |
| `4325` | Not after delivery date time (YYMMDDhhmm) | `N4+N10` |
| `4326` | Release date (YYMMDD) | `N4+N6` |
| `7003` | Expiration date and time (YYMMDDhhmm) | `N4+N10` |
| `7006` | First freeze date (YYMMDD) | `N4+N6` |
| `7007` | Harvest date (YYMMDD[YYMMDD]) | `N4+N6[+N6]` |
| `7011` | Test by date (YYMMDD[hhmm]) | `N4+N6[+N4]` |
| `8008` | Date and time of production (YYMMDDhh[mm[ss]]) | `N4+N8[+N..4]` |

#### Measures and counts (322 AIs)

| AI | GS1 description | Format |
|---|---|---|
| `30` | Variable count of items (variable measure trade item) | `N2+N..8` |
| `3100`–`3105` | Net weight, kilograms (variable measure trade item) | `N4+N6` |
| `3110`–`3115` | Length or first dimension, metres (variable measure trade item) | `N4+N6` |
| `3120`–`3125` | Width, diameter, or second dimension, metres (variable measure trade item) | `N4+N6` |
| `3130`–`3135` | Depth, thickness, height, or third dimension, metres (variable measure trade item) | `N4+N6` |
| `3140`–`3145` | Area, square metres (variable measure trade item) | `N4+N6` |
| `3150`–`3155` | Net volume, litres (variable measure trade item) | `N4+N6` |
| `3160`–`3165` | Net volume, cubic metres (variable measure trade item) | `N4+N6` |
| `3200`–`3205` | Net weight, pounds (variable measure trade item) | `N4+N6` |
| `3210`–`3215` | Length or first dimension, inches (variable measure trade item) | `N4+N6` |
| `3220`–`3225` | Length or first dimension, feet (variable measure trade item) | `N4+N6` |
| `3230`–`3235` | Length or first dimension, yards (variable measure trade item) | `N4+N6` |
| `3240`–`3245` | Width, diameter, or second dimension, inches (variable measure trade item) | `N4+N6` |
| `3250`–`3255` | Width, diameter, or second dimension, feet (variable measure trade item) | `N4+N6` |
| `3260`–`3265` | Width, diameter, or second dimension, yards (variable measure trade item) | `N4+N6` |
| `3270`–`3275` | Depth, thickness, height, or third dimension, inches (variable measure trade item) | `N4+N6` |
| `3280`–`3285` | Depth, thickness, height, or third dimension, feet (variable measure trade item) | `N4+N6` |
| `3290`–`3295` | Depth, thickness, height, or third dimension, yards (variable measure trade item) | `N4+N6` |
| `3300`–`3305` | Logistic weight, kilograms | `N4+N6` |
| `3310`–`3315` | Length or first dimension, metres | `N4+N6` |
| `3320`–`3325` | Width, diameter, or second dimension, metres | `N4+N6` |
| `3330`–`3335` | Depth, thickness, height, or third dimension, metres | `N4+N6` |
| `3340`–`3345` | Area, square metres | `N4+N6` |
| `3350`–`3355` | Logistic volume, litres | `N4+N6` |
| `3360`–`3365` | Logistic volume, cubic metres | `N4+N6` |
| `3370`–`3375` | Kilograms per square metre | `N4+N6` |
| `3400`–`3405` | Logistic weight, pounds | `N4+N6` |
| `3410`–`3415` | Length or first dimension, inches | `N4+N6` |
| `3420`–`3425` | Length or first dimension, feet | `N4+N6` |
| `3430`–`3435` | Length or first dimension, yards | `N4+N6` |
| `3440`–`3445` | Width, diameter, or second dimension, inches | `N4+N6` |
| `3450`–`3455` | Width, diameter, or second dimension, feet | `N4+N6` |
| `3460`–`3465` | Width, diameter, or second dimension, yard | `N4+N6` |
| `3470`–`3475` | Depth, thickness, height, or third dimension, inches | `N4+N6` |
| `3480`–`3485` | Depth, thickness, height, or third dimension, feet | `N4+N6` |
| `3490`–`3495` | Depth, thickness, height, or third dimension, yards | `N4+N6` |
| `3500`–`3505` | Area, square inches (variable measure trade item) | `N4+N6` |
| `3510`–`3515` | Area, square feet (variable measure trade item) | `N4+N6` |
| `3520`–`3525` | Area, square yards (variable measure trade item) | `N4+N6` |
| `3530`–`3535` | Area, square inches | `N4+N6` |
| `3540`–`3545` | Area, square feet | `N4+N6` |
| `3550`–`3555` | Area, square yards | `N4+N6` |
| `3560`–`3565` | Net weight, troy ounces (variable measure trade item) | `N4+N6` |
| `3570`–`3575` | Net weight (or volume), ounces (variable measure trade item) | `N4+N6` |
| `3600`–`3605` | Net volume, quarts (variable measure trade item) | `N4+N6` |
| `3610`–`3615` | Net volume, gallons U.S. (variable measure trade item) | `N4+N6` |
| `3620`–`3625` | Logistic volume, quarts | `N4+N6` |
| `3630`–`3635` | Logistic volume, gallons U.S. | `N4+N6` |
| `3640`–`3645` | Net volume, cubic inches (variable measure trade item) | `N4+N6` |
| `3650`–`3655` | Net volume, cubic feet (variable measure trade item) | `N4+N6` |
| `3660`–`3665` | Net volume, cubic yards (variable measure trade item) | `N4+N6` |
| `3670`–`3675` | Logistic volume, cubic inches | `N4+N6` |
| `3680`–`3685` | Logistic volume, cubic feet | `N4+N6` |
| `3690`–`3695` | Logistic volume, cubic yards | `N4+N6` |
| `37` | Count of trade items or trade item pieces contained in a logistic unit | `N2+N..8` |
| `7004` | Active potency | `N4+N..4` |
| `8001` | Roll products (width, length, core diameter, direction, splices) | `N4+N14` |

#### Amounts, prices and coupon values (52 AIs)

| AI | GS1 description | Format |
|---|---|---|
| `3900`–`3909` | Applicable amount payable or Coupon value, local currency | `N4+N..15` |
| `3910`–`3919` | Applicable amount payable with ISO currency code | `N4+N3+N..15` |
| `3920`–`3929` | Applicable amount payable, single monetary area (variable measure trade item) | `N4+N..15` |
| `3930`–`3939` | Applicable amount payable with ISO currency code (variable measure trade item) | `N4+N3+N..15` |
| `3940`–`3943` | Percentage discount of a coupon | `N4+N4` |
| `3950`–`3955` | Amount Payable per unit of measure single monetary area (variable measure trade item) | `N4+N6` |
| `8005` | Price per unit of measure | `N4+N6` |
| `8111` | Loyalty points of a coupon | `N4+N4` |

#### Delivery, return and transport data (30 AIs)

| AI | GS1 description | Format |
|---|---|---|
| `420` | Ship to / Deliver to postal code within a single postal authority | `N3+X..20` |
| `421` | Ship to / Deliver to postal code with ISO country code | `N3+N3+X..9` |
| `4300` | Ship-to / Deliver-to company name | `N4+X..35` |
| `4301` | Ship-to / Deliver-to contact | `N4+X..35` |
| `4302` | Ship-to / Deliver-to address line 1 | `N4+X..70` |
| `4303` | Ship-to / Deliver-to address line 2 | `N4+X..70` |
| `4304` | Ship-to / Deliver-to suburb | `N4+X..70` |
| `4305` | Ship-to / Deliver-to locality | `N4+X..70` |
| `4306` | Ship-to / Deliver-to region | `N4+X..70` |
| `4307` | Ship-to / Deliver-to country code | `N4+X2` |
| `4308` | Ship-to / Deliver-to telephone number | `N4+X..30` |
| `4309` | Ship-to / Deliver-to GEO location | `N4+N20` |
| `4310` | Return-to company name | `N4+X..35` |
| `4311` | Return-to contact | `N4+X..35` |
| `4312` | Return-to address line 1 | `N4+X..70` |
| `4313` | Return-to address line 2 | `N4+X..70` |
| `4314` | Return-to suburb | `N4+X..70` |
| `4315` | Return-to locality | `N4+X..70` |
| `4316` | Return-to region | `N4+X..70` |
| `4317` | Return-to country code | `N4+X2` |
| `4318` | Return-to postal code | `N4+X..20` |
| `4319` | Return-to telephone number | `N4+X..30` |
| `4320` | Service code description | `N4+X..35` |
| `4321` | Dangerous goods flag | `N4+N1` |
| `4322` | Authority to leave | `N4+N1` |
| `4323` | Signature required flag | `N4+N1` |
| `4330` | Maximum temperature in Fahrenheit (expressed in hundredths of degrees) | `N4+N6+[-]` |
| `4331` | Maximum temperature in Celsius (expressed in hundredths of degrees) | `N4+N6+[-]` |
| `4332` | Minimum temperature in Fahrenheit (expressed in hundredths of degrees) | `N4+N6+[-]` |
| `4333` | Minimum temperature in Celsius (expressed in hundredths of degrees) | `N4+N6+[-]` |

#### Countries and regions of origin or processing (6 AIs)

| AI | GS1 description | Format |
|---|---|---|
| `422` | Country of origin of a trade item | `N3+N3` |
| `423` | Country of initial processing | `N3+N3+N..12` |
| `424` | Country of processing | `N3+N3` |
| `425` | Country of disassembly | `N3+N3+N..12` |
| `426` | Country covering full process chain | `N3+N3` |
| `427` | Country subdivision Of origin | `N3+X..3` |

#### Data about a person (10 AIs)

| AI | GS1 description | Format |
|---|---|---|
| `7250` | Date of birth (YYYYMMDD) | `N4+N8` |
| `7251` | Date and time of birth (YYYYMMDDhhmm) | `N4+N12` |
| `7252` | Biological sex | `N4+N1` |
| `7253` | Family name of person | `N4+X..40` |
| `7254` | Given name of person | `N4+X..40` |
| `7255` | Name suffix of person | `N4+X..10` |
| `7256` | Full name of person | `N4+X..90` |
| `7257` | Address of person | `N4+X..70` |
| `7258` | Baby birth sequence | `N4+N1+X1+N1` |
| `7259` | Baby of family name | `N4+X..40` |

#### Other product attributes and codes (15 AIs)

| AI | GS1 description | Format |
|---|---|---|
| `20` | Internal product variant | `N2+N2` |
| `242` | Made-to-Order variation number | `N3+N..6` |
| `7002` | UN/ECE meat carcasses and cuts classification | `N4+X..30` |
| `7005` | Catch area | `N4+X..12` |
| `7008` | Species for fishery purposes | `N4+X..3` |
| `7009` | Fishing gear type | `N4+X..10` |
| `7010` | Production method | `N4+X..2` |
| `7021` | Functional status | `N4+X..20` |
| `7022` | Revision status | `N4+X..20` |
| `7041` | UN/CEFACT freight unit type | `N4+X..4` |
| `7241` | AIDC media type | `N4+N2` |
| `8009` | Optically Readable Sensor Indicator | `N4+X..50` |
| `8012` | Software version | `N4+X..20` |
| `8030` | Digital Signature (DigSig) | `N4+Z..90` |
| `8200` | Extended Packaging URL | `N4+X..70` |

#### Internal and mutually agreed data (10 AIs)

| AI | GS1 description | Format |
|---|---|---|
| `90` | Information mutually agreed between trading partners | `N2+X..30` |
| `91`–`99` | Company internal information | `N2+X..90` |

