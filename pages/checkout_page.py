"""Checkout page (Shopify checkout): reached from the cart; no payment is ever made."""
import re

from playwright.sync_api import Locator

from .base_page import BasePage


class CheckoutPage(BasePage):
    URL = re.compile(r"checkout")

    def line_item(self, product_name: str) -> Locator:
        return self.page.locator(self._line_item.format(name=product_name)).first

    # --- Locators -------------------------------------------------------------
    _line_item = "text={name}"
