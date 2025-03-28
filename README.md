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
```

## Running Tests

### Local Setup with Hatch

[Hatch](https://hatch.pypa.io/) is used for managing the project environments and dependencies.

```bash
# Install Hatch if not already installed
pip install hatch

# Run tests in the test environment
hatch run test:run

# Run tests with coverage
hatch run test:cov

# Run internal tests
hatch run test:internal

# Run tests with specific pytest arguments
hatch run test:run -v -k "test_email_field_is_accepting_email_addresses or test_wordings"

# Enter a shell in the default environment
hatch shell

# Enter a shell in the test environment
hatch shell test
```

### Running Specific Test Types with Hatch

The project includes specialized environments for different test types:

```bash
# Run UI web tests
hatch run ui:web

# Run API tests (not developed atm)
hatch run api:run
```

### Development Tools with Hatch

Testopus includes Hatch scripts for development tasks:

```bash
# Format code with Black
hatch run format

# Run linting with Ruff
hatch run lint

# Run type checking with MyPy
hatch run typecheck
```

### Hatch Environment Management

Hatch environments are defined in `pyproject.toml`. The project includes these environments:

- `default`: Development environment with code formatting tools
- `test`: Testing environment with pytest and coverage tools
- `ui`: Environment for UI testing with web browsers
- `api`: Environment for API testing

You can add custom scripts to these environments in the `pyproject.toml` file:

```toml
[tool.hatch.envs.custom]
dependencies = [
  "your-dependencies",
]

[tool.hatch.envs.custom.scripts]
run-custom = "your-command {args}"
```

Then run your custom script with:

```bash
hatch run custom:run-custom
```

### Traditional Setup

```bash
# Setup virtual environment
python -m venv .venv
source .venv/bin/activate
pip install -e .

# Run all tests
pytest tests

# Run with verbose output
pytest -v tests

# Run specific test file
pytest tests/ui_tests/web/gasag/test_gasag.py

# Run tests matching a keyword expression
pytest -k "test_email_field_is_accepting_email_addresses or test_wordings" tests

# Run tests by marker (not implemented atm)
pytest -m smoke tests
```

### Common Pytest Parameters

```bash
# Run with detailed output (-v), print stdout (-s)
pytest -v -s tests

# Run specific test by keyword
pytest -k test_login_with_invalid_credentials tests/ui_tests/web/gasag/test_gasag.py

# Run with JUnit XML report
pytest --junitxml=results.xml tests
```

### Docker Setup

```bash
# Build and run with Docker (run all tests)
docker-compose -f docker/docker-compose.yml build
docker-compose -f docker/docker-compose.yml up --remove-orphans

# Run with specific test types in Docker
docker-compose -f docker/docker-compose.yml run --rm testopus ui:web
docker-compose -f docker/docker-compose.yml run --rm testopus api:run
docker-compose -f docker/docker-compose.yml run --rm testopus test:internal

# Run with specific pytest arguments
docker-compose -f docker/docker-compose.yml run --rm testopus test:run -v -k "test_login_with_invalid_credentials"

# Run and specify environment variables
docker-compose -f docker/docker-compose.yml run --rm -e ENV=staging -e BROWSER=chrome testopus test:run

# Clean up orphaned containers (if warning persists)
docker-compose -f docker/docker-compose.yml down --remove-orphans
```

## Core Components

### Base Page

The `BasePage` class provides a comprehensive set of methods for interacting with web pages, including:

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

Tests can use the `@retry` decorator to automatically retry flaky tests:

```python
@retry(retries=3, delay=2, on_retry=log_retry)
def test_login_with_invalid_credentials(self, login_page):
    # Test implementation
```

### Soft Assertions

Tests can use `pytest_check` for soft assertions that continue test execution after failures:

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

## Extensibility

The framework is designed for extension:

1. **New Page Objects**: Create new page classes extending `BasePage`
2. **New Test Suites**: Add new directories under the appropriate test type
3. **New Environments**: Define additional environments in `pyproject.toml`
4. **New Integrations**: Add new directories under `core/` for new capabilities

## Future Development

- Mobile testing with Appium
- AI-assisted test generation and debugging
- Visual testing enhancements
- Documentation generation with MkDocs

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## P.S. 

The plan is to take neutral applications available in different countries, let's say the homepage of IKEA store or Wikipedia.
Which will serve as a reference for creating their own test cases.