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

# Importing our modules
from modules.branch_info import add_branch_info
from modules.cache_control import add_cache_control
from modules.date_formatter import fix_date_formats
from modules.dummy_report import create_dummy_report
from modules.error_handling import setup_error_handling
from modules.history import preserve_history

from utils.constants import (
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
    parser = argparse.ArgumentParser(
        description="Customize Allure reports with additional features."
    )
    parser.add_argument(
        "--report-dir",
        help=f"Path to the Allure report directory. Defaults to {DEFAULT_REPORT_DIR}",
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
    parser.add_argument(
        "--history", action="store_true", help="Preserve history between runs"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    return parser.parse_args()


def setup_logging(verbose=False):
    """Set up logging configuration.

    Args:
        verbose (bool): Whether to enable verbose output
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=log_level, format=log_format)


def main():
    """Main entry point for the script."""
    args = parse_args()

    # Set up logging
    setup_logging(args.verbose)

    # Set up error handling
    setup_error_handling()

    # Get report directory from arguments or environment variable or default
    report_dir = args.report_dir or os.environ.get(ENV_REPORT_DIR) or DEFAULT_REPORT_DIR

    # Create dummy report if needed
    create_dummy = args.dummy or os.environ.get(ENV_CREATE_DUMMY) == "true"
    if create_dummy:
        logger.info(f"Creating dummy report in {report_dir}")
        if args.dry_run:
            logger.info("DRY RUN: Would create dummy report")
        else:
            create_dummy_report(report_dir)
            logger.info("Dummy report created")

    # Check if report directory exists
    if not os.path.exists(report_dir):
        logger.error(f"Report directory does not exist: {report_dir}")
        return 1

    # Create .nojekyll file for GitHub Pages
    nojekyll_path = os.path.join(report_dir, NOJEKYLL_FILE)
    if not os.path.exists(nojekyll_path):
        logger.info(f"Creating {NOJEKYLL_FILE} file at {nojekyll_path}")
        if not args.dry_run:
            with open(nojekyll_path, "w") as f:
                pass
            logger.info(f"Created {NOJEKYLL_FILE} file at {nojekyll_path}")

    # Get branch name from arguments or environment variables
    branch = (
        args.branch
        or os.environ.get(ENV_BRANCH)
        or os.environ.get(ENV_GITHUB_HEAD_REF)
        or os.environ.get(ENV_GITHUB_REF, "").replace("refs/heads/", "")
        or None
    )

    # Add branch info to the report
    if branch:
        logger.info(f"Adding branch info: {branch}")
        if args.dry_run:
            logger.info("DRY RUN: Would add branch info")
        else:
            add_branch_info(report_dir, branch)
            logger.info(f"Added branch info: {branch}")

    # Add cache control headers
    logger.info("Adding cache control headers")
    if args.dry_run:
        logger.info("DRY RUN: Would add cache control headers")
    else:
        add_cache_control(report_dir)
        logger.info("Added cache control headers")

    # Fix date formats
    logger.info("Fixing date formats")
    if args.dry_run:
        logger.info("DRY RUN: Would fix date formats")
    else:
        fix_date_formats(report_dir)
        logger.info("Fixed date formats")

    # Preserve history between runs
    preserve_history_flag = (
        args.history or os.environ.get(ENV_PRESERVE_HISTORY) == "true"
    )
    if preserve_history_flag:
        logger.info("Preserving history between runs")
        if args.dry_run:
            logger.info("DRY RUN: Would preserve history")
        else:
            preserve_history(report_dir)
            logger.info("Preserved history")

    logger.info("Done!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
