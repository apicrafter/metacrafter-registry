# Дамп ROR v1.68: какие данные реестр и metacrafter не распознают (ноябрь 2026)

Цель: проверить, все ли поля дампа Research Organization Registry (ROR)
распознаются типами реестра и правилами metacrafter, и найти семантические
типы, которых в реестре нет.

## Источники и метод

- `v1.68-2025-07-15-ror-data_schema_v2.json` (схема v2.1) и
  `v1.68-2025-07-15-ror-data.json` (устаревшая схема v1). В каждом файле
  117 584 записи. Использованы также официальные CSV-выгрузки того же релиза.
- Профиль всех путей полей: число значений, число различных значений,
  перечисления.
- Значения каждого поля проверены регулярными выражениями всех 1991 записи
  реестра (`data/datatypes_latest.jsonl`). Для обзора по всем регуляркам
  взято до 1500 различных значений на поле. Для целевых проверок взяты все
  значения.
- Контрольные суммы: ISNI проверен через `checksums.iso7064_mod11_2`, ROR id
  проверен по алгоритму ROR (Crockford base32, затем ISO 7064 MOD 97-10).
- Реальное распознавание: `metacrafter scan file` (локальный checkout
  metacrafter `24cb144`, metacrafter-rules `1982330`, это закреплённая в
  `ecosystem.lock` версия). Сканировались три набора: выборки по 5000 строк из
  обоих CSV с исходными именами колонок, те же выборки с обезличенными
  именами (`c00`…), чтобы проверить распознавание только по значениям, и
  «чистые» колонки по 2000 значений, по одному значению в ячейке.

## Сводка по полям

«Реестр» — подходящая запись реестра и доля значений, совпавших с её
регулярным выражением. «Metacrafter» — что сканер выдал по значениям
(обезличенные колонки).

| Поле (v2 / v1) | Тип по смыслу | Реестр | Metacrafter |
|---|---|---|---|
| `id`, `relationships[].id` — `https://ror.org/04ttjf776` | ROR id в форме URL | `rorid` описывает только голый id; для URL-формы нет паттерна | `url` 100 %, `rorid` нет |
| `external_ids[grid]` — `grid.1017.7` | GRID | `grid` 100 % | **не распознан** (см. правила, п. 1) |
| `external_ids[isni]` — `0000 0001 2163 3550` | ISNI | `isni` 100 %, контрольная сумма верна у 57 539 из 57 539 | `isni` только 8 % (п. 2) |
| `external_ids[fundref]` — `501100001780` | Crossref Funder ID | `crossref_funder_id` (draft) 100 % | ложные `frcni` 47 %, `scopusauthoirid` 45 %; правила нет |
| `external_ids[wikidata]` — `Q1057890` | Wikidata item | у `wikidataid` **нет regexp**; форма `^Q[1-9]\d*$` даёт 100 % | `wikidataid` 100 % |
| `locations[].geonames_id` — `2158177` | GeoNames id | `geonamesid` 100 % (regexp — любое целое) | ложный `uiccode` 62 %; правила нет |
| `established` — `1887` | год основания | `year` 99,5 % (не проходят 712, 970, 976) | не распознан |
| `lat`, `lng` | широта / долгота | у `latitude` и `longitude` нет regexp | **не распознаны** (п. 4) |
| `continent_code` — `OC` | код континента | `continentcode` 100 % | не распознан, правила нет |
| `continent_name` | континент | `continent` | `continent` 78 % |
| `country_code` — `AU` | ISO 3166-1 alpha-2 | `countrycode_alpha2` 100 % | по значению не распознан; по имени поля — ключ `country_geo`, которого нет в реестре |
| `country_name` | страна | `encountryname` | `encountryname` 95 % |
| `country_subdivision_code` — `VIC`, `MOW`, `11` | часть кода ISO 3166-2 без префикса страны | **нет типа**: `iso3166code` требует `AU-VIC` (0 %; с префиксом `CC-` — 100 %) | не распознан |
| v1 `geonames_admin1.code` — `AU.VIC` | ISO 3166-2 с точкой вместо дефиса | **нет типа** (после замены `.`→`-` `iso3166code` даёт 100 %) | ложный `fqdn` 74 % |
| `country_subdivision_name` | регион первого уровня | `admin_area_1` (draft, правил нет) | частично `usstate` 26 % |
| `geonames_details.name`, v1 `city` | город | `city` | только по имени поля; `uscity` 17 % |
| `names[].value`, v1 `name`, `aliases`, `labels` | название организации | `orgname` (без regexp) | только по имени поля |
| `names[acronym]`, v1 `acronyms` — `RMIT` | аббревиатура организации | **нет типа** | ложный `icaoairportcode` 32 % |
| `names[].lang`, `ror_display_lang` | ISO 639-1 | `iso639_1` 100 %, `languagetag` 100 % | не распознан |
| `domains` | домен | `fqdn` 100 % | `fqdn` 99 % |
| `links[website]` | сайт | `url` 100 % | `url` 100 % |
| `links[wikipedia]`, v1 `wikipedia_url` | URL статьи Википедии | **нет типа**, только общий `url` | `url` |
| `types[]` — 9 значений | тип организации ROR | **нет типа** | не распознан |
| `status` — active / inactive / withdrawn | статус записи ROR | **нет типа** | не распознан |
| `relationships[].type` — parent, child, related, successor, predecessor | тип связи организаций | **нет типа** | не распознан |
| `names[].types[]` — ror_display, label, alias, acronym | тип названия ROR | **нет типа** | — |
| `external_ids[].type` — grid, isni, wikidata, fundref | схема внешнего идентификатора | **нет типа** (`org_id_scheme` — это коды ORG-ID.guide) | — |
| `admin.*.date` | дата | `date` | `date` 100 % |
| `admin.*.schema_version` — `1.0`, `2.1` | версия схемы | `version` (по имени поля) | — |

Итог: идентификаторы ROR, GRID, ISNI, Crossref Funder ID и Wikidata в реестре
есть. Но metacrafter надёжно распознаёт по значениям только Wikidata и голый
ROR id. GRID, ISNI, ROR-URL, Funder ID, GeoNames id и координаты в выгрузке
ROR на практике не распознаются или распознаются ложно.

## Что исправить в существующих записях реестра

1. **`rorid`: слишком широкая регулярка `^[a-z0-9]{9}$`.** Под неё попадают
   11 593 из 21 732 Crossref Funder ID (все 9-значные `100xxxxxx`). Точная
   форма `^0[0-9a-hjkmnp-tv-z]{6}[0-9]{2}$` выполняется для всех 117 584 id.
   Контрольная сумма ROR верна у всех 117 584 id и у всех 27 678 id в
   `relationships`. Ни один Funder ID не проходит точную форму с контрольной
   суммой. Предложение: добавить алгоритм `ror` в
   `src/metacrafter_registry/checksums.py`, указать `checksum: ror` и сузить
   regexp.
2. **Паттерн URL-формы ROR id** `^https://ror\.org/0[0-9a-hjkmnp-tv-z]{6}[0-9]{2}$`
   с `semantic_type: rorid`. В этой форме ROR публикует id во всех полях
   (`id`, `relationships[].id`). В фасетах DataCite (`dois.json`)
   встречается форма без схемы: `ror.org/01t3wyv61`.
3. **`wikidataid`: нет regexp.** Форма `^Q[1-9][0-9]*$` выполняется для всех
   54 295 значений. Запись сейчас описывает идентификаторы Wikidata в целом,
   поэтому для свойств (`P…`) и лексем (`L…`) нужно решить: расширить regexp
   или завести отдельные паттерны.
4. **`crossref_funder_id`** (draft): regexp выполняется для всех 21 732
   значений; длины 9 (`100…`) и 12 (`501…`). Запись можно проверять для
   `stable`. DOI-форма `10.13039/<id>` сейчас записана только как
   отрицательный пример. Это кандидат в отдельный паттерн.
5. **`year`** (`^\d{4}$`) не принимает трёхзначные годы основания (712, 970,
   976). Это мелочь, но для поля «год основания» такие значения законны.
6. У **`latitude` / `longitude`** нет regexp. Диапазоны в данных:
   −77,5…82,2 и −175,2…179,2.

## Кандидаты в новые типы

Высокий приоритет:

1. **Код субъекта ISO 3166-2 без кода страны** (`VIC`, `MOW`, `IDF`, `11`):
   821 различное значение. По значению его не отличить от других коротких
   кодов, поэтому распознавать его стоит по имени поля
   (`country_subdivision_code`, `subdivision_code`, `region_code`). Вариант
   оформления: паттерн записи `iso3166code`.
2. **ISO 3166-2 с точкой** (`AU.VIC`, `AL.11`, 2147 значений, v1 и GeoNames):
   паттерн `^[A-Z]{2}\.[A-Z0-9]{1,3}$` записи `iso3166code`. Сейчас эти
   значения ложно распознаются как `fqdn`.
3. **Тип организации ROR** (categorical): education, healthcare, company,
   archive, nonprofit, government, facility, other, funder. В v1 те же
   значения с заглавной буквы.
4. **URL статьи Википедии**: паттерн записи `url`, например
   `^https?://[a-z][a-z0-9-]{1,11}\.(?:m\.)?wikipedia\.org/(?:wiki/|[a-z]{2,3}(?:-[a-z]+)?/|\?title=)\S+$`.
   В ROR встречаются пути `/wiki/`, языковые варианты `/zh-hans/`, `/sr-el/`,
   `/zh/` и `/?title=`. Тип встречается во многих наборах данных, не только в
   ROR.
5. **Аббревиатура организации**: 35 638 различных значений. Тип без regexp,
   распознаётся по имени поля (`acronym`, `abbreviation`). Без него
   metacrafter выдаёт ложный `icaoairportcode`.

Средний и низкий приоритет:

6. **Схема идентификатора организации** (grid, isni, wikidata, fundref). В
   DataCite это поля `affiliationIdentifierScheme`, `nameIdentifierScheme`,
   `funderIdentifierType` со значениями `ROR`, `GRID`, `ISNI`,
   `Crossref Funder ID`.
7. **Статус записи ROR** (active, inactive, withdrawn).
8. **Тип связи организаций** (parent, child, related, successor,
   predecessor).
9. **Тип названия ROR** (ror_display, label, alias, acronym): узкий,
   специфичный для ROR.

## DataCite (беглый просмотр `dois.json`, вне двух основных файлов)

Подробно не проверялось. В ответе API DataCite есть типы, которых в
реестре нет:

- IGSN (`identifierType: IGSN`, например `10273/ODP0251DE`);
- `resourceTypeGeneral` DataCite (Dataset, PhysicalObject, Text и др.) и
  фасет `resourceTypes` (`dataset`, `physical-object`);
- id клиента (репозитория) DataCite (`cern.zenodo`, `rpht.nifs`) и id
  провайдера (`cern`, `rpht`);
- области науки OECD FOS в виде слагов (`biological_sciences`,
  `agriculture_forestry_and_fisheries`).

Префиксы DOI (`10.5281`) покрыты записью `doiprefix`, лицензии SPDX
(`cc-by-4.0`) — правилом `spdxlicensebyvalue` записи `software_license`.

## Почему metacrafter не распознаёт: дефекты metacrafter-rules

Это не реестр, но именно эти дефекты объясняют большую часть пропусков.

1. **`gridbyvalue`: `maxlen: 12`.** Длина GRID id достигает 14 символов
   (`grid.469496.0`). 102 967 из 103 677 GRID id (99,3 %) длиннее 12
   символов, поэтому GRID по значению не распознаётся почти никогда.
2. **`validate_isni` считает контрольную сумму неверно.** Он использует
   циклические веса 2…11 вместо ISO 7064 MOD 11-2 и отвергает контрольный
   символ `X`. В итоге он принимает 4708 из 57 539 корректных ISNI (8 %).
   Правильный алгоритм есть в реестре: `checksums.iso7064_mod11_2`.
3. **`roridbyvalue`: `Word(alphanums, exact=9)`.** URL-форма не проходит,
   хотя `validate_ror_id` уже умеет отрезать префикс `https://ror.org/`.
4. **`latitudevalue`, `longitudevalue`, `yearbydatafiltered`: `fieldrule`
   вида `Optional(Word(printables)) + … + "lat"` не срабатывает ни на одном
   имени поля.** `Word(printables)` жадно съедает всё имя, а pyparsing не
   откатывается назад. Проверено: не проходят даже `lat` и `latitude`. Кроме
   того, правило широты не принимает отрицательные значения и одну цифру до
   точки.
5. **Нет правил по значению** для `crossref_funder_id`, `geonamesid`,
   `continentcode`, `iso639_1`, `iso3166code`, `admin_area_1`.
6. **Ключи правил `country_geo` и `continent_geo`** не являются id или
   алиасами реестра (сканер выдаёт предупреждение).
7. **Ложные срабатывания:** Funder ID распознаётся как `frcni` и
   `scopusauthoirid`, GeoNames id — как `uiccode`, аббревиатуры — как
   `icaoairportcode`, коды `AU.VIC` — как `fqdn`.

## Замечания о качестве данных ROR

- В поле GRID два значения не являются GRID id: `100011307` (Funder ID) у
  `https://ror.org/05swbnm48` и `Q6214723` (Wikidata) у
  `https://ror.org/04yr81d29`.
- В ссылках типа `wikipedia` есть адреса не из Википедии: сайты организаций,
  fandom.com, conservapedia.com, commons.wikimedia.org, wikivoyage.org,
  doi.org, а также опечатка `wikipedi0.org`. Это 14 ссылок из 39 404.
- У 20 871 записи нет `established`. У ISNI, Wikidata и FundRef
  `preferred` в большинстве записей пустой.

## Что внесено в реестр по итогам анализа

- Алгоритм `ror` в `checksums.py` и его двойник в `static/identify-core.js`
  (Crockford base-32, ISO 7064 MOD 97-10; допускается префикс
  `https://ror.org/` или `ror.org/`). Тесты: эталонные значения в
  `tests/test_client.py`, сверка с JavaScript в `tests/test_ecosystem.py`.
  Источник: https://ror.readme.io/docs/identifier.
- `rorid`: regexp `^0[0-9a-hjkmnp-tv-z]{6}[0-9]{2}$`, `checksum: ror`,
  отрицательные примеры (Funder ID, URL-форма), описание и перевод.
- Новый паттерн `rorid_url` (`semantic_type: rorid`, `checksum: ror`).
- `wikidataid`: regexp `^Q[1-9][0-9]*$`, отрицательные примеры (`P6782`,
  `Q01`), описание элемента Wikidata и перевод.
- `crossref_funder_id` переведён в `stable`.
- Новые записи в статусе draft: `iso3166code_dotted` и `iso3166code_part`
  (паттерны `iso3166code`), `ror_organization_type`, `wikipedia_url`
  (паттерн `url`), `org_acronym` (`parent: orgname`). У `iso3166code_part` и
  `org_acronym` нет regexp: их значения нельзя отличить от других коротких
  кодов, распознавать их нужно по имени поля.

Проверка новых регулярок на полном дампе:

| Запись | Совпало |
|---|---|
| `rorid_url` на `id` | 117 584 из 117 584, контрольная сумма верна у всех |
| `rorid` на Funder ID (ложные срабатывания) | 0 из 21 732 (было 11 593) |
| `wikidataid` | 54 295 из 54 295 |
| `wikipedia_url` на ссылках `wikipedia` | 36 370 из 36 379 (9 отказов — ошибки данных, см. выше) |
| `wikipedia_url` на ссылках `website` | 1 совпадение: сайт, указанный ссылкой на Википедию |
| `iso3166code_dotted` на v1 `geonames_admin1.code` | 2147 из 2147 |
| `ror_organization_type` | 9 из 9 значений в обеих схемах |

`Registry.identify` на выборках по 200 значений ставит на первое место
`rorid_url` для `id`, `crossref_funder_id` для FundRef (раньше этого
типа не было среди вариантов), `wikidataid`, `grid` и `isni`. Тип
`wikipedia_url` идёт вторым после общего `url`. `ror_organization_type`
идёт вторым после `tld`, потому что `education` и `company` — домены
верхнего уровня. `iso3166code_dotted` идёт вторым после `ddi_agency_id`.

Не внесено: трёхзначные годы в `year` (расширение дало бы ложные
срабатывания на любых трёхзначных числах), regexp для `latitude` и
`longitude`, типы среднего приоритета (схема идентификатора, статус записи
ROR, тип связи, тип названия) и типы DataCite.

## Воспроизведение

Скрипты анализа (профиль полей, сверка с регулярками, целевые проверки,
выборки для metacrafter) лежали во временной папке сессии и в репозиторий не
входят. Чтобы повторить сканирование:

```bash
metacrafter scan file v1.68-2025-07-15-ror-data_schema_v2.csv --format short --registry-offline --limit 5000
```
