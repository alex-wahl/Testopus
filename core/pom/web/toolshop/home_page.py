from selenium.webdriver.common.by import By

from core.pom.web.base_page import BasePage


class HomePage(BasePage):
    """Toolshop product-overview (home) page — product listing and search.

    The Toolshop SPA exposes stable ``data-test`` hooks, so locators sit at the top of
    the locator ladder (data-testid first) — exactly the convention Testopus enforces.
    """

    # Root of the app; the test fixture appends this to the configured web URL.
    PAGE_URL = ""

    # Locators — stable data-test hooks (never inline these in a test).
    SEARCH_INPUT = (By.CSS_SELECTOR, "[data-test='search-query']")
    SEARCH_SUBMIT = (By.CSS_SELECTOR, "[data-test='search-submit']")
    SEARCH_RESET = (By.CSS_SELECTOR, "[data-test='search-reset']")
    PRODUCT_NAME = (By.CSS_SELECTOR, "[data-test='product-name']")
    PRODUCT_PRICE = (By.CSS_SELECTOR, "[data-test='product-price']")
    SORT = (By.CSS_SELECTOR, "[data-test='sort']")

    def search(self, term: str) -> None:
        """Type a query into the search box and submit it."""
        self.wait_for_element_visible(self.SEARCH_INPUT)
        self.fill_text(self.SEARCH_INPUT, term)
        self.click(self.SEARCH_SUBMIT)
        self.wait_until_page_is_fully_loaded()
