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
@pytest.mark.parametrize("account_name", ["unknown-user", "malformed-email"])  # made up by Faker for every test
def test_login_is_rejected_with_invalid_credentials(shop, page, accounts, step, account_name):
    """Invalid credentials show an error and do not open the account page."""
    # Test data
    account = accounts[account_name]

    # Execution steps
    step_number = 1
    with step(step_number, "Open the login page"):
        shop.login.open_page()
    step_number += 1
    with step(step_number, f"Log in as '{account['email']}' with a wrong password"):
        shop.login.login(account["email"], account["password"])
    step_number += 1
    with step(step_number, "Verify an error is shown and the account page is not opened"):
        expect(shop.login.error_message).to_be_visible()
        expect(page).not_to_have_url(re.compile(r"/account/?$"))


@pytest.mark.regression
def test_customer_opens_the_password_reset_form(shop, step):
    """'Forgot your password?' opens the password-reset form."""
    # Execution steps
    step_number = 1
    with step(step_number, "Open the login page"):
        shop.login.open_page()
    step_number += 1
    with step(step_number, "Choose 'Forgot your password?'"):
        shop.login.click_forgot_password()
    step_number += 1
    with step(step_number, "Verify the password-reset form is shown"):
        expect(shop.login.password_reset_form).to_be_visible()


@pytest.mark.regression
def test_header_log_in_link_opens_the_login_page(shop, page, step):
    """A guest sees "Log In" in the header, and it opens the login form."""
    # Execution steps
    step_number = 1
    with step(step_number, "Open the home page"):
        shop.home.open_page()
    step_number += 1
    with step(step_number, "Verify no customer is logged in"):
        assert not shop.home.is_customer_logged_in()
    step_number += 1
    with step(step_number, "Click 'Log In' in the header"):
        shop.home.open_login_page_from_header()
    step_number += 1
    with step(step_number, "Verify the login page is open"):
        expect(page).to_have_url(re.compile(r"/account/login"))


@pytest.mark.manual
@pytest.mark.negative
def test_password_reset_is_rejected_for_an_unknown_email(shop, accounts, step):
    """A password reset for an email with no account shows an error (no email is sent)."""
    # Test data
    unknown_user = accounts["unknown-user"]  # made up by Faker

    # Execution steps
    step_number = 1
    with step(step_number, "Open the login page"):
        shop.login.open_page()
    step_number += 1
    with step(step_number, f"Ask for a password reset for {unknown_user['email']!r}"):
        shop.login.request_password_reset(unknown_user["email"])
    step_number += 1
    with step(step_number, "Verify an error is shown"):
        expect(shop.login.error_message).to_be_visible()


@pytest.mark.auth
def test_customer_logs_in_and_out(shop, real_account, step):
    """The real customer logs in through the form, then logs out."""
    # Execution steps
    step_number = 1
    with step(step_number, "Open the login page"):
        shop.login.open_page()
    step_number += 1
    with step(step_number, "Log in with the real account from .env"):
        shop.login.login(real_account["email"], real_account["password"])
    step_number += 1
    with step(step_number, "Verify the customer is logged in"):
        assert shop.login.is_customer_logged_in()
    step_number += 1
    with step(step_number, "Log out"):
        shop.login.logout()
    step_number += 1
    with step(step_number, "Verify no customer is logged in"):
        assert not shop.login.is_customer_logged_in()
