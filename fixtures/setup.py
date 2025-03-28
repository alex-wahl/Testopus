import os

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


@pytest.fixture
def driver():
    options = Options()
    # Configure headless mode for Docker
    if os.environ.get('DOCKER_ENV') == 'true':
        options.add_argument("--headless=new")
        # Use Chromium binary path if specified
        if os.environ.get('CHROME_BIN'):
            options.binary_location = os.environ.get('CHROME_BIN')
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    # Use ChromeDriver from path if specified
    chrome_driver_path = os.environ.get('CHROMEDRIVER_PATH')
    if chrome_driver_path and os.path.exists(chrome_driver_path):
        service = Service(executable_path=chrome_driver_path)
        driver = webdriver.Chrome(options=options, service=service)
    else:
        driver = webdriver.Chrome(options=options)
        
    yield driver
    driver.quit()