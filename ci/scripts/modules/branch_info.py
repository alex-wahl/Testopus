#!/usr/bin/env python3
"""Branch information module for Allure report customization.

This module provides functions for adding branch information to Allure reports.
It detects the Git branch and adds it to the report in various formats.
"""

import os
import re
import json
import logging
import subprocess
import glob
from pathlib import Path
from typing import Optional

# Handle both relative imports for package usage and direct imports for script execution
try:
    from ..utils.file_utils import read_file, write_file, modify_file, find_files
except ImportError:
    # When run directly
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from utils.file_utils import read_file, write_file, modify_file, find_files

# Set up logging
logger = logging.getLogger('allure-customizer.branch_info')

# Make script idempotent (safe to run multiple times)
DRY_RUN = False

def set_dry_run(dry_run: bool) -> None:
    """Set dry run mode.
    
    Args:
        dry_run: Whether to perform operations in dry run mode
    """
    global DRY_RUN
    DRY_RUN = dry_run

def get_branch_name() -> str:
    """Get the current branch name from environment or git command.
    
    Attempts to determine the Git branch from multiple sources in order:
    1. ALLURE_BRANCH environment variable
    2. GitHub Actions environment variables
    3. Git command line
    4. .git/HEAD file
    5. Other CI environment variables (GitLab, Jenkins, Travis CI, CircleCI)
    6. Default branch names (main/master)
    
    Returns:
        str: Current branch name or a sensible default if not available.
    """
    # First check for explicit environment variable
    branch = os.environ.get('ALLURE_BRANCH', '')
    if branch:
        logger.info(f"Using branch name from ALLURE_BRANCH: {branch}")
        return branch

    # Try multiple approaches to get the branch name
    # 1. GitHub Actions environment variables
    branch = os.environ.get('GITHUB_HEAD_REF', '')  # For pull requests
    if not branch:
        ref = os.environ.get('GITHUB_REF', '')      # For direct pushes
        if ref.startswith('refs/heads/'):
            branch = ref.replace('refs/heads/', '')
    
    # 2. Try git command
    if not branch:
        try:
            # Try to get from git command as fallback
            branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
                                           stderr=subprocess.DEVNULL).decode('utf-8').strip()
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.warning("Failed to get branch name from git command")
    
    # 3. Look for .git/HEAD file
    if not branch:
        try:
            git_head_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '.git', 'HEAD')
            if os.path.exists(git_head_path):
                with open(git_head_path, 'r') as f:
                    content = f.read().strip()
                    if content.startswith('ref: refs/heads/'):
                        branch = content.replace('ref: refs/heads/', '')
        except Exception as e:
            logger.warning(f"Failed to read .git/HEAD: {str(e)}")
    
    # 4. Try CI environment variables from other systems
    if not branch:
        # GitLab
        branch = os.environ.get('CI_COMMIT_REF_NAME', '')
        # Jenkins
        if not branch:
            branch = os.environ.get('GIT_BRANCH', '')
            if branch and branch.startswith('origin/'):
                branch = branch.replace('origin/', '')
        # Travis CI
        if not branch:
            branch = os.environ.get('TRAVIS_BRANCH', '')
        # CircleCI
        if not branch:
            branch = os.environ.get('CIRCLE_BRANCH', '')
    
    # Final fallback to standard default branch names if still not found
    if not branch or branch == 'unknown':
        if os.path.exists('.git/refs/heads/main'):
            branch = 'main'
        elif os.path.exists('.git/refs/heads/master'):
            branch = 'master'
        else:
            branch = 'main'  # Default to main as a sensible default
    
    logger.info(f"Detected branch name: {branch}")
    return branch


def add_branch_info(report_dir: str, custom_branch: str = None) -> None:
    """Add git branch information to environment properties and make it visible in the UI.
    
    Adds the branch information to multiple locations in the Allure report:
    1. environment.properties file
    2. environment.json file
    3. HTML files with environment tables
    4. index.html with JavaScript for dynamic rendering
    
    Args:
        report_dir: Path to the Allure report directory.
        custom_branch: Optional custom branch name to use (overrides auto-detection).
    """
    env_file = os.path.join(report_dir, "environment.properties")
    
    # Get branch name - use custom branch if provided, otherwise auto-detect
    branch = custom_branch if custom_branch else get_branch_name()
    logger.info(f"Using branch name: {branch}")
    
    if DRY_RUN:
        logger.info(f"DRY-RUN: Would update environment files with branch={branch}")
        return
    
    # Update environment.properties
    update_environment_properties(env_file, branch)
    
    # Update environment.json
    update_environment_json(report_dir, branch)
    
    # Update HTML files
    update_environment_html(report_dir, branch)
    
    # Update index.html with JavaScript
    update_index_html(report_dir, branch)
    
    logger.info(f"Added branch information: {branch} at the top of the environment table")


def update_environment_properties(env_file: str, branch: str) -> None:
    """Update environment.properties file with branch information.
    
    Args:
        env_file: Path to environment.properties file.
        branch: Branch name to add.
    """
    try:
        # Read existing environment properties
        if os.path.exists(env_file):
            with open(env_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        else:
            lines = []
            logger.warning(f"Creating new environment.properties file at {env_file}")
        
        # Remove any existing Branch property
        lines = [line for line in lines if not line.startswith('Branch=')]
        
        # Always add branch at the beginning of the file
        lines.insert(0, f'Branch={branch}\n')
        
        # Write updated environment properties
        with open(env_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        logger.info(f"Updated environment.properties with branch={branch}")
    except Exception as e:
        logger.error(f"Failed to update environment.properties: {str(e)}")


def update_environment_json(report_dir: str, branch: str) -> None:
    """Update environment.json file with branch information.
    
    Args:
        report_dir: Path to the Allure report directory.
        branch: Branch name to add.
    """
    env_json_file = os.path.join(report_dir, "widgets", "environment.json")
    if not os.path.exists(env_json_file):
        logger.warning(f"environment.json not found at {env_json_file}")
        return
        
    try:
        with open(env_json_file, 'r', encoding='utf-8') as f:
            env_data = json.load(f)
        
        # For the Allure report in the screenshot, the structure is a list of objects with name/values
        if isinstance(env_data, list):
            # ALWAYS remove any existing Branch entries
            env_data = [item for item in env_data if not (isinstance(item, dict) and item.get("name") == "Branch")]
            
            # ALWAYS add Branch at position 0
            env_data.insert(0, {
                "name": "Branch",
                "values": [branch]
            })
            logger.info(f"Added Branch entry at the top of environment.json")
            
            # Write back the updated data
            with open(env_json_file, 'w', encoding='utf-8') as f:
                json.dump(env_data, f, indent=2)
            logger.info(f"Saved updated environment.json")
        else:
            logger.warning(f"environment.json has unexpected non-list structure")
    except Exception as e:
        logger.error(f"Error updating environment.json: {str(e)}")


def update_environment_html(report_dir: str, branch: str) -> None:
    """Update HTML files with branch information.
    
    Adds the branch information to HTML tables in all report pages.
    
    Args:
        report_dir: Path to the Allure report directory.
        branch: Branch name to add.
    """
    html_files = glob.glob(os.path.join(report_dir, "**", "*.html"), recursive=True)
    env_table_modified = False
    
    for html_file in html_files:
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            modified = False
            
            # Find any existing Branch row and remove it
            branch_pattern = r'<tr>\s*<td>\s*Branch\s*</td>\s*<td>[^<]*</td>\s*</tr>'
            clean_content = re.sub(branch_pattern, '', content)
            
            # Different approaches to fix the table formatting
            
            # 1. Approach for tables with existing rows
            if '<table' in clean_content and '<tr>' in clean_content:
                # Find the first <tr> tag after a <table>
                table_first_row_pattern = r'(<table[^>]*>(?:\s*(?:<colgroup>.*?</colgroup>)?\s*<tbody>?\s*)?)((?:<tr>))'
                
                if re.search(table_first_row_pattern, clean_content, re.DOTALL):
                    new_content = re.sub(
                        table_first_row_pattern,
                        f'\\1<tr><td>Branch</td><td>{branch}</td></tr>\\n\\2',
                        clean_content,
                        count=1,  # Only replace the first instance
                        flags=re.DOTALL
                    )
                    modified = True
            
            # If the first approach didn't work, try a simpler one
            if not modified and '<tr>' in clean_content:
                # Find the first <tr> tag anywhere
                first_tr_pattern = r'(<tr>)'
                
                if re.search(first_tr_pattern, clean_content):
                    new_content = re.sub(
                        first_tr_pattern,
                        f'<tr><td>Branch</td><td>{branch}</td></tr>\\n\\1',
                        clean_content,
                        count=1,  # Only replace the first instance
                    )
                    modified = True
            
            if modified:
                # Verify the HTML isn't malformed
                if not ('<tr><td>Branch</td><td>' in new_content and '</tr>' in new_content):
                    logger.warning(f"Skipping HTML update for {html_file} - could result in malformed HTML")
                    continue
                    
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                env_table_modified = True
                logger.info(f"Updated branch position in {html_file}")
        except Exception as e:
            logger.error(f"Error modifying branch in HTML {html_file}: {str(e)}")
    
    if not env_table_modified:
        logger.warning("No HTML files were modified to include branch information")


def update_index_html(report_dir: str, branch: str) -> None:
    """Update index.html file with JavaScript to display branch information.
    
    Adds a JavaScript script to the index.html file that dynamically displays
    the branch information in the UI.
    
    Args:
        report_dir: Path to the Allure report directory.
        branch: Branch name to add.
    """
    index_file = os.path.join(report_dir, "index.html")
    if not os.path.exists(index_file):
        logger.warning(f"index.html not found at {index_file}")
        return
        
    try:
        # Load branch info JavaScript from external file
        js_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "js")
        branch_js_path = os.path.join(js_dir, "branch_info.js")
        
        if not os.path.exists(branch_js_path):
            logger.warning(f"Branch info JavaScript file not found at {branch_js_path}")
            return
        
        # Read the file and replace branch placeholder
        with open(branch_js_path, 'r', encoding='utf-8') as f:
            branch_script = f.read().replace('{{BRANCH_NAME}}', branch)
        
        # Read the HTML file
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add the script to the head section
        if '</head>' in content:
            script_tag = f"<script type=\"text/javascript\">\n{branch_script}\n</script>"
            content = content.replace('</head>', script_tag + '</head>')
            
            with open(index_file, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Updated index.html with branch info script")
        else:
            logger.warning("Could not find </head> in index.html")
    except Exception as e:
        logger.error(f"Failed to update index.html: {str(e)}") 