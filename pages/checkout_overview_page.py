"""Checkout step two: /checkout-step-two.html (items, item total, tax, total, Finish)"""
from playwright.sync_api import Locator

from .base_page import BasePage


class CheckoutOverviewPage(BasePage):
    path = "/checkout-step-two.html"

    ############################################################################
    # Order summary methods
    # Scope: Checkout: Overview > Items, Price Total
    ############################################################################
    def get_product_names(self) -> list[str]:
        """The names of the products in the order, in the order shown (waits for the list to be drawn)."""
        self.find_element(self._cart_list).wait_for(state="visible")
        return self.get_texts(self._item_names)

    @property
    def item_total(self) -> Locator:
        """The line "Item total: $..." (the sum of the prices, without tax)."""
        return self.find_element(self._item_total)

    @property
    def tax(self) -> Locator:
        """The line "Tax: $..."."""
        return self.find_element(self._tax)

    @property
    def total(self) -> Locator:
        """The line "Total: $..." (item total + tax)."""
        return self.find_element(self._total)

    def click_finish(self):
        """Click Finish and wait for the order-complete page."""
        self.click_element(self._finish_button)
        self.wait_until_url_contains("/checkout-complete.html")

    # --- Locators -------------------------------------------------------------
    # Items
    _cart_list = "//*[@data-test='cart-list']"
    _item_names = "//*[@data-test='cart-list']//*[@data-test='inventory-item-name']"
    # Price total
    _item_total = "//*[@data-test='subtotal-label']"
    _tax = "//*[@data-test='tax-label']"
    _total = "//*[@data-test='total-label']"
    _finish_button = "//*[@data-test='finish']"
