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
def test_registration_is_rejected_without_an_email(shop):
    shop.register.open()
    shop.register.register("Test", "User", "", "Passw0rd!2026")
    expect(shop.register.error).to_be_visible()


@pytest.mark.data_creating
def test_registration_succeeds_with_valid_details(shop, page):
    shop.register.open()
    shop.register.register("Playwright", "Tester", f"pw.{uuid.uuid4().hex[:10]}@example.com", "Passw0rd!2026")
    expect(page).to_have_url(re.compile(r"/account/?$"))
