#!/usr/bin/env python3
"""Branch information module for Allure reports.

This module provides functions to add branch information to Allure reports,
making it easier to identify which branch a report was generated from.
"""

import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

# Set up Python path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Import from project
from ci.scripts.utils.constants import ENV_GITHUB_HEAD_REF, ENV_GITHUB_REF, ENV_PROPERTIES_FILE  # noqa: E402
from ci.scripts.utils.file_utils import find_files  # noqa: E402

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


def _read_git_head_file(head_path: str) -> Optional[str]:
    """Read and parse the .git/HEAD file.

    Args:
        head_path: Path to the HEAD file

    Returns:
        str or None: Branch name if found, None otherwise
    """
    if not os.path.exists(head_path):
        return None

    try:
        with open(head_path, "r") as f:
            content = f.read().strip()

        if not content.startswith("ref: refs/heads/"):
            return None

        return content.replace("ref: refs/heads/", "")
    except Exception:
        return None


def get_branch_from_git_head() -> Optional[str]:
    """Get branch name from .git/HEAD file.

    Returns:
        str or None: Branch name if found in .git/HEAD, None otherwise
    """
    git_dir = find_git_directory()
    if not git_dir:
        return None

    head_path = os.path.join(git_dir, "HEAD")
    return _read_git_head_file(head_path)


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
    branch_entry = "Branch={0}\n".format(branch)
    branch_exists = False

    with open(env_file, "r") as f:
        for line in f:
            if line.startswith("Branch="):
                # Skip existing branch line, we'll add it at the top
                branch_exists = True
            else:
                lines.append(line)

    # Create new content with branch at the top
    new_content = [branch_entry] + lines

    # Write updated file
    with open(env_file, "w") as f:
        f.writelines(new_content)

    action = "Updated" if branch_exists else "Added"
    logger.info(f"{action} branch information in environment.properties with value {branch} at the top")


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
    # Remove any existing branch entry and check if any were found
    initial_count = len(data)
    new_data = [item for item in data if item.get("name") != "Branch"]
    branch_existed = initial_count > len(new_data)

    # Add branch as the first item
    new_data.insert(0, {"name": "Branch", "values": [branch]})

    return new_data, branch_existed


def update_environment_json(report_dir: str, branch: str) -> None:
    """Update environment.json file with branch information.

    Args:
        report_dir: Path to the Allure report directory
        branch: Branch name to add
    """
    if _dry_run:
        logger.info("DRY RUN: Would update environment.json with branch {0}".format(branch))
        return

    # Find all environment JSON files
    for env_json in find_files(report_dir, "environment.json"):
        try:
            # Load existing data
            data = load_json_data(env_json)

            # Update data with branch info
            updated_data, existed = update_branch_in_json_data(data, branch)

            # Write updated data
            with open(env_json, "w") as f:
                json.dump(updated_data, f)

            action = "Updated" if existed else "Added"
            logger.info("{0} branch info in {1}".format(action, env_json))
        except Exception as e:
            logger.error("Failed to update environment.json file {0}: {1}".format(env_json, str(e)))


def get_js_script_content(script_name: str, replacements: Optional[Dict[str, str]] = None) -> str:
    """Get the content of a JavaScript file with optional replacements.

    Args:
        script_name: Name of the JavaScript file
        replacements: Dictionary of replacements to make in the script

    Returns:
        str: Content of the JavaScript file with replacements
    """
    script_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "js")
    script_path = os.path.join(script_dir, script_name)

    if not os.path.exists(script_path):
        logger.warning(f"JavaScript file not found: {script_path}")
        return ""

    try:
        with open(script_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Apply replacements
        if replacements:
            for key, value in replacements.items():
                content = content.replace(key, value)

        return content
    except Exception as e:
        logger.error(f"Error reading JavaScript file {script_path}: {str(e)}")
        return ""


def inject_branch_js(report_dir: str, branch: str) -> None:
    """Inject JavaScript to display branch info prominently.

    Args:
        report_dir: Path to the Allure report directory
        branch: Branch name to add
    """
    if _dry_run:
        logger.info("DRY RUN: Would inject branch JS")
        return

    # Get the content of the JS files
    replacements = {"{BRANCH_NAME}": branch, "{VERSION}": "1.0.0"}  # Version can be updated as needed

    branch_info_js = get_js_script_content("branch_info.js", replacements)
    branch_position_js = get_js_script_content("branch_position.js", replacements)

    # Combine the scripts
    combined_script = f"""
<script>
{branch_info_js}
{branch_position_js}
</script>
"""

    # Find index.html files
    for html_file in find_files(report_dir, "index.html"):
        try:
            with open(html_file, "r") as f:
                content = f.read()

            # Add script before closing body tag
            if "</body>" in content:
                content = content.replace("</body>", f"{combined_script}\n</body>")
            else:
                content += combined_script

            # Write modified content
            with open(html_file, "w") as f:
                f.write(content)

            logger.info("Injected branch JS in {0}".format(html_file))
        except Exception as e:
            logger.error("Failed to inject branch JS in {0}: {1}".format(html_file, str(e)))


def add_branch_info(report_dir: str, branch: str) -> None:
    """Add branch information to Allure report.

    This is the main entry point for branch info operations.

    Args:
        report_dir: Path to the Allure report directory
        branch: Branch name to add
    """
    if not branch:
        logger.warning("No branch name provided, skipping branch info")
        return

    # Update environment.properties
    update_environment_properties(report_dir, branch)

    # Update environment.json
    update_environment_json(report_dir, branch)

    # Inject JavaScript to ensure branch display is correct
    inject_branch_js(report_dir, branch)
