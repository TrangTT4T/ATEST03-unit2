"""Fixtures for the API tests: no browser.

  shop_api           API objects on their own request context (one per test: its own cart):
                     shop_api.product, .cart, .search, .account - the same split as `shop` for pages
"""
from types import SimpleNamespace

import pytest
from playwright.sync_api import Playwright

from api import AccountApi, CartApi, ProductApi, SearchApi


@pytest.fixture
def shop_api(playwright: Playwright, base_url: str):
    """API objects on their own API request context: no browser, its own cart (one per test)."""
    request_context = playwright.request.new_context(base_url=base_url)
    yield SimpleNamespace(product=ProductApi(request_context), cart=CartApi(request_context),
                          search=SearchApi(request_context), account=AccountApi(request_context))
    request_context.dispose()
