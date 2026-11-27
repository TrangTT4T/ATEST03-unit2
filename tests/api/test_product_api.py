"""Product API (Day 6: API testing): GET /products/<path-name>.js, tested without a browser.

The same requirement as the UI catalog tests, one layer lower and without rendering.
Requirement: @product_details (REQ-04).
"""
import pytest

from helper_utility.helpers import Helper

pytestmark = [pytest.mark.api, pytest.mark.regression]
PRODUCTS = Helper.read_test_data("products")["products"]


@pytest.mark.high
@pytest.mark.product_details
@pytest.mark.parametrize("name", sorted(PRODUCTS))
def test_product_api_returns_the_catalog_name_price_and_stock(shop_api, products, step, name):
    """The product JSON has the same name, price and stock status as dataset/products.json."""
    # Test data
    product = products[name]
    price_in_pence = Helper.money_to_pence(product["price"])  # the API counts pence
    in_stock = product["status"] == "available"

    # Execution steps
    step_number = 1
    with step(step_number, f"GET the product JSON of {name}"):
        response = shop_api.product.request_product(product["path-name"])
    step_number += 1
    with step(step_number, f"Verify HTTP 200, title {name!r}, price {price_in_pence} pence, available={in_stock}"):
        assert response.status == 200, f"HTTP {response.status} for {product['path-name']}"
        data = response.json()
        assert data["title"] == name
        assert data["price"] == price_in_pence
        assert data["available"] is in_stock


@pytest.mark.medium
@pytest.mark.product_details
@pytest.mark.parametrize("name", sorted(PRODUCTS))
def test_product_api_returns_the_catalog_type_vendor_and_options(shop_api, products, step, name):
    """The product JSON has the type, vendor and options (Size, Color ...) of dataset/products.json."""
    # Test data
    product = products[name]

    # Execution steps
    step_number = 1
    with step(step_number, f"GET the product JSON of {name}"):
        response = shop_api.product.request_product(product["path-name"])
        assert response.status == 200, f"HTTP {response.status} for {product['path-name']}"
        data = response.json()
    step_number += 1
    with step(step_number, f"Verify type {product['type']!r} and vendor {product['vendor']!r}"):
        assert data["type"] == product["type"]
        assert data["vendor"] == product["vendor"]
    step_number += 1
    with step(step_number, f"Verify the options {product['options']}"):
        options = {option["name"]: option["values"] for option in data["options"]}
        options.pop("Title", None)  # Shopify's placeholder {"Title": ["Default Title"]} for a product without options
        assert options == product["options"]


@pytest.mark.medium
@pytest.mark.negative
@pytest.mark.product_details
def test_unknown_product_returns_404(shop_api, step):
    """A product that does not exist answers 404, not an empty product."""
    # Test data
    path_name = "no-such-product"

    # Execution steps
    step_number = 1
    with step(step_number, f"GET the product JSON of {path_name!r}"):
        response = shop_api.product.request_product(path_name)
    step_number += 1
    with step(step_number, "Verify HTTP 404"):
        assert response.status == 404
