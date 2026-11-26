"""Cart (risk R01, Critical): add products, totals, change quantity, remove.

Requirements: @add_to_cart (REQ-01), @update_cart (REQ-02).
"""
import re

import pytest
from playwright.sync_api import expect

from pages import BasePage, CartPage

pytestmark = pytest.mark.critical


def expect_cart(cart: CartPage, items: int, total: str) -> None:
    """The cart holds ``items`` items in all and its total is ``total`` (e.g. "£55.00")."""
    expect(cart.mini_cart).to_have_text(re.compile(rf"My Cart \({items}\)"))  # retries until updated
    assert cart.total_quantity() == items
    assert cart.total() == BasePage.money_to_float(total)


@pytest.mark.smoke
@pytest.mark.add_to_cart
def test_add_an_in_stock_product_to_the_cart(shop, products, step):
    """A customer adds one in-stock product: the cart shows 1 item at the product's price."""
    # Test data
    grey_jacket = products["Grey jacket"]

    # Execution steps
    with step("Open the product page of Grey jacket"):
        shop.product.open_product(grey_jacket["path-name"])
    with step("Add 1 item to the cart"):
        shop.product.add_to_cart(1)
    with step("Verify the cart has 1 item, total £55.00"):
        expect_cart(shop.cart.open(), 1, "£55.00")


@pytest.mark.regression
@pytest.mark.add_to_cart
@pytest.mark.parametrize(
    "product, quantity, total",
    [("Noir jacket", 2, "£120.00"), ("Striped top", 3, "£150.00")],
    ids=["noir-jacket-x2", "striped-top-x3"],
)
def test_cart_total_equals_price_times_quantity(cart_with, step, product, quantity, total):
    """The cart total of N items of one product is N times its price."""
    # Execution steps
    with step(f"Put {quantity} x {product} in the cart"):
        cart = cart_with(product, quantity)
    with step(f"Verify the cart has {quantity} items, total {total}"):
        expect_cart(cart, quantity, total)


@pytest.mark.regression
@pytest.mark.update_cart
def test_change_the_quantity_of_a_product_in_the_cart(cart_with, step):
    """Changing a line's quantity in the cart updates the item count and the total."""
    # Execution steps
    with step("Put 1 x Bronze sandals in the cart"):
        cart = cart_with("Bronze sandals", 1)
    with step("Change the quantity of Bronze sandals to 2"):
        cart.set_quantity("Bronze sandals", 2)
    with step("Verify the cart has 2 items, total £79.98"):
        expect_cart(cart, 2, "£79.98")


@pytest.mark.regression
@pytest.mark.update_cart
def test_remove_the_only_product_from_the_cart(cart_with, step):
    """Removing the only line leaves an empty cart."""
    # Execution steps
    with step("Put 1 x Striped top in the cart"):
        cart = cart_with("Striped top", 1)
    with step("Remove Striped top from the cart"):
        cart.remove("Striped top")
    with step("Verify the cart has no lines left"):
        expect(cart.quantity_inputs).to_have_count(0)
