# Внешние источники семантических типов, не учтённые в реестре (2026-11-05)

Цель: найти значимые внешние источники семантических типов данных, которые
реестр пока не использует ни как маппинг, ни как ссылку, ни как список
`supported_types` инструмента.

## Исходные данные и метод

- Реестр: `data/datatypes_latest.jsonl` и `data/tools_latest.jsonl` на коммите
  `7604ce0` (1552 записи: 451 `stable`, 1101 `draft`; 50 инструментов).
- Для каждого кандидата проверено:
  - есть ли ключ в `mappings` (`schema/datatype.schema.json`) и сколько
    записей его используют;
  - есть ли ссылки на источник в `links` или в тексте записей (поиск по
    подстроке в JSON записи);
  - есть ли записи с соответствующими id в `data/datatypes/`;
  - сколько `supported_types` у инструмента в `data/tools/`.
- python-stdnum 2.2: список модулей взят из wheel, ссылки на документацию
  stdnum собраны из `data/datatypes/`.
- Уже выполненные обзоры (`devdocs/*_REVIEW.md`, Wikidata, Egeria, порталы
  data.gov.ru, data.mos.ru, opendata.mkrf.ru) и закрытые issues #1-#53 не
  пересматривались.

## Ограничения

- Числа по реестру посчитаны из файлов. Числа по внешним источникам
  (количество префиксов, детекторов, регионов) приблизительные, взяты по
  памяти и в этой работе не сверялись с источниками. Перед началом работы по
  каждому пункту их нужно проверить.
- Поиск по подстроке даёт ложные совпадения (например, `h3` в `half_year`).
  Совпадения, на которых строятся выводы, просмотрены вручную.
- Отсутствие записи с ожидаемым id не всегда значит отсутствие типа: запись
  может существовать под другим id (см. python-stdnum ниже).

## Что уже учтено

Маппинги (число записей с ключом):

| Ключ | Записей |
|---|---|
| `wikidata` | 303 |
| `orgid` | 236 |
| `purview` | 226 |
| `fta` | 188 |
| `autotype` | 90 |
| `google_dlp` | 70 |
| `presidio` | 67 |
| `cdm` | 47 |
| `gs1_ai` | 37 |
| `qddate` | 35 |
| `fibo` | 33 |
| `sherlock` | 30 |
| `d3m` | 13 |
| `schema_org` | 8 |
| `dpv` | 0 |

Типы ссылок: `wikipedia` 720, `doc` 713, `other` 632, `wikidata` 323,
`schema.org` 57, `dublincore` 18, `bioschemas` 3, `datadrivendiscovery` 2.

Инструменты с непустыми `supported_types`, среди прочих: `amazonmacie` (112),
`awscomprehend` (37), `azureailanguage` (166), `snowflake` (169),
`databricks` (83), `nightfall` (125), `ibmknowledgecatalog` (79), `collibra`
(78), `talend` (80), `pythonstdnum` (228), `gitleaks` (23), `trufflehog` (27),
`detectsecrets` (22), `dataprofiler` (17), `woodwork` (15).

## Итоги

- Самые крупные пробелы: идентификаторы наук о жизни (Bioregistry),
  кибербезопасность (CVE, CWE, ATT&CK и др.), шаблоны секретов,
  идентификаторы здравоохранения (HL7, FHIR, DICOM), торговые и
  профессиональные классификаторы (HS, ISCO), геосетки и SDMX.
- Два ключа маппинга почти пусты, хотя уже есть в схеме: `dpv` (0 записей) и
  `schema_org` (8 записей). Это самый дешёвый выигрыш.
- Форматы по странам (телефоны, почтовые индексы, даты) можно усилить из
  libphonenumber, адресных метаданных Google и GeoNames, Unicode CLDR.
- python-stdnum почти закрыт: реально нет около шести типов, остальные есть
  под другими id без ссылки на stdnum.

## Значимые и не учтённые источники

Порядок: по убыванию пользы для реестра.

### 1. Bioregistry и identifiers.org

- Что дают: реестр префиксов идентификаторов наук о жизни (около 1800
  префиксов), у каждого regex, пример и маппинг на Wikidata. Лицензия CC0.
- Состояние реестра: около 35 научных идентификаторов в
  `data/datatypes/any/science/` и `any/chemistry/`. Ни одной ссылки на
  Bioregistry или identifiers.org.
- Предложение: ключ `mappings.bioregistry` (префикс). Импортировать только
  префиксы, которые встречаются в данных, по тому же принципу, что в обзоре
  Wikidata (`devdocs/WIKIDATA_PROPERTIES_2026-11.md`).

### 2. Кибербезопасность: MISP, STIX 2.1, OCSF, Elastic ECS

- Что дают: типы атрибутов MISP, Cyber Observables STIX 2.1, типы
  наблюдаемых объектов OCSF, поля ECS.
- Состояние реестра: хеши, IP, криптоадреса, `tlsh`, `imphash`, `telfhash`
  есть. Нет CVE, CWE, CAPEC, CPE 2.3, MITRE ATT&CK (`T1059.001`), GHSA, OSV,
  JA3/JA4. По всем этим ключевым словам ноль совпадений.
- Предложение: записи для перечисленных идентификаторов; ключи `misp` и
  `ocsf` для кроссволка.

### 3. Шаблоны секретов: GitHub secret scanning, TruffleHog, Gitleaks

- Что дают: список шаблонов токенов GitHub secret scanning, детекторы
  TruffleHog (около 800), правила Gitleaks (около 200, с regex, MIT).
- Состояние реестра: 46 записей в категории `secrets`; у `trufflehog`
  размечено 27 типов, у `gitleaks` 23.
- Предложение: добавлять токены с документированным префиксом или форматом
  (они дают надёжный regex), начиная с самых распространённых сервисов.

### 4. Здравоохранение: HL7 v2, FHIR, DICOM

- Что дают: HL7 v2 Table 0203 (типы идентификаторов), URI систем
  идентификаторов FHIR (например, `http://hl7.org/fhir/sid/us-ssn`,
  NamingSystem на terminology.hl7.org), DICOM (Value Representations, UID).
- Состояние реестра: 66 записей в категории `medical`. Упоминаний HL7 и DICOM
  ноль, FHIR упомянут в одной записи (`de_pzn`).
- Предложение: ключ `mappings.fhir` с URI системы. Он связывает национальные
  идентификаторы реестра с тем, как они записываются в FHIR.

### 5. Отсутствующие классификаторы

- Нет записей: HS (WCO), CN, TARIC, HTS; ISCO-08, ESCO; COICOP; SITC;
  ISCED; SPDX license id; коды EPSG.
- Есть: `naicscode`, `eu_nace`, `isicrev4`, `unspsc`, `cpvcode`, `okved`,
  `nutsregion`. `software_license` не ссылается на SPDX.
- Источники: UNSD classifications, EU Vocabularies (Publications Office,
  authority tables), SPDX License List.
- Коды HS часто встречаются в торговых и таможенных данных; это первый
  кандидат в группе.

### 6. Геосетки и системы координат

- Нет записей: H3, geohash, S2, Plus codes (Open Location Code),
  Maidenhead, quadkey, коды EPSG.
- Есть: `what3words`, `mgrs`, `wkt`, `geojson`, `iso6709`.

### 7. Форматы по странам и локалям

Эти источники усиливают существующие типы, а не добавляют новые.

- libphonenumber (Apache-2.0): шаблоны и синтетические примеры номеров
  примерно для 245 регионов. Сейчас в реестре один страновой тип телефона:
  `nanpphone` (US). Синтетические примеры подходят для `examples`, потому что
  это не номера реальных людей.
- Адресные метаданные Google (libaddressinput) и GeoNames `countryInfo`:
  regex почтовых индексов по странам. В реестре 41 запись с индексами.
- Unicode CLDR: шаблоны дат, названия месяцев и дней для сотен локалей.
  Сейчас форматы дат (`data/datatypes/any/datetime/`) покрывают около 20
  языков.

### 8. SDMX

- Что даёт: cross-domain concepts (`FREQ`, `REF_AREA`, `OBS_STATUS`,
  `UNIT_MULT`) и форматы `TIME_PERIOD` (`2024-Q1`, `2024-S1`, `2024-W05`,
  `2024-M01`).
- Состояние реестра: ноль упоминаний. Есть `quarter`, `half_year`,
  `yearmonth`, но не в нотации SDMX.
- Главный источник для статистических данных.

### 9. Ключи маппинга, которые есть, но почти не заполнены

- W3C DPV / DPV-PD: ключ `dpv` есть в схеме и в спецификации
  (`openspec/changes/modernize-registry-platform/`), но нет ни одной записи с
  ним. При этом 311 записей в категории `pii`.
- Schema.org: `schema_org` есть у 8 записей, ссылок `schema.org` 57. Свойства
  `taxID`, `vatID`, `leiCode`, `duns`, `gtin*`, `isbn`, `iataCode`,
  `postalCode`, `telephone`, `birthDate` сопоставляются напрямую.

### 10. Аналоги metacrafter для открытых данных и реестры элементов данных

- csv-detective (Etalab, data.gouv.fr) и schema.data.gouv.fr: детектор
  французских форматов, по назначению тот же, что metacrafter. В
  `data/datatypes/FR/` 26 записей; нет FINESS, FANTOIR/RIVOLI, кода
  NAF/APE, координат Lambert-93. Предложение: запись инструмента и проверка
  его форматов против реестра.
- METeOR (Австралия, ISO 11179), каталог стандартов данных UK GDS, NHS Data
  Dictionary: реестры элементов данных с форматами и value domains.

### 11. Наборы данных для разметки колонок

- SOTAB (Web Data Commons, типы Schema.org), GitTables, SemTab, датасеты PII
  ai4privacy.
- Новых типов дают мало. Полезны для приоритизации: показывают, какие типы
  реально встречаются в таблицах и как часто.

## Почти закрыто

### python-stdnum

- В 2.2 246 модулей; ссылки на документацию stdnum есть у 117.
- Без ссылки и без id, совпадающего с именем модуля, осталось 52 модуля
  (служебные модули вроде `luhn` и `iso7064` не считались). Большинство из
  них, по всей видимости, уже есть в реестре под другим id, но без ссылки на
  stdnum, например
  `dk/cpr` (`dkcprnum`), `za/idnr` (`za_id`), `th/pin` (`thidcard`),
  `se/orgnr` (`seorgnumber`), `tr/vkn` (`trtaxnumber`), `vn/mst`
  (`vntaxcode`), `cfi` (`cficode`), `iso9362` (`bic`), `iso6346`
  (`containernumber`).
- Реально нет записей (проверено поиском по каталогам стран): VE RIF, MA
  ICE, UY RUT, TW UBN, PK CNIC, ISO 11649 (RF creditor reference). Подбор по
  имени эвристический, список может быть неполным.
- Предложение: ключ `mappings.stdnum` (имя модуля), чтобы покрытие
  считалось автоматически, а не по ссылкам.

### Коммерческие каталоги и DLP

- У `bigid`, `informatica` и `ataccama` список `supported_types` пустой.
- Нет записей инструментов AWS Glue Sensitive Data Detection и Oracle Data
  Safe. У обоих много предопределённых типов, в том числе страновых.

## Приоритеты

По соотношению пользы и затрат:

1. DPV и Schema.org: ключи уже есть, нужно только заполнить.
2. Bioregistry.
3. Идентификаторы кибербезопасности и шаблоны секретов.
4. libphonenumber и почтовые индексы.
5. HS, ISCO и SDMX.
6. HL7 и FHIR.

## Что сделано (2026-11-05)

Новые ключи маппинга: `bioregistry` (префикс Bioregistry), `stdnum` (модуль
python-stdnum без `stdnum.`), `fhir` (URI системы идентификаторов HL7 FHIR).
Для них есть схема, `crosswalk`, вывод на странице записи и тесты.

| Ключ | Записей до | Записей после |
|---|---|---|
| `dpv` | 0 | 264 |
| `schema_org` | 8 | 241 |
| `bioregistry` | - | 130 |
| `stdnum` | - | 259 |
| `fhir` | - | 78 |

Значения DPV взяты из DPV 2.3 с префиксом `pd:`. В DPV нет понятий для номеров
социального страхования, национальных ID и налоговых номеров: они отображены на
`pd:OfficialID`, паспорта на `pd:Passport`. Системы FHIR взяты из HL7
Terminology и из базовых руководств национальных аффилиатов HL7 (UK Core, AU
Base, DE Basisprofil, Nictiz, NZ Base).

220 новых записей, все `draft`:

- 101 почтовый индекс (паттерны `postindex`) по адресным метаданным Google,
  сверены с GeoNames; в `data/countries.yaml` добавлено 28 стран, в
  `data/langs.yaml` 9 языков.
- 40 идентификаторов из Bioregistry (RefSeq, INSDC, SRA, BioSample,
  BioProject, GEO, Pfam, InterPro, KEGG, Reactome, Rhea, MGI, ZFIN, FlyBase,
  WormBase, HPO, MONDO, UBERON, ClinVar, ISRCTN, MedDRA, EU CT number и др.).
- 25 типов токенов (Anthropic, Hugging Face, Shopify, HashiCorp Vault,
  Databricks, DigitalOcean и др.) по правилам Gitleaks и детекторам
  TruffleHog.
- 15 идентификаторов безопасности: CVE, CWE, CAPEC, CPE 2.3, пять типов
  MITRE ATT&CK, GHSA, OSV, JA3, JA3S, JA4, получатель age.
- 21 классификатор, геосетка и формат SDMX: HS, CN, TARIC, HTS, ISCO-08,
  ESCO (профессии и навыки), COICOP 2018, SITC Rev.4, ISCED 2011, ISCED-F
  2013, EPSG, H3, geohash, S2, Plus Code (полный и короткий), Maidenhead,
  quadkey, отчётные периоды SDMX, CL_FREQ.
- 16 идентификаторов python-stdnum и csv-detective: VE RIF, MA ICE, UY RUT,
  TW UBN, PK CNIC, ISO 11649 RF, UA РНОКПП, MK EDB, TH MOA, FR RCS, RNA, NAF,
  FINESS, FANTOIR, RIVOLI, идентификатор RNB.
- DICOM UID и коды HL7 v2 Table 0203.

Инструменты: новые `csvdetective`, `awsglue` (199 типов), `oracledatasafe`
(21 тип); `gitleaks` и `trufflehog` дополнены новыми типами токенов.
`software_license` получил описание, ссылку на список SPDX и Wikidata P2479.

### Не сделано

- Телефоны по странам (libphonenumber) и форматы дат CLDR.
- Ключ `misp`. Соответствия есть: `cve_id` - vulnerability, `cwe_id` -
  weakness, `cpe23` - cpe, `ja3_fingerprint` - ja3-fingerprint-md5.
- `supported_types` для BigID, Informatica и Ataccama: вендоры не
  публикуют списки встроенных типов.
- Оставшиеся модули stdnum без записей: dz.nif, gn.nifp, mz.nuit, sm.coe,
  tn.mf, in_.vid и др.

### Найденные ошибки в существующих записях (не исправлены)

- `euid`: regexp без точки, настоящий EUID `CYDRCOR.HE139104` не проходит.
- `icd10cm`: regexp не принимает коды вида `C4A.8`.
- Почтовые индексы: `gbpostcode` и `plpostcode` (`^[0-9]{4,10}$`) отвергают
  реальные индексы; у CN `postcode`, `krpostcode`, `sapostcode`,
  `thpostcode`, `trpostcode`, `vnpostcode` тот же слишком широкий regexp;
  `egpostcode`, `am_postal_code`, `espostcode`, `frpostcode` расходятся с
  Google; у `aepostcode` пример-заглушка `00000`.
- python-stdnum отвергает 23 положительных примера (семейство `cabn`,
  `siret`, `idnik`, `be_ogm_vcs`, `handelsregisternr`, `ke_kra_pin`, `me_pib`
  и др.); regexp `abaroutingnum`, `cusip`, `sedol`, `sepersonnummer`, `taxid`
  расходятся с stdnum.
- `checksums._compact` удаляет дефисы, поэтому `bech32` не проверяет
  секретный ключ age (`AGE-SECRET-KEY-...`).
