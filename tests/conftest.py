"""Fixtures and hooks for the whole suite (Unit 2): Playwright UI tests of Swag Labs (www.saucedemo.com).

Fixture map (Day 5-6):
  browser (session) -> context (one per test: isolation) -> page (one per test)
  products           test data from dataset/products.json (the other dataset files are read by the tests)
  swag_accounts      the Swag Labs demo accounts from .env; skips when unset
  shopper            the account logged_in_shop uses: --account (default standard-user)
  accounts           every login a test may need: the demo accounts + made-up ones (Faker), new per test
  checkout_information  a made-up customer for the checkout form (Faker)
  shop               Page Objects bound to this test's page
  logged_in_shop     shop, logged in with the saved cookie (no login form), on the products page
  fill_cart          factory fixture: add products from the products page
  phone_shop         shop in a context emulating an iPhone 13 (Day 5: contexts beyond isolation)
  open_shop_as       factory: log another account in, in a context of its own (visual comparison)
  saved_login_state  log in ONCE through the form, save the cookies; again only when they are about to expire
  step               numbered test steps: Allure step + trace group (helper_utility/steps.py)
"""
import logging
import os
import platform
import shutil
import time
from importlib.metadata import version
from pathlib import Path
from types import SimpleNamespace

import allure
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
AUTH_DIR = ROOT / ".auth"  # saved login states (git ignores it)
PHONE = "iPhone 13"  # a Playwright device: viewport, touch, user agent, scale
LOGIN_STATE_MAX_AGE = 9 * 60  # seconds: Swag Labs' session cookie expires 10 minutes after the login
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
        write_allure_settings(config)


def write_allure_settings(config):
    """Day 6 reporting / Day 8 failure analysis: what the Allure report shows next to the results.

    * categories.json (allure/categories.json): sorts every failure into a known defect (xfail),
      a product defect (an assertion failed: the shop showed a wrong value) or a test or environment
      problem (an exception: a timeout, a missing element, a browser error);
    * environment.properties: the base URL, browsers, account, Python and Playwright versions of this run.
    """
    ALLURE_RESULTS.mkdir(parents=True, exist_ok=True)
    shutil.copy(ROOT / "allure" / "categories.json", ALLURE_RESULTS / "categories.json")
    environment = {
        "Base.URL": config.getoption("base_url") or config.getini("base_url"),
        "Browsers": ", ".join(config.getoption("browser") or ["chromium"]),
        "Account": config.getoption("--account"),
        "Python": platform.python_version(),
        "Playwright": version("playwright"),
    }
    lines = [f"{key}={value}" for key, value in environment.items()]
    (ALLURE_RESULTS / "environment.properties").write_text("\n".join(lines) + "\n", encoding="utf-8")


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    """Attach the evidence of a failed browser test to Allure.

    * call phase: a full-page screenshot and the address of the page, in the test body;
    * teardown phase: the trace.zip and the video. pytest-playwright writes them when the browser
      context closes, which is after the test body, so they are attached once its own teardown
      report is done (they show under "Tear down").
    """
    report = yield
    page = item.funcargs.get("page")
    if report.when == "call":
        item.call_failed = report.failed
        if report.failed and page is not None and not page.is_closed():
            allure.attach(page.screenshot(full_page=True), name="Page at the failure",
                          attachment_type=allure.attachment_type.PNG)
            allure.attach(page.url, name="Address at the failure", attachment_type=allure.attachment_type.TEXT)
    elif report.when == "teardown" and getattr(item, "call_failed", False) and "output_path" in item.funcargs:
        output_path = Path(item.funcargs["output_path"])
        for trace in output_path.glob("*.zip"):
            allure.attach.file(str(trace), name="Playwright trace (open: playwright show-trace)", extension="zip")
        for video in output_path.glob("*.webm"):
            allure.attach.file(str(video), name="Video", attachment_type=allure.attachment_type.WEBM)
    return report


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
def make_shop(page: Page) -> SimpleNamespace:
    """Every Page Object, bound to ``page``: shop.login, shop.inventory, shop.cart ..."""
    return SimpleNamespace(
        home=BasePage(page), login=LoginPage(page), inventory=InventoryPage(page), product=ProductPage(page),
        cart=CartPage(page), checkout_information=CheckoutInformationPage(page),
        checkout_overview=CheckoutOverviewPage(page), checkout_complete=CheckoutCompletePage(page),
    )


@pytest.fixture
def shop(page: Page) -> SimpleNamespace:
    """Every Page Object, bound to this test's page."""
    return make_shop(page)


@pytest.fixture
def phone_shop(browser: Browser, playwright, base_url: str, saved_login_state) -> SimpleNamespace:
    """Day 5, browser contexts: ``shop`` in a context that emulates an iPhone 13 (390x844 screen, touch,
    mobile user agent, device scale 3), logged in with the saved cookie, on the products page.
    """
    device = {key: value for key, value in playwright.devices[PHONE].items() if key != "default_browser_type"}
    context = browser.new_context(**device, base_url=base_url)
    account_shop = make_shop(context.new_page())
    account_shop.inventory.add_login_cookies(saved_login_state)
    account_shop.inventory.open_page()
    account_shop.inventory.verify_products_page_is_open()
    yield account_shop
    context.close()


@pytest.fixture
def logged_in_shop(shop, saved_login_state) -> SimpleNamespace:
    """``shop``, logged in as the --account user WITHOUT the login form, on the products page.

    The session logged in once (saved_login_state); here the saved cookie goes into this test's own
    context. Only the cookie: the cart (localStorage) is not copied, so every test starts with an
    empty cart, as before.
    """
    shop.inventory.add_login_cookies(saved_login_state)
    shop.inventory.open_page()
    shop.inventory.verify_products_page_is_open()
    return shop


@pytest.fixture
def fill_cart(logged_in_shop):
    """Factory fixture: fill_cart(["Sauce Labs Backpack", ...]) adds the products from the products page."""
    def add_products(product_names: list[str]):
        logged_in_shop.inventory.add_products_to_cart(product_names)
        return logged_in_shop
    return add_products


@pytest.fixture
def open_shop_as(browser: Browser, browser_context_args, swag_accounts):
    """Factory fixture: open_shop_as("visual-user") logs that account in, in a NEW context of its own
    (same viewport and base URL as `page`), and returns its shop on the products page.

    For tests that compare two accounts side by side; the contexts are closed after the test.
    """
    contexts = []

    def open_shop(account_name: str) -> SimpleNamespace:
        if account_name not in swag_accounts:
            pytest.skip(f"Set the username of {account_name} in .env (see .env.example)")
        context = browser.new_context(**browser_context_args)
        contexts.append(context)
        page = context.new_page()
        account_shop = make_shop(page)
        account_shop.login.open_page()
        account_shop.login.login_and_wait_for_products(swag_accounts[account_name]["username"],
                                                       swag_accounts[account_name]["password"])
        account_shop.inventory.verify_products_page_is_open()
        return account_shop

    yield open_shop
    for context in contexts:
        context.close()


# --- authentication state (Day 6) ------------------------------------------------
@pytest.fixture(scope="session")
def login_state_record() -> dict:
    """When this session (this xdist worker) last saved its login state, and where."""
    return {"path": None, "saved_at": 0.0}


@pytest.fixture
def saved_login_state(browser: Browser, base_url: str, shopper, login_state_record) -> Path:
    """The saved login of the --account user: cookies + localStorage in .auth/<user>_<process>.json.

    The login form is used ONCE per session (per worker with -n, each has its own file), then the
    file is reused. It is renewed only when it is older than LOGIN_STATE_MAX_AGE, because Swag Labs'
    session cookie expires 10 minutes after the login.
    """
    age = time.monotonic() - login_state_record["saved_at"]
    if login_state_record["path"] is None or age > LOGIN_STATE_MAX_AGE:
        path = AUTH_DIR / f"{shopper['username']}_{os.getpid()}.json"
        context = browser.new_context(base_url=base_url)
        login = LoginPage(context.new_page())
        login.open_page()
        login.login_and_wait_for_products(shopper["username"], shopper["password"])
        AUTH_DIR.mkdir(exist_ok=True)
        context.storage_state(path=str(path))
        context.close()
        logging.getLogger("saved_login_state").info("Logged in as %s through the form; state saved in %s",
                                                    shopper["username"], path.name)
        login_state_record.update(path=path, saved_at=time.monotonic())
    return login_state_record["path"]


# --- test steps ---------------------------------------------------------------
@pytest.fixture
def step(request) -> Steps:
    """``with step(step_number, "Add 1 item to the cart"):`` - Step 1, Step 2 ... in Allure and the trace."""
    page = request.getfixturevalue("page") if "page" in request.fixturenames else None
    return Steps(page)
