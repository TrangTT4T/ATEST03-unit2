"""Checkout (risk R02, Critical): information form, overview totals, order complete.

The cases come from dataset/checkout.json; the customer is made up by Faker for every test.
Requirement: @checkout (REQ-03).
"""
import pytest
from playwright.sync_api import expect

from helper_utility.helpers import Helper

pytestmark = [pytest.mark.critical, pytest.mark.checkout]
CHECKOUT = Helper.read_test_data("checkout")


@pytest.mark.smoke
def test_customer_completes_an_order(fill_cart, checkout_information, step):
    """Cart -> information -> overview -> Finish: the order is confirmed and the cart is empty."""
    # Test data
    customer = checkout_information  # made up by Faker

    # Execution steps
    step_number = 1
    with step(step_number, "Put Sauce Labs Backpack in the cart and open the cart"):
        shop = fill_cart(["Sauce Labs Backpack"])
        shop.inventory.open_cart()
    step_number += 1
    with step(step_number, "Click Checkout"):
        shop.cart.click_checkout()
    step_number += 1
    with step(step_number, f"Fill in {customer['first_name']} {customer['last_name']}, {customer['postal_code']}"):
        shop.checkout_information.fill_information_and_continue(customer["first_name"], customer["last_name"],
                                                                customer["postal_code"])
    step_number += 1
    with step(step_number, "Click Finish"):
        shop.checkout_overview.click_finish()
    step_number += 1
    with step(step_number, f"Verify {CHECKOUT['order_complete_header']!r} and an empty cart"):
        expect(shop.checkout_complete.complete_header).to_have_text(CHECKOUT["order_complete_header"])
        expect(shop.checkout_complete.cart_badge).to_be_hidden()


@pytest.mark.regression
@pytest.mark.parametrize("case", CHECKOUT["totals"], ids=[case["id"] for case in CHECKOUT["totals"]])
def test_checkout_overview_shows_the_items_and_totals(fill_cart, checkout_information, step, case):
    """The overview lists the products, the item total, the 8% tax and the total (dataset/checkout.json)."""
    # Test data
    customer = checkout_information

    # Execution steps
    step_number = 1
    with step(step_number, f"Put {len(case['products'])} products in the cart and check out"):
        shop = fill_cart(case["products"])
        shop.inventory.open_cart()
        shop.cart.click_checkout()
    step_number += 1
    with step(step_number, "Fill in the customer and continue to the overview"):
        shop.checkout_information.fill_information_and_continue(customer["first_name"], customer["last_name"],
                                                                customer["postal_code"])
    step_number += 1
    with step(step_number, "Verify the overview lists exactly these products"):
        assert sorted(shop.checkout_overview.get_product_names()) == sorted(case["products"])
    step_number += 1
    with step(step_number, f"Verify item total {case['item_total']}, tax {case['tax']}, total {case['total']}"):
        expect(shop.checkout_overview.item_total).to_have_text(f"Item total: {case['item_total']}")
        expect(shop.checkout_overview.tax).to_have_text(f"Tax: {case['tax']}")
        expect(shop.checkout_overview.total).to_have_text(f"Total: {case['total']}")


@pytest.mark.regression
@pytest.mark.negative
@pytest.mark.parametrize("case", CHECKOUT["missing_information"],
                         ids=[case["id"] for case in CHECKOUT["missing_information"]])
def test_checkout_information_is_required(fill_cart, checkout_information, page, step, case):
    """Each empty field of the information form stops the checkout with its error (dataset/checkout.json)."""
    # Test data
    customer = {**checkout_information, case["missing"]: ""}

    # Execution steps
    step_number = 1
    with step(step_number, "Put Sauce Labs Onesie in the cart and check out"):
        shop = fill_cart(["Sauce Labs Onesie"])
        shop.inventory.open_cart()
        shop.cart.click_checkout()
    step_number += 1
    with step(step_number, f"Fill in the form without {case['missing']} and click Continue"):
        shop.checkout_information.fill_information(customer["first_name"], customer["last_name"],
                                                   customer["postal_code"])
    step_number += 1
    with step(step_number, f"Verify the error {case['error']!r} and that the overview is not opened"):
        expect(shop.checkout_information.error_message).to_have_text(case["error"])
        expect(shop.checkout_information.page_title).to_have_text("Checkout: Your Information")
