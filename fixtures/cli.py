import pytest

from core.config.config_loader import load_config_from_cli


def pytest_addoption(parser):
    parser.addoption(
        "--config",
        required=False,
        action="store",
        default=None,
        type=str,
        help="Path to an explicit base config file (overrides the default location).",
    )
    parser.addoption(
        "--override",
        required=False,
        action="store_true",
        default=False,
        help="Flag to merge the override configuration over the default.",
    )
    parser.addoption(
        "--framework",
        required=False,
        action="store",
        default="selenium",
        help=(
            "Web automation framework: 'selenium' (default). 'playwright'/'appium' "
            "are on the roadmap and fail loudly until implemented."
        ),
    )
    parser.addoption(
        "--ai",
        required=False,
        action="store_true",
        default=False,
        help="Reserved for AI-assisted features (not yet wired).",
    )


@pytest.fixture(scope="session")
def config(request) -> dict:
    """
    Fixture that provides configuration for tests.
    Uses load_config_from_cli to handle configuration loading and merging.

    :param request: The pytest request object
    :return: Configuration dictionary
    """
    return load_config_from_cli(request.config)
