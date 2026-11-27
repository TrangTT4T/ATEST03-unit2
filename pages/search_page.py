"""Search results page: /search?q=<keyword>"""
from playwright.sync_api import Locator

from .base_page import BasePage


class SearchPage(BasePage):
    ############################################################################
    # Search result methods
    # Scope: Search > Results page
    ############################################################################
    @property
    def search_result_links(self) -> Locator:
        """The links to the products found."""
        return self.find_elements(self._search_result_links)

    @property
    def no_results_message(self) -> Locator:
        """The "No results found for ..." message."""
        return self.find_element(self._no_results_message)

    # --- Locators -------------------------------------------------------------
    # Results: a link to each product found, and the message when nothing matched
    _search_result_links = "//a[contains(@href,'/products/')]"
    _no_results_message = "//*[contains(text(),'No results found for')]"
