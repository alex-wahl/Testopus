# Testopus

WARNING, the prototype is in development, testing, and back in development. For now, it is a concept.

A Python-based test automation framework combining Pytest, Selenium, Appium, Playwright, and AI/Google integrations under one roof. Streamline multi-platform testing with YAML-driven configs, POM architecture, and robust, extensible tooling.

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
hatch run test:run -v -k "login or registration"

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

## Features

- Selenium Web UI Testing
- Pytest Integration
- Docker Support
- CI/CD with GitHub Actions
- Parallel Test Execution
- Cross-browser Testing with Selenium Grid
- Hatch Environment Management