"""Visual comparison (Day 5: assertions beyond text), risk R05 (High). Requirement: @browse_catalog (REQ-06).

Playwright for Python has no screenshot assertion; helper_utility/visual_comparison.py compares two
screenshots with Pillow. The reference is the standard user's products page, taken in the same run,
browser and viewport: no baseline image is stored, so fonts and rendering never differ between
machines. The diff image (differing pixels in red) is saved and attached to Allure.
"""
import pytest

from helper_utility.visual_comparison import VisualComparison

pytestmark = [pytest.mark.high, pytest.mark.regression, pytest.mark.browse_catalog]
MAX_DIFFERING_PIXELS = 0.001  # 0.1 %: rendering noise stays far below it


@pytest.mark.parametrize("account_name", [
    "standard-user",  # the reference against itself: proves that the comparison is stable
    pytest.param("visual-user", marks=pytest.mark.xfail(
        strict=True, reason="Finding V1: visual_user's products page differs from the standard user's: the "
                            "Backpack shows a dog, wrong prices, shifted titles and button, the cart icon "
                            "moved onto the sort list (checked 2026-11-28)")),
])
def test_products_page_looks_like_the_standard_users(open_shop_as, tmp_path, step, account_name):
    """The products page of ``account_name`` looks like the standard user's, pixel by pixel."""
    # Test data
    comparison = VisualComparison(tmp_path)

    # Execution steps
    step_number = 1
    with step(step_number, "Screenshot the standard user's products page (the reference)"):
        expected = open_shop_as("standard-user").inventory.take_screenshot()
    step_number += 1
    with step(step_number, f"Screenshot the products page of {account_name}"):
        actual = open_shop_as(account_name).inventory.take_screenshot()
    step_number += 1
    with step(step_number, f"Verify at most {MAX_DIFFERING_PIXELS:.1%} of the pixels differ"):
        result = comparison.compare(f"products-page-{account_name}", actual, expected)
        assert result.ratio <= MAX_DIFFERING_PIXELS, result.message
