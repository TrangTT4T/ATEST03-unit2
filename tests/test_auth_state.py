"""Authentication state reuse (Day 6), login risk (High). Requirement: @secure_login (REQ-05).

The session fixture `saved_login_state` logs in once and saves cookies + localStorage to a file; a
context created from that file starts already logged in, without the login form.
"""
import pytest
from playwright.sync_api import Browser, expect

from helper_utility.helpers import Helper
from pages import InventoryPage

pytestmark = [pytest.mark.high, pytest.mark.regression, pytest.mark.secure_login]
LOGIN = Helper.read_test_data("login")


def test_saved_login_state_opens_the_products_without_login(browser: Browser, base_url, saved_login_state, step):
    """A context created from the saved login opens the products page directly."""
    # Execution steps
    step_number = 1
    with step(step_number, "Open a new browser context with the saved login"):
        context = browser.new_context(base_url=base_url, storage_state=str(saved_login_state))
        inventory = InventoryPage(context.new_page())
    step_number += 1
    with step(step_number, "Open the products page"):
        inventory.open_page()
    step_number += 1
    with step(step_number, "Verify the products are shown, without the login form"):
        expect(inventory.page_title).to_have_text("Products")
    step_number += 1
    with step(step_number, "Close the context"):
        context.close()


def test_login_state_does_not_leak_into_other_tests(shop, saved_login_state, step):
    """Isolation check: the default `page` has its own context, so it is NOT logged in."""
    # Execution steps
    step_number = 1
    with step(step_number, "Open the products page with the default page"):
        shop.inventory.open_page()
    step_number += 1
    with step(step_number, "Verify the login form asks for a login"):
        expect(shop.login.login_button).to_be_visible()
        expect(shop.login.error_message).to_have_text(LOGIN["not_logged_in_error"])
