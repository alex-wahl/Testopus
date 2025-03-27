from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

from core.pom.web.base_page import BasePage


class LoginPage(BasePage):
    """Login page of Gasag"""

    # URLs
    LOGIN_PAGE_URL = "onlineservice/login"

    # Texts
    TEXT_ERROR_MESSAGE = "Wir konnten zu Ihrer E-Mail-Adresse keine passende Anmeldung finden. Sie sind Geschäftskunde, dann geht es hier zum Energieportal."
    TEXT_INTRO = "Bitte melden Sie sich an."

    # Locators
    LOGIN_FORM = (By.ID, "localAccountForm")
    ANMELDEN_BUTTON = (By.ID, "next")
    EMAIL_FIELD = (By.ID, "signInName")
    PASSWORD_FIELD = (By.ID, "password")
    JETZT_REGISTRIEREN = (By.ID, "createAccount")
    FORGOT_PASSWORD = (By.ID, "forgotPassword")
    ANGEMELDET_BLEIBEN = (By.ID, "rememberMe")
    GOOGLE_LOGIN = (By.ID, "dummyGoogleBtn")
    APPLE_LOGIN = (By.ID, "dummyAppleBtn")

    # Elements
    ERROR_MESSAGE = (By.CLASS_NAME, "error")
    INTRO_TEXT = (By.CLASS_NAME, "intro")

    def login(self, username: str, password: str):
        self.wait_for_element_visible(self.LOGIN_FORM)
        self.fill_text(self.EMAIL_FIELD, username)
        self.fill_text(self.PASSWORD_FIELD, password)
        self.click(self.ANMELDEN_BUTTON)
        self.wait_until_page_is_fully_loaded()