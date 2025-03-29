# CI/CD Scripts

This directory contains scripts and tools used in the CI/CD pipeline for Testopus.

## Directory Structure

- `scripts/` - Python scripts for CI/CD operations
  - `templates/` - Template files used by scripts
- `requirements.txt` - Python dependencies needed for CI/CD scripts

## Scripts

### customize_allure_report.py

Customizes the generated Allure reports with:
- Date format correction (MM/DD/YYYY → DD-MM-YYYY)
- Cache-busting mechanisms to ensure fresh reports
- Proper formatting for timestamps

Usage:
```bash
# Customize an existing report
python customize_allure_report.py [path_to_report_dir]

# Create a dummy report (when no test results are available)
python customize_allure_report.py [path_to_report_dir] --dummy
```

Default report directory is `reports/allure-report` if not specified.

The script also automatically creates a dummy report if the specified directory exists but is empty.

#### Template Files

- `templates/dummy_report.html` - HTML template for the dummy report shown when no test results are available.

## Extending

When adding new CI/CD scripts:

1. Place them in the appropriate directory (e.g., `scripts/` for Python scripts)
2. Update this README with documentation on the new script
3. Update `requirements.txt` if the script requires new dependencies
4. Make scripts executable with `chmod +x` if they are meant to be run directly
5. If the script uses templates, place them in the `scripts/templates/` directory 