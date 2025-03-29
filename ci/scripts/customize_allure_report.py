#!/usr/bin/env python3
"""Customize and enhance Allure reports.

This script customizes Allure test reports by:
1. Adding cache control headers
2. Fixing date formats
3. Adding branch information
4. Preserving history between runs
5. Creating dummy reports when needed

Usage:
    python customize_allure_report.py [options]

Options:
    --report-dir DIR       Path to Allure report directory
    --dummy                Create a dummy report
    --dry-run              Print what would be done without making changes
    --branch NAME          Specify branch name
    --history              Preserve history between runs
    --verbose              Enable verbose output

Example:
    python customize_allure_report.py --report-dir ./allure-report --branch main --history
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Set up Python path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Import modules from the project
from ci.scripts.modules.branch_info import add_branch_info  # noqa: E402
from ci.scripts.modules.cache_control import add_cache_control  # noqa: E402
from ci.scripts.modules.date_formatter import fix_date_formats  # noqa: E402
from ci.scripts.modules.dummy_report import create_dummy_report  # noqa: E402
from ci.scripts.modules.history import preserve_history  # noqa: E402
from ci.scripts.utils.constants import (  # noqa: E402
    DEFAULT_REPORT_DIR,
    ENV_BRANCH,
    ENV_CREATE_DUMMY,
    ENV_GITHUB_HEAD_REF,
    ENV_GITHUB_REF,
    ENV_PRESERVE_HISTORY,
    ENV_REPORT_DIR,
    NOJEKYLL_FILE,
    VERSION,
)

__version__ = VERSION

# Set up logging
logger = logging.getLogger("allure-customizer")


def parse_args():
    """Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Customize Allure reports with additional features.")
    parser.add_argument(
        "--report-dir",
        help="Path to the Allure report directory. Defaults to {0}".format(DEFAULT_REPORT_DIR),
    )
    parser.add_argument(
        "--dummy",
        action="store_true",
        help="Create a dummy report if the directory doesn't exist",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without making changes",
    )
    parser.add_argument("--branch", help="Specify branch name")
    parser.add_argument("--history", action="store_true", help="Preserve history between runs")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--version", action="version", version="%(prog)s {0}".format(__version__))

    return parser.parse_args()


def setup_logging(verbose=False):
    """Set up logging configuration.

    Args:
        verbose (bool): Whether to enable verbose output
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=log_level, format=log_format)


def handle_dummy_report(report_dir, create_dummy, dry_run):
    """Create a dummy report if needed.

    Args:
        report_dir (str): Directory where the report should be created
        create_dummy (bool): Whether to create a dummy report
        dry_run (bool): Whether to run in dry run mode

    Returns:
        bool: True if successful, False otherwise
    """
    if not create_dummy:
        return True

    logger.info("Creating dummy report in {0}".format(report_dir))
    if dry_run:
        logger.info("DRY RUN: Would create dummy report")
    else:
        create_dummy_report(report_dir)
        logger.info("Dummy report created")
    return True


def create_nojekyll(report_dir, dry_run):
    """Create .nojekyll file for GitHub Pages.

    Args:
        report_dir (str): Directory where the file should be created
        dry_run (bool): Whether to run in dry run mode
    """
    nojekyll_path = os.path.join(report_dir, NOJEKYLL_FILE)
    if os.path.exists(nojekyll_path):
        return

    logger.info("Creating {0} file at {1}".format(NOJEKYLL_FILE, nojekyll_path))
    if not dry_run:
        open(nojekyll_path, "w").close()  # Create empty file
        logger.info("Created {0} file at {1}".format(NOJEKYLL_FILE, nojekyll_path))


def get_branch_info(args):
    """Get branch name from arguments or environment variables.

    Args:
        args: Command line arguments

    Returns:
        str or None: Branch name if found, None otherwise
    """
    return (
        args.branch
        or os.environ.get(ENV_BRANCH)
        or os.environ.get(ENV_GITHUB_HEAD_REF)
        or os.environ.get(ENV_GITHUB_REF, "").replace("refs/heads/", "")
        or None
    )


def add_branch_information(report_dir, branch, dry_run):
    """Add branch information to the report.

    Args:
        report_dir (str): Report directory
        branch (str): Branch name
        dry_run (bool): Whether to run in dry run mode
    """
    if not branch:
        return

    logger.info("Adding branch info: {0}".format(branch))
    if dry_run:
        logger.info("DRY RUN: Would add branch info")
    else:
        add_branch_info(report_dir, branch)
        logger.info("Added branch info: {0}".format(branch))


def add_cache_headers(report_dir, dry_run):
    """Add cache control headers to the report.

    Args:
        report_dir (str): Report directory
        dry_run (bool): Whether to run in dry run mode
    """
    logger.info("Adding cache control headers")
    if dry_run:
        logger.info("DRY RUN: Would add cache control headers")
    else:
        add_cache_control(report_dir)
        logger.info("Added cache control headers")


def fix_dates(report_dir, dry_run):
    """Fix date formats in the report.

    Args:
        report_dir (str): Report directory
        dry_run (bool): Whether to run in dry run mode
    """
    logger.info("Fixing date formats")
    if dry_run:
        logger.info("DRY RUN: Would fix date formats")
    else:
        fix_date_formats(report_dir)
        logger.info("Fixed date formats")


def handle_history(report_dir, preserve_history_flag, dry_run):
    """Preserve history between runs if needed.

    Args:
        report_dir (str): Report directory
        preserve_history_flag (bool): Whether to preserve history
        dry_run (bool): Whether to run in dry run mode
    """
    if not preserve_history_flag:
        return

    logger.info("Preserving history between runs")
    if dry_run:
        logger.info("DRY RUN: Would preserve history")
    else:
        preserve_history(report_dir)
        logger.info("Preserved history")


def main():
    """Entry point for the script."""
    args = parse_args()

    # Set up logging
    setup_logging(args.verbose)

    # Set up error handling
    from ci.scripts.modules.error_handling import setup_error_handling

    setup_error_handling()

    # Get report directory from arguments or environment variable or default
    report_dir = args.report_dir or os.environ.get(ENV_REPORT_DIR) or DEFAULT_REPORT_DIR

    # Create dummy report if needed
    create_dummy = args.dummy or os.environ.get(ENV_CREATE_DUMMY) == "true"
    handle_dummy_report(report_dir, create_dummy, args.dry_run)

    # Check if report directory exists
    if not os.path.exists(report_dir):
        logger.error("Report directory does not exist: {0}".format(report_dir))
        return 1

    # Create .nojekyll file for GitHub Pages
    create_nojekyll(report_dir, args.dry_run)

    # Get branch name and add branch info to the report
    branch = get_branch_info(args)
    add_branch_information(report_dir, branch, args.dry_run)

    # Add cache control headers
    add_cache_headers(report_dir, args.dry_run)

    # Fix date formats
    fix_dates(report_dir, args.dry_run)

    # Preserve history between runs
    preserve_history_flag = args.history or os.environ.get(ENV_PRESERVE_HISTORY) == "true"
    handle_history(report_dir, preserve_history_flag, args.dry_run)

    logger.info("Done!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
