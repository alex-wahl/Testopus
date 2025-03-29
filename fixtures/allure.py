import pytest
import os
import sys
import time
import datetime
import allure
from pathlib import Path

# Make sure directories exist
@pytest.fixture(scope="session", autouse=True)
def setup_directories():
    """Set up report directories at the start of test session."""
    directories = [
        "reports/allure-results",
        "reports/html",
        "reports/screenshots",
    ]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

# Setup for HTML reports if using pytest-html
@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    """Add metadata to HTML reports."""
    # This runs if pytest-html is installed
    if hasattr(config, '_html'):
        # Add metadata to HTML report
        config._html.append_extra_html(f'<p>Test Run: {datetime.datetime.now()}</p>')
        config._html.environment = {
            'Python': sys.version,
            'Platform': sys.platform,
            'Pytest': pytest.__version__,
            'Timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

# Capture status for each test phase
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture test status for each phase (setup, call, teardown)."""
    outcome = yield
    report = outcome.get_result()
    
    # Store the test result for each phase
    setattr(item, f"report_{report.when}", report)

# Screenshot capture on test failure
@pytest.hookimpl(trylast=True)
def pytest_runtest_teardown(item):
    """Capture screenshot on test failure if driver is available."""
    if not hasattr(item, "report_call") or not item.report_call.failed:
        return
    
    # Try to find a webdriver instance
    driver = None
    for name in ["driver", "browser", "page", "selenium"]:
        try:
            driver = item.funcargs.get(name)
            if driver:
                break
        except:
            continue
    
    if not driver:
        return
        
    try:
        # Create timestamp and screenshot filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        test_name = item.nodeid.replace("/", "_").replace("::", "_")
        screenshot_path = f"reports/screenshots/{test_name}_{timestamp}.png"
        
        # Save screenshot
        driver.save_screenshot(screenshot_path)
        
        # Attach to Allure report
        with open(screenshot_path, "rb") as f:
            allure.attach(
                f.read(),
                name=f"Failure Screenshot",
                attachment_type=allure.attachment_type.PNG
            )
            
        print(f"Screenshot saved to {screenshot_path}")
    except Exception as e:
        print(f"Failed to capture screenshot: {e}")

# Add environment info to Allure report
@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session):
    """Add environment information to Allure report."""
    env_file = Path("reports/allure-results/environment.properties")
    
    # Get browser info if available
    browser_name = os.environ.get("BROWSER", "Chrome")
    browser_version = os.environ.get("BROWSER_VERSION", "latest")

    # Set timezone to Berlin
    os.environ['TZ'] = 'Europe/Berlin'
    time.tzset()  # Apply timezone change
    
    with open(env_file, "w") as f:
        f.write(f"Browser={browser_name}\n")
        f.write(f"Browser.Version={browser_version}\n")
        f.write(f"OS={sys.platform}\n")
        f.write(f"Python.Version={sys.version.split(' ')[0]}\n")
        f.write(f"Timestamp={datetime.datetime.now().isoformat()}\n")
        f.write(f"Timezone=Europe/Berlin\n")
        f.write(f"Timestamp={datetime.datetime.now().isoformat()}\n")

# Add additional metadata using Allure's API
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item):
    """Add additional metadata using Allure's API."""
    # Extract docstrings for test descriptions
    test_doc = item.function.__doc__ or ""
    if test_doc:
        allure.dynamic.description(test_doc)
    
    # Extract markers for Allure labels
    for marker in item.iter_markers():
        if marker.name == "feature":
            allure.dynamic.feature(marker.args[0])
        elif marker.name == "story":
            allure.dynamic.story(marker.args[0])
        elif marker.name == "severity":
            allure.dynamic.severity(marker.args[0])
        elif marker.name == "tag":
            for tag in marker.args:
                allure.dynamic.tag(tag)
    
    yield 