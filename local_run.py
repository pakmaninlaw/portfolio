"""
Локальный запуск всего сайта как на PythonAnywhere: python local_run.py -> http://127.0.0.1:8000
Ожидает рядом папки ../Winchester и ../CRM (или пути в WINCHESTER_DIR и CRM_DIR);
../LegalCRM (LEGAL_DIR) подключается, если есть.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WINCHESTER_DIR = os.environ.get("WINCHESTER_DIR", os.path.join(HERE, "..", "Winchester"))
CRM_DIR = os.environ.get("CRM_DIR", os.path.join(HERE, "..", "CRM"))

os.environ.setdefault("CRM_DEMO", "1")
os.environ.setdefault("WINCHESTER_PUBLIC", "1")
os.environ.setdefault("CRM_DB", os.path.join(HERE, "demo_crm.db"))  # демо-база отдельно от рабочей
os.environ.setdefault("NOTES_DIR", os.path.join(HERE, "..", "notes"))       # конспект по паролю (вне репозитория)
os.environ.setdefault("CRM_DOCS", os.path.join(CRM_DIR, "docs", "РАЗБОР_КОДА.md"))
os.environ.setdefault("ICQ_DOCS", os.path.join(HERE, "..", "ICQ", "docs", "РАЗБОР_КОДА.md"))
LEGAL_DIR = os.environ.get("LEGAL_DIR", os.path.join(HERE, "..", "LegalCRM"))
# Локальные базы юридической CRM — рядом с витриной, чтобы не трогать папку самого проекта
os.environ.setdefault("LEGAL_DB", os.path.join(HERE, "local_legal.db"))
os.environ.setdefault("LEGAL_DEMO_DB", os.path.join(HERE, "demo_legal.db"))
os.environ.setdefault("LEGAL_UPLOADS", os.path.join(HERE, "local_legal_uploads"))
os.environ.setdefault("LEGAL_SECRET_KEY", "local-dev-only")
sys.path.insert(0, HERE)

import portal  # noqa: E402


def build():
    winchester = portal.load_module("winchester_app", os.path.join(WINCHESTER_DIR, "main.py"))
    crm = portal.load_module("crm_app", os.path.join(CRM_DIR, "main.py"))
    crm.init_db()
    mounts = {"/winchester": winchester.app, "/crm": crm.app}
    if os.path.isdir(os.path.join(LEGAL_DIR, "legalcrm")):   # юридическая CRM — если лежит рядом
        sys.path.insert(0, LEGAL_DIR)
        from legalcrm import create_app as create_legal_app
        mounts["/legal"] = create_legal_app()
        mounts["/legal-demo"] = create_legal_app({"DEMO": True})
    return portal.build_application(mounts)


if __name__ == "__main__":
    from werkzeug.serving import run_simple
    run_simple("127.0.0.1", 8000, build(), use_reloader=False, threaded=True)
