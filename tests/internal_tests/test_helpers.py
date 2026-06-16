import os

from utils.helpers import get_config_path, get_project_root


def test_project_root_contains_pyproject():
    root = get_project_root()
    assert os.path.isdir(root)
    assert os.path.exists(os.path.join(root, "pyproject.toml"))


def test_get_config_path_default():
    path = get_config_path(override=False)
    assert path.endswith(os.path.join("config", "yaml_configs", "default.yaml"))


def test_get_config_path_override():
    path = get_config_path(override=True)
    assert path.endswith(os.path.join("config", "yaml_configs", "override.yaml"))
