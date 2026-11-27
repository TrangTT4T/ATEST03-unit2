"""Product list and product pages (risks R03 and R05, High; sorting R07, Medium).

Requirements: @browse_catalog (REQ-06), @product_details (REQ-04).
The products come from dataset/products.json, the sort options from dataset/catalog.json.
"""
import pytest
from playwright.sync_api import expect

from helper_utility.helpers import Helper

pytestmark = [pytest.mark.regression]
PRODUCTS = Helper.read_test_data("products")["products"]
CATALOG = Helper.read_test_data("catalog")


@pytest.mark.high
@pytest.mark.browse_catalog
@pytest.mark.parametrize("name", sorted(PRODUCTS))
def test_products_page_shows_the_name_description_and_price(logged_in_shop, products, step, name):
    """Every product of dataset/products.json has a card with its name, description and price."""
    # Test data
    product = products[name]

    # Execution steps
    step_number = 1
    with step(step_number, f"Find the card of {name}"):
        card = logged_in_shop.inventory.product_card(name)
    step_number += 1
    with step(step_number, f"Verify the card shows the description and the price {product['price']}"):
        expect(card).to_contain_text(product["description"])
        expect(card).to_contain_text(product["price"])
        expect(logged_in_shop.inventory.cart_button(name)).to_have_text("Add to cart")


@pytest.mark.medium
@pytest.mark.browse_catalog
@pytest.mark.parametrize("case", CATALOG["sorting"], ids=[case["id"] for case in CATALOG["sorting"]])
def test_sort_products(logged_in_shop, products, step, case):
    """Each sort option orders the list by name or price (dataset/catalog.json)."""
    # Test data
    if case["by"] == "name":
        expected = sorted(products, reverse=case["descending"])
    else:
        expected = sorted((Helper.money_to_float(p["price"]) for p in products.values()), reverse=case["descending"])

    # Execution steps
    step_number = 1
    with step(step_number, f"Sort by {case['option']!r}"):
        logged_in_shop.inventory.sort_products(case["option"])
    step_number += 1
    with step(step_number, f"Verify the products are ordered by {case['by']}"):
        if case["by"] == "name":
            assert logged_in_shop.inventory.get_product_names() == expected
        else:  # two products share a price, so the prices are compared, not the names
            assert logged_in_shop.inventory.get_product_prices() == expected


@pytest.mark.high
@pytest.mark.product_details
@pytest.mark.parametrize("name", sorted(PRODUCTS))
def test_product_page_shows_the_same_name_description_and_price(logged_in_shop, products, step, name):
    """The product page shows the same name, description and price as dataset/products.json."""
    # Test data
    product = products[name]

    # Execution steps
    step_number = 1
    with step(step_number, f"Open the product page of {name} from the products page"):
        logged_in_shop.inventory.open_product_page(name)
    step_number += 1
    with step(step_number, f"Verify the name, the description and the price {product['price']}"):
        expect(logged_in_shop.product.product_name).to_have_text(name)
        expect(logged_in_shop.product.product_description).to_have_text(product["description"])
        expect(logged_in_shop.product.product_price).to_have_text(product["price"])
