"""PdfReceipt: the Swag Labs order receipt (the "Generate PDF order" download) read into fields.

The PDF's text comes out letter-spaced in places ("O R D E R  D E TA I L S", "T ax $ 3.20"), so the
labels are compared without spaces. A receipt reads:

    Swag Labs / Order Receipt / ORDER DETAILS / Order Date November 28, 2026 at 4:27 AM
    SHIP TO / Ann Lee / 12345
    ITEMS / DESCRIPTION PRICE / Sauce Labs Backpack $ 29.99 / ... / Item total $ 39.98 / Tax $ 3.20 / Total $ 43.18
    Thank you for your order! ...

Tests compare these fields with the order they placed, never the raw text.
"""
import re
from pathlib import Path

from pypdf import PdfReader


class PdfReceipt:
    AMOUNT_LINE = re.compile(r"^(?P<label>.+?)\s*\$\s*(?P<amount>[\d,]+\.\d{2})$")  # "Sauce Labs Backpack $ 29.99"
    TOTAL_LABELS = {"Itemtotal": "item_total", "Tax": "tax", "Total": "total"}  # labels without spaces

    def __init__(self, path: Path):
        self.path = Path(path)
        reader = PdfReader(self.path)
        self.page_count = len(reader.pages)
        self.text = "\n".join(page.extract_text() for page in reader.pages)
        self.lines = [line.strip() for line in self.text.splitlines() if line.strip()]
        self.order_date = ""
        self.ship_to: list[str] = []  # the name, then the postal code
        self.items: dict[str, str] = {}  # product name as the PDF writes it -> "$29.99"
        self.totals: dict[str, str] = {}  # item_total, tax, total -> "$39.98"
        self._read_fields()

    ############################################################################
    # Field methods
    # Scope: Order receipt > ship to, items, totals
    ############################################################################
    @property
    def customer_name(self) -> str:
        """The first line under SHIP TO, e.g. "Ann Lee"."""
        return self.ship_to[0] if self.ship_to else ""

    @property
    def postal_code(self) -> str:
        """The second line under SHIP TO, e.g. "12345"."""
        return self.ship_to[1] if len(self.ship_to) > 1 else ""

    @property
    def item_count(self) -> int:
        """How many product lines the receipt lists."""
        return len(self.items)

    def item_prices(self, product_names: list[str]) -> dict[str, str | None]:
        """The price the receipt shows for each of ``product_names`` (None: not listed).

        Names are matched without spaces: the PDF text can split a word ("T -Shirt" for "T-Shirt").
        """
        prices = {self._without_spaces(name): price for name, price in self.items.items()}
        return {name: prices.get(self._without_spaces(name)) for name in product_names}

    def contains(self, text: str) -> bool:
        """True when ``text`` is in the receipt, spaces ignored (the PDF letter-spaces some words)."""
        return self._without_spaces(text) in self._without_spaces(self.text)

    def _read_fields(self):
        section = ""
        for line in self.lines:
            label = self._without_spaces(line)
            if label.startswith("OrderDate"):
                self.order_date = re.sub(r"^O\s*r\s*d\s*e\s*r\s*D\s*a\s*t\s*e\s*", "", line)
            elif label in ("SHIPTO", "ITEMS"):
                section = label
            elif section == "SHIPTO":
                self.ship_to.append(line)
            elif section == "ITEMS" and (match := self.AMOUNT_LINE.match(line)):
                amount = "$" + match.group("amount")
                total_name = self.TOTAL_LABELS.get(self._without_spaces(match.group("label")))
                if total_name:
                    self.totals[total_name] = amount
                else:
                    self.items[match.group("label").strip()] = amount

    @staticmethod
    def _without_spaces(text: str) -> str:
        return re.sub(r"\s+", "", text)
