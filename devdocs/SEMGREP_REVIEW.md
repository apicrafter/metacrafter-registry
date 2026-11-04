# Semgrep Registry review (2026-11-04)

Research for issue
[#41 "Review Semgrep registry"](https://github.com/apicrafter/metacrafter-registry/issues/41).
The issue asks what the Semgrep Registry, a community-driven registry of
code-scanning rules, can teach a community-driven registry of semantic types
and detection rules.

Sources, all read on 2026-11-04:

- the [`semgrep/semgrep-rules`](https://github.com/semgrep/semgrep-rules)
  repository, branch `develop` at commit `16b9e6d` (2026-10-21);
- the Semgrep documentation at <https://docs.semgrep.dev>;
- the public registry endpoints `https://semgrep.dev/c/p/<ruleset>` and
  `https://semgrep.dev/api/registry/rulesets`;
- the [Semgrep Rules License](https://semgrep.dev/legal/rules-license) page;
- the [`opengrep/opengrep-rules`](https://github.com/opengrep/opengrep-rules)
  repository.

Registry numbers come from `metacrafter-registry stats` at commit `684e8e3`.
No Semgrep rule text is copied into this repository (see section 6).

## Summary

- **Semgrep ships rules. The registry ships types.**
  - A Semgrep rule holds detection logic, a message and metadata in one
    file.
  - In our ecosystem the same job is split in two. The registry says what a
    value means and what it looks like. metacrafter-rules says how
    metacrafter finds it. The rule `key` links the two.
- **The registry already matches Semgrep in most areas, and does better in
  some.**
  - Ids: registry ids do not depend on the file path, and aliases keep
    retired ids working. A Semgrep rule id contains its path, so moving a
    file changes the id.
  - Schema: the registry has a strict JSON Schema, checked on every file.
    Semgrep checks a loose metadata schema, and only on changed files.
  - Crosswalks: the registry maps to Wikidata, Schema.org, DPV, FIBO,
    Presidio, Google DLP, Purview, CDM, D3M and Sherlock. Semgrep maps to
    CWE, OWASP and ASVS.
  - Tests, playground and search: positive and negative examples, the
    `/identify` page, `/search` and `/quality` match what Semgrep offers.
- **Semgrep has three things we lack.**
  1. Curated **rulesets** that the scanner loads by name, for example
     `semgrep --config p/ci`. A ruleset serves a purpose, such as "few false
     positives" or "secrets". This is the main way people use the registry.
  2. A **one-click contribution path**: write a rule in the Playground,
     then "Publish to Registry", and Semgrep opens the pull request.
  3. **Detection metadata per rule** (`confidence`, `likelihood`,
     `impact`), which Semgrep uses to build low-noise rulesets.
- **The registry has no secrets.** The `generic/secrets/security/`
  directory of `semgrep-rules` has 50 rules that detect credential formats,
  for example GitHub tokens, AWS access key ids, Slack webhooks and PGP
  private key blocks. The registry has no `secrets` category and no record
  for any of these formats.
- **Two lessons in what not to copy.**
  - Licensing: in December 2024 Semgrep relicensed the community rules to
    the Semgrep Rules License v1.0. It allows internal use only and forbids
    redistribution and hosted services. The contributor license agreement
    (CLA) made this possible. The community fork of the rules is barely
    maintained.
  - Unreviewed publishing: 176 of the 305 public rulesets are personal packs
    (`<user>.<pack>`). 37 rulesets have "test", "demo", "poc" or "delme" in
    their name, and 108 have no description.

## 1. The Semgrep Registry in brief

[Semgrep](https://semgrep.dev) is a static analysis tool. It matches code
against rules written in YAML. The Semgrep Registry is the public catalog of
those rules:

| Part | What it is |
|---|---|
| `semgrep/semgrep-rules` | Git repository of the Community Edition rules: 1,291 stars and 618 forks. Rules sit in directories by language, such as `python/`, `generic/` and `terraform/`. Each rule has a test file next to it. |
| <https://semgrep.dev/r> | Search across Community and Pro rules |
| `https://semgrep.dev/r/<rule-id>` | Page for one rule |
| `https://semgrep.dev/p/<ruleset>` | Page for one ruleset |
| `https://semgrep.dev/c/p/<ruleset>` | The ruleset as one YAML config (`text/yaml`). The CLI downloads it for `--config p/<ruleset>`. |
| `https://semgrep.dev/c/r/<rule-id>` | One rule as a YAML config |
| `https://semgrep.dev/api/registry/rulesets` | JSON list of the 305 public rulesets, with author, tags, languages and CWE/OWASP statistics |
| Pro rules | Proprietary rules with cross-file and deep data-flow analysis. They are in the search but not in the repository. |

## 2. How a rule is defined

Each rule has `id`, `message`, `severity`, `languages` and a pattern. The
registry requires a `metadata` block. The repository validates it with
`metadata-schema.yaml.schm`:

- Always required: `category` and `technology`.
  - `category` is one of `security`, `correctness`, `best-practice`,
    `maintainability`, `portability`, `performance` or `accessibility`.
  - `technology` is a free list, such as `secrets` and `github`.
- Required when `category` is `security`: `cwe`, `likelihood`, `impact`,
  `subcategory` and `references`. The contribution guide adds `owasp`,
  `confidence` and `vulnerability_class`.
  - `confidence`, `likelihood` and `impact` are `LOW`, `MEDIUM` or `HIGH`.
  - `subcategory` is `vuln`, `audit` or `secure default`.
- Optional: `source`, `source-rule-url` and `asvs`. The metadata block
  itself is open, so rules also carry flags such as `cwe2022-top25`.

The published rule id is the file path joined with dots, then the rule's own
id. For example, the rule `detected-github-token` in
`generic/secrets/security/detected-github-token.yaml` is published as
`generic.secrets.security.detected-github-token.detected-github-token`.

The secret rules show the structure well. A typical one combines:

- a regex for the token format;
- an entropy check to drop low-randomness strings;
- `confidence: LOW`;
- `cwe` "CWE-798: Use of Hard-coded Credentials";
- `technology: [secrets, <vendor>]`;
- a `source-rule-url`, often the vendor's announcement of the token format
  or the TruffleHog regex list.

The registry has a regexp, examples and links in the same roles. It has no
counterpart for confidence, likelihood or impact.

## 3. Tests and CI

- **Tests.** Each rule file has a test file with the same name and an
  extension for the language. Comments mark the expected result of the
  next line:
  - `ruleid: <id>`: the rule must match (guards against false negatives);
  - `ok: <id>`: the rule must not match (guards against false positives);
  - `todoruleid: <id>` and `todook: <id>`: a known miss or a known false
    positive. It is recorded, but it does not fail the test.

  `semgrep test` runs them. Autofix rules also have a `.fixed` file with
  the expected result.
- **CI** (`.github/workflows/` in `semgrep-rules`):
  - `semgrep validate .` and `semgrep test .` on the latest Semgrep, plus
    jobs for the development and historical versions;
  - `validate-r2c-registry-metadata` validates the metadata of changed
    files only, with `jsonschema`;
  - `semgrep-rule-lints` runs Semgrep rules on the rules themselves. The
    `p/semgrep-rule-lints` ruleset finds unsatisfiable rules, duplicate ids,
    duplicate patterns and missing or empty messages and languages;
  - on merge, `update-semgrep-dev.yml` calls a semgrep.dev admin endpoint,
    and the site reloads the rules.
- **The loose schema shows in the data.** Most metadata keys are free-form,
  and the schema is checked only when a file changes. As a result, the
  statistics of one public ruleset (`minusworld.sql-injection`) count the
  same CWE twice: once as written and once with a trailing newline. They
  also list 19 of its rules as having no CWE.

The registry gates are stricter: `additionalProperties: false`, every file
checked on every build, and examples checked against the regexp. Semgrep's
`todoruleid` and `todook` have no counterpart. A contributor who knows that
a regexp misses a real value can only leave the example out (see R6).

## 4. Rulesets

Users rarely pick single rules. They pick rulesets:

| Ruleset | Rules on 2026-11-04 | Purpose |
|---|---|---|
| `p/default` | 1,073 | Default set of Semgrep AppSec Platform |
| `p/ci` | 159 | Few false positives, safe to block a CI pipeline |
| `p/secrets` | 52 | Secrets checked into version control |
| `p/gitleaks` | 175 | Rules ported from gitleaks |
| `p/owasp-top-ten`, `p/cwe-top-25` | | Rules mapped to a standard list |
| `p/python`, `p/django`, `p/terraform`, ... | | One language or framework |
| `--config=auto` | | Picks rulesets from the project's languages |

Of the 305 public rulesets, 129 are curated by Semgrep. The other 176 are
personal packs named `<user>.<pack>`. Any user can publish one, and no one
reviews them. Many are tests: `colleend.test`, `reeyaa.test2`,
`minusworld.django-test-delme`.

A ruleset is a list of rules with a name, a description, tags and an author.
Its purpose decides which rules it contains. Neither the language nor the
directory decides that alone. `p/ci` has rules in 20 languages, and every one
of them has `confidence: HIGH`.

The registry has no such unit. Its categories and countries describe what
a value is. They do not describe what a user wants to scan for. metacrafter
filters rules with `--contexts` and `--langs`, which correspond to
metacrafter-rules files. That is closer to Semgrep's language rulesets than
to `p/ci` or `p/secrets` (see R1).

## 5. Contribution and governance

- **Two paths in.**
  - The Playground: sign in, write or fork a rule, test it, then
    **Share** > **Publish to Registry**. The platform opens the pull request
    for the contributor.
  - A pull request to `semgrep-rules` with the rule and its test file.
    Contributors sign a CLA. A maintainer approves the pull request, and CI
    must pass.
- **Licensing history.**
  - From 2020 the rules were under LGPL 2.1 with the Commons Clause, which
    forbids selling the rules.
  - On 2024-12-13 Semgrep moved them to the Semgrep Rules License v1.0. The
    license allows use "only for your own internal business purposes". It
    forbids distribution and offering the rules to others as a service.
    The README says that contributors grant Semgrep a license under these
    terms.
  - Semgrep explained the change by companies that redistributed the rules
    against the earlier license. Several security vendors responded with
    [Opengrep](https://github.com/opengrep), a fork of the engine.
    `opengrep/opengrep-rules` keeps the rules as of 2024-12-13 under the
    earlier license. It has 6 stars, and its last push was on 2025-11-28.
- **Effect on the community.** The rules were written partly by outside
  contributors. Since the change, other tools may not redistribute them.
  The fork of the rules has not grown a community of its own. The CLA moved
  the right to relicense from the authors to one company.

The registry has no CLA. The repository, code and data, is under Apache-2.0.
Its section 5 says that a contribution is under the same license unless the
contributor states otherwise. One company cannot relicense the community's
records alone (see R5).

## 6. Semgrep Secrets and credential formats

Semgrep Secrets is a product of the Semgrep AppSec Platform. It finds
secrets with four methods:

- a regex for the token prefix and format;
- semantic analysis: data flow and constant propagation, so a secret is
  found after it is assigned to another variable;
- an entropy check;
- validators: a call to the service's API to check whether the secret is
  live. The results are "confirmed valid", "confirmed invalid", "validation
  error" and "no validator". Validation runs on the user's machine.

The community rules for secrets are of two kinds:

- Rules that find a hard-coded secret in code, for example a JWT secret
  passed to a library call. They describe code, not values, and are out of
  scope for the registry.
- Rules that find a value format, which is what a registry datatype
  describes. The `generic/secrets/security/` directory has 50 of them. The
  `p/secrets` ruleset contains 37 of these 50 and 15 rules of the first
  kind, 52 in all.

The 50 value-format rules:

| Group | Semgrep detectors (rule names) | In the registry |
|---|---|---|
| Cloud keys | AWS access key id, secret access key, session token, account id, AppSync GraphQL key, Amazon MWS auth token; Google API key, Cloud API key, Maps API key, OAuth client, OAuth access token, GCM service account; Heroku API key; SoftLayer API key | none |
| Code and package hosting | GitHub token, npm registry auth token, Artifactory token and password, Code Climate, SonarQube API key, Snyk API key, Sauce Labs token, HockeyApp | none |
| Messaging and SaaS | Slack token, Slack webhook, Outlook team webhook, Telegram bot API key, Twilio API key, Mailchimp API key, Mailgun API key, SendGrid API key, Facebook access token and OAuth, Kolide API key, Onfido live token, Picatic API key | none |
| Payments | Stripe API key and restricted key, Square access token and OAuth secret, PayPal Braintree access token | none |
| Keys and hashes | private key block (PEM), PGP private key block, bcrypt hash, `/etc/shadow` line | none. `private_key` exists, but it detects a field name only. |
| Generic | generic API key, generic secret, password in a URI, SSH password, JWT | none. `password` exists, but it has no format. |

These formats fit the registry well:

- Most have a fixed prefix (`ghp_`, `AKIA`, `xoxb-`, `sk_live_`), so a
  regexp finds them with few false positives.
- They matter for data, not only for code: tokens leak into CSV exports,
  logs and database columns, which is what metacrafter scans.
- They link the registry to secret scanners: Semgrep, gitleaks, TruffleHog
  and detect-secrets.

The regexps must not come from `semgrep-rules`, because its license forbids
redistribution. Use the vendors' own descriptions of their token formats and
projects under permissive licenses, such as gitleaks (MIT). The rule names
above are facts and are listed here only to show the gap (see R4).

## 7. Side by side

| Aspect | Semgrep Registry | Metacrafter registry | Verdict |
|---|---|---|---|
| Unit | Rule: detection logic, message, metadata | Datatype: meaning, format, examples. Detection is in metacrafter-rules. | Different by design. Keep the split. |
| Identity | Path plus rule id. Moving a file changes the id. | Flat id, independent of the path. Retired ids stay as aliases. | Registry is better |
| Schema | Loose metadata schema, changed files only | Strict JSON Schema and semantic gates on every file | Registry is better |
| Tests | Test file with `ruleid`, `ok`, `todoruleid` and `todook` | Positive and negative examples checked against the regexp | Equal, except known misses (R6) |
| Taxonomies | CWE, OWASP, ASVS | Wikidata, Schema.org, DPV, FIBO, Presidio, Google DLP, Purview, CDM, D3M, Sherlock | Registry is wider |
| Detection quality | `severity`, `confidence`, `likelihood`, `impact` | `is_pii` and `classification`. The quality score measures completeness, not precision. | Gap (R3) |
| Grouping | Curated rulesets by purpose | Categories and countries | Gap (R1) |
| Distribution | The CLI downloads a ruleset by name | metacrafter reads a rules checkout and filters by context and language | Gap (R1) |
| Playground | Write a rule, run it on code, publish it | `/identify`: paste values and rank datatypes. No path from there to a contribution. | Gap (R2) |
| Contribution | Pull request, or a pull request opened from the Playground. CLA required. | Pull request, or the "edit on GitHub" link on each page. No CLA, no issue forms. | Gap (R2) |
| Publishing by users | Unreviewed personal packs | Everything goes through review | Keep ours (R7) |
| License | Internal use only since 2024-12-13 | Apache-2.0 for code and data | Keep ours (R5) |
| Freshness | A merge triggers a reload of semgrep.dev | A merge triggers a Pages deploy | Equal |
| Statistics | CWE and OWASP counts per ruleset | `/quality`, `stats`, rule coverage | Equal |

## 8. Recommendations

- **R1. Add datatype packs.** A pack is a curated, named list of datatypes
  for one purpose, like a Semgrep ruleset.
  - Examples: credentials, special categories of personal data under GDPR,
    Russian personal data, and types that a checksum or a fixed prefix
    makes reliable.
  - Each pack gets a page, a JSON file under `/api/v1/packs/` with its
    datatypes, patterns and metacrafter-rules rule ids, and a Markdown twin.
  - metacrafter can then run `--pack <id>`, as Semgrep runs
    `--config p/<id>`. That is a separate change in metacrafter.
  - This pull request adds the OpenSpec proposal
    `openspec/changes/add-datatype-packs/`. Nothing is implemented yet.
- **R2. Make contributing easier.**
  - Done in this pull request:
    - GitHub issue forms to propose a datatype and to report a wrong record;
    - a pull request template with the checks CI runs;
    - in `CONTRIBUTING.md`, a link to the forms and the licensing of
      contributions.
  - Later: a "Propose a datatype" button on `/identify` when nothing
    matches. The page would fill a draft YAML record from the pasted values
    and open GitHub's "new file" page with it, so no backend is needed. This
    is our version of "Publish to Registry". It changes the site, so it
    should follow R1 or come as its own small change.
- **R3. Expose detection precision, but derive it. Do not ask contributors
  to set it.**
  - Semgrep's `confidence` belongs to a rule, not to the thing the rule
    finds. In our ecosystem that is metacrafter-rules. A `confidence` field
    per rule there would let metacrafter build a low-noise mode, like
    `p/ci`.
  - The registry can compute a precision hint from data it already has.
    28 records have a `checksum`. The Python client already measures how
    broad each regexp is: the share of other records' examples that it also
    matches (`_broadness` in `client.py`, used by `identify`). Publishing
    that number with each record would let users tell `^\d+$` from an IBAN.
    The "reliable types" pack in R1 is the first user of such a hint.
  - Do not add `likelihood`, `impact` or `severity` to records. They depend
    on the user's context. This is the same reason the Egeria review gave
    for not adding `matchThreshold` (`devdocs/RESEARCH_EGERIA_2026-11.md`,
    R5).
- **R4. Add a `secrets` category and credential datatypes.** This is a
  follow-up data task.
  - Add records for the formats in section 6 that have a public format
    description. Skip vague ones such as "generic secret". Mark the records
    `draft`, and verify each regexp against the vendor's documentation.
  - Take formats from vendor documentation and from permissive projects
    such as gitleaks. Do not take them from `semgrep-rules`.
  - Examples must be sample values that the vendor publishes, or values
    that cannot work. A real token must never be used, even a revoked one.
  - Mark the records `is_pii: false`. Add a `secrets` category so that
    users can scan for them on purpose.
  - Then add tool records for Semgrep and gitleaks, with the new types in
    `supported_types` (issue #31).
- **R5. Keep the licensing open, and keep it without a CLA.**
  - Contributions stay under Apache-2.0, as section 5 of the license says.
    `CONTRIBUTING.md` now states this (this pull request).
  - Do not ask contributors for a CLA. It would let one party relicense the
    community's work, as Semgrep did.
  - The maintainer may later choose a separate data license, for example
    CC0 or CC BY 4.0. The about page already notes that some descriptions
    quote Wikipedia under CC BY-SA 4.0. This review does not change the
    license.
- **R6. Allow known misses in examples, if contributors need them.**
  Semgrep's `todoruleid` and `todook` record that a rule misses a value, or
  matches one it should not, without failing CI. A registry example with,
  for example, `known_issue: true` would do the same for a regexp. It
  changes the data model, so it needs OpenSpec. Add it only when a
  contributor needs it.
- **R7. Do not copy these.**
  - Ids built from file paths: the registry's flat ids and aliases are
    safer for the URL contract.
  - Personal packs published without review: if the registry ever has
    community packs, they go through a pull request like any other record.
  - A CLA, or a license that limits redistribution.
  - Live validation of secrets: calling vendor APIs is the scanner's job,
    not the registry's. The registry's `checksum` stays offline.
- **R8. Test rules against registry examples (metacrafter-rules).**
  `semgrep test` checks every rule against its own fixtures. metacrafter-rules
  could run each rule against the registry examples for its `key`: positive
  examples must match, and negative examples must not. The examples are
  already published in `/api/v1/datatypes.jsonl`. This work belongs in
  metacrafter-rules.

## 9. Related issues

- #6 (closed): review of open source scanners. Semgrep, gitleaks and
  TruffleHog are secret scanners, a class that the review did not cover.
- #15: reading list. Add the Semgrep rule syntax and contribution guide.
- #31 (closed): catalog of tools. Semgrep and gitleaks tool records wait for
  R4.

## Sources

- Semgrep rules repository: <https://github.com/semgrep/semgrep-rules>
  (`README.md`, `CONTRIBUTING.md`, `LICENSE`, `metadata-schema.yaml.schm`,
  `.github/workflows/`, `generic/secrets/security/`)
- Contributing to Semgrep rules:
  <https://docs.semgrep.dev/contributing/contributing-to-semgrep-rules-repository>
- Running rules: <https://docs.semgrep.dev/running-rules>
- Testing rules: <https://docs.semgrep.dev/writing-rules/testing-rules>
- Semgrep Secrets overview:
  <https://docs.semgrep.dev/semgrep-secrets/conceptual-overview>
- Semgrep Rules License v1.0: <https://semgrep.dev/legal/rules-license>
- Ruleset list: <https://semgrep.dev/api/registry/rulesets>
- Rulesets as YAML: `https://semgrep.dev/c/p/<ruleset>` for `default`, `ci`,
  `secrets`, `gitleaks` and `semgrep-rule-lints`
- Opengrep rules fork: <https://github.com/opengrep/opengrep-rules>
- News on the relicensing and the fork:
  [InfoQ, February 2025](https://www.infoq.com/news/2025/02/semgrep-forked-opengrep),
  [The New Stack](https://thenewstack.io/opengrep-launches-as-free-fork-after-semgrep-license-shift/)
