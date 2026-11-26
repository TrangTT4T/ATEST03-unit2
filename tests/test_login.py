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
def test_login_is_rejected_with_invalid_credentials(shop, page, email, password):
    shop.login.open()
    shop.login.login(email, password)
    expect(shop.login.error).to_be_visible()
    expect(page).not_to_have_url(re.compile(r"/account/?$"))


@pytest.mark.regression
def test_customer_opens_the_password_reset_form(shop):
    shop.login.open()
    shop.login.open_password_reset()
    expect(shop.login.reset_form).to_be_visible()
