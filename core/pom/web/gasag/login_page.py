from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from core.pom.web.base_page import BasePage


class LoginPage(BasePage):
    """Login page of Gasag"""

    # URLs
    LOGIN_PAGE_URL = "onlineservice/login"

    # Texts
    TEXT_ERROR_MESSAGE = "Wir konnten zu Ihrer E-Mail-Adresse keine passende Anmeldung finden. Sie sind Geschäftskunde, dann geht es hier zum Energieportal."
    TEXT_INTRO = "Bitte melden Sie sich an."
    TEXT_JETZT_REGISTRIEREN = "Jetzt registrieren"
    TEXT_PASSWORT_VERGESSEN = "Kennwort vergessen?"
    TEXT_ANGEMELDET_BLEIBEN = "Angemeldet bleiben"
    TEXT_ANMELDEN = "Anmelden"
    TEXT_EMAIL = "E-Mail-Adresse"
    TEXT_KENNWORT = "Kennwort"
    TEXT_GOOGLE_LOGIN = "Anmelden mit Google"
    TEXT_APPLE_LOGIN = "Anmelden mit Apple"
    TEXT_GOOGLE_KEY_PHRASES = [
        "Sie können sich, wie in unseren Datenschutzhinweisen beschrieben",
        "in ein Google-Konto einloggen",
        "Daten ggf. in die USA und andere Drittstaaten übermittelt"
    ]
    TEXT_APPLE_KEY_PHRASES = [
        "Sie können sich, wie in unseren Datenschutzhinweisen beschrieben",
        "in ein Apple-Konto einloggen",
        "Daten ggf. in die USA und andere Drittstaaten übermittelt"
    ]

    # Locators
    ERROR_MESSAGE = (By.CLASS_NAME, "error")
    LOGIN_FORM = (By.ID, "localAccountForm")
    ANMELDEN_BUTTON = (By.ID, "next")
    EMAIL_FIELD = (By.ID, "signInName")
    PASSWORD_FIELD = (By.ID, "password")
    JETZT_REGISTRIEREN = (By.ID, "createAccount")
    FORGOT_PASSWORD = (By.ID, "forgotPassword")
    ANGEMELDET_BLEIBEN = (By.ID, "rememberMe")
    GOOGLE_LOGIN = (By.ID, "dummyGoogleBtn")
    APPLE_LOGIN = (By.ID, "dummyAppleBtn")
    GOOGLE_CONTINUE_BUTTON = (By.ID, "continueGoogleBtn")
    APPLE_CONTINUE_BUTTON = (By.ID, "continueAppleBtn")
    GOOGLE_LOGIN_TEXT = (By.CLASS_NAME, "social__legal-section__show")
    APPLE_LOGIN_TEXT = (By.CLASS_NAME, "social__legal-section__show d-hide")
    APPLE_LOGIN_TEXT_2 = (By.CLASS_NAME, "social__legal-section__show")


    def login(self, username: str, password: str):
        self.wait_for_element_visible(self.LOGIN_FORM)
        self.fill_text(self.EMAIL_FIELD, username)
        self.fill_text(self.PASSWORD_FIELD, password)
        self.click(self.ANMELDEN_BUTTON)
        self.wait_until_page_is_fully_loaded()