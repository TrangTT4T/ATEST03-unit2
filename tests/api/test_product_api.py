"""Product API (Day 6: API testing): GET /products/<path-name>.js, tested without a browser.

The same requirement as the UI catalog tests, one layer lower and without rendering.
Requirement: @product_details (REQ-04).
"""
import json
from pathlib import Path

import pytest

from pages import BasePage

pytestmark = [pytest.mark.api, pytest.mark.regression]
PRODUCTS = json.loads((Path(__file__).resolve().parents[2] / "dataset" / "products.json").read_text(encoding="utf-8"))[
    "products"
]


@pytest.mark.high
@pytest.mark.product_details
@pytest.mark.parametrize("name", sorted(PRODUCTS))
def test_product_api_returns_the_catalog_name_price_and_stock(shop_api, products, step, name):
    """The product JSON has the same name, price and stock status as dataset/products.json."""
    # Test data
    product = products[name]
    price_in_pence = round(BasePage.money_to_float(product["price"]) * 100)  # the API counts pence
    in_stock = product["status"] == "available"

    # Execution steps
    with step(f"GET the product JSON of {name}"):
        response = shop_api.product.request_product(product["path-name"])
    with step(f"Verify HTTP 200, title {name!r}, price {price_in_pence} pence, available={in_stock}"):
        assert response.status == 200, f"HTTP {response.status} for {product['path-name']}"
        data = response.json()
        assert data["title"] == name
        assert data["price"] == price_in_pence
        assert data["available"] is in_stock


@pytest.mark.medium
@pytest.mark.negative
@pytest.mark.product_details
def test_unknown_product_returns_404(shop_api, step):
    """A product that does not exist answers 404, not an empty product."""
    # Test data
    path_name = "no-such-product"

    # Execution steps
    with step(f"GET the product JSON of {path_name!r}"):
        response = shop_api.product.request_product(path_name)
    with step("Verify HTTP 404"):
        assert response.status == 404
