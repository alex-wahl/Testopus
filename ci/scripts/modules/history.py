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
from datetime import datetime
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


def has_existing_history(history_dir: str) -> bool:
    """Check if valid history data already exists.

    Args:
        history_dir: Path to the history directory

    Returns:
        bool: True if valid history data exists, False otherwise
    """
    history_json_path = os.path.join(history_dir, "history.json")
    return os.path.exists(history_json_path) and os.path.getsize(history_json_path) > 5


def find_test_results(results_dir: str) -> Dict[str, Dict[str, Any]]:
    """Find and load test result files.

    Args:
        results_dir: Path to the results directory

    Returns:
        Dict[str, Dict[str, Any]]: Dictionary of test results keyed by UUID
    """
    test_results: Dict[str, Dict[str, Any]] = {}

    # If no results directory, we can't find test results
    if not os.path.exists(results_dir):
        logger.warning(f"No results directory found at {results_dir}")
        return test_results

    # Look for test-result.json files
    for root, _, files in os.walk(results_dir):
        for file in files:
            if file.endswith("-result.json") or file.endswith("-container.json"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r") as f:
                        data = json.load(f)

                    # Get test UUID and status
                    if "uuid" in data and "status" in data:
                        uuid = data["uuid"]
                        status = data["status"]
                        name = data.get("name", "Unknown Test")

                        # Add to our test results dict
                        test_results[uuid] = {
                            "name": name,
                            "status": status,
                            "time": data.get("time", {"start": 0, "stop": 0, "duration": 0}),
                        }
                except Exception as e:
                    logger.warning(f"Error processing test result file {file_path}: {str(e)}")

    if not test_results:
        logger.warning("No test results found")

    return test_results


def calculate_status_statistics(test_results: Dict[str, Dict[str, Any]]) -> Dict[str, int]:
    """Calculate status statistics from test results.

    Args:
        test_results: Dictionary of test results

    Returns:
        Dict[str, int]: Dictionary with counts for each status type
    """
    total_stats = {"failed": 0, "broken": 0, "skipped": 0, "passed": 0, "unknown": 0, "total": len(test_results)}

    # Count statuses
    for test_info in test_results.values():
        status = test_info["status"]
        if status == "failed":
            total_stats["failed"] += 1
        elif status == "broken":
            total_stats["broken"] += 1
        elif status == "skipped":
            total_stats["skipped"] += 1
        elif status == "passed":
            total_stats["passed"] += 1
        else:
            total_stats["unknown"] += 1

    return total_stats


def create_history_data(test_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Create history data structure for history.json.

    Args:
        test_results: Dictionary of test results

    Returns:
        Dict[str, Any]: History data structure
    """
    history_data = {}
    timestamp = int(datetime.now().timestamp() * 1000)

    for uuid, test_info in test_results.items():
        # Create basic history entry for each test
        history_data[uuid] = {
            "statistic": {
                "failed": 1 if test_info["status"] == "failed" else 0,
                "broken": 1 if test_info["status"] == "broken" else 0,
                "skipped": 1 if test_info["status"] == "skipped" else 0,
                "passed": 1 if test_info["status"] == "passed" else 0,
                "unknown": 1 if test_info["status"] == "unknown" else 0,
                "total": 1,
            },
            "items": [
                {
                    "uid": uuid,
                    "status": test_info["status"],
                    "time": test_info["time"],
                    "reportUrl": f"data/test-cases/{uuid}.json",
                    "timestamp": timestamp,
                }
            ],
        }

    return history_data


def create_trend_data(total_stats: Dict[str, int]) -> Dict[str, List[Dict[str, Any]]]:
    """Create trend data for trend JSON files.

    Args:
        total_stats: Dictionary with counts for each status type

    Returns:
        Dict[str, List[Dict[str, Any]]]: Dictionary containing all trend data structures
    """
    # Build order for all trends
    build_order = 1
    report_url = "index.html"
    report_name = f"Run #{build_order}"

    # History trend
    history_trend = [{"buildOrder": build_order, "reportUrl": report_url, "reportName": report_name, "data": total_stats}]

    # Categories trend
    categories_trend = [
        {
            "buildOrder": build_order,
            "reportUrl": report_url,
            "reportName": report_name,
            "data": {"categoryA": total_stats["broken"], "categoryB": total_stats["failed"]},
        }
    ]

    # Duration trend
    duration_trend = [
        {
            "buildOrder": build_order,
            "reportUrl": report_url,
            "reportName": report_name,
            "data": {"duration": 0},  # We don't have aggregate duration info
        }
    ]

    # Retries trend
    retries_trend = [
        {
            "buildOrder": build_order,
            "reportUrl": report_url,
            "reportName": report_name,
            "data": {"retry": 0},  # We don't have retry info
        }
    ]

    return {
        "history-trend.json": history_trend,
        "categories-trend.json": categories_trend,
        "duration-trend.json": duration_trend,
        "retries-trend.json": retries_trend,
    }


def write_history_files(history_dir: str, history_data: Dict[str, Any], trend_data: Dict[str, List[Dict[str, Any]]]) -> bool:
    """Write history data to JSON files.

    Args:
        history_dir: Path to the history directory
        history_data: History data structure for history.json
        trend_data: Dictionary containing all trend data structures

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Write history.json
        with open(os.path.join(history_dir, "history.json"), "w") as f:
            json.dump(history_data, f)

        # Write all trend files
        for filename, data in trend_data.items():
            with open(os.path.join(history_dir, filename), "w") as f:
                json.dump(data, f)

        return True
    except Exception as e:
        logger.error(f"Error writing history files: {str(e)}")
        return False


def generate_basic_history_data(report_dir: str, history_dir: str) -> bool:
    """Generate basic history data from current test results if no history exists.

    This ensures that even for the first run, the history tab shows some minimal data.
    Orchestrates the process of creating history data by calling helper functions.

    Args:
        report_dir: Path to the Allure report directory
        history_dir: Path to the history directory

    Returns:
        bool: True if history was generated, False otherwise
    """
    logger.info("Generating basic history data from current run")

    # Ensure history directory exists
    ensure_dir_exists(history_dir)

    # Check if we already have history data
    if has_existing_history(history_dir):
        logger.info("Existing history data found, skipping basic generation")
        return False

    # Find test results directory and load test data
    results_dir = os.path.join(os.path.dirname(report_dir), "allure-results")
    test_results = find_test_results(results_dir)

    if not test_results:
        logger.warning("No test results found to generate history from")
        return False

    # Calculate statistics from test results
    total_stats = calculate_status_statistics(test_results)

    # Create history data structure
    history_data = create_history_data(test_results)

    # Create trend data structures
    trend_data = create_trend_data(total_stats)

    # Write all data to files
    success = write_history_files(history_dir, history_data, trend_data)

    if success:
        logger.info(f"Generated basic history data with {len(test_results)} tests")

    return success


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
    ensure_dir_exists(history_dir)
    ensure_dir_exists(results_history_dir)

    # Initialize empty history files if necessary
    if not os.path.exists(history_dir) or not os.listdir(history_dir):
        initialize_history_files(history_dir)
        logger.info(f"Initialized empty history files in {history_dir}")

    if not os.path.exists(storage_history_dir) or not os.listdir(storage_history_dir):
        initialize_history_files(storage_history_dir)
        logger.info(f"Initialized empty history files in {storage_history_dir}")

    if not os.path.exists(results_history_dir) or not os.listdir(results_history_dir):
        initialize_history_files(results_history_dir)
        logger.info(f"Initialized empty history files in {results_history_dir}")

    # If we don't have history data in the report, generate it
    history_empty = not os.path.exists(history_dir) or not os.listdir(history_dir)
    storage_empty = not os.path.exists(storage_history_dir) or not os.listdir(storage_history_dir)

    if history_empty and storage_empty:
        logger.info("No history data found, generating basic history from current run")
        success = generate_basic_history_data(report_dir, history_dir)
        if success:
            logger.info("Successfully generated basic history data")
        else:
            logger.warning("Failed to generate basic history data")

    # Force a copy of history files to the results directory for next run
    if os.path.exists(storage_history_dir):
        logger.info(f"Copying history from storage to results: {storage_history_dir} -> {results_history_dir}")
        for file_name in HISTORY_FILES:
            src_file = os.path.join(storage_history_dir, file_name)
            dst_file = os.path.join(results_history_dir, file_name)

            if os.path.exists(src_file):
                try:
                    # Ensure destination directory exists
                    os.makedirs(os.path.dirname(dst_file), exist_ok=True)

                    # Copy the file
                    import shutil

                    shutil.copy2(src_file, dst_file)
                    logger.info(f"Copied {file_name} to results directory")
                except Exception as e:
                    logger.error(f"Error copying {file_name}: {str(e)}")

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
    display_dir_contents(results_history_dir, "Final results history directory contents")

    logger.info("History preservation completed successfully")
