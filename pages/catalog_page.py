"""Catalog page: /collections/all"""
from playwright.sync_api import Locator

from .base_page import BasePage


class CatalogPage(BasePage):
    path = "/collections/all"

    def tile(self, handle: str) -> Locator:
        # Each product tile is a link to /products/<handle> holding name, price and "Sold Out".
        return self.page.locator(self._tile.format(handle=handle)).first

    # --- Locators -------------------------------------------------------------
    _tile = "a[href*='/products/{handle}']"
