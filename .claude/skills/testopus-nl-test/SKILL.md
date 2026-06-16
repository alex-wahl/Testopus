---
name: testopus-nl-test
description: This skill should be used when the user asks to turn a human-language test specification — a Testiny case pulled into a `specs/<app>/*.md` file — into a Testopus pytest suite (e.g. "generate the test for spec tc-1", "build the pytest from this Testiny case", "scaffold tests from the specs"). It reads the spec AND the referenced Page Object, grounds every locator/method/TEXT_* constant on real code (never invents selectors), and composes the testopus-page-object + testopus-web-test skills.
version: 0.1.0
---

# Testopus — generate a pytest suite from a human-language spec

Turn a `specs/<app>/tc-*.md` spec (a test case described in human language, usually pulled
from Testiny with `python -m tools.testiny pull …`) into a class-based pytest suite under
`tests/ui_tests/web/<app>/`. The reference suite is `tests/ui_tests/web/gasag/test_gasag.py`;
the reference grounding source is `core/pom/web/gasag/login_page.py`.

**The model is in the *authoring* loop only.** The output is plain, committed pytest that runs
deterministically forever (Selenium drives the browser, not an LLM). This matches the Testopus
invariant: *AI augments QA and never owns the test verdict; the deterministic path runs with AI
off.* This skill does **not** push results back to Testiny, does **not** add the `anthropic`
SDK, and does **not** execute anything agentically at test time.

## Inputs

1. A spec file `specs/<app>/tc-<id>-*.md` — YAML front-matter (`testiny_id`, `app`, `page`,
   `severity`, …) + a human-language body (`## Precondition`, `## Steps`, `## Expected Result`).
2. The Page Object it grounds on: `core/pom/web/<app>/<page>_page.py`, resolved from the
   `app` + `page` front-matter (e.g. `app: gasag`, `page: login` → `LoginPage`).

## Grounding discipline (the core rule — do this first)

1. **Read the Page Object before writing anything.** Build the allowed vocabulary: the locator
   constants (`(By.X, "…")` tuples), the `TEXT_*` copy constants, the page-URL constant name,
   and the snake_case action methods that **actually exist** in that file.
2. **Reference only symbols that exist.** Every `LoginPage.LOCATOR`, `LoginPage.TEXT_*`, and
   `page.method()` in the generated test must resolve to a real attribute/method. **Never invent
   a selector, never guess a method name, never inline a raw selector in the test** (CLAUDE.md
   hard rule — selectors live only on the page class).
3. **If the spec needs something the page lacks**, stop — do not fabricate. Either:
   - add the missing locator / `TEXT_*` / action method via the **`testopus-page-object`** skill
     (verifying any new Selenium API through **`docs-first`**), then continue; or
   - if you cannot (e.g. the real selector is unknown), emit the test method with a clear
     `# BLOCKED: needs LoginPage.<X>` marker and call it out for the human reviewer.
4. **Copy assertions** use the page's `TEXT_*` constants and the "stable key phrase, not the full
   localized sentence" convention (e.g. `LoginPage.TEXT_ERROR_KEY_PHRASE`).

## Compose, don't duplicate (DRY)

This skill orchestrates the two existing skills — it adds only the spec→test mapping, grounding,
and provenance:

- **Page Object layer** → **`testopus-page-object`** owns locator-ladder / `TEXT_*` / snake_case
  rules. Use it to create or extend the page when the spec needs a missing hook.
- **Test scaffold** → follow **`testopus-web-test`** exactly: class-based `Test<Name>` suite, an
  `autouse` config fixture, a per-test page fixture, `@retry` from `core.pom.web.base_page`,
  `pytest_check` soft assertions, and the registered Allure markers (`feature/story/severity/tag`).

## Spec → test mapping

| Spec | Test |
|---|---|
| `## Steps` | ordered page-object **action calls + waits** |
| `## Expected Result` | assertions — `assert` for the one hard outcome; `check.*` to collect several copy/field checks |
| `severity` front-matter | `@pytest.mark.severity("<severity>")` |
| `app` / `title` | `@pytest.mark.feature(...)` / `@pytest.mark.story(...)` (registered marks only) |
| each distinct expected behavior | its own `test_*` method |

## Provenance (required)

Every generated suite carries a docstring linking it back to the source, so a committed test is
traceable to its spec and Testiny case:

```python
class TestLoginInvalidCredentials:
    """Generated from Testiny case 1 (spec: specs/gasag/tc-1-login.md).
    Regenerate via `python -m tools.testiny pull` + the testopus-nl-test skill."""
```

## Generated shape (mirrors `tests/ui_tests/web/gasag/test_gasag.py`)

```python
import logging

import pytest

from core.pom.web.base_page import retry
from core.pom.web.gasag.login_page import LoginPage


def log_retry(attempt, exception, *args, **kwargs):
    logging.warning(f"Retry attempt {attempt + 1} due to: {str(exception)}")


@pytest.mark.feature("GASAG Login")
class TestLoginInvalidCredentials:
    """Generated from Testiny case 1 (spec: specs/gasag/tc-1-login.md)."""

    BASE_URL = None
    USERNAME = None
    PASSWORD = None

    @pytest.fixture(autouse=True)
    def setup_test_suite(self, config):
        if TestLoginInvalidCredentials.BASE_URL is None:
            self.BASE_URL = config["configuration"]["gasag"]["web_url"]
            self.USERNAME = config["configuration"]["gasag"]["username"]
            self.PASSWORD = config["configuration"]["gasag"]["password"]

    @pytest.fixture
    def login_page(self, driver):
        url = f"{self.BASE_URL}/{LoginPage.LOGIN_PAGE_URL}"
        return LoginPage(driver, url=url)

    @pytest.mark.severity("critical")
    @pytest.mark.story("Authentication")
    @retry(retries=3, delay=2, on_retry=log_retry)
    def test_login_rejects_invalid_credentials(self, login_page):
        # Steps: enter non-matching credentials and submit (LoginPage.login exists).
        login_page.login(self.USERNAME, self.PASSWORD)
        # Expected Result: the "no matching login" key phrase appears (real TEXT_* constant).
        assert login_page.wait_for_text_present(
            LoginPage.ERROR_MESSAGE, LoginPage.TEXT_ERROR_KEY_PHRASE
        )
```

## Steps

1. Read the spec front-matter; resolve `<app>`/`<page>` to `core/pom/web/<app>/<page>_page.py`.
2. **Read that Page Object** and build the allowed-symbol vocabulary (grounding rule above).
3. If the spec needs a missing hook, add it via **`testopus-page-object`** first (or mark
   `# BLOCKED`).
4. Generate `tests/ui_tests/web/<app>/test_<name>.py` from the **`testopus-web-test`** template,
   mapping Steps→actions and Expected Result→assertions, with the provenance docstring.
5. **Do not commit yet.** Hand the change to the mandatory gate, in order (CLAUDE.md "Before push"):
   the **`code-reviewer`** agent (Opus 4.8, effort `max`) → human review → run it with the
   **`testopus-run`** skill (`pytest --collect-only` first to catch marker/import errors cheaply,
   then `hatch run ui:web`). The run/review gate is what makes grounding enforceable — a fabricated
   `LoginPage.<X>` fails collection.

## Out of scope (future follow-ups)

Pushing test *results* back to Testiny (TestRun API); an `anthropic`-SDK generation pipeline;
runtime/agentic execution or locator self-healing. See `.claude/adr/0002-testiny-nl-authoring.md`.
