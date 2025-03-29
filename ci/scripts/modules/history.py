#!/usr/bin/env python3
"""History preservation module for Allure report customization.

This module provides functionality to preserve history data between Allure report generations,
ensuring test statistics and trends are maintained across multiple runs.
"""

import json
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Set up Python path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

# Import modules from the project
from ci.scripts.utils.file_utils import ensure_dir_exists  # noqa: E402

# Set up logging
logger = logging.getLogger("allure-customizer.history")

# Make script idempotent (safe to run multiple times)
DRY_RUN = False

# History file patterns
HISTORY_FILES = ["history.json", "history-trend.json", "categories-trend.json", "duration-trend.json", "retries-trend.json"]


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

    # Add history subdirectories
    results_history_dir = os.path.join(results_dir, "history")
    storage_history_dir = os.path.join(history_storage, "history")

    return {
        "history_dir": history_dir,
        "results_dir": results_dir,
        "results_history_dir": results_history_dir,
        "history_storage": history_storage,
        "storage_history_dir": storage_history_dir,
    }


def initialize_history_files(directory: str) -> None:
    """Create empty history files if they don't exist.

    Args:
        directory: Directory where history files should be created
    """
    logger.info(f"Initializing empty history files in {directory}")

    # Ensure the directory exists
    ensure_dir_exists(directory)

    # Create empty JSON files for each history type
    for file_name in HISTORY_FILES:
        file_path = os.path.join(directory, file_name)
        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                if file_name == "history.json":
                    # history.json needs to be an empty object
                    f.write("{}")
                else:
                    # trend files need to be empty arrays
                    f.write("[]")
            logger.info(f"Created empty history file: {file_name}")


def load_json_from_file(file_path: str, default_empty: Optional[Union[Dict, List]] = None) -> Union[Dict, List]:
    """Load JSON data from a file with error handling.

    Args:
        file_path: Path to the JSON file
        default_empty: Default value if file doesn't exist or is invalid

    Returns:
        Any: Loaded JSON data or default value
    """
    if default_empty is None:
        default_empty = {} if file_path.endswith("history.json") else []

    if not os.path.exists(file_path):
        return default_empty

    try:
        with open(file_path, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in file: {file_path}")
                return default_empty
    except Exception as e:
        logger.warning(f"Error reading file {file_path}: {str(e)}")
        return default_empty


def merge_trend_lists(source_data: List[Dict], target_data: List[Dict]) -> List[Dict]:
    """Merge two trend lists, avoiding duplicates.

    Args:
        source_data: Source list of trend data
        target_data: Target list of trend data

    Returns:
        List[Dict]: Merged list
    """
    result = target_data.copy()

    # If data has buildOrder field, use it to identify unique items
    if source_data and isinstance(source_data[0], dict) and "buildOrder" in source_data[0]:
        # Get existing buildOrder values
        existing_ids = {item.get("buildOrder") for item in result if "buildOrder" in item}

        # Add only items with unique buildOrder
        for item in source_data:
            if "buildOrder" in item and item["buildOrder"] not in existing_ids:
                result.append(item)
    else:
        # Simple list append for non-standard items
        result.extend(source_data)

    return result


def merge_history_json(src_path: str, dst_path: str) -> bool:
    """Merge history JSON files, preserving data from both.

    Args:
        src_path: Source JSON file path
        dst_path: Destination JSON file path

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Determine default data structure based on file type
        is_history_json = src_path.endswith("history.json")
        default_empty: Union[Dict[str, Any], List[Dict[str, Any]]] = {} if is_history_json else []

        # Load source and destination data
        src_data = load_json_from_file(src_path, default_empty)
        dst_data = load_json_from_file(dst_path, default_empty)

        # Merge data based on file type
        if isinstance(src_data, dict) and isinstance(dst_data, dict):
            # For history.json - combine dictionaries
            merged_data: Union[Dict[str, Any], List[Dict[str, Any]]] = {
                **dst_data,
                **src_data,
            }  # src_data overwrites conflicts
        elif isinstance(src_data, list) and isinstance(dst_data, list):
            # For trend files - merge lists, avoiding duplicates
            merged_data = merge_trend_lists(src_data, dst_data)
        else:
            # Incompatible data types, use source
            logger.warning(f"Incompatible data types in {src_path} and {dst_path}")
            merged_data = src_data

        # Write merged data
        with open(dst_path, "w") as f:
            json.dump(merged_data, f)

        return True
    except Exception as e:
        logger.error(f"Error merging history files: {str(e)}")
        return False


def copy_and_merge_history_files(src_dir: str, dst_dir: str, log_prefix: str = "") -> bool:
    """Copy and merge history files between directories.

    Args:
        src_dir: Source directory
        dst_dir: Destination directory
        log_prefix: Prefix for log messages

    Returns:
        bool: True if successful, False otherwise
    """
    if not os.path.exists(src_dir):
        logger.warning(f"{log_prefix}Source directory does not exist: {src_dir}")
        return False

    if not os.path.exists(dst_dir):
        ensure_dir_exists(dst_dir)

    # Check if source directory has any history files
    history_files_exist = any(os.path.exists(os.path.join(src_dir, file_name)) for file_name in HISTORY_FILES)

    if not history_files_exist:
        logger.warning(f"{log_prefix}No history files found in {src_dir}")
        return False

    logger.info(f"{log_prefix}Copying history files from {src_dir} to {dst_dir}")

    # Process each history file
    success = True
    for file_name in HISTORY_FILES:
        src_file = os.path.join(src_dir, file_name)
        dst_file = os.path.join(dst_dir, file_name)

        if os.path.isfile(src_file):
            try:
                # For history files, merge them instead of overwriting
                if merge_history_json(src_file, dst_file):
                    logger.info(f"{log_prefix}Merged {file_name}")
                else:
                    # If merge fails, try a simple copy
                    shutil.copy2(src_file, dst_file)
                    logger.info(f"{log_prefix}Copied {file_name} (fallback to simple copy)")
            except Exception as e:
                logger.error(f"{log_prefix}Error processing {file_name}: {str(e)}")
                success = False

    if success:
        logger.info(f"{log_prefix}Successfully processed history files")
    return success


def display_dir_contents(directory: str, description: str) -> None:
    """Display directory contents for debugging.

    Args:
        directory: Directory to display
        description: Description for logging
    """
    if not os.path.exists(directory):
        logger.info(f"{description} ({directory}): Directory does not exist")
        return

    files = os.listdir(directory)
    if not files:
        logger.info(f"{description} ({directory}): Directory is empty")
        return

    logger.info(f"{description} ({directory}):")
    for file_name in files:
        file_path = os.path.join(directory, file_name)
        if os.path.isfile(file_path):
            size = os.path.getsize(file_path)
            logger.info(f"  - {file_name} ({size} bytes)")
        elif os.path.isdir(file_path):
            subfiles = os.listdir(file_path)
            logger.info(f"  - {file_name}/ ({len(subfiles)} items)")


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
    results_history_dir = dirs["results_history_dir"]
    history_storage = dirs["history_storage"]
    storage_history_dir = dirs["storage_history_dir"]

    logger.info(f"Report directory: {report_dir}")
    logger.info(f"History directory: {history_dir}")
    logger.info(f"Results directory: {results_dir}")
    logger.info(f"History storage: {history_storage}")

    if DRY_RUN:
        logger.info(f"DRY-RUN: Would manage history between {history_storage} and {history_dir}")
        return

    # Display directory contents for debugging
    display_dir_contents(history_dir, "Report history directory contents")
    display_dir_contents(storage_history_dir, "Storage history directory contents")

    # Create directories if they don't exist
    ensure_dir_exists(history_storage)
    ensure_dir_exists(storage_history_dir)

    # Initialize history storage if empty
    if not os.path.exists(storage_history_dir) or not os.listdir(storage_history_dir):
        initialize_history_files(storage_history_dir)

    # Merge history from report to storage
    if os.path.exists(history_dir) and os.listdir(history_dir):
        copy_and_merge_history_files(history_dir, storage_history_dir, "Report to storage: ")
    else:
        logger.warning(f"No history directory found in report: {history_dir}")

    # Copy history from storage to results directory for next run
    if os.path.exists(results_dir):
        ensure_dir_exists(results_history_dir)
        copy_and_merge_history_files(storage_history_dir, results_history_dir, "Storage to results: ")
    else:
        logger.warning(f"Results directory does not exist: {results_dir}")

    # Final display of contents
    display_dir_contents(storage_history_dir, "Final storage history directory contents")

    logger.info("History preservation completed successfully")
