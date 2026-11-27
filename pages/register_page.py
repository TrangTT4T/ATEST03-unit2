"""Registration page: /account/register"""
from playwright.sync_api import Locator

from .base_page import BasePage


class RegisterPage(BasePage):
    path = "/account/register"

    ############################################################################
    # Registration methods
    # Scope: Account > Create account form
    ############################################################################
    def register(self, first: str, last: str, email: str, password: str):
        """Fill in the four fields, click Create and wait for the next page."""
        for field, value in (("first_name", first), ("last_name", last), ("email", email)):
            self.type_text(self._field.format(field), value)
        self.type_text(self._field.format("password"), password, secret=True)
        self.click_and_wait_for_new_page(self._create_button)

    @property
    def error_message(self) -> Locator:
        """The form's error message (e.g. email missing)."""
        return self.find_element(self._errors)

    # --- Locators -------------------------------------------------------------
    # Create account form: the account form that has an email field. _field.format("email")
    _field = "//form[contains(@action,'/account') and .//input[@name='customer[email]']]//input[@name='customer[{}]']"
    _create_button = "//form[contains(@action,'/account') and .//input[@name='customer[email]']]//*[@type='submit']"
    _errors = "//*[contains(@class,'errors') or contains(@class,'form-error') or @role='alert']"
