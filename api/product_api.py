"""Product API: GET /products/<path-name>.js"""
from playwright.sync_api import APIResponse

from .base_api import BaseApi


class ProductApi(BaseApi):
    ############################################################################
    # Product methods
    # Scope: Product page > product JSON
    ############################################################################
    def request_product(self, path_name: str) -> APIResponse:
        """GET the product JSON of ``path_name`` (from dataset/products.json); 404 when it does not exist.

        :param path_name: the product's "path-name", e.g. "grey-jacket"
        :return: the response; ``.json()`` holds title, price (in pence), available, variants
        """
        return self.get(self._product.format(path_name))

    # --- Endpoints ------------------------------------------------------------
    _product = "/products/{}.js"  # .format(path_name)
