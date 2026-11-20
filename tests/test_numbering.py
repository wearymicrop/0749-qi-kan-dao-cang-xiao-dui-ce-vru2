import pytest

from app.errors import LedgerError
from app.modules.m3_numbering.parser import parse_numbering


def test_normalizes_padded_volume_and_issue_preserving_raw(stages):
    # TRAP-06
    row = next(r for r in stages["numbering"]["parsed"] if r["line"] == 2)
    assert row["numbers"] == {"volume": 17, "first": 1, "last": 2, "kind": "regular"}
    assert row["raw"]["volume"] == "017"


def test_normalizes_fullwidth_tokens(stages):
    row = next(r for r in stages["numbering"]["parsed"] if r["line"] == 12)
    assert (row["numbers"]["volume"], row["numbers"]["first"], row["numbers"]["last"]) == (4, 12, 13)


def test_reversed_range_is_rejected(stages):
    # TRAP-07
    row = next(r for r in stages["numbering"]["isolated"] if r["line"] == 16)
    assert row["code"] == "ISSUE_ORDER" and row["raw"]["issue"] == "4–2"


def test_slash_ambiguity_is_rejected(stages):
    row = next(r for r in stages["numbering"]["isolated"] if r["line"] == 20)
    assert row["code"] == "BAD_ISSUE"


def test_supplement_range_is_rejected(stages):
    assert [(row["line"], row["code"]) for row in stages["numbering"]["isolated"]][-1] == (22, "SUPPLEMENT_RANGE")


def test_zero_volume_excluded():
    with pytest.raises(LedgerError) as error:
        parse_numbering("000", "01")
    assert error.value.code == "BAD_VOLUME"


def test_labels_and_inclusive_delimiter():
    assert parse_numbering("第 ３ 卷", "第 ３ 至 ５ 期") == {"volume": 3, "first": 3, "last": 5, "kind": "regular"}
