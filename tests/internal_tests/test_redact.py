from utils.redact import REDACTED, redact, redact_mapping


def test_redact_masks_email():
    out = redact("contact me at john.doe@example.com please")
    assert "john.doe@example.com" not in out
    assert REDACTED in out


def test_redact_passes_through_non_strings():
    assert redact(123) == 123
    assert redact(None) is None


def test_redact_mapping_masks_secret_keys():
    data = {
        "username": "a@b.com",
        "password": "hunter2",
        "nested": {"token": "xyz"},
    }
    safe = redact_mapping(data)
    assert safe["password"] == REDACTED
    assert safe["nested"]["token"] == REDACTED
    assert "a@b.com" not in safe["username"]


def test_redact_mapping_leaves_plain_values():
    assert redact_mapping({"url": "https://x.test"})["url"] == "https://x.test"
