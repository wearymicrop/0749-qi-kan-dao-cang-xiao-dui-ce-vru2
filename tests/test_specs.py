import copy

from app.pipeline import calculate
from app.source import load_sample


def renewal():
    return load_sample("renewal")


def test_two_specs_coexist_and_newest_is_adopted(renewal_stages):
    stages = renewal_stages
    report = stages["specs"]
    assert report["mode"] == "specs"
    assert report["adopted"]["id"] == "CST-2026"
    assert [doc["id"] for doc in report["retained"]] == ["CST-2025"]
    assert [doc["role"] for doc in report["specs"]] == ["retained", "adopted"]


def test_governing_map_shows_which_spec_owns_each_year(renewal_stages):
    stages = renewal_stages
    governing = {row["year"]: row["spec"] for row in stages["specs"]["governing"]}
    assert governing == {2025: "CST-2025", 2026: "CST-2026", 2027: "CST-2026"}


def test_affected_slots_are_the_first_year_after_the_switch(renewal_stages):
    stages = renewal_stages
    affected = stages["specs"]["affected"]
    assert affected["count"] == 4
    assert [(row["chain"], row["year"], row["reasons"]) for row in affected["years"]] == [
        ("CST", 2026, ["NUMBERING_CHANGED", "TITLE_CHANGED"])]
    slot = next(row for row in stages["balance"]["slots"] if row["year"] == 2026 and row["issue"] == 5)
    assert slot["changed"] == ["NUMBERING_CHANGED", "TITLE_CHANGED"]
    stable = next(row for row in stages["balance"]["slots"] if row["year"] == 2025 and row["issue"] == 1)
    assert stable["changed"] == []


def test_each_slot_records_the_governing_spec(renewal_stages):
    stages = renewal_stages
    for slot in stages["balance"]["slots"]:
        assert slot["spec"] == ({"2025": "CST-2025"}.get(str(slot["year"]), "CST-2026"))


def test_continuous_numbering_carries_across_the_new_name(renewal_stages):
    stages = renewal_stages
    years = [(row["year"], row["volume"], row["first"], row["last"]) for row in stages["orders"]["years"]]
    assert years == [(2025, 17, 1, 4), (2026, 18, 5, 8), (2027, 19, 9, 12)]


def test_transition_old_title_returns_to_original_chain(renewal_stages):
    stages = renewal_stages
    report = stages["specs"]
    assert report["basis_counts"] == {"CURRENT_TITLE": 8, "TRANSITION_TITLE": 2}
    bridge = {(row["line"], row["chain"], row["official_title"], row["expires"]) for row in report["transition"]}
    assert bridge == {(6, "CST", "海岸观测通报", 2027), (9, "CST", "海岸观测通报", 2027)}
    late = next(row for row in stages["balance"]["slots"] if row["year"] == 2027 and row["issue"] == 9)
    assert (late["status"], late["basis"], late["evidence"][0]["basis_label"]) == (
        "covered", ["TRANSITION_TITLE"], "过渡期旧刊名")


def test_old_title_is_not_mistaken_for_missing_or_unknown(renewal_stages):
    stages = renewal_stages
    codes = {row["line"]: row["code"] for row in stages["balance"]["quarantine"]}
    assert codes == {11: "UNKNOWN_TITLE"}
    assert all(row["status"] != "missing" for row in stages["balance"]["slots"]
               if row["year"] == 2027 and row["issue"] == 9)


def test_unresolved_disputes_stay_visible(renewal_stages):
    stages = renewal_stages
    disputes = stages["balance"]["disputes"]
    assert [(row["year"], row["issue"], row["code"], row["evidence"]) for row in disputes] == [
        (2026, 8, "CLAIM_OVERLAP", [6, 7])]
    assert stages["specs"]["unresolved"] == [
        {"line": 11, "accession": "00011", "code": "UNKNOWN_TITLE"}]


def test_cover_is_counted_once_on_recalculation():
    data = renewal()
    first = calculate(data)["balance"]
    second = calculate(data)["balance"]
    assert first == second
    assert first["row_totals"]["difference"] == 0
    assert first["totals"]["covered"] == 9
    assert first["row_totals"]["coverage"] == 9


def test_broken_new_spec_falls_back_and_keeps_old_records():
    data = copy.deepcopy(renewal())
    data["specs"][1]["rules"][0]["first_volume"] = 19
    result = calculate(data)
    report = result["specs"]
    assert report["fallback"]["code"] == "VOLUME_DISCONTINUITY"
    assert report["fallback"]["rejected"] == "CST-2026"
    assert report["adopted"]["id"] == "CST-2025"
    assert [row["id"] for row in report["rejected"]] == ["CST-2026"]
    assert result["balance"]["row_totals"]["difference"] == 0
    assert result["balance"]["row_totals"]["isolated"] == 8


def test_legacy_ledger_still_reports_one_implicit_spec():
    report = calculate(load_sample("clean"))["specs"]
    assert report["mode"] == "legacy"
    assert report["adopted"]["id"] == "base" and report["retained"] == []
    assert report["affected"]["count"] == 0


def test_archive_keeps_adjudication_and_reruns_without_double_cover(client):
    run = client.post("/api/runs", json={"sample": "renewal"}).json()
    result = run["result"]
    assert result["specs"]["adopted"]["id"] == "CST-2026"
    assert result["specs"]["affected"]["count"] == 4
    assert result["balance"]["row_totals"]["difference"] == 0
    again = client.post(f"/api/runs/{run['id']}/rerun").json()
    assert again["reused"] is True and again["id"] == run["id"]
    assert again["result"]["balance"]["totals"] == result["balance"]["totals"]


def test_year_gap_between_specs_falls_back_instead_of_silent_missing():
    data = copy.deepcopy(renewal())
    data["specs"][1]["effective_from"] = 2027
    data["specs"][1]["rules"][0]["from_year"] = 2027
    data["specs"][1]["titles"][0]["from_year"] = 2027
    data["specs"][1]["rules"][0]["first_volume"] = 19
    result = calculate(data)
    assert result["specs"]["fallback"]["code"] == "SPEC_PERIOD"
    assert result["specs"]["adopted"]["id"] == "CST-2025"
    codes = {row["line"]: row["code"] for row in result["balance"]["quarantine"]}
    assert 6 in codes and codes[6] == "TITLE_EXPIRED"   # the 2026 receipt is not silently dropped
