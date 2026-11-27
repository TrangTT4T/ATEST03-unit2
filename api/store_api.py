"""The store's JSON API (Shopify AJAX API): products, cart, search - no browser needed.

The same layout as the page objects: methods grouped under ``####`` banners, endpoints declared at
the bottom of the class, templates filled with ``.format()``. Every call is logged with its status.
"""
import logging

from playwright.sync_api import APIRequestContext, APIResponse


class StoreApi:
    def __init__(self, request: APIRequestContext):
        self.request = request  # a standalone API context, or page.context.request to share the browser's cart
        self.logger = logging.getLogger(type(self).__name__)

    ############################################################################
    # Product API
    # Scope: GET /products/<path-name>.js
    ############################################################################
    def request_product(self, path_name: str) -> APIResponse:
        """GET the product JSON of ``path_name`` (from dataset/products.json); 404 when it does not exist.

        :param path_name: the product's "path-name", e.g. "grey-jacket"
        :return: the response; ``.json()`` holds title, price (in pence), available, variants
        """
        response = self.request.get(self._product.format(path_name))
        self.logger.info("GET %s -> HTTP %s", self._product.format(path_name), response.status)
        return response

    ############################################################################
    # Cart API
    # Scope: /cart.js, /cart/add.js, /cart/change.js (the cart of this request context)
    ############################################################################
    def add_product_to_cart(self, path_name: str, quantity: int) -> APIResponse:
        """Add ``quantity`` of the product's first variant to the cart.

        :param path_name: the product's "path-name"
        :param quantity: how many to add
        :return: the /cart/add.js response (the added line on success)
        """
        variant_id = self.request_product(path_name).json()["variants"][0]["id"]
        response = self.request.post(self._cart_add, data={"id": variant_id, "quantity": quantity})
        self.logger.info("POST %s %s x%s -> HTTP %s", self._cart_add, path_name, quantity, response.status)
        return response

    def get_cart(self) -> dict:
        """The cart as JSON: item_count, total_price (in pence), items."""
        response = self.request.get(self._cart)
        self.logger.info("GET %s -> HTTP %s", self._cart, response.status)
        return response.json()

    def change_cart_line_quantity(self, line: int, quantity: int) -> APIResponse:
        """Set the quantity of cart line ``line`` (1 = first line); 0 removes the line.

        :param line: line number in the cart, starting at 1
        :param quantity: the new quantity
        :return: the /cart/change.js response (the whole cart)
        """
        response = self.request.post(self._cart_change, data={"line": line, "quantity": quantity})
        self.logger.info("POST %s line %s -> %s -> HTTP %s", self._cart_change, line, quantity, response.status)
        return response

    ############################################################################
    # Search API
    # Scope: GET /search/suggest.json
    ############################################################################
    def search_product_titles(self, keyword: str) -> list[str]:
        """Titles of the products the search suggests for ``keyword`` ([] when nothing matches)."""
        response = self.request.get(self._search_suggest, params={"q": keyword, "resources[type]": "product"})
        self.logger.info("GET %s q=%r -> HTTP %s", self._search_suggest, keyword, response.status)
        return [product["title"] for product in response.json()["resources"]["results"]["products"]]

    # --- Endpoints ------------------------------------------------------------
    _product = "/products/{}.js"  # .format(path_name)
    _cart = "/cart.js"
    _cart_add = "/cart/add.js"
    _cart_change = "/cart/change.js"
    _search_suggest = "/search/suggest.json"
