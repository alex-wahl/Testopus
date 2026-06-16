from __future__ import annotations

import os
from typing import Any, Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from core.drivers.base import BaseDriver
from core.drivers.selenium_driver import SeleniumDriver

SUPPORTED_FRAMEWORKS = ("selenium",)
ROADMAP_FRAMEWORKS = ("playwright", "appium")


def _build_chrome() -> webdriver.Chrome:
    """Build a Chrome WebDriver, honoring DOCKER_ENV / CHROME_BIN / CHROMEDRIVER_PATH."""
    options = Options()
    if os.environ.get("DOCKER_ENV") == "true":
        options.add_argument("--headless=new")
        if os.environ.get("CHROME_BIN"):
            options.binary_location = os.environ["CHROME_BIN"]

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    chrome_driver_path = os.environ.get("CHROMEDRIVER_PATH")
    if chrome_driver_path and os.path.exists(chrome_driver_path):
        return webdriver.Chrome(
            options=options, service=Service(executable_path=chrome_driver_path)
        )
    return webdriver.Chrome(options=options)


def create_driver(framework: str = "selenium", config: Optional[Any] = None) -> BaseDriver:
    """Create a :class:`BaseDriver` for the requested framework.

    Only ``selenium`` is implemented today. ``playwright`` / ``appium`` are on the
    roadmap and raise ``NotImplementedError`` so an unsupported ``--framework`` fails
    loudly instead of silently running Selenium.

    :param framework: The framework name (default ``selenium``).
    :param config: Reserved for future per-framework options.
    :raises NotImplementedError: For a known-but-unbuilt framework.
    :raises ValueError: For an unknown framework name.
    """
    name = (framework or "selenium").lower()
    if name == "selenium":
        return SeleniumDriver(_build_chrome())
    if name in ROADMAP_FRAMEWORKS:
        raise NotImplementedError(
            f"Framework '{name}' is on the roadmap but not yet implemented; "
            f"supported frameworks: {', '.join(SUPPORTED_FRAMEWORKS)}."
        )
    raise ValueError(
        f"Unknown framework '{framework}'. Supported: {', '.join(SUPPORTED_FRAMEWORKS)}."
    )
