---
name: testopus-web-test
description: This skill should be used when the user asks to create, scaffold, or add a new web UI test suite/case for Testopus (e.g. "write tests for the checkout page", "add a test suite for X"). It produces a class-based pytest suite matching Testopus's conventions exactly — autouse config fixture, per-test page-object fixture, the `@retry` decorator, `pytest_check` soft assertions, and optional Allure markers.
version: 0.1.0
---

# Testopus — scaffold a web test suite

Use this to add a class-based suite under `tests/ui_tests/web/<app>/test_<name>.py`. The reference
suite is `tests/ui_tests/web/gasag/test_gasag.py`. It pairs with a Page Object (see the
**`testopus-page-object`** skill) — **selectors live in the page object, never in the test**.

## Conventions (must follow)

1. **Class-based suite** `Test<Name>` with class attrs (`BASE_URL = None`, plus any creds) populated
   once by an **autouse** fixture from the session `config`.
2. **Config access**: `config['configuration']['<app>']['<key>']` — `<app>` matches the YAML block in
   `config/yaml_configs/default.yaml`. Never hardcode URLs/credentials in the test.
3. **Per-test page fixture** builds the page object from `driver`:
   `url = f"{self.BASE_URL}/{<Name>Page.PAGE_URL}"`.
4. **`@retry`** wraps every flaky-prone test method:
   `from core.pom.web.base_page import retry` → `@retry(retries=3, delay=2, on_retry=log_retry)`.
   Define `log_retry` at module level (as the reference suite does). Use retry to absorb genuine web
   flakiness — never to paper over a real, reproducible failure.
5. **Soft assertions** via `pytest_check` (`import pytest_check as check`; `check.is_in(...)`,
   `check.equal(...)`) when you want to collect several copy/field checks in one run. Use a plain
   `assert` for a single hard precondition.
6. **Optional Allure markers** — `@pytest.mark.feature/story/severity/tag` are mapped to Allure
   labels by `fixtures/allure.py`. If you use them, register them in `pytest.ini` under `markers =`
   (currently commented out) to avoid unknown-mark warnings. Confirm the exact supported marks in
   `fixtures/allure.py` before using.

## Template

```python
import logging

import pytest
import pytest_check as check

from core.pom.web.base_page import retry
from core.pom.web.shop.checkout_page import CheckoutPage


def log_retry(attempt, exception, *args, **kwargs):
    """Log retry attempts for debugging."""
    logging.warning(f"Retry attempt {attempt + 1} due to: {exception}")


class TestCheckout:
    """Checkout page test suite."""

    BASE_URL = None

    @pytest.fixture(autouse=True)
    def setup_test_suite(self, config):
        if TestCheckout.BASE_URL is None:
            self.BASE_URL = config['configuration']['shop']['web_url']

    @pytest.fixture
    def checkout_page(self, driver):
        url = f"{self.BASE_URL}/{CheckoutPage.PAGE_URL}"
        return CheckoutPage(driver, url=url)

    @retry(retries=3, delay=2, on_retry=log_retry)
    def test_heading_is_shown(self, checkout_page):
        checkout_page.wait_for_element(CheckoutPage.HEADING)
        # Soft assertion: bare check.* call — do NOT wrap in `assert`, which would hard-fail and
        # defeat the collect-all-failures purpose. Mirrors tests/ui_tests/web/gasag/test_gasag.py.
        check.is_in(
            CheckoutPage.TEXT_HEADING,
            checkout_page.get_text(CheckoutPage.HEADING),
            "Checkout heading is not displayed",
        )

    @retry(retries=3, delay=2, on_retry=log_retry)
    def test_promo_code_can_be_applied(self, checkout_page):
        checkout_page.apply_promo_code("WELCOME10")
        # assert on a page-object locator/state, e.g. a discount line becoming visible
        assert checkout_page.is_element_present(CheckoutPage.HEADING)
```

## Steps

1. Ensure the Page Object exists (use **`testopus-page-object`** first if not).
2. Add the `<app>` block to `config/yaml_configs/default.yaml` if new (`web_url`, etc.).
3. Create `tests/ui_tests/web/<app>/test_<name>.py` from the template; one `test_*` per behavior.
4. Run it with the **`testopus-run`** skill (Chrome/chromedriver or Docker required).
