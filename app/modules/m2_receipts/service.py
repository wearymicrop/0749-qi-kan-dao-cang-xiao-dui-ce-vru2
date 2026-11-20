from collections import defaultdict

from pydantic import ValidationError

from app.manifest import canonical
from app.modules.m2_receipts.models import Receipt


def read_receipts(rows):
    groups = defaultdict(list)
    duplicates = []
    isolated = []
    for line, raw in enumerate(rows, 1):
        if raw is None or raw == {} or raw == "":
            isolated.append({"line": line, "raw": raw, "code": "EMPTY_ROW"})
            continue
        try:
            row = Receipt.model_validate(raw).model_dump()
        except ValidationError as error:
            fields = [str(item["loc"][0]) for item in error.errors() if item["loc"]]
            isolated.append({"line": line, "raw": raw, "fields": fields, "code": "RECEIPT_SCHEMA"})
            continue
        groups[row["accession"]].append({**row, "line": line, "raw": raw})

    accepted = []
    conflicts = []
    for group in groups.values():
        seen = {}
        for row in group:
            key = canonical({field: row[field] for field in Receipt.model_fields})
            if key in seen:
                duplicates.append({**row, "code": "RECEIPT_REPLAY", "original_line": seen[key]})
            else:
                seen[key] = row["line"]
        if len(seen) == 1:
            accepted.append(group[0])
        else:
            distinct_lines = set(seen.values())
            conflicts.extend({**row, "code": "ACCESSION_CONFLICT"} for row in group if row["line"] in distinct_lines)

    return {"input": len(rows), "accepted": sorted(accepted, key=lambda row: row["line"]),
            "conflicts": sorted(conflicts, key=lambda row: row["line"]),
            "duplicates": sorted(duplicates, key=lambda row: row["line"]), "isolated": isolated}
