"""Toolshop API example — public product reads (no authentication)."""

import pytest


@pytest.mark.feature("Toolshop API")
@pytest.mark.story("Products")
class TestProductsApi:
    """The public /products endpoints."""

    @pytest.mark.severity("critical")
    def test_list_products_returns_a_page(self, api_client):
        response = api_client.get("/products")
        assert response.status_code == 200
        body = response.json()
        assert (
            isinstance(body.get("data"), list) and body["data"]
        ), "no products returned"
        first = body["data"][0]
        assert {"id", "name", "price"} <= set(
            first
        ), f"unexpected shape: {first.keys()}"

    @pytest.mark.severity("normal")
    def test_get_single_product(self, api_client):
        product_id = api_client.get("/products").json()["data"][0]["id"]
        response = api_client.get(f"/products/{product_id}")
        assert response.status_code == 200
        assert response.json()["id"] == product_id
