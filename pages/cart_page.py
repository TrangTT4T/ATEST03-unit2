"""Cart page: /cart"""
import re

from playwright.sync_api import Locator

from .base_page import BasePage


class CartPage(BasePage):
    """Every locator is scoped to #cart: each page also contains a HIDDEN mini-cart drawer with the
    same rows and quantity boxes, which would otherwise be counted twice."""

    path = "/cart"
    TOTAL_PATTERN = re.compile(r"(sub)?total[^£]{0,40}£\s?([\d,]+\.\d{2})", re.IGNORECASE)  # text, not a locator

    ############################################################################
    # Cart line methods
    # Scope: Cart page > Cart table
    ############################################################################
    @property
    def quantity_boxes(self) -> Locator:
        """The quantity box of every cart line."""
        return self.find_elements(self._quantity_boxes)

    def count_items_in_cart(self) -> int:
        """Sum of the quantity boxes: the number of items in the cart."""
        boxes = self.quantity_boxes
        return sum(int(boxes.nth(i).input_value() or 0) for i in range(boxes.count()))

    def change_product_quantity(self, product_name: str, quantity: int):
        """Type ``quantity`` in the line of ``product_name`` and click Update.

        Quantity 0 + Update removes the line (standard Shopify behaviour).
        """
        self.type_text(self._line_quantity.format(product_name), str(quantity))
        self.click_and_wait_for_new_page(self._update_button)

    def remove_product_from_cart(self, product_name: str):
        """Remove the line of ``product_name`` (quantity 0 + Update)."""
        self.change_product_quantity(product_name, 0)

    ############################################################################
    # Total and checkout methods
    # Scope: Cart page > Total, Check Out button
    ############################################################################
    def get_cart_total(self) -> float:
        """The cart total in pounds, e.g. 55.0."""
        text = self.find_element(self._cart_form).inner_text()
        match = self.TOTAL_PATTERN.search(text)
        if match:
            return float(match.group(2).replace(",", ""))
        return self.money_to_float(re.findall(r"£\s?[\d,]+\.\d{2}", text)[-1])

    def click_checkout(self):
        """Click Check Out and wait for the checkout page."""
        self.click_and_wait_for_new_page(self._checkout_button)
        self.wait_until_url_contains("checkout")

    # --- Locators -------------------------------------------------------------
    # Cart table (inside #cart; the hidden mini-cart drawer repeats every row)
    _cart_form = "//*[@id='cart']"
    _quantity_boxes = "//*[@id='cart']//input[starts-with(@name,'updates')]"
    _line_quantity = (  # the quantity box in the row of one product: .format(product_name)
        "//*[@id='cart']//div[contains(@class,'row')][.//a[contains(normalize-space(),'{}')]]"
        "//input[starts-with(@name,'updates')]"
    )
    # Cart buttons
    _update_button = "//*[@id='update']"
    _checkout_button = "//*[@id='checkout']"
