#!/usr/bin/env python3
"""Date formatter for Allure reports.

This module provides functions to standardize date formats in Allure reports,
making them more readable and consistent.
"""

import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Handle imports properly for IDEs and runtime
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from ci.scripts.utils.constants import DATE_PATTERN_MM_DD_YYYY, ISO_TIMESTAMP_PATTERN  # noqa: E402
from ci.scripts.utils.file_utils import modify_file  # noqa: E402

# Set up logging
logger = logging.getLogger("allure-customizer.date-formatter")

# Global (module-level) settings
_dry_run = False


def set_dry_run(dry_run: bool) -> None:
    """Set dry run mode.

    Args:
        dry_run: Whether to perform operations in dry run mode
    """
    global _dry_run
    _dry_run = dry_run


def get_current_date_formatted() -> str:
    """Get current date in standard format.

    Returns:
        str: Current date in DD-MM-YYYY format
    """
    return datetime.now().strftime("%d-%m-%Y")


def format_timestamp(timestamp_ms: int) -> str:
    """Format timestamp to human-readable date.

    Args:
        timestamp_ms: Timestamp in milliseconds

    Returns:
        str: Formatted date string in DD-MM-YYYY format
    """
    # Convert milliseconds to seconds
    timestamp_sec = timestamp_ms / 1000
    # Convert to human-readable date
    date_str = datetime.fromtimestamp(timestamp_sec).strftime("%d-%m-%Y")
    return date_str


def _fix_mm_dd_yyyy_dates(content: str) -> str:
    """Fix MM/DD/YYYY date format to DD-MM-YYYY.

    Args:
        content: HTML or JS content with dates

    Returns:
        str: Content with dates fixed
    """
    # Find and fix patterns like "ALLURE REPORT 3/29/2025" in titles
    report_title_pattern = r"(ALLURE REPORT\s+)(\d{1,2})/(\d{1,2})/(\d{4})"
    content = re.sub(
        report_title_pattern, lambda m: f"{m.group(1)}{m.group(3)}-{m.group(2)}-{m.group(4)}", content, flags=re.IGNORECASE
    )

    # Fix other MM/DD/YYYY patterns
    return re.sub(
        DATE_PATTERN_MM_DD_YYYY,
        lambda m: f"{m.group(2)}-{m.group(1)}-{m.group(3)}",
        content,
    )


def _fix_iso_timestamps(content: str) -> str:
    """Fix ISO timestamps to DD-MM-YYYY.

    Args:
        content: Content with ISO timestamps

    Returns:
        str: Content with timestamps fixed
    """
    return re.sub(
        ISO_TIMESTAMP_PATTERN,
        lambda m: f"{m.group(3)}-{m.group(2)}-{m.group(1)}",
        content,
    )


def fix_html_title_tags(report_dir: str) -> None:
    """Fix date format in HTML title tags.

    Args:
        report_dir: Path to the Allure report directory
    """
    if _dry_run:
        logger.info("DRY RUN: Would fix HTML title tags")
        return

    # Find all HTML files
    for root, _, files in os.walk(report_dir):
        for file in files:
            if file.endswith(".html"):
                file_path = os.path.join(root, file)
                modify_file(file_path, _fix_mm_dd_yyyy_dates)


def _process_json_file(file_path: str) -> bool:
    """Process a single JSON file to fix timestamps.

    Args:
        file_path: Path to the JSON file

    Returns:
        bool: True if processing succeeded, False if an error occurred
    """
    try:
        modify_file(file_path, _fix_iso_timestamps)
        return True
    except Exception as e:
        logger.warning(f"Failed to process {file_path}: {str(e)}")
        return False


def _find_json_files(directory: str) -> list:
    """Find all JSON files in the given directory and subdirectories.

    Args:
        directory: Root directory to search

    Returns:
        list: List of paths to JSON files
    """
    json_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".json"):
                json_files.append(os.path.join(root, file))
    return json_files


def fix_json_timestamps(report_dir: str) -> None:
    """Fix timestamps in JSON files.

    Args:
        report_dir: Path to the Allure report directory
    """
    if _dry_run:
        logger.info("DRY RUN: Would fix JSON timestamps")
        return

    # Find all JSON files
    json_files = _find_json_files(report_dir)

    # Process each file
    success_count = 0
    for file_path in json_files:
        if _process_json_file(file_path):
            success_count += 1

    logger.info(f"Fixed timestamps in {success_count}/{len(json_files)} JSON files")


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
        if replacements and isinstance(replacements, dict):
            for key, value in replacements.items():
                content = content.replace(key, value)

        return content
    except Exception as e:
        logger.error(f"Error reading JavaScript file {script_path}: {str(e)}")
        return ""


def _load_formatter_code() -> str:
    """Load date formatter JavaScript code from external files.

    Returns:
        str: The JavaScript code for date formatting
    """
    # Get date formatter script from external file
    replacements = {"{VERSION}": "1.0.0"}  # Version can be updated as needed
    formatter_code = get_js_script_content("date_formatter.js", replacements)

    if not formatter_code:
        logger.warning("Could not load date formatter JavaScript, using inline version")
        # Fallback to inline version from inline_date_formatter.js
        formatter_code = get_js_script_content("inline_date_formatter.js", replacements)
        if not formatter_code:
            logger.error("Could not load any date formatter script")
            return ""

    return formatter_code


def _inject_script_to_html(file_path: str, formatter_code: str) -> bool:
    """Inject date formatter script into HTML file.

    Args:
        file_path: Path to the HTML file
        formatter_code: JavaScript code to inject

    Returns:
        bool: True if the file was modified, False otherwise
    """
    try:

        def inject_formatter_script(content):
            if "date-formatter-script" not in content:
                script_tag = f'<script id="date-formatter-script">\n{formatter_code}\n</script>'
                if "</head>" in content:
                    return content.replace("</head>", f"{script_tag}\n</head>")
                elif "<body" in content:
                    return content.replace("<body", f"{script_tag}\n<body")
                else:
                    return content + script_tag
            return content

        return modify_file(file_path, inject_formatter_script)
    except Exception as e:
        logger.warning(f"Failed to update HTML file {file_path}: {e}")
        return False


def fix_js_date_formats(report_dir: str) -> None:
    """Fix date formats in JavaScript files.

    Args:
        report_dir: Path to the Allure report directory
    """
    if _dry_run:
        logger.info("DRY RUN: Would fix JavaScript date formats")
        return

    # Load the formatter code
    formatter_code = _load_formatter_code()
    if not formatter_code:
        return

    # Find all HTML files and add the script
    count = 0
    for root, _, files in os.walk(report_dir):
        for file in files:
            if file.endswith(".html"):
                file_path = os.path.join(root, file)
                if _inject_script_to_html(file_path, formatter_code):
                    count += 1

    logger.info(f"Added date formatter script to {count} HTML files")


def fix_date_formats(report_dir: str) -> None:
    """Fix all date formats in HTML, JS, and JSON files.

    This is the main entry point for date formatting operations.

    Args:
        report_dir: Path to the Allure report directory
    """
    # Fix HTML titles
    fix_html_title_tags(report_dir)

    # Fix JS dates
    fix_js_date_formats(report_dir)

    # Fix JSON timestamps
    fix_json_timestamps(report_dir)

    # Special fix for the index.html title directly
    index_html_path = os.path.join(report_dir, "index.html")
    if os.path.exists(index_html_path):
        try:
            with open(index_html_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Fix the Allure Report title specifically
            modified_content = re.sub(
                r"(<title>.*?ALLURE\s+REPORT\s+)(\d{1,2})/(\d{1,2})/(\d{4})(.*?</title>)",
                r"\1\3-\2-\4\5",
                content,
                flags=re.IGNORECASE,
            )

            if content != modified_content:
                with open(index_html_path, "w", encoding="utf-8") as f:
                    f.write(modified_content)
                logger.info(f"Fixed date format in main title of {index_html_path}")
        except Exception as e:
            logger.warning(f"Failed to fix index.html title: {e}")

    logger.info("Date formats fixed")
