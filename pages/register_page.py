"""Registration page: /account/register"""
from playwright.sync_api import Locator

from .base_page import BasePage


class RegisterPage(BasePage):
    path = "/account/register"

    ############################################################################
    # Registration methods
    # Scope: Account > Create account form
    ############################################################################
    @property
    def form(self) -> Locator:
        """The registration form (the one with an email field)."""
        email_field = self.find_element(self.locator(self._field, name="email"))
        return self.find_element(self._form).filter(has=email_field).first

    def register(self, first: str, last: str, email: str, password: str):
        """Fill in the four fields, click Create and wait for the next page."""
        for field, value in (("first_name", first), ("last_name", last), ("email", email)):
            self.type_text(self.form, self.locator(self._field, name=field), text=value)
        self.type_text(self.form, self.locator(self._field, name="password"), text=password, secret=True)
        self.click_and_wait_for_new_page(self.form, self._create_button)

    @property
    def error(self) -> Locator:
        """The form's error message (e.g. email missing)."""
        return self.find_element(self._errors, first=True)

    # --- Locators -------------------------------------------------------------
    _form = "css=form[action*='/account']"
    # Inside the form:
    _field = "name=customer[{name}]"
    _create_button = "css=[type='submit']"
    _errors = "css=.errors, .form-error, [role='alert']"
