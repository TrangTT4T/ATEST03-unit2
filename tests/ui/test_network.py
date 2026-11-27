"""Network control (Day 6-7): interception, request assertions, fault injection, throttling.

Third-party risk (manual in Unit 1): the shop keeps working when third-party services fail.
"""
import pytest
from playwright.sync_api import expect

pytestmark = [pytest.mark.network, pytest.mark.regression]

PROBE_THIRD_PARTY = """() => fetch('https://www.facebook.com/tr?probe=1').then(() => false, () => true)"""
SLOW_NETWORK = {"offline": False, "latency": 400, "downloadThroughput": 190_000, "uploadThroughput": 90_000}


@pytest.mark.medium
@pytest.mark.add_to_cart
def test_third_party_calls_are_blocked_and_shop_still_works(shop, page, block_third_party, products, step):
    """Third-party calls are aborted by the autouse route, and the shop still sells."""
    # Test data
    grey_jacket = products["Grey jacket"]

    # Execution steps
    with step("Open the home page"):
        shop.home.open_page()
    with step("Verify a third-party call made from the page is blocked"):
        failed = page.evaluate(PROBE_THIRD_PARTY)
        assert failed, "third-party request was not blocked"
        assert any("facebook.com" in url for url in block_third_party)
    with step("Add Grey jacket to the cart without the third-party services"):
        shop.product.open_product_page(grey_jacket["path-name"])
        shop.product.add_to_cart()
    with step("Verify the cart has 1 item"):
        shop.cart.open_page()
        assert shop.cart.count_items_in_cart() == 1


@pytest.mark.critical
@pytest.mark.add_to_cart
def test_add_to_cart_posts_the_product_form(shop, page, products, step):
    """Add to Cart sends a POST to /cart/add that carries the product id."""
    # Test data
    striped_top = products["Striped top"]

    # Execution steps
    with step("Open the product page of Striped top"):
        shop.product.open_product_page(striped_top["path-name"])
    with step("Add to cart and capture the /cart/add request"):
        with page.expect_request(lambda r: "/cart/add" in r.url and r.method == "POST") as request_info:
            shop.product.add_to_cart_button.click()
    with step("Verify the request carries the product id"):
        body = request_info.value.post_data or ""  # multipart (FormData) or url-encoded, depending on the theme
        assert 'name="id"' in body or "id=" in body, "add-to-cart POST carries no product id"


@pytest.mark.critical
@pytest.mark.negative
@pytest.mark.add_to_cart
def test_failed_add_to_cart_request_does_not_add_the_product(shop, page, products, step):
    """When the server answers 500 to Add to Cart, the cart stays empty."""
    # Test data
    noir_jacket = products["Noir jacket"]

    # Execution steps
    with step("Make the server answer 500 to every add-to-cart call (fault injection)"):
        page.route("**/cart/add*", lambda route: route.fulfill(status=500, body="Internal Server Error"))
    with step("Open the product page of Noir jacket and click Add to Cart"):
        shop.product.open_product_page(noir_jacket["path-name"])
        shop.product.add_to_cart_button.click()
    with step("Restore the network and verify the cart is empty"):
        page.unroute("**/cart/add*")
        shop.cart.open_page()
        expect(shop.cart.quantity_boxes).to_have_count(0)


@pytest.mark.high
@pytest.mark.browse_catalog
@pytest.mark.only_browser("chromium")
def test_catalog_loads_on_a_slow_network(shop, page, context, products, step):
    """On a slow network (400 ms latency, ~1.5 Mbit/s) the catalog still loads with prices."""
    # Test data
    bronze_sandals = products["Bronze sandals"]

    # Execution steps
    with step("Throttle the network through the Chromium DevTools protocol"):
        cdp = context.new_cdp_session(page)
        cdp.send("Network.enable")
        cdp.send("Network.emulateNetworkConditions", SLOW_NETWORK)
    with step("Open the catalog"):
        shop.catalog.open_page()
    with step("Verify Bronze sandals shows £39.99 (allowing 15 s)"):
        expect(shop.catalog.product_tile(bronze_sandals["path-name"])).to_contain_text("£39.99", timeout=15_000)
