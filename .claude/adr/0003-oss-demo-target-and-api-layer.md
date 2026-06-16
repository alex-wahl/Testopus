# ADR-0003: OSS demo target (Toolshop) and API testing layer

- **Status:** Accepted
- **Date:** 2026-06-16
- **Deciders:** tech-lead, qa-automation-engineer, backend-engineer, devops-engineer
- **Related:** ADR-0001 (`0001-driver-seam.md`) — the web driver seam is the analogue of the
  API client seam introduced here. ADR-0002 (`0002-testiny-nl-authoring.md`) — the Testiny
  spec format now targets `app: toolshop`.

## Context

Testopus was open-sourced, but its only suite targeted **GASAG** — a private, credentialed
service that external contributors cannot reach. The suite required `GASAG_USERNAME` /
`GASAG_PASSWORD` repository secrets; without them every CI run and every local setup outside
the original team environment failed immediately. This made the project effectively
non-contributable.

A replacement target needed to be:

1. Publicly accessible, no sign-up required for browsing.
2. Stable enough for a CI regression suite.
3. Cover both a web UI and a REST API in one app, so examples span both testing layers.
4. Expose deterministic, stable locator hooks suitable for demonstrating the locator-priority
   ladder (`data-testid` first).

Separately, the `tests/api_tests/` directory and `hatch run api:run` script had been removed
in a prior cleanup because they pointed at nothing. Re-adding an API layer was blocked on
choosing a target.

## Decision

### (a) Replace the gasag suite with the public Toolshop demo

**[Practice Software Testing "Toolshop"](https://practicesoftwaretesting.com)** is a purpose-built
open-source demo shop. It exposes a web UI and a REST API under a single domain; its Angular
SPA uses `data-test` attributes on interactive elements (the top of the locator-priority
ladder); and it ships a public demo account (`customer@practicesoftwaretesting.com` /
`welcome01`) that can be used in login examples without any secret management.

The gasag Page Objects, test suite, and `GasagConfig` Pydantic model were removed. In their
place:

- `core/pom/web/toolshop/home_page.py` — `HomePage` (`PAGE_URL=""`, locators
  `SEARCH_INPUT`/`SEARCH_SUBMIT`/`SEARCH_RESET`/`PRODUCT_NAME`/`PRODUCT_PRICE`/`SORT` as
  `(By.CSS_SELECTOR, "[data-test='...']")`, action method `search(term)`).
- `core/pom/web/toolshop/login_page.py` — `LoginPage` (`PAGE_URL="auth/login"`,
  `EMAIL_FIELD`/`PASSWORD_FIELD`/`LOGIN_SUBMIT`/`LOGIN_ERROR`, copy constant
  `TEXT_LOGIN_ERROR_KEY_PHRASE="Invalid email or password"`, action method
  `login(email, password)`).
- Web suites `tests/ui_tests/web/toolshop/`: `TestProducts`, `TestSearch`, `TestLogin` —
  class-based, `autouse` fixture reads `config["configuration"]["toolshop"]["web_url"]`.
- `core/config/schema.py`: `GasagConfig` replaced by `ToolshopConfig` (fields: `web_url`,
  `api_url`, `email`, `password`).
- `config/yaml_configs/default.yaml`: a single `toolshop` block with public defaults via
  `${TOOLSHOP_EMAIL:-customer@practicesoftwaretesting.com}` /
  `${TOOLSHOP_PASSWORD:-welcome01}` — these are **not secrets**. Remove any pre-existing
  `GASAG_*` repository secrets from GitHub Settings → Secrets.

### (b) Add an API testing layer

A thin REST client was added as `core/api/client.py`:

- `ApiClient(base_url, *, token=None, headers=None, timeout=30)` with `get`, `post`, `put`,
  `delete` methods returning `requests.Response` without raising on 4xx/5xx status codes.
  Tests assert `response.status_code` directly — this matches how API tests are actually
  written and avoids silently swallowing errors in unexpected-failure paths.
- The client is the API analogue of `SeleniumDriver` behind the `BaseDriver` Protocol seam
  (ADR-0001): a thin, reusable wrapper with no magic.

API fixtures live in a **local** `tests/api_tests/conftest.py` (not registered as a global
plugin in `conftest.py`): `api_client` (unauthenticated), `auth_token` (logs in with the
public demo account, returns bearer token), `authed_client` (pre-authenticated `ApiClient`).
The local conftest means a web-only install (`pip install -e .`) never imports `requests` or
`core.api`.

`requests` was added to a new `[api]` optional extra in `pyproject.toml`. The `test` Hatch
environment now includes `features = ["test", "tools", "api"]` so `hatch run test:run` covers
all three layers. A dedicated `[tool.hatch.envs.api]` environment (features `["api"]`) runs
`hatch run api:run` (`pytest tests/api_tests`) for API-only runs without a browser.

API suites: `tests/api_tests/test_products.py`, `test_categories.py`, `test_auth.py`. A
mocked unit test for `ApiClient` lives in `tests/internal_tests/test_api_client.py`.

### (c) `--import-mode=importlib`

Both `tests/ui_tests/web/toolshop/` and `tests/api_tests/` contain a file named
`test_products.py`. The default pytest import mode (`prepend`) would collide on the module
name. `pytest.ini` adds `--import-mode=importlib`, which uses unique module identifiers and
eliminates the collision. This flag must not be removed while the shared filename exists.

### (d) CI: one Docker job runs all three suites

`docker/Dockerfile` installs `pip install -e .[test,tools,api]`. The `test.yml` CI workflow
runs web + internal + API tests in a single Docker job, producing one unified Allure report.
An `api` dispatch option allows running the API suite in isolation. GASAG repository secrets
(`GASAG_USERNAME`, `GASAG_PASSWORD`) are no longer referenced and should be removed from
GitHub Settings → Secrets.

## Consequences

- External contributors can clone the repo and run `hatch run api:run` (no secrets needed)
  or `hatch run ui:web` (needs Chrome + chromedriver, or Docker) immediately.
- The Toolshop `data-test` hooks are a lived example of the locator-priority ladder mandated
  by CLAUDE.md Conventions and the `testopus-page-object` skill.
- `GasagConfig` is gone; `ToolshopConfig` is the only app-config schema.
- `pytest.ini` carries `--import-mode=importlib` permanently (or until the shared filename
  is resolved).
- `GASAG_USERNAME` / `GASAG_PASSWORD` secrets must be removed from the repository settings
  manually (CI would otherwise warn about unused secrets).

## Rejected alternatives

**Automation Exercise (automationexercise.com)** — web UI only (no matching public API);
ad-heavy and historically unstable.

**SauceDemo (web) + ReqRes (API)** — two separate targets with no thematic connection:
ReqRes is a mock API (canned responses), not a realistic one, and splitting web and API across
two unrelated apps fragments the config and fixtures for no benefit. Toolshop covers both under
one domain.

**A separate native API CI job** — running API tests in a separate CI job would fragment the
Allure report into two partial histories and complicate trend tracking. A single Docker job
covering all suites keeps the Allure trend unified.

**Putting `requests` in `[project].dependencies`** — `requests` is needed only for API tests
and authoring tooling, not for web-only Selenium runs. Keeping it in `[api]` and `[tools]`
extras preserves the minimal web install.
