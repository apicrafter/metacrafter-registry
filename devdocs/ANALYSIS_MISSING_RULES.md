# Analysis: Missing Rules in Metacrafter-Rules

## Executive Summary

**Total Datatypes in Registry:** 393  
**Datatypes with Rules:** 197  
**Datatypes Missing Rules:** 196 (50%)

This analysis identifies datatypes defined in the metacrafter-registry that do not have corresponding rules in the metacrafter-rules repository.

## Priority Recommendations

### High Priority (PII and Common Identifiers)

#### 1. US PII Rules (28 missing rules)
**Location:** `rules/US/`

**US_persons.yaml** - 9 rules needed:
- `usein` - US EIN (Employer Identification Number) - Pattern: `[0-9]{9}`
- `usitin` - US ITIN (Individual Taxpayer Identification Number) - Pattern: `(9\d{2})[- ]{1}((7[0-9]{1}|8[0-8]{1})|(9[0-2]{1})|(9[4-9]{1}))[- ]{1}(\d{4})`
- `usssn` - US Social Security Number - Pattern: `([0-9]{3})[- .]([0-9]{2})[- .]([0-9]{4})`
- `usatin` - US ATIN (Adoption Taxpayer Identification Number) - Pattern: `[0-9]{9}`
- `usptin` - US PTIN (Preparer Tax Identification Number)
- `uspassport` - US passport number - Pattern: `[0-9]{9}`
- `usnpi` - US National Provider Identifier (NPI)
- `usdeanumber` - USA DEA Registration Number - Pattern: `[a-zA-Z]{2}\d{7}|[a-zA-Z]{1}9\d{7}`
- `usdriverlic` - US driver license number - Complex pattern

**US_pii.yaml** - Same 9 rules as above (all PII)

**US_finances.yaml** - 2 rules:
- `cusip` - CUSIP code - Pattern: `^[0-9]{3}[a-zA-Z0-9]{2}[a-zA-Z0-9*@#]{3}[0-9]$`
- `abaroutingnum` - ABA routing number - Pattern: `[0123678]\d{3}-\d{4}-\d`

#### 2. GB (UK) Rules (17 missing rules)
**Location:** `rules/GB/`

**GB_persons.yaml** - 5 rules:
- `uknino` - UK National Insurance number
- `ukutr` - Unique Taxpayer Reference (UTR) - Pattern: `[0-9]{10}`
- `ukdriverlic` - UK driver license number - Pattern: `^[A-Z9]{5}\d{6}[A-Z9]{2}\d[A-Z]{2}$`
- `ukpassport` - British passport number - Pattern: `[0-9]{9}`
- `uknhsnum` - UK NHS Number - Pattern: `([0-9]{3})[- ]?([0-9]{3})[- ]?([0-9]{4})`

**GB_pii.yaml** - Same 5 rules as above

**GB_geo.yaml** - 3 rules:
- `uprn` - UK Unique Property Reference Number - Pattern: `\d{12}`
- `toid` - UK TOpographic IDentifier - Pattern: `\d{16}`
- `ukpostalcode` - UK Postal code

**GB_companies.yaml** - 1 rule:
- `companyhouseid` - Companies House company ID - Pattern: `(AC|FC|GE|GN|GS|IC|IP|LP|NA|NF|NI|NL|NO|NP|NR|NZ|OC|R|RC|SA|SC|SF|SI|SL|SO|SP|SR|SZ|ZC|[0-9]{2})[0-9RS]{6}`

**GB_finances.yaml** - 1 rule:
- `sedol` - SEDOL identifier - Pattern: `[0-9.]{7}`

#### 3. Russian (RU) Rules (24 missing rules)
**Location:** `rules/RU/`

**RU_persons.yaml** - 5 rules:
- `rupassport` - Russian passport foreign number
- `russurname` - Surname/Lastname in Russian
- `rusmidname` - Middle name in Russian
- `rusfullname` - Fullname of the person in Russian
- `rusfirstname` - First name in Russian

**RU_pii.yaml** - Same 5 rules as above

**RU_finances.yaml** - 4 rules:
- `rueqsecreg` - State registration number of equity securities - Pattern: `\d{1}\d{5}[A-Z]{1}`
- `rusbankaccount` - Bank account in Russia
- `rusecreg` - State registration number of additional issue - Pattern: `[0-9A-Z]{13}`
- `govlicaccount` - Personal account for government budgets - Pattern: `[0-9А-Я]{9,11}`

**RU_geo.yaml** - 2 rules:
- `rusregionname` - Russian region (federal subject) name
- `ruspostalcode` - Russian postal code

**RU_government.yaml** - 3 rules:
- `rnfi` - Russian government property ID (RNFI)
- `kvrname` - Russian budget expense type code name (KVR)
- `govlicaccount` - Personal account for government budgets

#### 4. French (FR) Rules (10 missing rules)
**Location:** `rules/FR/`

**FR_persons.yaml** - 4 rules:
- `frnir` - France National ID number (social number)
- `frcni` - French national identity card - Pattern: `^[0-9]{12}$`
- `frfullname` - French full name of the person
- `frpassport` - French passport number - Pattern: `^[0-9]{2}[A-z]{2}[0-9]{5}$`

**FR_pii.yaml** - Same 4 rules as above

**FR_companies.yaml** - 1 rule:
- `sirencode` - SIREN Code - Pattern: `\d{9}`

**FR_geo.yaml** - 1 rule:
- `frpostcode` - French postal code - Pattern: `\d{5}`

#### 5. Spanish (ES) Rules (9 missing rules)
**Location:** `rules/ES/`

**ES_persons.yaml** - 4 rules:
- `espassport` - Spanish passport number - Pattern: `^[A-z0-9]{2,3}[0-9]{6}$`
- `esnie` - Spanish Foreigner Identity Number (NIE) - Pattern: `^(X(-|\.)?0?\d{7}(-|\.)?[A-Z]|[A-Z](-|\.)?\d{7}(-|\.)?[0-9A-Z]|\d{8}(-|\.)?[A-Z])$`
- `esnif` - Spanish Tax identification number - Pattern: `[0-9]?[0-9]{7}[-]?[A-Z]`
- `esdriverlic` - Spain driver license number

**ES_pii.yaml** - Same 4 rules as above

**ES_geo.yaml** - 1 rule:
- `espostcode` - Spanish postal code - Pattern: `\d{5}`

### Medium Priority (Country-Specific Identifiers)

#### 6. Canadian (CA) Rules (11 missing rules)
**Location:** `rules/CA/`

**CA_persons.yaml** - 4 rules:
- `capassport` - Canadian passport number
- `cadriverlic` - Canada driver license number - Pattern: `^[A-Z](?:\d[- ]*){14}$`
- `caonohip` - Canada Ontario Health Insurance Plan (OHIP) number
- `cabcphn` - Canada British Columbia's Personal Health Number (PHN)

**CA_geo.yaml** - 3 rules:
- `caprovincecode` - Province of Canada alpha2 code - Pattern: `(NL|PE|NS|NB|QC|ON|MB|SK|AB|BC|YT|NT|NU)`
- `caprovince` - Province of Canada
- `casgc` - Standard Geographical Classification (SGC) - Pattern: `\d{2}(\d{2}(\d{3})?)`

#### 7. Australian (AU) Rules (9 missing rules)
**Location:** `rules/AU/`

**AU_persons.yaml** - 3 rules:
- `autfn` - Australian Tax File Number (TFN) - Pattern: `\d{3}\s\d{3}\s\d{3}`
- `aupassport` - Australian passport number
- `aumedicarenum` - Australian medicare number - Pattern: `[2-6]\d{3}\s\d{5}\s\d`

**AU_companies.yaml** - 2 rules:
- `auacn` - Australian Company Number (ACN) - Pattern: `\d{3}\s\d{3}\s\d{3}`
- `auabn` - Australian Business Number (ABN) - Pattern: `\d{2}\s\d{3}\s\d{3}\s\d{3}`

**AU_finances.yaml** - 1 rule:
- `aubsb` - Australia bank state branch (BSB) code - Pattern: `^[0-9]{3}-?[0-9]{3}$`

#### 8. German (DE) Rules (4 missing rules)
**Location:** `rules/DE/`

**DE_persons.yaml** - 2 rules:
- `depersonalausweis` - Germany national identity card - Pattern: `^[0-9]{12}$`
- `dedriverlic` - Germany driver license number

### Lower Priority (Smaller Countries)

#### 9. Swedish (SE) Rules (4 missing rules)
**Location:** `rules/SE/`

**SE_persons.yaml** - 2 rules:
- `sepassport` - Sweden passport number - Pattern: `^[0-9]{8}$`
- `sepersonnummer` - Sweden personal identity number - Pattern: `^[0-9]{2,4}[0-9]{2}(0[1-9]|1[0-2])(0[1-9]|[1-2][0-9]|3[0-1])[-+][0-9]{4}$`

#### 10. Other Countries

**Argentina (AR):** 1 rule - `ardni` - Argentina DNI  
**Belgium (BE):** 1 rule - `benatcardid` - Belgium national card ID  
**Brazil (BR):** 1 rule - `brcpf` - CPF number  
**Denmark (DK):** 1 rule - `dkcprnum` - CPR-Number  
**Finland (FI):** 1 rule - `fiidcard` - Finnish identity card  
**Singapore (SG):** 1 rule - `sgnric` - Singapore NRIC  
**Thailand (TH):** 1 rule - `thidcard` - Thai identity card  

**EU Rules:**
- `vatin` - EU VAT ID
- `eunuts` - NUTS code (EU)
- `eninumber` - ENI Number
- `eucin` - Craft Identification Number

## Implementation Guidelines

### Rule File Structure

Each rule file should follow this structure:

```yaml
name: {country}-{category}
description: {Description of the rules}
context: {category}
lang: {language_code}
country_code: {country_code}
rules:
  {rule_id}field:
    key: {datatype_id}
    is_pii: {True/False}
    name: {Rule name} by field name
    rule: {field_name_patterns}
    type: field
    match: text
  {rule_id}value:
    key: {datatype_id}
    is_pii: {True/False}
    name: {Rule name} by pattern
    match: ppr
    type: data
    rule: {pyparsing_pattern}
    maxlen: {max_length}
    minlen: {min_length}
```

### Pattern Conversion

When converting regexp patterns from datatypes to PyParsing rules:

1. **Simple patterns** can use `Word()` and `Literal()`
2. **Complex patterns** may need custom PyParsing expressions
3. **Field name rules** should include common field name variations in the target language

### Example: US SSN Rule

```yaml
ussnfield:
  key: usssn
  is_pii: True
  name: US Social Security Number by field name
  rule: ssn,social_security_number,ss_number,ssn_number
  type: field
  match: text
ussnvalue:
  key: usssn
  is_pii: True
  name: US Social Security Number by pattern
  match: ppr
  type: data
  rule: Word(nums, exact=3) + Optional(Literal('-') | Literal(' ') | Literal('.')) + Word(nums, exact=2) + Optional(Literal('-') | Literal(' ') | Literal('.')) + Word(nums, exact=4)
  maxlen: 11
  minlen: 9
```

## Next Steps

1. **Start with high-priority PII rules** (US, GB, RU, FR, ES)
2. **Create rule files** following the existing structure
3. **Test rules** against sample data
4. **Add field name variations** in appropriate languages
5. **Document patterns** and validation logic

## Notes

- Some datatypes appear in multiple categories (e.g., persons and pii) - create rules for both contexts
- Field name rules should include translations and common variations
- Pattern rules should handle optional separators (spaces, dashes, dots)
- Consider adding validators for complex patterns (like check digits)

