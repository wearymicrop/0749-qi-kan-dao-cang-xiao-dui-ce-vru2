from collections import defaultdict

BASIS = {"CURRENT_TITLE": "本期说明刊名", "TRANSITION_TITLE": "过渡期旧刊名"}


def tally_slots(slots, coverage, transition_ends=None):
    transition_ends = transition_ends or {}
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
        evidence = []
        for row in rows:
            basis = row.get("basis", "CURRENT_TITLE")
            evidence.append({
                "line": row["line"], "accession": row["accession"], "raw": row["raw"],
                "official_title": row["official_title"], "basis": basis, "basis_label": BASIS[basis],
                "spec": row.get("spec"), "expires": row.get("expires"), "conflict": row.get("code"),
            })
        outcomes.append({
            **slot, "status": status, "code": code, "evidence": evidence,
            "spec": slot.get("spec"),
            "basis": sorted({row["basis"] for row in evidence}) or ["NO_CLAIM"],
            "reasons": sorted({reason for row in evidence for reason in ([row["conflict"]] if row["conflict"] else [])}
                              | set(code and [code] or [])),
            "changed": slot.get("changed", []),
        })
    return outcomes
