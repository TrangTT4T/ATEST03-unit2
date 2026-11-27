"""Shared fixtures and hooks for the Playwright suite (Unit 2).

Inherited from Unit 1: the requirements and risks (as markers), the test data
(dataset/products.json), the Page Object pattern, one fresh browser state per test.
New in Unit 2: plain Playwright tests on pytest - fixtures instead of hooks, markers instead of
Gherkin tags, network control, tracing, auth state, xdist.

Fixture map (Day 5-6):
  browser (session) -> context (one per test: isolation) -> page (one per test)
  products           test data from dataset/products.json
  accounts           test accounts from .env (never committed; see .env.example)
  block_third_party  autouse network control: only the store and Shopify hosts are reached (browser tests only)
  shop               Page Objects bound to this test's page
  add_product_and_open_cart   factory fixture: put N of a product in the cart, then open the cart page
  store_api          StoreApi on its own API context (no browser): products, cart, search
  store_api_in_browser        StoreApi that shares the browser's cookies: an API call changes the page's cart
  saved_login_state  login once, reuse the saved storage state (auth)
  step               numbered test steps: Allure step + trace group (helper_utility/steps.py)
"""
import json
import os
import shutil
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlparse

import pytest
from dotenv import load_dotenv
from playwright.sync_api import Browser, Page, Playwright

from api import StoreApi
from helper_utility.steps import Steps
from pages import BasePage, CartPage, CatalogPage, CheckoutPage, LoginPage, ProductPage, RegisterPage, SearchPage

ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "dataset"  # same file as the ATEST03-unit1 repo: dataset/products.json
AUTH_FILE = ROOT / ".auth" / "customer.json"
load_dotenv(ROOT / ".env")  # account data and the real login live in .env, which git ignores
SHOPIFY_SUFFIXES = (".shopify.com", ".myshopify.com", ".shopifycdn.com", ".shopifycloud.com", ".shopifysvc.com")
# Third-party hosts the THEME needs to work. The shop loads jQuery from Google's CDN; blocked, the
# product page never renders its "Sold Out" button (found 2026-11-25). Tracking hosts stay blocked.
THEME_DEPENDENCIES = ("ajax.googleapis.com",)
ALLURE_RESULTS = ROOT / "reports" / "allure-results"


# --- reports ------------------------------------------------------------------
def pytest_configure(config):
    """Start every run with an empty Allure folder, so the report shows this run only.

    Done here on the controller, not with --clean-alluredir: under pytest -n every xdist worker
    would clean the folder, and a late worker could delete what an early one already wrote.
    """
    if not hasattr(config, "workerinput"):
        shutil.rmtree(ALLURE_RESULTS, ignore_errors=True)


# --- data ---------------------------------------------------------------------
@pytest.fixture(scope="session")
def products() -> dict:
    with open(DATASET / "products.json", encoding="utf-8") as fh:
        return json.load(fh)["products"]


@pytest.fixture(scope="session")
def accounts() -> dict:
    """Test accounts by name, read from .env (git ignores it; .env.example lists the variables).

    No email or password is written in a file that goes to GitHub. A test that needs a value
    missing from .env is skipped and the message names the variables to set.
    """
    needed = ["TEST_PASSWORD", "WRONG_PASSWORD", "UNKNOWN_USER_EMAIL", "MALFORMED_EMAIL",
              "NEW_CUSTOMER_FIRST_NAME", "NEW_CUSTOMER_LAST_NAME", "NEW_CUSTOMER_EMAIL"]
    missing = [name for name in needed if not os.getenv(name)]
    if missing:
        pytest.skip(f"Set {', '.join(missing)} in .env (see .env.example) to run the account tests")
    env = os.environ
    return {
        "new-customer": {"first_name": env["NEW_CUSTOMER_FIRST_NAME"], "last_name": env["NEW_CUSTOMER_LAST_NAME"],
                         "email": env["NEW_CUSTOMER_EMAIL"], "password": env["TEST_PASSWORD"]},
        "customer-without-email": {"first_name": env["NEW_CUSTOMER_FIRST_NAME"], "last_name": env["NEW_CUSTOMER_LAST_NAME"],
                                   "email": "", "password": env["TEST_PASSWORD"]},
        "unknown-user": {"email": env["UNKNOWN_USER_EMAIL"], "password": env["WRONG_PASSWORD"]},
        "malformed-email": {"email": env["MALFORMED_EMAIL"], "password": env["WRONG_PASSWORD"]},
    }


# --- browser context (isolation) ------------------------------------------------
@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Every test gets a fresh context with these options: own cookies, own cart, own storage."""
    return {**browser_context_args, "viewport": {"width": 1366, "height": 900}, "locale": "en-GB"}


# --- network control (Day 6-7) --------------------------------------------------
def _is_allowed_host(url: str, store_host: str) -> bool:
    host = urlparse(url).hostname or ""
    if urlparse(url).scheme in ("data", "blob"):
        return True
    return host in (store_host, "localhost", "127.0.0.1", *THEME_DEPENDENCIES) or host.endswith(SHOPIFY_SUFFIXES)


@pytest.fixture(autouse=True)
def block_third_party(request, base_url: str):
    """Abort requests to third-party hosts (social widgets, analytics, Sauce app).

    Removes the main source of flakiness that the store does not own.
    Opt out with @pytest.mark.allow_third_party. A test without a browser page (an API test) has
    nothing to block, and must not start a browser for it. Yields the list of blocked URLs.
    """
    blocked: list[str] = []
    if request.node.get_closest_marker("allow_third_party") or "page" not in request.fixturenames:
        yield blocked
        return
    context = request.getfixturevalue("context")
    store_host = urlparse(base_url).hostname

    def abort_third_party_request(route):
        if _is_allowed_host(route.request.url, store_host):
            route.continue_()
        else:
            blocked.append(route.request.url)
            route.abort()

    context.route("**/*", abort_third_party_request)
    yield blocked


# --- page objects ---------------------------------------------------------------
@pytest.fixture
def shop(page: Page) -> SimpleNamespace:
    return SimpleNamespace(home=BasePage(page), catalog=CatalogPage(page), product=ProductPage(page),
                           cart=CartPage(page), checkout=CheckoutPage(page), login=LoginPage(page),
                           register=RegisterPage(page), search=SearchPage(page))


@pytest.fixture
def add_product_and_open_cart(shop, products):
    """Factory fixture: add_product_and_open_cart("Noir jacket", 2) puts 2 Noir jackets in this test's
    cart, opens the cart page and returns it."""
    def add_and_open_cart(name: str, quantity: int = 1):
        shop.product.open_product_page(products[name]["path-name"])
        shop.product.add_to_cart(quantity)
        shop.cart.open_page()
        return shop.cart
    return add_and_open_cart


# --- API objects (Day 6: API testing) ---------------------------------------------
@pytest.fixture
def store_api(playwright: Playwright, base_url: str):
    """StoreApi on its own API request context: no browser, its own cart (one per test)."""
    request_context = playwright.request.new_context(base_url=base_url)
    yield StoreApi(request_context)
    request_context.dispose()


@pytest.fixture
def store_api_in_browser(page: Page) -> StoreApi:
    """StoreApi that shares the browser's cookies: what it adds to the cart, the page's cart shows."""
    return StoreApi(page.context.request)


# --- test steps ---------------------------------------------------------------
@pytest.fixture
def step(request) -> Steps:
    """``with step("Add 1 item to the cart"):`` - numbered for you: Step 1, Step 2, ..."""
    page = request.getfixturevalue("page") if "page" in request.fixturenames else None
    return Steps(page)


# --- authentication state (Day 6) ------------------------------------------------
@pytest.fixture(scope="session")
def saved_login_state(browser: Browser, base_url: str) -> Path:
    """Log in once per session and save cookies/localStorage; tests reuse the file."""
    email, password = os.getenv("SAUCE_EMAIL"), os.getenv("SAUCE_PASSWORD")
    if not (email and password):
        pytest.skip("Set SAUCE_EMAIL and SAUCE_PASSWORD to run @auth tests")
    context = browser.new_context(base_url=base_url)
    page = context.new_page()
    login = LoginPage(page)
    login.open_page()
    login.login(email, password)
    page.wait_for_url("**/account**")
    AUTH_FILE.parent.mkdir(exist_ok=True)
    context.storage_state(path=str(AUTH_FILE))
    context.close()
    return AUTH_FILE
