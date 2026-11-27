"""Search (risk R07, Medium). Requirement: @search_products (REQ-08).

The keywords come from dataset/search.json: matching ones (upper case, part of a word ...) and ones
that match nothing (a nonsense word, a <script> tag).
"""
import pytest
from playwright.sync_api import expect

from helper_utility.helpers import Helper

pytestmark = [pytest.mark.medium, pytest.mark.regression, pytest.mark.search_products]
SEARCH = Helper.read_test_data("search")


@pytest.mark.parametrize("case", SEARCH["matching"], ids=[case["id"] for case in SEARCH["matching"]])
def test_search_returns_matching_products(shop, step, case):
    """A keyword lists the products it names (dataset/search.json "matching")."""
    # Execution steps
    with step("Open the home page"):
        shop.home.open_page()
    with step(f"Search for {case['keyword']!r}"):
        shop.home.search_for(case["keyword"])
    with step(f"Verify the results include {', '.join(case['expected'])}"):
        for name in case["expected"]:
            expect(shop.search.search_result_links.filter(has_text=name).first).to_be_visible()


@pytest.mark.negative
@pytest.mark.parametrize("case", SEARCH["no_match"], ids=[case["id"] for case in SEARCH["no_match"]])
def test_search_with_no_matching_products(shop, step, case):
    """A keyword that matches nothing shows 'No results found' and no products (dataset/search.json "no_match")."""
    # Execution steps
    with step("Open the home page"):
        shop.home.open_page()
    with step(f"Search for {case['keyword']!r}"):
        shop.home.search_for(case["keyword"])
    with step("Verify 'No results found' is shown and no product is listed"):
        expect(shop.search.no_results_message).to_be_visible()
        expect(shop.search.search_result_links).to_have_count(0)
