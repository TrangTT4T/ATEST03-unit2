"""The custom BasePage methods against a real Chromium page built from local HTML (no network).

Checks that every locator prefix finds its element, and what the methods wait for, return, log
and raise.
"""
import logging
import time

import pytest
from playwright.sync_api import expect

from pages import BasePage

HTML = """
<form id="search" action="/search"><input name="q"><input name="password" type="password"></form>
<a href="/account/recover">Forgot your password?</a>
<div class="errors" style="display:none">Wrong password</div>
<p id="total">£50.00</p>
<h1 data-testid="title">Grey jacket</h1>
<ul><li class="row">Noir jacket <input name="qty" value="1"></li>
    <li class="row">Grey jacket <input name="qty" value="2"></li></ul>
<button id="buy" disabled>Sold Out</button>
<button id="later" disabled>Add to Cart</button>
<script>setTimeout(() => { document.getElementById('later').disabled = false; }, 300);</script>
"""


@pytest.fixture
def base(page):
    page.set_content(HTML)
    expect.set_options(timeout=1_000)  # failing checks fail fast here
    yield BasePage(page)
    expect.set_options(timeout=5_000)


@pytest.mark.parametrize("locator, text", [
    ("css=#total", "£50.00"),
    ("xpath=//p[@id='total']", "£50.00"),
    ("id=total", "£50.00"),
    ("tag=h1", "Grey jacket"),
    ("data-testid=title", "Grey jacket"),
    ("text=Wrong password", "Wrong password"),
    ("class=errors", "Wrong password"),
    ("link=Forgot your password?", "Forgot your password?"),
    ("partial_link=your password?", "Forgot your password?"),
    ("role=button[name='Sold Out']", "Sold Out"),
])
def test_every_locator_prefix_finds_its_element(base, locator, text):
    assert base.find_element(locator).text_content() == text


def test_locators_chain_and_scope_to_a_locator(base):
    grey_row = base.find_element("css=li.row").filter(has_text="Grey jacket")
    assert base.get_input_value(grey_row, "name=qty") == "2"
    assert base.count_elements("css=ul", "name=qty") == 2
    assert not base.is_element_present("css=#missing")


def test_type_text_fills_and_never_logs_a_secret(base, caplog):
    with caplog.at_level(logging.INFO, logger="BasePage"):
        base.type_text("name=q", text="jacket")
        base.type_text("name=password", text="Passw0rd!2026", secret=True)
    assert base.get_input_value("name=q") == "jacket"
    assert base.get_input_value("name=password") == "Passw0rd!2026"
    assert "Passw0rd" not in caplog.text
    assert "'***'" in caplog.text and "'jacket'" in caplog.text


def test_state_checks_answer_now_or_wait_for_the_state(base):
    start = time.monotonic()
    assert base.is_element_visible("id=total")
    assert not base.is_element_visible("class=errors")
    assert not base.is_element_enabled("id=buy")
    assert not base.is_element_enabled("id=missing")  # missing: False, not an exception
    assert time.monotonic() - start < 1
    assert base.is_element_enabled("id=later", timeout=3)  # enabled by the page after 0.3 s


def test_checks_pass_or_fail_with_a_readable_message(base):
    base.element_should_be_visible("id=total")
    base.element_should_be_disabled("id=buy")
    base.element_should_contain_text("id=total", text="£50.00")
    base.element_should_have_count("css=li.row", count=2)
    with pytest.raises(AssertionError, match="Element 'class=errors' is not visible"):
        base.element_should_be_visible("class=errors")
    with pytest.raises(AssertionError, match="The total must be £55.00"):
        base.element_should_contain_text("id=total", text="£55.00", error_msg="The total must be £55.00")
