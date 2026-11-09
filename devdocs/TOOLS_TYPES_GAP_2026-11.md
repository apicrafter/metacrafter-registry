# Типы из документации новых инструментов, которых нет в реестре (2026-11-09)

Цель: найти в документации семи инструментов, добавленных 2026-11-09,
семантические типы, которых нет в реестре и которые можно добавить.

Инструменты: `githubsecretscanning`, `gitguardian`, `datadogsds`,
`cloudflaredlp`, `pywhat`, `validatorjs`, `sasinformationcatalog`
(`data/tools/`).

## Исходные данные и метод

- Списки типов взяты из первоисточников:
  - GitHub: таблица «Supported secret scanning patterns», около 500 шаблонов.
  - GitGuardian: страница «Supported credentials», 653 специфичных и 19
    общих детекторов.
  - Datadog: «Scanning Rule Library», 506 правил.
  - Cloudflare: «Predefined detection entries», около 150 записей.
  - pyWhat: `pywhat/Data/regex.json`, 154 регулярных выражения.
  - validator.js: README и `src/lib/isTaxID.js`, `isIdentityCard.js`,
    `isPassportNumber.js`, `isVAT.js`.
  - SAS: общая страница QKB об identification analysis (версия 32) и страницы
    Field Content локалей (версия 33).
- Каждый тип искали в `data/datatypes/` по id, имени и `aliases`.
- Для секретов посчитано, сколько из пяти детекторов (GitHub, GitGuardian,
  Datadog, pyWhat, Cloudflare) находят тип. Столбец «gitleaks» показывает,
  есть ли правило в `config/gitleaks.toml` (MIT): из него можно взять regex,
  как это уже делалось для `data/datatypes/any/secrets/`.

## Ограничения

- Сопоставление шло по названиям. Форматы (regex, префиксы) здесь не
  проверялись. Перед добавлением записи формат нужно сверить с документацией
  поставщика.
- GitHub и GitGuardian не публикуют regex, только названия.
- validator.js - библиотека, а не стандарт. Её regex годятся как подсказка,
  но не как доказательство формата.
- Страницы Field Content SAS нашлись только для 8 локалей (перебор адресов
  `qkbci-<locale>-id-fldcnt.html`): dadnk, dedeu, encan, engbr, enusa,
  nlbel, nonor, svswe. У остальных локалей адреса другие или страниц нет.

## Итоги

- 23 типа уже есть в реестре, но не попали в `supported_types` новых
  инструментов. Это самая дешёвая правка.
- Номера карт по платёжным системам различают четыре инструмента. В реестре
  есть только общий `bankcard`.
- 14 типов секретов находят 4-5 инструментов, ещё около 55 - три. У 66
  поставщиков, которых знают 3+ инструмента, в реестре нет ни одной записи.
- Национальные идентификаторы: около 15 кандидатов (шведский
  samordningsnummer, португальский NISS, уругвайская CI, иранский код melli,
  NIC Шри-Ланки и др.).
- validator.js даёт форматы паспортов 19 стран, номерных знаков 8 стран и
  мобильных телефонов 170 локалей, которых в реестре нет.

## 1. Типы, которые есть в реестре, но не учтены в новых инструментах

| Инструмент | Тип в источнике | Запись реестра |
|---|---|---|
| pywhat | Browser User Agent | `user_agent` |
| pywhat | YouTube Video ID | `youtubevideoid` |
| pywhat | YouTube Channel ID | `youtube_channel_id` |
| pywhat | United States Postal Service (UPS) Tracking Number | `upstracking` |
| validatorjs | `isVAT('BY')` | `by_unp` |
| validatorjs | `isLocale` | `languagetag` |
| sasinformationcatalog | DK SOCIAL SECURITY NUMBER | `dkcprnum` |
| sasinformationcatalog | DE NATIONAL ID | `depersonalausweis` |
| sasinformationcatalog | CA DRIVERS LICENSE, PASSPORT, SOCIAL SECURITY NUMBER | `cadriverlic`, `capassport`, `casin` |
| sasinformationcatalog | GB COUNTY, DRIVERS LICENSE, NATIONAL INSURANCE NUMBER, VEHICLE REGISTRATION | `gb_county`, `ukdriverlic`, `uknino`, `gb_vehicle_plate` |
| sasinformationcatalog | US SOCIAL SECURITY NUMBER | `usssn` |
| sasinformationcatalog | BE IDENTITY CARD NUMBER, NATIONAL ID, VEHICLE REGISTRATION | `be_eid`, `benatcardid`, `be_vehicle_plate` |
| sasinformationcatalog | NO BANK ACCOUNT NUMBER, ORGANIZATION ID, SOCIAL SECURITY NUMBER | `no_kontonr`, `no_orgnr`, `no_fodselsnummer` |
| sasinformationcatalog | SE NATIONAL ID | `sepersonnummer` |

Сделано 2026-11-09: все 23 id добавлены в `supported_types`. В `doc` записи
`sasinformationcatalog` указано, что страновые типы взяты со страниц Field
Content QKB 33 восьми локалей.

## 2. Новые типы: не секреты

### 2.1. Номера карт по платёжным системам

| Источник | Системы |
|---|---|
| Datadog | American Express, Diners, Discover, JCB, Maestro, MasterCard, Visa |
| Cloudflare | American Express, Diners Club, Mastercard, UnionPay, Visa |
| pyWhat | American Express, Diners Club, Discover, JCB, Maestro, MasterCard, Visa и ещё 7 |
| validator.js | `isCreditCard` с `provider`: amex, dinersclub, discover, jcb, mastercard, unionpay, visa |

В реестре есть `bankcard`, `payment_card_brand` (название системы) и `iin`.
Предложение: паттерны с `semantic_type: bankcard` по системам. Диапазоны IIN
и длины опубликованы самими платёжными системами и в ISO/IEC 7812.

Сделано 2026-11-09: восемь паттернов `bankcard_visa`, `bankcard_mastercard`,
`bankcard_amex`, `bankcard_diners`, `bankcard_discover`, `bankcard_jcb`,
`bankcard_maestro`, `bankcard_unionpay`. Диапазоны взяты из таблицы IIN в
статье Wikipedia «Payment card number», примеры - тестовые номера Stripe и
Braintree. У UnionPay нет `checksum`: не для всех номеров документирована
проверка Луна.

### 2.2. Национальные идентификаторы

| Кандидат | Источник | Примечание |
|---|---|---|
| Шведский samordningsnummer | Datadog; validator.js `isTaxID('sv-SE')` | personnummer, у которого к дню рождения прибавлено 60 |
| Португальский NISS | Datadog | номер социального страхования |
| Хорватский MBO | Datadog «Croatia Health Insurance Number» | |
| Уругвайская CI | Cloudflare «Uruguay ID (CI)» | есть контрольная цифра |
| Иранский код melli | validator.js `isIdentityCard('IR')` | 10 цифр с контрольной цифрой |
| NIC Шри-Ланки | validator.js `isIdentityCard('LK')` | старый (9 цифр и V/X) и новый (12 цифр) формат |
| Национальный номер Ливии | validator.js `isIdentityCard('ar-LY')` | |
| Тунисская CIN | validator.js `isIdentityCard('ar-TN')` | |
| Удостоверение личности Мозамбика | validator.js `isIdentityCard('MZ')` | |
| STIR (ИНН) Узбекистана | validator.js `isVAT('UZ')` | 9 цифр |
| COE Сан-Марино | validator.js `isVAT('SM')` | 5 цифр; модуль `sm.coe` есть и в python-stdnum |
| Украинский ИНН плательщика НДС | validator.js `isVAT('UA')` | 12 цифр; отличается от `ua_rntrc` |
| Персональный номер Греции | Datadog | неясно, какой номер имеется в виду; проверить |
| Мобильный телефон Китая | Datadog «China Phone Number» | см. 2.5 |

Сделано 2026-11-09: пять записей.

| Запись | Источник формата | Примеры |
|---|---|---|
| `se_samordningsnummer` | страница Skatteverket, `checksum: luhn` | пример Skatteverket |
| `lk_nic` | Wikipedia, оба формата | примеры из Wikipedia |
| `uy_ci` | Wikipedia (8 цифр, контрольная цифра) | пример Cloudflare |
| `ir_melli_code` | Wikipedia (10 цифр, XXX-XXXXXX-X) | нет |
| `sm_coe` | python-stdnum `sm.coe` | пример stdnum |

Алгоритмы контрольных цифр CI Уругвая и кода melli известны только по
сторонним валидаторам, поэтому `checksum` у этих записей не задан.

Не добавлены, потому что не нашёлся официальный источник формата:
- NISS Португалии: на gov.pt нет даже числа цифр, веса только в стороннем коде;
- MBO Хорватии: в документах HZZO нет структуры номера;
- Ливия, Тунис, Мозамбик, STIR Узбекистана, ИНН плательщика НДС Украины: формат
  есть только в validator.js;
- персональный номер Греции из Datadog: неясно, какой это номер.

### 2.3. Паспорта

validator.js `isPassportNumber` знает формат паспорта для 19 стран, у которых
в реестре нет паспортной записи: AR, AZ, BY, BR, DZ, IN, IR, IS, JM, KZ, LI,
LY, MX, MY, MZ, NZ, PK, SL, ZA. Паспортные записи реестра - паттерны с
`semantic_type: passport`.

Сделано 2026-11-09: форматы 18 стран искали в Wikipedia и на сайтах
выпускающих органов (PRADO отвечает 403). Формат нашёлся для четырёх, по ним
добавлены паттерны:
- `ar_passport`: три буквы и шесть цифр, по argentina.gob.ar;
- `ir_passport`: буква и восемь цифр, по Wikipedia;
- `jm_passport`: буква и семь цифр, по Wikipedia;
- `my_passport`: A, H или K и восемь цифр, по Wikipedia.

Для AZ, BY, BR, DZ, IN, IS, KZ, LI, LY, MX, MZ, NZ, PK и ZA формат есть
только в validator.js и в коммерческих справочниках, поэтому они не добавлены.
`SL` в validator.js означает Словению, а `si_passport` уже есть.

### 2.4. Номерные знаки

| Страна | Источник |
|---|---|
| SE | validator.js `isLicensePlate('sv-SE')`, SAS svswe |
| DK, NO | SAS dadnk, nonor |
| AR, HU, PT, SG, PK, AL, LI | validator.js `isLicensePlate` |
| TR | pyWhat «Turkish License Plate Number» |

Сделано 2026-11-09: десять паттернов по статьям Wikipedia «Vehicle
registration plates of ...»: `ar_vehicle_plate`, `hu_vehicle_plate`,
`pt_vehicle_plate`, `sg_vehicle_plate`, `al_vehicle_plate`,
`li_vehicle_plate`, `se_vehicle_plate`, `dk_vehicle_plate`,
`no_vehicle_plate`, `tr_vehicle_plate`. Регулярки учитывают исключённые
буквы, которые указаны в статьях (Швеция, Норвегия, Турция, Сингапур);
контрольная буква Сингапура не проверяется. Пакистан не добавлен: у каждой
провинции свой формат, и общего описания нет.

### 2.5. Телефоны по странам

validator.js `isMobilePhone` поддерживает 170 локалей. В реестре есть только
`phone`, `phone_e164`, `nanpphone` и `tel_uri`. Источник лучше брать из
libphonenumber (см. `devdocs/SOURCES_GAP_2026-11.md`, раздел 7), а
validator.js использовать для сверки.

Сделано 2026-11-09: 190 паттернов `<cc>_phone` (номер в форме E.164) по
метаданным Google libphonenumber. Регулярка - `+`, код страны и national
number pattern из libphonenumber; примеры - образцовые номера libphonenumber
(стационарный и мобильный). Не созданы паттерны для территорий NANP (+1), их
покрывает `nanpphone`, и для 41 территории, которой нет в
`data/countries.yaml`. Национальная запись с префиксом выхода на межгород и
номера с пробелами не покрываются. Добавлен инструмент `libphonenumber`.

### 2.6. Прочие форматы

| Кандидат | Источник |
|---|---|
| AWS ARN | pyWhat |
| URI и URL объекта S3 | pyWhat |
| ID инстанса EC2 (`i-...`) | pyWhat |
| ID организации AWS (`o-...`) | pyWhat |
| Уникальный ID IAM (`AIDA...`, `AROA...`) | pyWhat |
| URI TOTP (`otpauth://`) | pyWhat |
| Выражение cron | pyWhat |
| Адрес Nano (`nano_...`) | pyWhat |
| Tox ID | pyWhat |
| Unix-время в миллисекундах | pyWhat |
| Сериализованный объект Java (Base64) и PHP | pyWhat |
| HTTP cookie | Datadog |
| Хеши MD4, RIPEMD-128, Tiger | validator.js `isHash` |
| Строки Base64, Base58, Base32 | validator.js |

Форматы AWS описаны в документации AWS, URI TOTP - в спецификации Key Uri
Format (Google Authenticator), cron - в POSIX `crontab`.

Сделано 2026-11-09: 11 записей.

| Запись | Источник формата |
|---|---|
| `aws_arn` | документация IAM («ARN format») |
| `aws_s3_uri` | справочник AWS CLI `s3` и правила именования бакетов S3 |
| `aws_ec2_instance_id` | AWS: префикс и 8 или 17 символов; hex - по примерам AWS |
| `aws_organization_id` | регулярка из API AWS Organizations |
| `aws_iam_unique_id` | таблица префиксов IAM (AIDA, AROA, AGPA и др.) |
| `otpauth_uri` | Key Uri Format |
| `cron_expression` | POSIX `crontab` и суффикс шага `/n` |
| `nano_address` | регулярка из Nano integration guide |
| `tox_id` | спецификация Tox (38 байт в hex) |
| `java_serialized_base64` | Java Object Serialization Specification (магия 0xACED) |
| `http_cookie` | RFC 6265, грамматика заголовка Cookie |

Не добавлены:
- Unix-время в миллисекундах: 13 цифр, как EAN-13, без контекста не отличить;
- хеши MD4, RIPEMD-128 и Tiger: по виду совпадают с MD5 и другими hex-хешами;
- строки Base64, Base58, Base32: это кодировки, а не семантические типы;
- сериализованный объект PHP: формальной грамматики нет;
- URL Notion, Google Calendar, Regex101, Firebase, ARN топика SNS (он уже
  покрыт `aws_arn`).

### 2.7. Типы, которые определяются по словарю

- Названия лекарств и действующих веществ (Cloudflare «FDA Drug Names», «FDA
  Active Ingredients»). В реестре есть только российские
  (`rumedicinetradename`) и коды (`us_ndc`, `us_rxcui`).
- Текстовые названия диагнозов (Cloudflare «ICD-10 FY2023 Short
  Description», «ICD-11 Short Description»). В реестре есть только коды
  (`icd10`, `icd11`).

Поправка 2026-11-09: оба типа в реестре есть, но первый поиск их не нашёл:
`medication_generic_name`, `medication_brand_name` и `medical_condition`.
`medication_generic_name` (по «FDA Active Ingredients» и «FDA Drug Names», в
примере у Cloudflare стоит генерическое имя ABACAVIR) и `medical_condition`
добавлены в `cloudflaredlp`. Новых записей не нужно.

## 3. Новые типы: секреты

### 3.1. Найдены в 4-5 инструментах

| Кандидат | Инструменты | gitleaks |
|---|---|---|
| Закрытый ключ OpenSSH | GitHub, GitGuardian, Datadog, pyWhat, Cloudflare | общее правило `private-key` |
| Секрет клиента Azure Entra ID | GitHub, GitGuardian, Datadog, Cloudflare | `azure-ad-client-secret` |
| API-токен Cloudflare (`cfut_`, `cfat_` и старый формат) | GitHub, GitGuardian, Datadog, Cloudflare | `cloudflare-api-key` |
| Токен бота Discord | GitHub, GitGuardian, Datadog, pyWhat | `discord-api-token` |
| URL вебхука Discord | GitGuardian, Datadog, pyWhat, Cloudflare | нет |
| Токен доступа Facebook (`EAA...`) | GitHub, GitGuardian, Datadog, pyWhat | `facebook-access-token` |
| Токен доступа Google OAuth (`ya29.`) | GitHub, GitGuardian, Datadog, pyWhat | нет |
| Секрет клиента Google OAuth | GitHub, GitGuardian, Datadog, pyWhat | нет |
| API-ключ Mailgun | GitHub, GitGuardian, Datadog, pyWhat | `mailgun-private-api-token` |
| Токен интеграции Notion | GitHub, GitGuardian, Datadog, pyWhat | `notion-api-token` |
| API-ключ NuGet | GitHub, GitGuardian, Datadog, pyWhat | нет |
| SID аккаунта Twilio (`AC...`) | GitHub, GitGuardian, Datadog, pyWhat | нет |
| Ключ приложения Datadog | GitHub, GitGuardian, Datadog, pyWhat | `datadog-access-token` |
| Секрет клиента LinkedIn | GitHub, GitGuardian, Datadog, pyWhat | `linkedin-client-secret` |

Ключи Datadog и секрет LinkedIn не имеют префикса. Их можно опознать только
по контексту, поэтому польза от записей невелика.

Сделано 2026-11-09: 10 записей в `data/datatypes/any/secrets/`:

| Запись | Источник формата |
|---|---|
| `openssh_private_key` | `sshkey.c` и `PROTOCOL.key` в openssh-portable |
| `discord_bot_token` | пример в справочнике Discord API |
| `discord_webhook_url` | маршрут Execute Webhook в документации Discord, варианты хоста по pyWhat |
| `facebook_access_token` | правила gitleaks и pyWhat; Meta формат не публикует |
| `twilio_account_sid` | глоссарий Twilio «What is a SID» |
| `notion_integration_token` | changelog Notion (префиксы), длины по gitleaks и pyWhat |
| `mailgun_api_key` | только старый формат `key-`, по gitleaks |
| `azure_entra_client_secret` | определение Purview и правило gitleaks (`Q~`) |
| `cloudflare_api_token` | страница Cloudflare «Token formats» (`cfut_`, `cfat_`) |
| `cloudflare_global_api_key` | страница Cloudflare «Token formats» (`cfk_`) |

Маппинги Purview «Microsoft Entra client secret» и «Azure AD client secret»
перенесены с `api_key` на `azure_entra_client_secret`, тест
`test_purview_crosswalk` обновлён.

Не добавлены, потому что формат не документирован поставщиком и нет правила
gitleaks:
- API-ключ NuGet (`oy2` известен только по сканерам);
- секрет клиента Google OAuth (`GOCSPX-` известен только по сканерам);
- токен доступа Google OAuth (Google называет токены непрозрачными, префикс
  `ya29.` не документирован).

Старые форматы Cloudflare (40 символов без префикса, 37-45 hex) и новые ключи
Mailgun в регулярные выражения не вошли: они слишком общие или не описаны.

### 3.2. Найдены в трёх инструментах

С правилом gitleaks: Adafruit IO, Airtable, Clojars, Cohere, Contentful,
Dropbox, Fastly, Flutterwave, токены GitLab (runner, deploy, feed, pipeline
trigger), Grafana Cloud, HubSpot, Intercom, Mapbox, Prefect, Shippo,
Twitter bearer, Typeform, Yandex Cloud.

Без правила gitleaks: Apify, Asana, сессионный токен AWS, токен MWS Amazon,
ключи Azure (Cache for Redis, Cosmos DB, DevOps PAT, Functions, OpenAI),
Buildkite, CircleCI, глобальный API-ключ Cloudflare, API-ключ Datadog,
DeepSeek, Docker PAT, Elastic, Figma, ключ сервисного аккаунта GCP, Groq,
LangSmith, MongoDB Atlas, ключ лицензии и Insights query key New Relic,
OpenRouter, PagerDuty, PayPal/Braintree, Polar, PostHog, Replicate,
Salesforce, Snowflake, секрет вебхука Stripe (`whsec_`), Supabase, Vercel,
WakaTime.

Префиксы токенов GitLab перечислены в документации GitLab («Token prefixes»).
Форматы ключей Azure с встроенной сигнатурой описаны в
`microsoft/security-utilities` (MIT).

Сделано 2026-11-09:
- 11 записей GitLab: `gitlab_runner_token` (`glrt-`, `glrtr-`, в том числе
  routable-форма), `gitlab_deploy_token`, `gitlab_feed_token`,
  `gitlab_trigger_token`, `gitlab_cicd_job_token`,
  `gitlab_incoming_mail_token`, `gitlab_agent_token`,
  `gitlab_oauth_app_secret`, `gitlab_scim_token`,
  `gitlab_feature_flags_client_token`, `gitlab_session_cookie`. Префиксы взяты
  из документации GitLab, длины - из правил gitleaks.
- 5 записей Azure: `azure_devops_pat`, `azure_ai_services_key` (Azure OpenAI,
  AI services, Cognitive Services), `azure_cosmosdb_key`,
  `azure_function_key`, `azure_cache_redis_key`. Регулярные выражения взяты из
  `PreciselyClassifiedSecurityKeys.json` библиотеки security-utilities и
  покрывают только ключи с сигнатурой (AZDO, COG, ACDb, AzFu, AzCa). Старые
  ключи без сигнатуры (32 hex, 88 символов Base64) неотличимы от хешей и других
  ключей и в регулярки не вошли.
- Имена Purview этих пяти ключей перенесены с общих записей `access_token`,
  `api_key`, `symmetric_key` и `password` на новые записи.

Не сделано: токен рабочего пространства GitLab (`glwt-`, длина нигде не
описана) и токен регистрации runner (`GR1348941`, в таблице префиксов GitLab
его нет).

Сделано 2026-11-09, остальные секреты из 3.2: форматы 47 типов сверены с
документацией поставщиков и правилами gitleaks, добавлены 23 записи.

| Источник формата | Записи |
|---|---|
| Документация поставщика | `replicate_api_token` (`r8_`, 40 символов), `yandex_cloud_iam_token` (регулярка Yandex), `yandex_oauth_token` (`y[0-3]_`), `vercel_token` (`vcp_`, `vci_`, `vca_`, `vcr_`, `vck_`), `stripe_webhook_secret` (`whsec_`), `supabase_secret_key` (`sb_secret_`), `supabase_personal_access_token` (`sbp_`), `posthog_personal_api_key` (`phx_`), `new_relic_license_key` (суффикс `NRAL`) |
| Префикс у поставщика, длина по gitleaks | `shippo_api_token`, `grafana_cloud_token` (`glc_`), `mapbox_access_token` (`pk`, `sk`, `tk`), `flutterwave_secret_key` (`FLWSECK`), `clojars_deploy_token`, `dropbox_short_lived_token` (`sl.`, со слов сотрудников Dropbox) |
| Только образец в документации поставщика | `typeform_personal_access_token` (`tfp_`), `polar_organization_access_token` (`polar_oat_`), `openrouter_api_key` (`sk-or-v1-`) |
| Только gitleaks или pyWhat | `airtable_personal_access_token`, `prefect_api_key` (`pnu_`), `yandex_cloud_api_key` (`AQVN`), `twitter_bearer_token`, `new_relic_insights_key` (`NRII-`, `NRIQ-`) |

Временные ключи AWS (`ASIA`) уже покрыты записью `aws_access_key_id`.

Не добавлены, потому что формат не описан ни поставщиком, ни gitleaks (или
правило gitleaks работает только рядом с ключевым словом): Adafruit, Cohere,
Fastly, Intercom, HubSpot, старые ключи Airtable, Contentful, Apify, Asana,
Buildkite, CircleCI, DeepSeek, Docker, Elastic, Figma, Groq, LangSmith
(документирован только префикс трассировочных ключей `lsv2_tr_`), MongoDB
Atlas, PagerDuty, PayPal/Braintree, Salesforce, Snowflake, WakaTime, токен
MWS Amazon, сессионный токен AWS, ключ сервисного аккаунта GCP (JSON), ключи
Datadog. Для части из них сканеры знают префиксы (`dckr_pat_`, `gsk_`,
`lsv2_pt_`, `figd_`, `pat-na1-`, `amzn.mws.`), но поставщики их не
документируют.

### 3.3. Поставщики без записей в реестре

66 поставщиков, которых знают хотя бы три инструмента, не имеют в реестре ни
одной записи. Больше всего типов у Buildkite, Yandex Cloud, Polar, Vercel,
Docker, Supabase, Adobe, Apify, Salesforce, HubSpot.

## 4. Что добавлять не стоит

- Классификаторы содержимого промптов и языков программирования
  (Cloudflare): это не форматы значений.
- Упоминания брендов («Visa Text», «United States SSN Text»): это ключевые
  слова, а не значения.
- Флаги CTF, полезная нагрузка Log4Shell, файлы HAR, пары «ключ: значение»,
  `sshpass` и `mount` с паролем (pyWhat, Cloudflare).
- Служебные идентичности SAS: EMPTY, UNKNOWN.
- validator.js `isAlpha`, `isNumeric`, `isStrongPassword` и подобные: это
  проверки символов, а не типы.

## 5. Приоритеты

1. ~~Добавить 23 пропущенных id в записи инструментов (раздел 1).~~
   Сделано.
2. ~~Паттерны номеров карт по платёжным системам (2.1).~~ Сделано.
3. ~~Секреты из 3.1 с документированным префиксом: OpenSSH, Discord (бот и
   вебхук), Facebook, Twilio SID, Notion, NuGet, Mailgun, Google OAuth,
   Azure Entra, Cloudflare.~~ Сделано, кроме NuGet и Google OAuth (см. 3.1).
4. ~~Токены GitLab и ключи Azure по официальным спискам префиксов (3.2).~~
   Сделано.
5. ~~Национальные идентификаторы (2.2) после сверки с документами
   выпускающих органов.~~ Сделано для пяти из четырнадцати (см. 2.2).
6. Паспорта, номерные знаки и телефоны (2.3-2.5).

## Источники

- https://docs.github.com/en/code-security/reference/secret-security/supported-secret-scanning-patterns
- https://docs.gitguardian.com/secrets-detection/secrets-detection-engine/detectors/supported_credentials
- https://docs.datadoghq.com/security/sensitive_data_scanner/scanning_rules/library_rules/
- https://developers.cloudflare.com/cloudflare-one/data-loss-prevention/detection-entries/predefined-detection-entries/
- https://github.com/bee-san/pyWhat/blob/main/pywhat/Data/regex.json
- https://github.com/validatorjs/validator.js/tree/master/src/lib
- https://support.sas.com/documentation/onlinedoc/qkb/32/QKBCI32/Help/Content/qkb-generaldoc/qkb-iddef.html
- https://support.sas.com/documentation/onlinedoc/qkb/33/QKBCI33/Help/Content/qkbci-enusa/qkbci-enusa-id-fldcnt.html
  (и такие же страницы для dadnk, dedeu, encan, engbr, nlbel, nonor, svswe)
- https://github.com/gitleaks/gitleaks/blob/master/config/gitleaks.toml

## 6. Что сделано по остальному плану (2026-11-09)

### Новые записи инструментов

По первому разбору инструментов, которых нет в реестре, добавлены 14 записей:

| Инструмент | Файл | Типов |
|---|---|---|
| Bearer CLI | `data/tools/detectors/bearer.yaml` | 23 |
| Privado | `data/tools/detectors/privado.yaml` | 19 |
| Duckling | `data/tools/other/duckling.yaml` | 7 |
| libpostal | `data/tools/other/libpostal.yaml` | 6 |
| Microsoft Recognizers-Text | `data/tools/other/recognizerstext.yaml` | 11 |
| libphonenumber | `data/tools/other/libphonenumber.yaml` | 193 |
| Private AI | `data/tools/pii/privateai.yaml` | 37 |
| Frictionless Table Schema | `data/tools/other/frictionless.yaml` | 11 |
| Pydantic и pydantic-extra-types | `data/tools/other/pydantic.yaml` | 35 |
| grok-шаблоны Logstash | `data/tools/etl/grok.yaml` | 13 |
| visions | `data/tools/detectors/visions.yaml` | 9 |
| Fides (Fideslang) | `data/tools/pii/fides.yaml` | 23 |
| SAP CDS (CSN Interop) | `data/tools/other/sapcds.yaml` | 6 |
| SDV | `data/tools/other/sdv.yaml` | 24 |

Fideslang, SAP CDS и SDV добавлены как инструменты, а не как новые ключи
`mappings`: так не нужно менять модель данных.

Не добавлены:
- SQL Server / Azure SQL Data Discovery & Classification: Microsoft не
  публикует список встроенных information types.
- TURL (метки Freebase, их нет в реестре), Pythagoras (официальный
  репозиторий не найден), ArcheType (метки задаёт пользователь, а наборы
  меток бенчмарков привязаны к датасетам).
- В SAP CSN Interop нет аннотаций email, телефона, адреса и имени, поэтому
  связей у записи мало. Эти аннотации есть в документации SAP CAP.

### Сверка связей, выставленных по названиям детекторов

| Связь | Итог |
|---|---|
| `githubsecretscanning` -> `github_fine_grained_pat` | удалена: в документации GitHub не нашлось подтверждения |
| `datadogsds` -> `it_codicefiscale`, `cz_dic`, `discord_webhook_url` | удалены: у правил нет описания |
| `gitleaks` -> `cloudflare_api_token`, `cloudflare_global_api_key` | удалены: правила gitleaks ловят только старый формат, а регулярки записей - новый |
| `gitguardian` -> `cloudflare_origin_ca_key`, `uri_with_password`, `symmetric_key` | оставлены, подтверждены страницами детекторов |
| `datadogsds` -> `sonarqube_token`, `cloudflaredlp` -> `at_tin`, `p2pkhaddr` | оставлены |
| `cloudflaredlp` -> `address` | оставлена: Cloudflare ищет адреса трёх стран, связь частичная |

### Даты CLDR

24 паттерна `date_<язык>` с названиями месяцев из Unicode CLDR (форматы long и
medium): шведский, датский, норвежский, финский, венгерский, греческий,
хорватский, сербский (кириллица), словенский, литовский, латышский,
эстонский, каталанский, индонезийский, малайский, вьетнамский, арабский,
персидский, иврит, хинди, исландский, албанский, белорусский, боснийский.

### Что осталось

Всё оставшееся заблокировано отсутствием источника формата:
- паспорта 14 стран (раздел 2.3) и номерные знаки Пакистана;
- около 27 секретов (разделы 3.1 и 3.2);
- 8 национальных идентификаторов (раздел 2.2);
- `supported_types` для BigID, Informatica и Ataccama;
- SQL Server Data Classification.
