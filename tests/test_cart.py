"""Cart (risk R01, Critical): add products, remove them, keep them while shopping.

The cases come from dataset/cart.json: a new case is a new line in that file, not new code.
Requirements: @add_to_cart (REQ-01), @update_cart (REQ-02).
"""
import pytest
from playwright.sync_api import expect

from helper_utility.helpers import Helper

pytestmark = pytest.mark.critical
CART = Helper.read_test_data("cart")


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


@pytest.mark.regression
@pytest.mark.add_to_cart
@pytest.mark.parametrize("case", CART["add"], ids=[case["id"] for case in CART["add"]])
def test_add_products_to_the_cart(fill_cart, step, case):
    """The badge counts the added products and the cart lists each of them (dataset/cart.json "add")."""
    # Execution steps
    step_number = 1
    with step(step_number, f"Add {len(case['products'])} products from the products page"):
        shop = fill_cart(case["products"])
    step_number += 1
    with step(step_number, f"Verify the cart badge shows {len(case['products'])}"):
        expect(shop.inventory.cart_badge).to_have_text(str(len(case["products"])))
    step_number += 1
    with step(step_number, "Open the cart and verify it lists exactly these products"):
        shop.inventory.open_cart()
        assert sorted(shop.cart.get_product_names()) == sorted(case["products"])


@pytest.mark.regression
@pytest.mark.add_to_cart
def test_add_a_product_from_its_product_page(logged_in_shop, step):
    """The product page's Add to cart button adds the product too."""
    # Test data
    bike_light = "Sauce Labs Bike Light"

    # Execution steps
    step_number = 1
    with step(step_number, f"Open the product page of {bike_light}"):
        logged_in_shop.inventory.open_product_page(bike_light)
    step_number += 1
    with step(step_number, "Click Add to cart"):
        logged_in_shop.product.add_to_cart()
    step_number += 1
    with step(step_number, "Verify the badge shows 1 and the button says Remove"):
        expect(logged_in_shop.product.cart_badge).to_have_text("1")
        expect(logged_in_shop.product.cart_button).to_have_text("Remove")


@pytest.mark.regression
@pytest.mark.update_cart
@pytest.mark.parametrize("case", CART["remove"], ids=[case["id"] for case in CART["remove"]])
def test_remove_a_product_from_the_cart(fill_cart, step, case):
    """Remove on the cart page takes the product out; the others stay (dataset/cart.json "remove")."""
    # Test data
    remaining = [name for name in case["products"] if name != case["remove"]]

    # Execution steps
    step_number = 1
    with step(step_number, f"Put {len(case['products'])} products in the cart and open it"):
        shop = fill_cart(case["products"])
        shop.inventory.open_cart()
    step_number += 1
    with step(step_number, f"Remove {case['remove']}"):
        shop.cart.remove_product_from_cart(case["remove"])
    step_number += 1
    with step(step_number, f"Verify the cart holds the {len(remaining)} other products"):
        assert sorted(shop.cart.get_product_names()) == sorted(remaining)
        assert shop.cart.get_cart_badge_count() == len(remaining)


@pytest.mark.regression
@pytest.mark.update_cart
def test_remove_a_product_from_the_products_page(fill_cart, step):
    """Remove on the product card takes the product out of the cart and the button says Add to cart again."""
    # Test data
    onesie = "Sauce Labs Onesie"

    # Execution steps
    step_number = 1
    with step(step_number, f"Add {onesie}"):
        shop = fill_cart([onesie])
    step_number += 1
    with step(step_number, f"Click Remove on the card of {onesie}"):
        shop.inventory.remove_product_from_cart(onesie)
    step_number += 1
    with step(step_number, "Verify the badge is gone and the button says Add to cart"):
        expect(shop.inventory.cart_badge).to_be_hidden()
        expect(shop.inventory.cart_button(onesie)).to_have_text("Add to cart")


@pytest.mark.regression
@pytest.mark.add_to_cart
def test_cart_keeps_its_products_while_shopping(fill_cart, step):
    """Going back from the cart to the products page keeps the cart."""
    # Test data
    chosen = ["Sauce Labs Bolt T-Shirt", "Sauce Labs Fleece Jacket"]

    # Execution steps
    step_number = 1
    with step(step_number, "Add two products and open the cart"):
        shop = fill_cart(chosen)
        shop.inventory.open_cart()
    step_number += 1
    with step(step_number, "Click Continue Shopping, then open the cart again"):
        shop.cart.continue_shopping()
        shop.inventory.open_cart()
    step_number += 1
    with step(step_number, "Verify the cart still holds both products"):
        assert sorted(shop.cart.get_product_names()) == sorted(chosen)


@pytest.mark.regression
@pytest.mark.update_cart
@pytest.mark.xfail(strict=True, reason="Finding F1: after Reset App State the cart is empty but the product's button "
                                        "still says Remove (checked 2026-11-27)")
def test_reset_app_state_empties_the_cart_and_resets_the_buttons(fill_cart, step):
    """Reset App State empties the cart AND turns every Remove button back into Add to cart."""
    # Test data
    backpack = "Sauce Labs Backpack"

    # Execution steps
    step_number = 1
    with step(step_number, f"Add {backpack}"):
        shop = fill_cart([backpack])
    step_number += 1
    with step(step_number, "Click Reset App State in the side menu"):
        shop.inventory.reset_app_state()
    step_number += 1
    with step(step_number, "Verify the badge is gone"):
        expect(shop.inventory.cart_badge).to_be_hidden()
    step_number += 1
    with step(step_number, "Verify the button says Add to cart again"):
        expect(shop.inventory.cart_button(backpack)).to_have_text("Add to cart")
