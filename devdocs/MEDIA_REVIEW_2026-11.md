# Ревизия категории «Media and entertainment» (ноябрь 2026)

Цель: проверить записи категории `media`, исправить устаревшие и неточные
поля, добавить отсутствующие типы, которые встречаются в наборах данных о
кино, музыке, телевидении и играх.

## Источники проверки

- Свойства Wikidata: метка, регулярное выражение формата (P1793), примеры
  (P1855). Регулярные выражения записей проверены на выборках до 5000
  значений каждого свойства через Wikidata Query Service.
- python-stdnum: контрольные символы примеров ISAN, ISRC, EAN, ISBN, EIDR
  (ISO 7064 mod 37,36).
- Документация сервисов: Spotify Web API (URI и ID), Vimeo oEmbed (проверка
  ID видео), MusicBrainz (MBID), README MovieLens (`imdbId`, `tmdbId`).
- Wikipedia: системы рейтингов MPA, TV Parental Guidelines, ESRB, PEGI,
  BBFC, FSK, USK, SMPTE timecode; ru.wikipedia — номера свидетельств о
  регистрации СМИ в статьях о СМИ.
- Правила `common/media.yaml` и `common/objects.yaml` из metacrafter-rules
  на закреплённом коммите `19823306`.

## Было

16 записей с категорией `media`. Проблемы:

| Запись | Проблема |
|---|---|
| `ean` | Описание-заглушка, нет примеров, regexp только для EAN-13 (правило metacrafter принимает и EAN-8), нет `checksum`. EAN — код GS1, а не медиа-идентификатор. |
| `isbn` | Описание-заглушка, нет примеров и ссылок, regexp не принимает ISBN-10, хотя правило metacrafter их принимает. ISBN относится к `publishing`. |
| `vimeovideoid` | Нет описания, regexp, примеров и ссылок (оценка 20). |
| `youtubevideoid` | `langs: en` у языконезависимого ID, нет отрицательного примера. |
| `imdb_id` | Нет примеров `tt` и `nm`, не поддержаны издания событий (`ev0000003/2015`). |
| `eidr` | Описание скопировано из Wikipedia, русский перевод на английском, regexp допускал не шестнадцатеричные символы в группах. |
| `isrc` | Описание скопировано из Wikipedia, regexp без якорей, не принимал печатную форму с дефисами, нет категории `media`. |
| `ru_age_rating*` | Нет ссылок на источник. |

## Изменения существующих записей

- `ean`: категории `gs1`, `objectids` (вместо `media`), файл перенесён в
  `any/gs1/`. Новое описание, regexp `^(?:\d{8}|\d{13})$`, `checksum: gtin`,
  примеры с демонстрационным префиксом GS1 952, перевод.
- `isbn`: категории `publishing`, `objectids` (вместо `media`), файл
  перенесён в `any/publishing/`. Описание, regexp для ISBN-10 и ISBN-13 с
  дефисами, примеры, ссылки, перевод. `isbn10` и `isbn13` получили
  `parent: isbn` и категорию `publishing`.
- `vimeovideoid`: описание, regexp `^[1-9]\d{0,9}$`, примеры (проверены
  через Vimeo oEmbed), ссылки на API, `langs: common`, перевод.
- `youtubevideoid`: описание уточнено, `langs: common`, пример с дефисом в
  начале, отрицательный пример (ID канала), ссылка на YouTube Data API,
  перевод.
- `imdb_id`: regexp с изданиями событий, примеры `tt`, `nm`, `ev`,
  отрицательный пример — форма без `tt` из MovieLens, перевод.
- `isan`: примеры из Wikidata (Toy Story, The Godfather), замечание о
  12-значных корнях в Wikidata, перевод.
- `eidr`: описание своими словами, regexp `[0-9A-F]{4}` в группах
  (3000/3000 значений Wikidata), пример Toy Story, отрицательный пример
  (EIDR party ID), ссылка на eidr.org, исправлен перевод.
- `isrc`: описание своими словами, regexp с якорями и необязательными
  дефисами и префиксом `ISRC`, примеры из Wikidata, отрицательный пример,
  категория `media`, перевод. Пример `GBUM71500123` без источника заменён.
- `iswc`, `genre`: добавлена категория `media`; в `genre` исправлена опечатка.
- `ru_age_rating`: ссылки на статьи ru.wikipedia о возрастной классификации
  и о законе 436-ФЗ, `parent: content_rating`, перевод описания.
  `ru_age_rating_label`, `ru_age_rating_number`: ссылки.

## Новые записи (38, все `draft`)

| Группа | Записи | Wikidata |
|---|---|---|
| Возрастные рейтинги | `content_rating` (общий родитель), `us_mpa_rating`, `us_tv_parental_guidelines`, `esrb_rating`, `pegi_rating`, `gb_bbfc_rating`, `de_fsk_rating`, `de_usk_rating` | P1657, P852, P908, P2629, P1981, P914 |
| MusicBrainz | `musicbrainz_id` (родитель, `parent: uuid`), `musicbrainz_artist_id`, `musicbrainz_release_group_id`, `musicbrainz_release_id`, `musicbrainz_recording_id`, `musicbrainz_work_id`, `musicbrainz_label_id` | P434, P436, P5813, P4404, P435, P966 |
| Spotify | `spotify_id` (родитель), `spotify_uri`, `spotify_artist_id`, `spotify_album_id`, `spotify_track_id` | P1902, P2205, P2207 |
| Discogs | `discogs_artist_id`, `discogs_master_id`, `discogs_release_id`, `discogs_label_id` | P1953, P1954, P2206, P1955 |
| AllMusic | `allmusic_artist_id` (`mn`), `allmusic_album_id` (`mw`), `allmusic_song_id` (`mt`), `allmusic_composition_id` (`mc`) | P1728, P1729, P1730, P1994 |
| Права на музыку | `ipi_name_number`, `ipi_base_number` | P1828, P3453 |
| EIDR | `eidr_party_id` (префикс 10.5237) | P12142 |
| Кино и ТВ | `tmdb_movie_id`, `tmdb_tv_series_id`, `tvdb_series_id`, `kinopoisk_film_id` | P4947, P4983, P4835, P2603 |
| Игры | `steam_app_id` | P1733 |
| Технические | `smpte_timecode` | — |
| Россия | `ru_mass_media_registration_number` (номер свидетельства о регистрации СМИ) | — |

Совпадение regexp с выборками Wikidata: 99–100% для всех свойств, кроме
`allmusic_song_id` (99,7%), `ipi_name_number` (99,3%) и `ipi_base_number`
(95,7%). Несовпадения — ошибки в Wikidata: ID альбомов в свойстве песен,
номера IPI без ведущих нулей, номера имён в свойстве базовых номеров.

Итог по категории `media` (оценка `metacrafter-registry report`):

| | Записей | Средняя оценка | Минимальная |
|---|---:|---:|---:|
| До | 16 | 74,7 | 20 (`vimeovideoid`) |
| После | 55 | 86,7 | 50 (`genre`: свободный текст, regexp не нужен) |

## Что не сделано и почему

- `ru_mass_media_registration_number`: сайт Роскомнадзора недоступен
  из-за геоблокировки, формат проверен по номерам в статьях ru.wikipedia
  (Lenta.ru, Первый канал, Regnum, региональные СМИ). Формы свидетельств
  1990-х и начала 2000-х годов regexp не принимает: их нужно проверить по
  открытым данным реестра СМИ.
- Не добавлены: Apple Music, Deezer, Letterboxd, Rotten Tomatoes,
  Metacritic, MyAnimeList, IGDB, TVmaze, Apple Podcasts, DDEX Party ID,
  Ad-ID. Это кандидаты следующего раунда; для DDEX и Ad-ID не найден
  проверяемый источник формата.
- Записи остаются `draft`. Кандидаты в `stable` после проверки человеком:
  `imdb_id`, `isan`, `iswc`, `youtubevideoid`, `grid_release`, `ismn`,
  `gb_bbc_programme_id`.

## Находки для metacrafter-rules

- `common/media.yaml`, правило `isrcvalue`: `Word(alphas, exact=2) +
  Word(alphanums, exact=3) + Word(nums, exact=7) + Word(alphanums, exact=2)`
  требует 14 символов при `maxlen: 12` и не находит ни одного настоящего
  ISRC (проверено pyparsing 3.3.3 на `USRC17607839`). Правило
  `objects_isrcvalue` в `common/objects.yaml` работает; `isrcvalue` стоит
  удалить или исправить.
- `common/media.yaml`, `vimeovideoidvalue`: `Word(nums, min=7, max=10)`
  помечено `imprecise`, но совпадает с любым 7–10-значным числом.
- Для новых записей правил нет. По значению хорошо распознаются
  `spotify_uri`, `allmusic_*`, `eidr_party_id`, `ipi_base_number`,
  `smpte_timecode`, `us_tv_parental_guidelines`,
  `ru_mass_media_registration_number`; числовые ID (TMDB, Discogs, Steam,
  Кинопоиск) — только по имени поля.
