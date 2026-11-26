"""Catalog and product pages (risks R03 and R05, High).

Requirements: @browse_catalog (REQ-06), @product_details (REQ-04).
"""
import json
from pathlib import Path

import pytest
from playwright.sync_api import expect

pytestmark = [pytest.mark.high, pytest.mark.regression]
PRODUCTS = json.loads((Path(__file__).resolve().parents[1] / "dataset" / "products.json").read_text(encoding="utf-8"))[
    "products"
]


@pytest.mark.browse_catalog
@pytest.mark.parametrize("name", sorted(PRODUCTS))
def test_catalog_shows_correct_price_and_stock_status(shop, products, name):
    shop.catalog.open()
    tile = shop.catalog.tile(products[name]["handle"])
    expect(tile).to_contain_text(name)
    expect(tile).to_contain_text(products[name]["price"])
    if products[name]["status"] == "sold out":
        expect(tile).to_contain_text("Sold Out", ignore_case=True)
    else:
        expect(tile).not_to_contain_text("Sold Out", ignore_case=True)


@pytest.mark.product_details
def test_product_page_shows_the_catalog_name_and_price(shop, products):
    shop.product.open_product(products["Noir jacket"]["handle"])
    expect(shop.product.title).to_have_text("Noir jacket")
    expect(shop.product.price).to_contain_text("£60.00")


@pytest.mark.product_details
@pytest.mark.negative
def test_a_sold_out_product_cannot_be_added_to_the_cart(shop, products):
    shop.product.open_product(products["Brown Shades"]["handle"])
    expect(shop.product.sold_out_button).to_be_visible()
    expect(shop.product.sold_out_button).to_be_disabled()
