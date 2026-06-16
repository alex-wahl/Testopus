from __future__ import annotations

from typing import Any, List, Optional, Tuple

from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from core.drivers.base import ElementHandle

Locator = Tuple[str, str]

# Transient conditions WebDriverWait should poll through rather than fail on.
_IGNORED_EXCEPTIONS = (StaleElementReferenceException,)


class SeleniumElement:
    """Selenium-backed :class:`ElementHandle`."""

    def __init__(self, element: WebElement):
        self._element = element

    @property
    def raw(self) -> WebElement:
        return self._element

    def click(self) -> None:
        self._element.click()

    def clear(self) -> None:
        self._element.clear()

    def send_keys(self, text: str) -> None:
        self._element.send_keys(text)

    def get_attribute(self, name: str) -> Optional[str]:
        return self._element.get_attribute(name)

    @property
    def text(self) -> str:
        return self._element.text

    def is_selected(self) -> bool:
        return self._element.is_selected()

    def is_enabled(self) -> bool:
        return self._element.is_enabled()

    def is_displayed(self) -> bool:
        return self._element.is_displayed()


def _unwrap(arg: Any) -> Any:
    """Unwrap a SeleniumElement back to its raw WebElement for execute_script."""
    return arg.raw if isinstance(arg, SeleniumElement) else arg


class SeleniumDriver:
    """Selenium WebDriver implementation of the :class:`BaseDriver` protocol.

    Waits go through ``WebDriverWait`` with ``ignored_exceptions`` so transient
    stale-element churn is polled through correctly — replacing the previous
    hand-rolled ``time.sleep`` retry loops.
    """

    def __init__(self, driver: WebDriver):
        self._driver = driver

    @property
    def raw(self) -> WebDriver:
        """Selenium escape hatch for the not-yet-abstracted long tail."""
        return self._driver

    def _wait(self, timeout: int) -> WebDriverWait:
        return WebDriverWait(
            self._driver, timeout, ignored_exceptions=_IGNORED_EXCEPTIONS
        )

    def get(self, url: str) -> None:
        self._driver.get(url)

    def find(self, locator: Locator) -> ElementHandle:
        return SeleniumElement(self._driver.find_element(*locator))

    def find_all(self, locator: Locator) -> List[ElementHandle]:
        return [SeleniumElement(el) for el in self._driver.find_elements(*locator)]

    def wait_for_present(self, locator: Locator, timeout: int) -> ElementHandle:
        return SeleniumElement(
            self._wait(timeout).until(EC.presence_of_element_located(locator))
        )

    def wait_for_visible(self, locator: Locator, timeout: int) -> ElementHandle:
        return SeleniumElement(
            self._wait(timeout).until(EC.visibility_of_element_located(locator))
        )

    def wait_for_clickable(self, locator: Locator, timeout: int) -> ElementHandle:
        return SeleniumElement(
            self._wait(timeout).until(EC.element_to_be_clickable(locator))
        )

    def wait_for_text(self, locator: Locator, text: str, timeout: int) -> bool:
        return bool(
            self._wait(timeout).until(EC.text_to_be_present_in_element(locator, text))
        )

    def wait_for_invisible(self, locator: Locator, timeout: int) -> bool:
        return bool(
            self._wait(timeout).until(EC.invisibility_of_element_located(locator))
        )

    def wait_for_page_loaded(self, locator: Locator, timeout: int) -> None:
        try:
            self._wait(timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
        except TimeoutException:
            # readyState doesn't always reach "complete"; the element wait below is
            # the real gate.
            pass
        self._wait(timeout).until(EC.presence_of_element_located(locator))

    def wait_for_url_change(self, original_url: str, timeout: int) -> bool:
        try:
            return self._wait(timeout).until(lambda d: d.current_url != original_url)
        except TimeoutException:
            return False

    def wait_for_url_contains(self, substring: str, timeout: int) -> bool:
        try:
            return self._wait(timeout).until(EC.url_contains(substring))
        except TimeoutException:
            return False

    def execute_script(self, script: str, *args: Any) -> Any:
        return self._driver.execute_script(script, *[_unwrap(a) for a in args])

    def accept_alert(self, timeout: int) -> None:
        WebDriverWait(self._driver, timeout).until(EC.alert_is_present()).accept()

    def save_screenshot(self, path: str) -> bool:
        return self._driver.save_screenshot(path)

    def refresh(self) -> None:
        self._driver.refresh()

    def back(self) -> None:
        self._driver.back()

    @property
    def current_url(self) -> str:
        return self._driver.current_url

    def quit(self) -> None:
        self._driver.quit()
