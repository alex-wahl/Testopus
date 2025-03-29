#!/usr/bin/env python3
"""History preservation module for Allure report customization.

This module provides functions for preserving test history between runs,
ensuring trend data persists across test executions in CI/CD pipelines.
"""

import logging
import os
import shutil
from pathlib import Path

# Handle both relative imports for package usage and direct imports for script execution
try:
    from ..utils.file_utils import ensure_dir_exists
except ImportError:
    # When run directly
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from utils.file_utils import ensure_dir_exists

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
    preserve_history_env = os.environ.get("ALLURE_PRESERVE_HISTORY", "true").lower()
    if preserve_history_env not in ("true", "yes", "1"):
        logger.info("History preservation disabled via environment variable")
        return

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

    logger.info(f"Using results directory: {results_dir}")
    logger.info(f"Using history storage directory: {history_storage}")

    if DRY_RUN:
        logger.info(
            f"DRY-RUN: Would manage history between {history_storage} and {history_dir}"
        )
        return

    # Create directories if they don't exist
    ensure_dir_exists(history_storage)
    ensure_dir_exists(history_dir)

    # Ensure history is properly copied to storage
    if os.path.exists(history_dir) and any(os.listdir(history_dir)):
        logger.info(f"Copying history from {history_dir} to {history_storage}")
        try:
            # Copy each file individually to avoid directory structure issues
            for history_file in os.listdir(history_dir):
                src_file = os.path.join(history_dir, history_file)
                dst_file = os.path.join(history_storage, history_file)

                if os.path.isfile(src_file):
                    shutil.copy2(src_file, dst_file)
                    logger.info(f"Copied {history_file} to history storage")

            logger.info(f"Successfully preserved test history to {history_storage}")
        except Exception as e:
            logger.error(f"Failed to preserve history: {str(e)}")
    else:
        logger.warning(f"No history data found in {history_dir}")

    # Also ensure results directory has history data for next report generation
    if os.path.exists(results_dir):
        results_history_dir = os.path.join(results_dir, "history")
        ensure_dir_exists(results_history_dir)

        if os.path.exists(history_storage) and any(os.listdir(history_storage)):
            logger.info("Copying history from storage to results directory")
            try:
                # Copy each file individually to avoid directory structure issues
                for history_file in os.listdir(history_storage):
                    src_file = os.path.join(history_storage, history_file)
                    dst_file = os.path.join(results_history_dir, history_file)

                    if os.path.isfile(src_file):
                        shutil.copy2(src_file, dst_file)

                logger.info("Successfully copied history to results directory")
            except Exception as e:
                logger.error(f"Error copying history to results: {str(e)}")
