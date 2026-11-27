"""Cart API: /cart.js, /cart/add.js, /cart/change.js (the cart of this request context)."""
from playwright.sync_api import APIResponse

from .base_api import BaseApi
from .product_api import ProductApi


class CartApi(BaseApi):
    ############################################################################
    # Cart methods
    # Scope: Cart page > cart JSON, add, change
    ############################################################################
    def add_product_to_cart(self, path_name: str, quantity: int) -> APIResponse:
        """Add ``quantity`` of the product's first variant to the cart.

        :param path_name: the product's "path-name"
        :param quantity: how many to add
        :return: the /cart/add.js response (the added line on success)
        """
        variant_id = ProductApi(self.request).request_product(path_name).json()["variants"][0]["id"]
        return self.post(self._cart_add, {"id": variant_id, "quantity": quantity})

    def get_cart(self) -> dict:
        """The cart as JSON: item_count, total_price (in pence), items."""
        return self.get(self._cart).json()

    def change_cart_line_quantity(self, line: int, quantity: int) -> APIResponse:
        """Set the quantity of cart line ``line`` (1 = first line); 0 removes the line.

        :param line: line number in the cart, starting at 1
        :param quantity: the new quantity
        :return: the /cart/change.js response (the whole cart)
        """
        return self.post(self._cart_change, {"line": line, "quantity": quantity})

    # --- Endpoints ------------------------------------------------------------
    _cart = "/cart.js"
    _cart_add = "/cart/add.js"
    _cart_change = "/cart/change.js"
