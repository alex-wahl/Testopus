"""Local fixtures for the Toolshop API examples.

Kept here (a local conftest) rather than in the global ``pytest_plugins`` list so a web-only
install never imports ``requests`` / ``core.api``. Reads the ``toolshop`` config block for the
API base URL and the public demo account.
"""

import pytest

from core.api.client import ApiClient


@pytest.fixture
def api_client(config):
    """Unauthenticated client pointed at the configured Toolshop API base URL."""
    api_url = config["configuration"]["toolshop"]["api_url"]
    return ApiClient(api_url)


@pytest.fixture
def auth_token(api_client, config):
    """Log in with the public demo account and return a bearer token.

    These auth examples depend on the upstream public demo account staying intact; if its
    password is rotated upstream, the authed tests fail at setup with a clear message.
    """
    creds = config["configuration"]["toolshop"]
    response = api_client.post(
        "/users/login",
        json={"email": creds["email"], "password": creds["password"]},
    )
    assert response.status_code == 200, f"Demo login failed ({response.status_code})"
    return response.json()["access_token"]


@pytest.fixture
def authed_client(config, auth_token):
    """Client carrying the demo account's bearer token."""
    api_url = config["configuration"]["toolshop"]["api_url"]
    return ApiClient(api_url, token=auth_token)
