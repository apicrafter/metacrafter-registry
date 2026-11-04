# Sherlock semantic types: review (2026-11-04)

Issue: [apicrafter/metacrafter-registry#37](https://github.com/apicrafter/metacrafter-registry/issues/37).

The issue asks to review the 78 semantic types of
[Sherlock](https://sherlock.media.mit.edu/), add the missing ones to the
registry, and create a Sherlock profile in the tools section.

Sources reviewed:

- The list of class labels of the trained model,
  `model_files/classes_sherlock.npy` of
  [mitmedialab/sherlock-project](https://github.com/mitmedialab/sherlock-project)
  at commit `f194013e795d90bc63553a2c47bb33f56c1c7b53` (2023-06-09, the head
  of `master`). The repository is licensed MIT. The file is a pickled NumPy
  array; its 78 strings were read with `pickletools`, without unpickling it.
- The paper: Hulsebos et al., "Sherlock: A Deep Learning Approach to Semantic
  Data Type Detection", KDD 2019 (`docs/assets/2019-Sherlock-KDD.pdf` in the
  same repository): section 3 (data) and Table 7 (the 78 types).
- The spreadsheet attached to the issue, also kept in
  `archive/analysis/sherlock/sherlock_datatypes.xlsx`. It lists example values
  for each type and a label for the kind of values (Categorical, Numeric,
  Context-Specific, ...). The archived copy has a second sheet, `registry`,
  with a first mapping to registry ids made in 2022.

## Summary

- Sherlock has **78 semantic types**. They are DBpedia properties from the
  T2Dv2 Gold Standard. The training data are the columns of the VizNet corpus
  whose header matched a type name, so a type is a column header word, not a
  definition of a value. The model returns labels such as `city`,
  `birth Date` and `file Size`. The paper writes them as `City`, `Birth date`
  and `File size`.
- Many types are generic header words. The spreadsheet shows that one type
  can hold very different values: `position` holds race positions (`8.0`) and
  job titles (`Director`); `result` holds numbers, `Win`/`Loss` and sentences;
  `order` holds weekdays and numbers.
- **Done in this change:**
  - The crosswalk key `mappings.sherlock` holds Sherlock labels as the model
    returns them. The schema lists the 78 labels and rejects any other value.
  - 32 Sherlock types are mapped to 30 records, only where the record has the
    same meaning as the type. A Sherlock type maps to at most one record (a
    test checks this).
  - 6 new draft records for types the registry did not have: `birthplace`,
    `brand`, `religion`, `weight`, `elevation` and `species`. The FTA review
    (issue #38, `devdocs/FTA_REVIEW.md`) added `industry` and `language` at the
    same time; they now carry the Sherlock mapping too.
  - `crosswalk("sherlock", ...)` ignores case and spaces, so `birth Date`,
    `Birth date` (the paper) and `birthDate` (Sato) all return `birthday`.
  - New tool record `sherlock` (category `detector`). Its `supported_types` are
    the 30 mapped records; a test keeps the two lists equal.
- **Not done, on purpose:** records for the other 46 types. They are generic
  header words, roles over person or organization names, or types whose
  values have several unrelated meanings. See
  [Sherlock types with no registry equivalent](#sherlock-types-with-no-registry-equivalent).

## Mapping to existing records

| Sherlock type | Registry id | Note |
|---|---|---|
| `address` | `address` | |
| `age` | `age` | |
| `birth Date` | `birthday` | `birthday` is the date of birth (CDM `means.demographic.birthDate`). |
| `category` | `category` | |
| `city` | `city` | |
| `company` | `orgname` | |
| `organisation` | `orgname` | |
| `continent` | `continent` | The spreadsheet shows continent codes (`EU`, `AS`); `continent` covers names and codes. |
| `country` | `country` | |
| `creator` | `dc_creator` | The Dublin Core element has the same meaning: the person or organization that made a resource. |
| `publisher` | `dc_publisher` | Same reason as `creator`. |
| `currency` | `currency` | |
| `description` | `description` | |
| `duration` | `duration` | |
| `file Size` | `filesize` | |
| `gender` | `gender` | |
| `sex` | `gender` | See the note below. |
| `genre` | `genre` | |
| `industry` | `industry` | Added by the FTA review. Names of sectors; the codes are `isicrev4`, `eu_nace`, `naicscode` and `okved`. |
| `isbn` | `isbn` | `isbn10` and `isbn13` are separate records; the type maps to the general one. |
| `language` | `language` | Added by the FTA review. Language names or codes; this change adds links to Wikipedia, the Wikidata item Q34770 and Schema.org `Language`. |
| `name` | `name` | |
| `nationality` | `nationality` | |
| `notes` | `comment` | The record is "Comment / Note". |
| `person` | `person_fullname` | |
| `year` | `year` | |

Notes on the mapping:

- **Sex and gender.** The registry has one record, `gender`, for the gender or
  sex flag of a person, and datasets use both header words for the same `M` /
  `F` values. So both Sherlock types map to `gender`. A separate `sex` record
  would need a maintainer decision.
- **Name and person.** `name` is any name (of a person, a place, a product).
  `person` is a person's name. The 2022 sheet mapped both to
  `person_fullname`; here `name` maps to the general `name` record.

## New records

All are drafts. Each has a description written for the registry, examples, a
Wikipedia link and, where one exists, a Wikidata property and a Schema.org
term that were checked.

| Sherlock type | New id | Category | Wikidata | Schema.org | Note |
|---|---|---|---|---|---|
| `birth Place` | `birthplace` | persons, pii, geo | P19 (place of birth) | `birthPlace` | `is_pii: true` |
| `brand` | `brand` | companies, ecommerce | P1716 (brand) | `brand` | |
| `religion` | `religion` | persons, pii | P140 (religion or worldview) | | `is_pii: true`; a special category of personal data under the GDPR |
| `weight` | `weight` | values, common | P2067 (mass) | `weight` | Child of `numeric`. The regexp matches only values with a unit (kg, g, mg, lb, lbs, oz) |
| `elevation` | `elevation` | geo, values | P2044 (elevation above sea level) | `elevation` | Child of `numeric`. No regexp: a plain number cannot be told apart from other numbers |
| `species` | `species` | science | | | Scientific or common names. Links to the Wikidata item Q7432 |

`species` has no Wikidata property mapping on purpose: P225 (taxon name)
covers taxa of every rank, not only species. For the same reason `language`
gets no property mapping: P407 (language of work or name) and P1412 (languages
spoken) are narrower.

## Sherlock types with no registry equivalent

| Group | Sherlock types | Closest registry records | Why not mapped |
|---|---|---|---|
| Roles over person names | `artist`, `director`, `jockey`, `owner` | `person_fullname` (`owner` can also be `orgname`) | The type says what role a person has, not what the value is. A record per role would duplicate `person_fullname`. |
| Roles over organization names | `affiliate`, `affiliation`, `manufacturer`, `operator` | `orgname` | Same reason. |
| Geography | `state`, `county`, `region` | `usstate`, `uscounty`, `rusregion`, `nutsregion`, `wbregion` | The registry has only country-specific records. The 2022 sheet mapped `state` to `usstate` and `county` to `uscounty`, but Sherlock does not limit the types to the US. See recommendation 1. |
| Geography roles | `location`, `origin` | `address`, `country` | `location` holds venue names (`VBC Arena`); `origin` is a country of origin, a role over `country`. |
| Generic header words | `class`, `classification`, `code`, `collection`, `command`, `component`, `credit`, `family`, `format`, `order`, `range`, `result`, `service`, `status`, `symbol`, `type` | `category` | Too general: the values depend on the dataset. `family` holds religious denominations in the spreadsheet; `range` holds time periods (`Last week`) and money amounts; `symbol` holds shapes and `$` signs. |
| Counts, ranks and measures | `area`, `capacity`, `depth`, `plays`, `position`, `rank`, `ranking`, `sales` | `numeric`, `quantity`, `score`, `jobtitle` | Mostly plain numbers with no unit, so the type cannot be told from the value. `area` also holds region names and `position` job titles. The paper reports `sales` and `ranking` as the two worst types (F1 0.514 and 0.468). |
| Names of works, products and groups | `album`, `product`, `team`, `team Name`, `club` | `name` | Free-text names (or team codes such as `HOU`). They could become records later; see recommendation 2. |
| Other | `day`, `education`, `grades`, `requirement` | `dayofweek`, `date`, `academicdegree`, `description` | `day` holds weekday names and dates; the registry's `day` record is a Chinese day name. `education` holds degrees in the spreadsheet (`Ph.D.`, `MA`), but an education level is broader than an academic degree. `grades` holds US school grade spans (`K-5`). `requirement` holds sentences. |

## Recommendations and follow-ups

1. **Generic first-level subdivision record.** This is the same decision as
   recommendation 1 of `devdocs/D3M_REVIEW.md` (D3M `State`). Sherlock adds
   `county` and `region`. A generic record for each level would let them be
   mapped.
2. **Names of creative works and products.** `album`, `product` and
   `team Name` could become records (for example `product_name`), with
   Schema.org `Product` and `MusicAlbum` links. They are free text, so they
   would have no regexp.
3. **Sato (issue #33).** Sato's `type78` list (`configs/types.json` of
   megagonlabs/sato at commit `c19ace3`) is the same 78 types, written in
   camelCase (`birthDate`, `fileSize`, `teamName`). `crosswalk("sherlock",
   ...)` already resolves these labels, so issue #33 can reuse
   `mappings.sherlock`. Done: see `devdocs/SATO_REVIEW.md`.
4. **Re-check is unlikely to be needed.** The model's class list is fixed by
   the published weights. The last commit on `master` is from June 2023.
