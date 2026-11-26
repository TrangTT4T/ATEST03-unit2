"""Search (risk R07, Medium). Requirement: @search_products (REQ-08)."""
import pytest
from playwright.sync_api import expect

pytestmark = [pytest.mark.medium, pytest.mark.regression, pytest.mark.search_products]


def test_search_returns_matching_products(shop):
    shop.home.open()
    shop.home.search("jacket")
    expect(shop.search.result_links.filter(has_text="Grey jacket").first).to_be_visible()
    expect(shop.search.result_links.filter(has_text="Noir jacket").first).to_be_visible()


@pytest.mark.negative
def test_search_with_no_matching_products(shop):
    # Shopify search also matches parts of words: "zzqxnotaproduct" finds products via "product".
    shop.home.open()
    shop.home.search("zzqqxx")
    expect(shop.search.no_results_message).to_be_visible()
    expect(shop.search.result_links).to_have_count(0)
