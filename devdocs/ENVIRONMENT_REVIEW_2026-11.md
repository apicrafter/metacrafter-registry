# Ревизия категории «Environment» (ноябрь 2026)

Цель: проверить записи категории `environment`, исправить неточные поля,
добавить отсутствующие типы, которые встречаются в данных об охраняемых
территориях, биоразнообразии, водных объектах, погоде и климате, опасных
природных явлениях, выбросах и отходах.

## Источники проверки

- Свойства Wikidata: метка, формат (P1793), примеры (P1855). Регулярные
  выражения проверены на выборках до 5000 различных значений каждого
  свойства через Wikidata Query Service.
- Нормативные тексты: EUR-Lex (Решение 2011/484/EU о Standard Data Form
  Natura 2000; Решение 2000/532/EC и 2014/955/EU, Делегированное решение
  2025/934 — перечень отходов; Приложение I Директивы 92/43/EEC; Директивы
  2000/60/EC и 2006/7/EC; Киотский протокол и Дохинская поправка), eCFR
  40 CFR part 261 (коды опасных отходов RCRA), текст Базельской конвенции и
  поправок 2021 и 2025 годов, IPCC 2006 Guidelines (том 1, глава 8, таблица
  8.2), приказы Минприроды России № 553 от 23.12.2015 и № 167 от 02.04.2025,
  приказ Росприроднадзора № 242 от 22.05.2017 (ФККО), приказ Росстата № 589
  от 02.10.2026 (форма 2-ТП (воздух)), приказ МПР № 138 от 29.05.2007.
- Документация выпускающих организаций: руководство WDPCA 2.0 (UNEP-WCMC,
  2026), IUCN Red List Categories and Criteria 3.1, руководство IUCN по
  категориям ООПТ (Dudley 2008), readme GHCN-Daily, документация IBTrACS,
  NHC ATCF README и формат HURDAT2, GLIDE, EM-DAT, USGS WBD (TM 11-A3),
  схемы XSD WISE (WFD 2016 и 2022), руководства RGI 7.0 и WGI (NSIDC),
  документация AQS, TRI, FRS, GHGRP, страницы AirNow и EEA.
- API и открытые данные: OSCAR/Surface ВМО (станции), словари Eionet (WISE
  WaterBody — 188 330 кодов, SpatialUnit, WFDProtectedArea — 31 909 мест
  купания, загрязнители воздуха), Envirofacts EPA (FRS, TRI — 64 990
  объектов, GHGRP — 11 358), AQS (20 994 станции, 1491 параметр), NID
  (92 689 плотин), NWIS (153 923 пункта по 6 штатам), WBD MapServer (все
  уровни HUC), ghcnd-stations.txt (133 041 станция), IBTrACS (13 632 шторма),
  HURDAT2, GLIDE API (9136 записей), USGS ComCat FDSN, списки GVP, таксономия
  eBird (18 631 код), WGI (132 890 ледников), Global Power Plant Database
  v1.3.0 (34 936 станций), полный текст ФККО (9170 кодов), приказы
  Росприроднадзора о включении объектов в ГРОРО.
- Правила metacrafter-rules на закреплённом коммите `19823306`: в
  `en/en_environment.yaml` три типа — `emissioninventory`, `powerplantid`,
  `gridnode`. Для `waterstation` правила нет.

## Было

12 записей с категорией `environment`, средняя оценка 66,3.

| Запись | Оценка | Проблема |
|---|---:|---|
| `emissioninventory`, `gridnode`, `powerplantid` | 30 | Описание-заглушка «Datatype for ... from rules in context 'environment'». Нет ссылок и перевода. |
| `waterstation` | 20 | То же; правила в metacrafter-rules для него нет. |
| `eu_natura2000_site` | 80 | Нет отрицательного примера, перевода, ссылки на нормативный документ. |
| `wigos_station_id`, `wmo_station_index` | 85 | Нет перевода; пример `0-20008-0-JFJ` и `06702` без источника. |
| `gbif_taxon_id`, `itis_tsn` | 80 | Нет отрицательного примера и перевода. |
| `ru_gvr_code` | 85 | Нет отрицательного примера и ссылки на источник формата. |
| `dtxsid`, `temperature` | 90-100 | Замечаний нет. |

## Проверка существующих записей

Регулярные выражения проверены на значениях Wikidata (до 5000 на свойство):

| Свойство | Запись | Совпало |
|---|---|---|
| P3425 | `eu_natura2000_site` | все 26 854 значения, кроме двух ошибок данных (`ES701020`, `Es7020050`) |
| P884 | `ru_gvr_code` | 5000 из 5000 |
| P4136 | `wigos_station_id` | 1477 из 1478 (не совпал пустой узел Wikidata) |
| P9737 | `wmo_station_index` | 1379 из 1383 (4 индекса без ведущего нуля, например `3402`) |
| P846 | `gbif_taxon_id` | 5000 из 5000 |
| P815 | `itis_tsn` | 5000 из 5000 |
| P3117 | `dtxsid` | 5000 из 5000 |
| P850 | `worms_aphia_id` | 5000 из 5000 |

Примеры станций проверены через API OSCAR/Surface ВМО: `0-20008-0-JFJ`
(Jungfraujoch), `0-20000-0-06702` (La Dole), `0-20000-0-10962`
(Hohenpeissenberg), `0-20000-0-27612` (Москва, ВДНХ). Определение кода
Natura 2000 (девять символов: код страны ISO и семь знаков национальной
системы) проверено по пояснениям к Standard Data Form в Решении 2011/484/EU.

## Изменения существующих записей

- `emissioninventory`, `powerplantid`, `gridnode`, `waterstation`: описания
  заглушки заменены честными описаниями обобщённых типов (без regexp: у них
  нет единого формата), ссылки, переводы. `powerplantid` получил категорию
  `energy`, `gridnode` перенесён в `energy` (узел энергосети не тип
  окружающей среды). `waterstation` переименован в «Water monitoring station
  identifier», `langs: [common]`.
- `eu_natura2000_site`: ссылка на Решение 2011/484/EU, уточнение про GR и
  коды UK после 2021 года, отрицательный пример, перевод.
- `wigos_station_id`, `wmo_station_index`: ссылка на OSCAR/Surface, источники
  примеров, пример `27612`, оговорка о потере ведущих нулей, переводы.
- `gbif_taxon_id`: отрицательный пример — идентификатор новой таксономии GBIF
  2026 года (`59R5F`, P14607), перевод. `itis_tsn`: отрицательный пример,
  перевод.
- `worms_aphia_id`, `species`: добавлена категория `environment`, перевод
  для `worms_aphia_id`.
- `data/categories.yaml`: название категории уточнено — «Environment
  (protected areas, biodiversity, water, weather, emissions, waste)»; id
  не изменился.
- `ru_gvr_code`: описание уточнено — структура 23 цифр в нормативных актах
  не опубликована, regexp проверяет только длину; ссылки на статью Wikipedia
  о реестре и приказ МПР № 138, отрицательный пример.

## Новые записи (54, все `draft`)

| Группа | Записи | Wikidata |
|---|---|---|
| Охраняемые территории | `wdpa_id`, `ramsar_site_id`, `kba_site_id`, `iucn_protected_area_category`, `eu_habitat_type_code` (EU) | P809, P2525, P10343, P6436 |
| Биоразнообразие | `iucn_taxon_id`, `iucn_red_list_category`, `cites_appendix`, `cites_species_plus_id`, `inaturalist_taxon_id`, `inaturalist_observation_id`, `ebird_taxon_code`, `ebird_hotspot_id`, `envo_id`, `marine_regions_mrgid` | P627, P2040, P3151, P5683, P3444, P5200, P3859, P3006 |
| Ледники | `glims_glacier_id`, `wgi_glacier_id`, `rgi_glacier_id` | P6799, P1404 |
| Водные объекты | `eu_surface_water_body_code`, `eu_river_basin_district_code`, `eu_bathing_water_id` (EU), `us_huc`, `usgs_site_number` (родитель `waterstation`), `us_nid_dam_id` (US) | P2856, P2965, P9616, P13020, P9439 |
| Погода и климат | `ghcnd_station_id`, `koppen_climate_class`, `compass_point` | — |
| Опасные природные явления | `ibtracs_sid`, `atcf_storm_id`, `glide_number`, `emdat_disaster_number`, `usgs_earthquake_id`, `gvp_volcano_number` | P4540, P14355, P3196, P1886 |
| Качество воздуха | `air_pollutant`, `us_aqi_category`, `us_aqs_site_id`, `us_aqs_parameter_code` (US), `eu_eaqi_band` (EU) | — |
| Выбросы и парниковые газы | `ipcc_emission_category`, `greenhouse_gas`, `ghg_protocol_scope`, `us_ghgrp_facility_id`, `us_epa_tri_facility_id`, `us_epa_frs_id` (US) | P10145 |
| Электростанции (родитель `powerplantid`) | `us_eia_plant_id` (US), `gppd_id` | P10682 |
| Отходы | `eu_waste_code` (EU), `basel_waste_code`, `us_epa_hazardous_waste_code` (US), `ru_fkko_code`, `ru_groro_number` (RU) | — |
| Землепользование | `corine_land_cover_code` | — |
| Россия: воздействие на среду | `ru_nvos_object_code`, `ru_air_pollutant_code` | — |

Bioregistry: `envo`, `inaturalist.taxon`, `inaturalist.observation`.

### Проверка регулярных выражений

Совпадение с выборками Wikidata — 100% для P809 (5000), P627 (5000), P2040
(5000), P3151 (5000), P3444 (13 270), P5200 (1247), P3859 (1486), P6799
(2415), P1404 (590), P10343 (289), P2965 (25), P10682 (11 928), P10145,
P13020. Остальные:

- P2525 (Ramsar) — 1431 из 1433: текст «complexe Ramsar n° 1017» и
  ошибочное значение 16883.
- P6436 (типы местообитаний) — 233 из 234: в свойство записан код
  территории Natura 2000 `ES7020008`.
- P3006 (MRGID) — 515 из 516: текст вместо числа. Пример P1855 в Wikidata
  ошибочен (MRGID 1906 — Северный Ледовитый океан, а не Атлантический).
- P2856 (водные объекты ЕС) — 7671 из 7672. Формат самого свойства
  (`[A-Z]{2}[A-Z0-9_]+`) неверен: он отвергает дефис и принимает только 126
  значений.
- P9616 (места купания) — 985 из 995: 6 значений в нижнем регистре и 4
  хорватских с лишним дефисом.
- P9439 (NID) — 46 262 из 46 263: идентификатор сооружения с суффиксом.
- P4540 (IBTrACS) — 2767 из 2768: в свойство записан код ATCF. Формат
  свойства отвергает 63 официальных SID до 1970 года с долготой больше 359.
- P1886 (GVP), P3196 (ComCat) — все, кроме пустых узлов.
- P5683 (наблюдения iNaturalist) — 7 из 8: имя пользователя вместо номера.
- P14355 (EM-DAT) — 3 из 3; полные данные EM-DAT закрыты логином.

Проверка по полным официальным спискам:

- `eu_waste_code` — 842 кода редакции 2015 года и 880 кодов консолидации с
  поправкой 2025/934, в четырёх написаниях (с пробелами и без, со
  звёздочкой и без).
- `basel_waste_code` — все 174 кода, включая поправки 2021 и 2025 годов.
- `us_epa_hazardous_waste_code` — 574 кода 40 CFR part 261.
- `ipcc_emission_category` — 281 код таблицы 8.2.
- `corine_land_cover_code` — ровно 44 класса третьего уровня.
- `eu_habitat_type_code` — 233 кода консолидированного Приложения I.
- `eu_surface_water_body_code` — 188 330 кодов WISE; `eu_bathing_water_id` —
  31 909; `eu_river_basin_district_code` — 230.
- `us_epa_tri_facility_id`, `us_epa_frs_id`, `us_ghgrp_facility_id`,
  `us_aqs_site_id`, `us_aqs_parameter_code`, `us_nid_dam_id`, `us_huc`,
  `usgs_site_number`, `ghcnd_station_id`, `ibtracs_sid`, `atcf_storm_id`,
  `glide_number`, `gppd_id`, `wgi_glacier_id`, `ebird_taxon_code`,
  `gvp_volcano_number` — все значения выгрузок, перечисленных в источниках
  (кроме 4 идентификаторов NID с пробелом в конце).
- `ru_fkko_code` — 9170 из 9170 кодов полного текста ФККО (опечатка
  источника `4 19 700 00 000` не совпадает); 5872 из 5890 кодов открытых
  данных ФККО 2014 года (остальное — опечатки файла).
- `ru_groro_number` — 103 из 103 номеров из 20 приказов Росприроднадзора
  2023–2025 годов (буквы Х и З кириллические, даты корректны).
- `ru_air_pollutant_code` — 2345 кодов справочника НИИ Атмосфера (2005) и
  162 кода формы 2-ТП (воздух) 2026 года.

Итог по категории `environment` (оценка `metacrafter-registry report`):

| | Записей | Средняя оценка | Минимальная |
|---|---:|---:|---:|
| До | 12 | 66,3 | 20 |
| После | 67 | 83,7 | 40 (`waterstation`: обобщённый тип без формата) |

## Что не сделано и почему

- **Формат выведен из данных, а не из документа.**
  - `us_epa_frs_id` (префикс 110), `us_ghgrp_facility_id` (диапазон
    1000001–1015132), `us_epa_tri_facility_id` (буква W вместо пятой цифры
    ZIP у 11 083 объектов не объяснена EPA), `eu_bathing_water_id`, `gppd_id`
    (формат подтверждён кодом WRI `make_id()`).
  - `ebird_taxon_code`, `ebird_hotspot_id`: eBird не публикует правила
    кодов; подсказанные форматы (`L\d{6,7}`) оказались неверны (есть L11).
  - `rgi_glacier_id`: только RGI 7.0; пять цифр номера выведены из примеров
    руководства и размера крупнейшего региона. Форма RGI 6.0 (`RGI60-…`) не
    подтверждена.
- **Слабая проверка.** `emdat_disaster_number` — 3 значения Wikidata и
  документация EM-DAT. `ru_air_pollutant_code` — актуальной редакции
  справочника после 2005 года в открытом доступе нет; regexp `^\d{4}$`
  распознаёт тип только по имени столбца.
- **`ru_nvos_object_code`.** Структура взята из приказа № 553. Два примера —
  коды из названий документов Росприроднадзора на rpn.gov.ru; сами документы
  открыть не удалось, поэтому описания примеров не называют
  природопользователей. Перед переводом в `stable` проверить примеры.
- **`ru_gvr_code`.** Значение позиций 23-значного кода не опубликовано.
  Похоже, что первые 9 цифр — код водохозяйственного участка (по одному
  документу о водопользовании), но это не подтверждено.
- **Не добавлены:**
  - `wqx_monitoring_location_id` — схема WQX допускает любые символы до 55
    знаков, префикс не всегда совпадает с организацией.
  - `ru_hydro_study_code` (P14399, «Гидрологическая изученность») — нет
    авторитетного описания; textual.ru показывает другой, 9-значный вид кода.
    В формате свойства опечатка `[2|4]`.
  - `ru_waste_license_number` — старые номера лицензий не нормированы, новые
    уже описаны записью `ru_license_erul`.
  - `ru_oopt_id` — нет ни свойства Wikidata, ни устойчивого кода кадастра ООПТ.
  - `gem_unit_id` (Global Energy Monitor) — данные трекеров закрыты
    регистрацией; P13333 — имя вики-страницы, а не код трекера.
  - Коды балансирующих зон EIA-930 и номера установок EU ETS — кандидаты
    для ревизии категории `energy`.
- **Проблемы ссылок.** iucnredlist.org, cites.org, rsis.ramsar.org,
  usgs.gov, volcano.si.edu, eia.gov, unfccc.int отвечают ботам 403/418/503.
  Ссылки оставлены: это адреса выпускающих организаций, часть из них
  открылась через WebFetch. rpn.gov.ru во
  время работы начал отклонять запросы с этой машины после постраничной
  выгрузки каталога ФККО.
- **Статус.** Все записи остаются `draft`. Кандидаты в `stable` после
  проверки человеком: `eu_natura2000_site`, `wdpa_id`, `eu_waste_code`,
  `basel_waste_code`, `us_epa_hazardous_waste_code`, `corine_land_cover_code`,
  `eu_habitat_type_code`, `ghcnd_station_id`, `ibtracs_sid`, `ru_fkko_code`.

## Находки для metacrafter-rules

- Шаблоны значений правил `enemisvalue` (`\d{2,6}-[A-Za-z0-9]{1,4}`),
  `enenergypointvalue` (`[A-Z]{2}\d{3,6}`) и `engridnodevalue`
  (`[A-Z]{3}-\d{2,4}`) не соответствуют ни одному найденному стандарту:
  коды EIA — 1–5 цифр, GPPD — 3 или 5 букв и 7 цифр. Их стоит убрать или
  заменить правилами для конкретных записей.
- Распознаются по значению: `glims_glacier_id`, `rgi_glacier_id`,
  `wgi_glacier_id`, `envo_id` (формы `ENVO:`/`ENVO_`), `glide_number`,
  `ibtracs_sid`, `atcf_storm_id`, `ghcnd_station_id`, `koppen_climate_class`,
  `us_epa_tri_facility_id`, `gppd_id`, `ipcc_emission_category`,
  `basel_waste_code`, `us_epa_hazardous_waste_code`, `eu_waste_code` (с
  пробелами), `greenhouse_gas`, `ghg_protocol_scope`, `ru_groro_number`,
  `ru_nvos_object_code`, `ru_fkko_code` (с пробелами), `us_epa_frs_id`,
  `us_aqi_category`, `eu_eaqi_band`.
- Только по имени столбца: голые числа (`wdpa_id`, `ramsar_site_id`,
  `iucn_taxon_id`, `cites_species_plus_id`, `inaturalist_*`,
  `marine_regions_mrgid`, `kba_site_id`, `us_huc`, `usgs_site_number`,
  `gvp_volcano_number`, `us_eia_plant_id`, `us_ghgrp_facility_id`,
  `us_aqs_parameter_code`, `corine_land_cover_code`, `ru_air_pollutant_code`),
  а также `iucn_red_list_category` (EN, CR совпадают с кодами стран и языков),
  `cites_appendix` и `iucn_protected_area_category` (римские цифры),
  `air_pollutant` (CO, NO — коды штата и страны), `compass_point`.
- Коды водных объектов, бассейновых округов и мест купания ЕС имеют один
  формат и по значению не различаются.
