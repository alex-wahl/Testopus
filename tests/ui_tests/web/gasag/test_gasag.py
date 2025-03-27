import pytest
import time
from selenium.webdriver.support.ui import WebDriverWait
from core.pom.web.gasag.login_page import LoginPage


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

    def test_login_with_invalid_credentials(self, driver):
        url = f"{self.BASE_URL}/{LoginPage.LOGIN_PAGE_URL}"
        login_page = LoginPage(driver, url=url)
        login_page.login(TestGasag.USERNAME, TestGasag.PASSWORD)
        login_page.wait_for_element_visible(LoginPage.ERROR_MESSAGE)
        assert login_page.get_text(LoginPage.ERROR_MESSAGE) == LoginPage.TEXT_ERROR_MESSAGE

    