"""Product detail page: /products/<handle>"""
from playwright.sync_api import Locator

from .base_page import BasePage


class ProductPage(BasePage):
    ############################################################################
    # Product detail methods
    # Scope: Product page > Name, price, stock
    ############################################################################
    def open_product(self, handle: str):
        """Open /products/<handle> (the handle comes from dataset/products.json)."""
        return self.open(f"/products/{handle}")

    @property
    def title(self) -> Locator:
        """The product name."""
        return self.page.locator(self._title)

    @property
    def price(self) -> Locator:
        """The product price."""
        return self.page.locator(self._price)

    @property
    def sold_out_button(self) -> Locator:
        """The disabled "Sold Out" button shown instead of Add to Cart."""
        return self.page.locator(self._sold_out_button)

    ############################################################################
    # Add to cart methods
    # Scope: Product page > Add to cart form
    ############################################################################
    @property
    def add_form(self) -> Locator:
        """The add-to-cart form."""
        return self.page.locator(self._add_form).first

    @property
    def add_button(self) -> Locator:
        """The Add to Cart button."""
        return self.add_form.locator(self._add_button).first

    def add_to_cart(self, quantity: int = 1):
        """Add ``quantity`` items and wait until the store has answered every add."""
        qty = self.add_form.locator(self._quantity)
        if qty.count() and qty.first.is_visible():
            qty.first.fill(str(quantity))
            self._click_add()
        else:  # theme without a visible quantity box: add the product N times
            for _ in range(quantity):
                self._click_add()

    def _click_add(self):
        """Add to Cart is AJAX: the theme posts /cart/add.js and stays on the page.

        Wait for the server's answer to THIS click (Day 6: network-aware waits). A navigation or
        load-state wait would hang or return at once - neither proves that the add finished.
        """
        with self.page.expect_response(lambda r: "/cart/add" in r.url and r.request.method == "POST") as answer:
            self.add_button.click()
        if not answer.value.ok:
            raise AssertionError(f"add to cart failed: HTTP {answer.value.status}")

    # --- Locators -------------------------------------------------------------
    # itemprop="name" (schema.org markup) is the product name; the shop's first <h1> is its logo.
    _title = "[itemprop='name']"
    _price = "#product-price"
    _sold_out_button = "role=button[name='Sold Out']"
    _add_form = "form[action*='/cart/add']"  # standard Shopify form
    # Inside the add form:
    _add_button = "[type='submit']"
    _quantity = "input[name='quantity']"
