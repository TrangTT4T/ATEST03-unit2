"""Fixtures for the UI tests (browser + page objects).

Fixture map (Day 5-6):
  browser (session) -> context (one per test: isolation) -> page (one per test)
  block_third_party  autouse network control: only the store and Shopify hosts are reached
  shop               Page Objects bound to this test's page
  add_product_and_open_cart   factory fixture: put N of a product in the cart, then open the cart page
  shop_api_in_browser         API objects bound to the page: share its cookies, watch or change its traffic
  saved_login_state  login once, reuse the saved storage state (auth)
"""
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlparse

import pytest
from playwright.sync_api import Browser, Page

from api import AccountApi, CartApi, NetworkApi, ProductApi, SearchApi
from pages import BasePage, CartPage, CatalogPage, CheckoutPage, LoginPage, ProductPage, RegisterPage, SearchPage

ROOT = Path(__file__).resolve().parents[2]
AUTH_FILE = ROOT / ".auth" / "customer.json"


# --- browser context (isolation) ------------------------------------------------
@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Every test gets a fresh context with these options: own cookies, own cart, own storage."""
    return {**browser_context_args, "viewport": {"width": 1366, "height": 900}, "locale": "en-GB"}


# --- network control (Day 6-7) --------------------------------------------------
@pytest.fixture(autouse=True)
def block_third_party(request, base_url: str):
    """Abort requests to third-party hosts (social widgets, analytics, Sauce app): NetworkApi does it.

    Removes the main source of flakiness that the store does not own.
    Opt out with @pytest.mark.allow_third_party. A test without a browser page has nothing to block,
    and must not start a browser for it. Yields the list of blocked URLs.
    """
    if request.node.get_closest_marker("allow_third_party") or "page" not in request.fixturenames:
        yield []
        return
    page = request.getfixturevalue("page")
    yield NetworkApi(page.context.request, page).block_third_party_hosts(urlparse(base_url).hostname)


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


@pytest.fixture
def shop_api_in_browser(page: Page) -> SimpleNamespace:
    """API objects bound to this test's page: they share the browser's cookies (what .cart adds, the cart
    page shows) and can watch or change the page's traffic (.cart add-to-cart requests, .network)."""
    request = page.context.request
    return SimpleNamespace(product=ProductApi(request, page), cart=CartApi(request, page),
                           search=SearchApi(request, page), network=NetworkApi(request, page),
                           account=AccountApi(request, page))


# --- authentication state (Day 6) ------------------------------------------------
@pytest.fixture(scope="session")
def saved_login_state(browser: Browser, base_url: str, real_account: dict) -> Path:
    """Log in once per session and save cookies/localStorage; tests reuse the file."""
    context = browser.new_context(base_url=base_url)
    page = context.new_page()
    login = LoginPage(page)
    login.open_page()
    login.login(real_account["email"], real_account["password"])
    page.wait_for_url("**/account**")
    AUTH_FILE.parent.mkdir(exist_ok=True)
    context.storage_state(path=str(AUTH_FILE))
    context.close()
    return AUTH_FILE
