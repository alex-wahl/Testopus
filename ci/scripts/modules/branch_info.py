#!/usr/bin/env python3
"""Branch information module for Allure reports.

This module provides functions to add branch information to Allure reports,
making it easier to identify which branch a report was generated from.
"""

import logging
import os
import re
import subprocess
from typing import Optional

from utils.constants import ENV_GITHUB_HEAD_REF, ENV_GITHUB_REF, ENV_PROPERTIES_FILE
from utils.file_utils import find_files, read_file, write_file

# Set up logging
logger = logging.getLogger("allure-customizer.branch-info")

# Global variables
_dry_run = False


def set_dry_run(dry_run: bool) -> None:
    """Set dry run mode.

    Args:
        dry_run: Whether to perform operations in dry run mode
    """
    global _dry_run
    _dry_run = dry_run


def get_branch_name() -> str:
    """Get current git branch name.

    Tries multiple methods to determine the current branch name:
    1. Environment variables (for CI/CD environments)
    2. Git command line
    3. Git HEAD file

    Returns:
        str: Branch name or "unknown" if not found
    """
    # Try environment variables first (for CI)
    # GitHub Actions
    github_head_ref = os.environ.get(ENV_GITHUB_HEAD_REF)
    if github_head_ref:
        return github_head_ref

    # For GitHub Actions push events
    github_ref = os.environ.get(ENV_GITHUB_REF)
    if github_ref and github_ref.startswith("refs/heads/"):
        return github_ref.replace("refs/heads/", "")

    # Try getting branch from git command
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            branch = result.stdout.strip()
            if branch != "HEAD":
                return branch
    except (subprocess.SubprocessError, FileNotFoundError):
        pass

    # Try reading from .git/HEAD
    try:
        git_dir = find_git_directory()
        if git_dir:
            head_path = os.path.join(git_dir, "HEAD")
            if os.path.exists(head_path):
                with open(head_path, "r") as f:
                    content = f.read().strip()
                    if content.startswith("ref: refs/heads/"):
                        return content.replace("ref: refs/heads/", "")
    except Exception:
        pass

    # Fallback to current directory name
    try:
        return os.path.basename(os.getcwd())
    except Exception:
        return "unknown"


def find_git_directory() -> str:
    """Find the .git directory.

    Returns:
        str: Path to .git directory or empty string if not found
    """
    current_dir = os.getcwd()
    while current_dir:
        git_dir = os.path.join(current_dir, ".git")
        if os.path.exists(git_dir) and os.path.isdir(git_dir):
            return git_dir
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            break
        current_dir = parent_dir
    return ""


def update_environment_properties(report_dir: str, branch: str) -> None:
    """Update environment.properties file with branch information.

    Args:
        report_dir: Path to the Allure report directory
        branch: Branch name to add
    """
    if _dry_run:
        logger.info("DRY RUN: Would update environment properties with branch {0}".format(branch))
        return

    env_file = os.path.join(report_dir, ENV_PROPERTIES_FILE)

    # Create file if it doesn't exist
    if not os.path.exists(env_file):
        logger.info("Creating environment.properties file")
        with open(env_file, "w") as f:
            f.write("Branch={0}\n".format(branch))
        return

    # Read existing file
    lines = []
    branch_line_exists = False

    with open(env_file, "r") as f:
        for line in f:
            if line.startswith("Branch="):
                lines.append("Branch={0}\n".format(branch))
                branch_line_exists = True
            else:
                lines.append(line)

    # Add branch info if not present
    if not branch_line_exists:
        lines.append("Branch={0}\n".format(branch))

    # Write updated file
    with open(env_file, "w") as f:
        f.writelines(lines)

    logger.info("Updated environment.properties with branch {0}".format(branch))


def update_environment_json(report_dir: str, branch: str) -> None:
    """Update environment.json file with branch information.

    Args:
        report_dir: Path to the Allure report directory
        branch: Branch name to add
    """
    import json

    if _dry_run:
        logger.info("DRY RUN: Would update environment.json with branch {0}".format(branch))
        return

    # Find environment.json files
    env_json_files = find_files(report_dir, "environment.json")

    for env_file in env_json_files:
        try:
            if os.path.exists(env_file):
                # Read existing JSON
                with open(env_file, "r") as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        data = []
            else:
                data = []

            # Check if branch is already in the data
            branch_exists = False
            for item in data:
                if item.get("name") == "Branch":
                    item["value"] = branch
                    branch_exists = True
                    break

            # Add branch if not exists
            if not branch_exists:
                data.append({"name": "Branch", "value": branch})

            # Write updated JSON
            with open(env_file, "w") as f:
                json.dump(data, f, indent=2)

            logger.info("Updated {0} with branch {1}".format(env_file, branch))
        except Exception as e:
            logger.warning("Error updating environment.json: {0}".format(str(e)))


def update_environment_html(report_dir: str, branch: str) -> None:
    """Update HTML files with branch information.

    Args:
        report_dir: Path to the Allure report directory
        branch: Branch name to add
    """
    if _dry_run:
        logger.info("DRY RUN: Would update HTML files with branch {0}".format(branch))
        return

    # Find all HTML files
    html_files = find_files(report_dir, "*.html")
    updated_count = 0

    for html_file in html_files:
        try:
            content = read_file(html_file)
            if content is None:
                continue

            # Inject branch info if not already present
            if not re.search(r"Branch:\s*" + re.escape(branch), content):
                # Different patterns based on where to inject

                # Try to find a good injection point
                if '<div class="environment">' in content:
                    # Inject into environment section
                    new_content = re.sub(
                        r"(<div class=\"environment\">)",
                        "\\1\n<div>Branch: {0}</div>".format(branch),
                        content,
                    )
                elif "<body>" in content:
                    # Inject after body tag
                    # Break long line into shorter parts
                    div_start = '\\1\n<div style="position:fixed;top:0;right:0;padding:5px;'
                    div_style = 'background:#f8f8f8;z-index:1000;font-size:12px;">'
                    div_content = "Branch: {0}</div>".format(branch)
                    new_content = re.sub(r"(<body>)", div_start + div_style + div_content, content)
                else:
                    # Skip if no injection point found
                    continue

                if new_content != content:
                    if write_file(html_file, new_content):
                        updated_count += 1
        except Exception as e:
            logger.warning("Error updating HTML file {0}: {1}".format(html_file, str(e)))

    logger.info("Updated {0} HTML files with branch information".format(updated_count))


def add_branch_info(report_dir: str, branch: Optional[str] = None) -> None:
    """Add branch information to Allure report.

    This is the main entry point for adding branch information.

    Args:
        report_dir: Path to the Allure report directory
        branch: Branch name to add (auto-detect if None)
    """
    # Auto-detect branch if not provided
    if branch is None:
        branch = get_branch_name()

    logger.info("Adding branch information: {0}".format(branch))

    # Update environment.properties
    update_environment_properties(report_dir, branch)

    # Update environment.json if it exists
    update_environment_json(report_dir, branch)

    # Update HTML files
    update_environment_html(report_dir, branch)

    logger.info("Branch information added successfully")
