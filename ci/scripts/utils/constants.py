#!/usr/bin/env python3
"""Constants for Allure report customization.

This module provides constants used throughout the Allure report customization process,
defining paths, environment variables, file patterns, and predefined content.

Attributes:
    VERSION: The version string for the customization script
    SCRIPT_DIR: Path to the scripts directory
    TEMPLATES_DIR: Path to the templates directory
    JS_DIR: Path to the JavaScript files directory
    PROJECT_ROOT: Path to the project root directory
    DEFAULT_REPORTS_DIR: Path to the reports directory
    DEFAULT_REPORT_DIR: Path to the Allure report directory
    DEFAULT_RESULTS_DIR: Path to the Allure results directory
    DEFAULT_HISTORY_DIR: Path to the Allure history directory
    ENV_*: Environment variable names
    *_FILES: File pattern globs
    *_FILE: File names
    JS_*: JavaScript file names
    DATE_PATTERN_*: Regex patterns for date formats
    ISO_TIMESTAMP_PATTERN: Regex pattern for ISO timestamps
    CACHE_CONTROL_*: Content for cache control directives
"""

import os
from pathlib import Path

# Version
VERSION = "1.3.1"

# Directory paths (relative to script location)
SCRIPT_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATES_DIR = SCRIPT_DIR / "templates"
JS_DIR = SCRIPT_DIR / "js"

# Project root directory - one more level up from script directory
PROJECT_ROOT = Path(os.path.dirname(os.path.dirname(SCRIPT_DIR)))

# Default paths (relative to project root)
DEFAULT_REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")
DEFAULT_REPORT_DIR = os.path.join(DEFAULT_REPORTS_DIR, "allure-report")
DEFAULT_RESULTS_DIR = os.path.join(DEFAULT_REPORTS_DIR, "allure-results")
DEFAULT_HISTORY_DIR = os.path.join(DEFAULT_REPORTS_DIR, "allure-history")

# Environment variable names
ENV_REPORT_DIR = "ALLURE_REPORT_DIR"
ENV_CREATE_DUMMY = "ALLURE_CREATE_DUMMY"
ENV_BRANCH = "ALLURE_BRANCH"
ENV_PRESERVE_HISTORY = "ALLURE_PRESERVE_HISTORY"
ENV_GITHUB_REF = "GITHUB_REF"
ENV_GITHUB_HEAD_REF = "GITHUB_HEAD_REF"

# File patterns
HTML_FILES = "*.html"
JS_FILES = "*.js"
JSON_FILES = "*.json"

# File names
NOJEKYLL_FILE = ".nojekyll"
ENV_PROPERTIES_FILE = "environment.properties"
ENV_JSON_FILE = os.path.join("widgets", "environment.json")
INDEX_HTML = "index.html"

# JavaScript files
JS_FIX_404_ERRORS = "fix_404_errors.js"
JS_BRANCH_INFO = "branch_info.js"
JS_DATE_FORMATTER = "date_formatter.js"
JS_INLINE_DATE_FORMATTER = "inline_date_formatter.js"

# Regex patterns
DATE_PATTERN_MM_DD_YYYY = r'(\d{1,2})/(\d{1,2})/(\d{4})'
DATE_PATTERN_DD_MM_YYYY = r'(\d{1,2})-(\d{1,2})-(\d{4})'
ISO_TIMESTAMP_PATTERN = r'(\d{4}).(\d{2}).(\d{2})T(\d{2}):(\d{2}):(\d{2})'

# Cache-Control headers
CACHE_CONTROL_HEADERS = """/*
  Cache-Control: no-cache, no-store, must-revalidate
  Pragma: no-cache
  Expires: 0
"""

# Cache-Control meta tags
CACHE_CONTROL_META = """<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">""" 