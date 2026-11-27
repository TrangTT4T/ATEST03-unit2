"""API objects: one class per area, like pages/ (product page <-> ProductApi), plus NetworkApi
for the browser's traffic; endpoints at the bottom."""
from .base_api import BaseApi
from .cart_api import CartApi
from .network_api import NetworkApi
from .product_api import ProductApi
from .search_api import SearchApi

__all__ = ["BaseApi", "CartApi", "NetworkApi", "ProductApi", "SearchApi"]
