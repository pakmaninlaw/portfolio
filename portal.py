"""
Портфолио системного аналитика — стартовая страница и «склейка» проектов на одном сайте.

  /             — витрина проектов
  /winchester/  — ВИНЧЕСТЕРЪ, конструктор колбасы (ДЗ «Мир колбасы Люкс»)
  /crm/         — CRM системного аналитика (итоговая работа)
  /notes        — конспект лекций (по паролю; файл и хеш пароля лежат только на сервере, не в GitHub)
  /docs/<проект> — разбор кода на русском (Markdown из репозиториев проектов)

Плюс защита от ботов: ограничение частоты POST-запросов с одного IP.
"""
import json
import os
import secrets
import threading
import time
from collections import deque
from datetime import timedelta

from flask import Flask, abort, redirect, render_template_string, request, session
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.security import check_password_hash

app = Flask(__name__)

# Закрытые материалы: папка вне репозитория (на сервере ~/notes): lectures.html и password.hash
NOTES_DIR = os.environ.get("NOTES_DIR") or os.path.expanduser("~/notes")
DOCS = {
    "crm": ("Разбор кода: CRM аналитика", os.environ.get("CRM_DOCS") or os.path.expanduser("~/crm/docs/РАЗБОР_КОДА.md"),
            "https://github.com/pakmaninlaw/crm-system-analyst"),
    "icq": ("Разбор кода: ICQ-мессенджер", os.environ.get("ICQ_DOCS") or os.path.expanduser("~/icq/docs/РАЗБОР_КОДА.md"),
            "https://github.com/pakmaninlaw/icq-messenger"),
}


def _secret_key():
    """Ключ подписи сессий: из переменной окружения или из файла рядом с материалами (создаётся один раз)."""
    if os.environ.get("PORTAL_SECRET"):
        return os.environ["PORTAL_SECRET"]
    path = os.path.join(NOTES_DIR, ".portal_secret")
    try:
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        key = secrets.token_hex(32)
        try:
            os.makedirs(NOTES_DIR, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(key)
        except OSError:
            pass
        return key


app.secret_key = _secret_key()
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                  PERMANENT_SESSION_LIFETIME=timedelta(days=30))

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
        "text": "Интервью со стейкхолдером (текстом или голосом) превращается в задачи по отделам и BPMN-схему процесса. "
                "Дашборд с графиками, канбан-доска, KPI и контроль качества, журнал событий.",
        "tags": ["Flask", "SQLite", "BPMN", "Канбан", "Chart.js"],
        "url": "/crm/",
        "repo": "https://github.com/pakmaninlaw/crm-system-analyst",
        "status": "live",
    },
    {
        "key": "icq",
        "title": "ICQ-мессенджер",
        "subtitle": "Клиент-серверный чат в духе «Аськи»",
        "text": "Сервер на Flask-SocketIO, веб-клиент и настольный клиент на python-socketio: вход с хешем пароля, "
                "история, «в сети», «печатает…», защита от спама и легендарное «о-оу». Запускается на своём компьютере.",
        "tags": ["Flask-SocketIO", "WebSocket", "Tkinter", "TCP/IP"],
        "url": None,
        "repo": "https://github.com/pakmaninlaw/icq-messenger",
        "status": "local",
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

  .mat-title { font-size: 1.25rem; margin: 44px 0 14px; font-weight: 800; }
  .mats { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; }
  .mat { display: flex; gap: 14px; align-items: flex-start; padding: 16px 18px; border-radius: 16px; border: 1px solid var(--line);
         background: linear-gradient(180deg, var(--panel-2), var(--panel)); color: inherit; text-decoration: none;
         transition: transform .3s, border-color .3s; }
  .mat:hover, .mat:focus-visible { transform: translateY(-3px); border-color: var(--accent); }
  .mat-ic { font-size: 1.6rem; line-height: 1; }
  .mat b { display: block; margin-bottom: 4px; }
  .mat small { color: var(--muted); line-height: 1.45; display: block; }
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
          {% if p.status == 'live' %}<span class="badge live">работает</span>{% elif p.status == 'local' %}<span class="badge dev">готов · на GitHub</span>{% else %}<span class="badge dev">в разработке</span>{% endif %}
        </div>
        <p class="text">{{ p.text }}</p>

        <div class="tags">{% for t in p.tags %}<span>{{ t }}</span>{% endfor %}</div>
        <div class="actions">
          {% if p.url %}<span class="go">Открыть</span>{% elif p.repo %}<span class="go" style="opacity:.75">Запуск на ПК</span>{% else %}<span class="go" style="opacity:.6">Скоро</span>{% endif %}
          {% if p.repo %}<object><a class="repo" href="{{ p.repo }}" target="_blank" rel="noopener">GitHub ↗</a></object>{% endif %}
        </div>
      </div>
    {% if p.url %}</a>{% else %}</div>{% endif %}
  {% endfor %}
  </main>

  <h2 class="mat-title">Материалы</h2>
  <div class="mats">
    <a class="mat" href="/notes"><span class="mat-ic">🔒</span><span><b>Конспект лекций</b><small>14–25 сентября: BPMN, алгоритмизация, Wi-Fi и TCP/IP. Доступ по паролю — из уважения к преподавателю.</small></span></a>
    <a class="mat" href="/docs/crm"><span class="mat-ic">📘</span><span><b>Разбор кода CRM</b><small>Как устроена CRM: SQL, шаблоны, разбор интервью, KPI, генератор BPMN — простыми словами.</small></span></a>
    <a class="mat" href="/docs/icq"><span class="mat-ic">📗</span><span><b>Разбор кода ICQ</b><small>WebSocket и Socket.IO, потоки, хеши паролей, синтез звука «о-оу».</small></span></a>
  </div>

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


# ==================== КОНСПЕКТ ПО ПАРОЛЮ ====================
NOTES_LOGIN = """
<!DOCTYPE html>
<html lang="ru"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Конспект лекций — вход</title>
<style>
  body { margin: 0; min-height: 100vh; display: grid; place-items: center; background: #0f1724; color: #e8edf4;
         font-family: 'Segoe UI', Roboto, Arial, sans-serif; padding: 16px; box-sizing: border-box; }
  form { background: #172233; border: 1px solid rgba(255,255,255,.08); border-radius: 18px; padding: 28px; width: min(380px, 100%); box-sizing: border-box; }
  h1 { font-size: 1.3rem; margin: 0 0 6px; } p { color: #9fb0c4; margin: 0 0 18px; font-size: .92rem; line-height: 1.5; }
  input { width: 100%; box-sizing: border-box; padding: 11px 13px; border-radius: 10px; border: 1px solid #2c3b52; background: #0f1724; color: #e8edf4; font-size: 1rem; }
  button { width: 100%; margin-top: 14px; padding: 11px; border: 0; border-radius: 10px; background: #c9a86a; color: #1b1406; font-weight: 700; font-size: 1rem; cursor: pointer; }
  .err { color: #f08a9c; margin-top: 12px; min-height: 1.2em; font-size: .9rem; }
  a { color: #9fb0c4; font-size: .85rem; display: inline-block; margin-top: 16px; }
</style></head>
<body>
<form method="post" action="/notes/login">
  <h1>🔒 Конспект лекций</h1>
  <p>Материалы курса «Системный аналитик» открыты для группы. Введите пароль.</p>
  <input type="password" name="password" autofocus autocomplete="current-password" aria-label="Пароль">
  <button>Открыть</button>
  <div class="err">{{ error }}</div>
  <a href="/">← Все проекты</a>
</form>
</body></html>
"""

NOTES_WRAP_HEAD = """<!DOCTYPE html>
<html lang="ru"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<style>
  .back-bar { position: sticky; top: 0; z-index: 20; display: flex; justify-content: space-between; gap: 10px; padding: 8px 16px;
              background: #0f1724; font: 14px 'Segoe UI', Roboto, Arial, sans-serif; }
  .back-bar a { color: #c9d6e8; text-decoration: none; }
  .back-bar a:hover { color: #fff; }
</style></head><body>
<div class="back-bar"><a href="/">← Все проекты</a><a href="/notes/logout">Выйти</a></div>
"""

NOTES_WRAP_TAIL = """
<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.esm.min.mjs';
  const dark = matchMedia('(prefers-color-scheme: dark)').matches;
  mermaid.initialize({startOnLoad: true, theme: dark ? 'dark' : 'neutral', securityLevel: 'strict'});
</script>
</body></html>
"""


def notes_hash():
    try:
        with open(os.path.join(NOTES_DIR, "password.hash"), encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return None


@app.route("/notes")
def notes():
    if not session.get("notes_ok"):
        return render_template_string(NOTES_LOGIN, error="")
    try:
        with open(os.path.join(NOTES_DIR, "lectures.html"), encoding="utf-8") as f:
            body = f.read()
    except OSError:
        abort(404)
    resp = app.response_class(NOTES_WRAP_HEAD + body + NOTES_WRAP_TAIL, mimetype="text/html")
    resp.headers["Cache-Control"] = "private, no-store"
    resp.headers["X-Robots-Tag"] = "noindex"
    return resp


@app.route("/notes/login", methods=["POST"])
def notes_login():
    stored = notes_hash()
    password = request.form.get("password", "")
    if stored and password and check_password_hash(stored, password):
        session.permanent = True
        session["notes_ok"] = True
        return redirect("/notes")
    time.sleep(0.5)   # замедляем подбор (плюс общий лимит POST-запросов с одного IP)
    return render_template_string(NOTES_LOGIN, error="Неверный пароль" if stored else "Материалы ещё не загружены"), 401


@app.route("/notes/logout")
def notes_logout():
    session.pop("notes_ok", None)
    return redirect("/")


# ==================== РАЗБОР КОДА (Markdown) ====================
DOC_PAGE = """
<!DOCTYPE html>
<html lang="ru"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ title }}</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600;700&family=IBM+Plex+Mono&display=swap" rel="stylesheet">
<style>
  :root { --bg: #f5f6f8; --paper: #fff; --ink: #16213a; --muted: #5d6781; --line: #dfe3ea; --accent: #1f4e79; --code: #eef2f7; }
  @media (prefers-color-scheme: dark) { :root { --bg: #0f1522; --paper: #161e2e; --ink: #e6ebf3; --muted: #9aa6bd; --line: #28334a; --accent: #8fb0dc; --code: #1c2940; color-scheme: dark; } }
  body { margin: 0; background: var(--bg); color: var(--ink); font: 16px/1.65 'IBM Plex Sans', 'Segoe UI', Roboto, Arial, sans-serif; }
  .bar { position: sticky; top: 0; z-index: 5; background: var(--paper); border-bottom: 1px solid var(--line); padding: 10px 16px;
         display: flex; gap: 14px; flex-wrap: wrap; align-items: center; font-size: .9rem; }
  .bar a { color: var(--accent); text-decoration: none; } .bar .sp { margin-left: auto; }
  main { max-width: 880px; margin: 0 auto; padding: 24px 16px 60px; }
  h1, h2, h3 { line-height: 1.25; } h1 { font-size: 2rem; } h2 { margin-top: 2.2em; padding-top: .6em; border-top: 1px solid var(--line); }
  a { color: var(--accent); }
  code { font-family: 'IBM Plex Mono', Consolas, monospace; font-size: .88em; background: var(--code); padding: 1px 5px; border-radius: 4px; }
  pre { background: var(--code); border-radius: 10px; padding: 12px 14px; overflow-x: auto; } pre code { background: none; padding: 0; }
  table { border-collapse: collapse; display: block; overflow-x: auto; margin: 12px 0; }
  th, td { border: 1px solid var(--line); padding: 6px 10px; text-align: left; vertical-align: top; }
  th { background: var(--code); }
  blockquote { margin: 12px 0; padding: 8px 14px; border-left: 3px solid var(--accent); background: var(--paper); border-radius: 0 8px 8px 0; }
  details { background: var(--paper); border: 1px solid var(--line); border-radius: 10px; padding: 8px 12px; margin: 8px 0; }
  img { max-width: 100%; }
</style></head>
<body>
<div class="bar"><a href="/">← Все проекты</a><b>{{ title }}</b><a class="sp" href="{{ repo }}" target="_blank" rel="noopener">Код на GitHub ↗</a></div>
<main id="doc">Загрузка…</main>
<script id="md" type="application/json">{{ markdown|tojson }}</script>
<script src="https://cdn.jsdelivr.net/npm/marked@12.0.2/marked.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/dompurify@3.1.6/dist/purify.min.js"></script>
<script type="module">
  const md = JSON.parse(document.getElementById('md').textContent);
  const doc = document.getElementById('doc');
  doc.innerHTML = DOMPurify.sanitize(marked.parse(md), {ADD_TAGS: ['details', 'summary']});
  // Диаграммы mermaid из блоков ```mermaid
  const blocks = doc.querySelectorAll('pre code.language-mermaid');
  if (blocks.length) {
    const {default: mermaid} = await import('https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.esm.min.mjs');
    blocks.forEach(b => { const pre = document.createElement('pre'); pre.className = 'mermaid'; pre.textContent = b.textContent; b.parentElement.replaceWith(pre); });
    mermaid.initialize({startOnLoad: false, theme: matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'neutral'});
    await mermaid.run();
  }
</script>
</body></html>
"""


@app.route("/docs/<name>")
def docs(name):
    if name not in DOCS:
        abort(404)
    title, path, repo = DOCS[name]
    try:
        with open(path, encoding="utf-8") as f:
            markdown = f.read()
    except OSError:
        abort(404)
    return render_template_string(DOC_PAGE, title=title, markdown=markdown, repo=repo)


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
