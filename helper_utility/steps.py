"""Numbered test steps: every action or check of a test is one ``with step(step_number, "..."):`` block.

The test counts its own steps, like the workplace pattern ``with allure.step(f"Step {step_index}: ...")``:

    step_number = 1
    with step(step_number, "Add Sauce Labs Backpack from the products page"):
        logged_in_shop.inventory.add_product_to_cart("Sauce Labs Backpack")
    step_number += 1
    with step(step_number, "Verify the cart badge shows 1"):
        expect(logged_in_shop.inventory.cart_badge).to_have_text("1")

Each block becomes:

* an Allure step "Step 1: Add Sauce Labs Backpack from the products page" - the Allure report shows the test
  as a numbered list, like the workplace pattern ``with allure.step(f"Step {step_index}: ...")``;
* a group in the Playwright trace - the Trace Viewer of a failed test lists its clicks and waits
  under the step name, so the failing step is found at a glance;
* a note on the error when the block fails ("failed in Step 2: ..."), so the HTML and JUnit
  reports name the step too.

The fixture checks the counter: the steps of a test must be numbered 1, 2, 3 ... A forgotten
``step_number += 1`` (two steps called "Step 2") or a skipped number stops the test with a clear
error instead of giving a report with wrong numbers.
"""
import contextlib
from collections.abc import Iterator

import allure
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page


class Steps:
    """The ``step`` fixture: call it with the step number and a title to open that step of one test."""

    def __init__(self, page: Page | None = None):
        self.page = page  # None: a test without the shared page (no trace to group)
        self.number = 0  # the number of the last step opened

    @contextlib.contextmanager
    def __call__(self, number: int, title: str) -> Iterator[None]:
        """Open Step ``number``: an Allure step, a trace group, and a note on the error if it fails.

        :param number: the test's step counter: 1 for the first step, then step_number += 1
        :param title: what the step does or checks, e.g. "Verify the cart has 2 items"
        :raises ValueError: when ``number`` is not the next number (a step skipped or counted twice)
        """
        if number != self.number + 1:
            raise ValueError(f"Step {number} ({title!r}) follows Step {self.number}: number the steps 1, 2, 3 ... "
                             f"(step_number = 1 before the first step, step_number += 1 before each next one)")
        self.number = number
        label = f"Step {number}: {title}"
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
