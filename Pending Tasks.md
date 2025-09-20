Project: Hawwa — Pending Tasks & Review
=====================================

Generated: 2025-09-20

Overview
--------
This document is a concise review of the repository state and a prioritized list of pending technical tasks to make local development, testing, and CI smoother. It focuses on actionable, testable items and low-risk improvements.

Repository highlights
---------------------
- Django project using Django 5.2.3, Python 3.12.
- DRF-based API (app `api`) with viewsets and token/session authentication.
- Several domain apps present: `accounts`, `services`, `bookings`, `financial`, `payments`, `vendors`, `wellness`, `ai_buddy`, `reporting`, `analytics`, `operations`, `admin_dashboard`, `hrms`, `core`.
- Development convenience: added `hawwa/settings_dev.py` (VM-friendly, env-driven defaults).

Quick health-check performed
---------------------------
- Ran focused tests under `hawwa.settings_dev` (SQLite):
  - `api.tests.BookingTests.test_create_booking`: OK
  - `api.tests.ServiceTests.test_create_service_admin_only`: OK
- Performed `manage.py check` during tests and saw no system-check failures under `hawwa.settings_dev`.

Per-app quick notes (scan results)
---------------------------------
- accounts
  - Provides custom user model.
  - Tests exercised via `api.tests`.
  - No immediate critical issues seen.

- api
  - Houses serializers and viewsets used by tests.
  - Recent fixes made to `BookingSerializer` and `ServiceSerializer`, and `ServiceViewSet` permission behavior.
  - Priority: add more unit tests for serializers and permission edge cases.

- services
  - Service model includes duration and pricing fields. Defensive fixes added to handle non-timedelta duration values in development/test fixtures.
  - Priority: validate and centralize duration parsing (input normalization at serializer or API client layer).

- bookings
  - Booking model historically accepted shorthand inputs; defensive `__init__`/`save()` changes applied.
  - Booking API now supports shorthand booking_date/booking_time and `note` alias.
  - Priority: add serializer-focused unit tests and documentation for API payloads.

- financial
  - Has an extensive test file (`financial/tests.py`) covering budgets, ledgers, posting signals, materialized balances and more.
  - Tests appear comprehensive; keep running as part of CI.

- payments, vendors, wellness, ai_buddy, reporting, analytics, operations, admin_dashboard, hrms
  - Present in repository with various models/views; some template placeholders were added earlier to avoid TemplateDoesNotExist errors.
  - Priority: run test subsets for these apps and add high-level smoke tests.

Top priority pending tasks (short-term)
--------------------------------------
1) Full test suite run under `hawwa.settings_dev` and fix remaining failures (if any)
   - Why: ensure changes don't regress other areas.
   - Command: `python3 manage.py test --settings=hawwa.settings_dev -v 1`
   - Estimated impact: medium time cost; high confidence gain.

2) Add unit tests for API serializer behaviors
   - Areas: `BookingSerializer` shorthand handling, `ServiceSerializer` write/read behavior (category PK vs nested), and `ServiceViewSet` permission matrix.
   - Why: prevents regressions and documents expected payloads.

3) CI configuration (optional but recommended)
   - Add a CI flow (GitHub Actions) that runs tests under `hawwa.settings_dev` and linting for each PR.
   - Why: prevents breaks and provides immediate feedback on PRs.

4) Document developer setup and env variables
   - Create `docs/DEV_SETUP.md` or `README-dev.md` describing `hawwa/settings_dev.py` env vars: `HAWWA_ALLOWED_HOSTS`, `HAWWA_DB_PATH`, `HAWWA_EMAIL_BACKEND`, `DJANGO_SECRET_KEY`.
   - Why: makes it easier for other devs/VMs to boot the project.

5) Serializer / Model input normalization review
   - Consolidate parsing/normalization for fields like `duration`, `booking_date`/`booking_time` so a single layer handles the conversions (recommended: serializer-level validation).
   - Why: reduces repeated defensive code in models and makes APIs predictable.

Medium term tasks
-----------------
- Add per-app smoke tests for all apps (e.g., basic model creation and view access).
- Add automated template-verifier to CI to ensure templates referenced in code exist (a tool was created earlier; consider integrating it into CI).
- Consider adding `settings_dev.example.py` and moving secrets-only into local `.env` (or keep `settings_dev.py` committed but defend against accidental production use with strong comments and `DJANGO_SECRET_KEY` env var guidance).

Lower priority / Nice-to-have
----------------------------
- Add type hints and mypy static checks (if the team wants stricter typing).
- Add small benchmarks for heavy reporting functions in `financial` if performance is a concern.

Next immediate actions (I can do for you)
-----------------------------------------
1. Run the full test suite under `hawwa.settings_dev` and produce a report (I can run this and open issues for failing tests). (confirm and I will run it now)
2. Create `docs/DEV_SETUP.md` documenting `settings_dev` env vars and recommended local setup.
3. Add unit tests for the serializer behaviors described above.

If you'd like I will now run the full test suite and attach the report to the repo as `test-results-summary.txt` and then create a PR description. Tell me which combination (run tests, write docs, add unit tests) to run next.
