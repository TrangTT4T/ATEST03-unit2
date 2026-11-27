"""Authentication state reuse (Day 6) – login risk (High).

Unit 1 logged in through the UI in every scenario that needed it. Here the session fixture
`saved_login_state` logs in once, saves cookies + localStorage, and each test starts already logged in.
Run with:  SAUCE_EMAIL=... SAUCE_PASSWORD=... pytest -m auth
"""
import re

import pytest
from playwright.sync_api import Browser, expect

pytestmark = [pytest.mark.auth, pytest.mark.high, pytest.mark.secure_login]

LOGOUT_LINK = re.compile("log ?out", re.I)


def test_saved_auth_state_opens_account_without_login(browser: Browser, base_url, saved_login_state, step):
    """A context created from the saved login opens My Account without the login form."""
    # Execution steps
    with step("Open a new browser context with the saved login"):
        context = browser.new_context(base_url=base_url, storage_state=str(saved_login_state))
        page = context.new_page()
    with step("Open My Account"):
        page.goto("/account")
    with step("Verify the account page is shown with a Log out link"):
        expect(page).not_to_have_url(re.compile(r"/account/login"))
        expect(page.get_by_role("link", name=LOGOUT_LINK)).to_be_visible()
    with step("Close the context"):
        context.close()


def test_auth_state_does_not_leak_into_other_tests(page, step):
    """Isolation check: the default `page` fixture has its own context, so it is NOT logged in."""
    # Execution steps
    with step("Open My Account with the default page"):
        page.goto("/account")
    with step("Verify the login page is shown"):
        expect(page).to_have_url(re.compile(r"/account/login"))
