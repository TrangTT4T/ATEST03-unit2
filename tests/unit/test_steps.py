"""The ``step`` helper (helper_utility/steps.py), with a fake page: no browser."""
import pytest
from playwright.sync_api import Error as PlaywrightError

from helper_utility.steps import Steps


class FakeTracing:
    def __init__(self, fail_on_group: bool = False):
        self.calls: list[str] = []
        self.fail_on_group = fail_on_group

    def group(self, name: str) -> None:
        if self.fail_on_group:
            raise PlaywrightError("context closed")
        self.calls.append(f"group {name}")

    def group_end(self) -> None:
        self.calls.append("end")


class FakePage:
    def __init__(self, tracing: FakeTracing):
        self.context = type("Context", (), {"tracing": tracing})()


def test_steps_are_numbered_and_grouped_in_the_trace() -> None:
    tracing = FakeTracing()
    step = Steps(FakePage(tracing))
    with step("Open the cart"):
        pass
    with step("Verify the total"):
        pass
    assert tracing.calls == ["group Step 1: Open the cart", "end", "group Step 2: Verify the total", "end"]


def test_a_failing_step_names_itself_and_closes_its_group() -> None:
    tracing = FakeTracing()
    step = Steps(FakePage(tracing))
    with step("Open the cart"):
        pass
    with pytest.raises(AssertionError) as failure, step("Verify the total"):
        raise AssertionError("total is 50.0")
    assert failure.value.__notes__ == ["failed in Step 2: Verify the total"]
    assert tracing.calls[-1] == "end"


def test_steps_work_without_a_page_or_a_trace() -> None:
    for step in (Steps(None), Steps(FakePage(FakeTracing(fail_on_group=True)))):
        with step("Check something"):
            pass
        assert step.number == 1


def test_skip_is_not_reported_as_a_failed_step() -> None:
    step = Steps(None)
    with pytest.raises(pytest.skip.Exception) as skipped, step("Needs an account"):
        pytest.skip("no account")
    assert not getattr(skipped.value, "__notes__", None)
