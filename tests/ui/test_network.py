"""Network control (Day 6-7): interception, request assertions, fault injection, throttling.

Third-party risk (manual in Unit 1): the shop keeps working when third-party services fail.
The request handling itself lives in api/ (CartApi, NetworkApi): these tests only act and check.
"""
import pytest
from playwright.sync_api import expect

pytestmark = [pytest.mark.network, pytest.mark.regression]


@pytest.mark.medium
@pytest.mark.add_to_cart
def test_third_party_calls_are_blocked_and_shop_still_works(shop, shop_api_in_browser, block_third_party, products,
                                                            step):
    """Third-party calls are aborted by the autouse block, and the shop still sells."""
    # Test data
    grey_jacket = products["Grey jacket"]
    third_party_url = "https://www.facebook.com/tr?probe=1"

    # Execution steps
    step_number = 1
    with step(step_number, "Open the home page"):
        shop.home.open_page()
    step_number += 1
    with step(step_number, "Verify a third-party call made from the page is blocked"):
        assert not shop_api_in_browser.network.can_page_reach(third_party_url), "third-party request was not blocked"
        assert any("facebook.com" in url for url in block_third_party)
    step_number += 1
    with step(step_number, "Add Grey jacket to the cart without the third-party services"):
        shop.product.open_product_page(grey_jacket["path-name"])
        shop.product.add_to_cart()
    step_number += 1
    with step(step_number, "Verify the cart has 1 item"):
        shop.cart.open_page()
        assert shop.cart.count_items_in_cart() == 1


@pytest.mark.critical
@pytest.mark.add_to_cart
def test_add_to_cart_posts_the_product_form(shop, shop_api_in_browser, products, step):
    """Add to Cart sends a POST to /cart/add that carries the product id."""
    # Test data
    striped_top = products["Striped top"]

    # Execution steps
    step_number = 1
    with step(step_number, "Open the product page of Striped top"):
        shop.product.open_product_page(striped_top["path-name"])
    step_number += 1
    with step(step_number, "Click Add to Cart and capture the /cart/add request"):
        with shop_api_in_browser.cart.capture_add_to_cart_request() as captured:
            shop.product.add_to_cart_button.click()
    step_number += 1
    with step(step_number, "Verify the request carries the product id"):
        carries_id = shop_api_in_browser.cart.request_carries_product_id(captured.value)
        assert carries_id, "add-to-cart POST carries no product id"


@pytest.mark.critical
@pytest.mark.negative
@pytest.mark.add_to_cart
def test_failed_add_to_cart_request_does_not_add_the_product(shop, shop_api_in_browser, products, step):
    """When the server answers 500 to Add to Cart, the cart stays empty."""
    # Test data
    noir_jacket = products["Noir jacket"]

    # Execution steps
    step_number = 1
    with step(step_number, "Make every add-to-cart request get HTTP 500 (fault injection)"):
        shop_api_in_browser.cart.answer_add_to_cart_with_error(500)
    step_number += 1
    with step(step_number, "Open the product page of Noir jacket and click Add to Cart"):
        shop.product.open_product_page(noir_jacket["path-name"])
        shop.product.add_to_cart_button.click()
    step_number += 1
    with step(step_number, "Restore the network and verify the cart is empty"):
        shop_api_in_browser.cart.stop_answering_add_to_cart()
        shop.cart.open_page()
        expect(shop.cart.quantity_boxes).to_have_count(0)


@pytest.mark.high
@pytest.mark.browse_catalog
@pytest.mark.only_browser("chromium")
def test_catalog_loads_on_a_slow_network(shop, shop_api_in_browser, products, step):
    """On a slow network (400 ms latency, ~1.5 Mbit/s) the catalog still loads with prices."""
    # Test data
    bronze_sandals = products["Bronze sandals"]

    # Execution steps
    step_number = 1
    with step(step_number, "Throttle the network: 400 ms latency, 190 kB/s down, 90 kB/s up"):
        shop_api_in_browser.network.throttle_network(latency_ms=400, download_bytes_per_second=190_000,
                                                     upload_bytes_per_second=90_000)
    step_number += 1
    with step(step_number, "Open the catalog"):
        shop.catalog.open_page()
    step_number += 1
    with step(step_number, "Verify Bronze sandals shows £39.99 (allowing 15 s)"):
        expect(shop.catalog.product_tile(bronze_sandals["path-name"])).to_contain_text("£39.99", timeout=15_000)
