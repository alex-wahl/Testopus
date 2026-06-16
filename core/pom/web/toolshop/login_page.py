from selenium.webdriver.common.by import By

from core.pom.web.base_page import BasePage


class LoginPage(BasePage):
    """Toolshop login page (``/auth/login``)."""

    PAGE_URL = "auth/login"

    # Expected copy — assert a stable key phrase, not the full localized sentence.
    TEXT_LOGIN_ERROR_KEY_PHRASE = "Invalid email or password"

    # Locators — stable data-test hooks.
    EMAIL_FIELD = (By.CSS_SELECTOR, "[data-test='email']")
    PASSWORD_FIELD = (By.CSS_SELECTOR, "[data-test='password']")
    LOGIN_SUBMIT = (By.CSS_SELECTOR, "[data-test='login-submit']")
    LOGIN_ERROR = (By.CSS_SELECTOR, "[data-test='login-error']")

    def login(self, email: str, password: str) -> None:
        """Fill the credentials and submit the login form."""
        self.wait_for_element_visible(self.EMAIL_FIELD)
        self.fill_text(self.EMAIL_FIELD, email)
        self.fill_text(self.PASSWORD_FIELD, password)
        self.click(self.LOGIN_SUBMIT)
        self.wait_until_page_is_fully_loaded()
