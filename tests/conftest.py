"""Fixtures and hooks for the whole suite (Unit 2): Playwright UI tests of Swag Labs (www.saucedemo.com).

Fixture map (Day 5-6):
  browser (session) -> context (one per test: isolation) -> page (one per test)
  products           test data from dataset/products.json (the other dataset files are read by the tests)
  swag_accounts      the Swag Labs demo accounts from .env; skips when unset
  shopper            the account logged_in_shop uses: --account (default standard-user)
  accounts           every login a test may need: the demo accounts + made-up ones (Faker), new per test
  checkout_information  a made-up customer for the checkout form (Faker)
  shop               Page Objects bound to this test's page
  logged_in_shop     shop, logged in as the standard user, on the products page
  fill_cart          factory fixture: add products from the products page
  saved_login_state  login once, save the storage state (Day 6: authentication state reuse)
  step               numbered test steps: Allure step + trace group (helper_utility/steps.py)
"""
import os
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest
from dotenv import load_dotenv
from playwright.sync_api import Browser, Page

from helper_utility.helpers import Helper
from helper_utility.steps import Steps
from pages import (BasePage, CartPage, CheckoutCompletePage, CheckoutInformationPage, CheckoutOverviewPage,
                   InventoryPage, LoginPage, ProductPage)

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")  # the demo accounts live in .env, which git ignores
ALLURE_RESULTS = ROOT / "reports" / "allure-results"
AUTH_FILE = ROOT / ".auth" / "standard_user.json"
# Every Swag Labs demo account (listed on its login page) and the .env variable that holds its username.
ACCOUNT_VARIABLES = {
    "standard-user": "SWAG_USERNAME",
    "locked-out-user": "SWAG_LOCKED_OUT_USERNAME",
    "problem-user": "SWAG_PROBLEM_USERNAME",
    "performance-glitch-user": "SWAG_PERFORMANCE_GLITCH_USERNAME",
    "error-user": "SWAG_ERROR_USERNAME",
    "visual-user": "SWAG_VISUAL_USERNAME",
}
REQUIRED_ACCOUNTS = ("standard-user", "locked-out-user")  # used by the login tests whatever --account is


def pytest_addoption(parser):
    """--account: the demo account the shopping tests log in as, e.g. pytest --account problem-user."""
    parser.addoption("--account", default="standard-user", choices=sorted(ACCOUNT_VARIABLES),
                     help="Swag Labs demo account for the logged-in tests (default: standard-user)")


def pytest_report_header(config):
    """Show the chosen account at the top of the run."""
    return f"Swag Labs account for the logged-in tests: {config.getoption('--account')}"


# --- reports ------------------------------------------------------------------
def pytest_configure(config):
    """Start every run with an empty Allure folder, so the report shows this run only.

    Done here on the controller, not with --clean-alluredir: under pytest -n every xdist worker
    would clean the folder, and a late worker could delete what an early one already wrote.
    """
    if not hasattr(config, "workerinput"):
        shutil.rmtree(ALLURE_RESULTS, ignore_errors=True)


# --- browser context (isolation) ------------------------------------------------
@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Every test gets a fresh context with these options: own cookies, own cart (localStorage)."""
    return {**browser_context_args, "viewport": {"width": 1366, "height": 900}, "locale": "en-US"}


# --- data ---------------------------------------------------------------------
@pytest.fixture(scope="session")
def products() -> dict:
    """Every product by name, from dataset/products.json (id, price, description)."""
    return Helper.read_test_data("products")["products"]


@pytest.fixture(scope="session")
def swag_accounts(pytestconfig) -> dict:
    """The Swag Labs demo accounts from .env by name, e.g. "standard-user": {username, password}.

    Skips the test when a needed variable is missing: copy .env.example to .env and fill in the
    accounts listed on the Swag Labs login page. No account is written in a file that goes to GitHub.
    """
    needed = {*REQUIRED_ACCOUNTS, pytestconfig.getoption("--account")}
    missing = [ACCOUNT_VARIABLES[name] for name in sorted(needed) if not os.getenv(ACCOUNT_VARIABLES[name])]
    missing += [] if os.getenv("SWAG_PASSWORD") else ["SWAG_PASSWORD"]
    if missing:
        pytest.skip(f"Set {', '.join(missing)} in .env (copy .env.example; the values are on the login page)")
    password = os.environ["SWAG_PASSWORD"]
    return {name: {"username": os.environ[variable], "password": password}
            for name, variable in ACCOUNT_VARIABLES.items() if os.getenv(variable)}


@pytest.fixture(scope="session")
def shopper(pytestconfig, swag_accounts) -> dict:
    """The account the logged-in tests use: --account (default standard-user)."""
    return swag_accounts[pytestconfig.getoption("--account")]


@pytest.fixture
def accounts(swag_accounts) -> dict:
    """Every login of dataset/login.json by name: the demo accounts + made-up ones (Faker), new per test."""
    standard_user = swag_accounts["standard-user"]
    return {
        **swag_accounts,
        "unknown-user": Helper.random_unregistered_login(),
        "wrong-password": {"username": standard_user["username"], "password": Helper.random_password()},
        "missing-username": {"username": "", "password": standard_user["password"]},
        "missing-password": {"username": standard_user["username"], "password": ""},
    }


@pytest.fixture
def checkout_information() -> dict:
    """A made-up customer for the checkout form (Faker): first_name, last_name, postal_code."""
    return Helper.random_checkout_information()


# --- page objects ---------------------------------------------------------------
@pytest.fixture
def shop(page: Page) -> SimpleNamespace:
    """Every Page Object, bound to this test's page: shop.login, shop.inventory, shop.cart ..."""
    return SimpleNamespace(
        home=BasePage(page), login=LoginPage(page), inventory=InventoryPage(page), product=ProductPage(page),
        cart=CartPage(page), checkout_information=CheckoutInformationPage(page),
        checkout_overview=CheckoutOverviewPage(page), checkout_complete=CheckoutCompletePage(page),
    )


@pytest.fixture
def logged_in_shop(shop, shopper) -> SimpleNamespace:
    """``shop``, logged in through the login form as the --account user, on the products page."""
    shop.login.open_page()
    shop.login.login_and_wait_for_products(shopper["username"], shopper["password"])
    return shop


@pytest.fixture
def fill_cart(logged_in_shop):
    """Factory fixture: fill_cart(["Sauce Labs Backpack", ...]) adds the products from the products page."""
    def add_products(product_names: list[str]):
        logged_in_shop.inventory.add_products_to_cart(product_names)
        return logged_in_shop
    return add_products


# --- authentication state (Day 6) ------------------------------------------------
@pytest.fixture(scope="session")
def saved_login_state(browser: Browser, base_url: str, swag_accounts) -> Path:
    """Log in once per session and save cookies + localStorage; a test opens a context from the file."""
    context = browser.new_context(base_url=base_url)
    login = LoginPage(context.new_page())
    login.open_page()
    standard_user = swag_accounts["standard-user"]
    login.login_and_wait_for_products(standard_user["username"], standard_user["password"])
    AUTH_FILE.parent.mkdir(exist_ok=True)
    context.storage_state(path=str(AUTH_FILE))
    context.close()
    return AUTH_FILE


# --- test steps ---------------------------------------------------------------
@pytest.fixture
def step(request) -> Steps:
    """``with step(step_number, "Add 1 item to the cart"):`` - Step 1, Step 2 ... in Allure and the trace."""
    page = request.getfixturevalue("page") if "page" in request.fixturenames else None
    return Steps(page)
