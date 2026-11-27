"""Helper: what the pages, API objects and tests share - locators, test data, prices, random data.

* Element finder: reads a locator string and gives Playwright the selector (the same idea as Unit 1).
  A locator is plain XPath with no prefix (the default, and what every page writes), or
  "prefix=criteria" / "prefix:criteria": "id=cart", "name=q", "css=#cart", "link=...", "partial link=...",
  "tag_name=h1", "class_name=errors", "xpath=//h1".
* Test data: one JSON file per area in dataset/ (products.json, cart.json, search.json).
* Prices: "£1,120.00" -> 1120.0 or -> 112000 pence (the store's API counts pence).
* Random data (Faker): a new customer, an unregistered login, a malformed email - generated at run
  time, so no account data is written in a file.

Kept outside tests/ so pytest never collects it.
"""
import json
import re
import uuid
from pathlib import Path

from faker import Faker

DATASET = Path(__file__).resolve().parents[1] / "dataset"


class Helper:
    MONEY_PATTERN = re.compile(r"£\s?([\d,]+\.\d{2})")  # a text pattern, not a locator
    _faker = Faker("en_GB")

    def __init__(self):
        # {raw}: the criteria as written; {quoted}: the criteria as an XPath string literal
        strategies = {
            "id": "id={raw}",
            "name": "xpath=//*[@name={quoted}]",
            "xpath": "xpath={raw}",
            "link": "xpath=//a[normalize-space()={quoted}]",
            "partial link": "xpath=//a[contains(normalize-space(),{quoted})]",
            "css": "css={raw}",
            "tag_name": "css={raw}",
            "class_name": "css=.{raw}",
            "default": "xpath={raw}",
        }
        self._strategies = strategies

    ############################################################################
    # Element finder
    # Scope: BasePage > locator string -> Playwright selector
    ############################################################################
    def by_locator(self, locator: str) -> str:
        """The Playwright selector for ``locator``.

        "//*[@id='cart']" -> "xpath=//*[@id='cart']";  "id=cart" or "id:cart" -> "id=cart"

        A locator starting with "/" or "(" is XPath (prefix "default"). Otherwise any word before
        the first "=" or ":" is the prefix, so a typo such as "nmae=q" fails here with a clear
        message instead of being sent to Playwright as XPath.

        :param locator: locator string, plain XPath or "prefix=criteria"
        :return: a selector for page.locator()
        :raises ValueError: when the locator is empty or its prefix is not supported
        """
        if not isinstance(locator, str) or not locator.strip():
            raise ValueError(f"A locator is a non-empty string, got {locator!r}")
        locator = locator.strip()
        prefix, criteria = "default", locator
        if not locator.startswith(("/", "(")):
            match = re.match(r"([A-Za-z_ ]+?)\s*[=:]\s*(.*)", locator, re.DOTALL)
            if match:
                prefix, criteria = match.group(1).strip().lower(), match.group(2)
        template = self._strategies.get(prefix)
        if template is None:
            raise ValueError(f"Element locator with prefix '{prefix}' is not supported: {locator!r}")
        quoted = f'"{criteria}"' if "'" in criteria else f"'{criteria}'"
        return template.format(raw=criteria, quoted=quoted)

    ############################################################################
    # Test data
    # Scope: dataset/ > one JSON file per area
    ############################################################################
    @staticmethod
    def read_test_data(area: str) -> dict:
        """The test data of one area: dataset/<area>.json, e.g. read_test_data("cart").

        :param area: the file name without ".json"
        :return: the file's JSON
        :raises FileNotFoundError: naming the file and the areas that exist
        """
        path = DATASET / f"{area}.json"
        if not path.exists():
            areas = sorted(p.stem for p in DATASET.glob("*.json"))
            raise FileNotFoundError(f"No test data file {path.name} in dataset/; the areas are: {areas}")
        return json.loads(path.read_text(encoding="utf-8"))

    ############################################################################
    # Prices
    # Scope: Every page and API > "£1,120.00" amounts
    ############################################################################
    @staticmethod
    def money_to_float(text: str) -> float:
        """'£1,120.00' -> 1120.0 (the first £ amount in ``text``).

        :raises ValueError: when ``text`` holds no £ amount
        """
        match = Helper.MONEY_PATTERN.search(text)
        if not match:
            raise ValueError(f"No £ amount found in: {text!r}")
        return float(match.group(1).replace(",", ""))

    @staticmethod
    def money_to_pence(text: str) -> int:
        """'£1,120.00' -> 112000: the unit the store's JSON API uses for prices and totals."""
        return round(Helper.money_to_float(text) * 100)

    ############################################################################
    # Random data (Faker)
    # Scope: Account tests > customers and logins made up at run time
    ############################################################################
    @staticmethod
    def random_customer() -> dict:
        """A new customer: first_name, last_name, a unique example.com email and a strong password."""
        first_name, last_name = Helper._faker.first_name(), Helper._faker.last_name()
        return {
            "first_name": first_name,
            "last_name": last_name,
            "email": f"{first_name}.{last_name}.{uuid.uuid4().hex[:8]}@example.com".lower(),
            "password": Helper._faker.password(length=14, special_chars=True, digits=True, upper_case=True),
        }

    @staticmethod
    def random_unregistered_login() -> dict:
        """An email and password no account has (a unique example.com address)."""
        customer = Helper.random_customer()
        return {"email": customer["email"], "password": customer["password"]}

    @staticmethod
    def random_malformed_email() -> str:
        """Text that is not an email address (no "@"), e.g. "vitae-2f1c"."""
        return f"{Helper._faker.word()}-{uuid.uuid4().hex[:4]}"
