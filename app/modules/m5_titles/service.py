from collections import defaultdict
from unicodedata import normalize

from pydantic import ValidationError

from app.errors import LedgerError
from app.modules.m5_titles.models import TitlePeriod


def title_key(title):
    return normalize("NFKC", title).strip().casefold()


def build_titles(rows, orders):
    by_title = defaultdict(list)
    by_chain_year = defaultdict(list)
    order_chains = {row["chain"] for row in orders["years"]}
    for line, row in enumerate(rows, 1):
        try:
            title = TitlePeriod.model_validate(row)
        except ValidationError as error:
            raise LedgerError("INVALID_TITLE", f"刊名沿革第 {line} 条无效") from error
        if title.chain not in order_chains or title.from_year > title.to_year:
            raise LedgerError("TITLE_PERIOD", f"刊名沿革第 {line} 条订阅链或年度无效")
        key = title_key(title.title)
        for other in by_title[key]:
            if title.from_year <= other.to_year and other.from_year <= title.to_year:
                raise LedgerError("TITLE_OVERLAP", f"刊名 {title.title} 的生效年度重叠")
        by_title[key].append(title)
        for year in range(title.from_year, title.to_year + 1):
            by_chain_year[title.chain, year].append(title.title)
    for row in orders["years"]:
        if not by_chain_year[row["chain"], row["year"]]:
            raise LedgerError("MISSING_TITLE", f"订阅链 {row['chain']} 缺少 {row['year']} 年刊名")
    return {"periods": [period.model_dump() for group in by_title.values() for period in group],
            "index": by_title}


def resolve_titles(parsed, titles):
    matched, isolated = [], []
    for row in parsed["parsed"]:
        periods = titles["index"].get(title_key(row["title"]), [])
        match = next((period for period in periods if period.from_year <= row["year"] <= period.to_year), None)
        if match:
            matched.append({**row, "chain": match.chain, "official_title": match.title})
        else:
            isolated.append({**row, "code": "TITLE_EXPIRED" if periods else "UNKNOWN_TITLE"})
    return {"periods": titles["periods"], "matched": matched, "isolated": isolated}
