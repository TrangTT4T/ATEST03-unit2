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
        return self.page.locator(self._form).first

    def login(self, email: str, password: str):
        """Fill in email and password, click Sign In and wait for the next page."""
        self.form.locator(self._email).fill(email)
        self.form.locator(self._password).fill(password)
        self.submit(self.form.locator(self._sign_in_button).first)

    @property
    def error(self) -> Locator:
        """The form's error message (e.g. wrong password)."""
        return self.page.locator(self._errors).first

    ############################################################################
    # Password reset methods
    # Scope: Account > Login page > Forgot your password?
    ############################################################################
    def open_password_reset(self):
        """Click "Forgot your password?" to show the password-reset form."""
        self.page.locator(self._forgot_password_link).click()

    @property
    def reset_form(self) -> Locator:
        """The password-reset form."""
        return self.page.locator(self._reset_form).first

    # --- Locators -------------------------------------------------------------
    _form = "form[action*='/account/login']"
    # Inside the form:
    _email = "input[name='customer[email]']"
    _password = "input[name='customer[password]']"
    _sign_in_button = "[type='submit']"
    _errors = ".errors, .form-error, [role='alert']"
    _forgot_password_link = "role=link[name='Forgot your password?']"
    _reset_form = "form[action*='/account/recover']"
