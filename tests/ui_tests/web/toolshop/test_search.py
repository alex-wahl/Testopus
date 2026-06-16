"""Toolshop web example — product search (positive and negative)."""

import logging

import pytest

from core.pom.web.base_page import retry
from core.pom.web.toolshop.home_page import HomePage


def log_retry(attempt, exception, *args, **kwargs):
    logging.warning(f"Retry attempt {attempt + 1} due to: {str(exception)}")


@pytest.mark.feature("Toolshop Catalog")
class TestSearch:
    """Search on the product-overview page."""

    BASE_URL = None

    @pytest.fixture(autouse=True)
    def setup_test_suite(self, config):
        if TestSearch.BASE_URL is None:
            self.BASE_URL = config["configuration"]["toolshop"]["web_url"]

    @pytest.fixture
    def home_page(self, driver):
        url = f"{self.BASE_URL}/{HomePage.PAGE_URL}"
        return HomePage(driver, url=url)

    @pytest.mark.severity("normal")
    @pytest.mark.story("Search")
    @retry(retries=3, delay=2, on_retry=log_retry)
    def test_search_returns_matching_products(self, home_page):
        home_page.search("Hammer")
        # The Angular grid re-renders *after* document.readyState=complete, so wait for a
        # matching result to appear rather than reading the (stale) pre-filter list.
        assert home_page.wait_for_text_present(
            HomePage.PRODUCT_NAME, "Hammer"
        ), "Search did not surface a matching 'Hammer' product"

    @pytest.mark.severity("minor")
    @pytest.mark.story("Search")
    @retry(retries=3, delay=2, on_retry=log_retry)
    def test_search_for_unknown_term_shows_no_products(self, home_page):
        home_page.search("zzzznotarealproduct")
        # Wait for the grid to clear rather than snapshotting it, so the SPA re-render
        # can't race the assertion.
        assert home_page.wait_for_element_to_disappear(
            HomePage.PRODUCT_NAME
        ), "Products should disappear for a nonsense query"
