"""Shared fixtures and hooks for the whole suite (Unit 2): UI tests in tests/ui, API tests in tests/api.

Inherited from Unit 1: the requirements and risks (as markers), the test data
(dataset/products.json), one fresh state per test. New in Unit 2: plain Playwright tests on pytest -
fixtures instead of hooks, markers instead of Gherkin tags, network control, tracing, auth state,
API testing, xdist.

Fixture map (shared here; tests/ui/conftest.py and tests/api/conftest.py add their own):
  products           test data from dataset/products.json (cart.json, search.json are read by the tests)
  accounts           made-up accounts (Faker), new for every test
  real_account       the real customer login from .env (only for -m auth; skips when it is not set)
  step               numbered test steps: Allure step + trace group (helper_utility/steps.py)
"""
import os
import shutil
from pathlib import Path

import pytest
from dotenv import load_dotenv

from helper_utility.helpers import Helper
from helper_utility.steps import Steps

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")  # the real customer login (for -m auth) lives in .env, which git ignores
ALLURE_RESULTS = ROOT / "reports" / "allure-results"


# --- reports ------------------------------------------------------------------
def pytest_configure(config):
    """Start every run with an empty Allure folder, so the report shows this run only.

    Done here on the controller, not with --clean-alluredir: under pytest -n every xdist worker
    would clean the folder, and a late worker could delete what an early one already wrote.
    """
    if not hasattr(config, "workerinput"):
        shutil.rmtree(ALLURE_RESULTS, ignore_errors=True)


# --- data ---------------------------------------------------------------------
@pytest.fixture(scope="session")
def products() -> dict:
    """Every product by name, from dataset/products.json (path-name, price, status, type, vendor, options)."""
    return Helper.read_test_data("products")["products"]


@pytest.fixture
def accounts() -> dict:
    """Made-up accounts for the login and registration tests, new for every test (Faker).

    Nothing is written in a file: the names, emails and passwords are generated at run time. Only a
    REAL customer login (for -m auth) comes from .env (SAUCE_EMAIL / SAUCE_PASSWORD).
    """
    customer = Helper.random_customer()
    return {
        "new-customer": customer,
        "customer-without-email": {**customer, "email": ""},
        "unknown-user": Helper.random_unregistered_login(),
        "malformed-email": {"email": Helper.random_malformed_email(), "password": customer["password"]},
    }


@pytest.fixture(scope="session")
def real_account() -> dict:
    """The real customer login (email, password) from .env: SAUCE_EMAIL / SAUCE_PASSWORD, for -m auth.

    Skips the test when they are not set. The password is never logged (type_text(secret=True)).
    """
    email, password = os.getenv("SAUCE_EMAIL"), os.getenv("SAUCE_PASSWORD")
    if not (email and password):
        pytest.skip("Set SAUCE_EMAIL and SAUCE_PASSWORD in .env to run the @auth tests")
    return {"email": email, "password": password}


# --- test steps ---------------------------------------------------------------
@pytest.fixture
def step(request) -> Steps:
    """``with step("Add 1 item to the cart"):`` - numbered for you: Step 1, Step 2, ..."""
    page = request.getfixturevalue("page") if "page" in request.fixturenames else None
    return Steps(page)
