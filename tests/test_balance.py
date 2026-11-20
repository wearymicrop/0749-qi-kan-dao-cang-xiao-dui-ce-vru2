def test_dirty_issue_and_row_conservation(stages):
    result = stages["balance"]
    assert result["totals"] == {"expected": 14, "covered": 7, "missing": 4, "disputed": 3, "supplements": 3, "difference": 0}
    assert result["row_totals"] == {"input": 22, "coverage": 9, "supplements": 3, "duplicates": 1, "isolated": 9, "difference": 0}
    assert result["status"] == "MATCHED"


def test_overlap_only_disputes_shared_slot(stages):
    # TRAP-11
    first, second, *_ = stages["balance"]["slots"]
    assert (first["status"], second["status"], second["code"]) == ("covered", "disputed", "CLAIM_OVERLAP")
    assert [r["line"] for r in second["evidence"]] == [2, 3]


def test_accession_conflict_can_dispute_unique_slot(stages):
    outcomes = [r for r in stages["balance"]["slots"] if r["code"] == "ACCESSION_CONFLICT"]
    assert [(r["issue"], len(r["evidence"])) for r in outcomes] == [(8, 1), (9, 1)]


def test_missing_slot_has_no_synthetic_evidence(stages):
    assert [(r["chain"], r["year"], r["issue"]) for r in stages["balance"]["slots"] if r["status"] == "missing"] == [
        ("CST", 2025, 3), ("CST", 2026, 3), ("CST", 2026, 4), ("GEO", 2026, 12)]
    assert all(r["evidence"] == [] for r in stages["balance"]["slots"] if r["code"] == "NO_CLAIM")


def test_clean_full_coverage(client):
    result = client.get("/api/balance/clean").json()
    assert result["totals"]["covered"] == 14 and result["quarantine"] == []


def test_year_breakdown_does_not_combine_same_issue(stages):
    rows = stages["balance"]["years"]
    assert [(r["year"], r["covered"], r["missing"], r["disputed"]) for r in rows if r["chain"] == "CST"] == [
        (2025, 2, 1, 1), (2026, 2, 2, 0)]


def test_empty_arrivals_preserve_full_missing_report(client, clean):
    result = client.post("/api/balance", json={"data": {**clean, "receipts": []}}).json()
    assert result["totals"]["missing"] == 14 and result["row_totals"]["input"] == 0
