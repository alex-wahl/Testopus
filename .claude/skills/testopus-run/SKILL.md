---
name: testopus-run
description: This skill should be used when the user asks to run Testopus tests, produce an Allure or HTML report, filter tests, or lint/format/type-check the framework (e.g. "run the web tests", "give me an allure report", "lint the code"). It knows the real Hatch scripts, the `--alluredir` requirement, and that lint/format/type targets are `core fixtures utils config tests` (no `src/` directory).
version: 0.1.0
---

# Testopus — run tests, reports, and checks

Environments and scripts are managed with **Hatch** (`pyproject.toml`). Local UI runs need
**Chrome + chromedriver** (or use Docker, which bundles headless Chromium). `pytest.ini` sets
`pythonpath=.` so direct `pytest` works too.

## Run tests

```bash
hatch run test:run                 # all tests              (pytest tests)
hatch run ui:web                   # web UI tests           (pytest tests/ui_tests/web)
hatch run api:run                  # API tests              (pytest tests/api_tests)
hatch run test:internal            # framework self-tests   (pytest tests/internal_tests)
hatch run test:run -k search       # forward pytest args, e.g. keyword filter

# Direct pytest (single file / single test):
pytest tests/ui_tests/web/toolshop/test_login.py
pytest tests/ui_tests/web/toolshop/test_login.py::TestLogin::test_login_with_invalid_credentials_shows_error
```

CLI options (registered in `fixtures/cli.py`): `--override` (merge `override.yaml`), `--framework
selenium|playwright|appium` (default `selenium`; `playwright`/`appium` raise `pytest.UsageError`
until implemented), `--ai` (**reserved, not yet wired**), `--config`.

`pytest.ini` sets `--strict-markers` — any unregistered marker is a hard error. Registered markers:
`feature`, `story`, `severity`, `tag`.

## Reports (nothing is captured unless `--alluredir` is passed — these scripts add it)

```bash
hatch run test:allure-report       # pytest --alluredir=reports/allure-results
hatch run test:view-allure         # allure serve reports/allure-results
hatch run test:generate-allure     # allure generate ... --clean && allure open
hatch run test:html-report         # self-contained pytest-html report
```

## Docker (headless Chromium, mirrors CI)

```bash
docker-compose -f docker/docker-compose.yml build
docker-compose -f docker/docker-compose.yml up --remove-orphans
```

## Lint / format / type-check

The Hatch scripts already target the real packages (`core fixtures utils config tests`) — no `src/`
directory exists or is expected. Invoke via Hatch or directly:

```bash
hatch run format       # black core fixtures utils config tests
hatch run lint         # ruff check core fixtures utils config tests
hatch run typecheck    # mypy core fixtures utils
```

Direct invocation (same targets):

```bash
black core fixtures utils config tests
ruff check core fixtures utils config tests
mypy core fixtures utils
```

## After a run

- Report pass/fail/skipped counts and name the failures.
- Point to the report path (`reports/allure-results/`, `reports/html/report.html`).
- If tests are flaky or failing, hand off to the **`flaky-triage`** skill to classify and propose fixes.
- `tests/api_tests/` exists and is fully wired. `hatch run api:run` uses the `[tool.hatch.envs.api]`
  env (features `["api"]`). For a web-only install `pip install -e .` (no extras) is sufficient —
  API tests require `pip install -e .[api]` or the `api` Hatch env.
