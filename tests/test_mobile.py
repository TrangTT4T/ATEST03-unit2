"""Phone emulation (Day 5: browser contexts beyond isolation), risks R01/R05. Requirements: @browse_catalog, @checkout.

A browser context can emulate a device: screen size, touch, mobile user agent, pixel density. The
`phone_shop` fixture opens Swag Labs as an iPhone 13 (Playwright's device list) in Chromium; the
same layout is what a customer on a phone sees.
"""
import pytest
from playwright.sync_api import expect

from helper_utility.helpers import Helper

pytestmark = [pytest.mark.medium, pytest.mark.regression]
CHECKOUT = Helper.read_test_data("checkout")


@pytest.mark.browse_catalog
def test_products_page_fits_a_phone_screen(phone_shop, products, step):
    """On a phone the products page does not scroll sideways and shows one full-width card per row."""
    # Execution steps
    step_number = 1
    with step(step_number, "Read the screen width and the width of every product card"):
        screen_width = phone_shop.inventory.get_screen_width()
        card_widths = phone_shop.inventory.get_product_card_widths()
    step_number += 1
    with step(step_number, f"Verify the {len(products)} cards fit the {screen_width}px screen, one per row"):
        assert len(card_widths) == len(products)
        assert not phone_shop.inventory.is_wider_than_the_screen(), "The products page scrolls sideways"
        assert all(screen_width * 0.8 <= width <= screen_width for width in card_widths), card_widths


@pytest.mark.checkout
def test_customer_orders_on_a_phone(phone_shop, checkout_information, step):
    """A customer on a phone adds a product, checks out and gets the confirmation."""
    # Test data
    customer = checkout_information

    # Execution steps
    step_number = 1
    with step(step_number, "Add Sauce Labs Onesie and open the cart"):
        phone_shop.inventory.add_product_to_cart("Sauce Labs Onesie")
        phone_shop.inventory.open_cart()
    step_number += 1
    with step(step_number, "Check out with the customer's details"):
        phone_shop.cart.click_checkout()
        phone_shop.checkout_information.fill_information_and_continue(customer["first_name"], customer["last_name"],
                                                                      customer["postal_code"])
    step_number += 1
    with step(step_number, "Finish the order"):
        phone_shop.checkout_overview.click_finish()
    step_number += 1
    with step(step_number, f"Verify {CHECKOUT['order_complete_header']!r}"):
        expect(phone_shop.checkout_complete.complete_header).to_have_text(CHECKOUT["order_complete_header"])
