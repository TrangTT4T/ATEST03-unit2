"""Registration (risk R06, Medium). Requirement: @create_account (REQ-07).

The form tests are excluded by default:
* manual: the store's bot protection (CAPTCHA) stops the form (as for login, checked 2026-11-25);
* data_creating: a successful registration creates a real account - only with trainer approval.
"""
import re

import pytest
from playwright.sync_api import expect

pytestmark = [pytest.mark.medium, pytest.mark.create_account]


@pytest.mark.manual
@pytest.mark.negative
def test_registration_is_rejected_without_an_email(shop, accounts, step):
    """Registering with an empty email shows an error."""
    # Test data
    customer = accounts["customer-without-email"]  # made up by Faker

    # Execution steps
    step_number = 1
    with step(step_number, "Open the registration page"):
        shop.register.open_page()
    step_number += 1
    with step(step_number, f"Register as {customer['first_name']} {customer['last_name']} with no email"):
        shop.register.register_account(customer["first_name"], customer["last_name"], customer["email"],
                                       customer["password"])
    step_number += 1
    with step(step_number, "Verify an error is shown"):
        expect(shop.register.error_message).to_be_visible()


@pytest.mark.data_creating
def test_registration_succeeds_with_valid_details(shop, page, accounts, step):
    """Valid details create an account and open My Account (creates REAL data)."""
    # Test data
    customer = accounts["new-customer"]  # made up by Faker: a new unique email every run

    # Execution steps
    step_number = 1
    with step(step_number, "Open the registration page"):
        shop.register.open_page()
    step_number += 1
    with step(step_number, f"Register as {customer['first_name']} {customer['last_name']} with a new email"):
        shop.register.register_account(customer["first_name"], customer["last_name"], customer["email"],
                                       customer["password"])
    step_number += 1
    with step(step_number, "Verify the account page is opened"):
        expect(page).to_have_url(re.compile(r"/account/?$"))


@pytest.mark.regression
def test_header_sign_up_link_opens_the_registration_page(shop, page, step):
    """The header's "Sign up" link opens the create-account form."""
    # Execution steps
    step_number = 1
    with step(step_number, "Open the home page"):
        shop.home.open_page()
    step_number += 1
    with step(step_number, "Click 'Sign up' in the header"):
        shop.home.open_register_page_from_header()
    step_number += 1
    with step(step_number, "Verify the registration page is open"):
        expect(page).to_have_url(re.compile(r"/account/register"))
