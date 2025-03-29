#!/usr/bin/env python3
"""Cache control module for Allure report customization.

This module provides functions for adding cache control directives to Allure reports,
configuring caching behavior when reports are served via HTTP.
"""

import glob
import logging
import os
import sys
from pathlib import Path

# Set up Python path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

# Import modules from the project
from ci.scripts.utils.constants import CACHE_CONTROL_HEADERS, CACHE_CONTROL_META  # noqa: E402

# Set up logging
logger = logging.getLogger("allure-customizer.cache-control")

# Make script idempotent (safe to run multiple times)
DRY_RUN = False


def set_dry_run(dry_run: bool) -> None:
    """Set dry run mode.

    Args:
        dry_run: Whether to perform operations in dry run mode
    """
    global DRY_RUN
    DRY_RUN = dry_run


def create_nojekyll_file(report_dir: str) -> None:
    """Create .nojekyll file to prevent GitHub Pages from using Jekyll.

    Creates an empty .nojekyll file in the report directory to ensure GitHub Pages
    doesn't process the report files with Jekyll, preserving the original structure.

    Args:
        report_dir: Path to the Allure report directory.
    """
    if DRY_RUN:
        logger.info(f"DRY-RUN: Would create .nojekyll file in {report_dir}")
        return

    nojekyll_path = os.path.join(report_dir, ".nojekyll")
    open(nojekyll_path, "w").close()  # Create empty file
    logger.info(f"Created .nojekyll file at {nojekyll_path}")


def add_cache_control(report_dir: str) -> None:
    """Add cache control headers and meta tags.

    Adds cache control directives to ensure browsers don't cache the report pages:
    1. Creates a _headers file for Netlify and other static hosts
    2. Adds cache control meta tags to all HTML files

    Args:
        report_dir: Path to the Allure report directory.
    """
    if DRY_RUN:
        logger.info(f"DRY-RUN: Would add cache control to {report_dir}")
        return

    # Create _headers file for GitHub Pages
    headers_file = os.path.join(report_dir, "_headers")
    with open(headers_file, "w") as f:
        f.write(CACHE_CONTROL_HEADERS)
    logger.info(f"Created _headers file at {headers_file}")

    # Add cache control meta tags to HTML files
    html_files = glob.glob(os.path.join(report_dir, "**", "*.html"), recursive=True)
    fixed_count = 0

    for html_file in html_files:
        try:
            with open(html_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Check if cache meta tags already exist
            if '<meta http-equiv="Cache-Control"' not in content:
                cache_tags = f"<head>\n{CACHE_CONTROL_META}"
                new_content = content.replace("<head>", cache_tags)

                if new_content != content:
                    with open(html_file, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    fixed_count += 1
        except Exception as e:
            logger.error(f"Error adding cache control to {html_file}: {str(e)}")

    logger.info(f"Added cache control meta tags to {fixed_count} HTML files")


def get_spinner_css(templates_dir=None):
    """Get CSS for fixing spinner animations.

    Args:
        templates_dir: Directory containing templates (default: derived from module path)

    Returns:
        str: CSS content for fixing spinner animations
    """
    if templates_dir is None:
        templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")

    spinner_css_path = os.path.join(templates_dir, "spinner_fix.css")

    if not os.path.exists(spinner_css_path):
        logger.warning(f"Spinner CSS template not found at {spinner_css_path}")
        return """/* Ensure spinners don't stay visible indefinitely */
.spinner, .spinner_centered, [class*="spinner"] {
  animation-duration: 2s !important;
  animation-iteration-count: 1 !important;
}"""

    # Read the spinner CSS template
    try:
        with open(spinner_css_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.warning(f"Error reading spinner CSS template: {str(e)}")
        return ""


def remove_refresh_meta_tags(content):
    """Remove meta refresh tags from HTML content.

    Args:
        content: HTML content

    Returns:
        tuple: (Modified content, Whether content was modified)
    """
    if '<meta http-equiv="refresh"' in content:
        new_content = content.replace('<meta http-equiv="refresh"', "<!-- removed refresh -->")
        return new_content, new_content != content
    return content, False


def add_spinner_fix_styles(content, spinner_css):
    """Add CSS styles to fix spinner animations.

    Args:
        content: HTML content
        spinner_css: CSS content to add

    Returns:
        tuple: (Modified content, Whether content was modified)
    """
    if "</head>" in content and "spinner-fix-styles" not in content:
        spinner_style_block = f'<style id="spinner-fix-styles">\n{spinner_css}\n</style>\n</head>'
        new_content = content.replace("</head>", spinner_style_block)
        return new_content, new_content != content
    return content, False


def remove_problematic_elements(report_dir: str) -> None:
    """Remove elements that might cause loading or display issues.

    Fixes potential issues in the HTML files:
    1. Removes any refresh meta tags that might cause page redirects
    2. Adds CSS to fix spinner animations that might get stuck

    Args:
        report_dir: Path to the Allure report directory.
    """
    if DRY_RUN:
        logger.info(f"DRY-RUN: Would remove problematic elements from HTML files in {report_dir}")
        return

    # Load spinner fix CSS
    spinner_css = get_spinner_css()

    html_files = glob.glob(os.path.join(report_dir, "**", "*.html"), recursive=True)
    fixed_count = 0

    for html_file in html_files:
        try:
            with open(html_file, "r", encoding="utf-8") as f:
                content = f.read()

            modified = False

            # Remove meta refresh tags
            content, refresh_modified = remove_refresh_meta_tags(content)
            modified = modified or refresh_modified

            # Add CSS to ensure spinners don't stay visible
            content, spinner_modified = add_spinner_fix_styles(content, spinner_css)
            modified = modified or spinner_modified

            if modified:
                with open(html_file, "w", encoding="utf-8") as f:
                    f.write(content)
                fixed_count += 1

        except Exception as e:
            logger.error(f"Error fixing problematic elements in {html_file}: {str(e)}")

    logger.info(f"Removed problematic elements from {fixed_count} HTML files")
