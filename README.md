# Swag Labs – Unit 2: Playwright End-to-End Automation

pytest + Playwright (pytest-playwright) · Application under test: https://www.saucedemo.com (Swag Labs)

Covers Day 5–8. Everything runs with the `pytest` command. The whole unit is documented in one file, with a section per day: `docs/Unit2_Playwright_vi.md` (Tiếng Việt) and `docs/Unit2_Playwright_en.md` (English).

Unit 2 is **plain Playwright**: tests are pytest functions that drive page objects, with no Gherkin layer. Unit 1 (behave + Selenium) is the BDD unit; combining BDD with Playwright is the job of the mock project (Unit 5). What Unit 2 takes over from Unit 1 is the working method — requirements and risks as markers, test data in files, page objects with locators at the bottom — not the tool.

**Why Swag Labs:** the first version of this unit tested the Shopify store of Unit 1. Its Cloudflare protection and rate limit ("Just a moment...", HTTP 429) stopped the browser tests on some networks, and a bot check is never bypassed. Swag Labs is a demo shop made for test automation: no bot protection, `data-test` attributes on its elements, demo accounts listed on its login page.

| From Unit 1 | In Unit 2 |
| --- | --- |
| Requirements and their risks | Every test carries one requirement marker (e.g. `@pytest.mark.add_to_cart`) and one risk-level marker, declared in `pytest.ini` |
| Gherkin tags `@critical` `@smoke` `@negative` | pytest markers with the same names (`--strict-markers`) |
| `dataset/*.json` | One JSON file per area, read with `Helper.read_test_data("<area>")`; parametrized tests run once per case |
| Page Object pattern, one class per file, plain XPath locators at the bottom, `Helper.by_locator`, custom BasePage methods | Same layout, locators and helper; BasePage methods on Playwright's auto-waiting |
| Hooks in `environment.py` | Fixtures in `tests/conftest.py` |
| Screenshot on failure | Trace + screenshot + video on failure |
| — | Saved auth state, parallel runs, flaky reruns |

| Requirement | Marker | Risk |
| --- | --- | --- |
| REQ-01 Add products to the cart | `add_to_cart` | Critical |
| REQ-02 Remove products from the cart | `update_cart` | Critical |
| REQ-03 Check out: information, overview totals, order complete | `checkout` | Critical |
| REQ-04 Correct product information | `product_details` | High |
| REQ-05 Log in and out securely | `secure_login` | High |
| REQ-06 Browse and sort the product list | `browse_catalog` | High (list), Medium (sorting) |

| Day | Topic | Section in the unit document | Code used |
| --- | --- | --- | --- |
| 5 | Architecture, contexts, locators, fixtures, assertions, isolation | Day 5 section | `pages/`, `tests/conftest.py`, `dataset/`, `tests/test_cart.py` … |
| 6 | Tracing, known defects (xfail), auth state, parallel, reporting | Day 6 section | `pytest.ini`, `tests/test_auth_state.py` |
| 7 | Lab: prioritised end-to-end workflows | Day 7 section | full suite |
| 8 | Revision + reliability, flaky control, stability | Day 8 section | repeated runs, `pytest-rerunfailures`, trace viewer |

```text
ATEST03-unit2/
├── pytest.ini                   # base_url, tracing, reports, markers (--strict-markers)
├── requirements.txt
├── .env.example                 # the demo account variables to copy into .env (git ignores .env: never pushed)
├── dataset/                     # test data, one JSON file per area: Helper.read_test_data("<area>")
│   ├── products.json            #   6 products: id, price, description
│   ├── login.json               #   rejected logins and their errors
│   ├── catalog.json             #   the 4 sort options
│   ├── cart.json                #   add / remove cases
│   └── checkout.json            #   overview totals, required fields and their errors
├── pages/                       # Page Objects: one class per file, locator strings at the bottom;
│                                #   BasePage = find_element(s), click/type/select, waits, header, side menu
├── tests/
│   ├── conftest.py              # products, accounts (.env + Faker), shop, logged_in_shop, fill_cart, saved login, step
│   ├── test_login.py            # @secure_login                     (High)
│   ├── test_catalog.py          # @browse_catalog, @product_details (High; sorting Medium)
│   ├── test_cart.py             # @add_to_cart, @update_cart        (Critical; + finding F1)
│   ├── test_checkout.py         # @checkout: totals, required fields, PDF receipt (Critical)
│   └── test_auth_state.py       # @secure_login: saved login + isolation check
├── helper_utility/helpers.py    # class Helper: by_locator(), read_test_data(), money_to_float(), Faker data
├── helper_utility/pdf_receipt.py  # class PdfReceipt: the downloaded order PDF read into fields (pypdf)
├── helper_utility/steps.py      # the `step` fixture: numbered steps -> Allure step + trace group
└── docs/Unit2_Playwright_vi.md, Unit2_Playwright_en.md
```

## Run

Requires **Python 3.12**: the version in `.python-version` (PyCharm, VS Code, pyenv and uv pick it up), the same in every ATEST03 repository.

```bash
pip install -r requirements.txt
playwright install chromium
cp .env.example .env                 # fill in the demo accounts shown on https://www.saucedemo.com
pytest                               # 46 tests: 45 pass, 1 xfail (finding F1)
pytest -m smoke                      # login, add to cart, complete an order
pytest -m critical                   # every Critical-risk test
pytest -m add_to_cart                # every test of one requirement
pytest tests/test_checkout.py        # one area
pytest -n auto                       # parallel
pytest --account problem-user        # the same suite as another demo account (see below)
pytest tests/test_cart.py --headed --slowmo 300
playwright show-trace test-results/<test>/trace.zip
```

Without `.env`, every test that needs an account is skipped and the end of the run names the variables to set.

## Page objects

Locators are plain XPath strings that describe the element — mostly Swag Labs' `data-test` attributes (`"//*[@data-test='checkout']"`, `"//*[@data-test='shopping-cart-badge']"`) — declared at the bottom of each page class under a comment naming the area of the page; a template uses `{}` and `.format()`. `Helper.by_locator()` (`helper_utility/helpers.py`, the same prefixes as Unit 1) turns them into Playwright selectors. Pages never touch `self.page`: they call the `BasePage` methods (`find_element`, `find_elements`, `get_texts`, `click_element`, `type_text`, `select_option` …), which log the action. Swag Labs is a single-page app, so a click that changes the page waits for the new address. No method returns the page for chaining. Details: Day 5 section 3 of the unit document.

## Log in once, reuse the cookie

The login form is used once per session (once per worker with `-n`): `saved_login_state` logs in and saves the cookies (`context.storage_state()`), and `logged_in_shop` puts that cookie into each test's own context and opens the products page directly. In a serial run the Login button is clicked 7 times (the saved login + the 6 tests about logging in) instead of once per test; 37 tests reuse the cookie. Swag Labs' session cookie lasts 10 minutes, so the saved state is renewed when it is older than 9 minutes. Only the cookie is copied, so every test still starts with an empty cart. Details: Day 6 section 3 of the unit document.

## How a test reads

Every test: a docstring, `# Test data`, then `# Execution steps` made only of `with step(step_number, "..."):` blocks: `step_number = 1` before the first step, `step_number += 1` before each next one (the `step` fixture stops the test if a number is skipped or repeated). Steps show up in the Allure report, in the Playwright trace and in the error message of a failure (`failed in Step 3: ...`). Page methods are grouped under `####` banners with `# Scope: <area of the page>`, each with a docstring; locators stay at the bottom.

```python
@pytest.mark.smoke
@pytest.mark.add_to_cart
def test_add_one_product_to_the_cart(logged_in_shop, products, step):
    """A customer adds one product: the badge shows 1, the button turns into Remove, the cart lists it."""
    # Test data
    backpack = "Sauce Labs Backpack"

    # Execution steps
    step_number = 1
    with step(step_number, f"Add {backpack} from the products page"):
        logged_in_shop.inventory.add_product_to_cart(backpack)
    step_number += 1
    with step(step_number, "Verify the cart badge shows 1 and the button says Remove"):
        expect(logged_in_shop.inventory.cart_badge).to_have_text("1")
        expect(logged_in_shop.inventory.cart_button(backpack)).to_have_text("Remove")
    step_number += 1
    with step(step_number, f"Open the cart and verify it holds {backpack} at {products[backpack]['price']}"):
        logged_in_shop.inventory.open_cart()
        assert logged_in_shop.cart.get_product_names() == [backpack]
        assert logged_in_shop.cart.get_product_price(backpack) == products[backpack]["price"]
```

## PDF receipt

The order-complete page has a **Generate PDF order** button. `test_order_pdf_matches_the_order` (one case per order of `dataset/checkout.json`) downloads the PDF (`BasePage.click_and_download`, Playwright's `expect_download`), reads it with `PdfReceipt` (`helper_utility/pdf_receipt.py`, pypdf) and compares it field by field with the order it placed: the file name, one page, the title, today's date, the customer's name and postal code, every product with its price from `products.json`, the item total, tax and total, the thank-you text. The PDF text is letter-spaced in places ("T ax", "T -Shirt"), so labels and names are compared without spaces.

## Test data

No test writes its own values: each area has a JSON file in `dataset/`, read with `Helper.read_test_data("<area>")`, and a parametrized test runs once per case: a new case is a new line in the file. The demo accounts live in `.env` (never pushed); everything else — an unknown username, a wrong password, the checkout customer — is made up by Faker for every test. Details: Day 5 section 4b of the unit document.

## Reports

Every run writes:

| Output | Path | For |
| --- | --- | --- |
| HTML report | `reports/report.html` | trainer, BA, PO |
| JUnit XML | `reports/junit.xml` | CI test tab |
| Allure results: numbered steps, docstring, markers as tags | `reports/allure-results/` (`allure serve reports/allure-results`, needs the Allure CLI) | trainer, BA, PO |
| Trace, screenshot, video of failed tests | `test-results/` | debugging |

`--strict-markers` rejects a marker typo such as `add_to_card`.

## Other demo accounts

Swag Labs has six demo accounts; four of them have defects on purpose, for practice. `pytest --account <name>` runs the logged-in tests as that account (default `standard-user`; its username goes in `.env`, see `.env.example`). The login tests always use `standard-user` and `locked-out-user`. Run on 2026-11-27 with `-n 4`:

| Account (`--account`) | Result | What the failures show |
| --- | --- | --- |
| `standard-user` (default) | 42 passed, 1 xfailed | — |
| `performance-glitch-user` | 42 passed, 1 xfailed, about 3.5× slower | the login takes several seconds; auto-waiting absorbs it, no test needs a longer timeout |
| `visual-user` | 8 failed | the products page shows wrong prices (e.g. Backpack $88.21 instead of $29.99), so price sorting is wrong too; cart and checkout totals stay right |
| `error-user` | 15 failed | sorting does nothing; only 3 of the 6 products can be added; Remove on the products page does nothing; the product page has no description; the last name field takes no text, yet the form goes on without it; Finish does not complete the order |
| `problem-user` | 19 failed | sorting does nothing; product names open the wrong product page (Fleece Jacket: "ITEM NOT FOUND"); only 3 products can be added, Remove on the products page does nothing; typing the last name overwrites the first name, so checkout never gets past the information form |

Every failure names its step ("failed in Step 2: Verify the cart badge shows 6"), so the run reads as a defect list of that account.

## Known defect

- **F1 — Reset App State leaves the buttons as "Remove":** after Reset App State the cart is empty, but the product's button still says "Remove". `test_reset_app_state_empties_the_cart_and_resets_the_buttons` states the expected behaviour and is marked `xfail(strict=True)`: it shows as a known defect, and when Swag Labs fixes it the run fails so the marker is removed.
- Never commit `.env` or `.auth/`.

## ATEST03 course repositories

One repository per unit:

| Unit | Days | Topic | Repository |
| --- | --- | --- | --- |
| 1 | 1–4 | BDD automation design and framework practices (behave + Selenium) | [ATEST03-unit1](https://github.com/TrangTT4T/ATEST03-unit1) |
| 2 | 5–8 | Playwright end-to-end automation (pytest + Playwright) | **ATEST03-unit2** (this repository) |
| 3 | 9–12 | Mobile (Appium) and asynchronous systems | [ATEST03-unit3](https://github.com/TrangTT4T/ATEST03-unit3) |
| 4 | 13–18 | Containers, AWS cloud execution, performance (JMeter), CI/CD | [ATEST03-unit4](https://github.com/TrangTT4T/ATEST03-unit4) |
| 5 | 19–22 | Mock project: Swag Labs, end to end, without AWS | [ATEST03-unit5-mock](https://github.com/TrangTT4T/ATEST03-unit5-mock) |
