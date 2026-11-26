"""Catalog page: /collections/all"""
from playwright.sync_api import Locator

from .base_page import BasePage


class CatalogPage(BasePage):
    path = "/collections/all"

    ############################################################################
    # Product tile methods
    # Scope: Catalog > All products
    ############################################################################
    def tile(self, handle: str) -> Locator:
        """The tile of one product: a link to /products/<handle> with name, price and "Sold Out"."""
        return self.page.locator(self._tile.format(handle=handle)).first

    # --- Locators -------------------------------------------------------------
    _tile = "a[href*='/products/{handle}']"
