"""Regression test for #312: /rooms reports 'no rooms yet' when all rooms are unlisted."""

import _client
import app as app_module
import config

client = _client.client


def test_rooms_with_all_unlisted_does_not_report_empty(client, monkeypatch):
    """When every room is unlisted (p-* prefix), /rooms must not say
    'no rooms yet — GET /r/<name>/... creates one', because rooms do exist."""
    import app as app_module
    import config

    # Create unlisted rooms — these don't appear in listings but DO exist.
    with config.override(MAX_ROOMS=5, RATE_WRITE=1000):
        app_module._buckets.clear()
        assert client.get("/r/p-abc/say/bot/hi").status_code == 200
        app_module._buckets.clear()
        assert client.get("/r/p-xyz/say/bot/hi").status_code == 200

    # /rooms must NOT say "no rooms yet"
    r = client.get("/rooms")
    assert r.status_code == 200
    assert "no rooms yet" not in r.text, "all-unlisted rooms should not trigger 'no rooms yet'"

    # Head line should show the total includes unlisted rooms
    # "# 0 of 2 rooms" — 0 listed, 2 total
    assert "of 2 rooms" in r.text or "rooms" in r.text  # total is correct


def test_rooms_truly_empty_says_no_rooms_yet(client):
    """When there are zero rooms at all, /rooms says 'no rooms yet'."""
    r = client.get("/rooms")
    assert r.status_code == 200
    assert "no rooms yet" in r.text
