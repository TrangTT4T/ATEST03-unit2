"""Catalog page: /collections/all"""
from playwright.sync_api import Locator

from .base_page import BasePage


class CatalogPage(BasePage):
    path = "/collections/all"

    ############################################################################
    # Product tile methods
    # Scope: Catalog > All products
    ############################################################################
    def tile(self, path_name: str) -> Locator:
        """The tile of one product (its "path-name" in dataset/products.json): name, price and "Sold Out"."""
        return self.find_element(self.locator(self._tile, path_name=path_name), first=True)

    # --- Locators -------------------------------------------------------------
    _tile = "css=a[href*='/products/{path_name}']"  # the tile links to the product page
