"""Fixtures for the UI tests (browser + page objects).

Fixture map (Day 5-6):
  browser (session) -> context (one per test: isolation) -> page (one per test)
  block_third_party  autouse network control: only the store and Shopify hosts are reached
  shop               Page Objects bound to this test's page
  add_product_and_open_cart   factory fixture: put N of a product in the cart, then open the cart page
  shop_api_in_browser         API objects that share the browser's cookies: an API call changes the page's cart
  saved_login_state  login once, reuse the saved storage state (auth)
"""
import os
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlparse

import pytest
from playwright.sync_api import Browser, Page

from api import CartApi, ProductApi, SearchApi
from pages import BasePage, CartPage, CatalogPage, CheckoutPage, LoginPage, ProductPage, RegisterPage, SearchPage

ROOT = Path(__file__).resolve().parents[2]
AUTH_FILE = ROOT / ".auth" / "customer.json"
SHOPIFY_SUFFIXES = (".shopify.com", ".myshopify.com", ".shopifycdn.com", ".shopifycloud.com", ".shopifysvc.com")
# Third-party hosts the THEME needs to work. The shop loads jQuery from Google's CDN; blocked, the
# product page never renders its "Sold Out" button (found 2026-11-25). Tracking hosts stay blocked.
THEME_DEPENDENCIES = ("ajax.googleapis.com",)


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


@pytest.fixture
def shop_api_in_browser(page: Page) -> SimpleNamespace:
    """API objects that share the browser's cookies: what shop_api_in_browser.cart adds, the cart page shows."""
    return SimpleNamespace(product=ProductApi(page.context.request), cart=CartApi(page.context.request),
                           search=SearchApi(page.context.request))


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
