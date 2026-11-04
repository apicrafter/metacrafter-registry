# Sato semantic types: review (2026-11-04)

Issue: [apicrafter/metacrafter-registry#33](https://github.com/apicrafter/metacrafter-registry/issues/33).

The issue asks to add [Sato](https://github.com/megagonlabs/sato), a research
model for semantic type detection in tables, as a tool, and to add the
semantic types that Sato supports.

Sources reviewed, all at
[megagonlabs/sato](https://github.com/megagonlabs/sato) commit
`c19ace3bc7d216dbb3442e2d6c7794df097ba1f7` (2021-08-30, the head of `master`).
The repository is licensed Apache 2.0.

- `README.md`: what Sato is, and the setup, which sets `TYPENAME='type78'`.
- `configs/types.json`: the type lists. `utils.get_valid_types(TYPENAME)`
  reads the list named by `TYPENAME`.
- `demo/predict.py` and `demo/pretrained_sato/model.pt`: the published model
  and the code that turns its output into labels. The model file is a pickled
  PyTorch state dict; its tensor shapes were read with `pickletools`, without
  unpickling it.
- The paper: Zhang et al., "Sato: Contextual Semantic Type Detection in
  Tables", PVLDB 13(12), 2020, <https://doi.org/10.14778/3407790.3407793>.
- The Sherlock review, `devdocs/SHERLOCK_REVIEW.md` (issue #37).

## Summary

- Sato extends Sherlock. Its column network is the Sherlock network plus an
  LDA topic vector of the whole table. A conditional random field (CRF) then
  predicts the types of all columns of a table together. So Sato uses the
  table context, while Sherlock looks at one column at a time.
- **Sato predicts the same 78 semantic types as Sherlock.** The published
  model uses the `type78` list. The CRF of `model.pt` has 78 tags (its
  `transitions` tensor is 78 x 78), and the prediction code maps the output
  back to the labels of the list named by `TYPENAME` with a `LabelEncoder`.
- The `type78` labels are the Sherlock labels in camelCase: `birthDate`,
  `birthPlace`, `fileSize` and `teamName`, where Sherlock writes `birth Date`,
  `birth Place`, `file Size` and `team Name`. The other 74 labels are the same
  lowercase words. `type78_raw` holds the paper's spelling (`Birth date`,
  `ISBN`, `Collection ` with a trailing space). Without case and spaces, both
  lists are equal to the 78 labels of `mappings.sherlock`.
- **Done in this change:**
  - New tool record `sato` (category `detector`). Its `supported_types` are
    the 30 records that carry `mappings.sherlock`, the same list as the
    `sherlock` tool. A test keeps the two lists equal.
  - `crosswalk("sato", label)` resolves a Sato label through
    `mappings.sherlock`: `crosswalk("sato", "birthDate")` returns `birthday`.
    The MCP `crosswalk` tool accepts `sato` too. A test checks that every
    `type78` label gives the same result as the Sherlock crosswalk.
  - A test checks that the 78 Sato labels, compared without case and spaces,
    are the 78 Sherlock labels of the schema.
  - The record page labels the mapping "Sherlock and Sato".
- **No new mapping key.** A `mappings.sato` key would repeat
  `mappings.sherlock` on the same 30 records. If Sato and Sherlock ever
  disagree on a type, a separate key can be added then.
- **No new records.** The 8 records that Sherlock types needed were added by
  the Sherlock and FTA reviews. The 46 Sherlock types that have no registry
  record were checked again against the 259 records added since the Sherlock
  review. None of them has the same meaning as one of those types. For example, the new
  `state` record is a state of India, and the Sherlock `state` type is not
  limited to one country.

## Mapping

The mapping is the Sherlock mapping in `devdocs/SHERLOCK_REVIEW.md`. Only the
four labels below are spelled differently in Sato; `crosswalk` ignores case
and spaces, so both spellings resolve.

| Sato label | Sherlock label | Registry id |
|---|---|---|
| `birthDate` | `birth Date` | `birthday` |
| `birthPlace` | `birth Place` | `birthplace` |
| `fileSize` | `file Size` | `filesize` |
| `teamName` | `team Name` | not mapped |

## Other type lists in `configs/types.json`

The file also has `type117` (with `type117_raw`), `type123` and `type274`.
They are lists of DBpedia property names, such as `deathDate`, `zipCode`,
`timeZone` and `iataAirlineCode`. The published model, the train and test
splits (`extract/out/train_test_split/*_type78*.json`) and the corpus mapping
(`configs/data_name_mapping.json`, keys `*_type78`) use only `type78`. The
repository has no model or split for the other lists. They are not imported,
because no published Sato model predicts them.

## Recommendations and follow-ups

1. **Same follow-ups as Sherlock.** The recommendations of
   `devdocs/SHERLOCK_REVIEW.md` apply to Sato unchanged: a generic
   first-level subdivision record (for `state`, `county`, `region`) and
   records for names of creative works and products (`album`, `product`,
   `team Name`). Each mapping added for Sherlock is a Sato mapping too.
2. **Keep the two tools in step.** The `sato` and `sherlock` tools list the
   same records. When a record gets `mappings.sherlock`, add it to both
   tools; the tests fail otherwise.
3. **Re-check is unlikely to be needed.** The last commit on `master` is from
   August 2021, and the type list is fixed by the published model.
