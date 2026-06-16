import pytest

from core.drivers.factory import create_driver


@pytest.fixture
def driver(request):
    """Create and yield a framework-agnostic BaseDriver for a test.

    The concrete framework is selected by ``--framework`` (default ``selenium``) and
    built by ``core.drivers.factory.create_driver``; the driver is ``quit()`` after
    the test. An unsupported framework fails loudly as a pytest usage error.

    Yields:
        BaseDriver: The configured driver for test execution.
    """
    framework = request.config.getoption("framework")
    try:
        web_driver = create_driver(framework)
    except (NotImplementedError, ValueError) as exc:
        raise pytest.UsageError(str(exc)) from exc

    yield web_driver
    web_driver.quit()
