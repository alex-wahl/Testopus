import pytest

def test_basic_functionality():
    """A basic test that always passes to verify the test framework is working."""
    assert True

def test_environment():
    """Verify that the environment is set up correctly."""
    import os
    import sys
    
    # Just print some debug info
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
    
    # Verify Python can find modules
    import pytest
    assert pytest.__name__ == "pytest" 