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
        logger.info("DRY-RUN: Would add error handling scripts")
        return

    # Check if report directory exists
    if not os.path.exists(report_dir):
        logger.warning(f"Report directory not found at {report_dir}")
        return

    # Copy error handler JS file to the report directory
    _copy_error_handler_js(report_dir)

    # Create 404.html page for GitHub Pages
    _create_404_page(report_dir)
    
    # Create 401.html page for GitHub Pages
    _create_401_page(report_dir)

    # Add error handler script to index.html
    _add_error_handler_to_index(report_dir)

    logger.info("Added error handling scripts to Allure report")


def _copy_error_handler_js(report_dir: str) -> None:
    """Copy the error handler JavaScript to the report directory.

    Args:
        report_dir: The report directory path
    """
    # Get error handler JS content
    error_handler_js = get_js_script_content("error_handler.js")

    if not error_handler_js:
        logger.warning("Error handler JavaScript file not found")
        return

    # Write to the report directory
    js_path = os.path.join(report_dir, "error_handler.js")
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(error_handler_js)

    logger.info(f"Created error handler JS at {js_path}")


def _create_404_page(report_dir: str) -> None:
    """Create a 404.html page for GitHub Pages.

    Args:
        report_dir: The report directory path
    """
    # Get template path to 404 template
    template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
    template_path = os.path.join(template_dir, "404.html")

    # If template doesn't exist, create a fallback page
    if not os.path.exists(template_path):
        logger.warning(f"404 template not found at {template_path}, using fallback template")
        _create_fallback_404_page(report_dir)
        return

    # Read the template and write to report directory
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()

        error_page_path = os.path.join(report_dir, "404.html")
        with open(error_page_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Created 404 error page at {error_page_path}")
    except Exception as e:
        logger.error(f"Error creating 404 page: {str(e)}")
        _create_fallback_404_page(report_dir)


def _create_401_page(report_dir: str) -> None:
    """Create a 401.html page for GitHub Pages.

    Args:
        report_dir: The report directory path
    """
    # Get template path to 401 template
    template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
    template_path = os.path.join(template_dir, "401.html")

    # If template doesn't exist, create a fallback page
    if not os.path.exists(template_path):
        logger.warning(f"401 template not found at {template_path}, using fallback template")
        _create_fallback_401_page(report_dir)
        return

    # Read the template and write to report directory
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()

        error_page_path = os.path.join(report_dir, "401.html")
        with open(error_page_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Created 401 error page at {error_page_path}")
    except Exception as e:
        logger.error(f"Error creating 401 page: {str(e)}")
        _create_fallback_401_page(report_dir)


def _create_fallback_404_page(report_dir: str) -> None:
    """Create a simple fallback 404.html page when template is missing.

    Args:
        report_dir: The report directory path
    """
    # Get path to fallback template
    template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
    fallback_template_path = os.path.join(template_dir, "fallback_404.html")

    try:
        # Read the fallback template
        with open(fallback_template_path, "r", encoding="utf-8") as f:
            fallback_content = f.read()

        error_page_path = os.path.join(report_dir, "404.html")
        with open(error_page_path, "w", encoding="utf-8") as f:
            f.write(fallback_content)

        logger.info(f"Created fallback 404 error page at {error_page_path}")
    except Exception as e:
        logger.error(f"Critical error: Could not read fallback template: {str(e)}")
        logger.error(f"Cannot create 404 page without a valid template at {fallback_template_path}")
        raise RuntimeError(f"Failed to create 404 page: fallback template missing at {fallback_template_path}")


def _create_fallback_401_page(report_dir: str) -> None:
    """Create a simple fallback 401.html page when template is missing.

    Args:
        report_dir: The report directory path
    """
    # Simple HTML template for 401 page
    fallback_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>401 - Unauthorized</title>
    <style>body{font-family:sans-serif;text-align:center;padding:20px;}</style>
</head>
<body>
    <h1>401 - Unauthorized</h1>
    <p>You don't have permission to access this resource.</p>
    <p><a href="/">Go to Homepage</a></p>
</body>
</html>"""

    try:
        error_page_path = os.path.join(report_dir, "401.html")
        with open(error_page_path, "w", encoding="utf-8") as f:
            f.write(fallback_content)

        logger.info(f"Created fallback 401 error page at {error_page_path}")
    except Exception as e:
        logger.error(f"Error creating fallback 401 page: {str(e)}")


def _add_error_handler_to_index(report_dir: str) -> None:
    """Add error handler script to index.html.

    Args:
        report_dir: The report directory path
    """
    index_file = os.path.join(report_dir, "index.html")
    if not os.path.exists(index_file):
        logger.warning(f"index.html not found at {index_file}")
        return

    try:
        # Read the HTML file
        with open(index_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Add the script to the head section if not already present
        if 'src="error_handler.js"' not in content and "</head>" in content:
            script_tag = '<script src="error_handler.js"></script>'
            content = content.replace("</head>", script_tag + "</head>")

            with open(index_file, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info("Added error handler script to index.html")
        elif 'src="error_handler.js"' in content:
            logger.info("Error handler script already present in index.html")
        else:
            logger.warning("Could not find </head> in index.html")
    except Exception as e:
        logger.error(f"Failed to add error handler script to index.html: {str(e)}")
