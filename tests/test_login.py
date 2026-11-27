"""Login (risk R04, High). Requirement: @secure_login (REQ-05).

The rejected logins come from dataset/login.json; the accounts themselves come from .env (the demo
accounts) or are made up by Faker for every test (unknown user, wrong password).
"""
import re

import pytest
from playwright.sync_api import expect

from helper_utility.helpers import Helper

pytestmark = [pytest.mark.high, pytest.mark.secure_login]
LOGIN = Helper.read_test_data("login")


@pytest.mark.smoke
def test_standard_user_logs_in_and_sees_the_products(shop, page, swag_accounts, products, step):
    """The standard user logs in and lands on the products page with every product."""
    # Test data
    standard_user = swag_accounts["standard-user"]

    # Execution steps
    step_number = 1
    with step(step_number, "Open the login page"):
        shop.login.open_page()
    step_number += 1
    with step(step_number, "Log in as the standard user"):
        shop.login.login(standard_user["username"], standard_user["password"])
    step_number += 1
    with step(step_number, f"Verify the products page lists the {len(products)} products"):
        expect(page).to_have_url(re.compile(r"/inventory\.html$"))
        expect(shop.inventory.page_title).to_have_text("Products")
        assert sorted(shop.inventory.get_product_names()) == sorted(products)


@pytest.mark.regression
@pytest.mark.negative
@pytest.mark.parametrize("case", LOGIN["rejected"], ids=[case["id"] for case in LOGIN["rejected"]])
def test_login_is_rejected(shop, page, accounts, step, case):
    """A wrong, locked-out or incomplete login shows its error and stays on the login page (dataset/login.json)."""
    # Test data
    account = accounts[case["account"]]

    # Execution steps
    step_number = 1
    with step(step_number, "Open the login page"):
        shop.login.open_page()
    step_number += 1
    with step(step_number, f"Log in as {case['account']} (username {account['username']!r})"):
        shop.login.login(account["username"], account["password"])
    step_number += 1
    with step(step_number, f"Verify the error {case['error']!r} and that the products page is not opened"):
        expect(shop.login.error_message).to_have_text(case["error"])
        expect(page).not_to_have_url(re.compile(r"/inventory\.html"))


@pytest.mark.regression
def test_customer_logs_out(logged_in_shop, step):
    """Logout returns to the login page, and the products page then asks for a login again."""
    # Execution steps
    step_number = 1
    with step(step_number, "Log out from the side menu"):
        logged_in_shop.inventory.logout()
    step_number += 1
    with step(step_number, "Verify the login form is shown"):
        expect(logged_in_shop.login.login_button).to_be_visible()
    step_number += 1
    with step(step_number, "Open the products page directly"):
        logged_in_shop.inventory.open_page()
    step_number += 1
    with step(step_number, "Verify the shop asks for a login"):
        expect(logged_in_shop.login.error_message).to_have_text(LOGIN["not_logged_in_error"])


@pytest.mark.regression
@pytest.mark.negative
def test_products_page_needs_a_login(shop, step):
    """A visitor who opens /inventory.html without logging in is sent back to the login form."""
    # Execution steps
    step_number = 1
    with step(step_number, "Open the products page without logging in"):
        shop.inventory.open_page()
    step_number += 1
    with step(step_number, "Verify the login form says a login is needed"):
        expect(shop.login.login_button).to_be_visible()
        expect(shop.login.error_message).to_have_text(LOGIN["not_logged_in_error"])
