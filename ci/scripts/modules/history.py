#!/usr/bin/env python3
"""History preservation module for Allure report customization.

This module provides functionality to preserve history data between Allure report generations,
ensuring test statistics and trends are maintained across multiple runs.
"""

import logging
import os
import shutil
import sys
from pathlib import Path

# Set up Python path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

# Import modules from the project
from ci.scripts.utils.file_utils import ensure_dir_exists  # noqa: E402

# Set up logging
logger = logging.getLogger("allure-customizer.history")

# Make script idempotent (safe to run multiple times)
DRY_RUN = False


def set_dry_run(dry_run: bool) -> None:
    """Set dry run mode.

    Args:
        dry_run: Whether to perform operations in dry run mode
    """
    global DRY_RUN
    DRY_RUN = dry_run


def should_preserve_history() -> bool:
    """Check if history preservation is enabled via environment variables.

    Returns:
        bool: True if history preservation is enabled, False otherwise
    """
    preserve_history_env = os.environ.get("ALLURE_PRESERVE_HISTORY", "true").lower()
    return preserve_history_env in ("true", "yes", "1")


def get_history_directories(report_dir: str) -> dict:
    """Get relevant history directories based on report directory.

    Args:
        report_dir: Path to the Allure report directory

    Returns:
        dict: Dictionary containing paths to relevant directories
    """
    # Define key directories based on report_dir
    history_dir = os.path.join(report_dir, "history")
    report_parent = os.path.dirname(report_dir)

    # Derive report-related directories using common patterns
    if report_dir.endswith("allure-report"):
        # Standard structure - allure-report, allure-results, and allure-history in same parent
        results_dir = os.path.join(report_parent, "allure-results")
        history_storage = os.path.join(report_parent, "allure-history")
    else:
        # Non-standard path - use neighboring directories
        results_dir = os.path.join(report_parent, "allure-results")
        history_storage = os.path.join(report_parent, "allure-history")

    return {"history_dir": history_dir, "results_dir": results_dir, "history_storage": history_storage}


def copy_files_between_directories(src_dir: str, dst_dir: str, log_prefix: str = "") -> bool:
    """Copy all files from source directory to destination directory.

    Args:
        src_dir: Source directory
        dst_dir: Destination directory
        log_prefix: Prefix for log messages

    Returns:
        bool: True if successful, False otherwise
    """
    if not os.path.exists(src_dir) or not any(os.listdir(src_dir)):
        logger.warning(f"{log_prefix}No files found in {src_dir}")
        return False

    logger.info(f"{log_prefix}Copying files from {src_dir} to {dst_dir}")

    try:
        # Copy each file individually to avoid directory structure issues
        for file_name in os.listdir(src_dir):
            src_file = os.path.join(src_dir, file_name)
            dst_file = os.path.join(dst_dir, file_name)

            if os.path.isfile(src_file):
                shutil.copy2(src_file, dst_file)
                logger.info(f"{log_prefix}Copied {file_name}")

        logger.info(f"{log_prefix}Successfully copied files")
        return True
    except Exception as e:
        logger.error(f"{log_prefix}Error copying files: {str(e)}")
        return False


def preserve_history(report_dir: str) -> None:
    """Preserve test history between runs.

    Manages the history files across multiple directories to ensure test trends
    and history data are preserved between test runs. This function:
    1. Copies history data from the report to a storage directory
    2. Ensures the results directory has the history data for the next run
    3. Creates necessary directories if they don't exist

    Args:
        report_dir: Path to the Allure report directory.
    """
    # Check if history preservation is enabled
    if not should_preserve_history():
        logger.info("History preservation disabled via environment variable")
        return

    # Get relevant directories
    dirs = get_history_directories(report_dir)
    history_dir = dirs["history_dir"]
    results_dir = dirs["results_dir"]
    history_storage = dirs["history_storage"]

    logger.info(f"Using results directory: {results_dir}")
    logger.info(f"Using history storage directory: {history_storage}")

    if DRY_RUN:
        logger.info(f"DRY-RUN: Would manage history between {history_storage} and {history_dir}")
        return

    # Create directories if they don't exist
    ensure_dir_exists(history_storage)
    ensure_dir_exists(history_dir)

    # Copy history from report to storage
    copy_files_between_directories(history_dir, history_storage, "Report to storage: ")

    # Copy history from storage to results directory for next run
    if os.path.exists(results_dir):
        results_history_dir = os.path.join(results_dir, "history")
        ensure_dir_exists(results_history_dir)

        copy_files_between_directories(history_storage, results_history_dir, "Storage to results: ")
