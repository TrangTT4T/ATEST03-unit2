"""Checkout step one: /checkout-step-one.html (first name, last name, postal code)"""
from playwright.sync_api import Locator

from .base_page import BasePage


class CheckoutInformationPage(BasePage):
    path = "/checkout-step-one.html"

    ############################################################################
    # Information form methods
    # Scope: Checkout: Your Information > form
    ############################################################################
    def fill_information(self, first_name: str, last_name: str, postal_code: str):
        """Type the three fields (an empty string leaves a field empty) and click Continue."""
        self.type_text(self._first_name, first_name)
        self.type_text(self._last_name, last_name)
        self.type_text(self._postal_code, postal_code)
        self.click_element(self._continue_button)

    def fill_information_and_continue(self, first_name: str, last_name: str, postal_code: str):
        """Fill the form and wait for the overview page: for tests that only need to get past it."""
        self.fill_information(first_name, last_name, postal_code)
        self.wait_until_url_contains("/checkout-step-two.html")

    @property
    def error_message(self) -> Locator:
        """The red error above the buttons, e.g. "Error: First Name is required"."""
        return self.find_element(self._error)

    # --- Locators -------------------------------------------------------------
    # Information form
    _first_name = "//*[@data-test='firstName']"
    _last_name = "//*[@data-test='lastName']"
    _postal_code = "//*[@data-test='postalCode']"
    _continue_button = "//*[@data-test='continue']"
    _error = "//*[@data-test='error']"
