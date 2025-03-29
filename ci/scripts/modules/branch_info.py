#!/usr/bin/env python3
"""Branch information module for Allure reports.

This module provides functions to add branch information to Allure reports,
making it easier to identify which branch a report was generated from.
"""

import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

# Set up Python path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Import from project
from ci.scripts.utils.constants import ENV_GITHUB_HEAD_REF, ENV_GITHUB_REF, ENV_PROPERTIES_FILE  # noqa: E402
from ci.scripts.utils.file_utils import find_files, read_file, write_file  # noqa: E402

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


def get_branch_from_env() -> Optional[str]:
    """Get branch name from environment variables.

    Returns:
        str or None: Branch name if found in environment variables, None otherwise
    """
    # GitHub Actions
    github_head_ref = os.environ.get(ENV_GITHUB_HEAD_REF)
    if github_head_ref:
        return github_head_ref

    # For GitHub Actions push events
    github_ref = os.environ.get(ENV_GITHUB_REF)
    if github_ref and github_ref.startswith("refs/heads/"):
        return github_ref.replace("refs/heads/", "")

    return None


def get_branch_from_git_command() -> Optional[str]:
    """Get branch name using git command.

    Returns:
        str or None: Branch name if found using git command, None otherwise
    """
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

    return None


def get_branch_from_git_head() -> Optional[str]:
    """Get branch name from .git/HEAD file.

    Returns:
        str or None: Branch name if found in .git/HEAD, None otherwise
    """
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

    return None


def get_branch_from_cwd() -> str:
    """Get branch name from current working directory.

    Returns:
        str: Current directory name or "unknown"
    """
    try:
        return os.path.basename(os.getcwd())
    except Exception:
        return "unknown"


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
    branch = get_branch_from_env()
    if branch:
        return branch

    # Try getting branch from git command
    branch = get_branch_from_git_command()
    if branch:
        return branch

    # Try reading from .git/HEAD
    branch = get_branch_from_git_head()
    if branch:
        return branch

    # Fallback to current directory name
    return get_branch_from_cwd()


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


def load_json_data(file_path: str) -> list:
    """Load JSON data from a file.

    Args:
        file_path: Path to the JSON file

    Returns:
        list: Loaded JSON data or empty list if file doesn't exist or is invalid
    """
    if not os.path.exists(file_path):
        return []

    try:
        with open(file_path, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    except Exception:
        return []


def update_branch_in_json_data(data: list, branch: str) -> Tuple[list, bool]:
    """Update branch information in JSON data.

    Args:
        data: JSON data to update
        branch: Branch name to add

    Returns:
        tuple: Updated data and whether branch existed previously
    """
    branch_exists = False
    for item in data:
        if item.get("name") == "Branch":
            item["value"] = branch
            branch_exists = True
            break

    if not branch_exists:
        data.append({"name": "Branch", "value": branch})

    return data, branch_exists


def save_json_data(file_path: str, data: list) -> bool:
    """Save JSON data to a file.

    Args:
        file_path: Path to the JSON file
        data: JSON data to save

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False


def update_environment_json(report_dir: str, branch: str) -> None:
    """Update environment.json file with branch information.

    Args:
        report_dir: Path to the Allure report directory
        branch: Branch name to add
    """
    if _dry_run:
        logger.info("DRY RUN: Would update environment.json with branch {0}".format(branch))
        return

    # Find environment.json files
    env_json_files = find_files(report_dir, "environment.json")

    for env_file in env_json_files:
        try:
            # Load JSON data
            data = load_json_data(env_file)

            # Update branch info in the data
            data, _ = update_branch_in_json_data(data, branch)

            # Save updated data
            if save_json_data(env_file, data):
                logger.info("Updated {0} with branch {1}".format(env_file, branch))
            else:
                logger.warning("Failed to update {0}".format(env_file))
        except Exception as e:
            logger.warning("Error updating environment.json: {0}".format(str(e)))


def should_update_html(content: Optional[str], branch: str) -> bool:
    """Check if HTML content needs to be updated with branch information.

    Args:
        content: HTML content to check
        branch: Branch name

    Returns:
        bool: True if content needs updating, False otherwise
    """
    return content is not None and not re.search(r"Branch:\s*" + re.escape(branch), content)


def inject_branch_into_environment(content: str, branch: str) -> str:
    """Inject branch info into the environment section of HTML.

    Args:
        content: HTML content
        branch: Branch name

    Returns:
        str: Updated HTML content
    """
    if '<div class="environment">' in content:
        return re.sub(
            r"(<div class=\"environment\">)",
            "\\1\n<div>Branch: {0}</div>".format(branch),
            content,
        )
    return content


def inject_branch_into_body(content: str, branch: str) -> str:
    """Inject branch info after the body tag of HTML.

    Args:
        content: HTML content
        branch: Branch name

    Returns:
        str: Updated HTML content
    """
    if "<body>" in content:
        # Break long line into shorter parts
        div_start = '\\1\n<div style="position:fixed;top:0;right:0;padding:5px;'
        div_style = 'background:#f8f8f8;z-index:1000;font-size:12px;">'
        div_content = "Branch: {0}</div>".format(branch)

        return re.sub(r"(<body>)", div_start + div_style + div_content, content)
    return content


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

            # Skip if content is None or already has branch info
            if not should_update_html(content, branch):
                continue

            # Content is not None at this point, so we can safely cast it
            assert content is not None

            # Try to inject branch info into environment section first
            new_content = inject_branch_into_environment(content, branch)

            # If no environment section, try body tag
            if new_content == content:
                new_content = inject_branch_into_body(content, branch)

            # Skip if no injection point found
            if new_content == content:
                continue

            # Write changes if content was modified
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
