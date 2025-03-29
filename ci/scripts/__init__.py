#!/usr/bin/env python3
"""Allure Report Customization Scripts.

This package contains scripts and modules for customizing Allure reports.
The main entry point is customize_allure_report.py.
"""

# Import version from main script
try:
    from .customize_allure_report import __version__
except ImportError:
    __version__ = "0.0.0"  # Default version if not found
