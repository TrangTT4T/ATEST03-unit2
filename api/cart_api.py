"""Cart API: /cart.js, /cart/add.js, /cart/change.js (the cart of this request context), and the
add-to-cart traffic of the browser page (capture it, or make it fail)."""
import contextlib
from collections.abc import Iterator

from playwright.sync_api import APIResponse, Request

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

    ############################################################################
    # Add-to-cart traffic of the page
    # Scope: Product page > the POST /cart/add request the Add to Cart button sends (needs a page)
    ############################################################################
    @contextlib.contextmanager
    def capture_add_to_cart_request(self) -> Iterator:
        """Capture the POST /cart/add the page sends inside the ``with`` block; ``.value`` is the request.

        Usage: ``with shop_api_in_browser.cart.capture_add_to_cart_request() as captured:`` + a click.
        """
        with self.page.expect_request(lambda r: self._cart_add_path in r.url and r.method == "POST") as captured:
            yield captured
        self.logger.info("Captured POST %s", captured.value.url)

    @staticmethod
    def request_carries_product_id(request: Request) -> bool:
        """True when an add-to-cart request body names a product id (multipart FormData or url-encoded)."""
        body = request.post_data or ""
        return 'name="id"' in body or "id=" in body

    def answer_add_to_cart_with_error(self, status: int = 500):
        """Fault injection: every add-to-cart request of the page gets HTTP ``status`` instead of the store's answer."""
        self.logger.info("Answer %s with HTTP %s", self._cart_add_route, status)
        self.page.route(self._cart_add_route, lambda route: route.fulfill(status=status, body="Injected error"))

    def stop_answering_add_to_cart(self):
        """Undo answer_add_to_cart_with_error: add-to-cart requests reach the store again."""
        self.page.unroute(self._cart_add_route)

    # --- Endpoints ------------------------------------------------------------
    _cart = "/cart.js"
    _cart_add = "/cart/add.js"
    _cart_change = "/cart/change.js"
    # The page's add-to-cart request (/cart/add or /cart/add.js, depending on the theme)
    _cart_add_path = "/cart/add"
    _cart_add_route = "**/cart/add*"
