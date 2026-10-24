# Поиск вакансий: инструкция запуска («Искать»)

Запуск: кнопка «Искать» в трекере → scheduled task `job-search: run` → эта сессия получает задание и выполняет шаги ниже.
Ничего не отправлять работодателям. Только найти, оценить, показать.

## Роли (пайплайн)
| Этап | Кто | Модель / reasoning |
|---|---|---|
| Сбор, чтение объявлений, предварительный разбор (triage) | сабагенты | `haiku` (Haiku 5.5), effort `low` |
| Финальная оценка fit + schedule, CV и сообщения под топ-вакансии | сабагенты | `sonnet` (Sonnet 5.5), effort `medium` |
| Надзор: раздаёт пачки, проверяет журналы покрытия и выборку оценок, перезапускает упавшие пачки, публикует | эта сессия | Opus 5.5 |

## 0. Перед стартом
- `PROFILE.md` — профиль и **жёсткие условия графика**.
- `tools/search/sources.json` — ≥100 источников. `tools/search/keywords.json` — ключевые слова.
- Исключения: `tracker/applications.json` + `PROFILE.md` («Уже подготовлено / подано») + уже оценённые id в `data/scored_*.jsonl`.

- Отметки кнопкой «Подался»: `ArtifactData query` трекера (`tracker_url` из config.json), коллекция `status`,
  `status == "applied"` → добавить в `tracker/applications.json` (status `confirmed`, note «Отмечено кнопкой «Подался»», url)
  и в `data/exclusions.json` (`company`, `role`, why `applied (button)`).

## 1. Сбор и triage (сабагенты: model `haiku`, effort `low`, до 8 параллельно)
- API-источники запускаю сам: `python3 tools/fetch_apis.py jooble fantastic arbeitnow apify_linkedin` (запросы — в config.json) (+ remoteok/himalayas/jobicy, если добавлены).
  Бюджеты: Apify ≤ $1 за запуск; Fantastic ≤ 100 вакансий за запуск.
- Остальные источники (`method: site|fetch`) делю на пачки по ~14 и отдаю Sonnet-сабагентам. Каждый:
  - для каждого источника делает 2–4 запроса WebSearch вида `site:<domain> (<keywords a>) (<locations> OR remote)` и `site:<domain> (<keywords b>) ...` из `tools/search/keywords.json`;
  - открывает (WebFetch) только объявления, похожие на junior/intern/staż и подходящие по локации;
  - пишет найденное в `data/raw/web_<YYYY-MM-DD>_<batch>.jsonl` в формате fetch_apis (`source`, `id`=`web:<url>`, `title`, `company`, `location`, `type`, `salary`, `posted`, `url`, `text` ≤ 4000 символов);
  - пишет журнал покрытия `data/logs/coverage_<YYYY-MM-DD>_<batch>.json`: по каждому источнику — запросы, число результатов, ошибки/блокировки.
  - не обходит капчи и защиту от ботов: заблокировано → отмечает `blocked` и идёт дальше;
  - **triage** каждой найденной вакансии: поле `triage` = `keep` | `drop` + `triage_reason` (одна фраза).
    `drop` только для явного мимо: senior/lead, 3+ лет обязательно, нетехническая роль, обязательный немецкий и т.п. Сомнение → `keep`.

## 2. Фильтр
`python3 tools/prefilter.py` → `data/candidates.jsonl` (дедуп, senior/немецкий, исключение уже поданных).
Новые = кандидаты без оценки и без `triage: drop` → `data/part_<дата>.jsonl`.

## 3. Финальная оценка (сабагенты: model `sonnet`, effort `medium`, по ~200 строк)
Каждая вакансия оценивается вручную по `tools/search/SCORING.md`. Результат → `data/scored_<дата>_<n>.jsonl`.

## 3a. Надзор (Opus)
- Журналы покрытия: сколько источников реально ответили; пачки с ошибками перезапустить один раз.
- Проверка triage: 15 случайных `drop` — если среди них есть подходящие, вернуть пачку на повторный разбор.
- Проверка оценок: все вакансии с fit ≥ 7 и 15 случайных из остальных. Явные ошибки исправить, при системной ошибке пачку переоценить.
- В отчёте пользователю: проверено источников / ответили / заблокировали; найдено → после triage → оценено; что исправлено надзором.

## 3b. CV под лучшие вакансии (Sonnet medium)
Для вакансий с fit ≥ 7 и schedule ≥ 7 (не больше 10 за запуск): сделать `cv/content/job_<safe id>.json` на основе
`cv/content/base_<a|b>_<язык>.json` (язык — по языку объявления), подогнать role/profil/порядок навыков под требования
без выдуманного опыта (правило: только то, что есть в PROFILE.md), собрать `python3 tools/cv/build_cv.py ...` и положить PDF в
`tracker/cv/tailored/<safe id>.pdf` (safe id = id, где всё кроме `A-Za-z0-9_-.~@+` и `:` заменено на `_`). В карточке появится «CV под вакансию».
Для тех же вакансий написать мотивационное сообщение (PL и/или EN, ≤ 1000 символов, без обещаний вложений, с условием графика)
в `data/messages.json` как `{"<id>": {"PL": "...", "EN": "..."}}`. Иначе кнопка «Сообщение» копирует шаблон по направлению.

## 4. Публикация
`python3 tools/build_tracker.py` → публикую трекер (`tracker/index.html` + `config.json` + `jobs.json` + `applications.json` + все PDF из `tracker/cv/`),
коммичу и пушу в `main`, коротко пишу пользователю: сколько источников реально проверено (по журналам), сколько новых, топ-10.
