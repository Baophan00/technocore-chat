"""Regression test for #782: forged high-nonce delegation must not suppress a real one."""

import io
import sys
import time
from contextlib import redirect_stdout

import pytest

sys.path.insert(0, "scripts")
from sign import check_note, did_of, delegation, load_key, signature


@pytest.fixture()
def keypair():
    seed = "a" * 64
    key, _ = load_key(seed)
    return key, did_of(key)


def _make_record(key, root, agent, scope, nonce, days=30):
    expires = str(int(time.time()) + 86400 * days)
    sig = signature(key, delegation(root, agent, scope, expires, nonce))
    return f"delegate: {agent} {scope} {expires} {nonce} {sig}"


def test_forged_high_nonce_does_not_suppress_real_delegation(keypair):
    """Bug #782: a forged record with a higher nonce than a real delegation
    must not cause the real delegation to be reported as SUPERSEDED."""
    key, root = keypair
    agent = did_of(key)  # self-delegate for simplicity

    real = _make_record(key, root, agent, "*", "1")
    forged = f"delegate: {agent} r:lobby 9999999999 999 AQgwAQgwAQgwAQgwAQgwAQgwAQgwAQgwAQgwAQgwAQgwAQgwAQgwAQgwAQgwAQgwAQgwAQgwAQgw"

    note = f"{real} {forged}"

    buf = io.StringIO()
    with redirect_stdout(buf):
        live = check_note(root, note)
    output = buf.getvalue()

    assert live == 1, f"expected 1 live delegation, got {live}"
    assert "SUPERSEDED" not in output, "real delegation should not be SUPERSEDED"
    assert "FORGED" in output, "forged record must be reported as FORGED"
    assert "OK" in output, "real delegation must be OK"


def test_real_superseding_still_works(keypair):
    """A real higher-nonce record should still supersede a lower-nonce one."""
    key, root = keypair
    agent = did_of(key)

    old = _make_record(key, root, agent, "*", "1")
    new = _make_record(key, root, agent, "r:lobby", "2")

    note = f"{old} {new}"

    buf = io.StringIO()
    with redirect_stdout(buf):
        live = check_note(root, note)
    output = buf.getvalue()

    assert live == 1
    assert "SUPERSEDED" in output, "lower-nonce record should be SUPERSEDED"
    assert "OK" in output, "higher-nonce record should be OK"
