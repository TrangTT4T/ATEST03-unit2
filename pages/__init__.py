"""Page objects: one class per file, its locators declared at the bottom of the class."""
from .base_page import BasePage
from .cart_page import CartPage
from .checkout_complete_page import CheckoutCompletePage
from .checkout_information_page import CheckoutInformationPage
from .checkout_overview_page import CheckoutOverviewPage
from .inventory_page import InventoryPage
from .login_page import LoginPage
from .product_page import ProductPage

__all__ = [
    "BasePage", "CartPage", "CheckoutCompletePage", "CheckoutInformationPage", "CheckoutOverviewPage",
    "InventoryPage", "LoginPage", "ProductPage",
]
