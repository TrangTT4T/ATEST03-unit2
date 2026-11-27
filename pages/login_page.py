"""Login page: /account/login (with the password-recovery form on the same page)"""
from playwright.sync_api import Locator

from .base_page import BasePage


class LoginPage(BasePage):
    path = "/account/login"

    ############################################################################
    # Login methods
    # Scope: Account > Login form
    ############################################################################
    def login(self, email: str, password: str):
        """Fill in email and password, click Sign In and wait for the next page."""
        self.type_text(self._email, email)
        self.type_text(self._password, password, secret=True)
        self.click_and_wait_for_new_page(self._sign_in_button)

    @property
    def error_message(self) -> Locator:
        """The form's error message (e.g. wrong password)."""
        return self.find_element(self._errors)

    ############################################################################
    # Password reset methods
    # Scope: Account > Login page > Forgot your password?
    ############################################################################
    def click_forgot_password(self):
        """Click "Forgot your password?" to show the password-reset form."""
        self.click_element(self._forgot_password_link)

    def request_password_reset(self, email: str):
        """Open "Forgot your password?", type ``email`` and submit; wait for the next page."""
        self.click_forgot_password()
        self.type_text(self._reset_email, email)
        self.click_and_wait_for_new_page(self._reset_submit_button)

    @property
    def password_reset_form(self) -> Locator:
        """The password-reset form."""
        return self.find_element(self._reset_form)

    # --- Locators -------------------------------------------------------------
    # Login form
    _email = "//form[contains(@action,'/account/login')]//input[@name='customer[email]']"
    _password = "//form[contains(@action,'/account/login')]//input[@name='customer[password]']"
    _sign_in_button = "//form[contains(@action,'/account/login')]//*[@type='submit']"
    _errors = "//*[contains(@class,'errors') or contains(@class,'form-error') or @role='alert']"
    # Password reset
    _forgot_password_link = "//a[normalize-space()='Forgot your password?']"
    _reset_form = "//form[contains(@action,'/account/recover')]"
    _reset_email = "//form[contains(@action,'/account/recover')]//input[@name='email']"
    _reset_submit_button = "//form[contains(@action,'/account/recover')]//*[@type='submit']"
