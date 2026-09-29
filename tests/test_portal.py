"""
Проверка сайта целиком (витрина + магазин + CRM): python tests/test_portal.py
Нужны соседние папки ../Winchester и ../CRM.
"""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ["CRM_DB"] = os.path.join(tempfile.mkdtemp(), "crm.db")
# Временная папка конспекта со своим тестовым паролем (настоящий пароль в репозиторий не попадает)
NOTES = tempfile.mkdtemp()
os.environ["NOTES_DIR"] = NOTES
from werkzeug.security import generate_password_hash  # noqa: E402
open(os.path.join(NOTES, "password.hash"), "w", encoding="utf-8").write(generate_password_hash("test-pass"))
open(os.path.join(NOTES, "lectures.html"), "w", encoding="utf-8").write("<h1>Секретный конспект</h1>")
sys.path.insert(0, HERE)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import local_run  # noqa: E402
from werkzeug.test import Client  # noqa: E402

client = Client(local_run.build())


def check(method, url, status, **kw):
    r = getattr(client, method)(url, **kw)
    assert r.status_code == status, (method, url, r.status_code, r.get_data(as_text=True)[:200])
    return r


html = check("get", "/", 200).get_data(as_text=True)
assert "ВИНЧЕСТЕРЪ" in html and "CRM аналитика" in html and "icq-messenger" in html
print("✔ витрина")

shop = check("get", "/winchester/", 200).get_data(as_text=True)
assert 'var ROOT = "/winchester"' in shop and 'src="/winchester/banner.jpg"' in shop
assert 'class="back-home" href="/"' in shop, "нет кнопки «Все проекты» в магазине"
check("get", "/winchester/banner.jpg", 200)
check("get", "/winchester/api/slice.png?meat=beef&caliber=20&tech=cured&fat=20&spice=1.5", 200)
check("get", "/winchester/api/quote?meat=beef", 200)
check("get", "/winchester/admin/orders", 404)
check("get", "/winchester/api/debug", 404)
print("✔ магазин под /winchester, служебные страницы закрыты")

assert check("get", "/banner.jpg", 308).headers["Location"].endswith("/winchester/banner.jpg")
assert "/winchester/?meat=pork" in check("get", "/?meat=pork", 301).headers["Location"]
print("✔ старые ссылки переадресуются")

crm = check("get", "/crm/", 200).get_data(as_text=True)
assert 'const ROOT = "/crm"' in crm and "Демо-версия" in crm
for page in ["/crm/", "/crm/tasks", "/crm/kanban", "/crm/bpmn", "/crm/interviews", "/crm/employees", "/crm/kpi", "/crm/log"]:
    assert 'class="back" href="/"' in check("get", page, 200).get_data(as_text=True), page
print("✔ CRM под /crm в демо-режиме")

assert "Введите пароль" in check("get", "/notes", 200).get_data(as_text=True)
assert "Неверный пароль" in check("post", "/notes/login", 401, data={"password": "wrong"}, headers={"X-Real-IP": "10.0.0.9"}).get_data(as_text=True)
check("post", "/notes/login", 302, data={"password": "test-pass"}, headers={"X-Real-IP": "10.0.0.9"})
page = check("get", "/notes", 200)
assert "Секретный конспект" in page.get_data(as_text=True) and page.headers["Cache-Control"] == "private, no-store"
check("get", "/notes/logout", 302)
assert "Введите пароль" in check("get", "/notes", 200).get_data(as_text=True)
for d in ("crm", "icq"):
    assert "marked.min.js" in check("get", f"/docs/{d}", 200).get_data(as_text=True)
check("get", "/docs/unknown", 404)
print("✔ конспект по паролю и разбор кода")

codes = [client.post("/winchester/api/order", json={"name": "Тест", "phone": "+7 900 000-00-00"},
                     headers={"X-Real-IP": "10.0.0.1"}).status_code for _ in range(4)]
assert codes[-1] == 429, codes
other_ip = client.post("/winchester/api/order", json={}, headers={"X-Real-IP": "10.0.0.2"}).status_code
assert other_ip != 429
print(f"✔ защита от ботов: заявки с одного IP {codes}")
print("Все проверки пройдены")
