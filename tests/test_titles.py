from app.pipeline import calculate


def test_title_change_keeps_chain(stages):
    # TRAP-10
    rows = stages["titles"]["matched"]
    assert {(row["official_title"], row["chain"]) for row in rows if row["chain"] == "CST"} == {
        ("海岸观测通报", "CST"), ("海岸观测季刊", "CST")}


def test_retired_title_is_isolated(stages):
    assert any(row["line"] == 13 and row["code"] == "TITLE_EXPIRED" for row in stages["titles"]["isolated"])


def test_unregistered_title_has_distinct_reason(stages):
    assert any(row["line"] == 15 and row["code"] == "UNKNOWN_TITLE" for row in stages["titles"]["isolated"])


def test_overlap_rejected_after_normalizing_title(client, clean):
    period = clean["titles"][0]
    response = client.post("/api/titles", json={"data": {**clean, "titles": [*clean["titles"], {**period, "chain": "GEO"}]}})
    assert response.status_code == 422 and response.json()["code"] == "TITLE_OVERLAP"


def test_missing_title_year_is_rejected(client, clean):
    response = client.post("/api/titles", json={"data": {**clean, "titles": clean["titles"][1:]}})
    assert response.status_code == 422 and response.json()["code"] == "MISSING_TITLE"


def test_narrow_and_fullwidth_alias_resolve_equally(clean):
    clean["titles"][2]["title"] = "A輯刊"
    clean["receipts"] = [{**clean["receipts"][7], "title": "ａ輯刊"}]
    match = calculate(clean, "titles")["titles"]["matched"][0]
    assert (match["official_title"], match["chain"]) == ("A輯刊", "GEO")
