#!/usr/bin/env python3
"""Utility functions for Allure report customization.

This package contains utility modules with helper functions used across the project.

Modules:
    constants: Common constants used throughout the customization process
    file_utils: File system utility functions for file operations
"""

# Import all modules to make them available at package level
from . import constants, file_utils

# Export key functions for easy access
from .file_utils import ensure_dir_exists, modify_file, read_file, write_file
