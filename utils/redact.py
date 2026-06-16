"""Shared redaction helpers.

``redact()`` masks email addresses in free text and is used on failure-path log
messages (see ``fixtures/allure.py``). ``redact_mapping()`` masks secret-looking keys in
a config-style dict and is the single shared helper for safely logging configuration or
telemetry payloads (e.g. the planned telemetry pipeline) — kept in one place so secret
handling never diverges.
"""

import re

# Key-name substrings (case-insensitive) whose values must never reach logs/reports.
_SECRET_KEY_HINTS = (
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "authorization",
)
_EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
REDACTED = "***REDACTED***"


def redact(text):
    """Mask email addresses in free text so PII never reaches logs or reports.

    :param text: Arbitrary value (returned unchanged if not a string).
    :return: The text with email addresses masked, or the original value.
    """
    if not isinstance(text, str):
        return text
    return _EMAIL_PATTERN.sub(REDACTED, text)


def redact_mapping(data):
    """Return a deep copy of a mapping with secret-looking values masked.

    Keys whose name hints at a secret (password/token/…) have their value replaced;
    other string values are email-redacted. Safe to log.

    :param data: A mapping of config-like values.
    :return: A new dict safe to log (non-mappings returned unchanged).
    """
    if not isinstance(data, dict):
        return data
    safe = {}
    for key, value in data.items():
        if any(hint in str(key).lower() for hint in _SECRET_KEY_HINTS):
            safe[key] = REDACTED
        elif isinstance(value, dict):
            safe[key] = redact_mapping(value)
        else:
            safe[key] = redact(value)
    return safe
