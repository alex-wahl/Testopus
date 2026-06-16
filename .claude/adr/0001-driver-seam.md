# ADR-0001: Driver-factory seam (`BaseDriver` / `ElementHandle`)

- **Status:** Accepted
- **Date:** 2026-06-16
- **Deciders:** `/project-audit` council (architect, backend-engineer, qa-automation-engineer,
  frontend-engineer) + lead
- **Fixes:** antipatterns AP-08 (driver hardcoded, no `core/drivers/` seam), AP-11 (inert
  `--framework`), and folds in AP-07/AP-10/AP-22 in `BasePage`.

## Context

Testopus hardcoded `webdriver.Chrome` in the `driver` fixture (`fixtures/setup.py`) and `BasePage`
was typed against Selenium's `WebDriver`/`WebElement`. The `--framework selenium|playwright` flag was
parsed but never read, so it silently ran Selenium. This violated DIP/OCP — adding a framework meant
editing the fixture and forking every page object — and blocked the Playwright/Appium roadmap and
mockable AI layers.

## Decision

Introduce `core/drivers/`:

- **`base.py`** — `@runtime_checkable` `BaseDriver` and `ElementHandle` Protocols covering the common
  automation path: navigate, find, the `wait_for_*` family, interact, screenshot, url, alert.
- **`selenium_driver.py`** — `SeleniumDriver` / `SeleniumElement` implementing the Protocols over
  `webdriver.Chrome`. Waits use `WebDriverWait(..., ignored_exceptions=(StaleElementReferenceException,))`,
  replacing the previous hand-rolled `time.sleep` poll loops.
- **`factory.py`** — `create_driver(framework)`: `selenium` builds Chrome (logic moved out of the
  fixture); `playwright`/`appium` raise `NotImplementedError`. The `driver` fixture surfaces that as a
  `pytest.UsageError`, so an unsupported `--framework` now fails loudly.

`BasePage.__init__` takes a `BaseDriver`. `execute_script` and `driver.raw` are explicit
**Selenium-only escape hatches** for the not-yet-abstracted long tail (`ActionChains`, `Select`,
alerts). `BasePage`'s public API is unchanged — only internals were rewritten — so page objects and
tests are unaffected.

## Consequences

- `--framework` is meaningful; a Playwright/Appium backend can be added behind the Protocol without
  forking page objects, and AI layers can mock `BaseDriver`.
- The deterministic Selenium path is preserved. **The gasag UI suite (`hatch run ui:web`) is the
  regression gate** and must pass in CI (requires a live browser + the target site).
- `js_input` now passes its value as a bound script argument (no f-string injection), the timeout
  constant is the single source of truth, and `WebDriverWait` owns polling.

## Rejected alternatives

- **Abstract all ~50 `BasePage` helpers immediately** — too large/risky in one step; the common path
  plus a documented escape hatch is the KISS scope.
- **Keep a raw `WebDriver` and branch on framework inside the fixture** — violates OCP and leaks
  Selenium throughout the page-object layer.
