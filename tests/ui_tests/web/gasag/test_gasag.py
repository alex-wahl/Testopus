import logging

import pytest
import pytest_check as check
from selenium.webdriver.support.ui import WebDriverWait

from core.pom.web.base_page import retry
from core.pom.web.gasag.login_page import LoginPage


def log_retry(attempt, exception, *args, **kwargs):
    """Log retry attempts for debugging."""
    logging.warning(f"Retry attempt {attempt+1} due to: {str(exception)}")


class TestGasag:

    BASE_URL = None
    USERNAME = None
    PASSWORD = None

    @pytest.fixture(autouse=True)
    def setup_test_suite(self, config):

        if TestGasag.BASE_URL is None:
            TestGasag.BASE_URL = config['configuration']['gasag']['web_url']
        if TestGasag.USERNAME is None:
            TestGasag.USERNAME = config['configuration']['gasag']['username']
        if TestGasag.PASSWORD is None:
            TestGasag.PASSWORD = config['configuration']['gasag']['password']

    @retry(retries=3, delay=2, on_retry=log_retry)
    def test_login_with_invalid_credentials(self, driver):
        url = f"{self.BASE_URL}/{LoginPage.LOGIN_PAGE_URL}"
        login_page = LoginPage(driver, url=url)
        login_page.login(TestGasag.USERNAME, TestGasag.PASSWORD)
        login_page.wait_until_page_is_fully_loaded()
        assert login_page.wait_for_text_present(LoginPage.ERROR_MESSAGE, LoginPage.TEXT_ERROR_MESSAGE)

    @retry(retries=3, delay=2, on_retry=log_retry)
    def test_email_field_is_accepting_email_addresses(self, driver):
        url = f"{self.BASE_URL}/{LoginPage.LOGIN_PAGE_URL}"
        login_page = LoginPage(driver, url=url)
        login_page.wait_for_element(LoginPage.EMAIL_FIELD)
        login_page.fill_text(LoginPage.EMAIL_FIELD, self.USERNAME)
        print(login_page.get_input_value(LoginPage.EMAIL_FIELD))
        assert login_page.get_input_value(LoginPage.EMAIL_FIELD) == self.USERNAME, f"Email is not accepted"

    @retry(retries=3, delay=2, on_retry=log_retry)
    def test_password_field_is_accepting_password(self, driver):
        url = f"{self.BASE_URL}/{LoginPage.LOGIN_PAGE_URL}"
        login_page = LoginPage(driver, url=url)
        login_page.wait_for_element(LoginPage.PASSWORD_FIELD)
        login_page.fill_text(LoginPage.PASSWORD_FIELD, self.PASSWORD)
        print(login_page.get_input_value(LoginPage.PASSWORD_FIELD))
        assert login_page.get_input_value(LoginPage.PASSWORD_FIELD) == self.PASSWORD, f"Password is not accepted"

    @retry(retries=3, delay=2, on_retry=log_retry)
    def test_redirect_to_gasag_portal_after_login(self, driver):
        url = f"{self.BASE_URL}/{LoginPage.LOGIN_PAGE_URL}"
        login_page = LoginPage(driver, url=url)
        login_page.wait_until_page_is_fully_loaded()
        assert login_page.wait_for_url_change(url), f"Redirect to {url} failed"

    @retry(retries=3, delay=2, on_retry=log_retry)
    def test_checkbox_is_checked(self, driver):
        url = f"{self.BASE_URL}/{LoginPage.LOGIN_PAGE_URL}"
        login_page = LoginPage(driver, url=url)
        login_page.wait_for_element(LoginPage.ANGEMELDET_BLEIBEN)
        element = login_page.find_element(LoginPage.ANGEMELDET_BLEIBEN)
        login_page.execute_script("arguments[0].click();", element)
        assert login_page.is_element_selected(LoginPage.ANGEMELDET_BLEIBEN), f"Checkbox is not checked"

    @retry(retries=3, delay=2, on_retry=log_retry)
    def test_wordings(self, driver):
        url = f"{self.BASE_URL}/{LoginPage.LOGIN_PAGE_URL}"
        login_page = LoginPage(driver, url=url)
        login_page.wait_for_element(LoginPage.LOGIN_FORM)
        check.is_in(LoginPage.TEXT_INTRO, login_page.get_text(login_page.LOGIN_FORM), f"Intro text is not displayed")
        check.is_in(LoginPage.TEXT_JETZT_REGISTRIEREN, login_page.get_text(login_page.LOGIN_FORM), f"Jetzt registrieren text is not displayed")
        check.is_in(LoginPage.TEXT_PASSWORT_VERGESSEN, login_page.get_text(login_page.LOGIN_FORM), f"Passwort vergessen text is not displayed")
        check.is_in(LoginPage.TEXT_ANGEMELDET_BLEIBEN, login_page.get_text(login_page.LOGIN_FORM), f"Angemeldet bleiben text is not displayed")
        check.is_in(LoginPage.TEXT_GOOGLE_LOGIN, login_page.get_text(login_page.LOGIN_FORM), f"Google login text is not displayed")
        check.is_in(LoginPage.TEXT_APPLE_LOGIN, login_page.get_text(login_page.LOGIN_FORM), f"Apple login text is not displayed")
        check.is_in(LoginPage.TEXT_ANMELDEN, login_page.get_text(login_page.LOGIN_FORM), f"Anmelden text is not displayed")
        check.is_in(LoginPage.TEXT_EMAIL, login_page.get_text(login_page.LOGIN_FORM), f"E-Mail-Adresse text is not displayed")
        check.is_in(LoginPage.TEXT_KENNWORT, login_page.get_text(login_page.LOGIN_FORM), f"Kennwort text is not displayed")

    @retry(retries=3, delay=2, on_retry=log_retry)
    def test_jetzt_registrieren(self, driver):
        url = f"{self.BASE_URL}/{LoginPage.LOGIN_PAGE_URL}"
        login_page = LoginPage(driver, url=url)
        login_page.wait_for_element(LoginPage.JETZT_REGISTRIEREN)
        current_url = login_page.get_current_url()
        login_page.click(LoginPage.JETZT_REGISTRIEREN)
        login_page.wait_until_page_is_fully_loaded()
        new_url = login_page.get_current_url()
        assert current_url != new_url, f"Redirect to {new_url} failed"

    @retry(retries=3, delay=2, on_retry=log_retry)
    def test_password_vergessen(self, driver):
        url = f"{self.BASE_URL}/{LoginPage.LOGIN_PAGE_URL}"
        login_page = LoginPage(driver, url=url)
        login_page.wait_for_element(LoginPage.FORGOT_PASSWORD)
        current_url = login_page.get_current_url()
        login_page.click(LoginPage.FORGOT_PASSWORD)
        login_page.wait_until_page_is_fully_loaded()
        new_url = login_page.get_current_url()
        assert current_url != new_url, f"Redirect to {new_url} failed"
    
    @retry(retries=3, delay=2, on_retry=log_retry)
    def test_google_login_wording(self, driver):
        url = f"{self.BASE_URL}/{LoginPage.LOGIN_PAGE_URL}"
        login_page = LoginPage(driver, url=url)
        login_page.wait_for_element(LoginPage.GOOGLE_LOGIN)
        login_page.click(LoginPage.GOOGLE_LOGIN)
        
        # Use the same improved selector approach
        google_text = login_page.execute_script("""
            // Use a more specific selector for the Google button
            var googleSection = document.querySelector('button.google-btn.social-btn').nextElementSibling;
            return googleSection ? googleSection.querySelector('label').textContent : '';
        """)
        
        for phrase in LoginPage.TEXT_GOOGLE_KEY_PHRASES:
            check.is_in(phrase, google_text, f"Expected phrase '{phrase}' not found in Google login text")
    
    @retry(retries=3, delay=2, on_retry=log_retry)
    def test_apple_login_wording(self, driver):
        url = f"{self.BASE_URL}/{LoginPage.LOGIN_PAGE_URL}"
        login_page = LoginPage(driver, url=url)
        login_page.wait_for_element(LoginPage.APPLE_LOGIN)
        login_page.click(LoginPage.APPLE_LOGIN)
        
        # Fix the selector to target Apple button more precisely
        apple_text = login_page.execute_script("""
            // Use a more specific selector for the Apple button
            var appleSection = document.querySelector('button.apple-btn.social-btn').nextElementSibling;
            return appleSection ? appleSection.querySelector('label').textContent : '';
        """)
        
        for phrase in LoginPage.TEXT_APPLE_KEY_PHRASES:
            check.is_in(phrase, apple_text, f"Expected phrase '{phrase}' not found in Apple login text")
    
    @retry(retries=3, delay=2, on_retry=log_retry)
    def test_google_login(self, driver):
        url = f"{self.BASE_URL}/{LoginPage.LOGIN_PAGE_URL}"
        login_page = LoginPage(driver, url=url)
        login_page.wait_for_element(LoginPage.GOOGLE_LOGIN)
        login_page.click(LoginPage.GOOGLE_LOGIN)
        login_page.wait_for_element(LoginPage.GOOGLE_CONTINUE_BUTTON)
        current_url = login_page.get_current_url()
        login_page.click(LoginPage.GOOGLE_CONTINUE_BUTTON)
        assert login_page.wait_for_url_change(current_url), f"Redirect to {url} failed"
    
    @retry(retries=3, delay=2, on_retry=log_retry)
    def test_apple_login(self, driver):
        url = f"{self.BASE_URL}/{LoginPage.LOGIN_PAGE_URL}"
        login_page = LoginPage(driver, url=url)
        login_page.wait_for_element(LoginPage.APPLE_LOGIN)
        login_page.click(LoginPage.APPLE_LOGIN)
        login_page.wait_for_element(LoginPage.APPLE_CONTINUE_BUTTON)
        current_url = login_page.get_current_url()
        login_page.click(LoginPage.APPLE_CONTINUE_BUTTON)
        assert login_page.wait_for_url_change(current_url), f"Redirect to {url} failed"