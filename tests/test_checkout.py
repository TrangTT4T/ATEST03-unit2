"""Checkout (risk R02, Critical). Scope stops at the checkout page: no payment on the shared store.

Requirement: @start_checkout (REQ-03).
"""
import pytest
from playwright.sync_api import expect


@pytest.mark.critical
@pytest.mark.smoke
@pytest.mark.start_checkout
def test_checkout_opens_from_a_non_empty_cart(shop, page, cart_with):
    cart_with("Grey jacket", 1).checkout()
    expect(page).to_have_url(shop.checkout.URL)
    expect(shop.checkout.line_item("Grey jacket")).to_be_visible()
