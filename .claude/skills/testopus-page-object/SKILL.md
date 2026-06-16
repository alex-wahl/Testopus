---
name: testopus-page-object
description: This skill should be used when the user asks to create, scaffold, or add a new Page Object / page class for Testopus's Selenium web tests (e.g. "add a page object for the checkout page", "create a POM class for X"). It produces a BasePage subclass that matches Testopus's conventions exactly — locators as class-constant tuples, ALL_CAPS expected-copy constants, snake_case action methods built from BasePage helpers.
version: 0.1.0
---

# Testopus — scaffold a Page Object

Use this to add a new page class under `core/pom/web/<app>/<name>_page.py`. Every page **extends
`BasePage`** (`core/pom/web/base_page.py`), whose `__init__(driver, url)` navigates to `url` on
construction and provides ~40 wait/interaction helpers. The reference page is
`core/pom/web/toolshop/login_page.py`.

## Conventions (must follow)

1. **Locators** are class-constant tuples `(By.X, "selector")` — e.g. `EMAIL_FIELD = (By.ID, "signInName")`.
   **Never put selectors in test files** — tests reference these constants only.
2. **Expected copy** is ALL_CAPS string constants (`TEXT_*`), or a list of `TEXT_*_KEY_PHRASES` for
   multi-phrase blocks. Tests assert against these constants, never inline literals.
3. **A URL constant** (e.g. `PAGE_URL = "relative/path"`) — the relative path appended to the app's
   base URL by the test fixture. (The shipped `LoginPage` predates this and names it
   `LOGIN_PAGE_URL`; pick a clear constant name — the test fixture references
   `<PageClass>.<THAT_CONSTANT>`.)
4. **Action methods** are snake_case and built from BasePage helpers — never call the raw Selenium
   driver directly when a helper exists.
5. **Locator priority ladder** — pick the highest available: `data-testid` → ARIA role/name →
   semantic CSS → `id` → XPath (last resort). Avoid brittle dynamic ids (e.g. `dummyGoogleBtn`),
   multi-class `By.CLASS_NAME` selectors, and absolute/positional XPath — they rot on re-render,
   CSS-in-JS, and i18n copy changes.

## BasePage helpers to reuse (don't reinvent)

Waits: `wait_for_element`, `wait_for_element_visible`, `wait_for_element_clickable`,
`wait_for_text_present`, `wait_for_element_to_disappear`, `wait_until_page_is_fully_loaded`,
`wait_for_url_change`, `wait_for_url_contains`. Interactions: `click`/`safe_click`,
`fill_text`/`safe_input`, `check_checkbox`, `select_dropdown_option`, `hover`, `drag_and_drop`,
`double_click`. Reads: `get_text`, `get_input_value`, `get_attribute`, `get_current_url`,
`get_title`, `is_element_present`, `is_element_enabled`, `is_element_selected`. Escape hatches:
`find_element`, `execute_script`, `take_screenshot`.

## Template

```python
from selenium.webdriver.common.by import By

from core.pom.web.base_page import BasePage


class CheckoutPage(BasePage):
    """Checkout page of <app>."""

    # URLs — relative path appended to the app base_url by the test fixture
    PAGE_URL = "shop/checkout"

    # Expected copy — ALL_CAPS constants; assert against these, never inline literals
    TEXT_HEADING = "Your order"
    TEXT_EMPTY_CART = "Your cart is empty"

    # Locators — class-constant (By, "selector") tuples; never inline these in tests
    HEADING = (By.CSS_SELECTOR, "h1")
    PROMO_CODE_FIELD = (By.ID, "promo")
    APPLY_BUTTON = (By.CSS_SELECTOR, "[data-testid='apply-promo']")
    PLACE_ORDER_BUTTON = (By.ID, "place-order")

    # Action methods — snake_case, composed from BasePage helpers
    def apply_promo_code(self, code: str) -> None:
        self.wait_for_element_visible(self.PROMO_CODE_FIELD)
        self.fill_text(self.PROMO_CODE_FIELD, code)
        self.click(self.APPLY_BUTTON)
        self.wait_until_page_is_fully_loaded()

    def place_order(self) -> None:
        self.click(self.PLACE_ORDER_BUTTON)
        self.wait_until_page_is_fully_loaded()
```

## Steps

1. Confirm the `<app>` package (e.g. `toolshop`) and create `core/pom/web/<app>/<name>_page.py`
   (add an `__init__.py` if the package is new).
2. Fill in the URL constant, locators, copy constants, and action methods per the template.
3. Add the matching test suite with the **`testopus-web-test`** skill (locators stay in the page).
4. Before relying on any Selenium API, verify it via the **`docs-first`** skill.
