from app.errors import LedgerError


def claim_issues(numbers, expected):
    if expected is None:
        raise LedgerError("OUT_OF_ORDER", "该年度不在订购规则内")
    if numbers["volume"] != expected["volume"]:
        raise LedgerError("WRONG_VOLUME", "来刊卷号与订购规则冲突")
    if numbers["kind"] == "supplement":
        return []
    if numbers["first"] < expected["first"] or numbers["last"] > expected["last"]:
        raise LedgerError("OUTSIDE_RANGE", "期号越出本卷，不拆分采信")
    return list(range(numbers["first"], numbers["last"] + 1))
