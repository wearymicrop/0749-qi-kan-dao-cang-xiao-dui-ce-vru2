from collections import defaultdict


def tally_slots(slots, coverage):
    lookup = defaultdict(list)
    for receipt in coverage:
        for issue in receipt["issues"]:
            lookup[receipt["chain"], receipt["year"], issue].append(receipt)
    outcomes = []
    for slot in slots:
        rows = lookup[slot["chain"], slot["year"], slot["issue"]]
        if not rows:
            status, code = "missing", "NO_CLAIM"
        elif any(row.get("code") == "ACCESSION_CONFLICT" for row in rows):
            status, code = "disputed", "ACCESSION_CONFLICT"
        elif len(rows) > 1:
            status, code = "disputed", "CLAIM_OVERLAP"
        else:
            status, code = "covered", None
        outcomes.append({**slot, "status": status, "code": code,
                         "evidence": [{key: row[key] for key in ("line", "accession", "raw", "official_title")} for row in rows]})
    return outcomes
