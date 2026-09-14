"""Regression for #810: isinstance(nonce, int) accepts True/False.

The HTTP endpoint has its own NONCE_RE check that rejects booleans,
but the internal store.append() function trusts isinstance(nonce, int),
which accepts True/False. This makes the internal function safe.
"""
import pytest
from pathlib import Path
import sys
sys.path.insert(0, "/tmp/flop-fix/technocore-chat")

import store
import didkey
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import base64


def _keypair(seed: int = 1):
    key = Ed25519PrivateKey.from_private_bytes(bytes([seed]) * 32)
    raw = key.public_key().public_bytes_raw()
    def sign(message: str) -> str:
        return base64.urlsafe_b64encode(key.sign(message.encode())).decode().rstrip("=")
    return f"{didkey.PREFIX}z{didkey._multibase(didkey.MULTICODEC_ED25519 + raw)}", sign


def test_bool_nonce_true_rejected(tmp_path):
    """True must be rejected by store.append despite isinstance(True, int)."""
    root = tmp_path / "test_room"
    root.mkdir()
    (root / "notes.jsonl").touch()
    (root / "usage.jsonl").touch()
    
    did, sign = _keypair()
    body = store.clean_text("test message")
    msg = f"test|{True}|{body}"
    sig = sign(msg)
    
    with pytest.raises(store.StoreError, match="integer nonce"):
        store.append(root, "test", "", body, did=did, nonce=True, sig=sig)


def test_bool_nonce_false_rejected(tmp_path):
    """False must be rejected by store.append despite isinstance(False, int)."""
    root = tmp_path / "test_room"
    root.mkdir()
    (root / "notes.jsonl").touch()
    (root / "usage.jsonl").touch()
    
    did, sign = _keypair()
    body = store.clean_text("test message")
    msg = f"test|{False}|{body}"
    sig = sign(msg)
    
    with pytest.raises(store.StoreError, match="integer nonce"):
        store.append(root, "test", "", body, did=did, nonce=False, sig=sig)


def test_integer_nonce_accepted(tmp_path):
    """Sanity: integer nonces still work."""
    root = tmp_path / "test_room"
    root.mkdir()
    (root / "notes.jsonl").touch()
    (root / "usage.jsonl").touch()
    
    did, sign = _keypair()
    body = store.clean_text("hello world")
    nonce = 1
    msg = f"test|{nonce}|{body}"
    sig = sign(msg)
    
    rec = store.append(root, "test", "", body, did=did, nonce=nonce, sig=sig)
    assert rec is not None
