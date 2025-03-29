#!/usr/bin/env python3
"""Allure Report Customization Modules.

This package contains the core modules used for customizing Allure reports.
Each module provides specific functionality for manipulating report files.
"""

# Import all modules to make them available at package level
from . import branch_info, cache_control, date_formatter, dummy_report, error_handling, history

# Export key functions for easy access
from .branch_info import add_branch_info, get_branch_name
from .cache_control import add_cache_control, create_nojekyll_file
from .date_formatter import fix_date_formats, get_current_date_formatted
from .dummy_report import create_dummy_report
from .history import preserve_history
