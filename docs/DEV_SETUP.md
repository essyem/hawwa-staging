Developer setup — Hawwa
=======================

Purpose
-------
This short doc explains how to use the provided `hawwa/settings_dev.py` file for local development and testing in a VM or codespace. `settings_dev.py` is intentionally committed to the repo to make onboarding easier.

Environment variables supported by `hawwa/settings_dev.py`
-------------------------------------------------------
- `HAWWA_ALLOWED_HOSTS` — comma-separated hostnames to allow (default: `localhost,127.0.0.1,testserver`).
- `HAWWA_DB_PATH` — path to the SQLite database file used for development (default: `db.sqlite3` in the repo root).
- `HAWWA_EMAIL_BACKEND` — Django email backend to use for development (default: `django.core.mail.backends.console.EmailBackend`).
- `DJANGO_SECRET_KEY` — optional secret key to override the default development secret. If not set, a development-safe secret is used (do not use for production).

Quick start (codespaces / local VM)
----------------------------------
1. Create and activate a Python virtual environment (recommended):
   - `python3 -m venv .venv && source .venv/bin/activate`
2. Install deps:
   - `pip install -r requirements.txt`
3. Set environment variables (optional):
   - `export HAWWA_ALLOWED_HOSTS=localhost,127.0.0.1,testserver`
   - `export HAWWA_DB_PATH=$PWD/db.sqlite3`
   - `export HAWWA_EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend`
4. Run migrations (dev settings use SQLite):
   - `python3 manage.py migrate --settings=hawwa.settings_dev`
5. Run tests under dev settings:
   - `python3 manage.py test --settings=hawwa.settings_dev -v 1`

Notes and safety
----------------
- `hawwa/settings_dev.py` is for development only and intentionally uses safe defaults. Never use it in production.
- Keep production secrets (database credentials, real secret keys) out of commits. Use environment variables or a secure secrets manager in production.

If you want, I can add a GitHub Actions workflow that executes the same `manage.py test --settings=hawwa.settings_dev` command on every PR.
