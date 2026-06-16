import copy
import logging
import os
import re
import sys

import yaml
from dotenv import load_dotenv
from pydantic import ValidationError

from core.config.schema import RootConfig
from utils.helpers import get_config_path

OVERRIDE_KEY = "--override"

logger = logging.getLogger(__name__)

# Load a local .env (if present) so ${VAR} interpolation and credential injection
# work outside CI. python-dotenv is a project dependency; this is a no-op when no
# .env exists.
load_dotenv()

# Matches ${VAR} and ${VAR:-default}
_ENV_VAR_PATTERN = re.compile(r"\$\{([^}:]+)(?::-([^}]*))?\}")


class ConfigError(Exception):
    """Raised when a configuration file is missing, unreadable, or malformed."""


def _interpolate_env(value):
    """Recursively replace ``${VAR}`` / ``${VAR:-default}`` with environment values.

    Secrets and environment-specific values live in the environment (or a local
    ``.env``), never in committed YAML. A missing variable with no default resolves
    to an empty string with a warning (fail-open) so config loading never crashes on
    an unset optional variable.

    :param value: A config value (dict, list, str, or scalar).
    :return: The value with any ``${VAR}`` references substituted.
    """
    if isinstance(value, dict):
        return {key: _interpolate_env(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_interpolate_env(item) for item in value]
    if not isinstance(value, str):
        return value

    def _replace(match):
        var_name, default = match.group(1), match.group(2)
        env_value = os.environ.get(var_name)
        if env_value is not None:
            return env_value
        if default is not None:
            return default
        logger.warning(
            "Config references unset environment variable ${%s}; using empty string.",
            var_name,
        )
        return ""

    return _ENV_VAR_PATTERN.sub(_replace, value)


def load_config(config_path: str) -> dict:
    """
    Loads a configuration from a YAML file, substituting ``${VAR}`` env references.

    :param config_path: The path to the configuration file
    :return: A dictionary containing the configuration
    :raises ConfigError: If the file is missing, not valid YAML, or not a mapping.
    """
    try:
        with open(config_path, "r") as file:
            data = yaml.safe_load(file)
    except FileNotFoundError as exc:
        raise ConfigError(f"Config file not found: {config_path}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(
            f"Invalid YAML in config file '{config_path}': {exc}"
        ) from exc

    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise ConfigError(
            f"Config file '{config_path}' must contain a mapping at the top level, "
            f"got {type(data).__name__}."
        )
    return _interpolate_env(data)


def merge_configs(default_config: dict, override_config: dict) -> dict:
    """
    Recursively merges two configuration dictionaries without aliasing either input.

    Override values take precedence; nested mappings are merged recursively. Inputs
    are never mutated and the result shares no nested objects with them (deep copy),
    so a session-scoped default config cannot be corrupted by a later mutation of the
    merged result.

    :param default_config: The base configuration dictionary
    :param override_config: The configuration with values to override or add
    :return: A merged configuration dictionary
    """
    if not isinstance(default_config, dict) or not isinstance(override_config, dict):
        # If either is not a dict, override takes precedence
        return copy.deepcopy(override_config)

    result = copy.deepcopy(default_config)

    for key, override_value in override_config.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(override_value, dict)
        ):
            # Both values are dicts, recursively merge
            result[key] = merge_configs(result[key], override_value)
        else:
            # Override / add the value (deep-copied so result never aliases override)
            result[key] = copy.deepcopy(override_value)

    return result


def _validate_config(config: dict) -> dict:
    """Validate the assembled config against the schema; fail fast on a bad shape.

    Lenient (extra keys allowed) — only the known load-bearing fields are checked — so a
    malformed config raises a clear ``ConfigError`` here instead of a cryptic ``KeyError`` deep
    in a test. Returns the (unchanged) config so dict-based consumers keep working.

    :raises ConfigError: If the config violates the schema.
    """
    try:
        RootConfig.model_validate(config)
    except ValidationError as exc:
        raise ConfigError(f"Configuration failed validation:\n{exc}") from exc
    return config


def load_config_from_cli(pytest_config=None) -> dict:
    """
    Load configuration based on command line arguments or pytest fixture.

    Honors ``--config`` (an explicit path to the base config file) and ``--override``
    (merge the override file over the base).

    :param pytest_config: Optional pytest config object from fixture
    :return: Configuration dictionary with default and override values merged if needed
    """
    explicit_path = None
    if pytest_config is not None and hasattr(pytest_config, "getoption"):
        explicit_path = pytest_config.getoption("config")

    default_config_path = explicit_path or get_config_path(override=False)
    default_config = load_config(default_config_path)

    # Determine if override should be used
    use_override = (
        pytest_config is not None
        and hasattr(pytest_config, "getoption")
        and pytest_config.getoption("override")
    ) or OVERRIDE_KEY in sys.argv

    # Return merged config if override is enabled, otherwise return default
    if not use_override:
        return _validate_config(default_config)

    # Load and merge override configuration
    override_config_path = get_config_path(override=True)
    override_config = load_config(override_config_path)
    return _validate_config(merge_configs(default_config, override_config))
