"""Tests for the Testiny client + CLI (tools/testiny/client.py, cli.py).

The network is mocked with pytest-mock — no live Testiny account needed. Verifies the
request shape (URL + ``X-Api-Key`` header), pagination, that the CLI writes the expected
spec, and — critically — that ``TESTINY_API_KEY`` never reaches the logs.
"""

import logging

import pytest

from tools.testiny import cli
from tools.testiny.client import TestinyClient

API_KEY = "SECRET-KEY-do-not-log"

CASE = {
    "id": 123,
    "project_id": 42,
    "title": "Login rejects invalid credentials",
    "priority": "high",
    "template": "TEXT",
    "precondition_text": "User is on the login page.",
    "steps_text": "1. Enter a wrong password.\n2. Submit.",
    "expected_result_text": "An error message is shown.",
}


def _mock_response(mocker, payload):
    response = mocker.Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = payload
    return response


def test_get_testcase_builds_url_and_sends_api_key(mocker):
    get = mocker.patch(
        "tools.testiny.client.requests.get",
        return_value=_mock_response(mocker, CASE),
    )
    client = TestinyClient(API_KEY, "https://app.testiny.io/api/v1")
    assert client.get_testcase(123) == CASE
    url = get.call_args.args[0]
    headers = get.call_args.kwargs["headers"]
    assert url.endswith("/testcase/123")
    assert headers["X-Api-Key"] == API_KEY


def test_client_requires_api_key():
    with pytest.raises(ValueError):
        TestinyClient("")


def test_find_paginates(mocker):
    # First page full (100) -> loop continues; second page short -> loop stops.
    page1 = {"data": [dict(CASE, id=index) for index in range(100)]}
    page2 = {"data": [dict(CASE, id=999)]}
    post = mocker.patch(
        "tools.testiny.client.requests.post",
        side_effect=[_mock_response(mocker, page1), _mock_response(mocker, page2)],
    )
    client = TestinyClient(API_KEY)
    cases = client.find({"folder_id": {"op": "eq", "value": 9}})
    assert len(cases) == 101
    assert post.call_count == 2


def test_cli_pull_writes_spec_and_masks_key(mocker, tmp_path, monkeypatch, caplog):
    monkeypatch.setenv("TESTINY_API_KEY", API_KEY)
    mocker.patch(
        "tools.testiny.client.requests.get",
        return_value=_mock_response(mocker, CASE),
    )
    with caplog.at_level(logging.DEBUG):
        exit_code = cli.main(
            [
                "pull",
                "--case-id",
                "123",
                "--default-app",
                "gasag",
                "--default-page",
                "login",
                "--out",
                str(tmp_path),
                "--verbose",
            ]
        )
    assert exit_code == 0
    specs = list(tmp_path.rglob("*.md"))
    assert len(specs) == 1
    content = specs[0].read_text(encoding="utf-8")
    assert "app: gasag" in content
    assert "severity: critical" in content
    # The key must never reach the logs; the masked marker proves redaction ran.
    assert API_KEY not in caplog.text
    assert "***REDACTED***" in caplog.text


def test_cli_missing_key_returns_2(monkeypatch):
    monkeypatch.delenv("TESTINY_API_KEY", raising=False)
    exit_code = cli.main(
        ["pull", "--case-id", "1", "--default-app", "x", "--default-page", "y"]
    )
    assert exit_code == 2
