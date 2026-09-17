import pytest

from collection_splitter import (
    CollectionSplitError,
    split_collection_blocks,
)


METER_START_PATTERN = (
    r"^(?:Електромер\s*№|Фабричен\s+номер)"
)


def test_splits_one_meter_block():
    blocks = split_collection_blocks(
        raw_text=(
            "Заглавие на фактура\n"
            "Електромер № 1234567890\n"
            "Потребление 87,50\n"
        ),
        start_pattern=METER_START_PATTERN,
    )

    assert blocks == [
        "Електромер № 1234567890\n"
        "Потребление 87,50"
    ]


def test_splits_multiple_meter_blocks_in_order():
    blocks = split_collection_blocks(
        raw_text=(
            "Данни за клиента\n"
            "Електромер №1111111111\n"
            "Потребление 10,25\n"
            "Фабричен номер 2222222222\n"
            "Потребление 20.75\n"
        ),
        start_pattern=METER_START_PATTERN,
    )

    assert blocks == [
        (
            "Електромер №1111111111\n"
            "Потребление 10,25"
        ),
        (
            "Фабричен номер 2222222222\n"
            "Потребление 20.75"
        ),
    ]


def test_ignores_text_before_first_item():
    blocks = split_collection_blocks(
        raw_text=(
            "ФАКТУРА № 1234567890\n"
            "Обща сума 50,00\n"
            "Електромер №3333333333\n"
            "Потребление 50,00"
        ),
        start_pattern=METER_START_PATTERN,
    )

    assert blocks[0].startswith(
        "Електромер №3333333333"
    )
    assert "ФАКТУРА" not in blocks[0]


def test_returns_empty_list_without_items():
    assert split_collection_blocks(
        raw_text="Фактура без измервателни данни",
        start_pattern=METER_START_PATTERN,
    ) == []


def test_matching_is_case_insensitive():
    blocks = split_collection_blocks(
        raw_text=(
            "ЕЛЕКТРОМЕР №4444444444\n"
            "Потребление 12,00"
        ),
        start_pattern=METER_START_PATTERN,
    )

    assert len(blocks) == 1


def test_rejects_invalid_regex():
    with pytest.raises(
        CollectionSplitError,
        match="Invalid collection start pattern",
    ):
        split_collection_blocks(
            raw_text="sample",
            start_pattern="(",
        )


def test_rejects_non_string_source_text():
    with pytest.raises(
        CollectionSplitError,
        match="source text must be a string",
    ):
        split_collection_blocks(
            raw_text=None,
            start_pattern=METER_START_PATTERN,
        )
