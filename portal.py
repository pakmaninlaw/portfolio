"""
Портфолио системного аналитика — стартовая страница и «склейка» проектов на одном сайте.

  /             — витрина проектов
  /winchester/  — ВИНЧЕСТЕРЪ, конструктор колбасы (ДЗ «Мир колбасы Люкс»)
  /crm/         — CRM системного аналитика (итоговая работа)

Плюс защита от ботов: ограничение частоты POST-запросов с одного IP.
"""
import json
import threading
import time
from collections import deque

from flask import Flask, redirect, render_template_string, request
from werkzeug.middleware.dispatcher import DispatcherMiddleware

app = Flask(__name__)

PROJECTS = [
    {
        "key": "winchester",
        "title": "ВИНЧЕСТЕРЪ",
        "subtitle": "Конструктор крафтовой колбасы",
        "text": "Интерактивный прототип интернет-магазина: шесть шагов конфигурации, ползунки состава, "
                "срез батона генерируется под выбранные параметры, технологическая карта, расчёт цены и срока созревания.",
        "tags": ["Python", "Flask", "Pillow", "UI-прототип"],
        "url": "/winchester/",
        "repo": "https://github.com/pakmaninlaw/Winchester",
        "status": "live",
        "image": "/winchester/banner.jpg",
    },
    {
        "key": "crm",
        "title": "CRM аналитика",
        "subtitle": "Интервью → задачи → исполнители → KPI",
        "text": "Протокол встречи со стейкхолдером (текстом или голосом) превращается в задачи для Frontend, Backend, "
                "Architecture и Security, назначается на свободных сотрудников, считается время, качество и KPI.",
        "tags": ["Flask", "SQLite", "Web Speech API", "KPI"],
        "url": "/crm/",
        "repo": "https://github.com/pakmaninlaw/crm-system-analyst",
        "status": "live",
    },
    {
        "key": "icq",
        "title": "ICQ-мессенджер",
        "subtitle": "Клиент-серверный чат в духе «Аськи»",
        "text": "Обмен сообщениями в реальном времени через WebSocket, статусы «в сети», история переписки "
                "и легендарное «о-оу». Проект в разработке.",
        "tags": ["Flask-SocketIO", "WebSocket", "TCP/IP"],
        "url": None,
        "repo": None,
        "status": "dev",
    },
]

PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Сергей Пакман — проекты системного аналитика</title>
<meta name="description" content="Учебные проекты системного аналитика: прототип магазина ВИНЧЕСТЕРЪ, CRM аналитика, ICQ-мессенджер.">
<script>try { document.documentElement.dataset.theme = new URLSearchParams(location.search).get('theme') || localStorage.getItem('sa-theme') || 'classic'; } catch (e) { document.documentElement.dataset.theme = 'classic'; }</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;800&display=swap" rel="stylesheet">
<style>
  /* Темы оформления: classic (по умолчанию), graphite, bordeaux, violet */
  :root, :root[data-theme="classic"] {
    --bg: #0f1724; --panel: #162131; --panel-2: #1b293d; --text: #e8edf4; --muted: #9fb0c4;
    --line: rgba(255,255,255,.08); --accent: #7d9cc4; --accent-2: #c9a86a;
    --glow-1: #1d3557; --glow-2: #2b2a24; --crm-cover: linear-gradient(135deg, #1f3a5f, #36557f);
    --win: #d8aa63; --crm: #7d9cc4; --icq: #7ed957; color-scheme: dark;
  }
  :root[data-theme="graphite"] {
    --bg: #141518; --panel: #1b1d21; --panel-2: #222529; --text: #ececec; --muted: #a4a8ae;
    --line: rgba(255,255,255,.08); --accent: #b4bcc8; --accent-2: #d9dde3;
    --glow-1: #2a2d33; --glow-2: #1f2226; --crm-cover: linear-gradient(135deg, #3a3f47, #59616c);
    --crm: #b4bcc8;
  }
  :root[data-theme="bordeaux"] {
    --bg: #1a1214; --panel: #22181b; --panel-2: #2a1d21; --text: #f1e9ea; --muted: #bfa9ad;
    --line: rgba(255,255,255,.08); --accent: #c7798a; --accent-2: #d8b98a;
    --glow-1: #4a1a28; --glow-2: #2c2320; --crm-cover: linear-gradient(135deg, #5a1a2b, #83344a);
    --crm: #c7798a;
  }
  :root[data-theme="violet"] {
    --bg: #0f1020; --panel: #171933; --panel-2: #1e2144; --text: #eceefe; --muted: #a3a8d6;
    --line: rgba(255,255,255,.08); --accent: #8b7cff; --accent-2: #4fd1c5;
    --glow-1: #2b2366; --glow-2: #0f4c55; --crm-cover: linear-gradient(135deg, #667eea, #764ba2);
    --crm: #8b7cff;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; }
  body {
    background: radial-gradient(1200px 600px at 10% -10%, var(--glow-1) 0%, transparent 60%),
                radial-gradient(900px 500px at 110% 10%, var(--glow-2) 0%, transparent 55%), var(--bg);
    color: var(--text); font-family: 'Manrope', 'Segoe UI', sans-serif; min-height: 100vh;
    transition: background-color .4s, color .4s;
  }
  .wrap { max-width: 1120px; margin: 0 auto; padding: 56px 16px 40px; }
  header { margin-bottom: 40px; position: relative; }

  /* Переключатель темы */
  .themes { position: absolute; top: -36px; right: 0; display: flex; align-items: center; gap: 8px; color: var(--muted); font-size: .8rem; }
  .themes button {
    width: 22px; height: 22px; border-radius: 50%; border: 2px solid transparent; padding: 0; cursor: pointer;
    background: var(--sw); box-shadow: 0 0 0 1px var(--line); transition: transform .25s, border-color .25s;
  }
  .themes button:hover { transform: scale(1.18); }
  .themes button[aria-pressed="true"] { border-color: var(--text); }
  .themes .t-classic { --sw: linear-gradient(135deg, #1f3a5f 50%, #c9a86a 50%); }
  .themes .t-graphite { --sw: linear-gradient(135deg, #3a3f47 50%, #d9dde3 50%); }
  .themes .t-bordeaux { --sw: linear-gradient(135deg, #5a1a2b 50%, #d8b98a 50%); }
  .themes .t-violet { --sw: linear-gradient(135deg, #764ba2 50%, #4fd1c5 50%); }
  @media (max-width: 600px) { .themes { position: static; margin-bottom: 18px; } }
  .eyebrow { color: var(--accent-2); font-weight: 600; letter-spacing: .12em; text-transform: uppercase; font-size: .8rem; }
  h1 { font-size: clamp(2rem, 5vw, 3.2rem); line-height: 1.1; margin: 10px 0 12px; font-weight: 800; }
  h1 span { background: linear-gradient(90deg, var(--accent), var(--accent-2)); -webkit-background-clip: text; background-clip: text; color: transparent; }
  .lead { color: var(--muted); max-width: 640px; font-size: 1.05rem; line-height: 1.6; margin: 0; }

  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 22px; }
  .card {
    --c: var(--accent);
    position: relative; display: flex; flex-direction: column; border-radius: 20px; overflow: hidden;
    background: linear-gradient(180deg, var(--panel-2), var(--panel)); border: 1px solid var(--line);
    color: inherit; text-decoration: none; isolation: isolate;
    transition: transform .35s cubic-bezier(.2,.8,.2,1), box-shadow .35s, border-color .35s;
  }
  .card::after {  /* мягкий блик, бегущий по карточке при наведении */
    content: ""; position: absolute; inset: 0; z-index: 2; pointer-events: none;
    background: linear-gradient(115deg, transparent 35%, rgba(255,255,255,.10) 50%, transparent 65%);
    transform: translateX(-120%); transition: transform .9s ease;
  }
  .card:hover, .card:focus-visible {
    transform: translateY(-6px); border-color: color-mix(in srgb, var(--c) 55%, transparent);
    box-shadow: 0 18px 50px -12px color-mix(in srgb, var(--c) 45%, transparent);
  }
  .card:hover::after, .card:focus-visible::after { transform: translateX(120%); }
  .card:focus-visible { outline: 2px solid var(--c); outline-offset: 3px; }
  .card.winchester { --c: var(--win); }
  .card.crm { --c: var(--crm); }
  .card.icq { --c: var(--icq); cursor: default; }

  .cover { height: 180px; position: relative; overflow: hidden; display: grid; place-items: center; }
  .cover img { width: 100%; height: 100%; object-fit: cover; transition: transform .6s ease; }
  .card:hover .cover img { transform: scale(1.06); }
  .cover.crm { background: var(--crm-cover); }
  .cover.icq { background: radial-gradient(circle at 50% 60%, #1f3a1a, #0f1a0d); }

  /* Мини-дашборд CRM на обложке */
  .dash { width: 78%; display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
  .dash div { background: rgba(255,255,255,.18); border-radius: 8px; height: 44px; transition: transform .4s; }
  .dash div:nth-child(1) { height: 60px; } .dash div:nth-child(3) { height: 36px; }
  .dash .bar { grid-column: span 4; height: 10px; background: rgba(255,255,255,.14); position: relative; overflow: hidden; }
  .dash .bar::before { content: ""; position: absolute; inset: 0; width: 72%; background: var(--accent-2); border-radius: 8px; transition: width .6s; }
  .card:hover .dash div:nth-child(odd) { transform: translateY(-4px); }
  .card:hover .dash .bar::before { width: 88%; }

  /* Цветок в духе ICQ — медленно вращается при наведении */
  .flower { width: 96px; height: 96px; position: relative; transition: transform 1.6s cubic-bezier(.2,.8,.2,1); }
  .flower i { position: absolute; left: 36px; top: 0; width: 24px; height: 40px; border-radius: 50%; background: var(--icq); transform-origin: 12px 48px; }
  .flower i:nth-child(1) { background: #ff5a4f; }
  .flower i:nth-child(2) { transform: rotate(51.4deg); } .flower i:nth-child(3) { transform: rotate(102.8deg); }
  .flower i:nth-child(4) { transform: rotate(154.2deg); } .flower i:nth-child(5) { transform: rotate(205.6deg); }
  .flower i:nth-child(6) { transform: rotate(257deg); } .flower i:nth-child(7) { transform: rotate(308.4deg); }
  .flower b { position: absolute; left: 34px; top: 34px; width: 28px; height: 28px; border-radius: 50%; background: #f5d547; }
  .card.icq:hover .flower { transform: rotate(180deg); }

  .body { padding: 20px 22px 22px; display: flex; flex-direction: column; gap: 10px; flex: 1; }
  .top { display: flex; justify-content: space-between; align-items: start; gap: 10px; }
  h2 { margin: 0; font-size: 1.35rem; font-weight: 800; }
  .sub { color: var(--c); font-weight: 600; font-size: .92rem; margin: 2px 0 0; }
  .badge { font-size: .72rem; font-weight: 700; padding: 5px 10px; border-radius: 999px; white-space: nowrap; }
  .badge.live { background: color-mix(in srgb, var(--accent-2) 16%, transparent); color: var(--accent-2); }
  .badge.live::before { content: "● "; animation: pulse 2s infinite; }
  .badge.dev { background: rgba(126,217,87,.12); color: var(--icq); }
  @keyframes pulse { 50% { opacity: .35; } }
  .text { color: var(--muted); line-height: 1.55; margin: 0; font-size: .95rem; }
  .tags { display: flex; flex-wrap: wrap; gap: 6px; margin-top: auto; padding-top: 6px; }
  .tags span { font-size: .75rem; color: var(--muted); border: 1px solid var(--line); padding: 3px 9px; border-radius: 999px; }
  .actions { display: flex; justify-content: space-between; align-items: center; margin-top: 8px; font-weight: 600; font-size: .9rem; }
  .go { color: var(--c); display: inline-flex; gap: 6px; align-items: center; }
  .go::after { content: "→"; transition: transform .3s; }
  .card:hover .go::after { transform: translateX(5px); }
  .repo { color: var(--muted); text-decoration: none; position: relative; z-index: 3; }
  .repo:hover { color: var(--text); }
  .progress { height: 6px; border-radius: 99px; background: rgba(255,255,255,.08); overflow: hidden; }
  .progress::before { content: ""; display: block; height: 100%; width: 25%; background: var(--icq); border-radius: 99px; transition: width 1.2s; }
  .card.icq:hover .progress::before { width: 35%; }

  footer { margin-top: 48px; color: var(--muted); font-size: .85rem; display: flex; flex-wrap: wrap; gap: 8px 20px; justify-content: space-between; }
  footer a { color: var(--muted); }
  @media (prefers-reduced-motion: reduce) { *, *::before, *::after { transition: none !important; animation: none !important; } }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="themes" role="group" aria-label="Оформление">
      <span>Оформление</span>
      <button class="t-classic" data-theme="classic" title="Классика"></button>
      <button class="t-graphite" data-theme="graphite" title="Графит"></button>
      <button class="t-bordeaux" data-theme="bordeaux" title="Бордо"></button>
      <button class="t-violet" data-theme="violet" title="Фиолетовая"></button>
    </div>
    <div class="eyebrow">Портфолио · курс «Системный аналитик»</div>
    <h1>Сергей Пакман — <span>проекты аналитика</span></h1>
    <p class="lead">Прототипы, которые я проектирую и собираю в процессе обучения: от интервью со стейкхолдером
      до работающего продукта. Выберите проект — всё открывается прямо в браузере.</p>
  </header>

  <main class="grid">
  {% for p in projects %}
    {% if p.url %}<a class="card {{ p.key }}" href="{{ p.url }}">{% else %}<div class="card {{ p.key }}" tabindex="0">{% endif %}
      <div class="cover {{ p.key }}">
        {% if p.image %}<img src="{{ p.image }}" alt="{{ p.title }}" fetchpriority="high">
        {% elif p.key == 'crm' %}<div class="dash"><div></div><div></div><div></div><div></div><div class="bar"></div></div>
        {% else %}<div class="flower"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><b></b></div>{% endif %}
      </div>
      <div class="body">
        <div class="top">
          <div><h2>{{ p.title }}</h2><p class="sub">{{ p.subtitle }}</p></div>
          {% if p.status == 'live' %}<span class="badge live">работает</span>{% else %}<span class="badge dev">в разработке</span>{% endif %}
        </div>
        <p class="text">{{ p.text }}</p>
        {% if p.status == 'dev' %}<div class="progress" title="Готовность"></div>{% endif %}
        <div class="tags">{% for t in p.tags %}<span>{{ t }}</span>{% endfor %}</div>
        <div class="actions">
          {% if p.url %}<span class="go">Открыть</span>{% else %}<span class="go" style="opacity:.6">Скоро</span>{% endif %}
          {% if p.repo %}<object><a class="repo" href="{{ p.repo }}" target="_blank" rel="noopener">GitHub ↗</a></object>{% endif %}
        </div>
      </div>
    {% if p.url %}</a>{% else %}</div>{% endif %}
  {% endfor %}
  </main>

  <footer>
    <span>© 2026 Сергей Пакман · учебные проекты</span>
    <a href="https://github.com/pakmaninlaw" target="_blank" rel="noopener">github.com/pakmaninlaw</a>
  </footer>
</div>
<script>
  // Тема сохраняется в браузере и общая для витрины и CRM
  const buttons = document.querySelectorAll('.themes button');
  function applyTheme(name) {
    document.documentElement.dataset.theme = name;
    buttons.forEach(b => b.setAttribute('aria-pressed', String(b.dataset.theme === name)));
    try { localStorage.setItem('sa-theme', name); } catch (e) {}
  }
  buttons.forEach(b => b.addEventListener('click', () => applyTheme(b.dataset.theme)));
  applyTheme(document.documentElement.dataset.theme || 'classic');
</script>
</body>
</html>
"""


@app.route("/")
def index():
    # Старые ссылки на магазин с параметрами конфигурации (?meat=…) ведут в магазин
    if request.args.get("meat") or request.args.get("caliber"):
        return redirect("/winchester/?" + request.query_string.decode(), code=301)
    return render_template_string(PAGE, projects=PROJECTS)


# Старые адреса магазина (до переезда на /winchester) — постоянная переадресация
@app.route("/banner.jpg")
@app.route("/tube.png")
@app.route("/api/<path:rest>")
@app.route("/set/<path:rest>")
def legacy_winchester(rest=None):
    target = "/winchester" + request.path
    if request.query_string:
        target += "?" + request.query_string.decode()
    return redirect(target, code=308)


@app.route("/favicon.ico")
def favicon():
    return app.response_class(status=204)


# ==================== ЗАЩИТА ОТ БОТОВ ====================
class PostRateLimit:
    """
    WSGI-прослойка: ограничивает число POST-запросов с одного IP.
    Правила проверяются по префиксу пути; первое совпавшее — действует.
    """

    RULES = [
        # (префикс пути, запросов в минуту, запросов в сутки)
        ("/winchester/api/order", 3, 20),   # заявки в магазин
        ("/crm/", 40, 600),                 # действия в CRM
        ("/", 20, 300),                     # всё остальное
    ]

    def __init__(self, wsgi_app):
        self.app = wsgi_app
        self.hits = {}
        self.lock = threading.Lock()
        self.last_cleanup = time.time()

    @staticmethod
    def client_ip(environ):
        forwarded = environ.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()
        return environ.get("HTTP_X_REAL_IP") or forwarded or environ.get("REMOTE_ADDR", "?")

    def __call__(self, environ, start_response):
        if environ.get("REQUEST_METHOD") != "POST":
            return self.app(environ, start_response)
        path = environ.get("SCRIPT_NAME", "") + environ.get("PATH_INFO", "")
        prefix, per_min, per_day = next(r for r in self.RULES if path.startswith(r[0]))
        now = time.time()
        with self.lock:
            if now - self.last_cleanup > 3600:
                self.hits = {k: q for k, q in self.hits.items() if q and now - q[-1] < 86400}
                self.last_cleanup = now
            q = self.hits.setdefault((self.client_ip(environ), prefix), deque())
            while q and now - q[0] > 86400:
                q.popleft()
            last_minute = sum(1 for t in q if now - t < 60)
            if last_minute >= per_min or len(q) >= per_day:
                body = json.dumps({"success": False, "ok": False,
                                   "error": "Слишком много запросов. Подождите минуту и попробуйте снова.",
                                   "errors": {"phone": "Слишком много заявок. Попробуйте позже."}},
                                  ensure_ascii=False).encode("utf-8")
                start_response("429 Too Many Requests", [
                    ("Content-Type", "application/json; charset=utf-8"),
                    ("Content-Length", str(len(body))),
                    ("Retry-After", "60"),
                ])
                return [body]
            q.append(now)
        return self.app(environ, start_response)


def load_module(name, path):
    """Загрузить проект по пути к файлу (у магазина и CRM одинаковое имя main.py)."""
    import importlib.util
    import os
    import sys
    folder = os.path.dirname(os.path.abspath(path))
    if folder not in sys.path:
        sys.path.append(folder)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def build_application(mounts):
    """Главное WSGI-приложение: витрина + проекты по префиксам + ограничение частоты запросов."""
    return PostRateLimit(DispatcherMiddleware(app.wsgi_app, mounts))


if __name__ == "__main__":
    # Локальный запуск только витрины: python portal.py
    app.run(port=5050, debug=True)
