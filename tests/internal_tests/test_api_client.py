"""Unit tests for the API client (core/api/client.py) — ``requests`` is mocked.

No network: verifies URL building, headers (Accept + bearer Authorization), that error
status codes are returned (NOT raised), and that base_url is required.
"""

import pytest

from core.api.client import ApiClient


def _mock_response(mocker, status=200, payload=None):
    response = mocker.Mock()
    response.status_code = status
    response.json.return_value = payload or {}
    return response


def test_requires_base_url():
    with pytest.raises(ValueError):
        ApiClient("")


def test_get_builds_url_and_sends_accept_header(mocker):
    get = mocker.patch(
        "core.api.client.requests.get", return_value=_mock_response(mocker)
    )
    ApiClient("https://api.test/").get("/products")
    assert get.call_args.args[0] == "https://api.test/products"
    headers = get.call_args.kwargs["headers"]
    assert headers["Accept"] == "application/json"
    assert "Authorization" not in headers


def test_token_sets_bearer_authorization(mocker):
    get = mocker.patch(
        "core.api.client.requests.get", return_value=_mock_response(mocker)
    )
    ApiClient("https://api.test", token="abc123").get("favorites")
    assert get.call_args.kwargs["headers"]["Authorization"] == "Bearer abc123"


def test_does_not_raise_on_error_status(mocker):
    mocker.patch(
        "core.api.client.requests.get",
        return_value=_mock_response(mocker, status=404),
    )
    response = ApiClient("https://api.test").get("/missing")
    assert response.status_code == 404  # returned, not raised


def test_post_sends_json_body(mocker):
    post = mocker.patch(
        "core.api.client.requests.post", return_value=_mock_response(mocker)
    )
    ApiClient("https://api.test").post("/users/login", json={"email": "a@b.test"})
    assert post.call_args.kwargs["json"] == {"email": "a@b.test"}
