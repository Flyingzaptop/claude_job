# Настройка (выполняет Claude в первой сессии)

Пользователь открыл сессию Claude Code с этим репозиторием и написал «Настрой поиск работы по SETUP.md». Делай по шагам, коротко отчитывайся.

1. **Интервью.** Задавай вопросы пачками по 3–5, на языке пользователя. Нужно: кто он, направления A и B, опыт и проекты
   (с доказательствами: CV, GitHub, портфолио — попроси файлы), языки, город, радиус и частота поездок, график и жёсткие условия,
   уровень, минимальные деньги, дата выхода, email для откликов. Ничего не додумывай: неизвестное — вопрос.
2. **PROFILE.md** — заполни только подтверждёнными фактами. Покажи кратко, попроси поправить.
3. **config.json** — name, email, phone, deadline, tracks (названия A/B), cv_prefix (`Imie_Nazwisko_CV`), cv_langs,
   messages (мотивационные шаблоны ≤ 1000 символов на A/B и языки, с {title} и {company}, условия графика),
   excluded_language_regex (обязательные языки, которых нет), linkedin_searches, jooble_queries, fantastic.
4. **tools/search/keywords.json** — ключевые слова A и B на языках рынка, locations.
   **tools/search/sources.json** — оставь подходящие источники, добавь местные для его страны/отрасли (≥ 100 всего).
5. **CV.** Для каждого направления и языка — `cv/content/base_<a|b>_<язык>.json` (блоки: name, role, contact, section, title,
   body, bullet, caption, image, page), сборка `python3 tools/cv/build_cv.py cv/content/base_*.json`, проверь PNG-превью глазами,
   скопируй PDF в `tracker/cv/` с именами `<cv_prefix>_<a|b>_<язык>.pdf`.
6. **Трекер.** Опубликуй `tracker/index.html` как Artifact (icon `briefcase`) с files: `config.json` (из корня),
   `jobs.json`, `applications.json`, PDF из `tracker/cv/`, и capabilities
   `{"db": {}, "user": {}, "downloads": true, "mcp": {"servers": [{"server": "Claude Code Remote", "tools": ["fire_trigger"]}]}}`.
   Запиши URL в `config.json` → `tracker_url`.
7. **Запланированные задачи** (create_trigger, привязаны к этой сессии):
   - `job-search: run` — без расписания, prompt: «Кнопка «Искать» нажата в трекере. Выполни поиск строго по SEARCH.md, опубликуй трекер, закоммить и запушь, коротко отчитайся». ID → `config.json` → `search_trigger_id`, переопубликуй трекер.
   - `job-search: mail check` — раз в день (спроси время и часовой пояс), только если подключён Gmail: отметки «Подался» из db (коллекция `status`) → `tracker/applications.json` и `data/exclusions.json`, письма за 2 дня → статусы, переопубликовать, коммит. Ничего не отвечать работодателям.
8. **Ключи API (по желанию)** — пользователь добавляет в переменные окружения: `JOOBLE_API_KEY`, `FANTASTIC_JOBS_API_KEY`, `APIFY_TOKEN`
   (не в чат). Без них работают только поиск по сайтам и бесплатные API.
9. Коммит, пуш. Сообщи пользователю ссылку на трекер и как пользоваться кнопками.
