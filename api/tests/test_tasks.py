from contextlib import nullcontext as does_not_raise
from copy import deepcopy

import pytest

from shipit_api.admin import tasks


@pytest.mark.parametrize(
    "avail_flavors, product, version, partial_updates, product_key, expectation, result",
    (
        (
            ["promote_firefox", "promote_firefox_rc", "push_firefox", "ship_firefox", "ship_firefox_rc"],
            "firefox",
            "100.0",
            None,
            None,
            does_not_raise(),
            [
                {"name": "promote_firefox_rc", "in_previous_graph_ids": True},
                {"name": "ship_firefox_rc", "in_previous_graph_ids": False},
                {"name": "push_firefox", "in_previous_graph_ids": True},
                {"name": "ship_firefox", "in_previous_graph_ids": True},
            ],
        ),
        (
            ["promote_firefox", "push_firefox", "ship_firefox"],
            "firefox",
            "100.0.1",
            None,
            None,
            does_not_raise(),
            [
                {"name": "promote_firefox", "in_previous_graph_ids": True},
                {"name": "push_firefox", "in_previous_graph_ids": True},
                {"name": "ship_firefox", "in_previous_graph_ids": True},
            ],
        ),
        (
            ["promote_firefox", "push_firefox", "ship_firefox"],
            "firefox",
            "100.0.1",
            None,
            "firefox",
            does_not_raise(),
            [
                {"name": "promote_firefox", "in_previous_graph_ids": True},
                {"name": "push_firefox", "in_previous_graph_ids": True},
                {"name": "ship_firefox", "in_previous_graph_ids": True},
            ],
        ),
        (["some-flavor"], "non-existing-product", "1.0", None, None, pytest.raises(ValueError), None),
        (
            ["promote_firefox", "push_firefox"],
            "firefox",
            "100.0.1",
            None,
            None,
            does_not_raise(),
            [
                {"name": "promote_firefox", "in_previous_graph_ids": True},
                {"name": "push_firefox", "in_previous_graph_ids": True},
            ],
        ),
        (
            ["extra_flavor", "promote_firefox", "push_firefox", "ship_firefox"],
            "firefox",
            "100.0.1",
            None,
            None,
            does_not_raise(),
            [
                {"name": "promote_firefox", "in_previous_graph_ids": True},
                {"name": "push_firefox", "in_previous_graph_ids": True},
                {"name": "ship_firefox", "in_previous_graph_ids": True},
            ],
        ),
    ),
)
def test_extract_our_flavors(avail_flavors, product, version, partial_updates, product_key, expectation, result):
    with expectation:
        assert tasks.extract_our_flavors(avail_flavors, product, version, partial_updates, product_key) == result


def test_extract_our_flavors_unsupported_flavor():
    # This error is only raised when someone adds a new product in
    # release._VERSION_CLASS_PER_PRODUCT but forgets to add that
    # new product in config.SUPPORTED_FLAVORS.
    supported_flavors = deepcopy(tasks.SUPPORTED_FLAVORS)

    del tasks.SUPPORTED_FLAVORS["firefox"]
    with pytest.raises(tasks.UnsupportedFlavor):
        tasks.extract_our_flavors([], "firefox", "100.0.1", None)

    tasks.SUPPORTED_FLAVORS = supported_flavors


@pytest.mark.parametrize(
    "avail_flavors, expected_records, expected_text",
    (
        (["promote_firefox", "push_firefox", "ship_firefox"], 0, None),
        (["promote_firefox", "push_firefox"], 1, "Some hardcoded flavors are not in actions.json: {'ship_firefox'}. Product: firefox. Version: 100.0.1"),
        (
            ["extra_flavor", "promote_firefox", "push_firefox", "ship_firefox"],
            1,
            "Some flavors in actions.json are not hardcoded in shipit: {'extra_flavor'}. Product: firefox. Version: 100.0.1",
        ),
    ),
)
def test_extract_our_flavors_warnings(caplog, avail_flavors, expected_records, expected_text):
    tasks.extract_our_flavors(avail_flavors, "firefox", "100.0.1", None)

    assert len(caplog.records) == expected_records
    if expected_records > 0:
        assert caplog.records[0].levelname == "WARNING"
        assert expected_text in caplog.text
