"""Framework tests: no browser, no network."""
import pytest


@pytest.fixture(autouse=True)
def block_third_party():
    """Overrides the browser fixture of tests/conftest.py: these tests never open a page."""
    yield []
