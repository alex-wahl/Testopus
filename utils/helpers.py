import sys
import os

def get_project_root() -> str:
    """
    Fetches the root directory of the project.
    :return: str - the root directory of the project.
    """
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_config_path(override: bool = False) -> str:
    """
    Fetches the path to the config file based on the override flag.
    :param override: bool - if True, the override config file is fetched, otherwise the default config file is fetched.
    :return: str - the path to the config file.
    """
    if override:
        return os.path.join(get_project_root(), "config", "yaml_configs", "override.yaml")
    else:
        return os.path.join(get_project_root(), "config", "yaml_configs", "default.yaml")
