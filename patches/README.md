# Patches for drought-monitoring-system

`drought-monitoring-system` (Backend Team's repo, github.com/ferhadedika/drought-monitoring-system)
is gitignored here and cloned separately -- see `.gitignore` and
[docs/environment-setup.md](../docs/environment-setup.md). This folder holds
patches against that repo that are useful to share back with the Backend
Team, without pushing directly to their repository.

## drought-monitoring-system-python310-compat.patch

Fixes an `ImportError: cannot import name 'UTC' from 'datetime'` that breaks
the dashboard and two backend test files on Python 3.10 (`datetime.UTC` was
only added in Python 3.11). Also fixes
`backend/tests/test_serial_bridge.py` failing with
`ModuleNotFoundError: No module named 'scripts'` by adding a
`backend/tests/conftest.py` that puts the repo root on `sys.path`.

Apply from inside a `drought-monitoring-system` checkout:

```bash
git apply /path/to/pbl2026-summer/patches/drought-monitoring-system-python310-compat.patch
```

Verified with `pytest` on Python 3.10.11: 23 passed in `backend/`, 4 passed
in `dashboard/`, and the Streamlit app (`streamlit run app.py`) loads all
four pages without a traceback.

## drought-monitoring-system-remove-stale-supabase-labels.patch

The local setup stores data in JSON Lines files instead of Supabase (see
the docstring in `backend/app/database/monitoring_repository.py`), but the
dashboard UI and some backend error messages still said "Supabase" (e.g.
the source pill at the top of every page read "Supabase + Gemini live",
and the sidebar detail line read "Sensors: Supabase · Weather: Supabase ·
Gemini: Supabase"). This patch replaces those labels with accurate
"Live"/"Backend" wording so the running site matches what it actually
does, without changing behavior or layout.

Apply the same way:

```bash
git apply /path/to/pbl2026-summer/patches/drought-monitoring-system-remove-stale-supabase-labels.patch
```

Verified with `pytest` on Python 3.10.11 (23 passed in `backend/`, 4 passed
in `dashboard/`) and by restarting both the FastAPI backend and the
Streamlit dashboard and loading all four pages -- no tracebacks, no
remaining "Supabase" text in the rendered UI.
