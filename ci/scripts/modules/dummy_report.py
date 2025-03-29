#!/usr/bin/env python3
"""Dummy report module for Allure report customization.

This module provides functions for creating a dummy report when no test results are available,
ensuring a fallback view for CI/CD pipelines with empty or missing test results.
"""

import os
import logging
from datetime import datetime
from pathlib import Path

# Handle both relative imports for package usage and direct imports for script execution
try:
    from ..utils.file_utils import ensure_dir_exists
    from .cache_control import add_cache_control, create_nojekyll_file
    from .date_formatter import get_current_date_formatted
except ImportError:
    # When run directly
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from utils.file_utils import ensure_dir_exists
    from modules.cache_control import add_cache_control, create_nojekyll_file
    from modules.date_formatter import get_current_date_formatted

# Set up logging
logger = logging.getLogger('allure-customizer.dummy-report')

def create_dummy_report(report_dir: str) -> None:
    """Create a dummy report when no test results are available.
    
    Generates a simple HTML report with current date information when no actual
    test results exist. This ensures CI/CD pipelines always have a report to display,
    even when tests failed to run or no tests were executed.
    
    Args:
        report_dir: Path to create the dummy report.
    """
    ensure_dir_exists(report_dir)
    today = get_current_date_formatted()
    
    # Get the template file path
    template_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                "templates", "dummy_report.html")
    
    # Check if template exists
    if not os.path.exists(template_path):
        logger.warning(f"Template file not found at {template_path}, creating a minimal version...")
        
        # Create the template directory if it doesn't exist
        template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
        ensure_dir_exists(template_dir)
        
        # Create a minimal fallback template if we can't find the real one
        minimal_template = f"""<!DOCTYPE html>
<html>
<head><title>ALLURE REPORT {today}</title></head>
<body>
  <h1>ALLURE REPORT {today}</h1>
  <p>No test results available. Template file missing.</p>
  <p>Generated on: {datetime.now().strftime("%d-%m-%Y %H:%M:%S")}</p>
</body>
</html>"""
        
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(minimal_template)
        logger.info(f"Created minimal fallback template at {template_path}")
        logger.warning(f"Please restore the proper template at {template_path} for better formatting")
    
    # Read the template file
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # Replace placeholders with values
    timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    dummy_html = template_content.replace('{today}', today).replace('{timestamp}', timestamp)
    
    # Write the HTML to index.html
    with open(os.path.join(report_dir, "index.html"), "w", encoding='utf-8') as f:
        f.write(dummy_html)
    
    # Create cache control files
    add_cache_control(report_dir)
    create_nojekyll_file(report_dir)
    
    logger.info("Created dummy report") 