"""Toolshop web example — product overview/listing.

Runs against the public Practice Software Testing demo shop; no credentials needed.
"""

import logging

import pytest
import pytest_check as check

from core.pom.web.base_page import retry
from core.pom.web.toolshop.home_page import HomePage


def log_retry(attempt, exception, *args, **kwargs):
    logging.warning(f"Retry attempt {attempt + 1} due to: {str(exception)}")


@pytest.mark.feature("Toolshop Catalog")
class TestProducts:
    """Product overview (home) page."""

    BASE_URL = None

    @pytest.fixture(autouse=True)
    def setup_test_suite(self, config):
        if TestProducts.BASE_URL is None:
            self.BASE_URL = config["configuration"]["toolshop"]["web_url"]

    @pytest.fixture
    def home_page(self, driver):
        url = f"{self.BASE_URL}/{HomePage.PAGE_URL}"
        return HomePage(driver, url=url)

    @pytest.mark.severity("critical")
    @pytest.mark.story("Product listing")
    @retry(retries=3, delay=2, on_retry=log_retry)
    def test_product_list_is_shown(self, home_page):
        home_page.wait_for_element_visible(HomePage.PRODUCT_NAME)
        # Soft assertions: collect both checks in one run.
        check.is_true(
            home_page.is_element_present(HomePage.PRODUCT_NAME),
            "No product names shown on the overview page",
        )
        check.is_true(
            home_page.is_element_present(HomePage.PRODUCT_PRICE),
            "No product prices shown on the overview page",
        )
