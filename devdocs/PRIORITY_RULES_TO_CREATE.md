# Priority Rules to Create - Action Plan

Based on the analysis of 393 datatypes in the registry, here are the **top priority rules** to create, organized by country and category.

## Top 5 Priority Countries (196 missing rules total)

### 1. 🇺🇸 United States (28 missing rules) - **HIGHEST PRIORITY**

#### US_persons.yaml
```yaml
name: us-persons
description: US person identifiers
context: persons
lang: en
country_code: us
rules:
  usssnfield:
    key: usssn
    is_pii: True
    name: US Social Security Number by field name
    rule: ssn,social_security_number,ss_number,ssn_number,social_security,ssn_id
    type: field
    match: text
  usssnvalue:
    key: usssn
    is_pii: True
    name: US Social Security Number by pattern
    match: ppr
    type: data
    rule: Word(nums, exact=3) + Optional(Literal('-') | Literal(' ') | Literal('.')) + Word(nums, exact=2) + Optional(Literal('-') | Literal(' ') | Literal('.')) + Word(nums, exact=4)
    maxlen: 11
    minlen: 9
  
  useinfield:
    key: usein
    is_pii: True
    name: US EIN by field name
    rule: ein,employer_id,employer_identification_number,ein_number
    type: field
    match: text
  useinvalue:
    key: usein
    is_pii: True
    name: US EIN by pattern
    match: ppr
    type: data
    rule: Word(nums, exact=9)
    maxlen: 9
    minlen: 9
  
  usitinfield:
    key: usitin
    is_pii: True
    name: US ITIN by field name
    rule: itin,individual_taxpayer_id,individual_taxpayer_identification_number
    type: field
    match: text
  usitinvalue:
    key: usitin
    is_pii: True
    name: US ITIN by pattern
    match: ppr
    type: data
    rule: Literal('9') + Word(nums, exact=2) + Optional(Literal('-') | Literal(' ')) + Word('7890123456789', exact=2) + Optional(Literal('-') | Literal(' ')) + Word(nums, exact=4)
    maxlen: 11
    minlen: 9
  
  uspassportfield:
    key: uspassport
    is_pii: True
    name: US passport by field name
    rule: passport,passport_number,us_passport,passport_id
    type: field
    match: text
  uspassportvalue:
    key: uspassport
    is_pii: True
    name: US passport by pattern
    match: ppr
    type: data
    rule: Word(nums, exact=9)
    maxlen: 9
    minlen: 9
  
  usdriverlicfield:
    key: usdriverlic
    is_pii: True
    name: US driver license by field name
    rule: driver_license,drivers_license,dl_number,license_number,driving_license
    type: field
    match: text
  usdriverlicvalue:
    key: usdriverlic
    is_pii: True
    name: US driver license by pattern
    match: ppr
    type: data
    rule: Word(alphanums, min=6, max=18)
    maxlen: 18
    minlen: 6
```

#### US_pii.yaml
Same rules as US_persons.yaml (all are PII)

#### US_finances.yaml
```yaml
name: us-finances
description: US financial identifiers
context: finances
lang: en
country_code: us
rules:
  abaroutingfield:
    key: abaroutingnum
    name: ABA routing number by field name
    rule: routing_number,aba_routing,aba_number,routing_num,bank_routing
    type: field
    match: text
  abaroutingvalue:
    key: abaroutingnum
    name: ABA routing number by pattern
    match: ppr
    type: data
    rule: Word('0123678', exact=1) + Word(nums, exact=3) + Optional(Literal('-')) + Word(nums, exact=4) + Optional(Literal('-')) + Word(nums, exact=1)
    maxlen: 11
    minlen: 9
  
  cusipfield:
    key: cusip
    name: CUSIP by field name
    rule: cusip,cusip_id,cusip_number
    type: field
    match: text
  cusipvalue:
    key: cusip
    name: CUSIP by pattern
    match: ppr
    type: data
    rule: Word(nums, exact=3) + Word(alphanums, exact=2) + Word(alphanums + '*@#', exact=3) + Word(nums, exact=1)
    maxlen: 9
    minlen: 9
```

---

### 2. 🇬🇧 United Kingdom (17 missing rules)

#### GB_persons.yaml
```yaml
name: gb-persons
description: UK person identifiers
context: persons
lang: en
country_code: gb
rules:
  ukninofield:
    key: uknino
    is_pii: True
    name: UK National Insurance number by field name
    rule: nino,national_insurance_number,ni_number,insurance_number
    type: field
    match: text
  ukninovalue:
    key: uknino
    is_pii: True
    name: UK National Insurance number by pattern
    match: ppr
    type: data
    rule: Word(alphas, exact=2) + Word(nums, exact=6) + Word(alphas, exact=1)
    maxlen: 9
    minlen: 9
  
  ukutrfield:
    key: ukutr
    is_pii: True
    name: UK UTR by field name
    rule: utr,unique_taxpayer_reference,tax_reference,taxpayer_reference
    type: field
    match: text
  ukutrvalue:
    key: ukutr
    is_pii: True
    name: UK UTR by pattern
    match: ppr
    type: data
    rule: Word(nums, exact=10)
    maxlen: 10
    minlen: 10
  
  ukpassportfield:
    key: ukpassport
    is_pii: True
    name: UK passport by field name
    rule: passport,passport_number,uk_passport,british_passport
    type: field
    match: text
  ukpassportvalue:
    key: ukpassport
    is_pii: True
    name: UK passport by pattern
    match: ppr
    type: data
    rule: Word(nums, exact=9)
    maxlen: 9
    minlen: 9
  
  uknhsnumfield:
    key: uknhsnum
    is_pii: True
    name: UK NHS Number by field name
    rule: nhs_number,nhs_num,national_health_service_number
    type: field
    match: text
  uknhsnumvalue:
    key: uknhsnum
    is_pii: True
    name: UK NHS Number by pattern
    match: ppr
    type: data
    rule: Word(nums, exact=3) + Optional(Literal('-') | Literal(' ')) + Word(nums, exact=3) + Optional(Literal('-') | Literal(' ')) + Word(nums, exact=4)
    maxlen: 12
    minlen: 10
```

#### GB_geo.yaml
```yaml
name: gb-geo
description: UK geographic identifiers
context: geo
lang: en
country_code: gb
rules:
  ukpostcodefield:
    key: ukpostalcode
    name: UK postal code by field name
    rule: postcode,postal_code,zip_code,uk_postcode
    type: field
    match: text
  ukpostcodevalue:
    key: ukpostalcode
    name: UK postal code by pattern
    match: ppr
    type: data
    rule: Word(alphas, min=1, max=2) + Word(nums, min=1, max=2) + Optional(Word(nums, exact=1)) + Optional(Literal(' ')) + Word(nums, exact=1) + Word(alphas, exact=2)
    maxlen: 8
    minlen: 5
  
  uprnfield:
    key: uprn
    name: UK UPRN by field name
    rule: uprn,unique_property_reference_number,property_reference
    type: field
    match: text
  uprnvalue:
    key: uprn
    name: UK UPRN by pattern
    match: ppr
    type: data
    rule: Word(nums, exact=12)
    maxlen: 12
    minlen: 12
```

---

### 3. 🇷🇺 Russia (24 missing rules)

#### RU_persons.yaml
```yaml
name: ru-persons
description: Russian person identifiers
context: persons
lang: ru
country_code: ru
rules:
  rupassportfield:
    key: rupassport
    is_pii: True
    name: Russian passport foreign number by field name
    rule: passport,passport_number,загранпаспорт,номер_загранпаспорта
    type: field
    match: text
  
  russurnamefield:
    key: russurname
    is_pii: True
    name: Russian surname by field name
    rule: surname,lastname,last_name,фамилия,familiya
    type: field
    match: text
  
  rusfirstnamefield:
    key: rusfirstname
    is_pii: True
    name: Russian first name by field name
    rule: firstname,first_name,имя,imya
    type: field
    match: text
  
  rusmidnamefield:
    key: rusmidname
    is_pii: True
    name: Russian middle name by field name
    rule: middlename,middle_name,отчество,otchestvo
    type: field
    match: text
  
  rusfullnamefield:
    key: rusfullname
    is_pii: True
    name: Russian full name by field name
    rule: fullname,full_name,полное_имя,polnoe_imya,фио,fio
    type: field
    match: text
```

#### RU_finances.yaml
```yaml
name: ru-finances
description: Russian financial identifiers
context: finances
lang: ru
country_code: ru
rules:
  rusbankaccountfield:
    key: rusbankaccount
    name: Russian bank account by field name
    rule: bank_account,account_number,расчетный_счет,raschetnyy_schet,счет,schet
    type: field
    match: text
  rusbankaccountvalue:
    key: rusbankaccount
    name: Russian bank account by pattern
    match: ppr
    type: data
    rule: Word(nums, exact=20)
    maxlen: 20
    minlen: 20
  
  rueqsecregfield:
    key: rueqsecreg
    name: Russian equity securities registration by field name
    rule: гос_регистрация_выпуска,gos_registratsiya_vypuska
    type: field
    match: text
  rueqsecregvalue:
    key: rueqsecreg
    name: Russian equity securities registration by pattern
    match: ppr
    type: data
    rule: Word(nums, exact=1) + Word(nums, exact=5) + Word(alphas, exact=1)
    maxlen: 7
    minlen: 7
```

---

### 4. 🇫🇷 France (10 missing rules)

#### FR_persons.yaml
```yaml
name: fr-persons
description: French person identifiers
context: persons
lang: fr
country_code: fr
rules:
  frnirfield:
    key: frnir
    is_pii: True
    name: French NIR by field name
    rule: nir,numéro_inscription_répertoire,numero_inscription_repertoire,social_security_number
    type: field
    match: text
  frnirvalue:
    key: frnir
    is_pii: True
    name: French NIR by pattern
    match: ppr
    type: data
    rule: Word(nums, exact=13)
    maxlen: 13
    minlen: 13
  
  frcnifield:
    key: frcni
    is_pii: True
    name: French CNI by field name
    rule: cni,carte_nationale_identité,carte_nationale_identite,identity_card
    type: field
    match: text
  frcnivalue:
    key: frcni
    is_pii: True
    name: French CNI by pattern
    match: ppr
    type: data
    rule: Word(nums, exact=12)
    maxlen: 12
    minlen: 12
  
  frpassportfield:
    key: frpassport
    is_pii: True
    name: French passport by field name
    rule: passport,passeport,passport_number,numero_passeport
    type: field
    match: text
  frpassportvalue:
    key: frpassport
    is_pii: True
    name: French passport by pattern
    match: ppr
    type: data
    rule: Word(nums, exact=2) + Word(alphas, exact=2) + Word(nums, exact=5)
    maxlen: 9
    minlen: 9
```

#### FR_companies.yaml
```yaml
name: fr-companies
description: French company identifiers
context: companies
lang: fr
country_code: fr
rules:
  sirenfield:
    key: sirencode
    name: SIREN by field name
    rule: siren,siren_code,numero_siren
    type: field
    match: text
  sirenvalue:
    key: sirencode
    name: SIREN by pattern
    match: ppr
    type: data
    rule: Word(nums, exact=9)
    maxlen: 9
    minlen: 9
```

---

### 5. 🇪🇸 Spain (9 missing rules)

#### ES_persons.yaml
```yaml
name: es-persons
description: Spanish person identifiers
context: persons
lang: es
country_code: es
rules:
  espassportfield:
    key: espassport
    is_pii: True
    name: Spanish passport by field name
    rule: passport,pasaporte,numero_pasaporte
    type: field
    match: text
  espassportvalue:
    key: espassport
    is_pii: True
    name: Spanish passport by pattern
    match: ppr
    type: data
    rule: Word(alphanums, min=2, max=3) + Word(nums, exact=6)
    maxlen: 9
    minlen: 8
  
  esniefield:
    key: esnie
    is_pii: True
    name: Spanish NIE by field name
    rule: nie,numero_identidad_extranjero,foreigner_id
    type: field
    match: text
  esnievalue:
    key: esnie
    is_pii: True
    name: Spanish NIE by pattern
    match: ppr
    type: data
    rule: (Literal('X') + Optional(Literal('-') | Literal('.')) + Optional(Literal('0')) + Word(nums, exact=7) + Optional(Literal('-') | Literal('.')) + Word(alphas, exact=1)) | (Word(alphas, exact=1) + Optional(Literal('-') | Literal('.')) + Word(nums, exact=7) + Optional(Literal('-') | Literal('.')) + Word(alphanums, exact=1)) | (Word(nums, exact=8) + Optional(Literal('-') | Literal('.')) + Word(alphas, exact=1))
    maxlen: 12
    minlen: 9
  
  esniffield:
    key: esnif
    is_pii: True
    name: Spanish NIF by field name
    rule: nif,dni,numero_identificacion_fiscal
    type: field
    match: text
  esnifvalue:
    key: esnif
    is_pii: True
    name: Spanish NIF by pattern
    match: ppr
    type: data
    rule: Optional(Word(nums, exact=1)) + Word(nums, exact=7) + Optional(Literal('-')) + Word(alphas, exact=1)
    maxlen: 9
    minlen: 8
```

---

## Summary Statistics

| Country | Missing Rules | Priority | Categories |
|---------|--------------|----------|------------|
| US | 28 | 🔴 Critical | persons, pii, finances, geo, government, medical, telecom, transport |
| GB | 17 | 🔴 Critical | persons, pii, companies, finances, geo, industry, medical |
| RU | 24 | 🟠 High | persons, pii, finances, geo, government, companies, common |
| FR | 10 | 🟠 High | persons, pii, companies, geo |
| ES | 9 | 🟠 High | persons, pii, geo |
| CA | 11 | 🟡 Medium | persons, pii, geo |
| AU | 9 | 🟡 Medium | persons, pii, companies, finances |
| DE | 4 | 🟡 Medium | persons, pii |
| SE | 4 | 🟢 Low | persons, pii |
| Others | 80 | 🟢 Low | Various |

## Implementation Checklist

- [ ] Create US rules (28 rules)
- [ ] Create GB rules (17 rules)
- [ ] Create RU rules (24 rules)
- [ ] Create FR rules (10 rules)
- [ ] Create ES rules (9 rules)
- [ ] Create CA rules (11 rules)
- [ ] Create AU rules (9 rules)
- [ ] Create remaining country rules (80 rules)

## Notes

1. **Field name rules** should include both English and native language variations
2. **Pattern rules** should handle optional separators (spaces, dashes, dots)
3. **PII flags** must be set correctly for all person-related identifiers
4. **Test patterns** against examples from the registry
5. **Follow existing rule structure** from similar rules in the codebase

