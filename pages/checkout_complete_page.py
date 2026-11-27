"""Checkout complete: /checkout-complete.html ("Thank you for your order!")"""
from playwright.sync_api import Locator

from .base_page import BasePage


class CheckoutCompletePage(BasePage):
    path = "/checkout-complete.html"

    ############################################################################
    # Confirmation methods
    # Scope: Checkout: Complete! > Confirmation
    ############################################################################
    @property
    def complete_header(self) -> Locator:
        """The confirmation heading, "Thank you for your order!"."""
        return self.find_element(self._complete_header)

    # --- Locators -------------------------------------------------------------
    # Confirmation
    _complete_header = "//*[@data-test='complete-header']"
