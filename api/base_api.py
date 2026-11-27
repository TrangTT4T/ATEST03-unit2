"""Base API object: the request context and the logged GET/POST every API object uses.

The store's pages call a JSON API (the Shopify AJAX API). Each area has its own API object, the
same split as pages/: ProductApi, CartApi, SearchApi, plus NetworkApi for the browser's traffic.
Every call is logged with its status. Tests only call these methods and check the result; no test
sends, routes or reads a request itself.
"""
import logging

from playwright.sync_api import APIRequestContext, APIResponse, Page


class BaseApi:
    def __init__(self, request: APIRequestContext, page: Page | None = None):
        self.request = request  # its own API context, or page.context.request to share the browser's cart
        self.page = page  # the browser page whose traffic this object watches or changes (UI tests only)
        self.logger = logging.getLogger(type(self).__name__)

    ############################################################################
    # Request methods
    # Scope: Every API object > GET, POST
    ############################################################################
    def get(self, endpoint: str, params: dict | None = None, follow_redirects: bool = True) -> APIResponse:
        """GET ``endpoint`` and log the status.

        :param endpoint: path after the base URL, e.g. "/cart.js"
        :param params: query parameters
        :param follow_redirects: False: return the redirect itself (status 302 and its "location" header)
        :return: the response
        """
        response = self.request.get(endpoint, params=params, max_redirects=20 if follow_redirects else 0)
        self.logger.info("GET %s %s -> HTTP %s", endpoint, params or "", response.status)
        return response

    def post(self, endpoint: str, data: dict) -> APIResponse:
        """POST ``data`` as JSON to ``endpoint`` and log the status.

        :param endpoint: path after the base URL, e.g. "/cart/add.js"
        :param data: the JSON body
        :return: the response
        """
        response = self.request.post(endpoint, data=data)
        self.logger.info("POST %s %s -> HTTP %s", endpoint, data, response.status)
        return response

    def post_form(self, endpoint: str, form: dict) -> APIResponse:
        """POST ``form`` as an HTML form would (form-encoded) and log the status; redirects are not followed.

        The log shows *** for every field whose name contains "password".

        :param endpoint: path after the base URL, e.g. "/account/login"
        :param form: the form fields, e.g. {"customer[email]": "..."}
        :return: the response: a redirect keeps its status (302) and its "location" header
        """
        response = self.request.post(endpoint, form=form, max_redirects=0)
        logged_form = {name: "***" if "password" in name else value for name, value in form.items()}
        self.logger.info("POST %s %s -> HTTP %s %s", endpoint, logged_form, response.status,
                         response.headers.get("location", ""))
        return response
