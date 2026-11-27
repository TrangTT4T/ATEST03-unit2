"""Catalog page: /collections/all"""
from playwright.sync_api import Locator

from .base_page import BasePage


class CatalogPage(BasePage):
    path = "/collections/all"

    ############################################################################
    # Product tile methods
    # Scope: Catalog > All products
    ############################################################################
    def product_tile(self, path_name: str) -> Locator:
        """The tile of one product (its "path-name" in dataset/products.json): name, price and "Sold Out"."""
        return self.find_element(self._tile.format(path_name))

    # --- Locators -------------------------------------------------------------
    # Product tiles: each tile links to its product page. .format(path_name)
    _tile = "//a[contains(@href,'/products/{}')]"
