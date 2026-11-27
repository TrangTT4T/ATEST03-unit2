"""Catalog and product pages (risks R03 and R05, High).

Requirements: @browse_catalog (REQ-06), @product_details (REQ-04).
"""
import pytest
from playwright.sync_api import expect

from helper_utility.helpers import Helper

pytestmark = [pytest.mark.high, pytest.mark.regression]
PRODUCTS = Helper.read_test_data("products")["products"]


@pytest.mark.browse_catalog
@pytest.mark.parametrize("name", sorted(PRODUCTS))
def test_catalog_shows_correct_price_and_stock_status(shop, products, step, name):
    """Every product of dataset/products.json is listed with its price and stock status."""
    # Test data
    product = products[name]
    sold_out = product["status"] == "sold out"

    # Execution steps
    step_number = 1
    with step(step_number, "Open the catalog"):
        shop.catalog.open_page()
    step_number += 1
    with step(step_number, f"Verify the tile of {name} shows its name and price {product['price']}"):
        tile = shop.catalog.product_tile(product["path-name"])
        expect(tile).to_contain_text(name)
        expect(tile).to_contain_text(product["price"])
    step_number += 1
    with step(step_number, f"Verify the tile {'shows' if sold_out else 'does not show'} 'Sold Out'"):
        if sold_out:
            expect(tile).to_contain_text("Sold Out", ignore_case=True)
        else:
            expect(tile).not_to_contain_text("Sold Out", ignore_case=True)


@pytest.mark.product_details
def test_product_page_shows_the_catalog_name_and_price(shop, products, step):
    """The product page shows the same name and price as the catalog."""
    # Test data
    noir_jacket = products["Noir jacket"]

    # Execution steps
    step_number = 1
    with step(step_number, "Open the product page of Noir jacket"):
        shop.product.open_product_page(noir_jacket["path-name"])
    step_number += 1
    with step(step_number, f"Verify the name is Noir jacket and the price {noir_jacket['price']}"):
        expect(shop.product.product_name).to_have_text("Noir jacket")
        expect(shop.product.product_price).to_contain_text(noir_jacket["price"])


@pytest.mark.product_details
@pytest.mark.negative
def test_a_sold_out_product_cannot_be_added_to_the_cart(shop, products, step):
    """A sold-out product shows a disabled 'Sold Out' button instead of Add to Cart."""
    # Test data
    brown_shades = products["Brown Shades"]

    # Execution steps
    step_number = 1
    with step(step_number, "Open the product page of Brown Shades (sold out)"):
        shop.product.open_product_page(brown_shades["path-name"])
    step_number += 1
    with step(step_number, "Verify the 'Sold Out' button is shown and disabled"):
        expect(shop.product.sold_out_button).to_be_visible()
        expect(shop.product.sold_out_button).to_be_disabled()
