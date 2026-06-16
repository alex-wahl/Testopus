from unittest.mock import MagicMock

import pytest

from core.drivers import factory
from core.drivers.base import BaseDriver, ElementHandle
from core.drivers.selenium_driver import SeleniumDriver, SeleniumElement


def test_selenium_driver_satisfies_protocol():
    assert isinstance(SeleniumDriver(MagicMock()), BaseDriver)


def test_selenium_element_satisfies_protocol():
    assert isinstance(SeleniumElement(MagicMock()), ElementHandle)


def test_create_driver_selenium(monkeypatch):
    sentinel = MagicMock()
    monkeypatch.setattr(factory, "_build_chrome", lambda: sentinel)
    drv = factory.create_driver("selenium")
    assert isinstance(drv, SeleniumDriver)
    assert drv.raw is sentinel


def test_create_driver_roadmap_framework_raises():
    with pytest.raises(NotImplementedError):
        factory.create_driver("playwright")


def test_create_driver_unknown_raises():
    with pytest.raises(ValueError):
        factory.create_driver("bogus")


def test_execute_script_unwraps_element_handle():
    raw_driver = MagicMock()
    drv = SeleniumDriver(raw_driver)
    handle = SeleniumElement(MagicMock(name="web_element"))
    drv.execute_script("return arguments[0];", handle)
    # The wrapped SeleniumElement must be unwrapped to its raw WebElement.
    raw_driver.execute_script.assert_called_once_with(
        "return arguments[0];", handle.raw
    )
