# Testopus

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](pyproject.toml)
[![CI](https://github.com/alex-wahl/Testopus/actions/workflows/test.yml/badge.svg)](https://github.com/alex-wahl/Testopus/actions/workflows/test.yml)

**Testopus** is a Pytest-based UI test automation framework: Selenium drives Chrome through a Page
Object Model, with Allure reporting and a CI pipeline that publishes trend reports to GitHub Pages.
Both web UI tests and REST API tests run against the public **Practice Software Testing "Toolshop"**
demo (https://practicesoftwaretesting.com) — no credentials required for browsing; the login examples
use a freely available public demo account.

> **Status: prototype.** Web UI testing (Selenium/Chrome) and API testing are implemented today.
> Playwright, Appium/mobile, and AI integrations are on the roadmap — declared in dependencies and
> config but **not yet implemented**.

## Quick Start (< 5 min)

**Prerequisites:** Python 3.12+. Running the web UI tests *locally* also needs **Chrome + chromedriver**
(matching versions) — or use the Docker path below, which bundles a headless browser.

```bash
git clone https://github.com/alex-wahl/Testopus.git
cd Testopus
pip install hatch                 # Hatch manages the virtualenv + dependencies for you

hatch run test:internal           # ✓ no browser — confirms your setup works
hatch run api:run                 # REST API tests (no browser needed)
hatch run ui:web                  # web UI tests (Selenium + Chrome)
```

`hatch run test:internal` is the fastest "did it work?" check: framework self-tests, no browser.
`hatch run api:run` exercises the Toolshop REST API — also no browser needed. Once both are green
your setup is good, and `hatch run ui:web` runs the actual web tests.

**No local Chrome? Use Docker** (bundles headless Chromium + chromedriver, runs the whole suite):

```bash
docker-compose -f docker/docker-compose.yml build          # first build is slower
docker-compose -f docker/docker-compose.yml up --remove-orphans
```

## Running tests

Hatch scripts (defined in `pyproject.toml`); anything after the script name is forwarded to pytest:

| Command | Runs |
|---|---|
| `hatch run test:internal` | Framework self-tests (no browser) |
| `hatch run api:run` | API tests — `tests/api_tests` (no browser) |
| `hatch run ui:web` | Web UI tests — `tests/ui_tests/web` |
| `hatch run test:run` | Everything — `tests/` |
| `hatch run test:run -k search` | Forward pytest args, e.g. a keyword filter |

Not using Hatch? `python -m venv .venv && source .venv/bin/activate && pip install -e .[api]`, then
call `pytest` directly (`pytest.ini` sets `pythonpath=.`):

```bash
pytest tests/internal_tests
pytest tests/api_tests
pytest tests/ui_tests/web/toolshop/test_login.py
```

Inside Docker, pass a **path** (the container entrypoint is already `pytest`):

```bash
docker-compose -f docker/docker-compose.yml run --rm testopus tests/internal_tests
```

## Reports

```bash
hatch run test:allure-report   # run tests + collect Allure results -> reports/allure-results/
hatch run test:view-allure     # open them in the Allure viewer (needs the Allure CLI)
hatch run test:html-report     # self-contained HTML -> reports/html/report.html
```

Allure captures nothing unless `--alluredir` is passed — the scripts above add it. On failure, a
screenshot and the run environment are attached automatically (`fixtures/allure.py`). The latest report
is published to **<https://alex-wahl.github.io/Testopus>**. CI/pipeline details:
[`ci/README.md`](ci/README.md) and [`docs/ci/`](docs/ci/).

## Configuration

Config lives in `config/yaml_configs/default.yaml`; tests read nested keys, e.g.
`config['configuration']['toolshop']['web_url']`. Pass `--override` to merge an `override.yaml`
on top of the defaults. The Toolshop target uses a **public demo account**
(`customer@practicesoftwaretesting.com` / `welcome01`), defaulted in the YAML via
`${TOOLSHOP_EMAIL:-...}` / `${TOOLSHOP_PASSWORD:-...}` — no repository secrets are needed to run
the suite. The `--framework selenium|playwright|appium` flag is wired — `playwright`/`appium` fail
loudly until their backends are built. The `--ai` flag is reserved but not yet active.

> ⚠️ Never commit `.env` or real credentials. `override.yaml` is gitignored for the same reason.
> Allure attaches failure screenshots — sensitive fields are scrubbed before capture.

## Project layout

```
core/      # config loader · driver seam (core/drivers/) · POM (core/pom/web) · API client (core/api/)
fixtures/  # pytest plugins: cli, setup (driver factory), allure
config/    # YAML configs (config/yaml_configs/default.yaml); public demo account via env fallbacks
tests/     # ui_tests/web (Selenium) · api_tests (REST) · internal_tests (framework self-tests)
utils/     # path helpers, redact, CI env
ci/        # CI pipeline scripts + templates (ci/scripts)
docs/      # project documentation (docs/ci/ — CI workflow & Allure customization)
docker/    # Dockerfile + docker-compose.yml (headless Chromium)
```

## Development

```bash
hatch run format      # Black
hatch run lint        # Ruff
hatch run typecheck   # MyPy
```

Conventions for writing page objects and tests — POM locators, the `@retry` decorator for genuinely
flaky web steps, `pytest_check` soft assertions — live in [`CLAUDE.md`](CLAUDE.md). Reference
suites: `tests/ui_tests/web/toolshop/test_login.py` (web) and `tests/api_tests/test_auth.py`
(API).

### Web + API examples (Toolshop)

The Toolshop suite covers both layers:

- **Web** (`tests/ui_tests/web/toolshop/`): `TestProducts` (product listing), `TestSearch`
  (search submit/reset), `TestLogin` (invalid credentials error, valid login redirect). Pages live
  in `core/pom/web/toolshop/`: `HomePage` (`search(term)`) and `LoginPage` (`login(email, password)`).
  All locators use stable `data-test` hooks.
- **API** (`tests/api_tests/`): `test_products.py` (list/filter), `test_categories.py` (listing),
  `test_auth.py` (login/token). Fixtures (`api_client`, `auth_token`, `authed_client`) live in
  `tests/api_tests/conftest.py` (local, not a global plugin).

```bash
hatch run ui:web              # all Toolshop web suites
hatch run api:run             # all Toolshop API suites
```

### Generate tests from Testiny (experimental)

Test cases written in [Testiny](https://app.testiny.io) can be pulled into local spec files and
then turned into committed pytest suites via Claude Code. The tool requires the `[tools]` extra
(`requests`):

```bash
pip install -e .[tools]
# Set TESTINY_API_KEY in .env (copy .env.example)

python -m tools.testiny pull --case-id 1          # writes specs/toolshop/tc-1-login.md
# Then invoke the testopus-nl-test skill to generate the pytest suite,
# followed by the mandatory code-reviewer + testopus-run gate before committing.
```

The LLM is in the authoring loop only — the committed output is plain Pytest with no AI dependency
at runtime. See [`docs/testiny/workflow.md`](docs/testiny/workflow.md) for the full end-to-end guide.

## Troubleshooting

- **ChromeDriver / Chrome mismatch** — match their versions, or set `CHROMEDRIVER_PATH`. (Docker avoids
  this entirely — it bundles both.)
- **Force headless** — set `DOCKER_ENV=true` (Docker/CI do this automatically). Env vars honored:
  `DOCKER_ENV`, `CHROME_BIN`, `CHROMEDRIVER_PATH`.
- **Empty Allure report** — make sure `--alluredir` is passed (the `test:*` report scripts do); install
  the Allure CLI to view results (`brew install allure` or `npm install -g allure-commandline`).

## Contributing

Contributions are welcome — please open a Pull Request.

## License

MIT — see [LICENSE](LICENSE).
