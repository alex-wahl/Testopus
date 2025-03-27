import os
import sys

import pytest

# Add the project root to the Python path to enable absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from core.config.config_loader import load_config_from_cli


def pytest_addoption(parser):
    parser.addoption("--config", required=False, action="store", default=None, type=str,
                     help="Required to define a particular test configuration")
    parser.addoption("--override", required=False, action="store_true", default=False,
                     help="Flag to use override configuration")
    parser.addoption("--framework", required=False, action="store", default="selenium",
                     help="Possible frameworks: selenium, playwright")
    parser.addoption("--ai", required=False, action="store_true", default=False,
                     help="Flag to use AI")
    

@pytest.fixture(scope='session')
def config(request) -> dict:
    """
    Fixture that provides configuration for tests.
    Uses load_config_from_cli to handle configuration loading and merging.
    
    :param request: The pytest request object
    :return: Configuration dictionary
    """
    return load_config_from_cli(request.config)