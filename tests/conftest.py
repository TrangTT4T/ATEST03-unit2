"""Shared fixtures and hooks for the whole suite (Unit 2): UI tests in tests/ui, API tests in tests/api.

Inherited from Unit 1: the requirements and risks (as markers), the test data
(dataset/products.json), one fresh state per test. New in Unit 2: plain Playwright tests on pytest -
fixtures instead of hooks, markers instead of Gherkin tags, network control, tracing, auth state,
API testing, xdist.

Fixture map (shared here; tests/ui/conftest.py and tests/api/conftest.py add their own):
  products           test data from dataset/products.json
  accounts           test accounts from .env (never committed; see .env.example)
  step               numbered test steps: Allure step + trace group (helper_utility/steps.py)
"""
import json
import os
import shutil
from pathlib import Path

import pytest
from dotenv import load_dotenv

from helper_utility.steps import Steps

ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "dataset"  # same file as the ATEST03-unit1 repo: dataset/products.json
load_dotenv(ROOT / ".env")  # account data and the real login live in .env, which git ignores
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
    with open(DATASET / "products.json", encoding="utf-8") as fh:
        return json.load(fh)["products"]


@pytest.fixture(scope="session")
def accounts() -> dict:
    """Test accounts by name, read from .env (git ignores it; .env.example lists the variables).

    No email or password is written in a file that goes to GitHub. A test that needs a value
    missing from .env is skipped and the message names the variables to set.
    """
    needed = ["TEST_PASSWORD", "WRONG_PASSWORD", "UNKNOWN_USER_EMAIL", "MALFORMED_EMAIL",
              "NEW_CUSTOMER_FIRST_NAME", "NEW_CUSTOMER_LAST_NAME", "NEW_CUSTOMER_EMAIL"]
    missing = [name for name in needed if not os.getenv(name)]
    if missing:
        pytest.skip(f"Set {', '.join(missing)} in .env (see .env.example) to run the account tests")
    env = os.environ
    return {
        "new-customer": {"first_name": env["NEW_CUSTOMER_FIRST_NAME"], "last_name": env["NEW_CUSTOMER_LAST_NAME"],
                         "email": env["NEW_CUSTOMER_EMAIL"], "password": env["TEST_PASSWORD"]},
        "customer-without-email": {"first_name": env["NEW_CUSTOMER_FIRST_NAME"], "last_name": env["NEW_CUSTOMER_LAST_NAME"],
                                   "email": "", "password": env["TEST_PASSWORD"]},
        "unknown-user": {"email": env["UNKNOWN_USER_EMAIL"], "password": env["WRONG_PASSWORD"]},
        "malformed-email": {"email": env["MALFORMED_EMAIL"], "password": env["WRONG_PASSWORD"]},
    }


# --- test steps ---------------------------------------------------------------
@pytest.fixture
def step(request) -> Steps:
    """``with step("Add 1 item to the cart"):`` - numbered for you: Step 1, Step 2, ..."""
    page = request.getfixturevalue("page") if "page" in request.fixturenames else None
    return Steps(page)
