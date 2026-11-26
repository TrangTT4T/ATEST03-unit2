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
@pytest.mark.parametrize(
    "email, password",
    [("not-a-user@example.com", "wrongpass1"), ("not-an-email", "wrongpass1")],
    ids=["unknown-user", "malformed-email"],
)
def test_login_is_rejected_with_invalid_credentials(shop, page, step, email, password):
    """Invalid credentials show an error and do not open the account page."""
    # Execution steps
    with step("Open the login page"):
        shop.login.open()
    with step(f"Log in as '{email}' with a wrong password"):
        shop.login.login(email, password)
    with step("Verify an error is shown and the account page is not opened"):
        expect(shop.login.error).to_be_visible()
        expect(page).not_to_have_url(re.compile(r"/account/?$"))


@pytest.mark.regression
def test_customer_opens_the_password_reset_form(shop, step):
    """'Forgot your password?' opens the password-reset form."""
    # Execution steps
    with step("Open the login page"):
        shop.login.open()
    with step("Choose 'Forgot your password?'"):
        shop.login.open_password_reset()
    with step("Verify the password-reset form is shown"):
        expect(shop.login.reset_form).to_be_visible()
