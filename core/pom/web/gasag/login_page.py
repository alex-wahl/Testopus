from selenium.webdriver.common.by import By

from core.pom.web.base_page import BasePage


class LoginPage(BasePage):
    """Login page of Gasag"""

    # URLs
    LOGIN_PAGE_URL = "onlineservice/login"

    # Texts
    # Assert a stable key phrase, not the full localized sentence (copy churns on edits).
    TEXT_ERROR_KEY_PHRASE = "keine passende Anmeldung"
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
        "Daten ggf. in die USA und andere Drittstaaten übermittelt",
    ]
    TEXT_APPLE_KEY_PHRASES = [
        "Sie können sich, wie in unseren Datenschutzhinweisen beschrieben",
        "in ein Apple-Konto einloggen",
        "Daten ggf. in die USA und andere Drittstaaten übermittelt",
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

    # CSS for the social-login buttons; the legal text is read relative to them
    # (see get_social_legal_text). Kept as page-class constants — never inlined in tests.
    GOOGLE_SOCIAL_BUTTON_CSS = "button.google-btn.social-btn"
    APPLE_SOCIAL_BUTTON_CSS = "button.apple-btn.social-btn"

    def login(self, username: str, password: str):
        self.wait_for_element_visible(self.LOGIN_FORM)
        self.fill_text(self.EMAIL_FIELD, username)
        self.fill_text(self.PASSWORD_FIELD, password)
        self.click(self.ANMELDEN_BUTTON)
        self.wait_until_page_is_fully_loaded()

    def get_social_legal_text(self, button_css: str) -> str:
        """Return the legal-text label rendered next to a social-login button.

        The selector is a page-class constant (never inlined in a test) and is passed
        to the script as a bound argument rather than string-interpolated.

        Args:
            button_css (str): A social-button CSS constant (e.g. GOOGLE_SOCIAL_BUTTON_CSS).

        Returns:
            str: The label text, or "" if the button/label is absent.
        """
        script = (
            "const btn = document.querySelector(arguments[0]);"
            "if (!btn || !btn.nextElementSibling) { return ''; }"
            "const label = btn.nextElementSibling.querySelector('label');"
            "return label ? label.textContent : '';"
        )
        return self.execute_script(script, button_css)
