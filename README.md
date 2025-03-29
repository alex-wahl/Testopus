# Testopus

A Python-based test automation framework combining Pytest, Selenium, Appium, Playwright, and AI/Google integrations under one roof. Streamline multi-platform testing with YAML-driven configs, POM architecture, and robust, extensible tooling.

**Status**: Prototype in development

## Overview

Testopus is a unified test automation ecosystem that integrates multiple testing tools and frameworks. It's designed to provide a consistent interface for testing web and mobile applications across different platforms.

## Key Features

- **Multi-Framework Support**
  - Selenium for web UI testing
  - Playwright for modern browser automation
  - Appium for mobile testing (planned)
  - Pytest integration for test organization and execution

- **Project Architecture**
  - Page Object Model (POM) design pattern
  - YAML-driven configuration
  - Environment-specific settings
  - Robust and extensible UI interaction tooling

- **DevOps Integration**
  - Docker containerization
  - CI/CD with GitHub Actions workflow
  - Comprehensive test reporting

- **Developer Experience**
  - Hatch for environment management
  - Type checking with MyPy
  - Linting with Ruff
  - Code formatting with Black

## Project Structure

```
testopus/
├── core/                      # Core framework components
│   ├── ai/                    # AI integration components
│   ├── config/                # Configuration management
│   ├── pom/                   # Page Object Model implementation
│   │   └── web/               # Web-specific page objects
│   └── visual_testing/        # Visual testing components
├── config/                    # Configuration files
│   ├── env_settings/          # Environment-specific settings
│   ├── pydantic_models/       # Pydantic models for config validation
│   └── yaml_configs/          # YAML configuration files
├── docker/                    # Docker configuration
├── fixtures/                  # Pytest fixtures
├── tests/                     # Test suites
│   ├── api_tests/             # API test cases
│   ├── internal_tests/        # Framework internal tests
│   └── ui_tests/              # UI test cases
├── utils/                     # Utility functions
├── reports/                   # Test reports output directory
│   ├── html/                  # HTML test reports
│   ├── json/                  # JSON test reports
│   ├── custom/                # Custom format reports
│   ├── screenshots/           # Screenshots of failed tests
│   ├── allure-results/        # Allure report data
│   └── allure-report/         # Generated Allure reports
```

## Setup and Installation

### Prerequisites

- Python 3.12 or higher
- Chrome browser (for UI testing)
- [Allure Command Line Tool](https://docs.qameta.io/allure/#_installing_a_commandline) (optional, for Allure reports)

### Installation

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/testopus.git
   cd testopus
   ```

2. Use one of these installation methods:

#### Option 1: Using Hatch (Recommended)

Install [Hatch](https://hatch.pypa.io/) globally:
```bash
pip install hatch
```

Hatch will automatically create and manage virtual environments and dependencies.

#### Option 2: Traditional Virtual Environment

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package in development mode
pip install -e .
```

#### Option 3: Docker (For CI/CD or containerized execution)

Ensure Docker and Docker Compose are installed on your system.

## Running Tests

### Using Hatch (Recommended)

Hatch manages environments and dependencies for you, making it the easiest way to run tests:

```bash
# Run all tests
hatch run test:run

# Run UI web tests specifically
hatch run ui:web

# Run framework internal tests
hatch run test:internal

# Run tests with specific pytest arguments
hatch run test:run -v -k "test_email_field_is_accepting_email_addresses"
```

### Traditional Method

If you're using a traditional virtual environment:

```bash
# Activate virtual environment (if not already active)
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run all tests
pytest tests

# Run UI web tests specifically
pytest tests/ui_tests/web

# Run internal tests
pytest tests/internal_tests

# Run specific test file
pytest tests/ui_tests/web/gasag/test_gasag.py

# Run tests matching a keyword expression
pytest -k "test_email_field_is_accepting_email_addresses" tests
```

### Using Docker

```bash
# Build and run with Docker (runs all tests)
docker-compose -f docker/docker-compose.yml build
docker-compose -f docker/docker-compose.yml up --remove-orphans

# Run specific test types in Docker
docker-compose -f docker/docker-compose.yml run --rm testopus ui:web
docker-compose -f docker/docker-compose.yml run --rm testopus test:internal
```

## Test Report Generation

Testopus includes a comprehensive reporting system that provides detailed insights into test execution results.

### Available Report Types

1. **HTML Reports**: Detailed, browser-viewable reports with test results and statistics
2. **JSON Reports**: Machine-readable reports for data analysis or integration
3. **Screenshots**: Automatic captures of the browser state when tests fail
4. **Allure Reports**: Interactive, rich reports with detailed test execution information

### Generating Reports (Hatch Method)

```bash
# Run tests with Allure reporting
hatch run test:allure-report

# Run tests with HTML reporting
hatch run test:html-report

# Run tests with both Allure and HTML reporting
hatch run test:run-all-reports

# Generate an Allure report from existing results
hatch run test:generate-allure

# View Allure results directly (without generating a report)
hatch run test:view-allure

# View the latest HTML report in your browser
hatch run test:view-report
```

### Generating Reports (Traditional Method)

```bash
# Run tests with Allure reporting
pytest --alluredir=reports/allure-results tests

# Run tests with HTML reporting
pytest --html=reports/html/report.html --self-contained-html tests

# Generate an Allure report
allure generate reports/allure-results -o reports/allure-report --clean

# View Allure results directly
allure serve reports/allure-results
```

### Viewing Allure Reports

Allure reports provide a rich, interactive experience for analyzing test results.

```bash
# Generate the report (if not already generated)
allure generate reports/allure-results -o reports/allure-report --clean

# Open the report in your default browser
allure open reports/allure-report

# Or use the Hatch convenience commands
hatch run test:generate-allure  # Generate and open
hatch run test:view-allure      # View existing results
```

### Allure Reporting Fixtures

Testopus includes automatic fixtures that enhance Allure reporting without requiring any additional code:

1. **Automatic Screenshot Capture**: When a UI test fails, the framework automatically:
   - Identifies the WebDriver instance in use
   - Captures a screenshot at the point of failure
   - Attaches the screenshot to the Allure report
   - Saves the screenshot to the reports/screenshots directory

2. **Environment Information**: The framework automatically adds environment details:
   - Browser and version
   - Operating system
   - Python version
   - Test execution timestamp

3. **Test Metadata Extraction**: Information from test docstrings and pytest markers is automatically added to reports:
   - Test descriptions from docstrings
   - Feature, story, and severity markers
   - Tags and other metadata

These fixtures are located in `fixtures/allure.py` and are loaded automatically, requiring no manual configuration.

### Allure Report Features

Allure provides rich reporting with many features:

- Test categorization by severity, feature, and story
- Detailed test step tracking
- Attachments for test data and screenshots
- Environment information
- Test history tracking
- Filtering and searching capabilities

To leverage all these features, use Allure decorators in your tests:

```python
@allure.epic("User Management")
@allure.feature("Authentication")
@allure.story("Login")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("web", "smoke")
def test_login():
    with allure.step("Enter credentials"):
        # Test code
        allure.attach("username/password", "Credentials", allure.attachment_type.TEXT)
    
    with allure.step("Click login button"):
        # More test code
        
    with allure.step("Verify successful login"):
        # Verification
        assert True
```

### Report Locations

All reports are saved in the `reports/` directory with the following structure:

- **HTML Reports**: `reports/html/report.html`
- **JSON Reports**: `reports/json/report_TIMESTAMP.json`
- **Screenshots**: `reports/screenshots/TEST_NAME_TIMESTAMP.png`
- **Allure Results**: `reports/allure-results/`
- **Allure Reports**: `reports/allure-report/`

### Online Report Access

The latest Allure report is automatically published to GitHub Pages and can be viewed at:
- [https://alex-wahl.github.io/Testopus](https://alex-wahl.github.io/Testopus)

This site is updated automatically after each successful test run through CI/CD. The report includes:
- Test results summary
- Detailed test execution information
- Environment details
- Screenshots of failed tests
- Test history and trends

## Configuration

Tests can be configured using YAML files and command-line options.

### Command-Line Configuration

```bash
# Specify a configuration file
pytest --config # (is not used atm)

# Override configuration settings
pytest --override tests

# Specify a test framework
pytest --framework=selenium tests  # or --framework=playwright (is not used atm)

# Enable AI features (if available)
pytest --ai tests #  (is not used atm)
```

## Development Tools

### Code Quality Tools

```bash
# Format code with Black
hatch run format

# Run linting with Ruff
hatch run lint

# Run type checking with MyPy
hatch run typecheck
```

## Core Components

### Base Page

The BasePage class provides a comprehensive set of methods for interacting with web pages, including:

- Element interaction (clicks, text input, form handling)
- Waiting mechanisms (element presence, visibility, clickability)
- Information retrieval (text, attributes, values)
- State verification (existence, enabled/disabled status)
- Page management (navigation, JavaScript execution, screenshots)

### Configuration Management

The framework uses a layered configuration approach:

- Base configuration in YAML files
- Environment overrides
- CLI parameters for runtime configuration

## Advanced Features

### Retry Mechanism

Tests can use the @retry decorator to automatically retry flaky tests:

```python
@retry(retries=3, delay=2, on_retry=log_retry)
def test_login_with_invalid_credentials(self, login_page):
    # Test implementation
```

### Soft Assertions

Tests can use pytest_check for soft assertions that continue test execution after failures:

```python
check.is_in(expected_text, actual_text, "Text not found")
```

## CI/CD Integration

Testopus includes GitHub Actions workflow configuration for continuous integration:

- Automated testing on pushes and pull requests
- Matrix testing for different test suites
- Docker integration for consistent execution
- Caching to optimize build times
- Manual workflow triggering with custom parameters

For more details about the CI/CD setup and customization scripts, see the [CI documentation](ci/README.md).

## Extensibility

The framework is designed for extension:

- **New Page Objects**: Create new page classes extending BasePage
- **New Test Suites**: Add new directories under the appropriate test type
- **New Environments**: Define additional environments in pyproject.toml
- **New Integrations**: Add new directories under core/ for new capabilities

## Future Development

- Mobile testing with Appium
- AI-assisted test generation and debugging
- Visual testing enhancements
- Documentation generation with MkDocs

## Troubleshooting

### Common Issues

1. **ChromeDriver Version Mismatch**
   - Ensure your Chrome browser and ChromeDriver versions are compatible
   - You can specify a custom ChromeDriver path with the `CHROMEDRIVER_PATH` environment variable

2. **Headless Mode Issues**
   - For Docker or CI environments, the framework automatically uses headless mode
   - Set `DOCKER_ENV=true` to force headless mode

3. **Report Generation Failures**
   - Ensure the `reports` directory and its subdirectories exist
   - Check file permissions if reports aren't being saved

4. **Allure Command Not Found**
   - Install Allure command-line tools:
     - macOS: `brew install allure`
     - npm: `npm install -g allure-commandline`

5. **Pytest Plugin Conflicts**
   - If you experience empty Allure reports, there might be a conflict between the custom Testopus plugin and Allure plugin
   - Use the new direct Allure integration commands (e.g., `hatch run test:allure-report`) which bypass the custom plugin
   - The framework includes fixtures in `fixtures/allure.py` that provide the same functionality without conflicts

For more detailed documentation, see the docs directory or contact the project maintainers.

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## P.S.
The plan is to take neutral applications available in different countries, let's say the homepage of IKEA store or Wikipedia. Which will serve as a reference for creating their own test cases.