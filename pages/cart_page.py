"""Cart page: /cart"""
import re

from playwright.sync_api import Locator

from .base_page import BasePage, money_to_float

TOTAL = re.compile(r"(sub)?total[^£]{0,40}£\s?([\d,]+\.\d{2})", re.IGNORECASE)  # a text pattern, not a locator


class CartPage(BasePage):
    """Every locator is scoped to #cart: each page also contains a HIDDEN mini-cart drawer with the
    same rows and quantity boxes, which would otherwise be counted twice."""

    path = "/cart"

    @property
    def root(self) -> Locator:
        return self.page.locator(self._root)

    @property
    def quantity_inputs(self) -> Locator:
        return self.root.locator(self._quantity_inputs)

    def total_quantity(self) -> int:
        inputs = self.quantity_inputs
        return sum(int(inputs.nth(i).input_value() or 0) for i in range(inputs.count()))

    def line_input(self, product_name: str) -> Locator:
        row = (self.root.locator(self._row)
               .filter(has=self.page.locator(self._product_link.format(name=product_name)))
               .filter(has=self.page.locator(self._quantity_inputs)).last)  # has=: relative to the row
        return row.locator(self._quantity_inputs).first

    def set_quantity(self, product_name: str, quantity: int):
        # Quantity 0 + Update removes the line (standard Shopify behaviour).
        self.line_input(product_name).fill(str(quantity))
        self.submit(self.root.locator(self._update_button).first)

    def remove(self, product_name: str):
        self.set_quantity(product_name, 0)

    def total(self) -> float:
        text = self.root.inner_text()
        match = TOTAL.search(text)
        if match:
            return float(match.group(2).replace(",", ""))
        return money_to_float(re.findall(r"£\s?[\d,]+\.\d{2}", text)[-1])

    def checkout(self):
        self.submit(self.root.locator(self._checkout_button).first)
        self.page.wait_for_url(re.compile(r"checkout"))

    # --- Locators -------------------------------------------------------------
    _root = "#cart"
    # Inside #cart:
    _quantity_inputs = "input[name^='updates']"
    # A cart line: the row that holds both the product link and a quantity box.
    _row = "tr, li, div"
    _product_link = "role=link[name='{name}' s]"  # exact name
    _update_button = "[name='update']"
    _checkout_button = "[name='checkout']"
