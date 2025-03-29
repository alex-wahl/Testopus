#!/usr/bin/env python3
"""Allure Report Customization Script.

This script customizes the Allure report generated by Allure commandline:
1. Fixes date formats to use DD-MM-YYYY instead of MM/DD/YYYY
2. Adds cache-busting mechanisms to ensure reports are always fresh
3. Implements better formatting for timestamps

Usage:
    python customize_allure_report.py [path_to_report_dir]
    python customize_allure_report.py [path_to_report_dir] --dummy
"""

import os
import sys
import time
import glob
import re
import json
from datetime import datetime
from pathlib import Path


def get_current_timestamp() -> int:
    """Get current timestamp in seconds since epoch.
    
    Returns:
        int: Current timestamp as seconds since epoch.
    """
    return int(time.time())


def get_current_date_formatted() -> str:
    """Get current date in DD-MM-YYYY format.
    
    Returns:
        str: Current date formatted as DD-MM-YYYY.
    """
    return datetime.now().strftime("%d-%m-%Y")


def create_cache_busting_script(report_dir: str, timestamp: int) -> None:
    """Create a JavaScript file that forces cache refresh.
    
    Args:
        report_dir: Path to the Allure report directory.
        timestamp: Timestamp to use for cache busting.
    """
    assets_dir = os.path.join(report_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)
    
    script_content = f"""// Cache-busting script generated on {datetime.now().isoformat()}
document.addEventListener('DOMContentLoaded', function() {{
  // Cache busting redirect
  if(!window.location.search.includes('ts=')) {{
    window.location.href = window.location.href + 
      (window.location.search ? '&' : '?') + 
      'ts={timestamp}';
  }}
  
  // Fix title date format if found
  try {{
    const titleElements = document.querySelectorAll('.allure-report-title, .title, h1');
    const dateRegex = /(ALLURE\\s+REPORT\\s+)(\\d{{1,2}})\\/(\\d{{1,2}})\\/(\\d{{4}})/i;
    
    titleElements.forEach(function(element) {{
      if (element && element.textContent) {{
        const match = element.textContent.match(dateRegex);
        if (match) {{
          // Create DD-MM-YYYY format
          const day = match[3].padStart(2, '0');
          const month = match[2].padStart(2, '0');
          const year = match[4];
          element.textContent = `${{match[1]}}${{day}}-${{month}}-${{year}}`;
          console.log('Fixed title date format via JS');
        }}
      }}
    }});
    
    // Also try to fix document title
    if (document.title.match(/Allure Report \\d{{1,2}}\\/\\d{{1,2}}\\/\\d{{4}}/i)) {{
      document.title = "Allure Report {get_current_date_formatted()}";
      console.log('Fixed document title via JS');
    }}
  }} catch (e) {{
    console.error('Error fixing date format:', e);
  }}
}});
"""
    
    with open(os.path.join(assets_dir, "force-refresh.js"), "w") as f:
        f.write(script_content)
    
    print(f"✅ Created cache-busting script with timestamp {timestamp}")


def add_cache_headers(report_dir: str) -> None:
    """Create _headers file for Netlify-style cache control.
    
    Args:
        report_dir: Path to the Allure report directory.
    """
    headers_content = """/*
  Cache-Control: no-cache, no-store, must-revalidate
  Pragma: no-cache
  Expires: 0
"""
    
    with open(os.path.join(report_dir, "_headers"), "w") as f:
        f.write(headers_content)
    
    print("✅ Added cache control headers")


def add_branch_info(report_dir: str) -> None:
    """Add git branch information to environment properties.
    
    Reads the branch name from GITHUB_REF or GITHUB_HEAD_REF environment variables
    and adds it to the Allure environment.properties file.
    
    Args:
        report_dir: Path to the Allure report directory.
    """
    env_file = os.path.join(report_dir, "environment.properties")
    
    # Try to get branch name from environment variables
    branch = os.environ.get('GITHUB_HEAD_REF', '')  # For pull requests
    if not branch:
        ref = os.environ.get('GITHUB_REF', '')      # For direct pushes
        if ref.startswith('refs/heads/'):
            branch = ref.replace('refs/heads/', '')
    
    if not branch:
        try:
            # Try to get from git command as fallback
            import subprocess
            branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
                                           stderr=subprocess.DEVNULL).decode('utf-8').strip()
        except (subprocess.SubprocessError, FileNotFoundError):
            branch = 'unknown'
    
    # Read existing environment properties
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    else:
        lines = []
    
    # Check if Branch property already exists
    branch_exists = False
    for i, line in enumerate(lines):
        if line.startswith('Branch='):
            lines[i] = f'Branch={branch}\n'
            branch_exists = True
            break
    
    # Add branch if it doesn't exist
    if not branch_exists:
        lines.append(f'Branch={branch}\n')
    
    # Write updated environment properties
    with open(env_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"✅ Added branch information: {branch}")


def fix_date_formats_in_json(report_dir: str) -> None:
    """Fix timestamp format in JSON files.
    
    Args:
        report_dir: Path to the Allure report directory.
    """
    json_files = glob.glob(os.path.join(report_dir, "**", "*.json"), recursive=True)
    pattern = r'(\d{4}).(\d{2}).(\d{2})T(\d{2}):(\d{2}):(\d{2})'
    replacement = r'\3-\2-\1 \4:\5:\6'
    
    count = 0
    for json_file in json_files:
        with open(json_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        new_content = re.sub(pattern, replacement, content)
        
        if new_content != content:
            with open(json_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            count += 1
    
    print(f"✅ Fixed date formats in {count} JSON files")


def fix_title_date_format(report_dir: str) -> None:
    """Fix date format in report titles.
    
    Args:
        report_dir: Path to the Allure report directory.
    """
    today = get_current_date_formatted()
    
    # Find index.html - special direct replacement for the main page
    index_file = os.path.join(report_dir, "index.html")
    if os.path.exists(index_file):
        print(f"✅ Processing index.html directly...")
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Direct substitute any pattern like "ALLURE REPORT MM/DD/YYYY" to our desired format
            # First find the pattern with regex
            title_matches = re.findall(r'ALLURE REPORT \d{1,2}/\d{1,2}/\d{4}', content, re.IGNORECASE)
            if title_matches:
                for match in title_matches:
                    content = content.replace(match, f"ALLURE REPORT {today}")
                    print(f"  - Replaced '{match}' with 'ALLURE REPORT {today}'")
            
            # Also try with regex capturing the date parts
            content = re.sub(
                r'(ALLURE\s+REPORT\s+)\d{1,2}/\d{1,2}/\d{4}', 
                f'\\1{today}', 
                content,
                flags=re.IGNORECASE
            )
            
            # Write the updated content
            with open(index_file, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            print(f"⚠️ Warning: Error updating index.html: {e}")
    
    # Process HTML files
    html_files = glob.glob(os.path.join(report_dir, "**", "*.html"), recursive=True)
    for html_file in html_files:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix title tag
        new_content = re.sub(
            r'<title>Allure Report</title>', 
            f'<title>Allure Report {today}</title>', 
            content
        )
        
        # Fix header titles with date - case insensitive matching
        patterns = [
            r'ALLURE REPORT \d{1,2}/\d{1,2}/\d{4}',  # ALLURE REPORT 3/29/2025
            r'Allure Report \d{1,2}/\d{1,2}/\d{4}',  # Allure Report 3/29/2025
            r'ALLURE REPORT \d{1,2}-\d{1,2}-\d{4}',  # ALLURE REPORT 3-29-2025
            r'Allure Report \d{1,2}-\d{1,2}-\d{4}'   # Allure Report 3-29-2025
        ]
        
        for pattern in patterns:
            new_content = re.sub(
                pattern, 
                f'ALLURE REPORT {today}', 
                new_content,
                flags=re.IGNORECASE
            )
        
        if new_content != content:
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
    
    # Process JavaScript files
    js_files = glob.glob(os.path.join(report_dir, "**", "*.js"), recursive=True)
    for js_file in js_files:
        with open(js_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace dates in various formats - all possible formats
        for pattern in [
            r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b',  # MM/DD/YYYY
            r'\b(\d{4})/(\d{1,2})/(\d{1,2})\b',  # YYYY/MM/DD
            r'\b(\d{1,2})-(\d{1,2})-(\d{4})\b',  # MM-DD-YYYY
            r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b'   # YYYY-MM-DD
        ]:
            new_content = re.sub(
                pattern, 
                f"{today}", 
                new_content
            )
        
        # Direct text replacement for title strings
        for title_pattern in [
            r'ALLURE REPORT \d{1,2}/\d{1,2}/\d{4}',
            r'Allure Report \d{1,2}/\d{1,2}/\d{4}',
            r'"title":"ALLURE REPORT \d{1,2}/\d{1,2}/\d{4}"',
            r'"title":"Allure Report \d{1,2}/\d{1,2}/\d{4}"',
            r'"title": "ALLURE REPORT \d{1,2}/\d{1,2}/\d{4}"',
            r'"title": "Allure Report \d{1,2}/\d{1,2}/\d{4}"'
        ]:
            new_content = re.sub(
                title_pattern, 
                f'ALLURE REPORT {today}', 
                new_content,
                flags=re.IGNORECASE
            )
        
        # Replace date format patterns
        new_content = re.sub(
            r'(date|Date).format.*MM.*DD.*YYYY', 
            r'\1.format("DD-MM-YYYY")', 
            new_content
        )
        
        if new_content != content:
            with open(js_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
    
    # Look for the Widgets JS file specifically (often controls title)
    widgets_files = glob.glob(os.path.join(report_dir, "**", "widgets.js"), recursive=True)
    for widget_file in widgets_files:
        try:
            with open(widget_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Brute force replacement of any MM/DD/YYYY pattern with our desired format
            # This is a more aggressive approach for the widgets.js file
            for month in range(1, 13):
                for day in range(1, 32):
                    for year in [2023, 2024, 2025, 2026]:
                        old_date = f"{month}/{day}/{year}"
                        
                        # Replace in the content
                        content = content.replace(old_date, today)
                        content = content.replace(f'"{old_date}"', f'"{today}"')
                        content = content.replace(f"'{old_date}'", f"'{today}'")
            
            with open(widget_file, 'w', encoding='utf-8') as f:
                f.write(content)
                
            print(f"✅ Fixed dates in widgets.js")
        except Exception as e:
            print(f"⚠️ Warning: Failed to process widgets.js: {e}")
    
    print("✅ Fixed date format in report titles")


def add_cache_busting_to_html(report_dir: str, timestamp: int) -> None:
    """Add cache-busting script to HTML files.
    
    Args:
        report_dir: Path to the Allure report directory.
        timestamp: Timestamp to use for cache busting.
    """
    html_files = glob.glob(os.path.join(report_dir, "**", "*.html"), recursive=True)
    head_tag_with_meta = f'<head><meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate"><script src="assets/force-refresh.js?v={timestamp}"></script>'
    
    for html_file in html_files:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add meta tags and script to head
        new_content = content.replace('<head>', head_tag_with_meta)
        
        if new_content != content:
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
    
    print(f"✅ Added cache-busting to HTML files")


def create_nojekyll_file(report_dir: str) -> None:
    """Create .nojekyll file to prevent GitHub Pages from using Jekyll.
    
    Args:
        report_dir: Path to the Allure report directory.
    """
    with open(os.path.join(report_dir, ".nojekyll"), "w") as f:
        pass
    
    print("✅ Created .nojekyll file")


def create_dummy_report(report_dir: str) -> None:
    """Create a dummy report when no test results are available.
    
    Creates a simple HTML report with error message when no test results exist,
    along with necessary cache control files.
    
    Args:
        report_dir: Path to create the dummy report.
    """
    os.makedirs(report_dir, exist_ok=True)
    
    # Get the template file path
    template_path = os.path.join(os.path.dirname(__file__), "templates", "dummy_report.html")
    
    # Check if template exists
    if not os.path.exists(template_path):
        print(f"⚠️ Warning: Template file not found at {template_path}. Using fallback template.")
        dummy_html = """<!DOCTYPE html>
<html><head><title>Test Report</title></head>
<body><h1>No test results available</h1><p>Generated on: {timestamp}</p></body>
</html>""".format(timestamp=datetime.now().strftime("%d-%m-%Y %H:%M:%S"))
    else:
        # Read the template file
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
        
        # Replace placeholder with current timestamp
        dummy_html = template.format(timestamp=datetime.now().strftime("%d-%m-%Y %H:%M:%S"))
    
    # Write the HTML to index.html
    with open(os.path.join(report_dir, "index.html"), "w", encoding='utf-8') as f:
        f.write(dummy_html)
    
    # Create headers file for cache control
    add_cache_headers(report_dir)
    
    # Create .nojekyll file
    create_nojekyll_file(report_dir)
    
    print("✅ Created dummy report")


def main() -> int:
    """Entry point for the script.
    
    Processes command line arguments and applies appropriate customizations
    to the specified Allure report directory.
    
    Returns:
        int: Exit code (0 for success, 1 for error).
    """
    # Get report directory from command line or use default
    if len(sys.argv) > 1:
        report_dir = sys.argv[1]
    else:
        report_dir = "reports/allure-report"
    
    # Check if we should create a dummy report
    create_dummy = False
    if len(sys.argv) > 2 and sys.argv[2] == "--dummy":
        create_dummy = True
    
    print(f"🔧 Processing Allure report in {report_dir}...")
    
    # Create dummy report if requested
    if create_dummy:
        create_dummy_report(report_dir)
        print("✅ Dummy report created successfully!")
        return 0
    
    # Ensure the directory exists
    if not os.path.isdir(report_dir):
        print(f"❌ Error: Directory {report_dir} does not exist!")
        return 1
    
    # Check if directory is empty
    if not os.listdir(report_dir):
        print(f"⚠️ Warning: Directory {report_dir} is empty. Creating dummy report.")
        create_dummy_report(report_dir)
        return 0
    
    timestamp = get_current_timestamp()
    
    # Apply customizations
    fix_date_formats_in_json(report_dir)
    fix_title_date_format(report_dir)
    create_cache_busting_script(report_dir, timestamp)
    add_cache_headers(report_dir)
    add_branch_info(report_dir)
    add_cache_busting_to_html(report_dir, timestamp)
    create_nojekyll_file(report_dir)
    
    print(f"✅ Allure report customization completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main()) 