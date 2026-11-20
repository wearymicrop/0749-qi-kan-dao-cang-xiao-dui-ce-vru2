import pytest

from app.errors import LedgerError
from app.modules.m1_orders.service import build_orders


def test_yearly_resets_when_volume_increments(stages):
    # TRAP-01
    rows = stages["orders"]["years"][:2]
    assert [(row["year"], row["volume"], row["first"], row["last"]) for row in rows] == [(2025, 17, 1, 4), (2026, 18, 1, 4)]


def test_continuous_numbering_rolls_forward(stages):
    rows = stages["orders"]["years"][2:]
    assert [(row["volume"], row["first"], row["last"]) for row in rows] == [(3, 7, 9), (4, 10, 12)]


def test_overlapping_rule_versions_are_rejected(dirty):
    # TRAP-02
    order = dirty["rules"][0]
    with pytest.raises(LedgerError, match="重叠") as error:
        build_orders([order, {**order, "from_year": 2026}])
    assert error.value.code == "ORDER_OVERLAP"


def test_rollover_across_approved_frequency_change(dirty):
    order = dirty["rules"][1]
    result = build_orders([{**order, "from_year": 2026, "first_volume": 4, "first_issue": 10, "issues_per_year": 2},
                           {**order, "to_year": 2025}])
    assert result["expected"] == 5
    assert result["years"][-1]["last"] == 11


def test_discontinuous_issue_version_fails(dirty):
    order = dirty["rules"][1]
    with pytest.raises(LedgerError) as error:
        build_orders([{**order, "to_year": 2025}, {**order, "from_year": 2026, "first_volume": 4}])
    assert error.value.code == "ISSUE_DISCONTINUITY"


def test_schedule_has_unique_keys_api(client):
    result = client.get("/api/orders/dirty").json()
    assert result["expected"] == len({(r["chain"], r["year"], r["issue"]) for r in result["slots"]}) == 14


def test_empty_orders_fail_with_own_reason(client, dirty):
    response = client.post("/api/orders", json={"data": {**dirty, "rules": []}})
    assert response.status_code == 422 and response.json()["code"] == "NO_ORDERS"
