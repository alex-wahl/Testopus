#!/usr/bin/env python3
"""Error handling module for Allure report customization.

This module provides functions for handling errors and missing data in Allure reports,
ensuring the reports are resilient against broken links and missing resources.
"""

import logging
import os
import time
from typing import Dict, Optional

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


def add_cache_busting_to_scripts(report_dir: str) -> None:
    """Add cache-busting version parameter to JavaScript URLs.

    This ensures browsers always load the latest version of JavaScript files
    and don't use cached versions that might contain bugs.

    Args:
        report_dir: Path to the Allure report directory
    """
    if DRY_RUN:
        logger.info(f"DRY-RUN: Would add cache busting to scripts in {report_dir}")
        return

    # Find all HTML files
    html_files = []
    for root, _, files in os.walk(report_dir):
        for file in files:
            if file.endswith(".html"):
                html_files.append(os.path.join(root, file))

    if not html_files:
        logger.warning(f"No HTML files found in {report_dir}")
        return

    # Current timestamp for cache busting
    timestamp = str(int(time.time()))
    modified_count = 0

    # Process each HTML file
    for html_file in html_files:
        try:
            with open(html_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Find script tags with src attribute
            import re

            modified = False

            # Add version parameter to script src
            def add_version(match):
                nonlocal modified
                src = match.group(1)
                # Only add version to .js files
                if src.endswith(".js"):
                    # Add or update version parameter
                    if "?" in src:
                        if "v=" in src:
                            new_src = re.sub(r'v=[^&"\']+', f"v={timestamp}", src)
                        else:
                            new_src = f"{src}&v={timestamp}"
                    else:
                        new_src = f"{src}?v={timestamp}"
                    modified = True
                    return f'src="{new_src}"'
                return match.group(0)

            # Find and replace script src attributes
            new_content = re.sub(r'src="([^"]+)"', add_version, content)

            # Only write if modified
            if modified:
                with open(html_file, "w", encoding="utf-8") as f:
                    f.write(new_content)
                modified_count += 1

        except Exception as e:
            logger.error(f"Error adding cache busting to {html_file}: {str(e)}")

    logger.info(f"Added cache busting to scripts in {modified_count}/{len(html_files)} HTML files")


def setup_error_handling() -> None:
    """Set up error handling for the script.

    This function configures the basic error handling and logging
    for the script's execution.
    """
    # Configure basic exception handling
    logging.captureWarnings(True)
    logger.info("Error handling configured")


def get_js_script_content(script_name: str, replacements: Optional[Dict[str, str]] = None) -> str:
    """Get the content of a JavaScript file with optional replacements.

    Args:
        script_name: Name of the JavaScript file
        replacements: Dictionary of replacements to make in the script

    Returns:
        str: Content of the JavaScript file with replacements
    """
    script_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "js")
    script_path = os.path.join(script_dir, script_name)

    if not os.path.exists(script_path):
        logger.warning(f"JavaScript file not found: {script_path}")
        return ""

    try:
        with open(script_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Apply replacements
        if replacements:
            for key, value in replacements.items():
                content = content.replace(key, value)

        return content
    except Exception as e:
        logger.error(f"Error reading JavaScript file {script_path}: {str(e)}")
        return ""


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
        fix_404_script = get_js_script_content("fix_404_errors.js")

        if not fix_404_script:
            logger.warning("404 error handling JavaScript file not found, aborting")
            return

        # Read the HTML file
        with open(index_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Add the script to the head section
        if "</head>" in content:
            script_tag = '<script type="text/javascript" id="error-handler">\n{0}\n</script>'.format(fix_404_script)
            content = content.replace("</head>", script_tag + "</head>")

            with open(index_file, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info("Added 404 handling script to index.html")
        else:
            logger.warning("Could not find </head> in index.html")
    except Exception as e:
        logger.error("Failed to add 404 handling script: {0}".format(str(e)))
