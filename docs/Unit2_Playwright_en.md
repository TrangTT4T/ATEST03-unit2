# Unit 2 – Playwright End-to-End Automation (Swag Labs)

pytest + Playwright (pytest-playwright) · Application under test: https://www.saucedemo.com (Swag Labs) · Code: `ATEST03-unit2/`

Unit 2 is plain Playwright: pytest tests that drive page objects, with no Gherkin layer (BDD is Unit 1's subject; BDD on top of Playwright is the mock project in Unit 5). The tests are built on Day 5, then gain tracing, saved login and parallel runs (Day 6), are applied to the prioritised workflows in the lab (Day 7), and are made reliable with failure analysis and flaky-test control (Day 8). Everything runs with the `pytest` command.

Why Swag Labs: the first version of this unit tested the Shopify store of Unit 1 (sauce-demo.myshopify.com). Its Cloudflare protection and rate limit (HTTP 429, "Just a moment...") stopped the browser tests on some networks, and a bot check must never be bypassed. Swag Labs is a demo shop made for test automation: no bot protection, no rate limit, `data-test` attributes on its elements, demo accounts listed on its login page.

| Day | Content | LO | Delivery | Minutes | Format |
| --- | --- | --- | --- | --- | --- |
| Day 5 | Playwright architecture, browser contexts, locators, fixtures, assertions, isolation | LO3 | Concept/Lecture | 120 | Virtual |
| Day 6 | Tracing, authentication state, parallel execution, reporting patterns | LO3 | Concept/Lecture | 120 | Virtual |
| Day 7 | Playwright implementation lab: prioritised end-to-end workflows with fixtures and tracing | LO3 | Assignment/Lab | 150 | Hybrid |
| Day 8 | Topic revision | LO3 | Guides/Review | 60 | Virtual |
| Day 8 | Reliability and maintainability: failure analysis, flaky-test control, tracing diagnostics, stability | LO3 | Concept/Lecture | 120 | Virtual |

Contents: Day 5 – Architecture · Day 6 – Tracing, auth, parallel · Day 7 – Lab · Day 8 – Revision + reliability

```text
ATEST03-unit2/
├── pytest.ini                   # base_url, tracing, reports, markers (--strict-markers)
├── requirements.txt
├── .env.example                 # SWAG_USERNAME, SWAG_LOCKED_OUT_USERNAME, SWAG_PASSWORD; copy to .env (git ignores it)
├── dataset/                     # test data, one JSON file per area (Helper.read_test_data("<area>"))
│   ├── products.json            #   the 6 products: id, price, description
│   ├── login.json               #   rejected logins and their errors
│   ├── catalog.json             #   the 4 sort options
│   ├── cart.json                #   add / remove cases
│   └── checkout.json            #   overview totals (item total, tax, total), required fields and their errors
├── pages/                       # Page Objects: one class per file, XPath locators at the bottom
│   ├── base_page.py             #   BasePage: find_element(s), click/type/select, waits, header, side menu
│   ├── login_page.py  inventory_page.py  product_page.py  cart_page.py
│   └── checkout_information_page.py  checkout_overview_page.py  checkout_complete_page.py
├── tests/
│   ├── conftest.py              # fixtures: products, accounts, shop, logged_in_shop, fill_cart, saved login, step
│   ├── test_login.py  test_catalog.py  test_cart.py  test_checkout.py   # one file per area
│   ├── test_auth_state.py       # saved login + isolation check
│   ├── test_visual.py           # visual comparison with the standard user (finding V1)
│   └── test_mobile.py           # an iPhone 13 context: layout and an order
├── helper_utility/helpers.py    # class Helper: by_locator(), read_test_data(), money_to_float(), Faker data
├── helper_utility/pdf_receipt.py  # class PdfReceipt: the order PDF read into fields (pypdf)
├── helper_utility/visual_comparison.py  # class VisualComparison: two screenshots, pixel by pixel (Pillow)
├── tools/flaky_report.py       # run the suite N times: stable / failing / flaky tests (Day 8)
├── allure/categories.json      # Allure failure categories (Day 8 failure analysis)
└── helper_utility/steps.py      # the `step` fixture: numbered steps -> Allure step + trace group
```

### Requirements and risks

| Requirement | Marker | Risk | Level |
| --- | --- | --- | --- |
| REQ-01 Add products to the cart | `add_to_cart` | R01 Wrong cart contents | Critical |
| REQ-02 Remove products from the cart | `update_cart` | R01 Wrong cart contents | Critical |
| REQ-03 Check out: information, overview totals, order complete | `checkout` | R02 Wrong total or lost order | Critical |
| REQ-04 Correct product information | `product_details` | R03 Product page differs from the list | High |
| REQ-05 Log in and out securely | `secure_login` | R04 Wrong user gets in, or a valid user cannot | High |
| REQ-06 Browse and sort the product list | `browse_catalog` | R05 Wrong name or price in the list (High); R07 Wrong sort order (Medium) | High / Medium |

---

## Day 5 – Playwright Architecture: Browser Contexts, Locators, Fixtures, Assertions & Isolation

Unit 2 · LO3 · Concept/Lecture · 120 min · Virtual

Unit 2 keeps the working method of Unit 1 (requirements, risks, data files, page objects) and changes the tool: plain pytest tests drive Playwright page objects, markers replace Gherkin tags, and pytest fixtures replace behave hooks.

### 1. What is inherited from Unit 1, what is new

| Unit 1 (behave + Selenium) | Unit 2 (pytest + Playwright) | Status |
| --- | --- | --- |
| `*.feature` scenarios | One pytest test per scenario in `tests/test_<area>.py`; Examples tables become `@pytest.mark.parametrize` over a data file | Rewritten as plain tests |
| Requirement tags `@add_to_cart` … | Markers `@pytest.mark.add_to_cart` …, declared in `pytest.ini` | Inherited |
| `dataset/*.json` | One JSON file per area, read with `Helper.read_test_data("<area>")` | Inherited |
| Tags `@critical`, `@smoke`, `@negative` | Same names as pytest markers: `pytest -m smoke`; the area is the file: `pytest tests/test_cart.py` | Inherited |
| Page Objects, plain XPath locators at the bottom, `Helper.by_locator` | Same layout; Playwright `Locator` instead of `WebElement` | Ported |
| `environment.py` hooks | `tests/conftest.py` fixtures | Replaced |
| `WebDriverWait` explicit waits | Auto-waiting actions + retrying `expect()` | Replaced |
| Fresh browser per scenario | Fresh **browser context** per test (much cheaper) | Improved |
| Screenshot on failure | Screenshot + video + **trace** on failure | Extended (Day 6) |
| — | Saved login state, parallel runs | New (Day 6) |

### 2. Playwright architecture

```text
pytest session
└── playwright  (driver process, one per worker)
    └── browser  (Chromium / Firefox / WebKit, one per worker, session scope)
        └── context  (one per test: own cookies, localStorage → own login, own cart)
            └── page  (one tab per test)
```

A context costs milliseconds, so every test starts logged out with an empty cart without restarting the browser. Swag Labs keeps the login in a cookie (`session-username`) and the cart in localStorage (`cart-contents`): both belong to the context, so no test sees another test's cart.

#### Contexts beyond isolation: a phone

A context can also emulate a device. `phone_shop` (`tests/conftest.py`) opens Swag Labs as an iPhone 13 from Playwright's device list — 390×844 screen, touch, mobile user agent, pixel density 3 — in Chromium, logged in with the saved cookie. `tests/test_mobile.py` checks that the products page fits the phone (one full-width card per row, no sideways scroll) and that a customer can order on it. Other browsers: `pytest --browser firefox --browser webkit` runs the suite in each (install them first with `playwright install firefox webkit`).

### 3. Locators

Swag Labs marks its elements with `data-test` attributes, made for test automation. They do not change when the layout or the text changes, so they come first:

| Priority | Locator (plain XPath) | Example in `pages/` |
| --- | --- | --- |
| 1 | `data-test` attribute | `//*[@data-test='checkout']`, `//*[@data-test='shopping-cart-badge']`, `//*[@data-test='error']` |
| 2 | Id | `//*[@id='react-burger-menu-btn']` (the menu button has no `data-test`) |
| 3 | Scoped to a parent by its text | `//*[@data-test='inventory-item'][.//*[@data-test='inventory-item-name' and normalize-space()='{}']]//button` — the button of one product card |
| 4 | Button text inside a scope | `…//button[normalize-space()='Remove']` |
| Never | Position | `(//button)[3]`, `//div[2]/a` |

`testid=checkout` is a short form of `//*[@data-test='checkout']` (the prefix `testid` in `Helper.by_locator`); the pages keep the full XPath, the short form is there for quick checks and new pages.

#### Locators and the custom BasePage methods (the same layout as Unit 1)

Locators are plain XPath strings that describe the element, grouped under a comment that names the area of the page; a template uses `{}` and `.format()`:

```python
    # --- Locators -------------------------------------------------------------
    # Cart items. .format(product_name): the line whose name is exactly product_name
    _item_names = "//*[@data-test='cart-list']//*[@data-test='inventory-item-name']"
    _item_line = "//*[@data-test='cart-list']//*[@data-test='inventory-item'][.//*[normalize-space()='{}']]"
    _remove_button = _item_line + "//button[normalize-space()='Remove']"
    # Cart buttons
    _continue_shopping_button = "//*[@data-test='continue-shopping']"
    _checkout_button = "//*[@data-test='checkout']"
```

`Helper.by_locator()` (`helper_utility/helpers.py`, the same prefixes as Unit 1) turns a locator into a Playwright selector:

| Locator | Playwright selector |
| --- | --- |
| `//*[@data-test='checkout']` (no prefix: what the pages write) | `xpath=//*[@data-test='checkout']` |
| `id=checkout` or `id:checkout` | `id=checkout` |
| `name=user-name` | `xpath=//*[@name='user-name']` |
| `link=About` / `partial link=Abo` | `xpath=//a[normalize-space()='…']` / `xpath=//a[contains(normalize-space(),'…')]` |
| `css=#checkout`, `tag_name=h3`, `class_name=error`, `xpath=//h3` | `css=#checkout`, `css=h3`, `css=.error`, `xpath=//h3` |
| `testid=checkout` | `xpath=//*[@data-test='checkout']` |
| `foo=bar` | `ValueError: Element locator with prefix 'foo' is not supported: 'foo=bar'` |

Pages never call `self.page`: they call the `BasePage` methods, which log the action (shown in the report of a failed test, passwords as `***`):

| Group | Methods |
| --- | --- |
| Navigation | `open_page(path)`, `wait_until_url_contains(fragment)`, `wait_until_url_ends_with(suffix)` |
| Locators | `find_element(locator)` (first match), `find_elements(locator)` (all matches), `get_texts(locator)` — Playwright locators are lazy: they wait when an action or `expect()` uses them |
| Actions | `click_element`, `type_text(locator, text, secret=False)`, `select_option(locator, label)` |
| State | `is_element_visible(locator, timeout=0)` — waits for the state up to `timeout` seconds, never a fixed sleep |
| Header | `page_title`, `cart_badge`, `get_cart_badge_count()`, `open_cart()` |
| Side menu | `logout()`, `reset_app_state()` |

Swag Labs is a single-page app: a click changes the address without loading a new page. So the pages wait for the address (`wait_until_url_contains("/cart.html")`), not for a page load. Every wait and action runs inside `_report_timeout()`: a Playwright timeout logs an ERROR line and says what the test was doing and on which page ("Clicking '//*[@data-test='checkout']' timed out on https://www.saucedemo.com/cart.html"), followed by Playwright's call log.

No method returns the page for chaining: call a method, then use the page, on two lines. Only methods the pages or tests use are kept.

### 4. Fixtures (`tests/conftest.py`)

| Fixture | Scope | Replaces in Unit 1 | Does |
| --- | --- | --- | --- |
| `browser`, `context`, `page` | session / test / test | `before_scenario` + `after_scenario` | Provided by pytest-playwright |
| `browser_context_args` | session | `_make_driver()` options | Viewport 1366×900, locale en-US |
| `products` | session | `before_all` loading JSON | `Helper.read_test_data("products")` |
| `swag_accounts` | session | — | The demo accounts from `.env` by name (`standard-user`, `locked-out-user`, `problem-user` …); skips with a clear message when a needed variable is missing |
| `shopper` | session | — | The account of the run: `--account` (default `standard-user`) |
| `accounts` | test | — | Every login of `dataset/login.json` by name: the demo accounts + made-up ones (Faker): `unknown-user`, `wrong-password`, `missing-username`, `missing-password` |
| `checkout_information` | test | — | A made-up customer for the checkout form (Faker) |
| `shop` | test | `Helper.create_page_object()` | Every Page Object bound to this test's page: `shop.login`, `shop.inventory`, `shop.cart` … |
| `logged_in_shop` | test | `Given I am logged in` step | `shop`, logged in as the `--account` user with the saved cookie (no login form), on the products page |
| `fill_cart` | test | `Given ... in the cart` step | Factory: `fill_cart(["Sauce Labs Backpack", "Sauce Labs Onesie"])` |
| `saved_login_state` | test (backed by a session record) | — | Logs in once per session, renews after 9 minutes (Day 6) |
| `step` | test | — | Numbered steps (section 5) |

```python
@pytest.fixture
def fill_cart(logged_in_shop):
    """Factory fixture: fill_cart(["Sauce Labs Backpack", ...]) adds the products from the products page."""
    def add_products(product_names: list[str]):
        logged_in_shop.inventory.add_products_to_cart(product_names)
        return logged_in_shop
    return add_products
```

### 4b. Test data (`dataset/`) and random data (Faker)

Tests hold no values of their own: they read one JSON file per area through `Helper.read_test_data("<area>")`, and a parametrized test runs once per case. A new case is a new line in the file, not new code.

| File | Holds | Used by |
| --- | --- | --- |
| `products.json` | 6 products: `id` (the product page is `/inventory-item.html?id=<id>`), `price`, `description` | `products` fixture: list, product page, cart, sorting |
| `login.json` | `rejected`: account name → error (unknown user, wrong password, locked-out user, missing username, missing password); the "not logged in" error | `test_login.py`, `test_auth_state.py` |
| `catalog.json` | `sorting`: the 4 options, sorted by name or price, ascending or descending | `test_catalog.py` |
| `cart.json` | `add` (lists of products), `remove` (products + the one to remove) | `test_cart.py` |
| `checkout.json` | `totals` (products → item total, 8% tax, total), `missing_information` (empty field → error), the confirmation heading, `pdf_receipt` (file name pattern, pages, title) | `test_checkout.py` |

```python
CART = Helper.read_test_data("cart")

@pytest.mark.parametrize("case", CART["add"], ids=[case["id"] for case in CART["add"]])
def test_add_products_to_the_cart(fill_cart, step, case):
    ...
```

Account data is never written in a file that goes to GitHub. The Swag Labs demo accounts (listed on its login page) live in `.env`, which git ignores; `.env.example` has only the names of the variables. Everything else is made up by Faker for every test: an unknown username, a wrong password, the checkout customer.

`Helper` (`helper_utility/helpers.py`) is what pages and tests share:

| Area | Methods |
| --- | --- |
| Element finder | `by_locator()`: locator string → Playwright selector; an unknown prefix raises `ValueError` |
| Test data | `read_test_data(area)`: a missing file raises `FileNotFoundError` listing the areas that exist |
| Prices | `money_to_float("$1,120.00")` → 1120.0 (also inside a text: `"Item total: $29.99"` → 29.99) |
| Random data | `random_checkout_information()`, `random_unregistered_login()`, `random_password()` |

### 5. Assertions

`expect()` retries until the condition holds or the timeout (5 s) ends, so no explicit waits are written:

```python
@pytest.mark.smoke
@pytest.mark.add_to_cart                      # requirement REQ-01 (the file adds @critical)
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

| Unit 1 | Unit 2 |
| --- | --- |
| `self.wait.until(EC.url_contains("checkout"))` | `expect(page).to_have_url(re.compile("checkout"))` |
| `assert badge.text == "1"` after a wait | `expect(shop.inventory.cart_badge).to_have_text("1")` |
| `assert error_text().strip()` | `expect(shop.login.error_message).to_have_text("Epic sadface: …")` |
| `assert not badge.is_displayed()` | `expect(shop.inventory.cart_badge).to_be_hidden()` |

#### Test layout: test data, then numbered steps

Every test reads the same way: a docstring saying what it proves, `# Test data` (plain assignments), then `# Execution steps` — only `with step(step_number, "..."):` blocks. The test counts its steps like the workplace pattern `with allure.step(f"Step {step_index}: ...")`: `step_number = 1` before the first step, `step_number += 1` before each next one. The `step` fixture (`helper_utility/steps.py`) checks the counter — a skipped number or a forgotten `+= 1` (two "Step 2") stops the test with a clear `ValueError` — and turns each block into:

| Where | What you see |
| --- | --- |
| Allure report | The test as a list "Step 1: … / Step 2: … / Step 3: …", the failed step in red; the docstring is the description, the markers are tags |
| Trace Viewer | The clicks and waits of a failed test grouped under the step name |
| HTML / JUnit report | The error ends with `failed in Step 3: Open the cart and verify it holds …` |

Page objects follow the same idea: methods are grouped under a banner naming the area of the page, every public method has a docstring, locators stay at the bottom:

```python
class CartPage(BasePage):
    ############################################################################
    # Navigation methods
    # Scope: Cart page > Continue Shopping, Checkout
    ############################################################################
    def click_checkout(self):
        """Click "Checkout" and wait for the checkout information page."""
        self.click_element(self._checkout_button)
        self.wait_until_url_contains("/checkout-step-one.html")
```

Both rules are part of the review checklist (Day 8, B4).

### 5b. Other demo accounts (`--account`)

Swag Labs has six demo accounts; four have defects on purpose. `pytest --account <name>` (an option added in `tests/conftest.py` with `pytest_addoption`) makes `logged_in_shop` and the login smoke test use that account; the header of the run names it. The same 43 tests then become a defect finder:

| Account (`--account`) | Result | What the failures show |
| --- | --- | --- |
| `standard-user` (default) | 42 passed, 1 xfailed | — |
| `performance-glitch-user` | 42 passed, 1 xfailed, about 3.5× slower | the login takes several seconds; auto-waiting absorbs it, no test needs a longer timeout |
| `visual-user` | 8 failed | the products page shows wrong prices (e.g. Backpack $88.21 instead of $29.99), so price sorting is wrong too; cart and checkout totals stay right |
| `error-user` | 15 failed | sorting does nothing; only 3 of the 6 products can be added; Remove on the products page does nothing; the product page has no description; the last name field takes no text, yet the form goes on without it; Finish does not complete the order |
| `problem-user` | 19 failed | sorting does nothing; product names open the wrong product page (Fleece Jacket: "ITEM NOT FOUND"); only 3 products can be added, Remove on the products page does nothing; typing the last name overwrites the first name, so checkout never gets past the information form |

### 5c. Visual comparison (`tests/test_visual.py`)

Text assertions miss what a customer sees: a wrong picture, a button out of place. Playwright for Python has no screenshot assertion, so `VisualComparison` (`helper_utility/visual_comparison.py`, Pillow) compares two screenshots pixel by pixel: a pixel differs when a colour channel moves by more than 16 (anti-aliasing noise stays below), and the test allows at most 0.1 % differing pixels. The expected, actual and diff images (differing pixels in red) are saved and attached to Allure.

The reference is the standard user's products page, taken in the same run, browser and viewport (`BasePage.take_screenshot()` waits for no network traffic and loaded fonts): no baseline image is stored, so fonts and rendering never differ between machines.

| Case | Result |
| --- | --- |
| `standard-user` against itself | passes: the comparison is stable |
| `visual-user` | **xfail, finding V1**: 2.8 % of the pixels differ — the Backpack shows a dog, wrong prices, shifted titles and button, the cart icon moved onto the sort list |

### 6. Isolation check

`tests/test_auth_state.py::test_login_state_does_not_leak_into_other_tests` proves that a test using the default `page` is not logged in even when another test in the same session uses the saved login.

### 7. Run

```bash
cd ATEST03-unit2
pip install -r requirements.txt
playwright install chromium
cp .env.example .env              # fill in the demo accounts shown on https://www.saucedemo.com
pytest --collect-only -q          # 50 tests
pytest -m smoke                   # 3 tests: login, add to cart, complete an order
pytest --headed --slowmo 300      # watch it run
```

### 8. Review questions

1. Why does a new browser context give the same isolation as a new browser, and why is it cheaper?
2. Where does Swag Labs keep the cart, and why does that make the context the right unit of isolation?
3. Rewrite `self.wait.until(lambda d: badge().text == "2")` as a Playwright assertion.
4. Why is `//*[@data-test='checkout']` preferred over `//button[2]` or `//button[text()='Checkout']`?

---

## Day 6 – Tracing, Authentication State, Parallel Execution & Reporting

Unit 2 · LO3 · Concept/Lecture · 120 min · Virtual

Day 6 adds what Unit 1 did not have: a full trace of every failed test, login reuse and parallel runs.

### 1. Tracing (extends Unit 1's screenshot on failure)

Configured once in `pytest.ini`:

```ini
addopts =
    --tracing retain-on-failure
    --screenshot only-on-failure
    --video retain-on-failure
    --output test-results
```

| Unit 1 | Unit 2 |
| --- | --- |
| `after_step` saves one PNG | `test-results/<test>/trace.zip`, `test-failed-1.png`, `video.webm` |
| Shows the last screen only | Every action, DOM snapshot before/after, console, network, source line, the numbered steps |

```bash
playwright show-trace test-results/<test-folder>/trace.zip   # open a trace
pytest --tracing on                                          # keep traces for every test while debugging
```

### 2. Known defects: `xfail(strict=True)`

**Finding F1:** after **Reset App State** (side menu) the cart is empty — the badge disappears — but the product's button still says "Remove" instead of "Add to cart". A customer sees a product as "in the cart" when it is not.

```python
@pytest.mark.xfail(strict=True, reason="Finding F1: after Reset App State the cart is empty but the product's button "
                                        "still says Remove (checked 2026-11-27)")
def test_reset_app_state_empties_the_cart_and_resets_the_buttons(fill_cart, step):
```

The test states the expected behaviour and is marked `xfail(strict=True)` with the finding: the report lists it as a known defect, and when the shop is fixed the test passes and `strict` makes the run fail, so the marker is removed. Run it without the marker to see the failing step: `pytest --runxfail tests/test_cart.py -k reset`.

### 2b. Downloads: the PDF receipt

The order-complete page has a **Generate PDF order** button that downloads the receipt (`swag-labs-order-<date>_<time>.pdf`). `BasePage.click_and_download(locator, folder)` wraps Playwright's `expect_download()` and saves the file under its own name in pytest's `tmp_path`; `CheckoutCompletePage.download_pdf_order(folder)` uses it.

`PdfReceipt` (`helper_utility/pdf_receipt.py`, pypdf) reads the PDF into fields, so the test compares data, not raw text:

| Field | Compared with |
| --- | --- |
| file name, page count, title | `checkout.json` `pdf_receipt` (name pattern, 1 page, "Order Receipt") |
| order date | today |
| ship to: name, postal code | the Faker customer the test typed in |
| items: name → price | `products.json` prices of the products the test ordered (and no other line) |
| item total, tax, total | the case in `checkout.json` `totals` |
| thank-you text | `checkout.json` `order_complete_header` |

The PDF's text comes out letter-spaced in places ("T ax $ 3.20", "Sauce Labs Bolt T -Shirt"), so `PdfReceipt` compares labels and product names without spaces.

### 3. Authentication state: log in once, reuse the cookie

Unit 1 typed credentials in every scenario that needed a login. Here the login form is used **once per session** (once per worker with `-n`): `saved_login_state` logs in, saves cookies and localStorage with `context.storage_state()`, and every test that only needs to be logged in (`logged_in_shop`) puts that cookie into its own context and opens the products page directly:

```python
@pytest.fixture
def saved_login_state(browser: Browser, base_url: str, shopper, login_state_record) -> Path:
    age = time.monotonic() - login_state_record["saved_at"]
    if login_state_record["path"] is None or age > LOGIN_STATE_MAX_AGE:   # 9 minutes
        path = AUTH_DIR / f"{shopper['username']}_{os.getpid()}.json"     # one file per xdist worker
        context = browser.new_context(base_url=base_url)
        login = LoginPage(context.new_page())
        login.open_page()
        login.login_and_wait_for_products(shopper["username"], shopper["password"])
        context.storage_state(path=str(path))
        context.close()
        login_state_record.update(path=path, saved_at=time.monotonic())
    return login_state_record["path"]


@pytest.fixture
def logged_in_shop(shop, saved_login_state) -> SimpleNamespace:
    shop.inventory.add_login_cookies(saved_login_state)   # only the cookie: every test still has an empty cart
    shop.inventory.open_page()
    shop.inventory.verify_products_page_is_open()
    return shop
```

| Check (serial run) | Result |
| --- | --- |
| Tests that start logged in (`logged_in_shop`) | 37, all with the saved cookie |
| Clicks on the Login button | 7: the one saved login + the 6 tests about the login itself (valid login, 5 rejected logins), which must use the form |
| Swag Labs' session cookie | expires 10 minutes after the login: the saved state is renewed when it is older than 9 minutes (checked with the limit set to 3 seconds: the session logged in again every few seconds and the cart and checkout tests passed) |

Only the cookie is copied: Swag Labs keeps the cart in localStorage, so every test still starts with an empty cart. `tests/test_auth_state.py` (risk R04) shows the other way to use the file — a new context created with `storage_state=` — and checks that the default `page` stays logged out. `.auth/` holds sessions: it is in `.gitignore`, never commit it.

### 4. Parallel execution

```bash
pytest -n auto        # pytest-xdist, one worker per CPU
pytest -n 4
```

Safe because every test has its own context (Day 5) and no test depends on another. Swag Labs is a static site, so parallel runs do not load a shared server.

### 5. Reporting patterns

| Report | Produced by | Path |
| --- | --- | --- |
| HTML | pytest-html (`--html` in `pytest.ini`) | `reports/report.html` |
| JUnit XML | `--junitxml` | `reports/junit.xml` |
| Allure results (numbered steps) | allure-pytest (`--alluredir`); view with `allure serve reports/allure-results` (Allure CLI) | `reports/allure-results/` |
| Trace, screenshot, video | pytest-playwright | `test-results/` |

Every test carries one requirement marker (`@pytest.mark.add_to_cart` …) and one risk-level marker: `pytest -m add_to_cart` runs one requirement, `pytest -m critical --collect-only -q` lists every Critical-risk test, and the markers appear in the HTML report. `-rfEs` in `pytest.ini` lists failures, errors and skips (with their reason) at the end of the run.

#### Allure: failure categories, environment, evidence

`tests/conftest.py` prepares the Allure results at the start of every run (Day 8, failure analysis):

| What | Where it comes from | What the report shows |
| --- | --- | --- |
| Categories | `allure/categories.json`, copied into the results | every failure sorted: **Product defects** (an assertion failed: the shop showed a wrong value), **Test or environment problems** (an exception: a timeout, a missing element), **Known defects** (xfail), **Set-up** (skipped for a missing `.env` value) |
| Environment | `environment.properties`, written by `pytest_configure` | base URL, browsers, `--account`, Python and Playwright versions of the run |
| Evidence of a failure | `pytest_runtest_makereport` | in the failed test: a full-page screenshot, the page address, the **Playwright trace** (`trace.zip`, open it with `playwright show-trace`) and the video |

### 6. Review questions

1. What does a trace show that a screenshot cannot?
2. Why is F1 an `xfail(strict=True)` and not a skipped or deleted test?
3. Why must `saved_login_state` be session-scoped, and why must `.auth/` stay out of git?
4. Why is `pytest -n auto` safe for this suite?

---

## Day 7 – Playwright Implementation Lab: Prioritised End-to-End Workflows with Fixtures & Tracing

Unit 2 · LO3 · Assignment/Lab · 150 min · Hybrid

The lab automates the risk priorities on Playwright: 50 tests, all in the default run (Swag Labs needs no manual or data-creating exclusions).

### 1. Prioritised workflows (from the risk table)

| Priority | Workflow | Risk | Tests | Unit 2 technique |
| --- | --- | --- | --- | --- |
| P1 | Add to cart, remove, keep while shopping, reset | R01 Critical | `test_cart.py`: 10 tests (cases from `dataset/cart.json`), 1 of them `xfail` (F1) | `fill_cart` factory, `parametrize`, `to_be_hidden()` |
| P1 | Checkout: information, totals, complete | R02 Critical | `test_checkout.py`: 10 tests (cases from `dataset/checkout.json`), 3 of them compare the downloaded PDF receipt | Faker customer, `to_have_text` on totals, `expect_download` + `PdfReceipt` |
| P1 | Product page = product list | R03 High | `test_catalog.py`: 6 cases (one per product) | `parametrize` over `products.json` |
| P1 | Login, logout, locked-out user, saved session | R04 High | `test_login.py` 8 tests + `test_auth_state.py` 2 tests | `accounts` from `.env` + Faker, `saved_login_state` |
| P1 | Product list names, descriptions and prices | R05 High | `test_catalog.py`: 6 cases | `product_card(name)` |
| P2 | Looks right: visual comparison | R05 High | `test_visual.py`: 2 cases, 1 `xfail` (V1) | `VisualComparison`, reference taken in the same run |
| P2 | Works on a phone | R01/R05 Medium | `test_mobile.py`: 2 tests | iPhone 13 context from `playwright.devices` |
| P2 | Sorting | R07 Medium | `test_catalog.py`: 4 cases (`dataset/catalog.json`) | expected order computed from `products.json` |

### 2. Files

| File | Role |
| --- | --- |
| `tests/test_<area>.py` | One file per area; every test has a risk, a suite and a requirement marker |
| `tests/conftest.py` | Fixtures: data, accounts, page objects, logged-in shop, cart factory, saved login, steps |
| `tests/test_auth_state.py` | Saved login and isolation check |
| `tools/flaky_report.py` | Flaky-test report over N runs (Day 8) |
| `allure/categories.json` | Failure categories of the Allure report |
| `pages/` | Page Objects, one per page of the shop |
| `dataset/` | Test data, one file per area |
| `pytest.ini` | base URL, tracing, reports, marker list (`--strict-markers`) |

### 3. Run the lab

```bash
cd ATEST03-unit2
pip install -r requirements.txt
playwright install chromium
cp .env.example .env                # fill in the demo accounts
pytest                              # the whole suite
pytest -m smoke                     # login + add to cart + complete an order
pytest -n auto                      # parallel
pytest -m critical                  # every Critical-risk test
pytest -m "critical and not negative"
pytest tests/test_checkout.py       # one area
```

### 4. Expected results

| Check | Result |
| --- | --- |
| `pytest` | 48 passed, 2 xfailed (findings F1, V1), about 72 s |
| `pytest -n 4` | 48 passed, 2 xfailed, about 31 s |
| `pytest` without `.env` | every test that needs an account is skipped, with the variables to set |
| Failed test | `test-results/<test>/trace.zip`, screenshot, video |

Verified on www.saucedemo.com (2026-11-27).

### 5. Lab tasks

1. Add a checkout case for three products to `dataset/checkout.json` (compute the 8% tax yourself). Which test runs it, without a code change?
2. Make `test_product_page_shows_the_same_name_description_and_price` fail by changing a price in `products.json`, then open its trace and find the failing step.
3. Add a login case for `problem_user` (a demo account that logs in but shows wrong images): which fixture and which `.env` variable does it need?
4. Run `pytest -n auto` three times and compare durations with the serial run.

---

## Day 8 – Topic Revision + Playwright Reliability & Maintainability: Failure Analysis, Flaky-Test Control, Tracing Diagnostics

Unit 2 · LO3 · Guides/Review (60 min) + Concept/Lecture (120 min) · Virtual

Day 8 closes both units: part A revises Unit 2 against Unit 1, part B makes the suite reliable with a trace-driven failure analysis routine, repeated runs to expose flaky tests and a maintainability checklist.

### Part A – Topic revision (60 min)

| Topic | Unit 1 (Day 1–4) | Unit 2 (Day 5–7) |
| --- | --- | --- |
| Specification | Gherkin features, tags | Plain pytest tests; markers for requirement, risk and suite |
| Engine | Selenium WebDriver | Playwright (auto-wait, contexts) |
| Setup / teardown | behave hooks | pytest fixtures (`conftest.py`) |
| Isolation | New browser per scenario | New context per test |
| Waiting | `WebDriverWait` | Actions auto-wait, `expect()` retries |
| Failure evidence | Screenshot | Trace + screenshot + video |
| Login | UI login each time | Login form once per session, then the saved cookie |
| Speed | Serial | `-n auto` parallel |
| Selection | `behave --tags=@cart` | `pytest tests/test_cart.py`, `pytest -m add_to_cart` |
| Application | Shopify demo store | Swag Labs (no bot protection: see the introduction) |

Revision questions:

1. Which parts of Unit 1 (data files, page-object layout, markers) carry over unchanged, and why is that useful?
2. Why did Unit 2 move from the Shopify store to Swag Labs, and why is bypassing a bot check never the answer?
3. Which Unit 1 review findings does Unit 2 address? (F3 stability: auto-wait and `expect()`; F7 and F8 form-submit races: every click that changes the page waits for the new address.)

### Part B – Reliability and maintainability (120 min)

#### B1. Failure analysis routine

```text
test fails
 ├─ 1. read the assertion message in reports/report.html ("failed in Step N: ...")
 ├─ 2. open test-results/<test>/trace.zip   (playwright show-trace)
 │     ├─ Actions tab: which step, which locator, how long it waited
 │     ├─ Snapshots: DOM before/after the action
 │     └─ Console tab: errors of the shop's JavaScript
 ├─ 3. classify
 │     ├─ product defect   → wrong total, wrong button text → raise a bug with the trace, xfail(strict) meanwhile
 │     ├─ test defect      → locator changed, wrong assumption → fix in pages/ or the data file
 │     └─ environment      → site down, network, missing .env → retry later, or fix the set-up
 └─ 4. if it passes on rerun without a change → flaky: see B2
```

#### B2. Flaky-test control

`tools/flaky_report.py` does the comparison: it runs the suite N times (or reads JUnit files) and sorts every test:

```bash
python tools/flaky_report.py --runs 3                        # runs pytest 3 times, then reports
python tools/flaky_report.py --runs 5 -- tests/test_checkout.py -k pdf   # extra pytest arguments after --
python tools/flaky_report.py reports/run_1.xml reports/run_2.xml        # existing JUnit files
```

It prints the stable, failing and flaky tests, with the outcome of each run, and exits with 1 when a test is failing or flaky. It found a real flaky test while this page was written: the PDF receipt letter-spaces some names ("T onya Jordan"), so a receipt test failed only when Faker made up such a name; the name is now compared without spaces.


| Result over the runs | Meaning | Action |
| --- | --- | --- |
| passed every time | stable | — |
| failed every time | real defect or broken test | analyse the trace (B1) |
| passed some times, failed others | flaky | quarantine, find the root cause |

Quarantine while the root cause is found (pytest-rerunfailures is installed):

```python
@pytest.mark.flaky(reruns=2, reruns_delay=1)   # temporary, with a ticket number in the commit
def test_something_flaky(...):
    ...
```

`pytest --reruns 1` on a whole run also exposes flaky tests: the HTML report marks them "rerun". Reruns hide problems, so they are a temporary label, never a default for the suite.

Typical root causes and the fix used in this code:

| Root cause | Fix in this repository |
| --- | --- |
| Fixed waits | None used; `expect()` and `wait_for_url` only |
| Next action before the page changed | Every click that changes the page waits for the new address (`wait_until_url_contains`); the single-page app loads no new document, so a load-state wait would return at once |
| Shared state between tests | One context per test (own cookie, own localStorage cart); `test_login_state_does_not_leak_into_other_tests` |
| Positional selectors | Not used; `data-test` attributes and text inside a scope only |
| Ties in sorted data | Two products share a price ($15.99): price sorting compares the prices, not the names |

#### B3. Stability checks before a commit

Quick searches (PowerShell; use `grep -rnE` in Git Bash):

```powershell
Select-String -Path tests\*.py, pages\*.py -Pattern 'wait_for_timeout|time\.sleep'   # fixed waits
Select-String -Path tests\*.py, pages\*.py -Pattern 'force=True'                     # forced clicks
Select-String -Path tests\*.py -Pattern ':nth-child|nth=|\.nth\('                     # positional selectors
```

| Rule | Why |
| --- | --- |
| No `wait_for_timeout(` / `time.sleep(` | Fixed waits are slow and still flaky |
| No `force=True` | Hides elements that a user could not click |
| No positional selectors in tests | Breaks when the layout changes |
| No raw CSS/XPath in tests | Locators belong in `pages/` |
| Every test has a risk-level marker (`critical`, `high`, `medium`) and exactly one requirement marker | Keeps `pytest -m critical` and `pytest -m <requirement>` complete |

#### B4. Maintainability criteria (checklist)

- [ ] Every requirement REQ-01 … REQ-06 has a test: `pytest -m <requirement> --collect-only -q`
- [ ] Tests read like the requirement: actions and checks through page objects, no URL or locator in tests
- [ ] No locator outside `pages/`; test values in `dataset/`, not in the tests
- [ ] Every test has a docstring, `# Test data`, then only `with step(step_number, ...)` blocks; every page method has a docstring under a `# Scope:` banner (review)
- [ ] No fixed waits, no `force=True` (B3 searches return nothing)
- [ ] 0 flaky tests in 3 consecutive runs (B2)
- [ ] Every failure leaves a trace, screenshot and video
- [ ] Suite passes with `-n auto`
- [ ] Accounts (`.env`) and sessions (`.auth/`) are never committed

### Expected results

| Check | Result |
| --- | --- |
| B3 searches | no matches |
| Serial run, parallel run (`-n 4`), `tools/flaky_report.py --runs 3 -- -n 4` | 48 passed + 2 xfailed each time; the flaky report: 50 stable, 0 failing, 0 flaky |
| Forced failure | `trace.zip`, `test-failed-1.png`, `video.webm` in `test-results/` |
