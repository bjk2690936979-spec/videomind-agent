import pytest

from backend.tools.text_splitter import split_text


def test_split_short_text() -> None:
    assert split_text("hello", chunk_size=10, overlap=2) == ["hello"]


def test_split_long_text() -> None:
    chunks = split_text("abcdefghij", chunk_size=4, overlap=1)

    assert chunks == ["abcd", "defg", "ghij"]


def test_split_overlap_is_applied() -> None:
    chunks = split_text("abcdefghij", chunk_size=5, overlap=2)

    # 前一段末尾两个字符，会出现在后一段开头。
    assert chunks[0][-2:] == chunks[1][:2]


def test_split_empty_text_raises_error() -> None:
    with pytest.raises(ValueError):
        split_text("   ")
