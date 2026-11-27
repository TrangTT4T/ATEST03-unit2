"""Search API (Day 6: API testing): GET /search/suggest.json, without a browser.

The keywords come from dataset/search.json, the same file as the UI search tests.
Requirement: @search_products (REQ-08).
"""
import pytest

from helper_utility.helpers import Helper

pytestmark = [pytest.mark.api, pytest.mark.regression, pytest.mark.medium, pytest.mark.search_products]
SEARCH = Helper.read_test_data("search")


@pytest.mark.parametrize("case", SEARCH["matching"], ids=[case["id"] for case in SEARCH["matching"]])
def test_search_api_suggests_matching_products(shop_api, step, case):
    """A keyword suggests the products it names (dataset/search.json "matching")."""
    # Execution steps
    with step(f"GET /search/suggest.json?q={case['keyword']}"):
        titles = shop_api.search.search_product_titles(case["keyword"])
    with step(f"Verify {', '.join(case['expected'])} are suggested"):
        assert set(case["expected"]) <= set(titles), titles


@pytest.mark.negative
@pytest.mark.parametrize("case", SEARCH["no_match"], ids=[case["id"] for case in SEARCH["no_match"]])
def test_search_api_suggests_nothing_for_an_unknown_keyword(shop_api, step, case):
    """A keyword that matches nothing suggests no product (dataset/search.json "no_match")."""
    # Execution steps
    with step(f"GET /search/suggest.json?q={case['keyword']}"):
        titles = shop_api.search.search_product_titles(case["keyword"])
    with step("Verify no product is suggested"):
        assert titles == []
