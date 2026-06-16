# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Testopus is a Pytest-based **UI test automation framework**: Selenium/Chrome driving web pages via a
Page Object Model, with Allure reporting and a CI pipeline that publishes trend reports to GitHub
Pages. Only Selenium/Chrome web tests are implemented today. Playwright and Appium are declared in
the `[frameworks]` optional extra and backed by a `core/drivers/` seam — the Protocol is in place,
but the concrete backends are not yet built. API testing and AI integrations are roadmap items only.

Python `>=3.12`. Local UI runs need Chrome + chromedriver (or use Docker, which bundles headless Chromium).

## Commands

Environments and scripts are managed with **Hatch** (`pyproject.toml`); there is no Makefile/tox/nox.

```bash
pip install hatch                 # one-time; Hatch manages venvs + deps per environment
# Alternative without Hatch: python -m venv .venv && source .venv/bin/activate && pip install -e .
```

Run tests (the `{args}` placeholder forwards extra pytest flags):

```bash
hatch run test:run                # all tests            (pytest tests)
hatch run ui:web                  # web UI tests         (pytest tests/ui_tests/web)
hatch run test:internal           # framework self-tests (pytest tests/internal_tests)
hatch run test:run -k email_field # forward pytest args, e.g. keyword filter

# Direct pytest works too (pytest.ini sets pythonpath=.):
pytest tests/ui_tests/web/gasag/test_gasag.py                                   # single file
pytest tests/ui_tests/web/gasag/test_gasag.py::TestGasag::test_email_field_is_accepting_email_addresses  # single test
```

CLI options (registered in `fixtures/cli.py`): `--override` (merge `override.yaml`), `--framework
selenium|playwright|appium` (default `selenium`; `playwright`/`appium` raise `pytest.UsageError`
until implemented), `--ai` (reserved, not yet wired), `--config`.

Allure / HTML reports (nothing is captured unless `--alluredir` is passed — these scripts add it):

```bash
hatch run test:allure-report      # pytest --alluredir=reports/allure-results
hatch run test:view-allure        # allure serve reports/allure-results
hatch run test:generate-allure    # allure generate ... --clean && allure open
hatch run test:html-report        # self-contained pytest-html report
```

Docker (headless Chromium, mirrors CI):

```bash
docker-compose -f docker/docker-compose.yml build
docker-compose -f docker/docker-compose.yml up --remove-orphans
```

## Architecture

**Fixture loading.** `conftest.py` registers three modules as pytest plugins via `pytest_plugins`
(so their fixtures/hooks are global, no imports in tests): `fixtures.cli`, `fixtures.setup`,
`fixtures.allure`.

**Config flow.** The session-scoped `config` fixture (`fixtures/cli.py`) calls
`core/config/config_loader.py::load_config_from_cli`, which loads `config/yaml_configs/default.yaml`
and, when `--override` is set, recursively merges `override.yaml` over it (`merge_configs`). The
assembled dict is then passed through `_validate_config()`, which runs Pydantic v2
(`core/config/schema.py`: `GasagConfig` / `Configuration` / `RootConfig`, all `extra="allow"`) and
raises `ConfigError` on a bad shape — fail-fast before any test touches the config. Returns the
same dict, so all dict-based consumers are unchanged. Paths resolve through `utils/helpers.py`
(`get_project_root`, `get_config_path`). Tests read nested keys, e.g.
`config['configuration']['gasag']['web_url']`.

**Driver.** The function-scoped `driver` fixture (`fixtures/setup.py`) calls
`core.drivers.factory.create_driver(framework)` and `quit()`s it after each test. `create_driver`
builds a `SeleniumDriver` wrapping Chrome (headless when `DOCKER_ENV=true`, honors `CHROME_BIN` /
`CHROMEDRIVER_PATH`). `playwright` / `appium` raise `NotImplementedError` (surfaced as
`pytest.UsageError`). The driver seam is defined in `core/drivers/`: `BaseDriver` and
`ElementHandle` are `@runtime_checkable` Protocols in `base.py`; `SeleniumDriver` implements them in
`selenium_driver.py`; see ADR-0001 (`.claude/adr/0001-driver-seam.md`).

**Page Object Model** (`core/pom/web/`). Every page extends `BasePage` (`base_page.py`), whose
`__init__(driver: BaseDriver, url)` navigates to the URL on construction and which provides ~50
wait/interaction helpers (`DEFAULT_TIMEOUT=3`, `PAGE_LOAD_TIMEOUT=10`). Page subclasses (e.g.
`gasag/login_page.py` `LoginPage`) define **locators as class-constant tuples** `(By.X, "selector")`,
**expected copy as ALL_CAPS string constants**, and **snake_case action methods** (e.g. `login()`).
Never hardcode selectors in tests — reference the page-class constants.

**Test conventions** (see `tests/ui_tests/web/gasag/test_gasag.py`):
- Class-based suites (`TestGasag`) with `test_*` methods; a class-scoped `autouse` fixture copies
  `config` values into class attributes, and a per-test fixture builds the page object from `driver`.
- Web flakiness is handled with the module-level `retry` decorator (defined in `base_page.py`):
  `from core.pom.web.base_page import retry` → `@retry(retries=3, delay=2, on_retry=log_retry)`,
  where `log_retry(attempt, exception, *args, **kwargs)` logs each attempt.
- Soft assertions via `pytest_check` (`import pytest_check as check; check.is_in(...)`) to collect
  multiple failures in one run.

**Allure hooks** (`fixtures/allure.py`, hooks not fixtures): creates `reports/` subdirs, captures a
screenshot on test failure and attaches it to Allure, writes `environment.properties` at session end
(browser/OS/Python/git branch, timezone `Europe/Berlin`), and maps `@pytest.mark.feature/story/
severity/tag` plus the test docstring into Allure metadata.

**CI / published reports.** `.github/workflows/test.yml` runs the suite in Docker, builds the Allure
report, then post-processes it with `ci/scripts/customize_allure_report.py` (branch labeling,
trend/history preservation, date formatting, 404 fixes) and deploys to the `reporting` branch →
GitHub Pages at https://alex-wahl.github.io/Testopus. Background: `docs/ci/github-actions.md`,
`docs/ci/allure_customization_flow.md`.

## Repo realities (avoid these traps)

- **`tests/api_tests/` does not exist yet.** The `api` Hatch env/script was removed — there is
  nothing to execute. Re-add it (with an `[api]` extra) when API testing actually lands.
- `pytest.ini` sets `addopts = --strict-markers` and registers `feature`, `story`, `severity`, `tag`
  markers for Allure. An unregistered marker is an error. Pass `--alluredir` explicitly (or via a
  `test:*-report` script) to get Allure output — it is intentionally not in `addopts`.

---

## Development methodology — TDD (proportional, going forward)

Apply **Red → Green → Refactor** to **pure logic** — `core/config/config_loader.py`
(`merge_configs`), `utils/helpers.py`, `core/drivers/` factory and Protocol contracts,
and AI/telemetry/triage helpers: write a failing self-test in `tests/internal_tests/` first, make it
pass with the minimum change, then refactor while green. **Don't** force TDD on thin
Selenium-delegating `BasePage` wrappers — testing those tests Selenium, not us. UI **product** tests
are the framework's output and follow the POM + test conventions below. (Existing code predates this
standard; apply it to new logic and whenever you touch a module.)

## Development principles (MANDATORY)

- **SOLID**, **DRY**, **KISS**. If you see a design that violates them, improve it incrementally —
  each change cleaner than the last — without breaking business logic/behavior.
- **Don't assume; surface tradeoffs.** Don't hide confusion.
- **Minimum code that solves the problem.** Nothing speculative.
- **Touch only what you must.** Clean up only your own mess.
- **Define success criteria; loop until verified.**

## Before push — MANDATORY gate (in order)

After a change is implemented, run these in order; **do not push until all pass.**

1. **Code review.** Delegate the diff to the dedicated **`code-reviewer`** agent
   (`.claude/agents/code-reviewer.md`) — it is **pinned to Opus 4.8**, and you **always invoke it at
   effort `max`** (run with the session at `/effort max` so the subagent inherits it, or pass
   `effort: max` when launching it). Act on its findings; a change with open **Blockers** is not
   push-ready. The `core/` + `main` bar is strict; docs/skills/config edits get a lighter-scope review
   but still go through `code-reviewer`. (The `/code-review` plugin remains available as a manual
   alternative.)
2. **Documentation update.** After review passes, delegate to the **`writer`** agent
   (`.claude/agents/writer.md`) to bring every affected doc in sync with the change — `README.md`,
   `CLAUDE.md`, `docs/` (incl. `docs/ci/`), ADRs, and any new skill/agent/command registration. **A change
   is not push-ready until its docs match reality.** (`writer` runs on `sonnet`, effort `medium` —
   `high` for large/structural docs.)
3. **Push** only after steps 1–2 are complete.

## Official documentation (lookup before new/uncertain API work)

Before writing or changing code against a **new or uncertain** API in **Selenium, Pytest,
pytest-check, Allure, Playwright, Appium, Hatch, or the Anthropic SDK**, fetch the official docs and
verify the current API surface — don't rely on cached knowledge (pinned versions in `pyproject.toml`
may differ). This is for unfamiliar or version-sensitive calls, not every edit. See the
**`docs-first`** skill (`.claude/skills/docs-first/`) for the curated link list and procedure. Quick links: Selenium <https://www.selenium.dev/documentation/> · Pytest
<https://docs.pytest.org/en/stable/> · Allure <https://allurereport.org/docs/> · Playwright (Python)
<https://playwright.dev/python/docs/intro> · Appium <https://appium.io/docs/en/latest/> · Hatch
<https://hatch.pypa.io/latest/> · Anthropic/Claude <https://docs.claude.com/>.

## Safety — credentials & irreversible actions (MANDATORY)

- **Never commit real secrets.** `config/yaml_configs/default.yaml` uses `${GASAG_USERNAME}` /
  `${GASAG_PASSWORD}` placeholders; `core/config/config_loader.py` resolves them from the environment
  via `python-dotenv` (see `.env.example`). In CI, inject them as repository secrets. `override.yaml`
  is gitignored — never commit it. **Never echo credentials into logs, reports, or screenshots**
  (Allure attaches failure screenshots — scrub sensitive fields).
- **No irreversible or outward-facing actions without explicit approval.** Tests or scripts that
  perform real account signups, password changes, payments, emails, or third-party OAuth against
  **live** sites/accounts require the owner's case-by-case go-ahead. Read-only checks and runs
  against disposable/test accounts are always fine.

## Conventions (explicit & enforceable)

- **Locators** live only as page-class constant tuples `(By.X, "selector")` — never inline a
  selector in a test. Pick the highest-priority stable hook — **`data-testid` → ARIA role/name →
  semantic CSS → stable `id`/`name` → XPath (last resort)**; never positional/absolute XPath or
  compound multi-class `By.CLASS_NAME` chains (they rot on re-render, CSS-in-JS, and i18n). The
  `testopus-page-object` skill enforces this ladder.
- **Expected copy** is ALL_CAPS `TEXT_*` constants on the page class; assert against those.
- **Action methods** are snake_case and composed from BasePage helpers; don't call the raw driver
  when a helper exists.
- **`@retry`** (`from core.pom.web.base_page import retry`) absorbs *genuine* web flakiness only —
  never to mask a reproducible failure. Default `exceptions=(WebDriverException,)` — do not widen to
  `Exception`, which would swallow `AssertionError`. Each retry emits a structured event to
  `reports/retry_events.jsonl` (fail-open).
- **Soft assertions** via `pytest_check` to collect multiple checks per run.
- **Allure** captures nothing unless `--alluredir` is passed; `pytest.ini` registers
  `feature/story/severity/tag` and enforces `--strict-markers` — any unregistered marker is an error.
- **Lint/format/type** target `core fixtures utils config tests` — not the nonexistent `src/`.

## Dependency currency (keep the project current)

- **Single source of truth:** all dependencies live in `pyproject.toml` — runtime deps in
  `[project].dependencies`, dev tools in `[project.optional-dependencies].dev`, test-only extras in
  `.test`, future framework backends (Playwright/Appium) in `.frameworks`. Hatch envs pull these via
  `features` (no per-env duplication). `docker/Dockerfile` installs with `pip install -e .[test]` —
  never hand-maintain a second dependency list.
- **Stay current automatically:** `.github/dependabot.yml` watches `pip` (pyproject), `github-actions`,
  and the `docker` base image weekly. Minor/patch Python bumps batch into one PR; each **major** bump
  opens its own PR for individual review. The CI test job validates every Dependabot PR.
- **Version style:** `>=` floors (no upper caps); Dependabot raises the floors. Don't reintroduce
  exact `==` pins or a hand-written `requirements.txt`.
- **When bumping (or reviewing a Dependabot PR):** run `pytest --collect-only` (loads every plugin —
  surfaces pytest/allure/plugin incompatibilities cheaply), then the suite, then the linters;
  run the `code-reviewer` agent (Opus 4.8, effort `max`) for major bumps. Watch the historically breaking jumps: pytest (8→9 fixture
  visibility), pytest-html (3→4), pydantic (validator strictness), mypy, isort.
- **Don't re-add unused/abandoned deps:** `pydantic-ai`, `langchain`, `pyviztest`, `pyscreenshot`
  were removed — add a dependency only when code actually imports it.
- **License compatibility:** the project is MIT (`LICENSE`). New deps must be permissive — MIT,
  Apache-2.0, BSD, ISC, PSF, or non-propagating MPL-2.0 are fine. No GPL/LGPL/AGPL copyleft.

## Toward an AI-Driven QA Framework (direction)

- The `--framework` flag (`fixtures/cli.py`) is **wired**: `selenium` builds a `SeleniumDriver` via
  `core/drivers/factory.create_driver`; `playwright`/`appium` fail loudly with `pytest.UsageError`
  until their backends are built. The `--ai` flag is still parsed but inert (reserved for AI feature
  gates; roadmap).
- AI seams reuse existing signal: **flaky/failure triage** off Allure JSON + 90-day history + failure
  screenshots; **locator self-healing** off failure screenshots/DOM; **test generation** from page
  objects. AI **augments** QA and never owns the test verdict; the deterministic test path must run
  with AI off (fail-open).
- For AI code, add the **official `anthropic` SDK** + latest Claude models (Opus 4.8 / Sonnet 4.6 /
  Haiku 4.5) when the first AI feature lands. The unused `pydantic-ai`, `langchain`, `pyviztest`, and
  (obsolete) `pyscreenshot` deps were removed in the dependency modernization. Keep AI/ML/data as
  **optional layers that depend on core, never the reverse.** This invariant is statically enforced
  by `tests/internal_tests/test_layering.py`, which AST-scans every module under `core/` and fails
  if it imports `core.ai`, `core.ml`, `core.telemetry`, `core.data`, or `anthropic`.

## `.claude/` team & tooling

This repo ships a Claude Code toolkit under `.claude/`:
- **Agent team** (`.claude/agents/`): a senior council — `tech-lead` plus `qa-automation-engineer`,
  `backend-engineer`, `frontend-engineer`, `devops-engineer`, `ai-engineer`, `ml-engineer`,
  `data-engineer`, `architect` (read-only advisors for design decisions).
- **`code-reviewer` agent** (`.claude/agents/code-reviewer.md`): the mandatory review gate — pinned
  to Opus 4.8, invoked at effort `max` (step 1 of "Before push"). Read-only; reports findings.
- **`writer` agent** (`.claude/agents/writer.md`): creates and maintains documentation; the mandatory
  post-review, pre-push doc-sync step (see "Before push" above). Runs on `sonnet`.
- **`/team-council`** (`.claude/commands/`): convenes the council on a topic and writes a decision
  doc to `.claude/council/`. Uses the experimental agent-teams feature when enabled
  (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in `.claude/settings.json`), else subagent fan-out.
- **`/project-audit`** (`.claude/commands/`): convenes the council to audit the project —
  antipatterns (+ action items), an improvement/feature roadmap, and best-practices adoption —
  writing three docs to `docs/audit/`. Same agent-teams/fan-out mode detection as `/team-council`.
- **Skills** (`.claude/skills/`): `testopus-page-object`, `testopus-web-test`, `testopus-run`,
  `flaky-triage`, `docs-first`.
- **ADRs** (`.claude/adr/`): architecture decision records. ADR-0001 (`0001-driver-seam.md`) records
  the `BaseDriver`/`ElementHandle` Protocol seam and driver factory.
