"""Cart API (Day 6: API testing): /cart.js, /cart/add.js, /cart/change.js, without a browser.

The API shows what the server itself allows: it found a sold-out product the server still adds to
the cart (finding A1), which the UI hides behind a disabled button.

Requirements: @add_to_cart (REQ-01), @update_cart (REQ-02), @product_details (REQ-04).
"""
import pytest

from helper_utility.helpers import Helper

pytestmark = [pytest.mark.api, pytest.mark.regression]
CART = Helper.read_test_data("cart")


@pytest.mark.critical
@pytest.mark.add_to_cart
@pytest.mark.parametrize("case", CART["add"], ids=[case["id"] for case in CART["add"]])
def test_cart_api_adds_the_product_and_totals_the_price(shop_api, products, step, case):
    """Adding N items of one product gives a cart of N items at N times the price (dataset/cart.json "add")."""
    # Test data
    product = products[case["product"]]
    total_in_pence = Helper.money_to_pence(case["total"])

    # Execution steps
    step_number = 1
    with step(step_number, f"POST /cart/add.js: {case['quantity']} x {case['product']}"):
        response = shop_api.cart.add_product_to_cart(product["path-name"], case["quantity"])
        assert response.status == 200, response.text()
    step_number += 1
    with step(step_number, f"Verify /cart.js: {case['quantity']} items, total {total_in_pence} pence, one line"):
        cart = shop_api.cart.get_cart()
        assert cart["item_count"] == case["quantity"]
        assert cart["total_price"] == total_in_pence
        assert [line["product_title"] for line in cart["items"]] == [case["product"]]


@pytest.mark.critical
@pytest.mark.update_cart
@pytest.mark.parametrize("case", CART["change"], ids=[case["id"] for case in CART["change"]])
def test_cart_api_changes_the_quantity_of_a_line(shop_api, products, step, case):
    """Changing a line's quantity updates the item count and the total (dataset/cart.json "change")."""
    # Test data
    product = products[case["product"]]
    total_in_pence = Helper.money_to_pence(case["total"])

    # Execution steps
    step_number = 1
    with step(step_number, f"POST /cart/add.js: {case['from']} x {case['product']}"):
        shop_api.cart.add_product_to_cart(product["path-name"], case["from"])
    step_number += 1
    with step(step_number, f"POST /cart/change.js: line 1 -> quantity {case['to']}"):
        response = shop_api.cart.change_cart_line_quantity(1, case["to"])
        assert response.status == 200, response.text()
    step_number += 1
    with step(step_number, f"Verify /cart.js: {case['to']} items, total {total_in_pence} pence"):
        cart = shop_api.cart.get_cart()
        assert cart["item_count"] == case["to"]
        assert cart["total_price"] == total_in_pence


@pytest.mark.critical
@pytest.mark.update_cart
@pytest.mark.parametrize("case", CART["remove"], ids=[case["id"] for case in CART["remove"]])
def test_cart_api_removes_a_line_set_to_zero(shop_api, products, step, case):
    """Setting the only cart line to quantity 0 empties the cart (dataset/cart.json "remove")."""
    # Test data
    product = products[case["product"]]

    # Execution steps
    step_number = 1
    with step(step_number, f"POST /cart/add.js: 1 x {case['product']}"):
        shop_api.cart.add_product_to_cart(product["path-name"], 1)
    step_number += 1
    with step(step_number, "POST /cart/change.js: line 1 -> quantity 0"):
        response = shop_api.cart.change_cart_line_quantity(1, 0)
        assert response.status == 200, response.text()
    step_number += 1
    with step(step_number, "Verify /cart.js: no items left"):
        assert shop_api.cart.get_cart()["item_count"] == 0


@pytest.mark.high
@pytest.mark.negative
@pytest.mark.product_details
@pytest.mark.xfail(strict=True, reason="Finding A1: the store adds a sold-out product through /cart/add.js "
                                        "(HTTP 200) although the UI disables its button (checked 2026-11-27)")
def test_cart_api_refuses_a_sold_out_product(shop_api, products, step):
    """A sold-out product cannot be added through the API either (expected: an error, the cart stays empty)."""
    # Test data
    brown_shades = products["Brown Shades"]  # status "sold out"

    # Execution steps
    step_number = 1
    with step(step_number, "POST /cart/add.js: 1 x Brown Shades (sold out)"):
        response = shop_api.cart.add_product_to_cart(brown_shades["path-name"], 1)
    step_number += 1
    with step(step_number, "Verify the add is refused and the cart stays empty"):
        assert response.status >= 400, f"sold-out product accepted: HTTP {response.status}"
        assert shop_api.cart.get_cart()["item_count"] == 0
