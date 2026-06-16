"""Pure-logic tests for the Testiny -> spec-Markdown normalizer.

Covers ``tools/testiny/normalize.py`` with no network or filesystem — exercises
``testiny_case_to_spec``, ``priority_to_severity`` and ``spec_filename`` against canned
Testiny test-case dicts. Front-matter is asserted by parsing it back with
``yaml.safe_load`` (robust to YAML formatting); the body by section content.
"""

import pytest
import yaml

from tools.testiny.normalize import (
    SpecValidationError,
    priority_to_severity,
    spec_filename,
    testiny_case_to_spec,
)


def _split_spec(spec_text):
    """Return ``(front_matter_dict, body_str)`` from a generated spec."""
    assert spec_text.startswith("---\n")
    _, front_matter, body = spec_text.split("---\n", 2)
    return yaml.safe_load(front_matter), body


def _full_case():
    return {
        "id": 123,
        "project_id": 42,
        "title": "Login rejects invalid credentials",
        "priority": "high",
        "template": "TEXT",
        "_etag": 'W/"abc"',
        "precondition_text": "User is on the login page.",
        "steps_text": "1. Enter a wrong password.\n2. Submit.",
        "expected_result_text": "An error message is shown.",
        "cf__app": "gasag",
        "cf__page": "login",
    }


def test_full_case_front_matter():
    spec = testiny_case_to_spec(_full_case(), pulled_at="2026-06-16T00:00:00Z")
    front, _ = _split_spec(spec)
    assert front["testiny_id"] == 123
    assert front["project_id"] == 42
    assert front["title"] == "Login rejects invalid credentials"
    assert front["app"] == "gasag"
    assert front["page"] == "login"
    assert front["priority"] == "high"
    assert front["severity"] == "critical"
    assert front["status"] == "draft"
    assert front["source"] == "testiny"
    assert front["pulled_at"] == "2026-06-16T00:00:00Z"
    assert front["testiny_etag"] == 'W/"abc"'


def test_full_case_body_sections():
    spec = testiny_case_to_spec(_full_case())
    _, body = _split_spec(spec)
    assert "# Login rejects invalid credentials" in body
    assert "## Precondition" in body
    assert "User is on the login page." in body
    assert "## Steps" in body
    assert "1. Enter a wrong password." in body
    assert "## Expected Result" in body
    assert "An error message is shown." in body


@pytest.mark.parametrize(
    "priority,expected",
    [
        ("highest", "blocker"),
        ("high", "critical"),
        ("medium", "normal"),
        ("normal", "normal"),
        ("low", "minor"),
        ("lowest", "trivial"),
        ("HIGH", "critical"),  # case-insensitive
        ("weird", "normal"),  # unknown -> normal
        (None, "normal"),  # missing -> normal
    ],
)
def test_priority_to_severity(priority, expected):
    assert priority_to_severity(priority) == expected


def test_app_page_fall_back_to_defaults():
    case = _full_case()
    del case["cf__app"]
    del case["cf__page"]
    spec = testiny_case_to_spec(case, default_app="shop", default_page="checkout")
    front, _ = _split_spec(spec)
    assert front["app"] == "shop"
    assert front["page"] == "checkout"


def test_custom_field_names_are_configurable():
    case = _full_case()
    del case["cf__app"]
    del case["cf__page"]
    case["cf__application"] = "gasag"
    case["cf__screen"] = "login"
    spec = testiny_case_to_spec(
        case, app_field="cf__application", page_field="cf__screen"
    )
    front, _ = _split_spec(spec)
    assert front["app"] == "gasag"
    assert front["page"] == "login"


def test_missing_app_without_default_raises():
    case = _full_case()
    del case["cf__app"]
    with pytest.raises(SpecValidationError):
        testiny_case_to_spec(case)


def test_missing_required_field_raises():
    case = _full_case()
    del case["title"]
    with pytest.raises(SpecValidationError):
        testiny_case_to_spec(case)


def test_non_text_template_raises():
    case = _full_case()
    case["template"] = "STEPS"
    with pytest.raises(SpecValidationError):
        testiny_case_to_spec(case)


def test_empty_precondition_renders_placeholder():
    case = _full_case()
    case["precondition_text"] = ""
    spec = testiny_case_to_spec(case)
    _, body = _split_spec(spec)
    # Section header kept for a stable three-section body the skill can rely on.
    assert "## Precondition" in body


def test_markdown_in_text_is_preserved_verbatim():
    case = _full_case()
    case["steps_text"] = "1. Click **Login**\n2. See `error`"
    spec = testiny_case_to_spec(case)
    _, body = _split_spec(spec)
    assert "**Login**" in body
    assert "`error`" in body


def test_optional_fields_omitted_when_absent():
    case = _full_case()
    del case["_etag"]
    del case["priority"]
    spec = testiny_case_to_spec(case)
    front, _ = _split_spec(spec)
    assert "testiny_etag" not in front
    assert "priority" not in front
    assert front["severity"] == "normal"  # missing priority still yields a severity


def test_spec_filename_is_deterministic_slug():
    case = {"id": 5, "title": "Login rejects invalid credentials!"}
    assert spec_filename(case) == "tc-5-login-rejects-invalid-credentials.md"


def test_spec_filename_folds_unicode():
    case = {"id": 7, "title": "Anmelden möglich"}
    assert spec_filename(case) == "tc-7-anmelden-moglich.md"


def test_spec_filename_caps_length():
    case = {"id": 9, "title": "x" * 200}
    name = spec_filename(case)
    assert name.startswith("tc-9-")
    assert name.endswith(".md")
    assert len(name) < 80
