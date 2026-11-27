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
<h1>Grey jacket</h1>
<ul><li class="row">Noir jacket <input name="qty" value="1"></li>
    <li class="row">Grey jacket <input name="qty" value="2"></li></ul>
<button id="later" style="display:none">Add to Cart</button>
<script>setTimeout(() => { document.getElementById('later').style.display = 'inline'; }, 300);</script>
"""


@pytest.fixture
def base(page):
    page.set_content(HTML)
    expect.set_options(timeout=1_000)  # failing checks fail fast here
    yield BasePage(page)
    expect.set_options(timeout=5_000)


@pytest.mark.parametrize("locator, text", [
    ("//p[@id='total']", "£50.00"),  # plain XPath: what every page writes
    ("(//li)[2]", "Grey jacket"),
    ("xpath=//p[@id='total']", "£50.00"),
    ("id=total", "£50.00"),
    ("id:total", "£50.00"),
    ("css=#total", "£50.00"),
    ("tag_name=h1", "Grey jacket"),
    ("class_name=errors", "Wrong password"),
    ("link=Forgot your password?", "Forgot your password?"),
    ("partial link=your password", "Forgot your password?"),
])
def test_every_locator_prefix_finds_its_element(base, locator, text):
    assert base.find_element(locator).text_content().strip() == text


def test_name_prefix_finds_the_input(base):
    base.type_text("name=q", "jacket")
    assert base.find_element("//input[@name='q']").input_value() == "jacket"


@pytest.mark.parametrize("bad, message", [
    ("", "A locator is a non-empty string"),
    ("foo=bar", "prefix 'foo' is not supported: 'foo=bar'"),
    ("nmae=q", "prefix 'nmae' is not supported: 'nmae=q'"),  # a typo fails here, not later as XPath
])
def test_bad_locators_fail_with_the_locator_in_the_message(base, bad, message):
    with pytest.raises(ValueError, match=message):
        base.find_element(bad)


def test_find_elements_returns_every_match(base):
    assert base.find_elements("//li[@class='row']").count() == 2
    assert base.find_elements("//*[@id='missing']").count() == 0


def test_type_text_fills_and_never_logs_a_secret(base, caplog):
    with caplog.at_level(logging.INFO, logger="BasePage"):
        base.type_text("//input[@name='q']", "jacket")
        base.type_text("//input[@name='password']", "Passw0rd!2026", secret=True)
    assert base.find_element("//input[@name='password']").input_value() == "Passw0rd!2026"
    assert "Passw0rd" not in caplog.text
    assert "'***'" in caplog.text and "'jacket'" in caplog.text


def test_is_element_visible_answers_now_or_waits_for_the_state(base):
    start = time.monotonic()
    assert base.is_element_visible("//p[@id='total']")
    assert not base.is_element_visible("//div[@class='errors']")
    assert not base.is_element_visible("//*[@id='missing']")
    assert time.monotonic() - start < 1
    assert base.is_element_visible("//*[@id='later']", timeout=3)  # shown by the page after 0.3 s
