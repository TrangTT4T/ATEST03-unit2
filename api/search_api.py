"""Search API: GET /search/suggest.json"""
from .base_api import BaseApi


class SearchApi(BaseApi):
    ############################################################################
    # Search methods
    # Scope: Search > product suggestions
    ############################################################################
    def search_product_titles(self, keyword: str) -> list[str]:
        """Titles of the products the search suggests for ``keyword`` ([] when nothing matches)."""
        response = self.get(self._search_suggest, {"q": keyword, "resources[type]": "product"})
        return [product["title"] for product in response.json()["resources"]["results"]["products"]]

    # --- Endpoints ------------------------------------------------------------
    _search_suggest = "/search/suggest.json"
