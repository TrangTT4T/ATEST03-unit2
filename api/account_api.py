"""Account API: log in, log out, register and reset a password without a browser.

Shopify has no JSON API for customer accounts: the store's own forms POST to /account/login,
/account and /account/recover. AccountApi sends the same form fields as the login and registration
pages. The store's bot protection answers such a POST with a redirect to /challenge: AccountApi
reports it and stops, it never tries to get past it. So, like the UI forms, the login and
registration API tests are manual on the public store (pytest -m manual, in a test environment
without CAPTCHA).
"""
from playwright.sync_api import APIResponse

from helper_utility.store_blocked_error import StoreBlockedError

from .base_api import BaseApi


class AccountApi(BaseApi):
    BOT_CHECK_PATH = "/challenge"  # where the store's bot protection redirects a form POST

    ############################################################################
    # Session methods
    # Scope: Account > logged in or not, log out
    ############################################################################
    def is_logged_in(self) -> bool:
        """True when /account opens the account page; a guest is redirected to the login page."""
        return self.get(self._account, follow_redirects=False).status == 200

    def get_account_redirect(self) -> str:
        """Where /account sends this session: "" when it opens, e.g. ".../account/login?return_url=..." for a guest."""
        return self.get(self._account, follow_redirects=False).headers.get("location", "")

    def logout(self):
        """End the customer session: GET /account/logout (the header's Log Out link)."""
        self.get(self._logout)

    ############################################################################
    # Login methods
    # Scope: Account > Login form, password reset form
    ############################################################################
    def login(self, email: str, password: str) -> APIResponse:
        """POST the login form.

        Accepted: a redirect to /account. Rejected: HTTP 200, the login page again with its error.

        :raises StoreBlockedError: when the store answers with its bot check
        """
        return self._post_account_form(self._login, {"form_type": "customer_login", "utf8": "\u2713",
                                                      "customer[email]": email, "customer[password]": password})

    def request_password_reset(self, email: str) -> APIResponse:
        """POST the "Forgot your password?" form for ``email`` (the store then emails a reset link).

        :raises StoreBlockedError: when the store answers with its bot check
        """
        return self._post_account_form(self._recover, {"form_type": "recover_customer_password", "utf8": "\u2713",
                                                        "email": email})

    ############################################################################
    # Registration methods
    # Scope: Account > Create account form
    ############################################################################
    def register_account(self, first_name: str, last_name: str, email: str, password: str) -> APIResponse:
        """POST the create-account form. Accepted: the new customer is logged in (a redirect away from the form).

        :raises StoreBlockedError: when the store answers with its bot check
        """
        return self._post_account_form(self._register, {
            "form_type": "create_customer", "utf8": "\u2713", "customer[first_name]": first_name,
            "customer[last_name]": last_name, "customer[email]": email, "customer[password]": password,
        })

    def _post_account_form(self, endpoint: str, form: dict) -> APIResponse:
        """POST an account form; stop with a clear error when the store answers with its bot check."""
        response = self.post_form(endpoint, form)
        if self.BOT_CHECK_PATH in response.headers.get("location", ""):  # never bypassed: report it clearly
            self.logger.error("The store answered POST %s with its bot check", endpoint)
            raise StoreBlockedError(f"The store asked to verify a human (redirect to {self.BOT_CHECK_PATH}) "
                                    f"instead of answering POST {endpoint}")
        return response

    # --- Endpoints ------------------------------------------------------------
    _account = "/account"
    _login = "/account/login"
    _logout = "/account/logout"
    _recover = "/account/recover"
    _register = "/account"  # the create-account form posts to /account
