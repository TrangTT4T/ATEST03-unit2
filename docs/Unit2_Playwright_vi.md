# Unit 2 – Tự động hoá End-to-End với Playwright (Swag Labs)

pytest + Playwright (pytest-playwright) · Ứng dụng được test: https://www.saucedemo.com (Swag Labs) · Code: `ATEST03-unit2/`

Unit 2 dùng Playwright thuần: test pytest điều khiển page object, không có lớp Gherkin (BDD là chủ đề của Unit 1; BDD trên Playwright là mock project ở Unit 5). Bộ test được dựng ở Day 5, sau đó có thêm tracing, lưu phiên đăng nhập và chạy song song (Day 6), được áp vào các luồng ưu tiên trong buổi lab (Day 7), và được làm cho ổn định bằng phân tích lỗi và kiểm soát test chập chờn (Day 8). Mọi thứ chạy bằng lệnh `pytest`.

Vì sao dùng Swag Labs: phiên bản đầu của unit này test store Shopify của Unit 1 (sauce-demo.myshopify.com). Lớp bảo vệ Cloudflare và giới hạn request của store đó (HTTP 429, "Just a moment...") chặn các test trình duyệt trên một số mạng, mà kiểm tra chống bot thì không bao giờ được vượt qua. Swag Labs là shop demo làm ra để luyện test tự động: không chặn bot, không giới hạn request, các phần tử có thuộc tính `data-test`, tài khoản demo ghi sẵn trên trang đăng nhập.

| Ngày | Nội dung | LO | Hình thức | Phút | Định dạng |
| --- | --- | --- | --- | --- | --- |
| Day 5 | Kiến trúc Playwright, browser context, locator, fixture, assertion, cô lập test | LO3 | Concept/Lecture | 120 | Virtual |
| Day 6 | Tracing, trạng thái đăng nhập, chạy song song, mẫu báo cáo | LO3 | Concept/Lecture | 120 | Virtual |
| Day 7 | Lab Playwright: các luồng end-to-end ưu tiên với fixture và tracing | LO3 | Assignment/Lab | 150 | Hybrid |
| Day 8 | Ôn tập | LO3 | Guides/Review | 60 | Virtual |
| Day 8 | Độ tin cậy và khả năng bảo trì: phân tích lỗi, kiểm soát test chập chờn, chẩn đoán bằng trace, độ ổn định | LO3 | Concept/Lecture | 120 | Virtual |

Nội dung: Day 5 – Kiến trúc · Day 6 – Tracing, đăng nhập, song song · Day 7 – Lab · Day 8 – Ôn tập + độ tin cậy

```text
ATEST03-unit2/
├── pytest.ini                   # base_url, tracing, báo cáo, marker (--strict-markers)
├── requirements.txt
├── .env.example                 # SWAG_USERNAME, SWAG_LOCKED_OUT_USERNAME, SWAG_PASSWORD; chép thành .env (git bỏ qua)
├── dataset/                     # dữ liệu test, mỗi khu vực một file JSON (Helper.read_test_data("<khu vực>"))
│   ├── products.json            #   6 sản phẩm: id, giá, mô tả
│   ├── login.json               #   các lần đăng nhập bị từ chối và thông báo lỗi
│   ├── catalog.json             #   4 cách sắp xếp
│   ├── cart.json                #   các ca thêm / xoá
│   └── checkout.json            #   tổng tiền ở trang overview (item total, thuế, total), trường bắt buộc và lỗi
├── pages/                       # Page Object: mỗi file một class, locator XPath ở cuối class
│   ├── base_page.py             #   BasePage: find_element(s), click/type/select, chờ, header, menu bên
│   ├── login_page.py  inventory_page.py  product_page.py  cart_page.py
│   └── checkout_information_page.py  checkout_overview_page.py  checkout_complete_page.py
├── tests/
│   ├── conftest.py              # fixture: products, accounts, shop, logged_in_shop, fill_cart, phiên đã lưu, step
│   ├── test_login.py  test_catalog.py  test_cart.py  test_checkout.py   # mỗi khu vực một file
│   └── test_auth_state.py       # phiên đăng nhập đã lưu + kiểm tra cô lập
├── helper_utility/helpers.py    # class Helper: by_locator(), read_test_data(), money_to_float(), dữ liệu Faker
├── helper_utility/pdf_receipt.py  # class PdfReceipt: đọc PDF đơn hàng thành từng trường (pypdf)
└── helper_utility/steps.py      # fixture `step`: bước đánh số -> bước Allure + nhóm trong trace
```

### Yêu cầu và rủi ro

| Yêu cầu | Marker | Rủi ro | Mức |
| --- | --- | --- | --- |
| REQ-01 Thêm sản phẩm vào giỏ | `add_to_cart` | R01 Giỏ hàng sai | Critical |
| REQ-02 Xoá sản phẩm khỏi giỏ | `update_cart` | R01 Giỏ hàng sai | Critical |
| REQ-03 Checkout: thông tin, tổng tiền, hoàn tất đơn | `checkout` | R02 Sai tổng tiền hoặc mất đơn | Critical |
| REQ-04 Thông tin sản phẩm đúng | `product_details` | R03 Trang sản phẩm khác danh sách | High |
| REQ-05 Đăng nhập, đăng xuất an toàn | `secure_login` | R04 Người không có quyền vào được, hoặc người dùng hợp lệ không vào được | High |
| REQ-06 Xem và sắp xếp danh sách sản phẩm | `browse_catalog` | R05 Sai tên hoặc giá trong danh sách (High); R07 Sắp xếp sai (Medium) | High / Medium |

---

## Day 5 – Kiến trúc Playwright: Browser Context, Locator, Fixture, Assertion & Cô lập

Unit 2 · LO3 · Concept/Lecture · 120 phút · Virtual

Unit 2 giữ cách làm của Unit 1 (yêu cầu, rủi ro, file dữ liệu, page object) và đổi công cụ: test pytest thuần điều khiển page object Playwright, marker thay tag Gherkin, fixture pytest thay hook của behave.

### 1. Phần kế thừa từ Unit 1, phần mới

| Unit 1 (behave + Selenium) | Unit 2 (pytest + Playwright) | Trạng thái |
| --- | --- | --- |
| Các scenario `*.feature` | Mỗi scenario là một test pytest trong `tests/test_<khu_vực>.py`; bảng Examples thành `@pytest.mark.parametrize` trên file dữ liệu | Viết lại thành test thuần |
| Tag yêu cầu `@add_to_cart` … | Marker `@pytest.mark.add_to_cart` …, khai báo trong `pytest.ini` | Kế thừa |
| `dataset/*.json` | Mỗi khu vực một file JSON, đọc bằng `Helper.read_test_data("<khu vực>")` | Kế thừa |
| Tag `@critical`, `@smoke`, `@negative` | Marker cùng tên: `pytest -m smoke`; khu vực là file: `pytest tests/test_cart.py` | Kế thừa |
| Page Object, locator XPath ở cuối class, `Helper.by_locator` | Cùng bố cục; `Locator` của Playwright thay `WebElement` | Chuyển sang |
| Hook trong `environment.py` | Fixture trong `tests/conftest.py` | Thay thế |
| Chờ tường minh `WebDriverWait` | Thao tác tự chờ + `expect()` tự thử lại | Thay thế |
| Trình duyệt mới cho mỗi scenario | **Browser context** mới cho mỗi test (rẻ hơn nhiều) | Cải tiến |
| Chụp màn hình khi fail | Ảnh + video + **trace** khi fail | Mở rộng (Day 6) |
| — | Lưu phiên đăng nhập, chạy song song | Mới (Day 6) |

### 2. Kiến trúc Playwright

```text
pytest session
└── playwright  (tiến trình driver, mỗi worker một cái)
    └── browser  (Chromium / Firefox / WebKit, mỗi worker một cái, scope session)
        └── context  (mỗi test một cái: cookie, localStorage riêng → đăng nhập riêng, giỏ riêng)
            └── page  (mỗi test một tab)
```

Tạo một context chỉ mất vài mili giây, nên test nào cũng bắt đầu ở trạng thái chưa đăng nhập, giỏ trống, mà không phải mở lại trình duyệt. Swag Labs giữ đăng nhập trong cookie (`session-username`) và giỏ hàng trong localStorage (`cart-contents`): cả hai thuộc về context, nên không test nào thấy giỏ của test khác.

### 3. Locator

Swag Labs gắn thuộc tính `data-test` lên các phần tử, làm riêng cho test tự động. Thuộc tính này không đổi khi bố cục hay chữ trên trang thay đổi, nên được ưu tiên trước:

| Ưu tiên | Locator (XPath) | Ví dụ trong `pages/` |
| --- | --- | --- |
| 1 | Thuộc tính `data-test` | `//*[@data-test='checkout']`, `//*[@data-test='shopping-cart-badge']`, `//*[@data-test='error']` |
| 2 | Id | `//*[@id='react-burger-menu-btn']` (nút menu không có `data-test`) |
| 3 | Giới hạn trong phần tử cha theo chữ | `//*[@data-test='inventory-item'][.//*[@data-test='inventory-item-name' and normalize-space()='{}']]//button` — nút của một thẻ sản phẩm |
| 4 | Chữ trên nút, trong phạm vi đó | `…//button[normalize-space()='Remove']` |
| Không bao giờ | Vị trí | `(//button)[3]`, `//div[2]/a` |

#### Locator và các method riêng của BasePage (cùng bố cục với Unit 1)

Locator là chuỗi XPath mô tả phần tử, gom dưới một dòng comment ghi khu vực của trang; locator dạng mẫu dùng `{}` và `.format()`:

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

`Helper.by_locator()` (`helper_utility/helpers.py`, cùng các prefix như Unit 1) đổi locator thành selector của Playwright:

| Locator | Selector Playwright |
| --- | --- |
| `//*[@data-test='checkout']` (không prefix: cách page viết) | `xpath=//*[@data-test='checkout']` |
| `id=checkout` hoặc `id:checkout` | `id=checkout` |
| `name=user-name` | `xpath=//*[@name='user-name']` |
| `link=About` / `partial link=Abo` | `xpath=//a[normalize-space()='…']` / `xpath=//a[contains(normalize-space(),'…')]` |
| `css=#checkout`, `tag_name=h3`, `class_name=error`, `xpath=//h3` | `css=#checkout`, `css=h3`, `css=.error`, `xpath=//h3` |
| `foo=bar` | `ValueError: Element locator with prefix 'foo' is not supported: 'foo=bar'` |

Page không bao giờ gọi `self.page`: page gọi các method của `BasePage`, các method này ghi log thao tác (hiện trong báo cáo của test fail, mật khẩu hiện `***`):

| Nhóm | Method |
| --- | --- |
| Điều hướng | `open_page(path)`, `wait_until_url_contains(fragment)`, `wait_until_url_ends_with(suffix)` |
| Locator | `find_element(locator)` (phần tử đầu), `find_elements(locator)` (mọi phần tử), `get_texts(locator)` — locator của Playwright là lazy: chỉ chờ khi một thao tác hay `expect()` dùng đến |
| Thao tác | `click_element`, `type_text(locator, text, secret=False)`, `select_option(locator, label)` |
| Trạng thái | `is_element_visible(locator, timeout=0)` — chờ trạng thái tối đa `timeout` giây, không bao giờ sleep cố định |
| Header | `page_title`, `cart_badge`, `get_cart_badge_count()`, `open_cart()` |
| Menu bên | `logout()`, `reset_app_state()` |

Swag Labs là ứng dụng một trang (single-page app): bấm nút thì địa chỉ đổi mà không tải trang mới. Vì vậy page chờ địa chỉ (`wait_until_url_contains("/cart.html")`), không chờ tải trang. Mọi thao tác chờ và thao tác chính chạy trong `_report_timeout()`: khi Playwright hết thời gian chờ thì log một dòng ERROR và nói test đang làm gì, ở trang nào ("Clicking '//*[@data-test='checkout']' timed out on https://www.saucedemo.com/cart.html"), kèm call log của Playwright.

Không method nào trả về page để gọi nối tiếp: gọi method rồi dùng page, viết hai dòng. Chỉ giữ method mà page hoặc test có dùng.

### 4. Fixture (`tests/conftest.py`)

| Fixture | Scope | Thay cho phần nào ở Unit 1 | Làm gì |
| --- | --- | --- | --- |
| `browser`, `context`, `page` | session / test / test | `before_scenario` + `after_scenario` | pytest-playwright cung cấp |
| `browser_context_args` | session | option trong `_make_driver()` | Viewport 1366×900, locale en-US |
| `products` | session | `before_all` đọc JSON | `Helper.read_test_data("products")` |
| `swag_accounts` | session | — | Tài khoản demo trong `.env` theo tên (`standard-user`, `locked-out-user`, `problem-user` …); thiếu biến cần thiết thì bỏ qua test với thông báo rõ ràng |
| `shopper` | session | — | Tài khoản của lần chạy: `--account` (mặc định `standard-user`) |
| `accounts` | test | — | Mọi lần đăng nhập trong `dataset/login.json` theo tên: tài khoản demo + tài khoản bịa bằng Faker: `unknown-user`, `wrong-password`, `missing-username`, `missing-password` |
| `checkout_information` | test | — | Khách hàng bịa cho form checkout (Faker) |
| `shop` | test | `Helper.create_page_object()` | Mọi Page Object gắn với page của test: `shop.login`, `shop.inventory`, `shop.cart` … |
| `logged_in_shop` | test | step `Given I am logged in` | `shop`, đã đăng nhập bằng tài khoản `--account` qua cookie đã lưu (không qua form), đang ở trang sản phẩm |
| `fill_cart` | test | step `Given ... in the cart` | Factory: `fill_cart(["Sauce Labs Backpack", "Sauce Labs Onesie"])` |
| `saved_login_state` | test (dựa trên bản ghi của session) | — | Đăng nhập một lần mỗi phiên chạy, làm mới sau 9 phút (Day 6) |
| `step` | test | — | Bước đánh số (mục 5) |

```python
@pytest.fixture
def fill_cart(logged_in_shop):
    """Factory fixture: fill_cart(["Sauce Labs Backpack", ...]) adds the products from the products page."""
    def add_products(product_names: list[str]):
        logged_in_shop.inventory.add_products_to_cart(product_names)
        return logged_in_shop
    return add_products
```

### 4b. Dữ liệu test (`dataset/`) và dữ liệu sinh ngẫu nhiên (Faker)

Test không tự chứa giá trị: mỗi khu vực một file JSON, đọc bằng `Helper.read_test_data("<khu vực>")`, và test có parametrize chạy một lần cho mỗi ca. Thêm ca mới là thêm một dòng trong file, không phải viết code mới.

| File | Chứa | Dùng ở |
| --- | --- | --- |
| `products.json` | 6 sản phẩm: `id` (trang sản phẩm là `/inventory-item.html?id=<id>`), `price`, `description` | fixture `products`: danh sách, trang sản phẩm, giỏ, sắp xếp |
| `login.json` | `rejected`: tên tài khoản → lỗi (user không tồn tại, sai mật khẩu, user bị khoá, thiếu username, thiếu mật khẩu); lỗi "chưa đăng nhập" | `test_login.py`, `test_auth_state.py` |
| `catalog.json` | `sorting`: 4 lựa chọn, sắp theo tên hoặc giá, tăng hoặc giảm | `test_catalog.py` |
| `cart.json` | `add` (danh sách sản phẩm), `remove` (sản phẩm + món cần xoá) | `test_cart.py` |
| `checkout.json` | `totals` (sản phẩm → item total, thuế 8%, total), `missing_information` (trường để trống → lỗi), tiêu đề xác nhận đơn, `pdf_receipt` (mẫu tên file, số trang, tiêu đề) | `test_checkout.py` |

```python
CART = Helper.read_test_data("cart")

@pytest.mark.parametrize("case", CART["add"], ids=[case["id"] for case in CART["add"]])
def test_add_products_to_the_cart(fill_cart, step, case):
    ...
```

Dữ liệu tài khoản không bao giờ nằm trong file được đẩy lên GitHub. Tài khoản demo của Swag Labs (ghi trên trang đăng nhập) nằm trong `.env`, git bỏ qua file này; `.env.example` chỉ có tên biến. Mọi dữ liệu khác do Faker tạo mới cho mỗi test: username không tồn tại, mật khẩu sai, khách hàng khi checkout.

`Helper` (`helper_utility/helpers.py`) là phần dùng chung của page và test:

| Nhóm | Method |
| --- | --- |
| Element finder | `by_locator()`: locator string → selector Playwright; prefix lạ thì báo `ValueError` |
| Dữ liệu test | `read_test_data(area)`: thiếu file thì báo `FileNotFoundError` kèm danh sách khu vực có sẵn |
| Giá tiền | `money_to_float("$1,120.00")` → 1120.0 (cả khi nằm trong câu: `"Item total: $29.99"` → 29.99) |
| Dữ liệu ngẫu nhiên | `random_checkout_information()`, `random_unregistered_login()`, `random_password()` |

### 5. Assertion

`expect()` tự thử lại tới khi điều kiện đúng hoặc hết thời gian chờ (5 giây), nên không cần viết lệnh chờ:

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
| `assert badge.text == "1"` sau khi chờ | `expect(shop.inventory.cart_badge).to_have_text("1")` |
| `assert error_text().strip()` | `expect(shop.login.error_message).to_have_text("Epic sadface: …")` |
| `assert not badge.is_displayed()` | `expect(shop.inventory.cart_badge).to_be_hidden()` |

#### Cấu trúc một test: dữ liệu test, rồi các bước được đánh số

Test nào cũng đọc theo cùng một khung: docstring nói test chứng minh điều gì, `# Test data` (chỉ gán biến), rồi `# Execution steps` — chỉ gồm các khối `with step(step_number, "..."):`. Test tự đếm bước giống mẫu ở công ty `with allure.step(f"Step {step_index}: ...")`: `step_number = 1` trước bước đầu, `step_number += 1` trước mỗi bước sau. Fixture `step` (`helper_utility/steps.py`) kiểm tra biến đếm — nhảy số hoặc quên `+= 1` (hai bước "Step 2") thì test dừng với `ValueError` rõ ràng — và biến mỗi khối thành:

| Ở đâu | Thấy gì |
| --- | --- |
| Báo cáo Allure | Test hiện thành danh sách "Step 1: … / Step 2: … / Step 3: …", bước fail tô đỏ; docstring là phần mô tả, marker là tag |
| Trace Viewer | Các click và wait của test fail được gom dưới tên bước |
| Báo cáo HTML / JUnit | Lỗi có thêm dòng `failed in Step 3: Open the cart and verify it holds …` |

Page object theo cùng ý: method được gom dưới banner ghi khu vực của trang, method public nào cũng có docstring, locator ở cuối class:

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

Cả hai quy tắc nằm trong checklist review (Day 8, B4).

### 5b. Các tài khoản demo khác (`--account`)

Swag Labs có sáu tài khoản demo; bốn tài khoản cố ý có lỗi. `pytest --account <tên>` (tuỳ chọn thêm trong `tests/conftest.py` bằng `pytest_addoption`) làm `logged_in_shop` và test smoke đăng nhập dùng tài khoản đó; đầu lần chạy ghi rõ tên tài khoản. Khi đó cùng 43 test trở thành công cụ tìm lỗi:

| Tài khoản (`--account`) | Kết quả | Các test fail cho thấy |
| --- | --- | --- |
| `standard-user` (mặc định) | 42 pass, 1 xfailed | — |
| `performance-glitch-user` | 42 pass, 1 xfailed, chậm hơn khoảng 3,5 lần | đăng nhập mất vài giây; cơ chế tự chờ xử lý được, không test nào cần tăng timeout |
| `visual-user` | 8 fail | trang danh sách hiện sai giá (vd. Backpack $88.21 thay vì $29.99), nên sắp theo giá cũng sai; tổng tiền ở giỏ và checkout vẫn đúng |
| `error-user` | 15 fail | sắp xếp không có tác dụng; chỉ thêm được 3/6 sản phẩm; nút Remove ở trang danh sách không có tác dụng; trang sản phẩm không có mô tả; ô họ (last name) không nhận chữ, vậy mà form vẫn cho đi tiếp; bấm Finish không hoàn tất đơn |
| `problem-user` | 19 fail | sắp xếp không có tác dụng; bấm tên sản phẩm mở nhầm trang (Fleece Jacket: "ITEM NOT FOUND"); chỉ thêm được 3 sản phẩm, nút Remove ở trang danh sách không có tác dụng; gõ họ (last name) thì đè lên tên (first name), nên checkout không qua được form thông tin |

### 6. Kiểm tra cô lập

`tests/test_auth_state.py::test_login_state_does_not_leak_into_other_tests` chứng minh test dùng `page` mặc định không ở trạng thái đăng nhập, kể cả khi một test khác trong cùng phiên chạy dùng phiên đăng nhập đã lưu.

### 7. Chạy

```bash
cd ATEST03-unit2
pip install -r requirements.txt
playwright install chromium
cp .env.example .env              # điền tài khoản demo ghi trên https://www.saucedemo.com
pytest --collect-only -q          # 46 test
pytest -m smoke                   # 3 test: đăng nhập, thêm vào giỏ, hoàn tất đơn
pytest --headed --slowmo 300      # xem trình duyệt chạy
```

### 8. Câu hỏi ôn tập

1. Vì sao browser context mới cô lập test giống như trình duyệt mới, và vì sao nó rẻ hơn?
2. Swag Labs giữ giỏ hàng ở đâu, và vì sao điều đó làm context là đơn vị cô lập phù hợp?
3. Viết lại `self.wait.until(lambda d: badge().text == "2")` thành assertion của Playwright.
4. Vì sao `//*[@data-test='checkout']` tốt hơn `//button[2]` hay `//button[text()='Checkout']`?

---

## Day 6 – Tracing, Trạng thái đăng nhập, Chạy song song & Báo cáo

Unit 2 · LO3 · Concept/Lecture · 120 phút · Virtual

Day 6 thêm những thứ Unit 1 chưa có: trace đầy đủ cho mọi test fail, dùng lại phiên đăng nhập và chạy song song.

### 1. Tracing (mở rộng từ việc chụp màn hình khi fail ở Unit 1)

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
| Chỉ thấy màn hình cuối | Mọi thao tác, DOM trước/sau, console, network, dòng code, các bước đánh số |

```bash
playwright show-trace test-results/<test-folder>/trace.zip   # mở một trace
pytest --tracing on                                          # giữ trace cho mọi test khi debug
```

### 2. Lỗi đã biết: `xfail(strict=True)`

**Phát hiện F1:** sau khi bấm **Reset App State** (menu bên), giỏ đã trống — badge biến mất — nhưng nút của sản phẩm vẫn ghi "Remove" thay vì "Add to cart". Khách thấy sản phẩm như đang "nằm trong giỏ" dù thực tế không có.

```python
@pytest.mark.xfail(strict=True, reason="Finding F1: after Reset App State the cart is empty but the product's button "
                                        "still says Remove (checked 2026-11-27)")
def test_reset_app_state_empties_the_cart_and_resets_the_buttons(fill_cart, step):
```

Test ghi hành vi đúng và được đánh dấu `xfail(strict=True)` kèm mô tả phát hiện: báo cáo liệt kê nó là lỗi đã biết, và khi shop sửa xong thì test pass, `strict` làm lần chạy fail để nhắc bỏ marker. Chạy bỏ qua marker để xem bước fail: `pytest --runxfail tests/test_cart.py -k reset`.

### 2b. Tải file: biên lai PDF

Trang hoàn tất đơn có nút **Generate PDF order** tải về biên lai (`swag-labs-order-<ngày>_<giờ>.pdf`). `BasePage.click_and_download(locator, folder)` bọc `expect_download()` của Playwright và lưu file với tên gốc vào `tmp_path` của pytest; `CheckoutCompletePage.download_pdf_order(folder)` dùng method này.

`PdfReceipt` (`helper_utility/pdf_receipt.py`, pypdf) đọc PDF thành từng trường, nên test so dữ liệu chứ không so nguyên văn:

| Trường | So với |
| --- | --- |
| tên file, số trang, tiêu đề | `pdf_receipt` trong `checkout.json` (mẫu tên file, 1 trang, "Order Receipt") |
| ngày đặt | hôm nay |
| người nhận: tên, mã bưu điện | khách hàng Faker mà test đã nhập |
| sản phẩm: tên → giá | giá trong `products.json` của các sản phẩm test đã đặt (không thừa dòng nào) |
| item total, thuế, total | ca tương ứng trong `totals` của `checkout.json` |
| lời cảm ơn | `order_complete_header` trong `checkout.json` |

Chữ trích từ PDF bị dãn ở vài chỗ ("T ax $ 3.20", "Sauce Labs Bolt T -Shirt"), nên `PdfReceipt` so nhãn và tên sản phẩm sau khi bỏ khoảng trắng.

### 3. Trạng thái đăng nhập: đăng nhập một lần, dùng lại cookie

Ở Unit 1, scenario nào cần đăng nhập cũng phải gõ tài khoản. Ở đây form login chỉ được dùng **một lần cho mỗi phiên chạy** (mỗi worker một lần khi chạy `-n`): `saved_login_state` đăng nhập, lưu cookie và localStorage bằng `context.storage_state()`, rồi test nào chỉ cần ở trạng thái đăng nhập (`logged_in_shop`) sẽ nạp cookie đó vào context riêng của mình và mở thẳng trang sản phẩm:

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

| Kiểm tra (chạy tuần tự) | Kết quả |
| --- | --- |
| Test bắt đầu ở trạng thái đăng nhập (`logged_in_shop`) | 37, tất cả dùng cookie đã lưu |
| Số lần bấm nút Login | 7: một lần để lưu phiên + 6 test về chính việc đăng nhập (đăng nhập đúng, 5 kiểu bị từ chối), các test này buộc phải đi qua form |
| Cookie phiên của Swag Labs | hết hạn 10 phút sau khi đăng nhập: phiên đã lưu được làm mới khi quá 9 phút (đã thử đặt giới hạn 3 giây: phiên đăng nhập lại sau mỗi vài giây, các test giỏ hàng và checkout vẫn pass) |

Chỉ chép cookie: Swag Labs giữ giỏ hàng trong localStorage, nên test nào cũng vẫn bắt đầu với giỏ trống. `tests/test_auth_state.py` (rủi ro R04) minh hoạ cách dùng file còn lại — tạo context mới với `storage_state=` — và kiểm tra `page` mặc định vẫn ở trạng thái chưa đăng nhập. `.auth/` chứa phiên đăng nhập: đã có trong `.gitignore`, không bao giờ commit.

### 4. Chạy song song

```bash
pytest -n auto        # pytest-xdist, mỗi CPU một worker
pytest -n 4
```

An toàn vì mỗi test có context riêng (Day 5) và không test nào phụ thuộc test khác. Swag Labs là site tĩnh, nên chạy song song không làm nặng máy chủ dùng chung nào.

### 5. Mẫu báo cáo

| Báo cáo | Do đâu tạo | Đường dẫn |
| --- | --- | --- |
| HTML | pytest-html (`--html` trong `pytest.ini`) | `reports/report.html` |
| JUnit XML | `--junitxml` | `reports/junit.xml` |
| Kết quả Allure (bước đánh số) | allure-pytest (`--alluredir`); xem bằng `allure serve reports/allure-results` (Allure CLI) | `reports/allure-results/` |
| Trace, ảnh, video | pytest-playwright | `test-results/` |

Test nào cũng mang một marker yêu cầu (`@pytest.mark.add_to_cart` …) và một marker mức rủi ro: `pytest -m add_to_cart` chạy một yêu cầu, `pytest -m critical --collect-only -q` liệt kê mọi test rủi ro Critical, và marker hiện trong báo cáo HTML. `-rfEs` trong `pytest.ini` liệt kê test fail, lỗi và test bị bỏ qua (kèm lý do) ở cuối lần chạy.

### 6. Câu hỏi ôn tập

1. Trace cho thấy những gì mà ảnh chụp màn hình không thấy?
2. Vì sao F1 là `xfail(strict=True)` chứ không skip hay xoá test?
3. Vì sao `saved_login_state` phải có scope session, và vì sao `.auth/` không được đưa vào git?
4. Vì sao `pytest -n auto` an toàn với bộ test này?

---

## Day 7 – Lab Playwright: Các luồng End-to-End ưu tiên với Fixture & Tracing

Unit 2 · LO3 · Assignment/Lab · 150 phút · Hybrid

Buổi lab tự động hoá các ưu tiên theo rủi ro trên Playwright: 46 test, tất cả đều chạy mặc định (Swag Labs không cần loại test manual hay tạo dữ liệu thật).

### 1. Các luồng ưu tiên (từ bảng rủi ro)

| Ưu tiên | Luồng | Rủi ro | Test | Kỹ thuật Unit 2 |
| --- | --- | --- | --- | --- |
| P1 | Thêm vào giỏ, xoá, giữ giỏ khi mua tiếp, reset | R01 Critical | `test_cart.py`: 10 test (ca trong `dataset/cart.json`), 1 test `xfail` (F1) | factory `fill_cart`, `parametrize`, `to_be_hidden()` |
| P1 | Checkout: thông tin, tổng tiền, hoàn tất | R02 Critical | `test_checkout.py`: 10 test (ca trong `dataset/checkout.json`), 3 test so biên lai PDF tải về | khách hàng Faker, `to_have_text` trên tổng tiền, `expect_download` + `PdfReceipt` |
| P1 | Trang sản phẩm = danh sách | R03 High | `test_catalog.py`: 6 ca (mỗi sản phẩm một) | `parametrize` trên `products.json` |
| P1 | Đăng nhập, đăng xuất, user bị khoá, phiên đã lưu | R04 High | `test_login.py` 8 test + `test_auth_state.py` 2 test | `accounts` từ `.env` + Faker, `saved_login_state` |
| P1 | Tên, mô tả, giá trong danh sách | R05 High | `test_catalog.py`: 6 ca | `product_card(name)` |
| P2 | Sắp xếp | R07 Medium | `test_catalog.py`: 4 ca (`dataset/catalog.json`) | thứ tự mong đợi tính từ `products.json` |

### 2. File

| File | Vai trò |
| --- | --- |
| `tests/test_<khu_vực>.py` | Mỗi khu vực một file; test nào cũng có marker rủi ro, bộ chạy và yêu cầu |
| `tests/conftest.py` | Fixture: dữ liệu, tài khoản, page object, shop đã đăng nhập, factory giỏ hàng, phiên đã lưu, bước |
| `tests/test_auth_state.py` | Phiên đăng nhập đã lưu và kiểm tra cô lập |
| `pages/` | Page Object, mỗi trang của shop một class |
| `dataset/` | Dữ liệu test, mỗi khu vực một file |
| `pytest.ini` | base URL, tracing, báo cáo, danh sách marker (`--strict-markers`) |

### 3. Chạy lab

```bash
cd ATEST03-unit2
pip install -r requirements.txt
playwright install chromium
cp .env.example .env                # điền tài khoản demo
pytest                              # cả bộ test
pytest -m smoke                     # đăng nhập + thêm vào giỏ + hoàn tất đơn
pytest -n auto                      # song song
pytest -m critical                  # mọi test rủi ro Critical
pytest -m "critical and not negative"
pytest tests/test_checkout.py       # một khu vực
```

### 4. Kết quả mong đợi

| Kiểm tra | Kết quả |
| --- | --- |
| `pytest` | 45 pass, 1 xfailed (phát hiện F1), khoảng 60 giây |
| `pytest -n 4` | 45 pass, 1 xfailed, khoảng 26 giây |
| `pytest` khi chưa có `.env` | mọi test cần tài khoản được bỏ qua, kèm tên biến cần điền |
| Test fail | `test-results/<test>/trace.zip`, ảnh, video |

Đã chạy trên www.saucedemo.com (2026-11-27).

### 5. Nhiệm vụ lab

1. Thêm một ca checkout ba sản phẩm vào `dataset/checkout.json` (tự tính thuế 8%). Test nào chạy ca đó mà không cần sửa code?
2. Làm `test_product_page_shows_the_same_name_description_and_price` fail bằng cách đổi một giá trong `products.json`, mở trace và tìm bước bị fail.
3. Thêm một ca đăng nhập cho `problem_user` (tài khoản demo đăng nhập được nhưng hiện sai ảnh): cần fixture nào và biến `.env` nào?
4. Chạy `pytest -n auto` ba lần, so thời gian với chạy tuần tự.

---

## Day 8 – Ôn tập + Độ tin cậy & khả năng bảo trì với Playwright: Phân tích lỗi, Kiểm soát test chập chờn, Chẩn đoán bằng Trace

Unit 2 · LO3 · Guides/Review (60 phút) + Concept/Lecture (120 phút) · Virtual

Day 8 khép lại cả hai unit: phần A ôn Unit 2 so với Unit 1, phần B làm bộ test ổn định bằng quy trình phân tích lỗi dựa trên trace, chạy lặp lại để lộ test chập chờn, và checklist bảo trì.

### Phần A – Ôn tập (60 phút)

| Chủ đề | Unit 1 (Day 1–4) | Unit 2 (Day 5–7) |
| --- | --- | --- |
| Đặc tả | Feature Gherkin, tag | Test pytest thuần; marker cho yêu cầu, rủi ro và bộ chạy |
| Engine | Selenium WebDriver | Playwright (tự chờ, context) |
| Chuẩn bị / dọn dẹp | Hook của behave | Fixture pytest (`conftest.py`) |
| Cô lập | Trình duyệt mới mỗi scenario | Context mới mỗi test |
| Chờ | `WebDriverWait` | Thao tác tự chờ, `expect()` tự thử lại |
| Bằng chứng khi fail | Ảnh chụp màn hình | Trace + ảnh + video |
| Đăng nhập | Đăng nhập qua UI mỗi lần | Form login một lần mỗi phiên chạy, sau đó dùng cookie đã lưu |
| Tốc độ | Tuần tự | Song song `-n auto` |
| Chọn test | `behave --tags=@cart` | `pytest tests/test_cart.py`, `pytest -m add_to_cart` |
| Ứng dụng | Store demo Shopify | Swag Labs (không chặn bot: xem phần mở đầu) |

Câu hỏi ôn tập:

1. Những phần nào của Unit 1 (file dữ liệu, bố cục page object, marker) giữ nguyên được, và vì sao điều đó có ích?
2. Vì sao Unit 2 chuyển từ store Shopify sang Swag Labs, và vì sao vượt qua kiểm tra chống bot không bao giờ là cách giải quyết?
3. Unit 2 xử lý những phát hiện review nào của Unit 1? (F3 độ ổn định: tự chờ và `expect()`; F7 và F8 race khi submit form: mọi click làm đổi trang đều chờ địa chỉ mới.)

### Phần B – Độ tin cậy và khả năng bảo trì (120 phút)

#### B1. Quy trình phân tích lỗi

```text
test fail
 ├─ 1. đọc thông báo assertion trong reports/report.html ("failed in Step N: ...")
 ├─ 2. mở test-results/<test>/trace.zip   (playwright show-trace)
 │     ├─ tab Actions: bước nào, locator nào, chờ bao lâu
 │     ├─ Snapshots: DOM trước/sau thao tác
 │     └─ tab Console: lỗi JavaScript của shop
 ├─ 3. phân loại
 │     ├─ lỗi sản phẩm   → sai tổng tiền, sai chữ trên nút → báo bug kèm trace, tạm xfail(strict)
 │     ├─ lỗi test       → locator đổi, giả định sai → sửa trong pages/ hoặc file dữ liệu
 │     └─ môi trường     → site sập, mạng, thiếu .env → chạy lại sau, hoặc sửa phần chuẩn bị
 └─ 4. nếu chạy lại không sửa gì mà pass → chập chờn: xem B2
```

#### B2. Kiểm soát test chập chờn

Chạy cả bộ vài lần rồi so sánh; mỗi lần ghi một file JUnit riêng:

```bash
pytest --junitxml=reports/run_1.xml
pytest --junitxml=reports/run_2.xml
pytest --junitxml=reports/run_3.xml
```

| Kết quả qua các lần chạy | Ý nghĩa | Việc cần làm |
| --- | --- | --- |
| lần nào cũng pass | ổn định | — |
| lần nào cũng fail | lỗi thật hoặc test hỏng | phân tích trace (B1) |
| lúc pass lúc fail | chập chờn | cách ly, tìm nguyên nhân gốc |

Cách ly trong lúc tìm nguyên nhân (đã cài pytest-rerunfailures):

```python
@pytest.mark.flaky(reruns=2, reruns_delay=1)   # temporary, with a ticket number in the commit
def test_something_flaky(...):
    ...
```

`pytest --reruns 1` cho cả lần chạy cũng làm lộ test chập chờn: báo cáo HTML đánh dấu chúng là "rerun". Chạy lại che giấu vấn đề, nên chỉ là nhãn tạm thời, không bao giờ là mặc định của bộ test.

Nguyên nhân gốc thường gặp và cách sửa trong code này:

| Nguyên nhân | Cách sửa trong repository này |
| --- | --- |
| Chờ cố định | Không dùng; chỉ `expect()` và `wait_for_url` |
| Thao tác tiếp theo chạy trước khi trang đổi xong | Mọi click làm đổi trang đều chờ địa chỉ mới (`wait_until_url_contains`); ứng dụng một trang không tải tài liệu mới, nên chờ load state sẽ trả về ngay |
| Trạng thái dùng chung giữa các test | Mỗi test một context (cookie riêng, giỏ trong localStorage riêng); `test_login_state_does_not_leak_into_other_tests` |
| Selector theo vị trí | Không dùng; chỉ thuộc tính `data-test` và chữ trong phạm vi |
| Giá trị trùng khi sắp xếp | Hai sản phẩm cùng giá ($15.99): sắp theo giá thì so danh sách giá, không so tên |

#### B3. Kiểm tra độ ổn định trước khi commit

Tìm nhanh (PowerShell; trong Git Bash dùng `grep -rnE`):

```powershell
Select-String -Path tests\*.py, pages\*.py -Pattern 'wait_for_timeout|time\.sleep'   # chờ cố định
Select-String -Path tests\*.py, pages\*.py -Pattern 'force=True'                     # click cưỡng ép
Select-String -Path tests\*.py -Pattern ':nth-child|nth=|\.nth\('                     # selector theo vị trí
```

| Quy tắc | Lý do |
| --- | --- |
| Không `wait_for_timeout(` / `time.sleep(` | Chờ cố định vừa chậm vừa vẫn chập chờn |
| Không `force=True` | Che mất phần tử mà người dùng không bấm được |
| Không selector theo vị trí trong test | Hỏng khi bố cục thay đổi |
| Không CSS/XPath trực tiếp trong test | Locator thuộc về `pages/` |
| Test nào cũng có marker mức rủi ro (`critical`, `high`, `medium`) và đúng một marker yêu cầu | Giữ cho `pytest -m critical` và `pytest -m <yêu cầu>` đầy đủ |

#### B4. Tiêu chí bảo trì (checklist)

- [ ] Yêu cầu REQ-01 … REQ-06 nào cũng có test: `pytest -m <yêu cầu> --collect-only -q`
- [ ] Test đọc như yêu cầu: thao tác và kiểm tra qua page object, không có URL hay locator trong test
- [ ] Không locator nào nằm ngoài `pages/`; giá trị test nằm trong `dataset/`, không nằm trong test
- [ ] Test nào cũng có docstring, `# Test data`, rồi chỉ các khối `with step(step_number, ...)`; method page nào cũng có docstring dưới banner `# Scope:` (review)
- [ ] Không chờ cố định, không `force=True` (các lệnh tìm ở B3 không ra kết quả)
- [ ] 0 test chập chờn qua 3 lần chạy liên tiếp (B2)
- [ ] Test fail nào cũng để lại trace, ảnh và video
- [ ] Bộ test pass với `-n auto`
- [ ] Tài khoản (`.env`) và phiên đăng nhập (`.auth/`) không bao giờ được commit

### Kết quả mong đợi

| Kiểm tra | Kết quả |
| --- | --- |
| Các lệnh tìm ở B3 | không có kết quả |
| Chạy tuần tự + chạy song song (`-n 4`) | mỗi lần 45 pass + 1 xfailed, 0 test chập chờn |
| Cố ý làm fail | `trace.zip`, `test-failed-1.png`, `video.webm` trong `test-results/` |
