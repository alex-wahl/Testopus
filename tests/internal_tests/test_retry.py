import json
from pathlib import Path

import pytest
from selenium.common.exceptions import TimeoutException

from core.pom.web.base_page import retry


def test_retry_does_not_mask_assertion_error():
    calls = {"n": 0}

    @retry(retries=3, delay=0)
    def always_asserts():
        calls["n"] += 1
        assert False, "reproducible failure"

    with pytest.raises(AssertionError):
        always_asserts()
    # AssertionError is not a web exception -> surfaces immediately, no retries.
    assert calls["n"] == 1


def test_retry_retries_web_exception_then_passes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    calls = {"n": 0}
    seen = []

    @retry(
        retries=3, delay=0, on_retry=lambda attempt, exc, *a, **k: seen.append(attempt)
    )
    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise TimeoutException("transient")
        return "ok"

    assert flaky() == "ok"
    assert calls["n"] == 3
    assert seen == [0, 1]  # on_retry fired before each of the two retries

    events_file = Path(tmp_path, "reports", "retry_events.jsonl")
    assert events_file.exists()
    events = [json.loads(line) for line in events_file.read_text().splitlines()]
    assert any(e["event"] == "retry_to_pass" for e in events)
    assert sum(1 for e in events if e["event"] == "retry") == 2


def test_retry_event_emission_is_fail_open(tmp_path, monkeypatch):
    # If the reports dir can't be written, retry must still work (telemetry is best-effort).
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "core.pom.web.base_page.os.makedirs",
        lambda *a, **k: (_ for _ in ()).throw(OSError("read-only fs")),
    )

    @retry(retries=2, delay=0)
    def flaky():
        raise TimeoutException("transient")

    with pytest.raises(TimeoutException):
        flaky()
