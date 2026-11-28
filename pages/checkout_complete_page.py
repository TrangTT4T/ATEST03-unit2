"""Checkout complete: /checkout-complete.html ("Thank you for your order!")"""
from pathlib import Path

from playwright.sync_api import Locator

from .base_page import BasePage


class CheckoutCompletePage(BasePage):
    path = "/checkout-complete.html"

    ############################################################################
    # Confirmation methods
    # Scope: Checkout: Complete! > Confirmation, Generate PDF order
    ############################################################################
    @property
    def complete_header(self) -> Locator:
        """The confirmation heading, "Thank you for your order!"."""
        return self.find_element(self._complete_header)

    def download_pdf_order(self, folder: Path) -> Path:
        """Click "Generate PDF order" and save the receipt in ``folder``; returns the PDF's path."""
        return self.click_and_download(self._generate_pdf_button, folder)

    # --- Locators -------------------------------------------------------------
    # Confirmation
    _complete_header = "//*[@data-test='complete-header']"
    _generate_pdf_button = "//*[@data-test='generate-pdf-order']"
