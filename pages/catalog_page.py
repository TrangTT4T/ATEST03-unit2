"""Catalog page: /collections/all"""
from playwright.sync_api import Locator

from .base_page import BasePage


class CatalogPage(BasePage):
    path = "/collections/all"

    ############################################################################
    # Product tile methods
    # Scope: Catalog > All products
    ############################################################################
    def tile(self, url: str) -> Locator:
        """The tile of one product (its ``url`` from dataset/products.json): name, price and "Sold Out"."""
        return self.find_element(self.locator(self._tile, url=url), first=True)

    # --- Locators -------------------------------------------------------------
    _tile = "css=a[href*='{url}']"  # the tile links to the product page
