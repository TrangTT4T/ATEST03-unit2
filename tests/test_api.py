"""Store API (Day 6: API testing): the Shopify AJAX API behind the pages, tested without a browser.

The same requirements as the UI tests, one layer lower: an API test is fast, needs no rendering and
shows what the server itself allows - here it found a sold-out product the server still adds to the
cart (finding A1), which the UI hides behind a disabled button.

Requirements: @product_details (REQ-04), @add_to_cart (REQ-01), @update_cart (REQ-02), @search_products (REQ-08).
"""
import json
from pathlib import Path

import pytest
from playwright.sync_api import expect

from pages import BasePage

pytestmark = [pytest.mark.api, pytest.mark.regression]
PRODUCTS = json.loads((Path(__file__).resolve().parents[1] / "dataset" / "products.json").read_text(encoding="utf-8"))[
    "products"
]


@pytest.mark.high
@pytest.mark.product_details
@pytest.mark.parametrize("name", sorted(PRODUCTS))
def test_product_api_returns_the_catalog_name_price_and_stock(store_api, products, step, name):
    """The product JSON has the same name, price and stock status as dataset/products.json."""
    # Test data
    product = products[name]
    price_in_pence = round(BasePage.money_to_float(product["price"]) * 100)  # the API counts pence
    in_stock = product["status"] == "available"

    # Execution steps
    with step(f"GET the product JSON of {name}"):
        response = store_api.request_product(product["path-name"])
    with step(f"Verify HTTP 200, title {name!r}, price {price_in_pence} pence, available={in_stock}"):
        assert response.status == 200, f"HTTP {response.status} for {product['path-name']}"
        data = response.json()
        assert data["title"] == name
        assert data["price"] == price_in_pence
        assert data["available"] is in_stock


@pytest.mark.medium
@pytest.mark.negative
@pytest.mark.product_details
def test_unknown_product_returns_404(store_api, step):
    """A product that does not exist answers 404, not an empty product."""
    # Test data
    path_name = "no-such-product"

    # Execution steps
    with step(f"GET the product JSON of {path_name!r}"):
        response = store_api.request_product(path_name)
    with step("Verify HTTP 404"):
        assert response.status == 404


@pytest.mark.critical
@pytest.mark.add_to_cart
def test_cart_api_adds_the_product_and_totals_the_price(store_api, products, step):
    """Adding 2 Noir jackets through the API gives a cart of 2 items, total £120.00."""
    # Test data
    noir_jacket = products["Noir jacket"]
    quantity = 2

    # Execution steps
    with step(f"POST /cart/add.js: {quantity} x Noir jacket"):
        response = store_api.add_product_to_cart(noir_jacket["path-name"], quantity)
        assert response.status == 200, response.text()
    with step("Verify /cart.js: 2 items, total 12000 pence, one line of Noir jacket"):
        cart = store_api.get_cart()
        assert cart["item_count"] == quantity
        assert cart["total_price"] == 12000
        assert [line["product_title"] for line in cart["items"]] == ["Noir jacket"]


@pytest.mark.critical
@pytest.mark.update_cart
def test_cart_api_removes_a_line_set_to_zero(store_api, products, step):
    """Setting the only cart line to quantity 0 empties the cart."""
    # Test data
    striped_top = products["Striped top"]

    # Execution steps
    with step("POST /cart/add.js: 1 x Striped top"):
        store_api.add_product_to_cart(striped_top["path-name"], 1)
    with step("POST /cart/change.js: line 1 -> quantity 0"):
        response = store_api.change_cart_line_quantity(1, 0)
        assert response.status == 200, response.text()
    with step("Verify /cart.js: no items left"):
        assert store_api.get_cart()["item_count"] == 0


@pytest.mark.high
@pytest.mark.negative
@pytest.mark.product_details
@pytest.mark.xfail(strict=True, reason="Finding A1: the store adds a sold-out product through /cart/add.js "
                                        "(HTTP 200) although the UI disables its button (checked 2026-11-27)")
def test_cart_api_refuses_a_sold_out_product(store_api, products, step):
    """A sold-out product cannot be added through the API either (expected: an error, the cart stays empty)."""
    # Test data
    brown_shades = products["Brown Shades"]  # status "sold out"

    # Execution steps
    with step("POST /cart/add.js: 1 x Brown Shades (sold out)"):
        response = store_api.add_product_to_cart(brown_shades["path-name"], 1)
    with step("Verify the add is refused and the cart stays empty"):
        assert response.status >= 400, f"sold-out product accepted: HTTP {response.status}"
        assert store_api.get_cart()["item_count"] == 0


@pytest.mark.medium
@pytest.mark.search_products
def test_search_api_suggests_matching_products(store_api, step):
    """Searching 'jacket' suggests both jackets."""
    # Test data
    keyword = "jacket"

    # Execution steps
    with step(f"GET /search/suggest.json?q={keyword}"):
        titles = store_api.search_product_titles(keyword)
    with step("Verify Grey jacket and Noir jacket are suggested"):
        assert {"Grey jacket", "Noir jacket"} <= set(titles), titles


@pytest.mark.medium
@pytest.mark.negative
@pytest.mark.search_products
def test_search_api_suggests_nothing_for_an_unknown_keyword(store_api, step):
    """A keyword that matches nothing suggests no product."""
    # Test data
    keyword = "zzqqxx"

    # Execution steps
    with step(f"GET /search/suggest.json?q={keyword}"):
        titles = store_api.search_product_titles(keyword)
    with step("Verify no product is suggested"):
        assert titles == []


@pytest.mark.critical
@pytest.mark.add_to_cart
def test_cart_prepared_through_the_api_shows_in_the_browser(shop, store_api_in_browser, products, step):
    """API for the set-up, browser for the check: a cart filled through the API shows on the cart page."""
    # Test data
    grey_jacket = products["Grey jacket"]

    # Execution steps
    with step("Open the store (the API calls share this browser's cookies)"):
        shop.home.open_page()
    with step("POST /cart/add.js: 1 x Grey jacket, without touching the product page"):
        response = store_api_in_browser.add_product_to_cart(grey_jacket["path-name"], 1)
        assert response.status == 200, response.text()
    with step("Open the cart page and verify it shows 1 item"):
        shop.cart.open_page()
        expect(shop.cart.quantity_boxes).to_have_count(1)
        assert shop.cart.count_items_in_cart() == 1
