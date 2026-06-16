import logging

import pytest
import pytest_check as check

from core.pom.web.base_page import retry
from core.pom.web.gasag.login_page import LoginPage


def log_retry(attempt, exception, *args, **kwargs):
    """Log retry attempts for debugging."""
    logging.warning(f"Retry attempt {attempt + 1} due to: {str(exception)}")


@pytest.mark.feature("GASAG Login")
class TestGasag:
    """Test suite for Gasag"""

    BASE_URL = None
    USERNAME = None
    PASSWORD = None

    @pytest.fixture(autouse=True)
    def setup_test_suite(self, config):
        if TestGasag.BASE_URL is None:
            self.BASE_URL = config["configuration"]["gasag"]["web_url"]
        if TestGasag.USERNAME is None:
            self.USERNAME = config["configuration"]["gasag"]["username"]
        if TestGasag.PASSWORD is None:
            self.PASSWORD = config["configuration"]["gasag"]["password"]

    @pytest.fixture
    def login_page(self, driver):
        """Fixture to create and return a LoginPage instance."""
        url = f"{self.BASE_URL}/{LoginPage.LOGIN_PAGE_URL}"
        page = LoginPage(driver, url=url)
        return page

    @pytest.mark.severity("critical")
    @pytest.mark.story("Authentication")
    @retry(retries=3, delay=2, on_retry=log_retry)
    def test_login_with_invalid_credentials(self, login_page):
        login_page.login(self.USERNAME, self.PASSWORD)
        login_page.wait_until_page_is_fully_loaded()
        assert login_page.wait_for_text_present(
            LoginPage.ERROR_MESSAGE, LoginPage.TEXT_ERROR_KEY_PHRASE
        )

    @pytest.mark.story("Field validation")
    @retry(retries=3, delay=2, on_retry=log_retry)
    def test_email_field_is_accepting_email_addresses(self, login_page):
        login_page.wait_for_element(LoginPage.EMAIL_FIELD)
        login_page.fill_text(LoginPage.EMAIL_FIELD, self.USERNAME)
        assert (
            login_page.get_input_value(LoginPage.EMAIL_FIELD) == self.USERNAME
        ), "Email is not accepted"

    @pytest.mark.story("Field validation")
    @retry(retries=3, delay=2, on_retry=log_retry)
    def test_password_field_is_accepting_password(self, login_page):
        login_page.wait_for_element(LoginPage.PASSWORD_FIELD)
        login_page.fill_text(LoginPage.PASSWORD_FIELD, self.PASSWORD)
        assert (
            login_page.get_input_value(LoginPage.PASSWORD_FIELD) == self.PASSWORD
        ), "Password is not accepted"

    @pytest.mark.story("Authentication")
    @retry(retries=3, delay=2, on_retry=log_retry)
    def test_login_page_loads(self, login_page):
        login_page.wait_until_page_is_fully_loaded()
        assert login_page.is_element_present(
            LoginPage.LOGIN_FORM
        ), "Login form did not load"

    @pytest.mark.story("Form interactions")
    @retry(retries=3, delay=2, on_retry=log_retry)
    def test_checkbox_is_checked(self, login_page):
        login_page.check_checkbox(LoginPage.ANGEMELDET_BLEIBEN)
        assert login_page.is_element_selected(
            LoginPage.ANGEMELDET_BLEIBEN
        ), "Checkbox is not checked"

    @pytest.mark.story("Page content")
    def test_wordings(self, login_page):
        login_page.wait_for_element(LoginPage.LOGIN_FORM)
        check.is_in(
            LoginPage.TEXT_INTRO,
            login_page.get_text(login_page.LOGIN_FORM),
            "Intro text is not displayed",
        )
        check.is_in(
            LoginPage.TEXT_JETZT_REGISTRIEREN,
            login_page.get_text(login_page.LOGIN_FORM),
            "Jetzt registrieren text is not displayed",
        )
        check.is_in(
            LoginPage.TEXT_PASSWORT_VERGESSEN,
            login_page.get_text(login_page.LOGIN_FORM),
            "Passwort vergessen text is not displayed",
        )
        check.is_in(
            LoginPage.TEXT_ANGEMELDET_BLEIBEN,
            login_page.get_text(login_page.LOGIN_FORM),
            "Angemeldet bleiben text is not displayed",
        )
        check.is_in(
            LoginPage.TEXT_GOOGLE_LOGIN,
            login_page.get_text(login_page.LOGIN_FORM),
            "Google login text is not displayed",
        )
        check.is_in(
            LoginPage.TEXT_APPLE_LOGIN,
            login_page.get_text(login_page.LOGIN_FORM),
            "Apple login text is not displayed",
        )
        check.is_in(
            LoginPage.TEXT_ANMELDEN,
            login_page.get_text(login_page.LOGIN_FORM),
            "Anmelden text is not displayed",
        )
        check.is_in(
            LoginPage.TEXT_EMAIL,
            login_page.get_text(login_page.LOGIN_FORM),
            "E-Mail-Adresse text is not displayed",
        )
        check.is_in(
            LoginPage.TEXT_KENNWORT,
            login_page.get_text(login_page.LOGIN_FORM),
            "Kennwort text is not displayed",
        )

    @pytest.mark.story("Navigation")
    @retry(retries=3, delay=2, on_retry=log_retry)
    def test_jetzt_registrieren(self, login_page):
        login_page.wait_for_element(LoginPage.JETZT_REGISTRIEREN)
        current_url = login_page.get_current_url()
        login_page.click(LoginPage.JETZT_REGISTRIEREN)
        login_page.wait_until_page_is_fully_loaded()
        new_url = login_page.get_current_url()
        assert current_url != new_url, f"Redirect to {new_url} failed"

    @pytest.mark.story("Navigation")
    @retry(retries=3, delay=2, on_retry=log_retry)
    def test_password_vergessen(self, login_page):
        login_page.wait_for_element(LoginPage.FORGOT_PASSWORD)
        current_url = login_page.get_current_url()
        login_page.click(LoginPage.FORGOT_PASSWORD)
        login_page.wait_until_page_is_fully_loaded()
        new_url = login_page.get_current_url()
        assert current_url != new_url, f"Redirect to {new_url} failed"

    @pytest.mark.story("Social login")
    def test_google_login_wording(self, login_page):
        login_page.wait_for_element(LoginPage.GOOGLE_LOGIN)
        login_page.click(LoginPage.GOOGLE_LOGIN)

        google_text = login_page.get_social_legal_text(
            LoginPage.GOOGLE_SOCIAL_BUTTON_CSS
        )

        for phrase in LoginPage.TEXT_GOOGLE_KEY_PHRASES:
            check.is_in(
                phrase,
                google_text,
                f"Expected phrase '{phrase}' not found in Google login text",
            )

    @pytest.mark.story("Social login")
    def test_apple_login_wording(self, login_page):
        login_page.wait_for_element(LoginPage.APPLE_LOGIN)
        login_page.click(LoginPage.APPLE_LOGIN)

        apple_text = login_page.get_social_legal_text(LoginPage.APPLE_SOCIAL_BUTTON_CSS)

        for phrase in LoginPage.TEXT_APPLE_KEY_PHRASES:
            check.is_in(
                phrase,
                apple_text,
                f"Expected phrase '{phrase}' not found in Apple login text",
            )

    @pytest.mark.story("Social login")
    @retry(retries=3, delay=2, on_retry=log_retry)
    def test_google_login(self, login_page):
        login_page.wait_for_element(LoginPage.GOOGLE_LOGIN)
        login_page.click(LoginPage.GOOGLE_LOGIN)
        login_page.wait_for_element(LoginPage.GOOGLE_CONTINUE_BUTTON)
        current_url = login_page.get_current_url()
        login_page.click(LoginPage.GOOGLE_CONTINUE_BUTTON)
        assert login_page.wait_for_url_change(
            current_url
        ), f"Redirect to {current_url} failed"

    @pytest.mark.story("Social login")
    @retry(retries=3, delay=2, on_retry=log_retry)
    def test_apple_login(self, login_page):
        login_page.wait_for_element(LoginPage.APPLE_LOGIN)
        login_page.click(LoginPage.APPLE_LOGIN)
        login_page.wait_for_element(LoginPage.APPLE_CONTINUE_BUTTON)
        current_url = login_page.get_current_url()
        login_page.click(LoginPage.APPLE_CONTINUE_BUTTON)
        assert login_page.wait_for_url_change(
            current_url
        ), f"Redirect to {current_url} failed"
