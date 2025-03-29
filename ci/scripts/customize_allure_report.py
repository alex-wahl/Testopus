#!/usr/bin/env python3
"""Allure Report Customization Script.

This script customizes the Allure report generated by Allure commandline.
Following CI/CD best practices for report generation and customization.

Features:
1. Date format standardization (DD-MM-YYYY)
2. Branch information inclusion
3. Clean HTML/CSS modifications
4. No JavaScript redirects or manipulations
5. Performance optimization

Usage:
    python customize_allure_report.py [path_to_report_dir] [options]
    
Options:
    --dummy              Create a dummy report if no results available
    --branch BRANCH      Specify branch name (overrides auto-detection)
    --dry-run            Test run without making changes

Environment Variables:
    ALLURE_REPORT_DIR    Report directory (default: reports/allure-report)
    ALLURE_CREATE_DUMMY  Create dummy report if true (default: false)
    ALLURE_BRANCH        Branch name to use
"""

import os
import sys
import re
import glob
import json
import time
import logging
import subprocess
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Union

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('allure-customizer')

# Version for reproducibility in CI/CD logs
__version__ = "1.1.0"

# Make script idempotent (safe to run multiple times)
DRY_RUN = False


def get_current_date_formatted() -> str:
    """Get current date in DD-MM-YYYY format.
    
    Returns:
        str: Current date formatted as DD-MM-YYYY.
    """
    return datetime.now().strftime("%d-%m-%Y")


def create_nojekyll_file(report_dir: str) -> None:
    """Create .nojekyll file to prevent GitHub Pages from using Jekyll.
    
    Args:
        report_dir: Path to the Allure report directory.
    """
    if DRY_RUN:
        logger.info(f"DRY-RUN: Would create .nojekyll file in {report_dir}")
        return
        
    nojekyll_path = os.path.join(report_dir, ".nojekyll")
    with open(nojekyll_path, "w") as f:
        pass
    
    logger.info(f"Created .nojekyll file at {nojekyll_path}")


def get_branch_name() -> str:
    """Get the current branch name from environment or git command.
    
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
            git_head_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '.git', 'HEAD')
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
    """Update index.html with JavaScript to dynamically update branch information.
    
    Args:
        report_dir: Path to the Allure report directory.
        branch: Branch name to add.
    """
    index_html = os.path.join(report_dir, "index.html")
    if not os.path.exists(index_html):
        logger.warning(f"index.html not found at {index_html}")
        return
    
    # Path to JavaScript files
    js_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "js")
    branch_js_path = os.path.join(js_dir, "branch_position.js")
    
    if not os.path.exists(branch_js_path):
        logger.error(f"JavaScript file not found: {branch_js_path}")
        return
        
    try:
        # Load JavaScript from external file
        with open(branch_js_path, 'r', encoding='utf-8') as f:
            branch_script_template = f.read()
        
        # Replace placeholders with actual values
        branch_script = branch_script_template\
            .replace('{BRANCH_NAME}', branch)\
            .replace('{VERSION}', __version__)
        
        # Wrap in script tags
        branch_script = f"<script>\n{branch_script}\n</script>"
        
        # Insert into HTML
        with open(index_html, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove any existing branch positioning scripts
        content = re.sub(
            r'<script>\s*//\s*(?:Branch|Immediate script to update branch name).*?</script>',
            '',
            content,
            flags=re.DOTALL
        )
        
        # Insert script in the head
        if '<head>' in content:
            content = content.replace('<head>', f'<head>\n{branch_script}')
            with open(index_html, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Added branch update and positioning script to {index_html}")
        else:
            logger.warning(f"Could not find <head> tag in {index_html}")
    except Exception as e:
        logger.error(f"Error adding branch script to index.html: {str(e)}")


def fix_html_title_tags(report_dir: str) -> None:
    """Fix date format in HTML title tags.
    
    Args:
        report_dir: Path to the Allure report directory.
    """
    today = get_current_date_formatted()
    
    # Get branch name for the script
    branch = get_branch_name()
    
    if DRY_RUN:
        logger.info(f"DRY-RUN: Would update HTML title tags with date {today}")
        return
    
    html_files = glob.glob(os.path.join(report_dir, "**", "*.html"), recursive=True)
    updated_count = 0
    
    for html_file in html_files:
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Fix HTML title tag
            new_content = re.sub(
                r'<title>(?:Allure Report|ALLURE REPORT)(?:\s+\d{1,2}[-/]\d{1,2}[-/]\d{4})?</title>', 
                f'<title>ALLURE REPORT {today}</title>', 
                content
            )
            
            # Fix visible title in the HTML content - more specific pattern matching
            # Match both MM/DD/YYYY and DD-MM-YYYY formats
            date_patterns = [
                # Match "ALLURE REPORT MM/DD/YYYY" format seen in screenshot
                r'(ALLURE\s+REPORT\s+)(\d{1,2})/(\d{1,2})/(\d{4})',
                # Also match other possible formats
                r'(ALLURE\s+REPORT\s+)(\d{1,2})-(\d{1,2})-(\d{4})',
                r'(Allure\s+Report\s+)(\d{1,2})/(\d{1,2})/(\d{4})',
                r'(Allure\s+Report\s+)(\d{1,2})-(\d{1,2})-(\d{4})'
            ]
            
            for pattern in date_patterns:
                # Replace with the correct DD-MM-YYYY format
                # Group 2 is the month, 3 is the day, 4 is the year in the regex
                new_content = re.sub(
                    pattern,
                    lambda m: f"{m.group(1)}{m.group(3)}-{m.group(2)}-{m.group(4)}" if len(m.groups()) >= 4 else f"{m.group(1)}{today}",
                    new_content,
                    flags=re.IGNORECASE
                )
            
            # Find and fix the main header date format from the screenshot
            # Direct replacement for the exact format from the screenshot
            main_pattern = r'(ALLURE REPORT )(\d)/(\d{2})/(\d{4})'
            new_content = re.sub(
                main_pattern,
                lambda m: f'{m.group(1)}{m.group(3)}-0{m.group(2)}-{m.group(4)}',
                new_content
            )
            
            # Try with full month number
            main_pattern2 = r'(ALLURE REPORT )(\d{2})/(\d{2})/(\d{4})'
            new_content = re.sub(
                main_pattern2,
                lambda m: f'{m.group(1)}{m.group(3)}-{m.group(2)}-{m.group(4)}',
                new_content
            )
            
            # Inject JavaScript for SPA interfaces like the one in the screenshot
            if html_file.endswith('index.html'):
                logger.info(f"Processing index.html, injecting dynamic content fix script")
                
                # Load date formatter JavaScript from external file
                js_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "js")
                date_js_path = os.path.join(js_dir, "date_formatter.js")
                
                if os.path.exists(date_js_path):
                    # Remove any existing date formatting scripts
                    new_content = re.sub(
                        r'<script>\s*//\s*(?:Date format standardization|Script to fix date formats).*?</script>',
                        '',
                        new_content,
                        flags=re.DOTALL
                    )
                    
                    with open(date_js_path, 'r', encoding='utf-8') as f:
                        date_script_template = f.read()
                    
                    # Replace placeholder with actual version
                    date_script = date_script_template.replace('{VERSION}', __version__)
                    
                    # Wrap in script tags
                    date_fix_script = f"\n<script>\n{date_script}\n</script>\n"
                    
                    # Add the script just before the closing body tag
                    if '</body>' in new_content:
                        new_content = new_content.replace('</body>', date_fix_script + '</body>')
                        logger.info("Injected date format fixing script into index.html")
                else:
                    logger.warning(f"Date formatter JavaScript not found: {date_js_path}")
            
            if new_content != content:
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                updated_count += 1
        except Exception as e:
            logger.error(f"Error fixing title in {html_file}: {str(e)}")
    
    logger.info(f"Fixed date format in {updated_count} HTML files")


def fix_js_date_formats(report_dir: str) -> None:
    """Fix date formats in JavaScript files.
    
    Args:
        report_dir: Path to the Allure report directory.
    """
    today = get_current_date_formatted()
    
    js_files = glob.glob(os.path.join(report_dir, "**", "*.js"), recursive=True)
    fixed_count = 0
    
    for js_file in js_files:
        try:
            with open(js_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            modified = False
            
            # Replace date strings directly using regex pattern matching and direct string replacement
            date_patterns = [
                r'ALLURE\s+REPORT\s+\d{1,2}/\d{1,2}/\d{4}',
                r'Allure\s+Report\s+\d{1,2}/\d{1,2}/\d{4}',
                r'ALLURE\s+REPORT\s+\d{1,2}-\d{1,2}-\d{4}',
                r'Allure\s+Report\s+\d{1,2}-\d{1,2}-\d{4}'
            ]
            
            for pattern in date_patterns:
                regex = re.compile(pattern, re.IGNORECASE)
                matches = regex.findall(content)
                for match in matches:
                    content = content.replace(match, f'ALLURE REPORT {today}')
                    modified = True
            
            # Also look for title fields in JSON-like structures
            title_patterns = [
                r'"title"\s*:\s*"[^"]*\d{1,2}/\d{1,2}/\d{4}[^"]*"',
                r'"title"\s*:\s*"[^"]*\d{1,2}-\d{1,2}-\d{4}[^"]*"'
            ]
            
            for pattern in title_patterns:
                regex = re.compile(pattern, re.IGNORECASE)
                matches = regex.findall(content)
                for match in matches:
                    # Extract just the part between quotes after title:
                    content = content.replace(match, f'"title":"ALLURE REPORT {today}"')
                    modified = True
            
            # Special case for app.js - this is where the main UI component renders
            if os.path.basename(js_file) == 'app.js':
                logger.info(f"Processing app.js, using dynamic date formatter script from js/date_formatter.js")
                
                # Load date formatter JavaScript from external file
                js_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "js")
                inline_date_js_path = os.path.join(js_dir, "inline_date_formatter.js")
                
                if not os.path.exists(inline_date_js_path):
                    logger.warning(f"Inline date formatter JavaScript not found at {inline_date_js_path}, creating it...")
                    os.makedirs(js_dir, exist_ok=True)
                    
                    # Get the template file path
                    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                               "templates", "inline_date_formatter.js.template")
                    
                    # Check if template exists
                    if os.path.exists(template_path):
                        # Copy from template
                        with open(template_path, 'r', encoding='utf-8') as src, \
                             open(inline_date_js_path, 'w', encoding='utf-8') as dst:
                            dst.write(src.read())
                        logger.info(f"Created inline date formatter JS from template at {inline_date_js_path}")
                    else:
                        logger.warning(f"Template file not found at {template_path}, creating a basic version...")
                        # Create the template directory if it doesn't exist
                        template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
                        os.makedirs(template_dir, exist_ok=True)
                        
                        # Copy from existing file if it exists
                        if os.path.exists("ci/scripts/js/inline_date_formatter.js"):
                            with open("ci/scripts/js/inline_date_formatter.js", 'r', encoding='utf-8') as src, \
                                 open(template_path, 'w', encoding='utf-8') as dst:
                                dst.write(src.read())
                            logger.info(f"Created template from existing JS file at {template_path}")
                            
                            # Also copy to destination
                            with open("ci/scripts/js/inline_date_formatter.js", 'r', encoding='utf-8') as src, \
                                 open(inline_date_js_path, 'w', encoding='utf-8') as dst:
                                dst.write(src.read())
                        else:
                            logger.error(f"Could not find any source for inline date formatter JS")
                            # Don't proceed with this part if we can't get the script
                            continue
                
                # Read the script from the external file
                with open(inline_date_js_path, 'r', encoding='utf-8') as f:
                    inline_date_script = f.read()
                
                # Inject our script at the end, before the closing script tag
                if '</script>' in content:
                    parts = content.rsplit('</script>', 1)
                    content = parts[0] + inline_date_script + '</script>' + parts[1]
                    modified = True
                    logger.info("Injected date format fixing script into app.js")
            
            if modified:
                with open(js_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                fixed_count += 1
        except Exception as e:
            logger.warning(f"Error fixing JS date formats in {js_file}: {e}")
    
    logger.info(f"Fixed date formats in {fixed_count} JavaScript files")


def fix_json_timestamps(report_dir: str) -> None:
    """Fix timestamp format in JSON files.
    
    Args:
        report_dir: Path to the Allure report directory.
    """
    json_files = glob.glob(os.path.join(report_dir, "**", "*.json"), recursive=True)
    fixed_count = 0
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Fix ISO timestamps to DD-MM-YYYY HH:MM:SS
            pattern = r'(\d{4}).(\d{2}).(\d{2})T(\d{2}):(\d{2}):(\d{2})'
            replacement = r'\3-\2-\1 \4:\5:\6'
            
            new_content = re.sub(pattern, replacement, content)
            
            if new_content != content:
                with open(json_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                fixed_count += 1
        except Exception as e:
            logger.warning(f"Error fixing JSON timestamp in {json_file}: {e}")
    
    logger.info(f"Fixed timestamps in {fixed_count} JSON files")


def add_cache_control(report_dir: str) -> None:
    """Add cache control headers and meta tags.
    
    Args:
        report_dir: Path to the Allure report directory.
    """
    # Create _headers file for GitHub Pages
    headers_content = """/*
  Cache-Control: no-cache, no-store, must-revalidate
  Pragma: no-cache
  Expires: 0
"""
    with open(os.path.join(report_dir, "_headers"), "w") as f:
        f.write(headers_content)
    
    # Load cache headers template
    cache_template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                      "templates", "cache_headers.html")
    
    if not os.path.exists(cache_template_path):
        logger.warning(f"Cache headers template not found at {cache_template_path}, creating it...")
        template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
        os.makedirs(template_dir, exist_ok=True)
        
        # Create cache headers template
        with open(cache_template_path, 'w', encoding='utf-8') as f:
            f.write("""<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">""")
        logger.info(f"Created cache headers template at {cache_template_path}")
    
    # Read the cache headers template
    with open(cache_template_path, 'r', encoding='utf-8') as f:
        cache_headers = f.read()
    
    # Add cache control meta tags to HTML files
    html_files = glob.glob(os.path.join(report_dir, "**", "*.html"), recursive=True)
    fixed_count = 0
    
    for html_file in html_files:
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if cache meta tags already exist
            if '<meta http-equiv="Cache-Control"' not in content:
                cache_tags = f'<head>\n{cache_headers}'
                new_content = content.replace('<head>', cache_tags)
                
                if new_content != content:
                    with open(html_file, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    fixed_count += 1
        except Exception as e:
            logger.error(f"Error adding cache control to {html_file}: {str(e)}")
    
    logger.info(f"Added cache control meta tags to {fixed_count} HTML files")


def remove_problematic_elements(report_dir: str) -> None:
    """Remove elements that might cause loading or display issues.
    
    Args:
        report_dir: Path to the Allure report directory.
    """
    # Load spinner fix CSS template
    spinner_css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                   "templates", "spinner_fix.css")
    
    if not os.path.exists(spinner_css_path):
        logger.warning(f"Spinner CSS template not found at {spinner_css_path}, creating it...")
        template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
        os.makedirs(template_dir, exist_ok=True)
        
        # Create spinner fix CSS template
        with open(spinner_css_path, 'w', encoding='utf-8') as f:
            f.write("""/* Ensure spinners don't stay visible indefinitely */
.spinner, .spinner_centered, [class*="spinner"] {
  animation-duration: 2s !important;
  animation-iteration-count: 1 !important;
}""")
        logger.info(f"Created spinner CSS template at {spinner_css_path}")
    
    # Read the spinner CSS template
    with open(spinner_css_path, 'r', encoding='utf-8') as f:
        spinner_css = f.read()
    
    html_files = glob.glob(os.path.join(report_dir, "**", "*.html"), recursive=True)
    fixed_count = 0
    
    for html_file in html_files:
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            modified = False
            
            # Remove meta refresh tags
            if '<meta http-equiv="refresh"' in content:
                new_content = re.sub(r'<meta\s+http-equiv=["\']refresh["\'][^>]*>', '', content)
                if new_content != content:
                    content = new_content
                    modified = True
            
            # Add CSS to ensure spinners don't stay visible
            if '</head>' in content and 'spinner-fix-styles' not in content:
                spinner_style_block = f"<style id=\"spinner-fix-styles\">\n{spinner_css}\n</style>\n</head>"
                new_content = content.replace('</head>', spinner_style_block)
                if new_content != content:
                    content = new_content
                    modified = True
            
            if modified:
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                fixed_count += 1
        except Exception as e:
            logger.error(f"Error fixing problematic elements in {html_file}: {str(e)}")
    
    logger.info(f"Removed problematic elements from {fixed_count} HTML files")


def create_dummy_report(report_dir: str) -> None:
    """Create a dummy report when no test results are available.
    
    Args:
        report_dir: Path to create the dummy report.
    """
    os.makedirs(report_dir, exist_ok=True)
    today = get_current_date_formatted()
    
    # Get the template file path
    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "dummy_report.html")
    
    # Check if template exists
    if not os.path.exists(template_path):
        logger.warning(f"Template file not found at {template_path}, creating a minimal version...")
        
        # Create the template directory if it doesn't exist
        template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
        os.makedirs(template_dir, exist_ok=True)
        
        # Create a minimal fallback template if we can't find the real one
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write("""<!DOCTYPE html>
<html>
<head><title>ALLURE REPORT {today}</title></head>
<body>
  <h1>ALLURE REPORT {today}</h1>
  <p>No test results available. Template file missing.</p>
  <p>Generated on: {timestamp}</p>
</body>
</html>""")
        logger.info(f"Created minimal fallback template at {template_path}")
        logger.warning(f"Please restore the proper template at {template_path} for better formatting")
    
    # Read the template file
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # Replace placeholders with values
    dummy_html = template_content.replace('{today}', today).replace(
        '{timestamp}', datetime.now().strftime("%d-%m-%Y %H:%M:%S"))
    
    # Write the HTML to index.html
    with open(os.path.join(report_dir, "index.html"), "w", encoding='utf-8') as f:
        f.write(dummy_html)
    
    # Create cache control files
    add_cache_control(report_dir)
    create_nojekyll_file(report_dir)
    
    logger.info("Created dummy report")


def parse_args():
    """Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description='Customize Allure reports for CI/CD')
    parser.add_argument('report_dir', nargs='?', default=os.environ.get('ALLURE_REPORT_DIR', 'reports/allure-report'),
                      help='Path to the Allure report directory')
    parser.add_argument('--dummy', action='store_true', default=os.environ.get('ALLURE_CREATE_DUMMY', 'false').lower() == 'true',
                      help='Create a dummy report if no results available')
    parser.add_argument('--branch', default=os.environ.get('ALLURE_BRANCH', None),
                      help='Specify branch name (overrides auto-detection)')
    parser.add_argument('--dry-run', action='store_true',
                      help='Test run without making changes')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}',
                      help='Show version information and exit')
    
    return parser.parse_args()


def main() -> int:
    """Entry point for the script."""
    global DRY_RUN
    
    args = parse_args()
    
    # Set dry run mode if specified
    DRY_RUN = args.dry_run
    if DRY_RUN:
        logger.info("Running in dry-run mode, no changes will be applied")
    
    report_dir = args.report_dir
    create_dummy = args.dummy
    custom_branch = args.branch
    
    logger.info(f"Processing Allure report in {report_dir}...")
    
    # Create dummy report if requested
    if create_dummy:
        create_dummy_report(report_dir)
        logger.info("Dummy report created successfully!")
        return 0
    
    # Ensure the directory exists
    if not os.path.isdir(report_dir):
        logger.error(f"Error: Directory {report_dir} does not exist!")
        return 1
    
    # Check if directory is empty
    if not os.listdir(report_dir):
        logger.warning(f"Warning: Directory {report_dir} is empty. Creating dummy report.")
        create_dummy_report(report_dir)
        return 0
    
    # Apply customizations (in appropriate order to minimize file reads/writes)
    try:
        # 1. Fix the date formats in various files
        fix_html_title_tags(report_dir)
        fix_js_date_formats(report_dir)
        fix_json_timestamps(report_dir)
        
        # 2. Remove problematic elements causing loading issues
        remove_problematic_elements(report_dir)
        
        # 3. Add cache control
        add_cache_control(report_dir)
        
        # 4. Add branch info (with custom branch if provided)
        add_branch_info(report_dir, custom_branch)
        
        # 5. Create .nojekyll file
        create_nojekyll_file(report_dir)
        
        logger.info("Allure report customization completed successfully!")
        return 0
    except Exception as e:
        logger.error(f"Error customizing Allure report: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main()) 