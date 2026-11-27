"""Product detail page: /products/<path-name>"""
from playwright.sync_api import Locator

from .base_page import BasePage


class ProductPage(BasePage):
    URL_TEMPLATE = "/products/{path_name}"  # path_name = "path-name" in dataset/products.json
    MAX_RETRY_AFTER_SECONDS = 30  # the longest "Retry-After" wait accepted from the store on HTTP 429

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
    def add_to_cart_button(self) -> Locator:
        """The Add to Cart button."""
        return self.find_element(self._add_to_cart_button)

    def add_to_cart(self, quantity: int = 1):
        """Add ``quantity`` items and wait until the store has answered every add."""
        if self.is_element_visible(self._quantity):
            self.type_text(self._quantity, str(quantity))
            self._click_add_to_cart_and_wait()
        else:  # theme without a visible quantity box: add the product N times
            for _ in range(quantity):
                self._click_add_to_cart_and_wait()

    def _click_add_to_cart_and_wait(self):
        """Add to Cart is AJAX: the theme posts /cart/add.js and stays on the page.

        Wait for the server's answer to THIS click (Day 6: network-aware waits). A navigation or
        load-state wait would hang or return at once - neither proves that the add finished.

        HTTP 429 means the store is rate-limiting this network (too many adds in a short time): wait
        as long as its "Retry-After" header asks (at most MAX_RETRY_AFTER_SECONDS) and click once more.
        A second 429 stops the test with a message saying so, not a bare status code.
        """
        answer = self.click_and_wait_for_response(self._add_to_cart_button, url_part="/cart/add")
        if answer.status == 429:
            retry_after = min(int(answer.headers.get("retry-after", "5") or 5), self.MAX_RETRY_AFTER_SECONDS)
            self.logger.warning("Add to cart: HTTP 429 (rate limit), waiting %s s as the store asks", retry_after)
            self.page.wait_for_timeout(retry_after * 1000)  # the store's own Retry-After, not a guessed sleep
            answer = self.click_and_wait_for_response(self._add_to_cart_button, url_part="/cart/add")
        if answer.status == 429:
            self.logger.error("Add to cart: HTTP 429 again, the store is still rate-limiting this network")
            raise AssertionError("add to cart failed: HTTP 429 - the store is rate-limiting this network (too many "
                                 "requests in a short time). Wait a few minutes, then run the suite again "
                                 "serially or one folder at a time (pytest tests/ui)")
        if not answer.ok:
            raise AssertionError(f"add to cart failed: HTTP {answer.status}")

    # --- Locators -------------------------------------------------------------
    # Product details. itemprop="name" (schema.org) is the name; the first <h1> is the shop logo.
    _title = "//*[@itemprop='name']"
    _price = "//*[@id='product-price']"
    _sold_out_button = "//input[@type='submit' and @value='Sold Out']"
    # Add to cart form (standard Shopify)
    _add_to_cart_button = "//form[contains(@action,'/cart/add')]//*[@type='submit']"
    _quantity = "//form[contains(@action,'/cart/add')]//input[@name='quantity']"
