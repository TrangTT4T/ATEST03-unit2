"""Login page: / (the root of the shop)"""
from playwright.sync_api import Locator

from .base_page import BasePage


class LoginPage(BasePage):
    path = "/"

    ############################################################################
    # Login methods
    # Scope: Login page > Login form
    ############################################################################
    def login(self, username: str, password: str):
        """Fill in username and password and click Login (the password is logged as ***)."""
        self.type_text(self._username, username)
        self.type_text(self._password, password, secret=True)
        self.click_element(self._login_button)

    def login_and_wait_for_products(self, username: str, password: str):
        """Log in and wait for the products page: for tests that only need to be logged in."""
        self.login(username, password)
        self.wait_until_url_contains("/inventory.html")

    @property
    def login_button(self) -> Locator:
        """The Login button: visible only on the login page."""
        return self.find_element(self._login_button)

    @property
    def error_message(self) -> Locator:
        """The red error under the form, e.g. "Epic sadface: Username is required"."""
        return self.find_element(self._error)

    # --- Locators -------------------------------------------------------------
    # Login form
    _username = "//*[@data-test='username']"
    _password = "//*[@data-test='password']"
    _login_button = "//*[@data-test='login-button']"
    _error = "//*[@data-test='error']"
