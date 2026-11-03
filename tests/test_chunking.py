import pytest

from rag.chunking import chunk_text


def test_default_chunk_size_and_overlap():
    text = "a" * 1520
    chunks = chunk_text(text)

    assert len(chunks) == 2
    assert len(chunks[0]) == 800
    assert len(chunks[1]) == 800
    assert chunks[0][-80:] == chunks[1][:80]


def test_short_text_returns_one_chunk():
    assert chunk_text("hello") == ["hello"]


def test_empty_text_returns_no_chunks():
    assert chunk_text("   ") == []


def test_custom_chunk_size_and_overlap():
    chunks = chunk_text("abcdefghij", chunk_size=6, overlap=2)

    assert chunks == ["abcdef", "efghij"]


def test_invalid_chunk_size():
    with pytest.raises(ValueError):
        chunk_text("hello", chunk_size=0)


def test_invalid_overlap():
    with pytest.raises(ValueError):
        chunk_text("hello", chunk_size=5, overlap=5)
