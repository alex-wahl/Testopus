"""Toolshop API example — JWT auth: login, rejection, and an authenticated read."""

import pytest


@pytest.mark.feature("Toolshop API")
@pytest.mark.story("Authentication")
class TestAuthApi:
    """The /users/login flow and bearer-token enforcement."""

    @pytest.mark.severity("critical")
    def test_login_returns_a_token(self, api_client, config):
        creds = config["configuration"]["toolshop"]
        response = api_client.post(
            "/users/login",
            json={"email": creds["email"], "password": creds["password"]},
        )
        assert response.status_code == 200
        assert response.json().get("access_token"), "no access_token in login response"

    @pytest.mark.severity("normal")
    def test_login_with_bad_password_is_rejected(self, api_client, config):
        creds = config["configuration"]["toolshop"]
        response = api_client.post(
            "/users/login",
            json={"email": creds["email"], "password": "definitely-wrong"},
        )
        assert response.status_code in (401, 422)

    @pytest.mark.severity("normal")
    def test_protected_endpoint_requires_authentication(self, api_client):
        # Without a token a protected endpoint must reject the request.
        assert api_client.get("/favorites").status_code == 401

    @pytest.mark.severity("normal")
    def test_authenticated_request_succeeds(self, authed_client):
        # With a valid bearer token the same endpoint is reachable.
        assert authed_client.get("/favorites").status_code == 200
