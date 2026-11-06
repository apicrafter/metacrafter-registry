# Имена полей из каталогов открытых данных: типы, которых нет в реестре (2026-11-06)

Цель: по именам полей из нескольких каталогов открытых данных найти
семантические типы, которых сейчас нет в реестре.

## Исходные данные

Репозиторий `apicrafter/metacrafter-datacatalogs-raw`, слепок 2022 года
(февраль–май). Значений полей в нём нет: только имена. Для Socrata есть ещё
тип колонки и её описание.

| Каталог | Файл | Наборов | Строк (поле в файле) |
|---|---|---:|---:|
| data.gov.ru | `fields_short.csv.xz` | 15 181 | 134 700 |
| data.gov.uk | `fields_short.csv.xz` | 8 491 | 2 075 049 |
| data.opendatasoft.com (ODS) | `fields_short.csv.xz` | 23 684 | 399 941 |
| socrata.com (295 доменов) | `fields_full.csv.xz` | 40 137 | 840 201 |

## Метод

1. Нормализация имени: исправление двойной перекодировки CP1251/UTF-8 в
   файлах UK и ODS (`п»ї`, `Г§`), удаление BOM, разбиение camelCase, нижний
   регистр, все небуквенные символы заменены на `_`. Служебные колонки
   Socrata `:@computed_region_*` отброшены. Получилось 437 223 разных имени.
2. Частота имени — число разных наборов, где оно встречается, а не число
   файлов. В data.gov.uk один набор часто состоит из сотен файлов.
3. Сопоставление с существующими типами. Имя считается распознанным, если
   выполнено одно из условий:
   - сработало полевое правило metacrafter-rules (локальная копия, коммит
     `1982330`; правила загружены `RulesProcessor` из metacrafter: 2780
     ключевых слов и 20 правил pyparsing);
   - имя совпало с `id`, алиасом, `name` или переводом `name` записи из
     `data/datatypes_latest.jsonl` (1867 записей).

   Проверялись исходное имя, нормализованное, без `_` и без числового
   суффикса (`location_1`).
4. Нераспознанные имена, которые встречаются в 3 и более наборах (74 572
   имени), разобраны вручную по убыванию частоты. Отдельно проверены
   имена-кандидаты на идентификаторы (`code`, `id`, `num`, `код` и т. п.).
5. Каждый кандидат проверен поиском по `id`, `name` и полному тексту YAML
   в `data/datatypes/`.

## Охват сейчас

| Каталог | Распознано вхождений (набор × поле) |
|---|---:|
| data.gov.ru | 33,8 % |
| data.gov.uk | 19,6 % |
| ODS | 18,2 % |
| Socrata | 14,2 % |
| Всего | 17,5 % |

Распознано 4017 из 74 572 имён. Большая часть остальных имён — показатели
(`value`, `total`, `amount`, `count`), месяцы и годы в заголовках широких
таблиц, вопросы анкет. Семантическими типами они не являются.

Главный вывод: новых типов достаточно для нескольких десятков записей. Но
охват сильнее вырастет, если научить metacrafter-rules распознавать имена
полей для типов, которые в реестре уже есть (раздел 3).

## 1. Кандидаты в новые типы

«Наборы» — число наборов, где встречается хотя бы одно из имён группы.
«Где» — каталог и, если известно, число доменов Socrata или порталов ODS.
Структура кода указана только там, где она известна из стандарта или из
описания колонки в Socrata. Значений в слепке нет, поэтому перед созданием
записей формат нужно сверить с первоисточником и с данными.

### 1.1. Сильные кандидаты: стандартный код, много наборов или источников

| Предлагаемый id | Что это | Наборы | Где | Имена полей (наборов) | Структура |
|---|---|---:|---|---|---|
| `unit_of_measure` | Единица измерения: название или обозначение | 2222 | все 4 каталога; Socrata 60+ доменов | `Unit` (650), `Единица измерения` (241), `units` (222), `enhet` (201), `unite` (129), `unit_of_measure` (86) | Свободный текст. Для кодов — отдельные паттерны `unece_rec20_unit_code` (UN/ECE Rec 20: `KGM`, `MTR`) и `ucum_code` (`kg`, `m/s`). В реестре есть только `okei`, `okeiname` (РФ) и `etim_unit_code`. |
| `us_census_tract` | Переписной участок (tract) Бюро переписи США | 1100 | Socrata, 32 домена | `census_tract` (512), `tract` (271), `tract_number` (115), `tractce` (41) | 6 цифр, часто с точкой (`1011.10`). |
| `us_census_geoid` | GEOID географии переписи США | 826 | Socrata, 50 доменов | `geoid` (588), `geo_id` (87), `geoid10` (47), `affgeoid` (39) | Число цифр зависит от уровня: штат 2, округ 5, tract 11, block group 12, block 15. Вариант AFFGEOID — с префиксом уровня (`1400000US…`). |
| `us_census_block_group` | Группа кварталов переписи США | 120 | Socrata | `census_block_group` (30), `block_group` (20) | 12 цифр в составе GEOID. Можно сделать паттерном `us_census_geoid`. |
| `us_cbsa` | Core-Based Statistical Area (агломерация) | 184 | Socrata | `cbsa_name` (101), `cbsa` (49), `cbsa_code` (16), `msa` (9) | Код из 5 цифр или название. |
| `week_of_year`, `iso_week`, `epi_week` | Номер недели в году; ISO-неделя; эпидемиологическая неделя CDC MMWR | 520 | Socrata (3 домена для MMWR), ODS | `mmwr_week` (311), `week` (129), `semana` (22), `semaine` (15) | 1–53; ISO 8601 `2021-W05`; MMWR по описанию Socrata — `YYYYWW`. В реестре нет ни одного типа недели, есть только `dayofweek`. |
| `nyc_borough` | Боро Нью-Йорка | 950 | Socrata, 5 доменов | `borough` (731), `boro` (140), `borocode` (46) | 5 значений; коды `1`–`5` или `MN`, `BX`, `BK`, `QN`, `SI`. Имя `borough` есть и в данных Лондона (там `ukboroughcode`). |
| `nyc_bbl` | Borough-Block-Lot, налоговый участок NYC | 546 | Socrata, 4 домена | `bbl` (374), `*_boro_block_lot` (90) | 10 цифр: боро 1, квартал 5, участок 4. |
| `nyc_dbn` | District-Borough-Number школы NYC | 477 | Socrata, 2 домена | `dbn` (434), `school_dbn` (34) | Например `01M015`: округ 2 цифры, буква боро, номер 3 цифры. |
| `nyc_community_district` | Community district (community board) NYC | 432 | Socrata, 3 домена | `community_board` (367), `community_district` (39), `borocd` (24) | 3 цифры: код боро и номер округа (по описанию колонки). |
| `nyc_nta` | Neighborhood Tabulation Area NYC | 398 | Socrata | `nta` (350), `nta_name` (20), `ntacode` (18) | 2010: `BK09`; 2020: `BK0101`. |
| `nyc_bin` | Building Identification Number NYC | 391 | Socrata | `bin` (388) | 7 цифр, первая — код боро. Имя `bin_number` в данных о скорости означает интервал, а не здание. |
| `fr_canton` | Кантон (Франция) | 721 | ODS, 42–46 порталов | `canton` (283), `code_canton` (142), `nom_canton` (109), `numero_canton` (65) | Код департамента и номер кантона; формат проверить по COG INSEE. Сейчас есть только `ch_canton`. |
| `fr_arrondissement` | Округ департамента и муниципальный округ (Париж, Лион, Марсель) | 563 | ODS, 24–64 портала | `arrondissement` (128), `codearrondissementetablissement` (110), `com_arm_code` (83), `arrdep_code` (63) | Муниципальные округа: 75101–75120, 13201–13216, 69381–69389. |
| `fr_iris` | Ячейка IRIS INSEE | 296 | ODS, 36 порталов | `iris` (104), `code_iris` (56), `nom_iris` (43) | 9 знаков: код коммуны INSEE (5) и 4 цифры. |
| `fr_nic` | NIC — номер заведения в SIRET | 291 | ODS, 72 портала | `nic` (196), `nicsiegeunitelegale` (84) | 5 цифр; SIRET = SIREN (9) + NIC (5). |
| `fr_categorie_juridique` | Категория юридической формы INSEE | 336 | ODS, 32–62 портала | `forme_juridique` (112), `categoriejuridiqueunitelegale` (84) | 4 цифры (уровень III). |
| `fr_tranche_effectifs` | Код размера штата Sirene | 256 | ODS, 62 портала | `trancheeffectifsetablissement` (85), `trancheeffectifsunitelegale` (84) | `NN`, `00`, `01`, `02`, `03`, `11`, `12`, `21`, `22`, `31`, `32`, `41`, `42`, `51`, `52`, `53`. |
| `fr_insee_zonage` (несколько типов) | Зоны занятости, городские единицы, бассейны жизни, ареалы притяжения городов | 572 | ODS, ~29 порталов | `ze2010_code`, `ze2020_code`, `uu2010`, `bv2012_code`, `com_aav2020_code` | Коды INSEE; формат каждого зонирования проверить. |
| `fr_academie` | Академия (учебный округ) | 240 | ODS, 22–37 порталов | `academie` (117), `code_academie` (76), `libelle_academie` (47) | Закрытый перечень; формат кода проверить. |
| `fr_circonscription_legislative` | Законодательный округ | 387 | ODS, 25 порталов | `nom_circonscription` (98), `numero_circonscription` (63), `circonscription` (57) | Номер внутри департамента; формат проверить. |
| `fr_code_greffe` | Код суда (greffe), где ведётся RCS | 234 | ODS, 25–29 порталов | `greffe` (137), `code_greffe` (89) | Код из 4 цифр (проверить). |
| `fr_cedex` | Код CEDEX | 573 | ODS, 21 портал (`cedex`) | `cedex` (117), `codecedexetablissement` (84) | 5 цифр, как почтовый индекс. 336 из 573 наборов — копии выгрузки Sirene. |
| `fr_pcs` | Профессия или социально-профессиональная категория (PCS INSEE) | 123 | ODS, 26 порталов | `code_de_la_categorie_socio_professionnelle` (43), `csp` (26), `pcs` (8) | Группа 1 цифра, категория 2 цифры, профессия 4 знака (`372a` в PCS 2003). |
| `fr_chapitre_budgetaire`, `fr_compte_nature`, `fr_fonction_budgetaire`, `fr_nomenclature_budgetaire` | Бюджетная классификация местных бюджетов (M14, M57) | 2209 | ODS, 5–44 портала | `libelle_article` (276), `libelle_chapitre` (272), `chapitre` (250), `article` (215), `fonction` (200), `nomenclature` (124) | Глава, счёт по природе, функциональный код, сама номенклатура (`M14`, `M57`). Имена `article` и `fonction` неоднозначны, оценка завышена. |
| `fr_actes_matiere` | Классификация актов (@ctes) в выгрузках решений | 204 | ODS, 25 порталов | `delib_matiere_code` (100), `delib_matiere_nom` (102) | Код вида `1.1` (проверить). |
| `fr_bureau_de_vote` | Избирательный участок | 676 | ODS; `bureau_de_vote` 11 порталов, `code_bureau` 3 | `bureau_de_vote` (130), `code_bureau` (93), `uniq_bdv` (83) | Номер внутри коммуны; единого формата нет. |
| `co_estrato` | Социально-экономическая страта жилья (Колумбия) | 363 | Socrata (datos.gov.co, 2 домена) | `estrato` (143), `estratopri` (78), `estratosec` (31) | 1–6. |
| `co_divipola` | Код DIVIPOLA (DANE) департамента или муниципалитета | ~400 | Socrata | `codigo_dane` (64), `cod_dane_m` (57), `c_digo_divipola_municipio` (10) | Департамент 2 цифры, муниципалитет 5 цифр. `co_department` и `co_municipality` в реестре — только названия. |

### 1.2. Средние кандидаты: узкий источник, локальный код или нет формата

| Предлагаемый id | Что это | Наборы | Где | Имена полей (наборов) | Замечание |
|---|---|---:|---|---|---|
| `school_grade_level` | Класс школы (США) | 421 | Socrata, 11 доменов | `grade_level` (157), `gradetested` (125), `gradelevel` (108) | `PK`, `K`, `01`–`12`; описание колонки: «two-character alphanumeric identifier of a school grade». |
| `political_party`, `fr_nuance_politique` | Партия; политический оттенок списка во Франции | 287 | Socrata 16 доменов, ODS 15 порталов | `party` (162), `nuance_liste` (43), `nuance` (32), `code_nuance` (18) | Перечни зависят от страны и выборов. |
| `osm_amenity`, `osm_wheelchair` и др. | Значения тегов OpenStreetMap | 1408 | ODS, 9–11 порталов | `amenity` (472), `wheelchair` (470), `highway` (103), `leisure` (96), `tourism` (96) | Выгрузки OSM. В реестре есть `osm_id` и другие id, значений тегов нет. `wheelchair`: `yes`, `limited`, `no`, `designated`. |
| `gtfs_route_type`, `gtfs_stop_id`, `gtfs_route_id` | Поля фидов GTFS | 526 | ODS, Socrata 15 доменов | `route_id` (109), `stop_id` (94), `route_type` (69), `stop_code` (55), `wheelchair_boarding` (49) | У `route_type` закрытый список кодов. `stop_id` и `route_id` уникальны только внутри фида. |
| `eunis_habitat_code`, `gb_jncc_biotope_code` | Код местообитания EUNIS; биотоп морской классификации JNCC | 435 | UK (одна серия, 351), ODS 70 | `HabitatCode` (351), `cod_eunis` (17) | EUNIS вида `A5.23`. Что именно в UK `HabitatCode`, проверить по данным. |
| `sacfor_abundance` | Шкала обилия SACFOR | 346 | UK, одна серия наборов | `Abundance_SACFORN` (346) | `S`, `A`, `C`, `F`, `O`, `R` и `N` (не найдено). |
| `gb_civil_service_grade` | Грейд госслужбы Великобритании | 269 | UK, серия штатных расписаний | `Grade (or equivalent)` (269) | `SCS1`–`SCS4`, `Grade 6`, `Grade 7`, `SEO`, `HEO`, `EO`, `AO`, `AA`. |
| `animal_breed` | Порода животного (код или название) | 552 | UK 457, Socrata 65 | `Breed Type` (188), `Breed` (133), `DAM BREED CODE` (25) | Справочник кодов пород проверить. |
| `us_congressional_district` | Округ Палаты представителей США | 220 | Socrata, в основном одна серия USAspending | `legalentitycongressional` (134), `congressional_district` (26) | Номер внутри штата. Близкий тип — `ocd_division_id`. |
| `us_city_council_district`, `us_precinct` | Округ городского совета; полицейский или избирательный участок | 586 и 252 | Socrata, 23 и 27 доменов | `council_district` (450), `precinct` (210) | Просто номера, формата нет. |
| `zoning_district` | Код зонирования | 146 | Socrata, 22 домена | `zoning` (125), `zoning_district` (18) | Локальные коды (`R-1`, `C-2`), общего формата нет. |
| `us_epa_aqs_parameter_code` | Код параметра (загрязнителя) EPA AQS | 208 | Socrata, 3 домена | `parameter_code` (106), `pollutant_standard` (102) | 5 цифр (`44201` — озон, `88101` — PM2.5). |
| `mcc` | Merchant Category Code (ISO 18245) | 58 | UK 42, ODS 10, Socrata 6 | `Merchant Category` (23), `MCC` (12) | 4 цифры. В UK одна серия выписок по картам (`MCH.MCC DESCRIPTION`) занимает 4154 файла. |
| `ocds_ocid`, `ocds_procurement_method` | Идентификатор процедуры OCDS; способ закупки | 154 | UK (Contracts Finder) | `ocid` (75), `procurementMethod` (79) | `ocds-` + префикс издателя + локальный id; перечень `open`, `selective`, `limited`, `direct`. |
| `us_fec_committee_id` | Идентификатор комитета FEC | 41 | Socrata, 2 домена | `cmte_id` (28), `committee_id` (13) | `C` и 8 цифр. |
| `eu_wfd_water_body_id` | Идентификатор водного объекта по Водной рамочной директиве | 90 | UK | `RWB_ID_RBP2` (84), `eu_cd` (6) | В UK — `GB` и 12 цифр. |
| `gb_lgsl` | Local Government Service List | 66 | UK | `ServiceTypeURI` (66) | URI услуги в справочнике ESD; проверить. |
| `us_zcta`, `us_puma` | ZIP Code Tabulation Area; Public Use Microdata Area | 33 и 41 | Socrata | `zcta` (18), `zcta5ce10` (7), `puma` (31) | 5 цифр. |
| `device_type`, `operating_system`, `browser_name` | Тип устройства, ОС, браузер | 851 | Socrata, 1 домен | `devicetype` (281), `browsertype` (275), `ostype` (268) | Почти всё — служебные поля опросов одного портала. |

### 1.3. Россия (data.gov.ru)

| Предлагаемый id | Что это | Наборы | Имена полей (наборов) | Замечание |
|---|---|---:|---|---|
| `row_number` | Порядковый номер строки | 2753 | `№ п/п` (1623), `_p_p` (769), `poryadkovyy_nomer` (111), `№ пп` (59) | Самое частое нераспознанное поле data.gov.ru. Это не тип значения, а служебная колонка. Её лучше пропускать, чем считать идентификатором. Решить: запись в реестре или правило игнорирования в metacrafter. |
| `okato_name` | Название объекта ОКАТО | 190 | `okato_name` (190) | Есть `okato` (код) и `oktmoname`; парной записи для названий ОКАТО нет. |
| `ru_forest_use_type` | Вид использования лесов | 174 | `Вид использования лесов` (141) | Уже предложен в `DATA_GOV_RU_2026-11.md` (раздел 3); записи пока нет. Имена полей здесь это подтверждают. |

Остальные частые российские поля — реквизиты лицензий, свидетельств об
аккредитации, проверок, охотничьих угодий. Это составные тексты без единого
формата, и по одним именам тип не выделить. Типы, найденные по значениям,
описаны в `DATA_GOV_RU_2026-11.md`.

### 1.4. Технические поля

| Группа | Наборы | Имена полей (наборов) | Замечание |
|---|---:|---|---|
| Площадь и длина геометрии ГИС (ESRI) | 7425 | `shape_area` (1735), `shape_length` (1253), `st_lengthshape` (939), `st_areashape` (928), `shape_leng` (705) | Служебные поля geodatabase, числа в единицах системы координат. Семантическим типом это не назвать, но поля очень частые. Лучше пропускать их в metacrafter. |

## 2. Сводка по приоритету

1. Мировые стандарты и большой охват: `unit_of_measure` (с паттернами Rec 20
   и UCUM), `week_of_year`, `iso_week`, `epi_week`, `mcc`, `ocds_ocid`.
2. География переписи США: `us_census_tract`, `us_census_geoid` (паттерны по
   уровням), `us_cbsa`, затем `us_zcta`, `us_puma`.
3. Франция, INSEE и Sirene: `fr_iris`, `fr_canton`, `fr_arrondissement`,
   `fr_nic`, `fr_categorie_juridique`, `fr_tranche_effectifs`, `fr_pcs`,
   зонирования INSEE, `fr_academie`, `fr_circonscription_legislative`,
   `fr_code_greffe`, `fr_cedex`.
4. Бюджетная классификация Франции (M14, M57).
5. Нью-Йорк: `nyc_bbl`, `nyc_bin`, `nyc_dbn`, `nyc_nta`,
   `nyc_community_district`, `nyc_borough`. Это коды одного города, но NYC
   Open Data — один из крупнейших порталов Socrata.
6. Колумбия: `co_divipola`, `co_estrato`.
7. Средние кандидаты из раздела 1.2 — по мере появления значений для
   проверки.

## 3. Типы есть в реестре, но имена полей не распознаются

Это задачи для metacrafter-rules, а не для реестра. Здесь учтены только
имена, которые сейчас не распознаёт ни одно правило.

| Тип реестра | Наборы | Нераспознанные имена (наборов) |
|---|---:|---|
| `geopoint`, `wkt`, `geojson` | 12 931 | `location` (3264), `the_geom` (2786), `location_1` (2041), `geocoded_column` (709), `localisation` (635), `geom` (599) |
| `fr_department`, `fr_department_code` | 4363 | `departement` (1282), `code_departement` (569), `dep_name` (463), `dep_code` (458), `nom_dep` (313), `nom_dept` (218) |
| `address` | 3521 | `adresse` (1866), `direccion` (317), `direcci_n` (197), `varc_address` (193), `adr` (153) |
| `latitude`, `longitude` | 3507 | `lat` (1278), `long` (1018), `lon` (202), `координата_y` (167), `x_coordinate` (146) |
| `uscounty` | 3143 | `county` (2465), `county_name` (423), `sitecounty` (124), `countyname` (123) |
| `inseecode`, `fr_commune` | 3089 | `code_commune` (537), `nom_com` (299), `nom_commune` (272), `codgeo` (258), `libgeo` (249) |
| `fr_region`, `fr_region_code` | 2140 | `reg_code` (520), `code_region` (440), `reg_name` (431), `nom_reg` (393) |
| `year` | 2139 | `a_o` (= `año`, 497), `exercice` (444), `fy` (416), `vigencia` (210), `calendar_year` (192) |
| `gender` | 1799 | `sex` (694), `sexe` (336), `sexo` (317), `genero` (285), `code_sexe` (95) |
| `city` | 1615 | `ville` (940), `localidad` (134), `naselennyy_punkt` (131), `localite` (104) |
| `url` | 1436 | `web` (529), `link` (367), `site_web` (335), `lien` (123) |
| `easting`, `northing` | 1296 | `bng_e` (523), `bng_n` (523), `geo_x` (125), `geo_y` (125) |
| `opening_hours` | 1283 | `schedule` (441), `shedule` (208), `horaires` (167), `rezhim_raboty` (133), `график_работы` (127) |
| `buildingnumber` | 1129 | `addr_housenumber` (364), `street_number` (176), `dom` (136), `house_number` (56) |
| `race_ethnicity` | 1064 | `race` (624), `ethnicity` (181), `hispanic` (180), `etnia` (71) |
| `phone` | 918 | `tel` (363), `mobile_phone` (141), `varc_phone` (96), `tel_fono` (77), `faks` (63) |
| `street` | 865 | `addr_street` (373), `rue` (220), `nom_voie` (145), `voie` (105) |
| `language` | 862 | `idioma` (839) |
| `person_fullname` | 803 | `chief` (421), `cheif` (101), `f_i_o_rukovoditelya` (82), `director` (72) |
| `co_department` | 688 | `departamento` (625), `dpto` (36) |
| `oktmoname` | 687 | `munitsipalnoe_obrazovanie` (411), `geodata_munitsobr` (121), `муниципальное_образование` (52) |
| `email` | 624 | `mail` (187), `courriel` (151), `varc_email` (81), `elektronnaya_pochta` (63) |
| `fr_naf` | 447 | `code_ape` (145), `activiteprincipaleunitelegale` (86), `code_naf` (45) |
| `country` | 396 | `pays` (185), `pais` (162), `land` (43) |
| `district` | 363 | `districtname` (193), `rayon` (89), `район` (81) |
| `worms_aphia_id` | 346 | `aphia_id` (346) |
| `age_range` | 329 | `age_group` (223), `agegroup` (32), `grupo_edad` (19) |
| `postindex`, `de_postcode`, `frpostcode` | 228 | `codepostal` (105), `plz` (102), `addr_postcode` (21) |
| `fr_uai` | 193 | `uai` (68), `ref_uai` (33), `numero_uai` (28), `code_rne` (21) |
| `fips52`, `fips64` | 181 | `fips` (181) |
| `co_nit` | 168 | `nit` (135), `n_mero_nit` (19) |
| `fr_finess` | 140 | `ref_fr_finess` (52), `finess` (45) |
| `ru_mos_metro_station` | 139 | `metro` (99), `nearest_subway_station` (40) |
| `marital_status` | 107 | `estado_civil` (104) |
| `wikidataid` | 87 | `wikidata` (31), `identifiant_wikidata` (13) |
| `org_id_scheme` | 77 | `scheme` (77, OCDS в UK) |
| `ch_bfs_gemeinde` | 74 | `bfs_nr_gemeinde` (71) |
| `usdeanumber` | 64 | `reporter_dea_no` (25), `buyer_dea_no` (25) |
| `rufias` | 62 | `kod_fias` (62) |
| `gb_vat` | 53 | `vat_registration_number` (50) |
| `epsg_code` | 37 | `epsg` (37) |
| `ukgsscode` | 928 | 82 варианта вида `<код уровня><год>cd`: `oa11_cd` (47), `lad11cd` (34), `lad17_cd` (30), `pcon15cd` (27), `ccg17cd`, `wd15cd` |

## 4. Ложные срабатывания правил

Замечены при сопоставлении. Это тоже задачи для metacrafter-rules.

- `адрес` получает `phone` вместе с `address`, а `телефон` — `address`
  вместе с `phone`.
- `инн` и `огрн` дополнительно получают `name`.
- `dep` получает `package_name`. В ODS и Socrata это код департамента (то же
  отмечено в `DATA_GOV_RU_2026-11.md`).
- `zip` и `code_postal` получают `ca_postalcode` (канадский индекс), а не
  общий `postindex`.
- `title` получает `headline`.
- `postcode` и `zip_code` получают сразу до 11 страновых индексов
  (`aepostcode`, `egpostcode`, `krpostcode` и т. д.). Кроме того, запись
  реестра с id `postcode` описывает китайский индекс, хотя id выглядит общим.

## Ограничения

- В слепке только имена полей. Структура кодов в таблицах взята из стандартов
  и описаний колонок Socrata, а не проверена на значениях.
- Слепок 2022 года; часть наборов с тех пор изменилась.
- Частоты завышены сериями наборов. В data.gov.uk это штатные расписания
  ведомств, Contracts Finder (OCDS) и выгрузки Marine Recorder. В ODS один
  набор (выгрузка Sirene, справочники georef) скопирован на десятки порталов.
  Для таких полей указано число порталов или доменов.
- Нормализация простая. Часть имён неоднозначна: `unit`, `grade`, `bin`,
  `borough`, `article`, `fonction`, `party`.

## Что дальше

1. Создать черновики (`status: draft`) для групп 1–3 из раздела 2. Формат
   сверить с первоисточниками (Census Bureau, INSEE, UN/ECE, CDC, OCDS).
   Примеры значений взять из реальных данных через API Socrata и ODS.
2. Передать раздел 3 и раздел 4 в metacrafter-rules.
3. Решить, нужны ли в реестре служебные типы (`row_number`, метрики геометрии
   ГИС) или достаточно правила игнорирования в metacrafter.

## Созданные записи (группы 1–3)

Все записи созданы как `status: draft`. Формат каждого кода сверен с
первоисточником. Примеры взяты из документации или справочных файлов.

| Запись | Тип | Файл | Источник формата |
|---|---|---|---|
| `unit_of_measure` | datatype | `any/values/` | Wikipedia, Wikidata Q47574 |
| `unece_rec20_unit_code` | pattern → `unit_of_measure` | `any/values/` | UNECE Rec 20, Wikidata P6512 |
| `ucum_code` | pattern → `unit_of_measure` | `any/values/` | ucum.org, Wikidata P7825 |
| `week_of_year` | datatype | `any/datetime/` | ISO 8601 |
| `iso_week` | datatype | `any/datetime/` | ISO 8601 |
| `epi_week` | datatype, parent `week_of_year` | `any/datetime/` | CDC, памятка MMWR Week |
| `merchant_category_code` | datatype | `any/finances/` | ISO 18245, руководство Visa, Wikidata P4573 |
| `ocds_ocid` | datatype | `any/government/` | документация OCDS 1.1.5 |
| `us_census_geoid` | datatype | `US/geo/` | Census Bureau, страница о GEOID |
| `us_census_geoid_fq` | pattern → `us_census_geoid` | `US/geo/` | data.census.gov, Census Data API |
| `us_census_tract` | datatype | `US/geo/` | TIGER/Line 2023 |
| `us_census_block_group` | datatype, parent `us_census_geoid` | `US/geo/` | Census Bureau, глоссарий и GEOID |
| `us_cbsa` | datatype | `US/geo/` | Census Bureau, глоссарий; файл CBSA 2023 |
| `us_zcta` | datatype | `US/geo/` | Census Bureau, страница о ZCTA |
| `us_puma` | datatype | `US/geo/` | TIGER/Line 2023; список PUMA 2020 |
| `fr_iris_code` | datatype | `FR/geo/` | INSEE |
| `fr_canton_code` | datatype | `FR/geo/` | COG 2026 (INSEE), Wikidata P2506 |
| `fr_arrondissement_code` | datatype | `FR/geo/` | COG 2026 (INSEE), Wikidata P3423 |
| `fr_arrondissement_municipal_code` | datatype, parent `inseecode` | `FR/geo/` | INSEE |
| `fr_nic` | datatype | `FR/companies/` | INSEE |
| `fr_categorie_juridique` | datatype | `FR/companies/` | INSEE, nomenclature 2022 |
| `fr_tranche_effectifs` | datatype | `FR/companies/` | README Etalab `sirene_as_api` |
| `fr_pcs` | datatype | `FR/persons/` | INSEE, PCS 2020 и PCS 2003 |
| `fr_zone_emploi_code` | datatype | `FR/geo/` | INSEE |
| `fr_unite_urbaine_code` | datatype | `FR/geo/` | INSEE |
| `fr_aire_attraction_villes_code` | datatype | `FR/geo/` | INSEE |
| `fr_bassin_vie_code` | datatype | `FR/geo/` | INSEE |
| `fr_academie_code` | datatype | `FR/education/` | справочник школ data.education.gouv.fr |
| `fr_circonscription_legislative_code` | datatype | `FR/geo/` | итоги выборов 2024 (МВД, data.gouv.fr) |
| `fr_cedex` | datatype | `FR/geo/` | La Poste (памятка UPU по адресам Франции) |

Что не до конца проверено:

- `fr_code_greffe` не создан. Формат кода суда найти не удалось: в XSD INPI
  это строка без ограничений, а список Infogreffe закрыт.
- `fr_iris_code`: то, что 4 последних символа — цифры, видно по примерам.
  Явно INSEE этого не пишет.
- `fr_tranche_effectifs`: коды взяты из README Etalab, документация INSEE
  была недоступна.
- `fr_zone_emploi_code`, `fr_unite_urbaine_code`,
  `fr_aire_attraction_villes_code`, `fr_bassin_vie_code`: регулярных
  выражений нет, потому что формат кодов в заморских территориях не
  проверен. У `fr_bassin_vie_code` нет и примера.
- `epi_week`: форма `YYYYWW` описана в `doc`, но в регулярное выражение не
  входит, потому что совпадает с `YYYYMM`.
- `us_census_tract`: регулярное выражение не учитывает зарезервированные
  диапазоны номеров. TIGER/Line 2023 и критерии 2020 года описывают их
  по-разному.
- `us_cbsa`: соответствие Wikidata P882 (FIPS 6-4) не указано, потому что это
  другой код.
