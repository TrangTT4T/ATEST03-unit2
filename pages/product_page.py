"""Product detail page: /products/<path-name>"""
from playwright.sync_api import Locator

from .base_page import BasePage


class ProductPage(BasePage):
    URL_TEMPLATE = "/products/{path_name}"  # path_name = "path-name" in dataset/products.json

    ############################################################################
    # Product detail methods
    # Scope: Product page > Name, price, stock
    ############################################################################
    def open_product_page(self, path_name: str):
        """Open /products/<path_name>; ``path_name`` comes from dataset/products.json, e.g. "grey-jacket"."""
        self.open_page(self.URL_TEMPLATE.format(path_name=path_name))

    @property
    def product_name(self) -> Locator:
        """The product name."""
        return self.find_element(self._title)

    @property
    def product_price(self) -> Locator:
        """The product price."""
        return self.find_element(self._price)

    @property
    def sold_out_button(self) -> Locator:
        """The disabled "Sold Out" button shown instead of Add to Cart."""
        return self.find_element(self._sold_out_button)

    ############################################################################
    # Add to cart methods
    # Scope: Product page > Add to cart form
    ############################################################################
    @property
    def add_button(self) -> Locator:
        """The Add to Cart button."""
        return self.find_element(self._add_button)

    def add_to_cart(self, quantity: int = 1):
        """Add ``quantity`` items and wait until the store has answered every add."""
        if self.is_element_visible(self._quantity):
            self.type_text(self._quantity, str(quantity))
            self._click_add()
        else:  # theme without a visible quantity box: add the product N times
            for _ in range(quantity):
                self._click_add()

    def _click_add(self):
        """Add to Cart is AJAX: the theme posts /cart/add.js and stays on the page.

        Wait for the server's answer to THIS click (Day 6: network-aware waits). A navigation or
        load-state wait would hang or return at once - neither proves that the add finished.
        """
        answer = self.click_and_wait_for_response(self._add_button, url_part="/cart/add")
        if not answer.ok:
            raise AssertionError(f"add to cart failed: HTTP {answer.status}")

    # --- Locators -------------------------------------------------------------
    # Product details. itemprop="name" (schema.org) is the name; the first <h1> is the shop logo.
    _title = "//*[@itemprop='name']"
    _price = "//*[@id='product-price']"
    _sold_out_button = "//input[@type='submit' and @value='Sold Out']"
    # Add to cart form (standard Shopify)
    _add_button = "//form[contains(@action,'/cart/add')]//*[@type='submit']"
    _quantity = "//form[contains(@action,'/cart/add')]//input[@name='quantity']"
