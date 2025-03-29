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

**Usage:**
```bash
# Customize an existing report
python customize_allure_report.py [path_to_report_dir]

# Create a dummy report (when no test results are available)
python customize_allure_report.py --dummy

# Specify a branch name explicitly
python customize_allure_report.py --branch feature-branch

# Test changes without applying them
python customize_allure_report.py --dry-run
```

**Environment Variables:**
- `ALLURE_REPORT_DIR` - Path to report directory (default: reports/allure-report)
- `ALLURE_CREATE_DUMMY` - Create dummy report if "true" (default: "false")
- `ALLURE_BRANCH` - Branch name to use in report

## Documentation

The following documentation files provide detailed information about the CI/CD pipeline:

- `docs/github-actions.md` - Comprehensive guide to the GitHub Actions workflow configuration
- `docs/allure_customization_flow.md` - Visual diagram and explanation of the Allure report customization process

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