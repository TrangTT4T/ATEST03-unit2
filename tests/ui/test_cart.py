"""Cart (risk R01, Critical): add products, totals, change quantity, remove.

The cases come from dataset/cart.json: a new case is a new line in that file, not new code.
Requirements: @add_to_cart (REQ-01), @update_cart (REQ-02).
"""
import re

import pytest
from playwright.sync_api import expect

from helper_utility.helpers import Helper
from pages import CartPage

pytestmark = pytest.mark.critical
CART = Helper.read_test_data("cart")


def verify_cart_contents(cart: CartPage, items: int, total: str) -> None:
    """The cart holds ``items`` items in all and its total is ``total`` (e.g. "£55.00")."""
    expect(cart.header_cart_link).to_have_text(re.compile(rf"My Cart \({items}\)"))  # retries until updated
    assert cart.count_items_in_cart() == items
    assert cart.get_cart_total() == Helper.money_to_float(total)


@pytest.mark.smoke
@pytest.mark.add_to_cart
def test_add_an_in_stock_product_to_the_cart(shop, products, step):
    """A customer adds one in-stock product: the cart shows 1 item at the product's price."""
    # Test data
    grey_jacket = products["Grey jacket"]

    # Execution steps
    with step("Open the product page of Grey jacket"):
        shop.product.open_product_page(grey_jacket["path-name"])
    with step("Add 1 item to the cart"):
        shop.product.add_to_cart(1)
    with step(f"Verify the cart has 1 item, total {grey_jacket['price']}"):
        shop.cart.open_page()
        verify_cart_contents(shop.cart, 1, grey_jacket["price"])


@pytest.mark.regression
@pytest.mark.add_to_cart
@pytest.mark.parametrize("case", CART["add"], ids=[case["id"] for case in CART["add"]])
def test_cart_total_equals_price_times_quantity(add_product_and_open_cart, step, case):
    """The cart total of N items of one product is N times its price (dataset/cart.json "add")."""
    # Execution steps
    with step(f"Put {case['quantity']} x {case['product']} in the cart"):
        cart = add_product_and_open_cart(case["product"], case["quantity"])
    with step(f"Verify the cart has {case['quantity']} items, total {case['total']}"):
        verify_cart_contents(cart, case["quantity"], case["total"])


@pytest.mark.regression
@pytest.mark.update_cart
@pytest.mark.parametrize("case", CART["change"], ids=[case["id"] for case in CART["change"]])
def test_change_the_quantity_of_a_product_in_the_cart(add_product_and_open_cart, step, case):
    """Changing a line's quantity updates the item count and the total (dataset/cart.json "change")."""
    # Execution steps
    with step(f"Put {case['from']} x {case['product']} in the cart"):
        cart = add_product_and_open_cart(case["product"], case["from"])
    with step(f"Change the quantity of {case['product']} to {case['to']}"):
        cart.change_product_quantity(case["product"], case["to"])
    with step(f"Verify the cart has {case['to']} items, total {case['total']}"):
        verify_cart_contents(cart, case["to"], case["total"])


@pytest.mark.regression
@pytest.mark.update_cart
@pytest.mark.parametrize("case", CART["remove"], ids=[case["id"] for case in CART["remove"]])
def test_remove_the_only_product_from_the_cart(add_product_and_open_cart, step, case):
    """Removing the only line leaves an empty cart (dataset/cart.json "remove")."""
    # Execution steps
    with step(f"Put 1 x {case['product']} in the cart"):
        cart = add_product_and_open_cart(case["product"], 1)
    with step(f"Remove {case['product']} from the cart"):
        cart.remove_product_from_cart(case["product"])
    with step("Verify the cart has no lines left"):
        expect(cart.quantity_boxes).to_have_count(0)


@pytest.mark.critical
@pytest.mark.add_to_cart
def test_cart_prepared_through_the_api_shows_in_the_browser(shop, shop_api_in_browser, products, step):
    """API for the set-up, browser for the check: a cart filled through the API shows on the cart page."""
    # Test data
    grey_jacket = products["Grey jacket"]

    # Execution steps
    with step("Open the store (the API calls share this browser's cookies)"):
        shop.home.open_page()
    with step("POST /cart/add.js: 1 x Grey jacket, without touching the product page"):
        response = shop_api_in_browser.cart.add_product_to_cart(grey_jacket["path-name"], 1)
        assert response.status == 200, response.text()
    with step("Open the cart page and verify it shows 1 item"):
        shop.cart.open_page()
        expect(shop.cart.quantity_boxes).to_have_count(1)
        assert shop.cart.count_items_in_cart() == 1
