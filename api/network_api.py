"""Network API: the browser page's traffic - block third-party hosts, probe a URL, throttle the network.

Used by the UI tests (it needs a page); kept here, with the other API objects, so that no test or
fixture routes or sends requests itself.
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
        """True for the store, Shopify, local and data URLs, and the hosts the theme needs."""
        if urlparse(url).scheme in ("data", "blob"):
            return True
        host = urlparse(url).hostname or ""
        allowed_hosts = (store_host, "localhost", "127.0.0.1", *self.THEME_DEPENDENCIES)
        return host in allowed_hosts or host.endswith(self.SHOPIFY_SUFFIXES)

    def can_page_reach(self, url: str) -> bool:
        """True when a fetch() made by the page to ``url`` gets an answer (False: blocked or unreachable)."""
        reached = self.page.evaluate("url => fetch(url).then(() => true, () => false)", url)
        self.logger.info("fetch %s from the page -> %s", url, "reached" if reached else "blocked")
        return reached

    ############################################################################
    # Network speed methods
    # Scope: Browser (Chromium only) > DevTools network emulation
    ############################################################################
    def throttle_network(self, latency_ms: int, download_bytes_per_second: int, upload_bytes_per_second: int):
        """Slow the page's network down through the Chromium DevTools protocol.

        :param latency_ms: added round-trip time
        :param download_bytes_per_second: download speed
        :param upload_bytes_per_second: upload speed
        """
        devtools = self.page.context.new_cdp_session(self.page)
        devtools.send("Network.enable")
        devtools.send("Network.emulateNetworkConditions", {
            "offline": False, "latency": latency_ms,
            "downloadThroughput": download_bytes_per_second, "uploadThroughput": upload_bytes_per_second,
        })
        self.logger.info("Throttle: %s ms, %s B/s down, %s B/s up",
                         latency_ms, download_bytes_per_second, upload_bytes_per_second)

    # --- Hosts ------------------------------------------------------------------
    SHOPIFY_SUFFIXES = (".shopify.com", ".myshopify.com", ".shopifycdn.com", ".shopifycloud.com", ".shopifysvc.com")
    # Third-party hosts the THEME needs to work. The shop loads jQuery from Google's CDN; blocked, the
    # product page never renders its "Sold Out" button (found 2026-11-25). Tracking hosts stay blocked.
    THEME_DEPENDENCIES = ("ajax.googleapis.com",)
