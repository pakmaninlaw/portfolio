"""
WSGI-файл для PythonAnywhere: один сайт — несколько проектов.
Копируется в /var/www/pakmaninlaw_pythonanywhere_com_wsgi.py

  /             -> ~/portfolio/portal.py     (витрина)
  /winchester/  -> ~/mysite/main.py          (ВИНЧЕСТЕРЪ)
  /crm/         -> ~/crm/main.py             (CRM аналитика, демо-режим)
"""
import os
import sys
import time

HOME = "/home/PakmanInLaw"

# Сервер PythonAnywhere живёт по UTC — сроки задач и «сегодня» считаем по Самаре (UTC+4)
os.environ["TZ"] = "Europe/Samara"
time.tzset()

os.environ["CRM_DEMO"] = "1"            # CRM: демо-данные, лимиты, ежедневный сброс
os.environ["WINCHESTER_PUBLIC"] = "1"   # магазин: закрыть журнал заявок и отладку

sys.path.insert(0, f"{HOME}/portfolio")
import portal  # noqa: E402

winchester = portal.load_module("winchester_app", f"{HOME}/mysite/main.py")
crm = portal.load_module("crm_app", f"{HOME}/crm/main.py")
crm.init_db()

application = portal.build_application({
    "/winchester": winchester.app,
    "/crm": crm.app,
})
