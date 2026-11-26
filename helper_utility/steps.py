"""Numbered test steps: every action or check of a test is one ``with step("..."):`` block.

    with step("Open the product page of Grey jacket"):
        shop.product.open_product(grey_jacket["url"])

Each block becomes:

* an Allure step "Step 1: Open the product page of Grey jacket" - the Allure report shows the test
  as a numbered list, like the workplace pattern ``with allure.step(f"Step {step_index}: ...")``;
* a group in the Playwright trace - the Trace Viewer of a failed test lists its clicks and waits
  under the step name, so the failing step is found at a glance;
* a note on the error when the block fails ("failed in Step 2: ..."), so the HTML and JUnit
  reports name the step too.

Numbering is automatic: there is no ``step_index`` counter to keep in sync when a step is added.
"""
import contextlib
from collections.abc import Iterator

import allure
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page


class Steps:
    """The ``step`` fixture: call it with a title to open the next numbered step of one test."""

    def __init__(self, page: Page | None = None):
        self.page = page  # None: a test without the shared page (no trace to group)
        self.number = 0

    @contextlib.contextmanager
    def __call__(self, title: str) -> Iterator[None]:
        self.number += 1
        label = f"Step {self.number}: {title}"
        with allure.step(label):
            grouped = self._open_trace_group(label)
            try:
                yield
            except Exception as error:  # pytest.skip/xfail are BaseException: not a failed step
                error.add_note(f"failed in {label}")
                raise
            finally:
                if grouped:
                    self._close_trace_group()

    def _open_trace_group(self, label: str) -> bool:
        if self.page is None:
            return False
        try:
            self.page.context.tracing.group(label)  # a no-op when tracing is off
        except PlaywrightError:
            return False
        return True

    def _close_trace_group(self) -> None:
        with contextlib.suppress(PlaywrightError):  # the context is gone (crash): nothing to close
            self.page.context.tracing.group_end()
