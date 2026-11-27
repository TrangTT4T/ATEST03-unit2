"""Account API (Day 6: API testing): log in, log out, register, without a browser.

Requirements: @secure_login (REQ-05), @create_account (REQ-07).

The store's bot protection (CAPTCHA) also guards the account forms, so the tests that POST a form
are excluded by default, like their UI twins: manual (run in a test environment without CAPTCHA),
data_creating (creates a real account) and auth (needs the real account from .env).
"""
import pytest

pytestmark = [pytest.mark.api]


@pytest.mark.high
@pytest.mark.regression
@pytest.mark.secure_login
def test_account_page_sends_a_guest_to_the_login_page(shop_api, step):
    """A guest asking for /account is redirected to the login page, not shown an account."""
    # Execution steps
    step_number = 1
    with step(step_number, "GET /account without logging in"):
        redirect = shop_api.account.get_account_redirect()
    step_number += 1
    with step(step_number, "Verify the redirect goes to /account/login and the session is not logged in"):
        assert "/account/login" in redirect, f"/account redirected to {redirect!r}"
        assert not shop_api.account.is_logged_in()


@pytest.mark.high
@pytest.mark.manual
@pytest.mark.negative
@pytest.mark.secure_login
@pytest.mark.parametrize("account_name", ["unknown-user", "malformed-email"])  # made up by Faker for every test
def test_login_api_rejects_invalid_credentials(shop_api, accounts, step, account_name):
    """Invalid credentials do not log in: the login page answers again (HTTP 200) and /account stays closed."""
    # Test data
    account = accounts[account_name]

    # Execution steps
    step_number = 1
    with step(step_number, f"POST /account/login as {account['email']!r}"):
        response = shop_api.account.login(account["email"], account["password"])
    step_number += 1
    with step(step_number, "Verify the login is refused and the session is not logged in"):
        assert response.status == 200, f"HTTP {response.status} -> {response.headers.get('location')}"
        assert not shop_api.account.is_logged_in()


@pytest.mark.high
@pytest.mark.auth
@pytest.mark.secure_login
def test_login_api_logs_the_customer_in_and_out(shop_api, real_account, step):
    """The real customer logs in (/account opens) and logs out (/account is closed again)."""
    # Execution steps
    step_number = 1
    with step(step_number, "POST /account/login with the real account from .env"):
        shop_api.account.login(real_account["email"], real_account["password"])
    step_number += 1
    with step(step_number, "Verify /account opens"):
        assert shop_api.account.is_logged_in()
    step_number += 1
    with step(step_number, "GET /account/logout"):
        shop_api.account.logout()
    step_number += 1
    with step(step_number, "Verify /account is closed again"):
        assert not shop_api.account.is_logged_in()


@pytest.mark.medium
@pytest.mark.manual
@pytest.mark.negative
@pytest.mark.create_account
def test_register_api_rejects_a_missing_email(shop_api, accounts, step):
    """Registering with an empty email creates no account: the session is not logged in."""
    # Test data
    customer = accounts["customer-without-email"]  # made up by Faker

    # Execution steps
    step_number = 1
    with step(step_number, f"POST /account as {customer['first_name']} {customer['last_name']} with no email"):
        shop_api.account.register_account(customer["first_name"], customer["last_name"], customer["email"],
                                          customer["password"])
    step_number += 1
    with step(step_number, "Verify the session is not logged in"):
        assert not shop_api.account.is_logged_in()


@pytest.mark.medium
@pytest.mark.data_creating
@pytest.mark.create_account
def test_register_api_creates_an_account_and_logs_it_in(shop_api, accounts, step):
    """Valid details create an account and log the new customer in (creates REAL data)."""
    # Test data
    customer = accounts["new-customer"]  # made up by Faker: a new unique email every run

    # Execution steps
    step_number = 1
    with step(step_number, f"POST /account as {customer['email']}"):
        shop_api.account.register_account(customer["first_name"], customer["last_name"], customer["email"],
                                          customer["password"])
    step_number += 1
    with step(step_number, "Verify the new customer is logged in"):
        assert shop_api.account.is_logged_in()
