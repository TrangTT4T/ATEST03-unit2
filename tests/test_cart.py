"""Cart (risk R01, Critical): add products, totals, change quantity, remove.

Requirements: @add_to_cart (REQ-01), @update_cart (REQ-02).
"""
import re

import pytest
from playwright.sync_api import expect

from pages import CartPage, money_to_float

pytestmark = pytest.mark.critical


def expect_cart(cart: CartPage, items: int, total: str) -> None:
    expect(cart.mini_cart).to_have_text(re.compile(rf"My Cart \({items}\)"))  # retries until updated
    assert cart.total_quantity() == items
    assert cart.total() == money_to_float(total)


@pytest.mark.smoke
@pytest.mark.add_to_cart
def test_add_an_in_stock_product_to_the_cart(shop, products):
    shop.product.open_product(products["Grey jacket"]["handle"])
    shop.product.add_to_cart(1)
    expect_cart(shop.cart.open(), 1, "£55.00")


@pytest.mark.regression
@pytest.mark.add_to_cart
@pytest.mark.parametrize(
    "product, quantity, total",
    [("Noir jacket", 2, "£120.00"), ("Striped top", 3, "£150.00")],
    ids=["noir-jacket-x2", "striped-top-x3"],
)
def test_cart_total_equals_price_times_quantity(cart_with, product, quantity, total):
    expect_cart(cart_with(product, quantity), quantity, total)


@pytest.mark.regression
@pytest.mark.update_cart
def test_change_the_quantity_of_a_product_in_the_cart(cart_with):
    cart = cart_with("Bronze sandals", 1)
    cart.set_quantity("Bronze sandals", 2)
    expect_cart(cart, 2, "£79.98")


@pytest.mark.regression
@pytest.mark.update_cart
def test_remove_the_only_product_from_the_cart(cart_with):
    cart = cart_with("Striped top", 1)
    cart.remove("Striped top")
    expect(cart.quantity_inputs).to_have_count(0)
