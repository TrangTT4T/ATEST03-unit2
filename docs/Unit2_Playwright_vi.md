# Unit 2 – Playwright End-to-End Automation (Sauce Demo)

pytest + Playwright (pytest-playwright) · Website kiểm thử: https://sauce-demo.myshopify.com · Code: `ATEST03-unit2/`

Unit 2 là Playwright thuần: tự động hóa cùng các yêu cầu, rủi ro và dữ liệu test của Unit 1 bằng test pytest gọi page object, không có lớp Gherkin (BDD là chủ đề của Unit 1; BDD kết hợp Playwright là mock project ở Unit 5). Test được xây ở Day 5; thêm tracing, kiểm soát network, lưu phiên đăng nhập, chạy song song (Day 6); áp dụng cho các luồng ưu tiên trong bài lab (Day 7); và làm cho ổn định bằng phân tích lỗi và kiểm soát flaky (Day 8). Mọi thứ chạy bằng lệnh `pytest`.

| Day | Nội dung | LO | Hình thức | Phút | Format |
| --- | --- | --- | --- | --- | --- |
| Day 5 | Kiến trúc Playwright, browser context, locator, fixture, assertion, cô lập | LO3 | Concept/Lecture | 120 | Virtual |
| Day 6 | Tracing, chặn/giả lập network, trạng thái đăng nhập, chạy song song, mẫu báo cáo | LO3 | Concept/Lecture | 120 | Virtual |
| Day 7 | Lab Playwright: tự động hóa luồng E2E ưu tiên với fixture, tracing, kiểm soát network | LO3 | Assignment/Lab | 150 | Hybrid |
| Day 8 | Ôn tập chủ đề | LO3 | Guides/Review | 60 | Virtual |
| Day 8 | Độ tin cậy và bảo trì: phân tích lỗi, kiểm soát flaky, chẩn đoán bằng trace, ổn định | LO3 | Concept/Lecture | 120 | Virtual |

Nội dung: Day 5 – Kiến trúc · Day 6 – Tracing, network, đăng nhập, song song · Day 7 – Lab · Day 8 – Ôn tập + độ tin cậy

```text
ATEST03-unit2/
├── pytest.ini                   # base_url, tracing, báo cáo, marker (--strict-markers)
├── requirements.txt
├── dataset/products.json        # cùng dữ liệu test với Unit 1
├── pages/                       # Page Object Playwright (chuyển từ Unit 1): mỗi file một class
└── tests/
    ├── conftest.py              # fixture: dữ liệu, cô lập, kiểm soát network, đăng nhập
    ├── test_cart.py  test_checkout.py  test_catalog.py
    ├── test_login.py test_register.py  test_search.py   # mỗi khu vực một file, mỗi yêu cầu một marker
    ├── test_network.py          # chặn request, kiểm tra request, giả lập lỗi, mạng chậm
    ├── test_auth_state.py       # phiên đăng nhập đã lưu + kiểm tra cô lập
    └── unit/                    # quy tắc của framework (không mở trình duyệt): cấu trúc page object và test, helper step
helper_utility/steps.py          # fixture `step`: bước đánh số -> bước Allure + nhóm trong trace
```

---

## Day 5 – Playwright Architecture: Browser Contexts, Locators, Fixtures, Assertions & Isolation

Unit 2 · LO3 · Concept/Lecture · 120 phút · Virtual

Unit 2 giữ CÁI GÌ Unit 1 kiểm thử (yêu cầu, rủi ro, dữ liệu) và đổi CÁCH LÀM: test pytest thuần gọi page object Playwright, marker thay cho tag Gherkin, fixture của pytest thay cho hook của behave.

### 1. Kế thừa từ Unit 1 và phần mới

| Unit 1 (behave + Selenium) | Unit 2 (pytest + Playwright) | Trạng thái |
| --- | --- | --- |
| `tests/features/*.feature` (14 scenario) | Mỗi scenario thành một test pytest trong `tests/test_<khu_vực>.py`; bảng Examples thành `@pytest.mark.parametrize` | Viết lại thành test thường |
| Tag yêu cầu `@add_to_cart` … | Marker `@pytest.mark.add_to_cart` …, khai báo trong `pytest.ini` | Kế thừa |
| `dataset/products.json` | Cùng file | Kế thừa |
| Tag `@critical`, `@smoke`, `@negative` | Cùng tên, thành marker pytest: `pytest -m smoke`; khu vực là file: `pytest tests/test_cart.py` | Kế thừa |
| Page Object (`pages/`) | Cùng tên class, dùng `Locator` của Playwright thay `WebElement` | Chuyển đổi |
| Hook trong `tests/environment.py` | Fixture trong `tests/conftest.py` | Thay thế |
| Explicit wait `WebDriverWait` | Action tự chờ + `expect()` tự thử lại | Thay thế |
| Trình duyệt mới mỗi scenario | **Browser context** mới mỗi test (rẻ hơn nhiều) | Cải tiến |
| Ảnh khi fail | Ảnh + video + **trace** khi fail | Mở rộng (Day 6) |
| — | Chặn/giả lập network, lưu phiên đăng nhập, chạy song song | Mới (Day 6) |

### 2. Kiến trúc Playwright

```text
pytest session
└── playwright  (tiến trình driver, mỗi worker một cái)
    └── browser  (Chromium / Firefox / WebKit, mỗi worker một cái, scope session)
        └── context  (mỗi test một cái: cookie, cache, storage riêng → cô lập)
            └── page  (mỗi test một tab)
```

Tạo context chỉ mất vài mili giây, nên mỗi test có giỏ hàng sạch mà không cần khởi động lại trình duyệt. Ở Unit 1, muốn cô lập như vậy phải mở Chrome mới cho mỗi scenario.

### 3. Locator

| Ưu tiên | Locator | Ví dụ trong `pages/` |
| --- | --- | --- |
| 1 | Role + tên hiển thị | `role=link[name=/My Cart \(\d+\)/]` (mini cart) |
| 2 | Thuộc tính ngữ nghĩa | `css=[itemprop='name']` (tên sản phẩm: `<h1>` đầu tiên của trang là logo) |
| 3 | Text | `text=No results found for` |
| 4 | Thuộc tính ổn định / action của form | `css=form[action*='/cart/add']`, `css=input[name^='updates']`, `name=update` |
| 5 | Locator có filter | dòng trong `#cart` `.filter(has=role=link[name='Striped top' s])`: giới hạn trong `#cart` vì trang nào cũng có mini-cart ẩn lặp lại các dòng đó |
| Không dùng | Theo vị trí | `:nth-child`, `xpath=(//a)[3]` |

#### Locator dạng chuỗi và các method tự viết của BasePage

Locator là chuỗi có tiền tố chiến lược, viết giống repo Unit 1 (Selenium). `BasePage.parse_locator()` đổi chúng thành selector của Playwright:

| Chuỗi locator | Selector Playwright |
| --- | --- |
| `css=#cart`, `xpath=//h1`, `text=...`, `role=...`, `id=product-price`, `data-testid=...` | giữ nguyên (engine có sẵn của Playwright) |
| `name=q` | `css=[name='q']` |
| `tag=html`, `class=errors` | `css=html`, `css=.errors` |
| `link=Forgot your password?` | `role=link[name='Forgot your password?' s]` (khớp đúng) |
| `partial_link=password` | `role=link[name=/password/]` (chứa, phân biệt hoa thường như Selenium) |
| `//h1` / `input[name='q']` (không tiền tố) | `xpath=//h1` / `css=input[name='q']` |

Page không gọi `self.page`: page truyền chuỗi locator cho các method của `BasePage`. Các method này ghi log thao tác (hiện trong báo cáo của test fail, mật khẩu ghi là `***`) và báo lỗi có tên locator:

| Nhóm | Method |
| --- | --- |
| Điều hướng | `open(path)`, `url`, `wait_for_url_contains(fragment)` |
| Locator | `locator(template, **values)`, `find_element(*locators, first=False)` (nối chuỗi: `find_element(self._root, self._update_button)`; phần tử đầu có thể là một Locator làm phạm vi), `count_elements`, `is_element_present` |
| Thao tác | `click_element`, `click_and_wait_for_new_page` (nút submit form), `click_and_wait_for_response(..., url_part=)` (AJAX), `type_text(..., text=, secret=False)`, `press_enter` |
| Đọc và trạng thái | `get_text`, `get_input_value`, `is_element_visible(..., timeout=0)`, `is_element_enabled(..., timeout=0)` — chờ trạng thái tối đa `timeout` giây, không ngủ cố định |
| Kiểm tra (`expect()`, raise `AssertionError`) | `element_should_be_visible`, `element_should_be_disabled`, `element_should_contain_text`, `element_should_have_count` — đều nhận `error_msg` tùy chọn |

`tests/unit/test_page_objects_layout.py` làm lần chạy fail nếu có locator mà `BasePage.parse_locator()` không nhận, có `self.page` ngoài `BasePage`, hoặc có code nằm ngoài class page (hàm phụ như `money_to_float` là method của `BasePage`); `tests/unit/test_base_page_methods.py` chạy từng tiền tố locator và các method trong Chromium với HTML cục bộ (không cần mạng).

### 4. Fixture (`tests/conftest.py`)

| Fixture | Scope | Thay cho phần nào ở Unit 1 | Làm gì |
| --- | --- | --- | --- |
| `browser`, `context`, `page` | session / test / test | `before_scenario` + `after_scenario` | pytest-playwright cung cấp |
| `browser_context_args` | session | option trong `_make_driver()` | Viewport 1366×900, locale en-GB |
| `products` | session | `before_all` đọc JSON | Đọc `dataset/products.json` |
| `shop` | test | `helper_utility/helpers.page()` | Mọi Page Object gắn với page của test |
| `cart_with` | test | code của step Given | Factory: `cart_with("Noir jacket", 2)` |
| `block_third_party` | test, autouse | — | Kiểm soát network (Day 6) |
| `customer_state` | session | — | Lưu trạng thái đăng nhập (Day 6) |

```python
@pytest.fixture
def cart_with(shop, products):
    """Factory fixture: cart_with("Noir jacket", 2) puts 2 Noir jackets in this test's cart."""
    def _add(name: str, quantity: int = 1):
        shop.product.open_product(products[name]["path-name"])
        shop.product.add_to_cart(quantity)
        return shop.cart.open()
    return _add
```

### 5. Assertion

`expect()` tự thử lại tới khi đúng hoặc hết timeout (5 giây), nên không phải viết wait:

```python
@pytest.mark.critical
@pytest.mark.smoke
@pytest.mark.add_to_cart                      # yêu cầu REQ-01
def test_add_an_in_stock_product_to_the_cart(shop, products, step):
    """A customer adds one in-stock product: the cart shows 1 item at the product's price."""
    # Test data
    grey_jacket = products["Grey jacket"]

    # Execution steps
    with step("Open the product page of Grey jacket"):
        shop.product.open_product(grey_jacket["path-name"])
    with step("Add 1 item to the cart"):
        shop.product.add_to_cart(1)           # chờ response AJAX của /cart/add
    with step("Verify the cart has 1 item, total £55.00"):
        expect_cart(shop.cart.open(), 1, "£55.00")   # expect(mini_cart) "My Cart (1)" + total
```

| Unit 1 | Unit 2 |
| --- | --- |
| `self.wait.until(EC.url_contains("checkout"))` | `expect(page).to_have_url(re.compile("checkout"))` |
| `assert cart.is_empty()` sau khi wait | `expect(cart.quantity_inputs).to_have_count(0)` |
| `assert error_text().strip()` | `expect(shop.login.error).to_be_visible()` |

#### Cấu trúc một test: dữ liệu test, rồi các bước được đánh số

Test nào cũng đọc theo cùng một khung: docstring nói test chứng minh điều gì, `# Test data` (chỉ gán biến), rồi `# Execution steps` — chỉ gồm các khối `with step("..."):`. Fixture `step` (`helper_utility/steps.py`) tự đánh số bước (không cần biến đếm `step_index` tự cộng tay) và biến mỗi khối thành:

| Ở đâu | Thấy gì |
| --- | --- |
| Báo cáo Allure | Test hiện thành danh sách "Step 1: … / Step 2: … / Step 3: …", bước fail tô đỏ; docstring là phần mô tả, marker là tag |
| Trace Viewer | Các click và wait của test fail được gom dưới tên bước |
| Báo cáo HTML / JUnit | Lỗi có thêm dòng `failed in Step 3: Verify the cart has 1 item, total £55.00` |

Page object theo cùng ý: method được gom dưới banner ghi khu vực của trang, method public nào cũng có docstring, locator vẫn ở cuối class:

```python
class ProductPage(BasePage):
    ############################################################################
    # Add to cart methods
    # Scope: Product page > Add to cart form
    ############################################################################
    def add_to_cart(self, quantity: int = 1):
        """Add ``quantity`` items and wait until the store has answered every add."""
        ...

    # --- Locators -------------------------------------------------------------
    _add_form = "form[action*='/cart/add']"
```

Hai quy tắc này là test framework (`tests/unit/test_tests_read_as_steps.py`, `tests/unit/test_page_objects_layout.py`): test thiếu step hoặc method page thiếu docstring sẽ làm lần chạy fail.

### 6. Kiểm tra tính cô lập

`tests/test_auth_state.py::test_auth_state_does_not_leak_into_other_tests` chứng minh test dùng `page` mặc định không bị đăng nhập, dù test khác trong cùng session dùng trạng thái đăng nhập đã lưu.

### 7. Chạy

```bash
cd ATEST03-unit2
pip install -r requirements.txt
playwright install chromium
pytest --collect-only -q          # 28 test trình duyệt (22 chạy mặc định) + 38 test framework
pytest -m smoke                   # cùng tag smoke như Unit 1
pytest --headed --slowmo 300      # xem trình duyệt chạy
```

### 8. Câu hỏi ôn tập

1. Vì sao browser context mới cô lập giống trình duyệt mới, và vì sao rẻ hơn?
2. `browser_context_args` thay cho file nào ở Unit 1?
3. Viết lại `self.wait.until(lambda d: name in body_text())` bằng assertion của Playwright.
4. Vì sao `get_by_role("link", name=...)` tốt hơn `a[href*='/cart']`?

---

## Day 6 – Tracing, Network Interception, Authentication State, Parallel Execution & Reporting

Unit 2 · LO3 · Concept/Lecture · 120 phút · Virtual

Day 6 thêm những gì Unit 1 chưa có: trace đầy đủ cho mỗi test fail, kiểm soát lưu lượng network, dùng lại phiên đăng nhập và chạy song song.

### 1. Tracing (mở rộng ảnh chụp khi fail của Unit 1)

Cấu hình một lần trong `pytest.ini`:

```ini
addopts =
    --tracing retain-on-failure
    --screenshot only-on-failure
    --video retain-on-failure
    --output test-results
```

| Unit 1 | Unit 2 |
| --- | --- |
| `after_step` lưu một ảnh PNG | `test-results/<test>/trace.zip`, `test-failed-1.png`, `video.webm` |
| Chỉ thấy màn hình cuối | Mọi action, DOM trước/sau, console, network, dòng code |

```bash
playwright show-trace test-results/<thư-mục-test>/trace.zip   # mở trace
pytest --tracing on                                           # giữ trace cho mọi test khi debug
```

### 2. Chặn và giả lập network

#### 2.1 Chặn request bên thứ ba (fixture autouse)

```python
@pytest.fixture(autouse=True)
def block_third_party(request, context: BrowserContext, base_url: str):
    blocked: list[str] = []
    if request.node.get_closest_marker("allow_third_party"):
        yield blocked
        return
    store_host = urlparse(base_url).hostname

    def handle(route):
        if _is_allowed(route.request.url, store_host):
            route.continue_()
        else:
            blocked.append(route.request.url)
            route.abort()

    context.route("**/*", handle)
    yield blocked
```

Cho phép: host của store và `*.shopify.com`, `*.myshopify.com`, `*.shopifycdn.com`. Mọi host khác (Facebook, Twitter, Pinterest, ứng dụng Sauce) bị hủy. Rủi ro R09 (widget bên thứ ba), vốn kiểm thủ công ở Unit 1, giờ test được.

#### 2.2 Bốn test network (`tests/test_network.py`)

| Test | Kỹ thuật | Risk |
| --- | --- | --- |
| `test_third_party_calls_are_blocked_and_shop_still_works` | `context.route` + abort, rồi chạy luồng giỏ hàng | R09 |
| `test_add_to_cart_posts_the_product_form` | `page.expect_request(...)`: kiểm tra method và body | R01 |
| `test_failed_add_to_cart_request_does_not_add_the_product` | `page.route(...).fulfill(status=500)`: giả lập lỗi server | R01 |
| `test_catalog_loads_on_a_slow_network` | CDP của Chromium `Network.emulateNetworkConditions` (trễ 400 ms) | R05 |

Test network cũng mang marker rủi ro và marker yêu cầu như mọi test khác (`@pytest.mark.critical`, `@pytest.mark.add_to_cart`).

```python
page.route("**/cart/add*", lambda route: route.fulfill(status=500, body="Internal Server Error"))
shop.product.open_product(products["Noir jacket"]["path-name"])
shop.product.add_button.click()
page.unroute("**/cart/add*")
expect(shop.cart.open().quantity_inputs).to_have_count(0)
```

### 3. Lưu trạng thái đăng nhập

Unit 1 gõ thông tin đăng nhập ở mọi scenario cần đăng nhập. Unit 2 đăng nhập một lần mỗi session và lưu cookie, localStorage:

```python
@pytest.fixture(scope="session")
def customer_state(browser: Browser, base_url: str) -> Path:
    email, password = os.getenv("SAUCE_EMAIL"), os.getenv("SAUCE_PASSWORD")
    if not (email and password):
        pytest.skip("Set SAUCE_EMAIL and SAUCE_PASSWORD to run @auth tests")
    context = browser.new_context(base_url=base_url)
    page = context.new_page()
    login = LoginPage(page).open()
    login.login(email, password)
    page.wait_for_url("**/account**")
    AUTH_FILE.parent.mkdir(exist_ok=True)
    context.storage_state(path=str(AUTH_FILE))
    context.close()
    return AUTH_FILE
```

Được dùng trong `tests/test_auth_state.py` (rủi ro R04). File `.auth/customer.json` chứa phiên đăng nhập: không được đưa lên git.

```bash
# Linux/macOS
SAUCE_EMAIL=you@example.com SAUCE_PASSWORD='...' pytest -m auth
# Windows PowerShell
$env:SAUCE_EMAIL="you@example.com"; $env:SAUCE_PASSWORD="..."; pytest -m auth
```

### 4. Chạy song song

```bash
pytest -n auto        # pytest-xdist, mỗi CPU một worker
pytest -n 4
```

An toàn vì mỗi test có context riêng (Day 5) và không test nào phụ thuộc test khác. Store demo dùng chung nên trên site thật để `-n` nhỏ.

### 5. Mẫu báo cáo

| Báo cáo | Tạo bởi | Đường dẫn |
| --- | --- | --- |
| HTML | pytest-html (`--html` trong `pytest.ini`) | `reports/report.html` |
| JUnit XML | `--junitxml` | `reports/junit.xml` |
| Kết quả Allure (bước đánh số) | allure-pytest (`--alluredir`); xem bằng `allure serve reports/allure-results` (Allure CLI) | `reports/allure-results/` |
| Trace, ảnh, video | pytest-playwright | `test-results/` |

Test nào cũng mang một marker yêu cầu (`@pytest.mark.add_to_cart` …): `pytest -m add_to_cart` chạy riêng một yêu cầu, `pytest -m critical --collect-only -q` liệt kê mọi test rủi ro Critical, và marker hiện trong báo cáo HTML.

### 6. Câu hỏi ôn tập

1. Trace cho thấy những gì mà ảnh chụp không cho thấy?
2. Vì sao `block_third_party` là autouse, và test muốn bỏ qua thì làm thế nào?
3. Vì sao `customer_state` phải có scope session, và vì sao `.auth/` không được đưa lên git?
4. Vì sao chạy `pytest -n auto` an toàn với bộ test này?

---

## Day 7 – Playwright Implementation Lab: Prioritised End-to-End Workflows with Fixtures, Tracing & Network Control

Unit 2 · LO3 · Assignment/Lab · 150 phút · Hybrid

Bài lab tự động hóa các ưu tiên rủi ro của Unit 1 trên Playwright: 22 test trình duyệt trong lần chạy mặc định, thêm 2 test đăng nhập khi có tài khoản, 3 test `manual` (CAPTCHA) và 1 test `data_creating`.

### 1. Luồng nghiệp vụ theo ưu tiên (từ bảng rủi ro của Unit 1)

| Ưu tiên | Luồng | Risk | Test | Kỹ thuật Unit 2 |
| --- | --- | --- | --- | --- |
| P1 | Thêm vào giỏ, tổng tiền, đổi, xóa | R01 Critical (20) | 5 test trong `test_cart.py` + 3 test network | fixture `cart_with`, `expect_request`, giả lập lỗi 500 |
| P1 | Giỏ hàng → checkout | R02 Critical (15) | 1 test trong `test_checkout.py` | `expect(page).to_have_url` |
| P1 | Trang chi tiết, hàng hết | R03 High (12) | 2 test trong `test_catalog.py` | `css=[itemprop='name']`, `to_be_disabled()` |
| P1 | Đăng nhập, reset mật khẩu, phiên đã lưu | R04 High (12) | reset mật khẩu + 2 test auth; 2 test đăng nhập sai là `manual` (CAPTCHA) | storage state `customer_state` |
| P1 | Giá và tình trạng trên catalog | R05 High (12) | 7 trường hợp parametrize (mỗi sản phẩm một) + test mạng chậm | `parametrize`, giới hạn băng thông qua CDP |
| P2 | Kiểm tra lỗi đăng ký | R06 Medium (9) | 1 test `manual` (CAPTCHA) + 1 test `data_creating` | — |
| P2 | Tìm kiếm | R07 Medium (9) | 2 test trong `test_search.py` | thông báo không có kết quả |
| P2 | Dịch vụ bên thứ ba lỗi không làm hỏng việc mua hàng | R09 Medium (6) | 1 test network | route của `block_third_party` |

### 2. File

| File | Vai trò |
| --- | --- |
| `tests/test_<khu_vực>.py` | Mỗi khu vực một file; test nào cũng có marker rủi ro, bộ chạy và yêu cầu |
| `tests/conftest.py` | Fixture, kiểm soát network, trạng thái đăng nhập |
| `tests/test_network.py` | Chặn request, kiểm tra request, giả lập lỗi, mạng chậm |
| `tests/test_auth_state.py` | Phiên đăng nhập đã lưu và kiểm tra cô lập |
| `pages/` | Page Object chuyển từ Unit 1 |
| `pytest.ini` | base URL, tracing, báo cáo, bộ lọc marker mặc định, danh sách marker (`--strict-markers`) |

### 3. Chạy bài lab

```bash
cd ATEST03-unit2
pip install -r requirements.txt
playwright install chromium
pytest                              # bộ mặc định
pytest -m smoke                     # @smoke: thêm vào giỏ + checkout
pytest -n auto                      # chạy song song
pytest -m auth                      # cần SAUCE_EMAIL / SAUCE_PASSWORD
pytest -m critical                  # mọi test rủi ro Critical
pytest -m "critical and not negative"
```

### 4. Kết quả mong đợi

| Kiểm tra | Kết quả |
| --- | --- |
| `pytest` | 60 pass (22 trình duyệt + 38 framework), 6 bị lọc (`auth` ×2, `manual` ×3, `data_creating` ×1) |
| `pytest -n auto` | 60 pass |
| `pytest -m auth` (có tài khoản) | 2 pass |
| Test fail | `test-results/<test>/trace.zip`, ảnh, video |

Đã chạy trên store thật (2026-11-25). Store thật dạy bộ test hai điều: theme cần jQuery từ `ajax.googleapis.com` (bị chặn thì nút "Sold Out" không bao giờ hiện và Add to Cart thành post cả trang), và CAPTCHA của store chặn form đăng nhập và đăng ký.

### 5. Nhiệm vụ lab

1. Thêm test giả lập lỗi: trang giỏ hàng trả 503. Khách hàng phải thấy gì? Viết assertion.
2. Làm `test_catalog_loads_on_a_slow_network` fail bằng cách giảm timeout xuống 1 giây, mở trace và tìm request chậm.
3. Thêm một test tìm "sandals" với đúng marker yêu cầu và rủi ro. Chạy `pytest -m search_products` và kiểm tra nó chạy cùng các test khác của REQ-08.
4. Chạy `pytest -n auto` ba lần, so thời gian với chạy tuần tự.

---

## Day 8 – Topic Revision + Playwright Reliability & Maintainability: Failure Analysis, Flaky-Test Control, Tracing Diagnostics

Unit 2 · LO3 · Guides/Review (60 phút) + Concept/Lecture (120 phút) · Virtual

Day 8 khép lại cả hai Unit: phần A ôn tập Unit 2 so với Unit 1; phần B làm cho bộ test ổn định bằng quy trình phân tích lỗi dựa trên trace, chạy lặp để lộ test flaky, và checklist bảo trì.

### Phần A – Ôn tập (60 phút)

| Chủ đề | Unit 1 (Day 1–4) | Unit 2 (Day 5–7) |
| --- | --- | --- |
| Đặc tả | Feature Gherkin, tag | Test pytest thường; marker cho yêu cầu, rủi ro và bộ chạy |
| Động cơ | Selenium WebDriver | Playwright (tự chờ, context) |
| Setup / teardown | Hook của behave | Fixture của pytest (`conftest.py`) |
| Cô lập | Trình duyệt mới mỗi scenario | Context mới mỗi test |
| Chờ | `WebDriverWait` | Action tự chờ, `expect()` tự thử lại |
| Bằng chứng lỗi | Ảnh chụp | Trace + ảnh + video |
| Network | Không kiểm soát | Chặn, kiểm tra, giả lập lỗi, giả lập chậm |
| Đăng nhập | Đăng nhập qua UI mỗi lần | Dùng lại storage state đã lưu |
| Tốc độ | Tuần tự | Song song `-n auto` |
| Lọc | `behave --tags=@cart` | `pytest tests/test_cart.py`, `pytest -m add_to_cart` |

Câu hỏi ôn tập:

1. Unit 2 chạy nguyên vẹn những file nào của Unit 1, và vì sao điều đó có ích?
2. Kể hai rủi ro có kỹ thuật test thay đổi ở Unit 2 và giải thích.
3. Unit 2 xử lý những phát hiện review nào của Unit 1? (F3 độ ổn định; F7 và F8 lỗi chờ submit form, đã sửa ở cả hai Unit.)

### Phần B – Độ tin cậy và khả năng bảo trì (120 phút)

#### B1. Quy trình phân tích lỗi

```text
test fail
 ├─ 1. đọc thông điệp assertion trong reports/report.html
 ├─ 2. mở test-results/<test>/trace.zip   (playwright show-trace)
 │     ├─ tab Actions: step nào, locator nào, chờ bao lâu
 │     ├─ Snapshots: DOM trước/sau action
 │     └─ tab Network: mã trạng thái, request chậm hoặc lỗi
 ├─ 3. phân loại
 │     ├─ lỗi sản phẩm   → sai giá, sai tổng, trang lỗi → báo bug kèm trace
 │     ├─ lỗi test       → locator đổi, giả định sai → sửa trong pages/ hoặc trong test
 │     └─ môi trường     → store sập, captcha, mạng → chạy lại sau, gắn @manual nếu kéo dài
 └─ 4. chạy lại pass mà không sửa gì → flaky: xem B2
```

#### B2. Kiểm soát test flaky

Chạy cả bộ nhiều lần rồi so; mỗi lần ghi một file JUnit riêng:

```bash
pytest --junitxml=reports/run_1.xml
pytest --junitxml=reports/run_2.xml
pytest --junitxml=reports/run_3.xml
```

| Kết quả qua các lần chạy | Ý nghĩa | Hành động |
| --- | --- | --- |
| lần nào cũng pass | ổn định | — |
| lần nào cũng fail | lỗi thật hoặc test hỏng | phân tích trace (B1) |
| lúc pass lúc fail | flaky | cách ly, tìm nguyên nhân gốc |

Cách ly trong lúc tìm nguyên nhân (đã cài pytest-rerunfailures):

```python
@pytest.mark.flaky(reruns=2, reruns_delay=1)   # tạm thời, ghi số ticket trong commit
def test_something_flaky(...):
    ...
```

Chạy `pytest --reruns 1` cho cả bộ cũng làm lộ test flaky: báo cáo HTML đánh dấu chúng là "rerun". Chạy lại sẽ che giấu vấn đề, nên đây chỉ là nhãn tạm, không bao giờ để làm mặc định cho cả bộ.

Nguyên nhân hay gặp và cách code này xử lý:

| Nguyên nhân | Cách xử lý trong repo |
| --- | --- |
| Chờ cố định | Không dùng; chỉ `expect()` và `wait_for_url` |
| Action sau chạy trước khi request trước xong | `BasePage.submit()` chờ chuyển trang sau mỗi nút submit form; thêm vào giỏ còn chờ response `/cart/add` (phát hiện F7, F8 của Unit 1: ảnh lỗi cho thấy giỏ hàng cũ) |
| Script bên thứ ba | Fixture autouse `block_third_party` |
| Trạng thái dùng chung giữa các test | Mỗi test một context; `test_auth_state_does_not_leak_into_other_tests` |
| Selector theo vị trí | Không dùng; chỉ role, text và thuộc tính ổn định |

#### B3. Kiểm tra độ ổn định trước khi commit

Lệnh tìm nhanh (PowerShell; trong Git Bash dùng `grep -rnE`):

```powershell
Select-String -Path tests\*.py, pages\*.py -Pattern 'wait_for_timeout|time\.sleep'   # chờ cố định
Select-String -Path tests\*.py, pages\*.py -Pattern 'force=True'                     # bấm cưỡng ép
Select-String -Path tests\*.py -Pattern ':nth-child|nth=|\.nth\('                     # selector theo vị trí
```

| Quy tắc | Lý do |
| --- | --- |
| Không `wait_for_timeout(` / `time.sleep(` | Chờ cố định vừa chậm vừa vẫn flaky |
| Không `force=True` | Che đi phần tử mà người dùng không bấm được |
| Không selector theo vị trí trong test | Hỏng khi bố cục thay đổi |
| Không CSS/XPath thô trong test | Locator phải nằm trong `pages/` |
| Test nào cũng có marker mức rủi ro (`critical`, `high`, `medium`) và đúng một marker yêu cầu | Giữ `pytest -m critical` và `pytest -m <yêu_cầu>` đầy đủ |

#### B4. Tiêu chí bảo trì (checklist)

- [ ] Yêu cầu REQ-01 … REQ-08 nào cũng có test: `pytest -m <yêu_cầu> --collect-only -q`
- [ ] Test đọc giống yêu cầu: thao tác và kiểm tra qua page object, không URL hay CSS trong test
- [ ] Không có locator ngoài `pages/`
- [ ] Test nào cũng có docstring, `# Test data`, rồi chỉ các khối `with step(...)`; method page nào cũng có docstring dưới banner `# Scope:` (test framework)
- [ ] Không chờ cố định, không `force=True` (lệnh tìm ở B3 không ra kết quả)
- [ ] 0 test flaky trong 3 lần chạy liên tiếp (B2)
- [ ] Mỗi lần fail đều có trace, ảnh và video
- [ ] Bộ test pass với `-n auto`
- [ ] Thông tin bí mật (`SAUCE_PASSWORD`, `.auth/`) không bao giờ đưa lên git

### Kết quả mong đợi

| Kiểm tra | Kết quả trên site giả lập |
| --- | --- |
| Lệnh tìm ở B3 | không có kết quả |
| 3 lần chạy `pytest` | mỗi lần 60 pass, 0 flaky |
| Cố ý làm fail | `trace.zip`, `test-failed-1.png`, `video.webm` trong `test-results/` |
