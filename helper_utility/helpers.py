"""Helper: reads a locator string and gives Playwright the selector to use (the same idea as Unit 1).

A locator is plain XPath with no prefix (the default, and what every page writes): "//*[@id='cart']",
"(//a)[1]"; or "prefix=criteria" / "prefix:criteria" for another strategy: "id=cart", "name=q",
"css=#cart", "link=Forgot your password?", "partial link=Forgot", "tag_name=h1", "class_name=errors",
"xpath=//h1". The prefixes are the Unit 1 ones, so a locator reads the same in both repositories.

Kept outside tests/ so pytest never collects it.
"""
import re


class Helper:
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
