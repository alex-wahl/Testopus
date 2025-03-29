#!/usr/bin/env python3
"""Date formatter for Allure reports.

This module provides functions to standardize date formats in Allure reports,
making them more readable and consistent.
"""

import logging
import os
import re
from datetime import datetime

from utils.constants import DATE_PATTERN_MM_DD_YYYY, ISO_TIMESTAMP_PATTERN
from utils.file_utils import modify_file

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


def fix_json_timestamps(report_dir: str) -> None:
    """Fix timestamps in JSON files.

    Args:
        report_dir: Path to the Allure report directory
    """
    if _dry_run:
        logger.info("DRY RUN: Would fix JSON timestamps")
        return

    # Find all JSON files
    for root, _, files in os.walk(report_dir):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                try:
                    modify_file(file_path, _fix_iso_timestamps)
                except Exception as e:
                    logger.warning(f"Failed to process {file_path}: {str(e)}")


def _update_js_file_with_date_formatter(
    file_path: str, code: str, inline: bool = False
) -> bool:
    """Update JavaScript file with date formatter.

    Args:
        file_path: Path to the JavaScript file
        code: JavaScript code to insert
        inline: Whether to inline the code or add it separately

    Returns:
        bool: Whether the file was updated
    """
    logger.debug(f"Updating JavaScript file: {file_path}")

    def _modify_js(content: str) -> str:
        if inline:
            # For inline update, add the code at strategic locations
            if "Date.prototype.toDateString" in content:
                logger.debug("Date formatter already exists in JS file")
                return content

            # Check if file already has the date formatter
            if "function formatDate" in content:
                logger.debug("Date formatter function already exists")
                return content

            # Add before the first function declaration
            match = re.search(r"(function\s+\w+\s*\()", content)
            if match:
                pos = match.start()
                return content[:pos] + code + "\n\n" + content[pos:]

            # If no function found, add at the end
            return content + "\n\n" + code

        else:
            # For separate includes, check if it's already referenced
            if code.strip() in content:
                logger.debug("Date formatter already included")
                return content

            # Add as a separate script include at the head of the document
            return content

    return modify_file(file_path, _modify_js)


def fix_js_date_formats(report_dir: str) -> None:
    """Fix date formats in JavaScript files.

    Args:
        report_dir: Path to the Allure report directory
    """
    if _dry_run:
        logger.info("DRY RUN: Would fix JavaScript date formats")
        return

    # Get date formatter code
    formatter_code = """
// Custom date formatter
function formatDate(date) {
    if (!date) return '';
    if (typeof date === 'number') {
        date = new Date(date);
    }
    if (!(date instanceof Date)) {
        try {
            date = new Date(date);
        } catch (e) {
            return date;
        }
    }
    if (isNaN(date.getTime())) return date;

    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();

    return `${day}-${month}-${year}`;
}

// Override Date.prototype.toDateString to use our format
Date.prototype._originalToDateString = Date.prototype.toDateString;
Date.prototype.toDateString = function() {
    return formatDate(this);
};
"""

    # Find all JS files
    count = 0
    for root, _, files in os.walk(report_dir):
        for file in files:
            if file.endswith(".js"):
                file_path = os.path.join(root, file)
                try:
                    if _update_js_file_with_date_formatter(
                        file_path, formatter_code, inline=True
                    ):
                        count += 1
                except Exception as e:
                    logger.warning(f"Failed to update JavaScript file {file_path}: {e}")

    logger.info(f"Updated {count} JavaScript files with date formatter")


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

    logger.info("Date formats fixed")
