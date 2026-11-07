# Ревизия категории «Texts and articles» (ноябрь 2026)

Цель: проверить записи категории `texts`, переписать заглушки, добавить
отсутствующие типы, которые встречаются в выгрузках CMS и новостных
сайтов, корпусах текстов, социальных сетях и метаданных статей.

## Источники проверки

- Свойства Wikidata: формат (P1793), formatter URL (P1630) и выборки до
  3000 значений через Wikidata Query Service. Научные статьи после
  разделения графа Wikidata живут на отдельном эндпоинте, поэтому выборки
  для P4011, P893, P6179 и P5875 небольшие (200–800 значений).
- Schema.org: articleBody, articleSection, wordCount, headline,
  alternativeHeadline, abstract, author, reviewBody, numberOfPages, comment.
- IPTC: словарь Media Topics в JSON с cv.iptc.org (выпуск 2026-09-30,
  1394 понятия, из них 335 выведены из употребления), руководство по
  NewsCodes (QCode `medtop:`), алиас Subject Codes `subj`.
- Universal Dependencies: список 17 тегов UPOS и страница изменений v2
  (`CONJ` → `CCONJ`).
- Спецификация CTS URN (cite-architecture.github.io).
- Unicode Standard 16.0, приложение A (запись `U+` и 4–6 цифр).
- Реестр IANA Character Sets (имена до 40 символов, без учёта регистра).
- twitter-text (conformance/extract.yml) и Mastodon (`app/models/tag.rb`):
  хештег только из цифр не распознаётся.
- WordPress (`wp-admin/includes/upgrade.php`): слаги по умолчанию
  `hello-world` и `sample-page`.
- Правила metacrafter-rules на закреплённом коммите `19823306`
  (`rules/common/texts.yaml`, `en_common.yaml`, `ru_common.yaml`).

## Было

8 файлов в `data/datatypes/any/texts/`, 7 записей с категорией `texts`
(1 `stable`), средняя оценка 33,6. Проблемы:

| Запись | Проблема |
|---|---|
| `article_id`, `comment_id`, `content_id`, `document_id` | Имя «… by field name» описывает способ распознавания, а не тип; описание повторяет имя («Article ID by field name identifier»); нет перевода и ссылок. |
| `headline` | Описание — пять слов из Schema.org; нет примеров и ссылки на Wikipedia. |
| `comment` | Короткое описание; нет сопоставления со свойством Schema.org `comment`. |
| `description` | Лежит в `texts/`, правило `descriptionfield` — в контексте `texts`, но категории `texts` не было. |
| `keyword` | Нет русского описания. |
| `pmid`, `pmcid`, `arxiv_id`, `publisher_item_identifier` | Идентификаторы статей не входили в категорию. |

## Изменения существующих записей

- `article_id`, `comment_id`, `content_id`, `document_id`: имена без
  «by field name» (по прецеденту `youtubevideoid`, `snowflake_id`),
  описания своими словами с именами полей из правил metacrafter, ссылки
  на записи с известным форматом (`doi`, `pmid`, `gdti`), переводы.
  `content_id` отличён от YouTube Content ID.
- `headline`: описание, `parent: title`, примеры исторических заголовков
  (Chicago Daily Tribune 1948, The New York Times 1969), ссылка на
  Wikipedia, перевод.
- `comment`: описание, `schema_org: comment`, перевод.
- `description`: категория `texts`, описание, отсылки к `abstract` и
  `dc_description`.
- `keyword`: русское описание.
- Категория `texts` добавлена к `pmid`, `pmcid`, `arxiv_id`,
  `publisher_item_identifier`.

## Новые записи (26, все `draft`)

| Группа | Записи | Источник | Совпадение с выборкой |
|---|---|---|---|
| Поля текста | `title` (`parent: name`), `subtitle`, `abstract` (`parent: description`), `article_body`, `article_section`, `author_name`, `review_text` | P1476, P1680, P2093; Schema.org | — |
| Счётчики | `word_count`, `number_of_pages` (`parent: quantity`, без regexp) | P6570, P1104; Schema.org | — |
| Форматы | `hashtag`, `url_slug`, `unicode_code_point`, `character_encoding`, `upos_tag`, `cts_urn` (`parent: urn`), `iptc_media_topic` | P2572, P4213; UD, IANA, IPTC, CTS | хештеги 2910/3000, кодовые точки 3000/3000, Media Topics 1394/1394 |
| Тексты и авторы | `gutenberg_ebook_id`, `gutenberg_author_id` | P2034, P1938 | 3000/3000, 3000/3000 |
| Посты | `x_post_id` | P5933 | 505/507 |
| Научные статьи | `semantic_scholar_paper_id`, `ssrn_article_id`, `dimensions_publication_id`, `researchgate_publication_id`, `jstor_article_id` | P4011, P893, P6179, P5875, P888 | 399/399, 202/202, 532/600, 724/801, 3000/3000 |
| Энциклопедии | `britannica_id`, `ru_bigenc_id` (БРЭ, `RU/texts/`) | P1417, P11514 | 3000/3000, 2999/3000 |

Несовпадения — ошибки в Wikidata: размеры книг в P6179 («6 x 0.59 x 9
inches»), ISSN и пути URL с названием в P5875, пустые значения в P5933,
числовой ID старого сайта в P11514.

Решения по regexp:

- `hashtag` требует знак `#` и хотя бы одну букву: без `#` хештег — просто
  слово, а тег из одних цифр X и Mastodon не распознают. Wikidata хранит
  хештеги без `#`.
- `unicode_code_point` требует `U+`: четыре шестнадцатеричные цифры без
  префикса неотличимы от числа.
- `iptc_media_topic` принимает QCode (`medtop:`, `mediatopic:`) и URI, но
  не голые восемь цифр: они совпадают с датами и Subject Codes.
- `url_slug` требует хотя бы один дефис: однословный слаг (`about`)
  неотличим от слова.
- `x_post_id`, `ssrn_article_id`, `gutenberg_*`, `researchgate_publication_id`:
  числовые форматы Wikidata; распознавать по имени поля.
- `semantic_scholar_paper_id`: 40 шестнадцатеричных символов, как у любого
  SHA-1.

Итог по категории `texts` (оценка `metacrafter-registry report`):

| | Записей | `stable` | Средняя оценка | Минимальная |
|---|---:|---:|---:|---:|
| До | 7 | 1 | 33,6 | 20 (`document_id` и др.) |
| После | 38 | 2 | 73,6 | 50 (поля без формата: `article_id`, `article_body`, `word_count` и др.) |

## Что не сделано и почему

- Не добавлены: метка тональности (sentiment), теги Penn Treebank и NER
  (нет единого стандарта значений), ISTC (агентство не подтверждено, нет
  свойства Wikidata), ID статей Википедии, постов Reddit, Telegram и VK
  (нет проверяемого формата), КиберЛенинка (нет свойства Wikidata),
  Stanford Encyclopedia of Philosophy (P3123), старые ID БРЭ (P2924),
  IPTC Subject Codes и Genre, диапазон страниц (P304: сложный формат с
  римскими цифрами), ссылки на Библию (OSIS), время чтения. Кандидаты
  следующего раунда.
- Свободные тексты (`article_body`, `abstract`, `comment`, `description`,
  `review_text`) оставлены без примеров: пример произвольного текста ничего
  не проверяет.
- Записи остаются `draft`. Кандидаты в `stable` после проверки человеком:
  `headline`, `title`, `upos_tag`, `iptc_media_topic`, `unicode_code_point`,
  `gutenberg_ebook_id`, `gutenberg_author_id`.

## Находки для metacrafter-rules

Проверено на закреплённом коммите `19823306`:

- `common/texts.yaml`, `headlinefield`: в списке полей `title` и
  `article_title`, а `en/en_common.yaml`, `enitemnameknown`, относит
  `title` к `name`. Одно поле получает два типа. Теперь есть запись
  `title`; поля `title`, `article_title` лучше отнести к ней, а
  `headline` оставить для `headline*`.
- `common/texts.yaml`, `descriptionfield`: `summary` и `abstract`
  относятся к `description`; для них теперь есть запись `abstract`.
- `common/texts.yaml`, `documentidfield`: `reference_number`, `ref_number`,
  `ref_no` — общие имена (номер платежа, заказа, заявки), которые дадут
  ложные срабатывания.
- Правил нет для новых записей. По значению хорошо распознаются `hashtag`,
  `unicode_code_point`, `iptc_media_topic`, `cts_urn`, `upos_tag`,
  `ru_bigenc_id`, `britannica_id`; остальные — по имени поля (`slug`,
  `charset`, `upos`, `tweet_id`, `gutenberg_id`, `word_count`, `pages`,
  `subtitle`, `abstract`, `author`, `body`).
