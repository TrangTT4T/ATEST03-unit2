"""Product detail page: /products/<handle>"""
import re

from playwright.sync_api import Locator

from .base_page import BasePage


class ProductPage(BasePage):
    def open_product(self, handle: str):
        return self.open(f"/products/{handle}")

    @property
    def title(self) -> Locator:
        return self.page.locator(self._title).first

    @property
    def add_form(self) -> Locator:
        return self.page.locator(self._add_form).first

    @property
    def add_button(self) -> Locator:
        return self.add_form.locator(self._add_button).first

    def can_add_to_cart(self) -> bool:
        if self.add_button.count() == 0 or self.add_button.is_disabled():
            return False
        label = (self.add_button.get_attribute("value") or self.add_button.inner_text() or "").lower()
        return "sold out" not in label and "unavailable" not in label

    def add_to_cart(self, quantity: int = 1):
        qty = self.add_form.locator(self._quantity)
        if qty.count():
            qty.fill(str(quantity))
            self._submit()
        else:  # theme without a quantity box: add the product N times
            url = self.page.url
            for i in range(quantity):
                if i:
                    self.page.goto(url)
                self._submit()

    def _submit(self):
        # Wait on the network call itself, not on a timer (Day 6: network-aware waits).
        with self.page.expect_response(lambda r: "/cart/add" in r.url):
            self.submit(self.add_button)
        self.page.wait_for_url(re.compile(r"/cart"))

    # --- Locators -------------------------------------------------------------
    _title = "role=heading[level=1]"
    _add_form = "form[action*='/cart/add']"  # standard Shopify form
    # Inside the add form:
    _add_button = "[type='submit']"
    _quantity = "input[name='quantity']"
