"""Checkout page (Shopify checkout): reached from the cart; no payment is ever made."""
import re

from playwright.sync_api import Locator

from .base_page import BasePage


class CheckoutPage(BasePage):
    URL = re.compile(r"checkout")

    ############################################################################
    # Order summary methods
    # Scope: Checkout > Order summary
    ############################################################################
    def order_summary_line(self, product_name: str) -> Locator:
        """The order-summary line of ``product_name``."""
        return self.find_element(self._line_item.format(product_name))

    # --- Locators -------------------------------------------------------------
    # Order summary: the element whose own text names the product. .format(product_name)
    _line_item = "//*[text()[contains(normalize-space(),'{}')]]"
