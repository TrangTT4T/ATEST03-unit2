"""Network API: the browser page's traffic - block third-party hosts.

Used by the autouse fixture block_third_party of the UI tests (it needs a page); kept here, with the
other API objects, so that no test or fixture routes requests itself.
"""
from functools import partial
from urllib.parse import urlparse

from .base_api import BaseApi


class NetworkApi(BaseApi):
    ############################################################################
    # Third-party traffic methods
    # Scope: Browser > every request of the page
    ############################################################################
    def block_third_party_hosts(self, store_host: str) -> list[str]:
        """Abort every request to a host that is not the store, Shopify or a theme dependency.

        :param store_host: the store's host name, e.g. "sauce-demo.myshopify.com"
        :return: the list the blocked URLs are appended to, as the page sends them
        """
        blocked: list[str] = []
        self.page.context.route("**/*", partial(self._abort_or_continue, store_host=store_host, blocked=blocked))
        return blocked

    def _abort_or_continue(self, route, store_host: str, blocked: list[str]):
        """Route handler: let an allowed host through, abort (and record) any other."""
        if self.is_allowed_host(route.request.url, store_host):
            route.continue_()
        else:
            blocked.append(route.request.url)
            route.abort()

    def is_allowed_host(self, url: str, store_host: str) -> bool:
        """True for the store, Shopify, local and data URLs, the hosts the theme needs and the store's
        security check (blocking it would only turn the store's check into a "blocked network" page)."""
        if urlparse(url).scheme in ("data", "blob"):
            return True
        host = urlparse(url).hostname or ""
        allowed_hosts = (store_host, "localhost", "127.0.0.1", *self.THEME_DEPENDENCIES)
        return host in allowed_hosts or host.endswith(self.SHOPIFY_SUFFIXES)

    # --- Hosts ------------------------------------------------------------------
    SHOPIFY_SUFFIXES = (".shopify.com", ".myshopify.com", ".shopifycdn.com", ".shopifycloud.com", ".shopifysvc.com")
    # Third-party hosts the THEME needs to work. The shop loads jQuery from Google's CDN; blocked, the
    # product page never renders its "Sold Out" button (found 2026-11-25). Tracking hosts stay blocked.
    # The store's security check (Cloudflare) loads its script from challenges.cloudflare.com: it is let
    # through so the check works as in any browser - blocked, the page only says the network blocked it
    # (found 2026-11-27). The check itself is never solved or bypassed: BasePage stops the test on it.
    THEME_DEPENDENCIES = ("ajax.googleapis.com", "challenges.cloudflare.com")
