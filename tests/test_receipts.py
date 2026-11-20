from app.modules.m2_receipts.service import read_receipts


def test_replay_is_counted_once(stages):
    # TRAP-03
    result = stages["receipts"]
    assert [(r["line"], r["original_line"], r["code"]) for r in result["duplicates"]] == [(6, 1, "RECEIPT_REPLAY")]


def test_disagreeing_accession_preserves_both_originals(stages):
    # TRAP-04
    result = stages["receipts"]
    assert [(r["accession"], r["issue"], r["code"]) for r in result["conflicts"]] == [
        ("00013", "8", "ACCESSION_CONFLICT"), ("00013", "9", "ACCESSION_CONFLICT")]


def test_empty_and_truncated_records_have_distinct_reasons(stages):
    # TRAP-05
    rows = stages["receipts"]["isolated"]
    assert [(r["line"], r["code"]) for r in rows] == [(17, "EMPTY_ROW"), (18, "RECEIPT_SCHEMA")]
    assert rows[1]["raw"] == {"accession": "00019"}


def test_non_string_accession_is_not_coerced(clean):
    row = clean["receipts"][0]
    assert read_receipts([{**row, "accession": 1}])["isolated"][0]["fields"] == ["accession"]


def test_accession_padding_is_preserved(clean):
    assert read_receipts(clean["receipts"])["accepted"][0]["accession"] == "00001"


def test_intake_works_before_orders_are_available(client, clean):
    result = client.post("/api/receipts", json={"data": {**clean, "rules": []}}).json()
    assert len(result["accepted"]) == result["input"] == 10


def test_replay_of_disputed_variant_keeps_first_line(dirty):
    rows = [dirty["receipts"][8], dirty["receipts"][9], dirty["receipts"][9]]
    result = read_receipts(rows)
    assert [r["line"] for r in result["conflicts"]] == [1, 2]
    assert result["duplicates"][0]["original_line"] == 2
