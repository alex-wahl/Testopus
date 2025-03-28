# Testopus

WARNING, the prototype is in development, testing, and back in development. For now, it is a concept.

A Python-based test automation framework combining Pytest, Selenium, Appium, Playwright, and AI/Google integrations under one roof. Streamline multi-platform testing with YAML-driven configs, POM architecture, and robust, extensible tooling.

## Running Tests

### Local Setup

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
pytest -k "login or registration" tests

# Run tests by marker
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
docker-compose -f docker/docker-compose.yml up

# Run with specific pytest arguments
docker-compose -f docker/docker-compose.yml run testopus pytest -v -k "test_login_with_invalid_credentials" tests

# Run and specify environment variables
docker-compose -f docker/docker-compose.yml run -e ENV=staging -e BROWSER=chrome testopus pytest tests
```

## Features

- Selenium Web UI Testing
- Pytest Integration
- Docker Support
- CI/CD with GitHub Actions
- Parallel Test Execution
- Cross-browser Testing with Selenium Grid
