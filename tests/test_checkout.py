"""Checkout (risk R02, Critical). Scope stops at the checkout page: no payment on the shared store.

Requirement: @start_checkout (REQ-03).
"""
import pytest
from playwright.sync_api import expect


@pytest.mark.critical
@pytest.mark.smoke
@pytest.mark.start_checkout
def test_checkout_opens_from_a_non_empty_cart(shop, page, add_product_and_open_cart, step):
    """From a cart with one product, Checkout opens the checkout page listing that product."""
    # Execution steps
    with step("Put 1 x Grey jacket in the cart"):
        cart = add_product_and_open_cart("Grey jacket", 1)
    with step("Start checkout from the cart"):
        cart.click_checkout()
    with step("Verify the checkout page lists Grey jacket"):
        expect(page).to_have_url(shop.checkout.URL)
        expect(shop.checkout.order_summary_line("Grey jacket")).to_be_visible()
