# qddate date patterns as registry types: review (2026-11-04)

Issue: [apicrafter/metacrafter-registry#12](https://github.com/apicrafter/metacrafter-registry/issues/12).

The issue asks to add the date patterns of qddate to the registry as data
types.

Source reviewed: [ivbeg/qddate](https://github.com/ivbeg/qddate) at tag
`v1.1.0`, commit `ec1f57aadb54c0bb92f44219ddf125782caadc26` (2026-11-04). This
is the release on PyPI. The patterns are in `qddate/patterns/` (`base.py` for
English, numeric and no-separator dates, one file per other language, and
`cjk.py`). All numbers below were computed with qddate 1.1.0 installed from
PyPI.

## Summary

- qddate 1.1.0 has **151 date patterns** (`qddate.patterns.ALL_PATTERNS`).
  Each has a key such as `dt:date:date_2`. 17 belong to no language (13
  numeric notations and 4 Chinese, Japanese and Korean ones), and 134 read a
  month or weekday name in one of 15 languages: English 34, Spanish, Italian,
  Portuguese and Russian 12 each, French 10, German and Dutch 8 each,
  Ukrainian 6, Czech, Polish, Romanian and Slovak 4 each, Bulgarian and
  Turkish 2 each.
- `DateParser` also generates variants of every pattern: a time after the
  date (`:time_1` to `:time_4`), a time before it (`:time_left`), and any
  text after the date (`:t_right`), for example
  `dt:date:date_2:time_1` for `25.12.2024 14:30`.
- **metacrafter** runs qddate on the string values of each column. When enough values match,
  it reports a `datetime` match whose `format` is the qddate key of the last
  matching pattern (`metacrafter/classify/processor.py`). Until now that key
  led nowhere in the registry.
- **Done in this change:**
  - New crosswalk key `mappings.qddate`. It holds qddate pattern keys; the
    schema accepts `dt:date:<name>` only, so generated variants are not
    mapped. `crosswalk("qddate", ...)` resolves a variant to its base pattern
    (`dt:date:date_2:time_1` gives the record of `dt:date:date_2`) and
    accepts a key without the `dt:date:` prefix (`date_2`).
  - **35 new draft patterns**: 30 of `date` and 5 of `monthday`. All 151
    qddate patterns are mapped, each to exactly one record (a test checks
    this). See [Mapping](#mapping-in-mappingsqddate).
  - New tool `qddate` (detector). A test checks that its `supported_types`
    are the records that carry `mappings.qddate`.
  - `scripts/check_qddate.py` checks the mappings against an installed
    qddate. It is not run in CI, because qddate is not a dependency of the
    registry. Run it after a qddate release.
- **Not done, on purpose:** the time patterns and the generated date-and-time
  variants get no records of their own. See [What is not mapped](#what-is-not-mapped).

## License

qddate is released under the BSD 3-Clause license, copyright Ivan Begtin.
The registry copies no code from it. The regexps of the new records were
written for the registry and checked against the qddate grammars (see
[How the records were checked](#how-the-records-were-checked)); the month
names in them are the ordinary names of the months in each language.

## One record per notation, not per pattern

qddate has many patterns for one notation, because a pyparsing grammar has to
spell out every variant: the month name capitalised (`de_base`) or in lower
case (`de_base_lc`), full or abbreviated (`de_short`), with a weekday
(`de_weekday`) or an article (`es_base_article`), day first or month first
(`es_rare_1`). These variants do not change what a value means or how it is
read, so one registry record per notation is enough:

- **Numeric dates:** one record per field order and separator, because
  `25.12.2024`, `25/12/2024`, `12/25/2024` and `2024-12-25` need a different
  format string. A two-digit year is a record of its own (`date_dmy_dot_yy`),
  because the century has to be inferred.
- **Dates with a month name:** one record per language (`date_german`,
  `date_russian`, ...). The month name fixes the order of day and month, so
  the order does not need a record of its own. English is one record too,
  for both `5 May 2022` and `May 5, 2022`.
- **Dates with units:** `date_cjk` for Chinese and Japanese (`2024年12月25日`)
  and `date_korean` (`2024년 12월 25일`), whose units differ.
- **Dates without a year** are patterns of `monthday`, not of `date`.

Record ids name the field order and separator (`date_dmy_dot`, `date_ymd_dash`)
or the language (`date_english`), as the AutoType benchmark does
(`date-german`, `date-chinese`). A language record has no country, because a
language is written in several countries, so all records are in
`data/datatypes/any/datetime/`.

## Mapping (in `mappings.qddate`)

| Record | Example | qddate keys (without `dt:date:`) |
|---|---|---|
| `date_dmy_dot` | 25.12.2024 | `date_2` |
| `date_dmy_dot_yy` | 25.12.24 | `date_4`, `date_4_point` |
| `date_dmy_slash` | 25/12/2024 | `date_1` |
| `date_dmy_slash_yy` | 25/12/24 | `date_8` |
| `date_dmy_dash` | 25-12-2024 | `date_iso8601` |
| `date_dmy_dash_yy` | 25-12-24 | `date_iso8601_short` |
| `date_mdy_slash` | 12/25/2024 | `date_usa` |
| `date_mdy_slash_yy` | 12/25/24 | `date_usa_1` |
| `date_ymd_dash` | 2024-12-25 | `date_9` |
| `date_ymd_slash` | 2024/12/25 | `date_3` |
| `date_ymd_dot` | 2024.12.25 | `date_10` |
| `date_ymd_compact` | 20241225 | `date_6` |
| `date_dmy_compact` | 25122024 | `date_5` |
| `monthday_dm_dot` | 25.12 | `noyear_1` |
| `date_cjk` | 2024年12月25日 | `date_cjk` |
| `date_korean` | 2024년 12월 25일 | `date_cjk_ko` |
| `monthday_cjk` | 12月25日 | `date_cjk_noyear` |
| `monthday_korean` | 12월 25일 | `date_cjk_ko_noyear` |
| `date_english` | 25 December 2024 | `date_eng1`, `date_eng1x`, `date_eng1_lc`, `date_eng1_short`, `date_eng2`, `date_eng2_lc`, `date_eng2_short`, `date_eng3`, `date_eng3_nolc`, `date_eng4_short`, `weekday_eng`, `weekday_eng_lc`, `weekday_eng_wshort`, `weekday_eng_mshort_wshort`, `weekday_eng_iso`, `weekday_short_eng_iso`, `weekday_eng_mixed`, `date_eng_abbrev1`, `date_eng_abbrev2`, `date_eng_abbrev3`, `weekday_eng_abbrev1`, `weekday_eng_abbrev2`, `weekday_eng_abbrev3`, `weekday_eng_us`, `weekday_eng_wshort_us`, `weekday_eng_abbrev_wshort_us`, `date_eng_abbrev_postfix`, `date_eng5`, `date_eng6`, `date_eng4` |
| `monthday_english` | May 5 | `date_eng_noyear_md`, `date_eng_noyear_dm` |
| `date_german` | 25. Dezember 2024 | `de_base`, `de_base_lc`, `de_weekday`, `de_weekday_lc`, `de_short`, `de_short_lc`, `de_rare_1`, `de_rare_2` |
| `date_spanish` | 25 de diciembre de 2024 | `es_base`, `es_base_lc`, `es_base_article`, `es_base_lc_article`, `es_rare_1`, `es_rare_2`, `es_short`, `es_short_lc`, `es_short_monthfirst`, `es_short_lc_monthfirst`, `es_weekday`, `es_weekday_lc` |
| `date_french` | 25 décembre 2024 | `fr_base`, `fr_base_lc`, `fr_base_article`, `fr_base_lc_article`, `fr_short`, `fr_short_lc`, `fr_short_monthfirst`, `fr_short_lc_monthfirst`, `fr_weekday`, `fr_weekday_lc` |
| `date_italian` | 25 dicembre 2024 | `it_base`, `it_base_lc`, `it_base_article`, `it_base_lc_article`, `it_rare_1`, `it_rare_2`, `it_weekday`, `it_weekday_lc`, `it_short`, `it_short_lc`, `it_short_monthfirst`, `it_short_lc_monthfirst` |
| `date_dutch` | 5 mei 2022 | `nl_base`, `nl_base_lc`, `nl_weekday`, `nl_weekday_lc`, `nl_short`, `nl_short_lc`, `nl_rare_1`, `nl_rare_2` |
| `date_polish` | 25 grudnia 2024 | `pl_base`, `pl_base_lc`, `pl_gen`, `pl_gen_lc` |
| `date_portuguese` | 25 de dezembro de 2024 | `pt_base`, `pt_base_lc`, `pt_base_article`, `pt_base_lc_article`, `pt_short`, `pt_short_lc`, `pt_short_monthfirst`, `pt_short_lc_monthfirst`, `pt_weekday`, `pt_weekday_lc`, `pt_weekday_short`, `pt_weekday_short_lc` |
| `date_romanian` | 25 decembrie 2024 | `ro_base`, `ro_base_lc`, `ro_short`, `ro_short_lc` |
| `date_russian` | 25 декабря 2024 | `date_rus`, `date_rus2`, `date_rus3`, `date_rus_lc1`, `date_rus_lc2`, `weekday_rus`, `weekday_rus_lc1`, `rus_rare_2`, `rus_rare_3`, `rus_rare_5`, `rus_rare_6` |
| `monthday_russian` | 25 декабря | `date_rus_noyear` |
| `date_ukrainian` | 25 грудня 2024 | `uk_base`, `uk_base_lc`, `uk_gen`, `uk_gen_lc`, `uk_short`, `uk_short_lc` |
| `date_bulgarian` | 25 декември 2024 | `bg_base`, `bg_base_lc` |
| `date_turkish` | 25 Aralık 2024 | `tr_base`, `tr_base_lc` |
| `date_czech` | 25. prosince 2024 | `cz_base`, `cz_base_lc`, `cz_gen`, `cz_gen_lc` |
| `date_slovak` | 25. decembra 2024 | `sk_base`, `sk_base_lc`, `sk_gen`, `sk_gen_lc` |

Notes:

- **`date_rus3`** reads a numeric date followed by the Russian year word
  (`05.05.2022 г.`). It is mapped to `date_russian`, not to `date_dmy_dot`,
  because the year word is Russian text.
- **`weekday_eng_iso` and `weekday_short_eng_iso`** read an English weekday
  before a numeric date (`Monday, 25/12/2024`). They are mapped to
  `date_english` for the same reason.
- **Ambiguous numeric dates.** `date_dmy_slash` and `date_mdy_slash` have the
  same shape. A value whose first two numbers are both 12 or less, such as
  `05/06/2024`, matches both regexps; qddate reads it as day first
  (`date_1`). A column usually tells them apart with one value above 12.
- **Words shared by languages.** `5 September 2022` matches `date_english`
  and `date_slovak`, and `5 May 2022` matches `date_english` and
  `date_spanish` (`May` is the Spanish abbreviation of `mayo`). qddate
  prefers English in both cases.

## How the records were checked

Each regexp was written from the qddate grammar of its patterns and then
checked with qddate 1.1.0:

1. Every positive example of every record is read by `DateParser().match()`
   with one of the record's keys, and every negative example fails the
   regexp. `scripts/check_qddate.py` repeats this check.
2. For each of the 151 patterns, one or more sample values (184 in all) were
   parsed by that pattern's own grammar, and the record's regexp matches
   them, except for the forms listed in the next section.
3. Every month name that qddate's patterns use in a language matches the
   language record in a `5 <month> 2022` date: 672 forms, counting the full
   and abbreviated, capitalised and lower-case, nominative and genitive
   forms as `MONTHS_BY_LANGUAGE` lists them. `scripts/check_qddate.py`
   repeats this check too.

The regexps check the range of the day (1 to 31) and the month (1 to 12),
which qddate does when it converts a match to a date, not when it matches.

## What the regexps leave out

The registry regexps describe the usual written form of each notation. They
leave out some inputs that qddate accepts:

- **Whitespace.** pyparsing skips whitespace between tokens, so qddate also
  reads `25. 12. 2024` and `5 . May 2022`. The regexps allow a space only
  where the notation has one.
- **Spaces instead of slashes.** `date_1`, `date_3` and `date_8` also read
  `25 12 2024`, `2024 12 25` and `25 12 24`. The regexps of
  `date_dmy_slash`, `date_ymd_slash` and `date_dmy_slash_yy` take the slash
  form only: three numbers separated by spaces are rarely a date.
- **Capitals.** qddate reads English month names in any case (`5 MAY 2022`).
  The regexps take capitalised and lower-case names only (`May`, `may`).
- **`25Dec20`.** `date_eng4_short` reads the day, month and year without
  hyphens; the regexp needs the hyphens (`25-Dec-20`).
- **Italian with `de`.** `it_base_article` and `it_base_lc_article` read
  `5 de maggio de 2022`, which is not Italian (see finding 2). The regexp of
  `date_italian` leaves it out.
- **`rus_rare_6`** reads a weekday before a month-first date
  (`четверг, мая 5, 2022`), which is not a usual Russian form. The regexp of
  `date_russian` leaves it out.
- **Bulgarian look-alike letters.** `bg_base` also reads month names written
  with Latin letters that look Cyrillic (`Мapт`). The regexp takes Cyrillic
  only.
- **Weekdays and times after CJK dates.** The CJK patterns accept a time
  written with units (`14時30分`) after the date. The regexps of `date_cjk`
  and `date_korean` take the date and an optional weekday, not a time.

The regexps of `date_bulgarian` and `date_ukrainian` accept the year word
after the date (`25 декември 2024 г.`, `25 грудня 2024 р.`). qddate's grammars
for these languages do not include it, but `DateParser().match()` reads such
values with the base pattern and ignores the rest.

## What is not mapped

- **Generated variants** (`:time_1` ... `:time_4`, `:time_left`, `:t_right`).
  They are a date notation with a time or other text around it. The schema
  rejects their keys in `mappings.qddate`, and `crosswalk` resolves them to
  the record of their date part. A value such as `25.12.2024 14:30` is a
  `datetime`; the registry has no record per date-and-time notation yet.
- **Time patterns** (`BASE_TIME_PATTERNS`: `pat:time:minutes`,
  `pat:time:ampm`, `pat:time:timezone` and others). qddate uses them only
  inside the generated variants; they are not patterns that `match()`
  reports. The registry has `time`, `timezone` and `utctimezoneoffset` for
  these values.
- **Relative dates** (`qddate/relative.py`: `yesterday`, `3 дня назад`).
  They are not notations of a calendar date.

## Findings in qddate

These do not block the mapping. They are worth fixing in qddate:

1. **`dt:date:date_iso8601` is not ISO 8601.** It reads `25-12-2024`
   (day, month, year); ISO 8601 writes the year first, which `dt:date:date_9`
   reads. `date_iso8601_short` reads `25-12-24`. The names mislead readers
   of metacrafter's output; the registry maps them to `date_dmy_dash` and
   `date_dmy_dash_yy`.
2. **Italian article patterns expect `de`.** `it_base_article` and
   `it_base_lc_article` read `5 de maggio de 2022`, a Spanish or Portuguese
   form. Italian writes `5 maggio 2022`, or `il 5 maggio 2022` with the
   article; qddate reads neither `il 5 maggio 2022` nor `5 di maggio 2022`.
3. **Wrong `format` strings.** `es_rare_1`, `es_rare_2`, `it_rare_1` and
   `it_rare_2` declare `%M %d %Y`; in `strftime`, `%M` is minutes, and these
   patterns read a month name (`%B`). `date_iso8601_short` declares
   `%d-%m-%Y` for a two-digit year (`%y`).
4. **Lower-case Russian weekday.** `weekday_rus_lc1` reads a lower-case month
   but a capitalised weekday only: `Четверг, 5 мая 2022 г.` is read,
   `четверг, 5 мая 2022 г.` is not.
5. **Unused month tables.** The Turkish abbreviations (`Oca`, `Şub`, ...)
   are in `MONTHS_BY_LANGUAGE`, but no pattern uses them, so `5 Oca 2022`
   is not read. The same holds for the Russian, Polish and Bulgarian
   abbreviations.
6. **French `1er`.** French writes the first day of a month as `1er`
   (`1er mai 2022`); qddate does not read it.

## Recommendations and follow-ups

1. **metacrafter:** link a qddate match to the notation record. With the
   `format` key, `crosswalk("qddate", format)` gives the record, for example
   `date_dmy_dot`, whose page and JSON say what the column holds.
2. **Registry `identify`:** `identify` also tries a value without hyphens and
   spaces, so `2024-12-25` used to match every `\d{8}` regexp (`am_tin`,
   `okpo`, ...), and those stable records outranked the draft
   `date_ymd_dash`. Commit `b32688d` on `main` fixed this: a compact-form
   hit no longer counts when a regexp at least as specific matches the value
   as written, and `date_ymd_dash` now ranks first for ISO dates. A column of
   `20241225` values still ranks the eight-digit codes first: without
   separators, a date and an eight-digit code look alike.
3. **Records per date-and-time notation** (`datetime` patterns such as
   `YYYY-MM-DDTHH:MM:SS`) would give the generated variants a record of
   their own. They need a decision on how many time forms to list.
4. **qddate:** the findings above. When qddate adds or renames a pattern,
   run `scripts/check_qddate.py` and map the new keys.
