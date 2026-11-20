from app.errors import LedgerError
from app.modules.m3_numbering.parser import parse_numbering


def normalize_receipts(intake):
    parsed = []
    rejected = []
    rows = sorted(intake["accepted"] + intake["conflicts"], key=lambda receipt: receipt["line"])
    for row in rows:
        try:
            numbers = parse_numbering(row["volume"], row["issue"], row["kind"])
        except LedgerError as error:
            rejected.append({**row, **error.payload()})
        else:
            parsed.append({**row, "numbers": numbers})
    return {"parsed": parsed, "isolated": rejected}
