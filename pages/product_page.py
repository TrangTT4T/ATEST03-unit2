"""Product page: /inventory-item.html?id=<id>"""
from playwright.sync_api import Locator

from .base_page import BasePage


class ProductPage(BasePage):
    path = "/inventory-item.html"

    ############################################################################
    # Product detail methods
    # Scope: Product page > Name, description, price
    ############################################################################
    def open_product_page(self, product_id: int):
        """Open the page of one product; ``product_id`` is its "id" in dataset/products.json."""
        self.open_page(f"{self.path}?id={product_id}")

    @property
    def product_name(self) -> Locator:
        """The product name."""
        return self.find_element(self._name)

    @property
    def product_description(self) -> Locator:
        """The product description."""
        return self.find_element(self._description)

    @property
    def product_price(self) -> Locator:
        """The product price, e.g. "$29.99"."""
        return self.find_element(self._price)

    ############################################################################
    # Cart button methods
    # Scope: Product page > Add to cart / Remove
    ############################################################################
    def add_to_cart(self):
        """Click "Add to cart" (the button then says "Remove")."""
        self.click_element(self._add_button)

    @property
    def cart_button(self) -> Locator:
        """The Add to cart / Remove button."""
        return self.find_element(self._cart_button)

    # --- Locators -------------------------------------------------------------
    # Product details
    _name = "//*[@data-test='inventory-item-name']"
    _description = "//*[@data-test='inventory-item-desc']"
    _price = "//*[@data-test='inventory-item-price']"
    # Buttons
    _cart_button = "//*[@data-test='inventory-item']//button"
    _add_button = "//*[@data-test='add-to-cart']"
