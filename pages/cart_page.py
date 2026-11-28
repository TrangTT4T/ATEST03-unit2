"""Cart page: /cart.html"""
from .base_page import BasePage


class CartPage(BasePage):
    path = "/cart.html"

    ############################################################################
    # Cart list methods
    # Scope: Cart page > Cart items
    ############################################################################
    def get_product_names(self) -> list[str]:
        """The names of the products in the cart, in the order shown ([] for an empty cart).

        Waits for the cart list first: the address changes to /cart.html a moment before the list is drawn.
        """
        self.find_element(self._cart_list).wait_for(state="visible")
        return self.get_texts(self._item_names)

    def get_product_price(self, product_name: str) -> str:
        """The price shown in the cart line of ``product_name``, e.g. "$29.99"."""
        return self.find_element(self._item_price.format(product_name)).inner_text().strip()

    def remove_product_from_cart(self, product_name: str):
        """Click "Remove" in the cart line of ``product_name``."""
        self.click_element(self._remove_button.format(product_name))

    ############################################################################
    # Navigation methods
    # Scope: Cart page > Continue Shopping, Checkout
    ############################################################################
    def continue_shopping(self):
        """Click "Continue Shopping" and wait for the products page."""
        self.click_element(self._continue_shopping_button)
        self.wait_until_url_contains("/inventory.html")

    def click_checkout(self):
        """Click "Checkout" and wait for the checkout information page."""
        self.click_element(self._checkout_button)
        self.wait_until_url_contains("/checkout-step-one.html")

    # --- Locators -------------------------------------------------------------
    # Cart items. .format(product_name): the line whose name is exactly product_name
    _cart_list = "//*[@data-test='cart-list']"
    _item_names = "//*[@data-test='cart-list']//*[@data-test='inventory-item-name']"
    _item_line = "//*[@data-test='cart-list']//*[@data-test='inventory-item'][.//*[normalize-space()='{}']]"
    _item_price = _item_line + "//*[@data-test='inventory-item-price']"
    _remove_button = _item_line + "//button[normalize-space()='Remove']"
    # Cart buttons
    _continue_shopping_button = "//*[@data-test='continue-shopping']"
    _checkout_button = "//*[@data-test='checkout']"
