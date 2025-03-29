# CI/CD Documentation for Testopus

This directory contains scripts, templates and configuration files used in the CI/CD pipeline for Testopus.

## Directory Structure

- `scripts/` - Python scripts for CI/CD operations
  - `templates/` - Template files used by scripts
    - `dummy_report.html` - HTML template for empty test reports
    - `cache_headers.html` - Cache control headers template
    - `spinner_fix.css` - CSS template for fixing spinner animations
    - `inline_date_formatter.js.template` - JavaScript template for date formatting
  - `js/` - JavaScript files for dynamic report modifications
    - `date_formatter.js` - Handles date format standardization
    - `branch_position.js` - Positions branch info in environment table
    - `inline_date_formatter.js` - Injected into app.js for fixing dynamic content
- `requirements.txt` - Python dependencies needed for CI/CD scripts

## Main CI/CD Workflow

The main CI/CD workflow is defined in `.github/workflows/test.yml` and follows these steps:

1. **Trigger Conditions:**
   - Pushes to main/master branches
   - Pull requests to main/master branches
   - Manual workflow dispatch with configurable parameters

2. **Environment Setup:**
   - Sets up Python 3.12
   - Installs Hatch package manager
   - Installs CI dependencies from `ci/requirements.txt`
   - Creates report directories

3. **Docker Setup:**
   - Sets up Docker Buildx for improved caching
   - Builds Docker image for tests
   - Uses layer caching to speed up builds

4. **Test Execution:**
   - Runs tests in Docker containers with selected test suite
   - Options include UI tests, API tests, internal tests, or all tests
   - Collects test results in multiple formats (Allure, HTML, JUnit)

5. **Report Generation:**
   - Generates Allure report from test results
   - Customizes reports with `customize_allure_report.py`
   - Creates dummy report if no tests were executed
   - Preserves all reports as artifacts

6. **Report Deployment:**
   - Deploys Allure report to GitHub Pages
   - Uses the 'reporting' branch for deployment
   - Adds PR comments with report links
   - Publishes test results to PR checks

## Local Code Quality Tools

The repository includes several tools to ensure code quality during local development, before code is pushed to the remote repository. For detailed information, see [Local Checks Documentation](docs/local-checks.md).

### Pre-commit Hooks

Pre-commit hooks run automatically before each commit to catch issues early in the development process.

#### Configuration

The hooks are configured in `.pre-commit-config.yaml` and include:

```yaml
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
    -   id: check-added-large-files

-   repo: https://github.com/psf/black
    rev: 25.1.0
    hooks:
    -   id: black
        files: ^ci/scripts/

-   repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
    -   id: isort
        args: ["--profile", "black"]
        files: ^ci/scripts/

-   repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
    -   id: flake8
        files: ^ci/scripts/
        args: ["--select=E9,F63,F7,F82", "--show-source", "--statistics", "--ignore=E402"]
        additional_dependencies: [flake8-docstrings]

-   repo: https://github.com/pycqa/pylint
    rev: v3.1.0
    hooks:
    -   id: pylint
        files: ^ci/scripts/
        args: ["--disable=all", "--enable=unused-import,unused-variable,unused-argument,undefined-variable"]

-   repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.9.0
    hooks:
    -   id: mypy
        files: ^ci/scripts/
        args: ["--ignore-missing-imports", "--namespace-packages", "--explicit-package-bases", "--config-file=mypy.ini"]
```

#### Installation and Usage

To set up pre-commit hooks:

```bash
# Install pre-commit hooks to run before each commit
pre-commit install

# Install pre-push hooks to run before each push
pre-commit install --hook-type pre-push

# Run hooks manually on all files
pre-commit run --all-files

# Run a specific hook
pre-commit run black
```

### Local CI Check Script

The `local_ci_check.sh` script provides a comprehensive check of code before pushing to the remote repository.

#### Script Workflow

1. **Tool Verification**: Checks if all required tools are installed:
   - black
   - isort
   - flake8
   - pylint
   - mypy

2. **Pre-commit Hook Installation**: Ensures pre-commit hooks are installed

3. **Code Quality Checks**:
   - Import sorting with isort
   - Code formatting with black
   - Linting with flake8
   - Static analysis with pylint
   - Type checking with mypy

4. **Test Execution**:
   - Runs unit tests
   - Generates test coverage reports
   - Outputs test coverage metrics

#### Usage

```bash
# Run all local CI checks
./local_ci_check.sh
```

### Integration with GitHub Actions

The same checks run in the local CI script are also configured in GitHub Actions workflows, ensuring consistent code quality standards between local development and CI/CD environments. Key differences include:

1. **Scope**: Local CI checks focus on the code you're currently working on, while GitHub Actions runs on the entire codebase
2. **Timing**: Local CI checks run before pushing, GitHub Actions runs after pushing
3. **Environment**: Local CI runs in your development environment, GitHub Actions runs in a fresh, isolated container

### Benefits of Local Quality Checks

- **Catch Issues Early**: Problems are identified before they enter the codebase
- **Consistent Style**: Ensures all code follows the same formatting and style guidelines
- **Reduce CI Failures**: Fixes issues before they cause CI pipeline failures
- **Improve Code Quality**: Static analysis catches potential bugs and anti-patterns
- **Save Time**: Immediate feedback rather than waiting for CI/CD pipeline results

## Scripts

### customize_allure_report.py

This is the main script for customizing Allure reports to ensure consistent formatting and improved usability. It follows CI/CD best practices with separation of concerns, using external templates for all HTML, CSS, and JavaScript.

**Features:**
- Date format standardization (MM/DD/YYYY → DD-MM-YYYY)
- Branch information inclusion in reports
- Cache-busting for ensuring fresh reports
- Fixes for dynamic content rendering
- Creation of dummy reports when no tests run
- GitHub Pages integration and optimization
- Test history preservation across runs (30-90 day trends)

**Usage:**
```bash
# Customize an existing report
python customize_allure_report.py [path_to_report_dir]

# Create a dummy report (when no test results are available)
python customize_allure_report.py --dummy

# Specify a branch name explicitly
python customize_allure_report.py --branch feature-branch

# Disable history preservation
python customize_allure_report.py --no-history

# Test changes without applying them
python customize_allure_report.py --dry-run
```

**Environment Variables:**
- `ALLURE_REPORT_DIR` - Path to report directory (default: reports/allure-report)
- `ALLURE_CREATE_DUMMY` - Create dummy report if "true" (default: "false")
- `ALLURE_BRANCH` - Branch name to use in report
- `ALLURE_PRESERVE_HISTORY` - Preserve test history if "true" (default: "true")

## Documentation

The following documentation files provide detailed information about the CI/CD pipeline:

- `docs/github-actions.md` - Comprehensive guide to the GitHub Actions workflow configuration
- `docs/allure_customization_flow.md` - Visual diagram and explanation of the Allure report customization process
- `docs/local-checks.md` - Detailed guide to local code quality checks, pre-commit hooks, and the local CI script

## Template Files

The script uses template files instead of embedding content directly in the code, following best practices for maintainability:

### HTML Templates
- `templates/dummy_report.html` - Template for the dummy report shown when no test results are available
- `templates/cache_headers.html` - Cache control headers to prevent browser caching

### CSS Templates
- `templates/spinner_fix.css` - Fixes for UI spinner animations that might get stuck

### JavaScript Templates
- `templates/inline_date_formatter.js.template` - Template for fixing date formats in dynamic content

## GitHub Actions Workflow Details

The workflow in `.github/workflows/test.yml` is designed for maximum flexibility and maintainability:

### Input Parameters
- `test_suite` - Select which test suite to run (all, ui, api, internal)
- `debug_mode` - Enable debug output in tests
- `custom_flags` - Pass additional flags to pytest

### CI/CD Optimizations
- Docker layer caching for faster builds
- Parallel job execution where possible
- Artifact retention policies to prevent storage bloat
- Efficient Docker image building with BuildX

### GitHub Integration
- Automatically comments on PRs with report links
- Publishes test results as PR checks
- Deploys reports to GitHub Pages for easy viewing
- Uses GitHub security permissions model

## Extending the CI/CD Pipeline

When adding new CI/CD components:

1. Place scripts in the appropriate directory (e.g., `scripts/` for Python scripts)
2. Extract all HTML, CSS and JavaScript to template files in the `templates/` directory
3. Use environment variables for configuration where possible
4. Update this README with documentation on new components
5. Update `requirements.txt` if new dependencies are required
6. Make scripts executable with `chmod +x` if they are meant to be run directly
7. Add new steps to the GitHub Actions workflow as needed
8. Follow the separation of concerns principle - keep code, templates, and configuration separate
