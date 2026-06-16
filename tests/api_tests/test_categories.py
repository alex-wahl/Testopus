"""Toolshop API example — categories and brands (no authentication)."""

import pytest


@pytest.mark.feature("Toolshop API")
@pytest.mark.story("Catalog metadata")
class TestCatalogApi:
    """The public /categories and /brands endpoints."""

    @pytest.mark.severity("normal")
    def test_list_categories(self, api_client):
        response = api_client.get("/categories")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.severity("minor")
    def test_list_brands(self, api_client):
        response = api_client.get("/brands")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
