"""Login page: /account/login (with the password-recovery form on the same page)"""
from playwright.sync_api import Locator

from .base_page import BasePage


class LoginPage(BasePage):
    path = "/account/login"

    ############################################################################
    # Login methods
    # Scope: Account > Login form
    ############################################################################
    @property
    def form(self) -> Locator:
        """The login form."""
        return self.find_element(self._form, first=True)

    def login(self, email: str, password: str):
        """Fill in email and password, click Sign In and wait for the next page."""
        self.type_text(self._form, self._email, text=email)
        self.type_text(self._form, self._password, text=password, secret=True)
        self.click_and_wait_for_new_page(self._form, self._sign_in_button)

    @property
    def error(self) -> Locator:
        """The form's error message (e.g. wrong password)."""
        return self.find_element(self._errors, first=True)

    ############################################################################
    # Password reset methods
    # Scope: Account > Login page > Forgot your password?
    ############################################################################
    def open_password_reset(self):
        """Click "Forgot your password?" to show the password-reset form."""
        self.click_element(self._forgot_password_link)

    @property
    def reset_form(self) -> Locator:
        """The password-reset form."""
        return self.find_element(self._reset_form, first=True)

    # --- Locators -------------------------------------------------------------
    _form = "css=form[action*='/account/login']"
    # Inside the form:
    _email = "name=customer[email]"
    _password = "name=customer[password]"
    _sign_in_button = "css=[type='submit']"
    _errors = "css=.errors, .form-error, [role='alert']"
    _forgot_password_link = "link=Forgot your password?"
    _reset_form = "css=form[action*='/account/recover']"
