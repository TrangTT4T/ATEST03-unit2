"""Cart page: /cart"""
import re

from playwright.sync_api import Locator

from .base_page import BasePage, money_to_float

TOTAL = re.compile(r"(sub)?total[^£]{0,40}£\s?([\d,]+\.\d{2})", re.IGNORECASE)  # a text pattern, not a locator


class CartPage(BasePage):
    """Every locator is scoped to #cart: each page also contains a HIDDEN mini-cart drawer with the
    same rows and quantity boxes, which would otherwise be counted twice."""

    path = "/cart"

    ############################################################################
    # Cart line methods
    # Scope: Cart page > Cart table
    ############################################################################
    @property
    def root(self) -> Locator:
        """The cart form (#cart); every other locator of this page is inside it."""
        return self.find_element(self._root)

    @property
    def quantity_inputs(self) -> Locator:
        """The quantity box of every cart line."""
        return self.find_element(self._root, self._quantity_inputs)

    def total_quantity(self) -> int:
        """Sum of the quantity boxes: the number of items in the cart."""
        inputs = self.quantity_inputs
        return sum(int(inputs.nth(i).input_value() or 0) for i in range(inputs.count()))

    def line_input(self, product_name: str) -> Locator:
        """The quantity box of the line of ``product_name``."""
        product_link = self.find_element(self.locator(self._product_link, name=product_name))
        quantity_box = self.find_element(self._quantity_inputs)
        row = self.find_element(self._root, self._row).filter(has=product_link).filter(has=quantity_box).last
        return self.find_element(row, self._quantity_inputs, first=True)  # has=: relative to the row

    def set_quantity(self, product_name: str, quantity: int):
        """Type ``quantity`` in the line of ``product_name`` and click Update."""
        # Quantity 0 + Update removes the line (standard Shopify behaviour).
        self.logger.info("Set quantity of %s to %s", product_name, quantity)
        self.line_input(product_name).fill(str(quantity))
        self.click_and_wait_for_new_page(self._root, self._update_button)

    def remove(self, product_name: str):
        """Remove the line of ``product_name`` (quantity 0 + Update)."""
        self.set_quantity(product_name, 0)

    ############################################################################
    # Total and checkout methods
    # Scope: Cart page > Total, Check Out button
    ############################################################################
    def total(self) -> float:
        """The cart total in pounds, e.g. 55.0."""
        text = self.get_text(self._root)
        match = TOTAL.search(text)
        if match:
            return float(match.group(2).replace(",", ""))
        return money_to_float(re.findall(r"£\s?[\d,]+\.\d{2}", text)[-1])

    def checkout(self):
        """Click Check Out and wait for the checkout page."""
        self.click_and_wait_for_new_page(self._root, self._checkout_button)
        self.wait_for_url_contains("checkout")

    # --- Locators -------------------------------------------------------------
    _root = "css=#cart"
    # Inside #cart:
    _quantity_inputs = "css=input[name^='updates']"
    # A cart line: the row that holds both the product link and a quantity box.
    _row = "css=tr, li, div"
    _product_link = "role=link[name='{name}' s]"  # exact name
    _update_button = "name=update"
    _checkout_button = "name=checkout"
