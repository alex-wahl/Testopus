#!/usr/bin/env python3
"""Error handling module for Allure report customization.

This module provides functions for handling errors and missing data in Allure reports,
ensuring the reports are resilient against broken links and missing resources.
"""

import logging
import os

# Set up logging
logger = logging.getLogger("allure-customizer.error-handling")

# Make script idempotent (safe to run multiple times)
DRY_RUN = False


def set_dry_run(dry_run: bool) -> None:
    """Set dry run mode.

    Args:
        dry_run: Whether to perform operations in dry run mode
    """
    global DRY_RUN
    DRY_RUN = dry_run


def setup_error_handling() -> None:
    """Set up error handling for the script.

    This function configures the basic error handling and logging
    for the script's execution.
    """
    # Configure basic exception handling
    logging.captureWarnings(True)
    logger.info("Error handling configured")


def fix_missing_test_results(report_dir: str) -> None:
    """Add JavaScript to handle 404 errors when test results are missing.

    Adds a JavaScript handler to the index.html file that gracefully handles missing
    test results by displaying a custom error message instead of failing with a 404 error.
    This improves the user experience when viewing reports with incomplete data.

    Args:
        report_dir: Path to the Allure report directory.
    """
    if DRY_RUN:
        logger.info("DRY-RUN: Would add 404 handling script to index.html")
        return

    index_file = os.path.join(report_dir, "index.html")
    if not os.path.exists(index_file):
        logger.warning("index.html not found at {0}".format(index_file))
        return

    try:
        # Load 404 error handling JavaScript from external file
        js_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "js"
        )
        fix_404_js_path = os.path.join(js_dir, "fix_404_errors.js")

        if not os.path.exists(fix_404_js_path):
            logger.warning(
                "404 error handling JavaScript file not found at {0}".format(
                    fix_404_js_path
                )
            )
            return

        # Read the file
        with open(fix_404_js_path, "r", encoding="utf-8") as f:
            fix_404_script = f.read()

        # Read the HTML file
        with open(index_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Add the script to the head section
        if "</head>" in content:
            script_tag = '<script type="text/javascript">\n{0}\n</script>'.format(
                fix_404_script
            )
            content = content.replace("</head>", script_tag + "</head>")

            with open(index_file, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info("Added 404 handling script to index.html")
        else:
            logger.warning("Could not find </head> in index.html")
    except Exception as e:
        logger.error("Failed to add 404 handling script: {0}".format(str(e)))
