"""Thin HTTP client for API testing — the API analogue of the ``core/drivers`` web seam.

A small, reusable wrapper over ``requests``. Unlike a production client it does **not** raise
on 4xx/5xx: API tests assert on status codes (200, 401, 404, …), so callers inspect
``response.status_code`` themselves. Auth is a bearer token sent via the ``Authorization``
header.

This is an *optional* layer — ``requests`` lives in the ``[api]`` extra and the ``api_client``
fixture is local to ``tests/api_tests`` — so a web-only install never imports this module.
"""

import requests

_DEFAULT_TIMEOUT = 30


class ApiClient:
    """Minimal REST client for tests — returns responses without raising on error codes."""

    def __init__(self, base_url, *, token=None, headers=None, timeout=_DEFAULT_TIMEOUT):
        if not base_url:
            raise ValueError("base_url is required")
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._headers = {"Accept": "application/json"}
        if headers:
            self._headers.update(headers)
        if token:
            self._headers["Authorization"] = f"Bearer {token}"

    def _url(self, endpoint):
        return f"{self._base_url}/{endpoint.lstrip('/')}"

    def get(self, endpoint, *, params=None):
        """GET ``endpoint``; returns the ``requests.Response`` (never raises on status)."""
        return requests.get(
            self._url(endpoint),
            params=params,
            headers=self._headers,
            timeout=self._timeout,
        )

    def post(self, endpoint, *, json=None):
        """POST a JSON body to ``endpoint``; returns the ``requests.Response``."""
        return requests.post(
            self._url(endpoint),
            json=json,
            headers=self._headers,
            timeout=self._timeout,
        )

    def put(self, endpoint, *, json=None):
        """PUT a JSON body to ``endpoint``; returns the ``requests.Response``."""
        return requests.put(
            self._url(endpoint),
            json=json,
            headers=self._headers,
            timeout=self._timeout,
        )

    def delete(self, endpoint):
        """DELETE ``endpoint``; returns the ``requests.Response``."""
        return requests.delete(
            self._url(endpoint), headers=self._headers, timeout=self._timeout
        )
