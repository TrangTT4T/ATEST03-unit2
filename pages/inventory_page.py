"""Products page: /inventory.html (the product list after login)"""
from playwright.sync_api import Locator

from .base_page import BasePage


class InventoryPage(BasePage):
    path = "/inventory.html"

    ############################################################################
    # Product list methods
    # Scope: Products page > Product cards
    ############################################################################
    def verify_products_page_is_open(self):
        """Fail with a clear message when the products page is not shown (e.g. an expired login cookie)."""
        if not self.is_element_visible(self._product_names, timeout=5):
            raise AssertionError(f"The products page is not open (now {self.page.url}): the login did not hold")

    def get_product_names(self) -> list[str]:
        """The names of the listed products, in the order shown."""
        return self.get_texts(self._product_names)

    def get_product_prices(self) -> list[float]:
        """The prices of the listed products, in the order shown, e.g. [29.99, 9.99, ...]."""
        return [self._helper.money_to_float(price) for price in self.get_texts(self._product_prices)]

    def product_card(self, product_name: str) -> Locator:
        """The card of one product: name, description, price and its Add to cart / Remove button."""
        return self.find_element(self._product_card.format(product_name))

    def open_product_page(self, product_name: str):
        """Click the product's name and wait for its product page."""
        self.click_element(self._product_name_link.format(product_name))
        self.wait_until_url_contains("/inventory-item.html")

    ############################################################################
    # Sort methods
    # Scope: Products page > Sort drop-down
    ############################################################################
    def sort_products(self, option: str):
        """Sort the list, e.g. sort_products("Price (low to high)")."""
        self.select_option(self._sort_list, option)

    ############################################################################
    # Cart button methods
    # Scope: Products page > Product cards > Add to cart / Remove
    ############################################################################
    def add_product_to_cart(self, product_name: str):
        """Click "Add to cart" on the product's card (the button then says "Remove")."""
        self.click_element(self._add_button.format(product_name))

    def add_products_to_cart(self, product_names: list[str]):
        """Add every product of ``product_names`` from its card."""
        for product_name in product_names:
            self.add_product_to_cart(product_name)

    def remove_product_from_cart(self, product_name: str):
        """Click "Remove" on the product's card (the button then says "Add to cart" again)."""
        self.click_element(self._remove_button.format(product_name))

    def cart_button(self, product_name: str) -> Locator:
        """The Add to cart / Remove button of one product."""
        return self.find_element(self._card_button.format(product_name))

    # --- Locators -------------------------------------------------------------
    # Product cards. .format(product_name): the card whose name is exactly product_name
    _product_names = "//*[@data-test='inventory-item-name']"
    _product_prices = "//*[@data-test='inventory-item-price']"
    _product_card = ("//*[@data-test='inventory-item']"
                     "[.//*[@data-test='inventory-item-name' and normalize-space()='{}']]")
    _product_name_link = "//*[@data-test='inventory-item-name' and normalize-space()='{}']"
    # Card buttons. .format(product_name)
    _card_button = _product_card + "//button"
    _add_button = _product_card + "//button[normalize-space()='Add to cart']"
    _remove_button = _product_card + "//button[normalize-space()='Remove']"
    # Sort
    _sort_list = "//*[@data-test='product-sort-container']"
