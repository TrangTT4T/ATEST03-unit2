"""Login (risk R04, High). Requirement: @secure_login (REQ-05).

MANUAL on the public demo store: its bot protection (CAPTCHA) stops the login form - no request is
sent and no error is shown (checked 2026-11-25), so a wrong-password test could only fail. The test
is complete: in a test environment without CAPTCHA, run it with  pytest -m manual.
"""
import re

import pytest
from playwright.sync_api import expect

pytestmark = [pytest.mark.high, pytest.mark.secure_login]


@pytest.mark.manual
@pytest.mark.negative
@pytest.mark.parametrize("account_name", ["unknown-user", "malformed-email"])  # accounts come from .env
def test_login_is_rejected_with_invalid_credentials(shop, page, accounts, step, account_name):
    """Invalid credentials show an error and do not open the account page."""
    # Test data
    account = accounts[account_name]

    # Execution steps
    with step("Open the login page"):
        shop.login.open_page()
    with step(f"Log in as '{account['email']}' with a wrong password"):
        shop.login.login(account["email"], account["password"])
    with step("Verify an error is shown and the account page is not opened"):
        expect(shop.login.error_message).to_be_visible()
        expect(page).not_to_have_url(re.compile(r"/account/?$"))


@pytest.mark.regression
def test_customer_opens_the_password_reset_form(shop, step):
    """'Forgot your password?' opens the password-reset form."""
    # Execution steps
    with step("Open the login page"):
        shop.login.open_page()
    with step("Choose 'Forgot your password?'"):
        shop.login.click_forgot_password()
    with step("Verify the password-reset form is shown"):
        expect(shop.login.password_reset_form).to_be_visible()
