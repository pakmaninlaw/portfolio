"""
Локальный запуск всего сайта как на PythonAnywhere: python local_run.py -> http://127.0.0.1:8000
Ожидает рядом папки ../Winchester и ../CRM (или пути в WINCHESTER_DIR и CRM_DIR).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WINCHESTER_DIR = os.environ.get("WINCHESTER_DIR", os.path.join(HERE, "..", "Winchester"))
CRM_DIR = os.environ.get("CRM_DIR", os.path.join(HERE, "..", "CRM"))

os.environ.setdefault("CRM_DEMO", "1")
os.environ.setdefault("WINCHESTER_PUBLIC", "1")
os.environ.setdefault("CRM_DB", os.path.join(HERE, "demo_crm.db"))  # демо-база отдельно от рабочей
sys.path.insert(0, HERE)

import portal  # noqa: E402


def build():
    winchester = portal.load_module("winchester_app", os.path.join(WINCHESTER_DIR, "main.py"))
    crm = portal.load_module("crm_app", os.path.join(CRM_DIR, "main.py"))
    crm.init_db()
    return portal.build_application({"/winchester": winchester.app, "/crm": crm.app})


if __name__ == "__main__":
    from werkzeug.serving import run_simple
    run_simple("127.0.0.1", 8000, build(), use_reloader=False, threaded=True)
