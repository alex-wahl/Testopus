import yaml
import sys
import os

# Add the project root to the Python path to enable absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from utils.helpers import get_config_path

OVERRIDE_KEY = "--override"

def load_config(config_path: str) -> dict:
    """
    Loads a configuration from a YAML file.
    
    :param config_path: The path to the configuration file
    :return: A dictionary containing the configuration
    """
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)


def merge_configs(default_config: dict, override_config: dict) -> dict:
    """
    Recursively merges two configuration dictionaries.
    Override values take precedence over default values, but preserves the structure
    from default_config when possible.
    
    :param default_config: The base configuration dictionary
    :param override_config: The configuration with values to override or add
    :return: A merged configuration dictionary
    """
    if not isinstance(default_config, dict) or not isinstance(override_config, dict):
        # If either is not a dict, override takes precedence
        return override_config
        
    result = default_config.copy()
    
    for key, override_value in override_config.items():
        if key in result:
            # Key exists in both configs
            if isinstance(result[key], dict) and isinstance(override_value, dict):
                # Both values are dicts, recursively merge
                result[key] = merge_configs(result[key], override_value)
            else:
                # Override the value
                result[key] = override_value
        else:
            # Key only in override, add it
            result[key] = override_value
            
    return result


def load_config_from_cli(pytest_config=None) -> dict:
    """
    Load configuration based on command line arguments or pytest fixture.
    
    :param pytest_config: Optional pytest config object from fixture
    :return: Configuration dictionary with default and override values merged if needed
    """
    # Load default configuration
    default_config_path = get_config_path(override=False)
    default_config = load_config(default_config_path)
    
    # Determine if override should be used
    use_override = (
        (pytest_config and hasattr(pytest_config, 'getoption') and pytest_config.getoption("override")) or
        OVERRIDE_KEY in sys.argv
    )
    
    # Return merged config if override is enabled, otherwise return default
    if not use_override:
        return default_config
        
    # Load and merge override configuration
    override_config_path = get_config_path(override=True)
    override_config = load_config(override_config_path)
    return merge_configs(default_config, override_config)