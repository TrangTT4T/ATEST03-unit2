# Sauce Demo – Unit 2: Playwright End-to-End Automation

pytest + Playwright (pytest-playwright) · Application under test: https://sauce-demo.myshopify.com

Covers Day 5–8. Everything runs with the `pytest` command. The whole unit is documented in one file, with a section per day: `docs/Unit2_Playwright_vi.md` (Tiếng Việt) and `docs/Unit2_Playwright_en.md` (English).

Unit 2 is **plain Playwright**: tests are pytest functions that drive page objects, with no Gherkin layer. Unit 1 (behave + Selenium) is the BDD unit; combining BDD with Playwright is the job of the mock project (Unit 5). What Unit 2 takes over from Unit 1 is the *what* — requirements, risks and test data — not the *how*.

| From Unit 1 | In Unit 2 |
| --- | --- |
| Requirements REQ-01 … REQ-08 and their risks | Every test carries one requirement marker, e.g. `@pytest.mark.add_to_cart` (declared in `pytest.ini`) |
| Gherkin tags `@critical` `@smoke` `@negative` | pytest markers with the same names, declared in `pytest.ini` (`--strict-markers`) |
| `dataset/products.json` | Same file: each product's `path-name` is the last part of its page address (`/products/<path-name>`), never derived from the name (Black heels is `flower-print-jeans`) |
| Page Object pattern, one class per file, locator strings (`css=`, `xpath=`, `name=` …) at the bottom, custom BasePage methods | Same layout and locator syntax; BasePage methods on Playwright's auto-waiting |
| Hooks in `environment.py` | Fixtures in `tests/conftest.py` |
| Screenshot on failure | Trace + screenshot + video on failure |
| — | Network interception, fault injection, throttling, saved auth state, parallel runs, flaky reruns |

| Day | Topic | Section in the unit document | Code used |
| --- | --- | --- | --- |
| 5 | Architecture, contexts, locators, fixtures, assertions, isolation | Day 5 section | `pages/`, `tests/conftest.py`, `tests/test_cart.py` … |
| 6 | Tracing, network interception, auth state, parallel, reporting | Day 6 section | `pytest.ini`, `tests/test_network.py`, `tests/test_auth_state.py` |
| 7 | Lab: prioritised end-to-end workflows | Day 7 section | full suite |
| 8 | Revision + reliability, flaky control, stability | Day 8 section | repeated runs, `pytest-rerunfailures`, trace viewer |

```text
ATEST03-unit2/
├── pytest.ini                   # base_url, tracing, reports, markers (--strict-markers)
├── requirements.txt
├── dataset/
│   └── products.json            # Unit 1 test data
├── pages/                       # Page Objects: one class per file, locator strings at the bottom;
│                                #   BasePage = parse_locator(), money_to_float() + click/type/wait/check methods
├── tests/
│   ├── conftest.py              # fixtures, network control, auth state
│   ├── test_cart.py             # @add_to_cart, @update_cart        (Critical)
│   ├── test_checkout.py         # @start_checkout                   (Critical)
│   ├── test_catalog.py          # @browse_catalog, @product_details (High)
│   ├── test_login.py            # @secure_login                     (High)
│   ├── test_register.py         # @create_account                   (Medium)
│   ├── test_search.py           # @search_products                  (Medium)
│   ├── test_network.py          # interception, fault injection, throttling
│   ├── test_auth_state.py       # saved login (needs a real account)
│   └── unit/                    # framework rules (no browser): page-object and test layout, step helper
├── helper_utility/steps.py      # the `step` fixture: numbered steps -> Allure step + trace group
└── docs/Unit2_Playwright_vi.md, Unit2_Playwright_en.md
```

## Run

Requires **Python 3.12**: the version in `.python-version` (PyCharm, VS Code, pyenv and uv pick it up), the same in every ATEST03 repository.

```bash
pip install -r requirements.txt
playwright install chromium
pytest                               # 22 browser tests + 61 framework tests; manual/data_creating/auth excluded
pytest -m smoke
pytest -m critical                   # every Critical-risk test
pytest -m add_to_cart                # every test of one requirement
pytest -n auto                       # parallel
pytest -m auth                       # needs SAUCE_EMAIL / SAUCE_PASSWORD
pytest tests/test_cart.py --headed --slowmo 300
playwright show-trace test-results/<test>/trace.zip
```

## Page objects

Locators are strings with a strategy prefix, the same syntax as Unit 1: `"css=#cart"`, `"xpath=//h1"`, `"role=button[name='Sold Out']"`, `"name=q"`, `"link=Forgot your password?"`, declared at the bottom of each page class. `BasePage.parse_locator()` turns them into Playwright selectors. Pages never touch `self.page`: they call the `BasePage` methods (`find_element`, `click_element`, `type_text`, `click_and_wait_for_response`, `is_element_enabled`, `element_should_be_disabled` …), which log the action and fail with the locator's name. A page file holds only imports and its one class: helpers such as `parse_locator` and `money_to_float` are `BasePage` methods (a framework test enforces it). Details: Day 5 section 3 of the unit document.

## How a test reads

Every test: a docstring, `# Test data`, then `# Execution steps` made only of `with step("..."):` blocks. Steps are numbered automatically and show up in the Allure report, in the Playwright trace and in the error message of a failure (`failed in Step 3: ...`). Page methods are grouped under `####` banners with `# Scope: <area of the page>`, each with a docstring; locators stay at the bottom. Framework tests enforce both.

```python
@pytest.mark.smoke
@pytest.mark.add_to_cart
def test_add_an_in_stock_product_to_the_cart(shop, products, step):
    """A customer adds one in-stock product: the cart shows 1 item at the product's price."""
    # Test data
    grey_jacket = products["Grey jacket"]

    # Execution steps
    with step("Open the product page of Grey jacket"):
        shop.product.open_product(grey_jacket["path-name"])
    with step("Add 1 item to the cart"):
        shop.product.add_to_cart(1)
    with step("Verify the cart has 1 item, total £55.00"):
        expect_cart(shop.cart.open(), 1, "£55.00")
```

## Reports

Every run writes:

| Output | Path | For |
| --- | --- | --- |
| HTML report | `reports/report.html` | trainer, BA, PO |
| JUnit XML | `reports/junit.xml` | CI test tab |
| Allure results: numbered steps, docstring, markers as tags | `reports/allure-results/` (`allure serve reports/allure-results`, needs the Allure CLI) | trainer, BA, PO |
| Trace, screenshot, video of failed tests | `test-results/` | debugging |

Every test carries one requirement marker (`@pytest.mark.add_to_cart` …, declared in `pytest.ini`): `pytest -m add_to_cart` runs one requirement, and the markers appear in the HTML report. `--strict-markers` rejects a marker typo such as `add_to_card`.

## Known limits of the public demo store

- **Login and registration forms are MANUAL** (`@pytest.mark.manual`): the store's bot protection (CAPTCHA) stops them — no request is sent and no error is shown — so a wrong-password test could only fail. The tests are complete; run them with `pytest -m manual` in a test environment without CAPTCHA. Opening the password-reset form is automated.
- **The theme needs jQuery from `ajax.googleapis.com`**: `block_third_party` allows that one host, otherwise the product page never renders its "Sold Out" button and Add to Cart falls back to a full-page form post. Tracking hosts stay blocked.
- Never commit `.auth/`.

## ATEST03 course repositories

One repository per unit:

| Unit | Days | Topic | Repository |
| --- | --- | --- | --- |
| 1 | 1–4 | BDD automation design and framework practices (behave + Selenium) | [ATEST03-unit1](https://github.com/TrangTT4T/ATEST03-unit1) |
| 2 | 5–8 | Playwright end-to-end automation (pytest + Playwright) | **ATEST03-unit2** (this repository) |
| 3 | 9–12 | Mobile (Appium) and asynchronous systems | [ATEST03-unit3](https://github.com/TrangTT4T/ATEST03-unit3) |
| 4 | 13–18 | Containers, AWS cloud execution, performance (JMeter), CI/CD | [ATEST03-unit4](https://github.com/TrangTT4T/ATEST03-unit4) |
| 5 | 19–22 | Mock project: Swag Labs, end to end, without AWS | [ATEST03-unit5-mock](https://github.com/TrangTT4T/ATEST03-unit5-mock) |
