# Портфолио системного аналитика

Стартовая страница и «склейка» учебных проектов на одном сайте: https://pakmaninlaw.pythonanywhere.com

| Адрес | Проект | Репозиторий |
|---|---|---|
| `/` | Витрина проектов | этот |
| `/winchester/` | ВИНЧЕСТЕРЪ — конструктор крафтовой колбасы | [Winchester](https://github.com/pakmaninlaw/Winchester) |
| `/crm/` | CRM системного аналитика (демо) | [crm-system-analyst](https://github.com/pakmaninlaw/crm-system-analyst) |
| — | ICQ-мессенджер | в разработке |

## Устройство

- `portal.py` — витрина, переадресация старых ссылок магазина, защита от ботов (лимит POST-запросов с одного IP).
- `pythonanywhere_wsgi.py` — WSGI-файл для PythonAnywhere: подключает проекты по префиксам через `DispatcherMiddleware`.
- `local_run.py` — запуск всего сайта локально (`python local_run.py` → http://127.0.0.1:8000), проекты лежат в соседних папках `../Winchester` и `../CRM`.
- `tests/test_portal.py` — проверка сайта целиком.

## Обновление на PythonAnywhere

```bash
cd ~/portfolio && git pull
cd ~/crm && git pull
cd ~/Winchester && git pull && cp main.py ~/mysite/main.py
```

Затем на вкладке **Web** нажать **Reload**.
