"""StoreBlockedError: the store refused this network, so the test could not check anything."""


class StoreBlockedError(AssertionError):
    """The live store blocked this network: HTTP 429 (rate limit) or its bot check ("Just a moment...").

    Raised by the pages and API objects; the hook in tests/conftest.py reports such a test as SKIPPED
    with this message instead of FAILED: the store did not answer, so the test checked nothing, and a
    rerun later (or from another network) is what it needs - not a code change. The check is never
    bypassed.
    """
