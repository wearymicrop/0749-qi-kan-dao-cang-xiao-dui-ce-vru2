from app.errors import LedgerError
from app.modules.m4_combined.claims import claim_issues


def expand_claims(titles, orders):
    years = {(row["chain"], row["year"]): row for row in orders["years"]}
    coverage, supplements, isolated = [], [], []
    for row in titles["matched"]:
        try:
            issues = claim_issues(row["numbers"], years.get((row["chain"], row["year"])))
        except LedgerError as error:
            isolated.append({**row, **error.payload()})
        else:
            if issues:
                coverage.append({**row, "issues": issues})
            else:
                supplements.append(row)
    return {"coverage": coverage, "supplements": supplements, "isolated": isolated}
