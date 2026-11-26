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
        return self.page.locator(self._form).filter(has=self.page.locator(self._field.format(name="email"))).first

    def register(self, first: str, last: str, email: str, password: str):
        """Fill in the four fields, click Create and wait for the next page."""
        for field, value in (("first_name", first), ("last_name", last), ("email", email), ("password", password)):
            self.form.locator(self._field.format(name=field)).fill(value)
        self.submit(self.form.locator(self._create_button).first)

    @property
    def error(self) -> Locator:
        """The form's error message (e.g. email missing)."""
        return self.page.locator(self._errors).first

    # --- Locators -------------------------------------------------------------
    _form = "form[action*='/account']"
    # Inside the form:
    _field = "input[name='customer[{name}]']"
    _create_button = "[type='submit']"
    _errors = ".errors, .form-error, [role='alert']"
