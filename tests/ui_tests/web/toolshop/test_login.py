"""Toolshop web example — login (negative + positive with the public demo account)."""

import logging

import pytest

from core.pom.web.base_page import retry
from core.pom.web.toolshop.login_page import LoginPage


def log_retry(attempt, exception, *args, **kwargs):
    logging.warning(f"Retry attempt {attempt + 1} due to: {str(exception)}")


@pytest.mark.feature("Toolshop Account")
class TestLogin:
    """Login page (/auth/login)."""

    BASE_URL = None
    EMAIL = None
    PASSWORD = None

    @pytest.fixture(autouse=True)
    def setup_test_suite(self, config):
        if TestLogin.BASE_URL is None:
            self.BASE_URL = config["configuration"]["toolshop"]["web_url"]
            self.EMAIL = config["configuration"]["toolshop"]["email"]
            self.PASSWORD = config["configuration"]["toolshop"]["password"]

    @pytest.fixture
    def login_page(self, driver):
        url = f"{self.BASE_URL}/{LoginPage.PAGE_URL}"
        return LoginPage(driver, url=url)

    @pytest.mark.severity("critical")
    @pytest.mark.story("Authentication")
    @retry(retries=3, delay=2, on_retry=log_retry)
    def test_login_with_invalid_credentials_shows_error(self, login_page):
        login_page.login("nobody@example.com", "wrong-password")
        assert login_page.wait_for_text_present(
            LoginPage.LOGIN_ERROR, LoginPage.TEXT_LOGIN_ERROR_KEY_PHRASE
        ), "Expected an authentication error for invalid credentials"

    @pytest.mark.severity("critical")
    @pytest.mark.story("Authentication")
    @retry(retries=3, delay=2, on_retry=log_retry)
    def test_login_with_valid_credentials_succeeds(self, login_page):
        login_url = f"{self.BASE_URL}/{LoginPage.PAGE_URL}"
        login_page.login(self.EMAIL, self.PASSWORD)
        assert login_page.wait_for_url_change(
            login_url
        ), "Login did not navigate away from the form"
