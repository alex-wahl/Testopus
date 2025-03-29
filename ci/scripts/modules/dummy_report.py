#!/usr/bin/env python3
"""Dummy report module for Allure report customization.

This module provides functions for creating a dummy report when no test results are available,
ensuring a fallback view for CI/CD pipelines with empty or missing test results.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Handle imports properly for IDEs and runtime
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from ci.scripts.modules.cache_control import add_cache_control, create_nojekyll_file  # noqa: E402
from ci.scripts.modules.date_formatter import get_current_date_formatted  # noqa: E402
from ci.scripts.utils.file_utils import ensure_dir_exists  # noqa: E402

# Set up logging
logger = logging.getLogger("allure-customizer.dummy-report")


def create_dummy_report(report_dir: str) -> None:
    """Create a dummy report when no test results are available.

    Generates a simple HTML report with current date information when no actual
    test results exist. This ensures CI/CD pipelines always have a report to display,
    even when tests failed to run or no tests were executed.

    Args:
        report_dir: Path to create the dummy report.
    """
    ensure_dir_exists(report_dir)

    # Create history directory
    history_dir = os.path.join(report_dir, "history")
    ensure_dir_exists(history_dir)

    # Create an empty history file to ensure directory is not empty
    with open(os.path.join(history_dir, "dummy-history.json"), "w", encoding="utf-8") as f:
        f.write('{"data": {"time": {"start": %d}}}' % int(datetime.now().timestamp() * 1000))

    today = get_current_date_formatted()

    # Get the template file path
    template_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "templates",
        "dummy_report.html",
    )

    # Check if template exists
    if not os.path.exists(template_path):
        logger.warning(f"Template file not found at {template_path}, creating a minimal version...")

        # Create the template directory if it doesn't exist
        template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
        ensure_dir_exists(template_dir)

        # Create a minimal fallback template if we can't find the real one
        minimal_template = f"""<!DOCTYPE html>
<html>
<head><title>ALLURE REPORT {today}</title></head>
<body>
  <h1>ALLURE REPORT {today}</h1>
  <p>No test results available. Template file missing.</p>
  <p>Generated on: {datetime.now().strftime("%d-%m-%Y %H:%M:%S")}</p>
</body>
</html>"""

        with open(template_path, "w", encoding="utf-8") as f:
            f.write(minimal_template)
        logger.info(f"Created minimal fallback template at {template_path}")
        logger.warning(f"Please restore the proper template at {template_path} for better formatting")

    # Read the template file
    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()

    # Replace placeholders with values
    timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    dummy_html = template_content.replace("{today}", today).replace("{timestamp}", timestamp)

    # Write the HTML to index.html
    with open(os.path.join(report_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(dummy_html)

    # Create cache control files
    add_cache_control(report_dir)
    create_nojekyll_file(report_dir)

    logger.info("Created dummy report")
