"""Thin HTTP client for the Testiny REST API (https://app.testiny.io/api/v1/).

The ONLY network code under ``tools/testiny`` — kept minimal so the CLI and the pure
normalizer stay testable (tests mock ``requests`` rather than hitting the network).
The API key is sent only in the ``X-Api-Key`` header and is never logged; the CLI
routes any debug output through ``utils.redact``.
"""

import requests

DEFAULT_BASE_URL = "https://app.testiny.io/api/v1"
_DEFAULT_TIMEOUT = 30
_DEFAULT_PAGE_SIZE = 100


class TestinyClient:
    """Minimal Testiny REST client — fetch test cases by id or by filter."""

    # Name starts with "Test", matching pytest's default class-collection glob; opt out
    # so pytest never tries to collect this client as a test suite.
    __test__ = False

    def __init__(self, api_key, base_url=DEFAULT_BASE_URL, *, timeout=_DEFAULT_TIMEOUT):
        if not api_key:
            raise ValueError("api_key is required")
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._headers = {"X-Api-Key": api_key, "Accept": "application/json"}

    def get_testcase(self, case_id):
        """Return a single test case (``GET /testcase/:id``)."""
        response = requests.get(
            f"{self._base_url}/testcase/{case_id}",
            headers=self._headers,
            timeout=self._timeout,
        )
        response.raise_for_status()
        return response.json()

    def find(self, filter_obj=None, *, page_size=_DEFAULT_PAGE_SIZE):
        """Return every case matching a filter (``POST /testcase/find``), across pages.

        :param filter_obj: A Testiny filter object, e.g.
            ``{"folder_id": {"op": "eq", "value": 9}}``. ``None`` fetches all cases.
        :param page_size: Page size for the ``limit``/``offset`` pagination loop.
        """
        results = []
        offset = 0
        while True:
            body = {"limit": page_size, "offset": offset}
            if filter_obj:
                body["filter"] = filter_obj
            response = requests.post(
                f"{self._base_url}/testcase/find",
                json=body,
                headers=self._headers,
                timeout=self._timeout,
            )
            response.raise_for_status()
            page = _extract_cases(response.json())
            results.extend(page)
            if len(page) < page_size:
                break
            offset += page_size
        return results


def _extract_cases(payload):
    """Pull the list of cases out of a Testiny ``find`` response.

    Defensive about the envelope — tolerates ``{"data": [...]}``, ``{"items": [...]}``,
    ``{"results": [...]}`` or a bare list — so a minor API-shape change does not break
    the pull. Confirm the exact envelope against your Testiny instance.
    """
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("data", "items", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
    return []
