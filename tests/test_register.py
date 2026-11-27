"""Registration (risk R06, Medium). Requirement: @create_account (REQ-07).

Both tests are excluded by default:
* manual: the store's bot protection (CAPTCHA) stops the form (as for login, checked 2026-11-25);
* data_creating: a successful registration creates a real account - only with trainer approval.
"""
import re
import uuid

import pytest
from playwright.sync_api import expect

pytestmark = [pytest.mark.medium, pytest.mark.create_account]


@pytest.mark.manual
@pytest.mark.negative
def test_registration_is_rejected_without_an_email(shop, accounts, step):
    """Registering with an empty email shows an error."""
    # Test data
    customer = accounts["customer-without-email"]  # from .env

    # Execution steps
    with step("Open the registration page"):
        shop.register.open_page()
    with step(f"Register as {customer['first_name']} {customer['last_name']} with no email"):
        shop.register.register(customer["first_name"], customer["last_name"], customer["email"], customer["password"])
    with step("Verify an error is shown"):
        expect(shop.register.error_message).to_be_visible()


@pytest.mark.data_creating
def test_registration_succeeds_with_valid_details(shop, page, accounts, step):
    """Valid details create an account and open My Account (creates REAL data)."""
    # Test data
    customer = accounts["new-customer"]  # from .env
    email = customer["email"].format(unique=uuid.uuid4().hex[:10])  # a new address every run

    # Execution steps
    with step("Open the registration page"):
        shop.register.open_page()
    with step(f"Register as {customer['first_name']} {customer['last_name']} with a new email"):
        shop.register.register(customer["first_name"], customer["last_name"], email, customer["password"])
    with step("Verify the account page is opened"):
        expect(page).to_have_url(re.compile(r"/account/?$"))
