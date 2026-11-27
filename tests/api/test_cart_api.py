"""Cart API (Day 6: API testing): /cart.js, /cart/add.js, /cart/change.js, without a browser.

The API shows what the server itself allows: it found a sold-out product the server still adds to
the cart (finding A1), which the UI hides behind a disabled button.

Requirements: @add_to_cart (REQ-01), @update_cart (REQ-02), @product_details (REQ-04).
"""
import pytest

pytestmark = [pytest.mark.api, pytest.mark.regression]


@pytest.mark.critical
@pytest.mark.add_to_cart
def test_cart_api_adds_the_product_and_totals_the_price(shop_api, products, step):
    """Adding 2 Noir jackets through the API gives a cart of 2 items, total £120.00."""
    # Test data
    noir_jacket = products["Noir jacket"]
    quantity = 2

    # Execution steps
    with step(f"POST /cart/add.js: {quantity} x Noir jacket"):
        response = shop_api.cart.add_product_to_cart(noir_jacket["path-name"], quantity)
        assert response.status == 200, response.text()
    with step("Verify /cart.js: 2 items, total 12000 pence, one line of Noir jacket"):
        cart = shop_api.cart.get_cart()
        assert cart["item_count"] == quantity
        assert cart["total_price"] == 12000
        assert [line["product_title"] for line in cart["items"]] == ["Noir jacket"]


@pytest.mark.critical
@pytest.mark.update_cart
def test_cart_api_removes_a_line_set_to_zero(shop_api, products, step):
    """Setting the only cart line to quantity 0 empties the cart."""
    # Test data
    striped_top = products["Striped top"]

    # Execution steps
    with step("POST /cart/add.js: 1 x Striped top"):
        shop_api.cart.add_product_to_cart(striped_top["path-name"], 1)
    with step("POST /cart/change.js: line 1 -> quantity 0"):
        response = shop_api.cart.change_cart_line_quantity(1, 0)
        assert response.status == 200, response.text()
    with step("Verify /cart.js: no items left"):
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
    with step("POST /cart/add.js: 1 x Brown Shades (sold out)"):
        response = shop_api.cart.add_product_to_cart(brown_shades["path-name"], 1)
    with step("Verify the add is refused and the cart stays empty"):
        assert response.status >= 400, f"sold-out product accepted: HTTP {response.status}"
        assert shop_api.cart.get_cart()["item_count"] == 0
