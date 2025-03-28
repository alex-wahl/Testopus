import functools
import time
from typing import Any, List, Optional, Tuple, Union

from selenium.common.exceptions import (ElementNotVisibleException,
                                        NoSuchElementException,
                                        TimeoutException)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait


class BasePage:
    TITLE = "head > title"
    TAG_NAME = "body"
    DEFAULT_TIMEOUT = 3  # Default timeout for element interactions
    PAGE_LOAD_TIMEOUT = 10  # Longer timeout for page loads

    def __init__(self, driver: WebDriver, url: str):
        self.driver = driver
        self.driver.get(url)

    def _wait(self, condition: Any, timeout: Optional[int] = None) -> Any:
        """Wait for a condition to be true.
        
        Args:
            condition (Any): The expected condition to wait for.
            timeout (int, optional): Time to wait in seconds.
            
        Returns:
            Any: The element if found.
            
        Raises:
            TimeoutException: If element is not found within timeout.
        """
        timeout = timeout or self.DEFAULT_TIMEOUT
        return WebDriverWait(self.driver, timeout).until(condition)

    def wait_until_page_is_fully_loaded(self, locator: Optional[Tuple[str, str]] = None) -> None:
        """Wait for the page to be fully loaded by checking for a specific element.
        
        Args:
            locator (Tuple[str, str], optional): The element locator to wait for.
        """
        if locator is None:
            locator = (By.TAG_NAME, self.TAG_NAME)
        
        # First wait for document ready state
        try:
            self._wait(
                lambda driver: driver.execute_script("return document.readyState") == "complete",
                timeout=self.PAGE_LOAD_TIMEOUT
            )
        except TimeoutException:
            # Continue anyway, as sometimes readyState doesn't reach complete
            pass
            
        # Then wait for specific element
        self._wait(EC.presence_of_element_located(locator), timeout=self.PAGE_LOAD_TIMEOUT)
    
    def wait_for_element(self, locator: Tuple[str, str], timeout: int = 3) -> WebElement:
        """Wait for element to be present in the DOM with retry mechanism.
        
        Args:
            locator (Tuple[str, str]): The element locator.
            timeout (int, optional): Time to wait in seconds. Defaults to 3.
            
        Returns:
            WebElement: The found element.
        """
        start_time = time.time()
        last_exception = None
        
        # Add short retry mechanism to handle stale element issues
        while time.time() - start_time < timeout:
            try:
                return self._wait(EC.presence_of_element_located(locator), timeout=1)
            except Exception as e:
                last_exception = e
                time.sleep(0.5)
        
        if last_exception:
            raise last_exception
        
        # If we made it here without an exception but also without returning, raise a timeout
        raise TimeoutException(f"Timed out waiting for element {locator} to be present")

    def wait_for_element_visible(self, locator: Tuple[str, str], timeout: int = 3) -> WebElement:
        """Wait for element to be visible on the page.
        
        Args:
            locator (Tuple[str, str]): The element locator.
            timeout (int, optional): Time to wait in seconds. Defaults to 3.
            
        Returns:
            WebElement: The visible element.
        """
        return self._wait(EC.visibility_of_element_located(locator), timeout)

    def wait_for_element_clickable(self, locator: Tuple[str, str], timeout: int = 3) -> WebElement:
        """Wait for element to be clickable.
        
        Args:
            locator (Tuple[str, str]): The element locator.
            timeout (int, optional): Time to wait in seconds. Defaults to 3.
            
        Returns:
            WebElement: The clickable element.
        """
        return self._wait(EC.element_to_be_clickable(locator), timeout)
    
    def wait_for_text_present(self, locator: Tuple[str, str], text: str, timeout: int = 3) -> bool:
        """Wait for specific text to be present in the element.
        
        Args:
            locator (Tuple[str, str]): The element locator.
            text (str): The text to wait for.
            timeout (int, optional): Time to wait in seconds. Defaults to 3.
            
        Returns:
            bool: True if text is present.
        """
        return self._wait(EC.text_to_be_present_in_element(locator, text), timeout)
    
    def wait_for_element_to_disappear(self, locator: Tuple[str, str], timeout: int = 3) -> bool:
        """Wait for element to disappear from DOM or become invisible.
        
        Args:
            locator (Tuple[str, str]): The element locator.
            timeout (int, optional): Time to wait in seconds. Defaults to 3.
            
        Returns:
            bool: True if element disappeared.
        """
        return self._wait(EC.invisibility_of_element_located(locator), timeout)

    def simple_click(self, element: WebElement) -> None:
        """Perform a standard Selenium click on an element.
        
        Args:
            element (WebElement): The element to click.
        """
        element.click()
    
    def js_click(self, element: WebElement) -> None:
        """Click an element using JavaScript.
        
        Args:
            element (WebElement): The element to click.
        """
        self.driver.execute_script("arguments[0].click();", element)
    
    def safe_click(self, locator: Tuple[str, str], timeout: int = None) -> None:
        """Click on an element with retry mechanism and automatic strategy selection.
        
        Args:
            locator (Tuple[str, str]): The element locator.
            timeout (int, optional): Time to wait in seconds.
            
        Raises:
            ElementNotVisibleException: If element is not clickable.
        """
        timeout = timeout or self.DEFAULT_TIMEOUT
        start_time = time.time()
        last_exception = None
        
        while time.time() - start_time < timeout:
            try:
                element = self.wait_for_element_visible(locator, timeout=1)
                
                # Try regular click first
                try:
                    self.simple_click(element)
                    return
                except Exception:
                    # If regular click fails, try JavaScript click
                    self.js_click(element)
                    return
                    
            except Exception as e:
                last_exception = e
                time.sleep(0.5)
        
        if last_exception:
            raise ElementNotVisibleException(f"Element {locator} not clickable after multiple attempts: {str(last_exception)}")
    
    def click(self, locator: Tuple[str, str], timeout: int = None) -> None:
        """Click on an element with retry mechanism for stale elements and interruptions.
        
        This is maintained for backward compatibility, now calls safe_click().
        
        Args:
            locator (Tuple[str, str]): The element locator.
            timeout (int, optional): Time to wait in seconds.
        """
        self.safe_click(locator, timeout)

    def clear_field(self, element: WebElement) -> None:
        """Clear the contents of an input field.
        
        Args:
            element (WebElement): The input field to clear.
        """
        try:
            element.clear()
        except Exception:
            # If standard clear fails, use JavaScript
            self.driver.execute_script("arguments[0].value = '';", element)
    
    def simple_input(self, element: WebElement, text: str) -> None:
        """Enter text in an input field using standard Selenium method.
        
        Args:
            element (WebElement): The input field element.
            text (str): The text to enter.
        """
        element.send_keys(text)
    
    def js_input(self, element: WebElement, text: str) -> None:
        """Enter text in an input field using JavaScript.
        
        Args:
            element (WebElement): The input field element.
            text (str): The text to enter.
        """
        self.driver.execute_script(f"arguments[0].value = '{text}';", element)
    
    def safe_input(self, locator: Tuple[str, str], text: str, timeout: int = None) -> None:
        """Enter text in an input field with retry mechanism and validation.
        
        Args:
            locator (Tuple[str, str]): The input field locator.
            text (str): The text to enter.
            timeout (int, optional): Time to wait in seconds.
            
        Raises:
            NoSuchElementException: If the element is not found after retries.
        """
        timeout = timeout or self.DEFAULT_TIMEOUT
        start_time = time.time()
        last_exception = None
        
        while time.time() - start_time < timeout:
            try:
                element = self.wait_for_element_visible(locator, timeout=1)
                
                # Try standard approach first
                try:
                    self.clear_field(element)
                    self.simple_input(element, text)
                    
                    # Verify the text was entered correctly
                    input_value = element.get_attribute("value")
                    if input_value == text:
                        return
                    
                    # If verification fails, try JavaScript approach
                    self.js_input(element, text)
                    return
                    
                except Exception:
                    # If standard approach fails, use JavaScript
                    self.clear_field(element)
                    self.js_input(element, text)
                    return
                    
            except Exception as e:
                last_exception = e
                time.sleep(0.5)
        
        if last_exception:
            raise NoSuchElementException(f"Could not fill text in {locator} after multiple attempts: {str(last_exception)}")
    
    def fill_text(self, locator: Tuple[str, str], text: str) -> None:
        """Enter text in an input field with retry mechanism.
        
        This is maintained for backward compatibility, now calls safe_input().
        
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
        return self.driver.find_element(By.CSS_SELECTOR, self.TITLE).text

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
        self._wait(EC.alert_is_present()).accept()
        
    def take_screenshot(self, filename: str) -> None:
        """Take a screenshot of the current page.
        
        Args:
            filename (str): The path to save the screenshot.
        """
        self.driver.save_screenshot(filename)
    
    # Form interactions
    def select_dropdown_option(self, locator: Tuple[str, str], option_text: str) -> None:
        """Select an option from a dropdown by visible text.
        
        Args:
            locator (Tuple[str, str]): The dropdown element locator.
            option_text (str): The visible text of the option to select.
            
        Raises:
            NoSuchElementException: If dropdown or option cannot be found.
        """
        try:
            element = self.wait_for_element_visible(locator)
            Select(element).select_by_visible_text(option_text)
        except (TimeoutException, NoSuchElementException) as e:
            raise NoSuchElementException(f"Could not select option '{option_text}' from {locator}: {str(e)}")
    
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
            raise NoSuchElementException(f"Could not {'check' if check else 'uncheck'} checkbox {locator}: {str(e)}")
    
    def get_attribute(self, locator: Tuple[str, str], attribute: str) -> str:
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
            raise NoSuchElementException(f"Could not get attribute '{attribute}' from {locator}: {str(e)}")
    
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
    
    # Advanced interactions
    def hover(self, locator: Tuple[str, str]) -> None:
        """Hover over an element.
        
        Args:
            locator (Tuple[str, str]): The element locator to hover over.
            
        Raises:
            ElementNotVisibleException: If element cannot be found or hovered.
        """
        try:
            element = self.wait_for_element_visible(locator)
            ActionChains(self.driver).move_to_element(element).perform()
        except (TimeoutException, NoSuchElementException) as e:
            raise ElementNotVisibleException(f"Could not hover over element {locator}: {str(e)}")
    
    def drag_and_drop(self, source_locator: Tuple[str, str], target_locator: Tuple[str, str]) -> None:
        """Drag and drop an element.
        
        Args:
            source_locator (Tuple[str, str]): The source element locator.
            target_locator (Tuple[str, str]): The target element locator.
            
        Raises:
            ElementNotVisibleException: If elements cannot be found or dragged.
        """
        try:
            source = self.wait_for_element_visible(source_locator)
            target = self.wait_for_element_visible(target_locator)
            ActionChains(self.driver).drag_and_drop(source, target).perform()
        except (TimeoutException, NoSuchElementException) as e:
            raise ElementNotVisibleException(f"Could not perform drag and drop: {str(e)}")
    
    def double_click(self, locator: Tuple[str, str]) -> None:
        """Double click on an element.
        
        Args:
            locator (Tuple[str, str]): The element locator to double click on.
            
        Raises:
            ElementNotVisibleException: If element cannot be found or double-clicked.
        """
        try:
            element = self.wait_for_element_clickable(locator)
            ActionChains(self.driver).double_click(element).perform()
        except (TimeoutException, NoSuchElementException) as e:
            raise ElementNotVisibleException(f"Could not double click on element {locator}: {str(e)}")
    
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

    def get_input_value(self, locator: tuple) -> str:
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
        try:
            return self._wait(
                lambda driver: driver.current_url != original_url,
                timeout
            )
        except TimeoutException:
            return False

    def wait_for_url_contains(self, url_substring: str, timeout: int = 10) -> bool:
        """Wait for the URL to contain a specific substring.
        
        Args:
            url_substring (str): The substring to wait for in the URL.
            timeout (int, optional): Time to wait in seconds. Defaults to 10.
            
        Returns:
            bool: True if substring found in URL, False otherwise.
        """
        try:
            return self._wait(
                EC.url_contains(url_substring),
                timeout
            )
        except TimeoutException:
            return False

    def find_element(self, locator: Tuple[str, str]) -> WebElement:
        """Find an element.
        
        Args:
            locator (Tuple[str, str]): The element locator.
        """
        return self.driver.find_element(*locator)

def retry(retries=3, delay=1, exceptions=(Exception,), on_retry=None):
    """Retry decorator for functions that might fail temporarily.
    
    Args:
        retries: Number of retry attempts. Default is 3.
        delay: Delay between retries in seconds. Default is 1.
        exceptions: Exceptions to catch and retry. Default is all exceptions.
        on_retry: Optional callback function to execute between retries.
            The callback receives (attempt, exception, *args, **kwargs).
        
    Returns:
        The decorated function.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < retries - 1:
                        if on_retry is not None:
                            on_retry(attempt, e, *args, **kwargs)
                        time.sleep(delay)
            if last_exception:
                raise last_exception
        return wrapper
    return decorator