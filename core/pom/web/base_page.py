import functools
import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Optional, Tuple

from selenium.common.exceptions import (
    ElementNotVisibleException,
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from core.drivers.base import BaseDriver, ElementHandle


class BasePage:
    TITLE = "head > title"
    TAG_NAME = "body"
    # Single source of truth for waits; overridable via env for slow environments (e.g. CI
    # against a freshly-booted dev server). Defaults preserve local/Docker behaviour.
    DEFAULT_TIMEOUT = int(os.environ.get("SELENIUM_DEFAULT_TIMEOUT", "3"))
    PAGE_LOAD_TIMEOUT = int(os.environ.get("SELENIUM_PAGE_LOAD_TIMEOUT", "10"))

    def __init__(self, driver: BaseDriver, url: str):
        # `driver` is a framework-agnostic BaseDriver (see core/drivers/), not a raw
        # Selenium WebDriver. Page objects depend only on this interface.
        self.driver = driver
        self.driver.get(url)

    def wait_until_page_is_fully_loaded(
        self, locator: Optional[Tuple[str, str]] = None
    ) -> None:
        """Wait for the page to be fully loaded by checking for a specific element.

        Args:
            locator (Tuple[str, str], optional): The element locator to wait for.
        """
        if locator is None:
            locator = (By.TAG_NAME, self.TAG_NAME)
        self.driver.wait_for_page_loaded(locator, self.PAGE_LOAD_TIMEOUT)

    def wait_for_element(
        self, locator: Tuple[str, str], timeout: Optional[int] = None
    ) -> ElementHandle:
        """Wait for element to be present in the DOM.

        Args:
            locator (Tuple[str, str]): The element locator.
            timeout (int, optional): Time to wait in seconds. Defaults to DEFAULT_TIMEOUT.

        Returns:
            ElementHandle: The found element.
        """
        return self.driver.wait_for_present(locator, timeout or self.DEFAULT_TIMEOUT)

    def wait_for_element_visible(
        self, locator: Tuple[str, str], timeout: Optional[int] = None
    ) -> ElementHandle:
        """Wait for element to be visible on the page.

        Args:
            locator (Tuple[str, str]): The element locator.
            timeout (int, optional): Time to wait in seconds. Defaults to DEFAULT_TIMEOUT.

        Returns:
            ElementHandle: The visible element.
        """
        return self.driver.wait_for_visible(locator, timeout or self.DEFAULT_TIMEOUT)

    def wait_for_element_clickable(
        self, locator: Tuple[str, str], timeout: Optional[int] = None
    ) -> ElementHandle:
        """Wait for element to be clickable.

        Args:
            locator (Tuple[str, str]): The element locator.
            timeout (int, optional): Time to wait in seconds. Defaults to DEFAULT_TIMEOUT.

        Returns:
            ElementHandle: The clickable element.
        """
        return self.driver.wait_for_clickable(locator, timeout or self.DEFAULT_TIMEOUT)

    def wait_for_text_present(
        self, locator: Tuple[str, str], text: str, timeout: Optional[int] = None
    ) -> bool:
        """Wait for specific text to be present in the element.

        Args:
            locator (Tuple[str, str]): The element locator.
            text (str): The text to wait for.
            timeout (int, optional): Time to wait in seconds. Defaults to DEFAULT_TIMEOUT.

        Returns:
            bool: True if text is present.
        """
        return self.driver.wait_for_text(locator, text, timeout or self.DEFAULT_TIMEOUT)

    def wait_for_element_to_disappear(
        self, locator: Tuple[str, str], timeout: Optional[int] = None
    ) -> bool:
        """Wait for element to disappear from DOM or become invisible.

        Args:
            locator (Tuple[str, str]): The element locator.
            timeout (int, optional): Time to wait in seconds. Defaults to DEFAULT_TIMEOUT.

        Returns:
            bool: True if element disappeared.
        """
        return self.driver.wait_for_invisible(locator, timeout or self.DEFAULT_TIMEOUT)

    def simple_click(self, element: ElementHandle) -> None:
        """Perform a standard click on an element.

        Args:
            element (ElementHandle): The element to click.
        """
        element.click()

    def js_click(self, element: ElementHandle) -> None:
        """Click an element using JavaScript.

        Args:
            element (ElementHandle): The element to click.
        """
        self.driver.execute_script("arguments[0].click();", element)

    def safe_click(
        self, locator: Tuple[str, str], timeout: Optional[int] = None
    ) -> None:
        """Click on an element, falling back to a JavaScript click.

        Waiting/polling (including stale-element churn) is handled by the driver's
        explicit wait, so no manual sleep loop is needed here.

        Args:
            locator (Tuple[str, str]): The element locator.
            timeout (int, optional): Time to wait in seconds.

        Raises:
            ElementNotVisibleException: If element is not clickable within the timeout.
        """
        timeout = timeout or self.DEFAULT_TIMEOUT
        try:
            element = self.wait_for_element_visible(locator, timeout)
        except TimeoutException as exc:
            raise ElementNotVisibleException(
                f"Element {locator} not clickable within {timeout}s: {exc}"
            ) from exc

        try:
            self.simple_click(element)
        except WebDriverException:
            # If the regular click is intercepted/fails, fall back to a JS click.
            self.js_click(element)

    def click(self, locator: Tuple[str, str], timeout: Optional[int] = None) -> None:
        """Click on an element. Maintained for backward compatibility; calls safe_click().

        Args:
            locator (Tuple[str, str]): The element locator.
            timeout (int, optional): Time to wait in seconds.
        """
        self.safe_click(locator, timeout)

    def clear_field(self, element: ElementHandle) -> None:
        """Clear the contents of an input field.

        Args:
            element (ElementHandle): The input field to clear.
        """
        try:
            element.clear()
        except WebDriverException:
            # If standard clear fails, use JavaScript.
            self.driver.execute_script("arguments[0].value = '';", element)

    def simple_input(self, element: ElementHandle, text: str) -> None:
        """Enter text in an input field using the standard method.

        Args:
            element (ElementHandle): The input field element.
            text (str): The text to enter.
        """
        element.send_keys(text)

    def js_input(self, element: ElementHandle, text: str) -> None:
        """Enter text in an input field using JavaScript.

        The value is passed as a bound script argument (never string-interpolated),
        so quotes/backslashes/newlines in ``text`` are handled safely.

        Args:
            element (ElementHandle): The input field element.
            text (str): The text to enter.
        """
        self.driver.execute_script("arguments[0].value = arguments[1];", element, text)

    def safe_input(
        self, locator: Tuple[str, str], text: str, timeout: Optional[int] = None
    ) -> None:
        """Enter text in an input field with a JavaScript fallback and validation.

        Args:
            locator (Tuple[str, str]): The input field locator.
            text (str): The text to enter.
            timeout (int, optional): Time to wait in seconds.

        Raises:
            NoSuchElementException: If the element is not found within the timeout.
        """
        timeout = timeout or self.DEFAULT_TIMEOUT
        try:
            element = self.wait_for_element_visible(locator, timeout)
        except TimeoutException as exc:
            raise NoSuchElementException(
                f"Could not fill text in {locator} within {timeout}s: {exc}"
            ) from exc

        try:
            self.clear_field(element)
            self.simple_input(element, text)
            # Verify the text was entered correctly; fall back to JS if not.
            if element.get_attribute("value") == text:
                return
            self.js_input(element, text)
        except WebDriverException:
            self.clear_field(element)
            self.js_input(element, text)

    def fill_text(self, locator: Tuple[str, str], text: str) -> None:
        """Enter text in an input field. Maintained for compatibility; calls safe_input().

        Args:
            locator (Tuple[str, str]): The input field locator.
            text (str): The text to enter.
        """
        self.safe_input(locator, text)

    def get_title(self) -> str:
        """Get the page title text.

        Returns:
            str: The page title.
        """
        return self.driver.find((By.CSS_SELECTOR, self.TITLE)).text

    def is_element_present(self, locator: Tuple[str, str], timeout: int = 1) -> bool:
        """Check if element is present without raising an exception.

        Args:
            locator (Tuple[str, str]): The element locator.
            timeout (int, optional): Time to wait in seconds. Defaults to 1.

        Returns:
            bool: True if element is present, False otherwise.
        """
        try:
            self.wait_for_element(locator, timeout)
            return True
        except TimeoutException:
            return False

    def get_text(self, locator: Tuple[str, str]) -> str:
        """Get text from an element.

        Args:
            locator (Tuple[str, str]): The element locator.

        Returns:
            str: The element's text.
        """
        return self.wait_for_element_visible(locator).text

    def execute_script(self, script: str, *args) -> Any:
        """Execute JavaScript in the context of the page.

        Args:
            script (str): The JavaScript code to execute.
            *args: Arguments to pass to the script.

        Returns:
            Any: The script execution result.
        """
        return self.driver.execute_script(script, *args)

    def accept_alert(self) -> None:
        """Accept a JavaScript alert."""
        self.driver.accept_alert(self.DEFAULT_TIMEOUT)

    def take_screenshot(self, filename: str) -> None:
        """Take a screenshot of the current page.

        Args:
            filename (str): The path to save the screenshot.
        """
        self.driver.save_screenshot(filename)

    # Form interactions
    def select_dropdown_option(
        self, locator: Tuple[str, str], option_text: str
    ) -> None:
        """Select an option from a dropdown by visible text.

        Uses the Selenium escape hatch (``Select``); a non-Selenium backend would
        provide its own implementation.

        Args:
            locator (Tuple[str, str]): The dropdown element locator.
            option_text (str): The visible text of the option to select.

        Raises:
            NoSuchElementException: If dropdown or option cannot be found.
        """
        try:
            self.wait_for_element_visible(locator)
            Select(self.driver.raw.find_element(*locator)).select_by_visible_text(
                option_text
            )
        except (TimeoutException, NoSuchElementException) as e:
            raise NoSuchElementException(
                f"Could not select option '{option_text}' from {locator}: {str(e)}"
            )

    def check_checkbox(self, locator: Tuple[str, str], check: bool = True) -> None:
        """Check or uncheck a checkbox.

        Args:
            locator (Tuple[str, str]): The checkbox element locator.
            check (bool, optional): True to check, False to uncheck. Defaults to True.

        Raises:
            NoSuchElementException: If checkbox cannot be found or manipulated.
        """
        try:
            element = self.wait_for_element_clickable(locator)
            if element.is_selected() != check:
                element.click()
        except (TimeoutException, NoSuchElementException) as e:
            raise NoSuchElementException(
                f"Could not {'check' if check else 'uncheck'} checkbox {locator}: {str(e)}"
            )

    def get_attribute(self, locator: Tuple[str, str], attribute: str) -> Optional[str]:
        """Get attribute value of an element.

        Args:
            locator (Tuple[str, str]): The element locator.
            attribute (str): The attribute name.

        Returns:
            str: The attribute value.

        Raises:
            NoSuchElementException: If element cannot be found.
        """
        try:
            element = self.wait_for_element(locator)
            return element.get_attribute(attribute)
        except (TimeoutException, NoSuchElementException) as e:
            raise NoSuchElementException(
                f"Could not get attribute '{attribute}' from {locator}: {str(e)}"
            )

    # Navigation
    def navigate_to(self, url: str) -> None:
        """Navigate to a specific URL.

        Args:
            url (str): The URL to navigate to.
        """
        self.driver.get(url)

    def refresh_page(self) -> None:
        """Refresh the current page."""
        self.driver.refresh()

    def go_back(self) -> None:
        """Navigate back to the previous page."""
        self.driver.back()

    # Advanced interactions (Selenium escape hatch via driver.raw)
    def hover(self, locator: Tuple[str, str]) -> None:
        """Hover over an element.

        Args:
            locator (Tuple[str, str]): The element locator to hover over.

        Raises:
            ElementNotVisibleException: If element cannot be found or hovered.
        """
        try:
            self.wait_for_element_visible(locator)
            element = self.driver.raw.find_element(*locator)
            ActionChains(self.driver.raw).move_to_element(element).perform()
        except (TimeoutException, NoSuchElementException) as e:
            raise ElementNotVisibleException(
                f"Could not hover over element {locator}: {str(e)}"
            )

    def drag_and_drop(
        self, source_locator: Tuple[str, str], target_locator: Tuple[str, str]
    ) -> None:
        """Drag and drop an element.

        Args:
            source_locator (Tuple[str, str]): The source element locator.
            target_locator (Tuple[str, str]): The target element locator.

        Raises:
            ElementNotVisibleException: If elements cannot be found or dragged.
        """
        try:
            self.wait_for_element_visible(source_locator)
            self.wait_for_element_visible(target_locator)
            source = self.driver.raw.find_element(*source_locator)
            target = self.driver.raw.find_element(*target_locator)
            ActionChains(self.driver.raw).drag_and_drop(source, target).perform()
        except (TimeoutException, NoSuchElementException) as e:
            raise ElementNotVisibleException(
                f"Could not perform drag and drop: {str(e)}"
            )

    def double_click(self, locator: Tuple[str, str]) -> None:
        """Double click on an element.

        Args:
            locator (Tuple[str, str]): The element locator to double click on.

        Raises:
            ElementNotVisibleException: If element cannot be found or double-clicked.
        """
        try:
            self.wait_for_element_clickable(locator)
            element = self.driver.raw.find_element(*locator)
            ActionChains(self.driver.raw).double_click(element).perform()
        except (TimeoutException, NoSuchElementException) as e:
            raise ElementNotVisibleException(
                f"Could not double click on element {locator}: {str(e)}"
            )

    # Verification methods
    def is_element_enabled(self, locator: Tuple[str, str]) -> bool:
        """Check if element is enabled.

        Args:
            locator (Tuple[str, str]): The element locator.

        Returns:
            bool: True if enabled, False otherwise.
        """
        try:
            element = self.wait_for_element(locator)
            return element.is_enabled()
        except TimeoutException:
            return False

    def is_element_selected(self, locator: Tuple[str, str]) -> bool:
        """Check if element is selected (for checkboxes, radio buttons).

        Args:
            locator (Tuple[str, str]): The element locator.

        Returns:
            bool: True if selected, False otherwise.
        """
        try:
            element = self.wait_for_element(locator)
            return element.is_selected()
        except TimeoutException:
            return False

    def get_current_url(self) -> str:
        """Get the current page URL.

        Returns:
            str: The current URL.
        """
        return self.driver.current_url

    def get_input_value(self, locator: Tuple[str, str]) -> Optional[str]:
        """Get value from an input element.

        Args:
            locator (Tuple[str, str]): The element locator.

        Returns:
            str: The input's value.
        """
        return self.wait_for_element_visible(locator).get_attribute("value")

    def wait_for_url_change(self, original_url: str, timeout: int = 10) -> bool:
        """Wait for the URL to change from the original URL.

        Args:
            original_url (str): The URL to change from.
            timeout (int, optional): Time to wait in seconds. Defaults to 10.

        Returns:
            bool: True if URL changed, False otherwise.
        """
        return self.driver.wait_for_url_change(original_url, timeout)

    def wait_for_url_contains(self, url_substring: str, timeout: int = 10) -> bool:
        """Wait for the URL to contain a specific substring.

        Args:
            url_substring (str): The substring to wait for in the URL.
            timeout (int, optional): Time to wait in seconds. Defaults to 10.

        Returns:
            bool: True if substring found in URL, False otherwise.
        """
        return self.driver.wait_for_url_contains(url_substring, timeout)

    def find_element(self, locator: Tuple[str, str]) -> ElementHandle:
        """Find an element.

        Args:
            locator (Tuple[str, str]): The element locator.

        Returns:
            ElementHandle: The found element.
        """
        return self.driver.find(locator)


def _emit_retry_event(event: dict) -> None:
    """Append a structured retry event to reports/retry_events.jsonl (fail-open).

    This is observation only — telemetry must never affect the test verdict, so any
    failure to emit is swallowed.
    """
    try:
        reports_dir = os.path.join(os.getcwd(), "reports")
        os.makedirs(reports_dir, exist_ok=True)
        with open(
            os.path.join(reports_dir, "retry_events.jsonl"), "a", encoding="utf-8"
        ) as handle:
            handle.write(json.dumps(event) + "\n")
    except Exception:
        pass


def retry(retries=3, delay=1, exceptions=(WebDriverException,), on_retry=None):
    """Retry decorator for functions that fail on *genuine* web flakiness.

    The default ``exceptions`` is ``(WebDriverException,)`` — Selenium's base error
    — so transient web issues (timeouts, stale elements, intercepted clicks) are
    retried while ``AssertionError`` and other logic failures surface immediately
    rather than being masked. Each retry (and a retry-to-pass) emits a fail-open
    ``retry_event`` so flakiness is observable.

    Args:
        retries: Number of attempts. Default 3.
        delay: Delay between retries in seconds. Default 1.
        exceptions: Exception types to catch and retry. Default web exceptions only.
        on_retry: Optional callback ``(attempt, exception, *args, **kwargs)``.

    Returns:
        The decorated function.
    """

    def decorator(func):
        func_name = getattr(func, "__qualname__", repr(func))

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(retries):
                try:
                    result = func(*args, **kwargs)
                    if attempt > 0:
                        _emit_retry_event(
                            {
                                "event": "retry_to_pass",
                                "function": func_name,
                                "attempts": attempt + 1,
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            }
                        )
                    return result
                except exceptions as e:
                    last_exception = e
                    _emit_retry_event(
                        {
                            "event": "retry",
                            "function": func_name,
                            "attempt": attempt + 1,
                            "exception": type(e).__name__,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )
                    if attempt < retries - 1:
                        if on_retry is not None:
                            on_retry(attempt, e, *args, **kwargs)
                        time.sleep(delay)
            if last_exception:
                raise last_exception

        return wrapper

    return decorator
