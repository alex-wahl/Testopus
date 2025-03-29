import pytest
import os
import sys
import time
import datetime
import allure
import subprocess
from pathlib import Path

# Make sure directories exist
@pytest.fixture(scope="session", autouse=True)
def setup_directories():
    """Set up report directories at the start of test session.
    
    Creates the necessary directory structure for reports including
    allure-results, html reports, and screenshots.
    
    Returns:
        None
    """
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
    """Add metadata to HTML reports.
    
    Configures HTML report with additional metadata if pytest-html is installed.
    
    Args:
        config: The pytest config object.
        
    Returns:
        None
    """
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
    """Capture test status for each phase.
    
    Stores the test result for setup, call, and teardown phases
    as attributes on the test item.
    
    Args:
        item: The test item being executed.
        call: The call information.
        
    Yields:
        The hookwrapper.
    """
    outcome = yield
    report = outcome.get_result()
    
    # Store the test result for each phase
    setattr(item, f"report_{report.when}", report)

# Screenshot capture on test failure
@pytest.hookimpl(trylast=True)
def pytest_runtest_teardown(item):
    """Capture screenshot on test failure if driver is available.
    
    Attempts to find a webdriver instance and take a screenshot when
    a test fails, then attaches it to the Allure report.
    
    Args:
        item: The test item being torn down.
        
    Returns:
        None
    """
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
    """Add environment information to Allure report.
    
    Creates an environment.properties file containing browser, OS, Python version,
    and timestamp information for the Allure report.
    
    Args:
        session: The pytest session object.
        
    Returns:
        None
    """
    env_file = Path("reports/allure-results/environment.properties")
    
    # Get browser info if available
    browser_name = os.environ.get("BROWSER", "Chrome")
    browser_version = os.environ.get("BROWSER_VERSION", "latest")

    # Try to get branch info
    branch = os.environ.get('GITHUB_HEAD_REF', '')  # For pull requests
    if not branch:
        ref = os.environ.get('GITHUB_REF', '')      # For direct pushes
        if ref.startswith('refs/heads/'):
            branch = ref.replace('refs/heads/', '')
    
    if not branch:
        try:
            # Try to get from git command as fallback
            branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
                                           stderr=subprocess.DEVNULL).decode('utf-8').strip()
        except (subprocess.SubprocessError, FileNotFoundError):
            branch = 'unknown'

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
        f.write(f"Branch={branch}\n")

# Add additional metadata using Allure's API
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item):
    """Add additional metadata using Allure's API.
    
    Extracts test docstrings and pytest markers to populate Allure report
    with features, stories, severity levels, and tags.
    
    Args:
        item: The test item being executed.
        
    Yields:
        The hookwrapper.
    """
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