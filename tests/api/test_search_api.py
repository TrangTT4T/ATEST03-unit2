"""Search API (Day 6: API testing): GET /search/suggest.json, without a browser.

Requirement: @search_products (REQ-08).
"""
import pytest

pytestmark = [pytest.mark.api, pytest.mark.regression]


@pytest.mark.medium
@pytest.mark.search_products
def test_search_api_suggests_matching_products(shop_api, step):
    """Searching 'jacket' suggests both jackets."""
    # Test data
    keyword = "jacket"

    # Execution steps
    with step(f"GET /search/suggest.json?q={keyword}"):
        titles = shop_api.search.search_product_titles(keyword)
    with step("Verify Grey jacket and Noir jacket are suggested"):
        assert {"Grey jacket", "Noir jacket"} <= set(titles), titles


@pytest.mark.medium
@pytest.mark.negative
@pytest.mark.search_products
def test_search_api_suggests_nothing_for_an_unknown_keyword(shop_api, step):
    """A keyword that matches nothing suggests no product."""
    # Test data
    keyword = "zzqqxx"

    # Execution steps
    with step(f"GET /search/suggest.json?q={keyword}"):
        titles = shop_api.search.search_product_titles(keyword)
    with step("Verify no product is suggested"):
        assert titles == []
