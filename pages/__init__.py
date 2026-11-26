"""Page objects: one class per file, its locators declared at the bottom of the class."""
from .base_page import BasePage
from .cart_page import CartPage
from .catalog_page import CatalogPage
from .checkout_page import CheckoutPage
from .login_page import LoginPage
from .product_page import ProductPage
from .register_page import RegisterPage
from .search_page import SearchPage

__all__ = ["BasePage", "CatalogPage", "CheckoutPage", "ProductPage", "CartPage", "LoginPage", "RegisterPage", "SearchPage"]
