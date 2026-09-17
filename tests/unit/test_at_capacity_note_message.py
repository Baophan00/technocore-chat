"""Regression test for #285: _at_capacity() note message must not reference /rooms or stillborn rule."""

import pytest

import store


def test_at_capacity_note_message_does_not_reference_rooms_or_stillborn(tmp_path, monkeypatch):
    """When MAX_NOTES_PER_NS is reached, the refusal message must give
    note-accurate guidance: no /rooms (notes are not listed), no stillborn
    rule (that is room-only)."""
    monkeypatch.setattr(store, "MAX_NOTES_PER_NS", 1)
    store.note_set(tmp_path, "ns", "only", "v")
    with pytest.raises(store.StoreError) as refused:
        store.note_set(tmp_path, "ns", "second", "v")
    message = str(refused.value)
    # Must not contain room-specific guidance.
    assert "GET /rooms" not in message, "note refusal should not reference /rooms"
    assert "24 hours" not in message, "note refusal should not quote stillborn rule"
    # Must contain note-accurate guidance.
    assert "Overwrite a note you already own" in message
    assert "notes are not listed" in message
    assert "7 days" in message


def test_at_capacity_room_message_unchanged(tmp_path, monkeypatch):
    """Room capacity refusal keeps the existing room-specific guidance."""
    monkeypatch.setattr(store, "MAX_ROOMS", 1)
    store.append(tmp_path, "only", "bot", "hi")
    with pytest.raises(store.StoreError) as refused:
        store.append(tmp_path, "second", "bot", "hi")
    message = str(refused.value)
    assert "GET /rooms" in message
    assert "24 hours" in message
    assert "7 days" in message
