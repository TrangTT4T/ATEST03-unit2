"""Search (risk R07, Medium). Requirement: @search_products (REQ-08)."""
import pytest
from playwright.sync_api import expect

pytestmark = [pytest.mark.medium, pytest.mark.regression, pytest.mark.search_products]


def test_search_returns_matching_products(shop, step):
    """Searching 'jacket' lists both jackets of the catalog."""
    # Test data
    keyword = "jacket"

    # Execution steps
    with step("Open the home page"):
        shop.home.open_page()
    with step(f"Search for '{keyword}'"):
        shop.home.search_for(keyword)
    with step("Verify Grey jacket and Noir jacket are in the results"):
        expect(shop.search.search_result_links.filter(has_text="Grey jacket").first).to_be_visible()
        expect(shop.search.search_result_links.filter(has_text="Noir jacket").first).to_be_visible()


@pytest.mark.negative
def test_search_with_no_matching_products(shop, step):
    """A keyword that matches nothing shows 'No results found' and no products."""
    # Test data
    keyword = "zzqqxx"  # Shopify also matches parts of words: "zzqxnotaproduct" finds products via "product"

    # Execution steps
    with step("Open the home page"):
        shop.home.open_page()
    with step(f"Search for '{keyword}'"):
        shop.home.search_for(keyword)
    with step("Verify 'No results found' is shown and no product is listed"):
        expect(shop.search.no_results_message).to_be_visible()
        expect(shop.search.search_result_links).to_have_count(0)
