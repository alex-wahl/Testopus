#!/usr/bin/env python3
"""Basic tests for the customize_allure_report script.

This module contains basic unit tests for validating the core functionality
of the Allure report customization script.
"""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Add project root to Python path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

# Import modules for testing
from ci.scripts import customize_allure_report  # noqa: E402
from ci.scripts.modules.branch_info import get_branch_name  # noqa: E402
from ci.scripts.modules.date_formatter import get_current_date_formatted  # noqa: E402
from ci.scripts.modules.dummy_report import create_dummy_report  # noqa: E402
from ci.scripts.utils.constants import VERSION  # noqa: E402


class TestBasicFunctionality(unittest.TestCase):
    """Basic tests for the customize_allure_report script.

    This test suite validates core functionality of the customize_allure_report script,
    including version consistency, date formatting, branch detection, and dummy report creation.
    """

    def setUp(self):
        """Set up test fixtures.

        Creates a temporary directory structure for testing.
        """
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()
        self.report_dir = os.path.join(self.test_dir, "reports/allure-report")
        os.makedirs(self.report_dir, exist_ok=True)

    def tearDown(self):
        """Tear down test fixtures.

        Removes the temporary directory and all its contents.
        """
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)

    def test_version(self):
        """Test that the version is set correctly.

        Verifies that the version in the main script matches the expected version
        from constants.
        """
        self.assertEqual(customize_allure_report.__version__, VERSION)

    def test_get_current_date_formatted(self):
        """Test that get_current_date_formatted returns a string.

        Verifies that the date formatting function returns a non-empty string.
        """
        date_str = get_current_date_formatted()
        self.assertIsInstance(date_str, str)
        self.assertTrue(len(date_str) > 0)

    def test_get_branch_name(self):
        """Test that get_branch_name returns a string.

        Verifies that the branch detection function returns a non-empty string.
        """
        branch = get_branch_name()
        self.assertIsInstance(branch, str)
        self.assertTrue(len(branch) > 0)

    def test_dummy_report(self):
        """Test creating a dummy report.

        Verifies that the dummy report creation function correctly creates
        the necessary files and directory structure.
        """
        # Remove the report directory
        shutil.rmtree(self.report_dir, ignore_errors=True)
        # Create the dummy report
        create_dummy_report(self.report_dir)
        # Check that the report was created
        self.assertTrue(os.path.exists(self.report_dir))
        self.assertTrue(os.path.exists(os.path.join(self.report_dir, "index.html")))


if __name__ == "__main__":
    unittest.main()
