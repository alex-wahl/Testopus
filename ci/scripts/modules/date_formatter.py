#!/usr/bin/env python3
"""Date formatter module for Allure report customization.

This module provides functions for standardizing date formats in Allure reports,
ensuring consistent date presentation across all report elements.
"""

import os
import re
import glob
import logging
from datetime import datetime
from pathlib import Path
from typing import List

# Handle both relative imports for package usage and direct imports for script execution
try:
    from ..utils.constants import ISO_TIMESTAMP_PATTERN, VERSION
    from ..utils.file_utils import read_file, write_file, find_files
except ImportError:
    # When run directly
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from utils.constants import ISO_TIMESTAMP_PATTERN, VERSION
    from utils.file_utils import read_file, write_file, find_files

# Set up logging
logger = logging.getLogger("allure-customizer.date-formatter")

# Make script idempotent (safe to run multiple times)
DRY_RUN = False


def set_dry_run(dry_run: bool) -> None:
    """Set dry run mode.

    Args:
        dry_run: Whether to perform operations in dry run mode
    """
    global DRY_RUN
    DRY_RUN = dry_run


def get_current_date_formatted() -> str:
    """Get current date in DD-MM-YYYY format.

    Returns:
        str: Current date formatted as DD-MM-YYYY.
    """
    return datetime.now().strftime("%d-%m-%Y")


def fix_html_title_tags(report_dir: str) -> None:
    """Fix date format in HTML title tags.

    Standardizes dates in HTML files to use DD-MM-YYYY format:
    - Updates title tags
    - Updates visible date text in the content
    - Adds dynamic JavaScript to ensure consistency

    Args:
        report_dir: Path to the Allure report directory.
    """
    today = get_current_date_formatted()

    if DRY_RUN:
        logger.info(f"DRY-RUN: Would update HTML title tags with date {today}")
        return

    html_files = glob.glob(os.path.join(report_dir, "**", "*.html"), recursive=True)
    updated_count = 0

    for html_file in html_files:
        try:
            with open(html_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Fix HTML title tag
            new_content = re.sub(
                r"<title>(?:Allure Report|ALLURE REPORT)(?:\s+\d{1,2}[-/]\d{1,2}[-/]\d{4})?</title>",
                f"<title>ALLURE REPORT {today}</title>",
                content,
            )

            # Fix visible title in the HTML content - more specific pattern matching
            # Match both MM/DD/YYYY and DD-MM-YYYY formats
            date_patterns = [
                # Match "ALLURE REPORT MM/DD/YYYY" format seen in screenshot
                r"(ALLURE\s+REPORT\s+)(\d{1,2})/(\d{1,2})/(\d{4})",
                # Also match other possible formats
                r"(ALLURE\s+REPORT\s+)(\d{1,2})-(\d{1,2})-(\d{4})",
                r"(Allure\s+Report\s+)(\d{1,2})/(\d{1,2})/(\d{4})",
                r"(Allure\s+Report\s+)(\d{1,2})-(\d{1,2})-(\d{4})",
            ]

            for pattern in date_patterns:
                # Replace with the correct DD-MM-YYYY format
                # Group 2 is the month, 3 is the day, 4 is the year in the regex
                new_content = re.sub(
                    pattern,
                    lambda m: (
                        f"{m.group(1)}{m.group(3)}-{m.group(2)}-{m.group(4)}"
                        if len(m.groups()) >= 4
                        else f"{m.group(1)}{today}"
                    ),
                    new_content,
                    flags=re.IGNORECASE,
                )

            # Find and fix the main header date format from the screenshot
            # Direct replacement for the exact format from the screenshot
            main_pattern = r"(ALLURE REPORT )(\d)/(\d{2})/(\d{4})"
            new_content = re.sub(
                main_pattern,
                lambda m: f"{m.group(1)}{m.group(3)}-0{m.group(2)}-{m.group(4)}",
                new_content,
            )

            # Try with full month number
            main_pattern2 = r"(ALLURE REPORT )(\d{2})/(\d{2})/(\d{4})"
            new_content = re.sub(
                main_pattern2,
                lambda m: f"{m.group(1)}{m.group(3)}-{m.group(2)}-{m.group(4)}",
                new_content,
            )

            # Inject JavaScript for SPA interfaces like the one in the screenshot
            if html_file.endswith("index.html"):
                logger.info(
                    f"Processing index.html, injecting dynamic content fix script"
                )

                # Load date formatter JavaScript from external file
                js_dir = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "js"
                )
                date_js_path = os.path.join(js_dir, "date_formatter.js")

                if os.path.exists(date_js_path):
                    # Remove any existing date formatting scripts
                    new_content = re.sub(
                        r"<script>\s*//\s*(?:Date format standardization|Script to fix date formats).*?</script>",
                        "",
                        new_content,
                        flags=re.DOTALL,
                    )

                    with open(date_js_path, "r", encoding="utf-8") as f:
                        date_script_template = f.read()

                    # Replace placeholder with actual version
                    date_script = date_script_template.replace("{VERSION}", VERSION)

                    # Wrap in script tags
                    date_fix_script = f"\n<script>\n{date_script}\n</script>\n"

                    # Add the script just before the closing body tag
                    if "</body>" in new_content:
                        new_content = new_content.replace(
                            "</body>", date_fix_script + "</body>"
                        )
                        logger.info(
                            "Injected date format fixing script into index.html"
                        )
                else:
                    logger.warning(
                        f"Date formatter JavaScript not found: {date_js_path}"
                    )

            if new_content != content:
                with open(html_file, "w", encoding="utf-8") as f:
                    f.write(new_content)
                updated_count += 1
        except Exception as e:
            logger.error(f"Error fixing title in {html_file}: {str(e)}")

    logger.info(f"Fixed date format in {updated_count} HTML files")


def fix_js_date_formats(report_dir: str) -> None:
    """Fix date formats in JavaScript files.

    Standardizes dates in JavaScript files to use DD-MM-YYYY format:
    - Updates date strings in JavaScript code
    - Updates date references in JSON-like structures
    - Injects dynamic date formatting code in app.js

    Args:
        report_dir: Path to the Allure report directory.
    """
    today = get_current_date_formatted()

    if DRY_RUN:
        logger.info(
            f"DRY-RUN: Would fix date formats in JavaScript files with date {today}"
        )
        return

    js_files = glob.glob(os.path.join(report_dir, "**", "*.js"), recursive=True)
    fixed_count = 0

    for js_file in js_files:
        try:
            with open(js_file, "r", encoding="utf-8") as f:
                content = f.read()

            modified = False

            # Replace date strings directly using regex pattern matching and direct string replacement
            date_patterns = [
                r"ALLURE\s+REPORT\s+\d{1,2}/\d{1,2}/\d{4}",
                r"Allure\s+Report\s+\d{1,2}/\d{1,2}/\d{4}",
                r"ALLURE\s+REPORT\s+\d{1,2}-\d{1,2}-\d{4}",
                r"Allure\s+Report\s+\d{1,2}-\d{1,2}-\d{4}",
            ]

            for pattern in date_patterns:
                regex = re.compile(pattern, re.IGNORECASE)
                matches = regex.findall(content)
                for match in matches:
                    content = content.replace(match, f"ALLURE REPORT {today}")
                    modified = True

            # Also look for title fields in JSON-like structures
            title_patterns = [
                r'"title"\s*:\s*"[^"]*\d{1,2}/\d{1,2}/\d{4}[^"]*"',
                r'"title"\s*:\s*"[^"]*\d{1,2}-\d{1,2}-\d{4}[^"]*"',
            ]

            for pattern in title_patterns:
                regex = re.compile(pattern, re.IGNORECASE)
                matches = regex.findall(content)
                for match in matches:
                    # Extract just the part between quotes after title:
                    content = content.replace(match, f'"title":"ALLURE REPORT {today}"')
                    modified = True

            # Special case for app.js - this is where the main UI component renders
            if os.path.basename(js_file) == "app.js":
                logger.info(
                    f"Processing app.js, using dynamic date formatter script from js/date_formatter.js"
                )

                # Load date formatter JavaScript from external file
                js_dir = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "js"
                )
                inline_date_js_path = os.path.join(js_dir, "inline_date_formatter.js")

                if os.path.exists(inline_date_js_path):
                    # Read the script from the external file
                    with open(inline_date_js_path, "r", encoding="utf-8") as f:
                        inline_date_script = f.read()

                    # Inject our script at the end, before the closing script tag
                    if "</script>" in content:
                        parts = content.rsplit("</script>", 1)
                        content = parts[0] + inline_date_script + "</script>" + parts[1]
                        modified = True
                        logger.info("Injected date format fixing script into app.js")
                else:
                    logger.warning(
                        f"Inline date formatter JavaScript not found: {inline_date_js_path}"
                    )

            if modified:
                with open(js_file, "w", encoding="utf-8") as f:
                    f.write(content)
                fixed_count += 1
        except Exception as e:
            logger.warning(f"Error fixing JS date formats in {js_file}: {e}")

    logger.info(f"Fixed date formats in {fixed_count} JavaScript files")


def fix_json_timestamps(report_dir: str) -> None:
    """Fix timestamp format in JSON files.

    Converts ISO timestamps (YYYY-MM-DDThh:mm:ss) to DD-MM-YYYY HH:MM:SS format
    in all JSON files within the report directory.

    Args:
        report_dir: Path to the Allure report directory.
    """
    if DRY_RUN:
        logger.info(f"DRY-RUN: Would fix timestamps in JSON files")
        return

    json_files = glob.glob(os.path.join(report_dir, "**", "*.json"), recursive=True)
    fixed_count = 0

    for json_file in json_files:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Fix ISO timestamps to DD-MM-YYYY HH:MM:SS
            pattern = ISO_TIMESTAMP_PATTERN
            replacement = r"\3-\2-\1 \4:\5:\6"

            new_content = re.sub(pattern, replacement, content)

            if new_content != content:
                with open(json_file, "w", encoding="utf-8") as f:
                    f.write(new_content)
                fixed_count += 1
        except Exception as e:
            logger.warning(f"Error fixing JSON timestamp in {json_file}: {e}")

    logger.info(f"Fixed timestamps in {fixed_count} JSON files")
