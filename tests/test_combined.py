from app.pipeline import calculate


def test_combined_receipt_claims_inclusive_range(stages):
    claim = next(row for row in stages["combined"]["coverage"] if row["line"] == 2)
    assert claim["issues"] == [1, 2]


def test_out_of_volume_range_never_partially_applied(stages):
    # TRAP-08
    expansion = stages["combined"]
    assert any(row["line"] == 12 and row["code"] == "OUTSIDE_RANGE" for row in expansion["isolated"])
    assert all(row["line"] != 12 for row in expansion["coverage"])


def test_supplement_same_number_stays_separate(stages):
    # TRAP-09
    expansion = stages["combined"]
    assert [r["numbers"]["first"] for r in expansion["supplements"]] == [1, 2, 7]
    assert all(r["kind"] == "regular" for r in expansion["coverage"])


def test_wrong_volume_isolated(stages):
    assert any(row["line"] == 14 and row["code"] == "WRONG_VOLUME" for row in stages["combined"]["isolated"])


def test_past_unsubscribed_year_isolated(clean):
    data = {**clean, "rules": [{**clean["rules"][0], "from_year": 2026, "first_volume": 18}, clean["rules"][1]]}
    isolated = calculate(data, "combined")["combined"]["isolated"]
    assert [r["code"] for r in isolated] == ["OUT_OF_ORDER"] * 3


def test_clean_expansion_counts_copies_and_slots_separately(client):
    result = client.get("/api/combined/clean").json()
    assert (len(result["coverage"]), sum(len(r["issues"]) for r in result["coverage"])) == (9, 14)
