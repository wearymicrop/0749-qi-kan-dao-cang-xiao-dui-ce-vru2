from collections import Counter, defaultdict

from pydantic import ValidationError

from app.errors import LedgerError
from app.modules.m1_orders.service import build_orders
from app.modules.m5_titles.service import build_titles, title_key
from app.modules.m8_specs.models import SpecDocument

EMPTY_AFFECTED = {"count": 0, "reasons": [], "years": [], "slots": []}
BASIS_LABELS = {"CURRENT_TITLE": "本期说明刊名", "TRANSITION_TITLE": "过渡期旧刊名"}


def _spec_years(doc):
    return sorted({year for rule in doc["rules"] for year in range(rule["from_year"], rule["to_year"] + 1)})


def _summary(doc, role):
    return {
        "id": doc["id"], "revision": doc["revision"], "effective_from": doc["effective_from"],
        "transition_until": doc.get("transition_until"), "role": role,
        "years": _spec_years(doc), "chains": sorted({rule["chain"] for rule in doc["rules"]}),
        "title_count": len(doc["titles"]),
    }


def _implicit(doc):
    return {
        "id": doc["id"], "revision": doc["revision"], "effective_from": doc["effective_from"],
        "transition_until": doc.get("transition_until"), "rules": doc["rules"], "titles": doc["titles"],
    }


def _validate_one(doc):
    if not doc["rules"]:
        raise LedgerError("SPEC_PERIOD", f"出版说明 {doc['id']} 缺少订购段")
    try:
        starts = min(int(rule["from_year"]) for rule in doc["rules"])
        earlier = [int(rule["from_year"]) for rule in doc["rules"] if int(rule["from_year"]) < doc["effective_from"]]
        title_starts = [int(row["from_year"]) for row in doc["titles"]]
    except (KeyError, TypeError, ValueError) as error:
        raise LedgerError("INVALID_SPEC", f"出版说明 {doc['id']} 结构无效") from error
    if starts != doc["effective_from"] or earlier:
        raise LedgerError("SPEC_PERIOD", f"出版说明 {doc['id']} 只能管辖生效年及以后")
    if any(year < doc["effective_from"] for year in title_starts):
        raise LedgerError("SPEC_PERIOD", f"出版说明 {doc['id']} 的刊名年度早于生效年")
    if doc.get("transition_until") is not None and doc["transition_until"] < doc["effective_from"]:
        raise LedgerError("SPEC_PERIOD", f"出版说明 {doc['id']} 的过渡截止早于生效年")


def _rebuild(plan):
    docs = plan["candidates"]
    merged_rules = []
    merged_titles = []
    governing = {}
    meta = {}
    for doc in docs:
        attach = None if plan["mode"] == "legacy" else doc["id"]
        for rule in doc["rules"]:
            merged_rules.append({**rule, "spec": attach})
        for row in doc["titles"]:
            merged_titles.append({**row, "spec": attach})
        meta[doc["id"]] = {"revision": doc["revision"], "effective_from": doc["effective_from"],
                           "transition_until": doc.get("transition_until")}
        for year in _spec_years(doc):
            if year in governing:
                raise LedgerError("SPEC_OVERLAP", f"{year} 年同时由 {governing[year]} 与 {doc['id']} 管辖")
            governing[year] = doc["id"]
    adopted_id = docs[-1]["id"]
    plan.update({"merged_rules": merged_rules, "merged_titles": merged_titles,
                 "governing": governing, "meta": meta, "adopted_id": adopted_id,
                 "transition_ids": [doc["id"] for doc in docs[:-1]],
                 "affected": dict(EMPTY_AFFECTED)})
    return plan


def initial_plan(data):
    rows = data.get("specs") or []
    if not rows:
        try:
            first_year = min(int(rule["from_year"]) for rule in data["rules"])
        except (KeyError, TypeError, ValueError) as error:
            raise LedgerError("NO_ORDERS", "请提供至少一个订购段") from error
        doc = _implicit({"id": "base", "revision": 1, "effective_from": first_year,
                         "transition_until": None, "rules": data["rules"], "titles": data["titles"]})
        return _rebuild({"mode": "legacy", "candidates": [doc], "rejected": [], "fallback": None})

    docs = []
    for line, row in enumerate(rows, 1):
        try:
            docs.append(SpecDocument.model_validate(row).model_dump())
        except ValidationError as error:
            raise LedgerError("INVALID_SPEC", f"出版说明第 {line} 份无效") from error
    docs.sort(key=lambda doc: (doc["effective_from"], doc["revision"]))
    seen_ids = set()
    seen_years = set()
    for doc in docs:
        if doc["id"] in seen_ids:
            raise LedgerError("SPEC_DUPLICATE", f"出版说明编号 {doc['id']} 重复")
        if doc["effective_from"] in seen_years:
            raise LedgerError("SPEC_OVERLAP", f"出版说明 {doc['id']} 的生效年度重复")
        seen_ids.add(doc["id"])
        seen_years.add(doc["effective_from"])
    for doc in docs[:-1]:
        _validate_one(doc)
    try:
        _validate_one(docs[-1])
    except LedgerError as error:
        if len(docs) == 1:
            raise
        plan = _rebuild({"mode": "specs", "candidates": docs, "rejected": [], "fallback": None})
        return _drop(plan, error)
    return _rebuild({"mode": "specs", "candidates": docs, "rejected": [], "fallback": None})


def _drop(plan, error):
    dropped = plan["candidates"].pop()
    plan["rejected"].append({"id": dropped["id"], "revision": dropped["revision"],
                             "effective_from": dropped["effective_from"], "code": error.code,
                             "message": str(error)})
    plan["fallback"] = {"code": error.code, "message": str(error), "rejected": dropped["id"],
                        "retained": plan["candidates"][-1]["id"]}
    return _rebuild(plan)


def _can_fallback(plan):
    return plan["mode"] == "specs" and len(plan["candidates"]) > 1


def _title_changes(titles):
    by_chain_year = defaultdict(set)
    for period in titles["periods"]:
        for year in range(period["from_year"], period["to_year"] + 1):
            by_chain_year[period["chain"], year].add(title_key(period["title"]))
    return by_chain_year


def _affected(plan, orders, titles):
    marks = defaultdict(set)
    grouped = defaultdict(list)
    for row in orders["years"]:
        grouped[row["chain"]].append(row)
    names = _title_changes(titles)
    for chain, rows in grouped.items():
        rows = sorted(rows, key=lambda row: row["year"])
        for previous, current in zip(rows, rows[1:]):
            if previous["spec"] == current["spec"]:
                continue
            if (previous["numbering"] != current["numbering"]
                    or previous["issues_per_year"] != current["issues_per_year"]):
                marks[chain, current["year"]].add("NUMBERING_CHANGED")
            if names.get((chain, previous["year"]), set()) != names.get((chain, current["year"]), set()):
                marks[chain, current["year"]].add("TITLE_CHANGED")
    slots = []
    for slot in orders["slots"]:
        reasons = marks.get((slot["chain"], slot["year"]))
        if reasons:
            slot["changed"] = sorted(reasons)
            slots.append({**slot, "reasons": slot["changed"]})
        else:
            slot.pop("changed", None)
    years = []
    for chain, year in sorted(marks):
        years.append({"chain": chain, "year": year, "reasons": sorted(marks[chain, year]),
                      "slots": sum(1 for row in slots if row["chain"] == chain and row["year"] == year)})
    plan["affected"] = {"count": len(slots), "slots": slots, "years": years,
                        "reasons": sorted({reason for values in marks.values() for reason in values})}
    return plan


def _check_contiguous(plan, orders):
    if plan["mode"] != "specs":
        return
    years = defaultdict(list)
    for row in orders["years"]:
        years[row["chain"]].append(row["year"])
    for chain, values in years.items():
        values = sorted(values)
        if any(later != earlier + 1 for earlier, later in zip(values, values[1:])):
            raise LedgerError("SPEC_PERIOD", f"订阅链 {chain} 的出版说明年度不连续")


def with_orders(plan):
    while True:
        try:
            orders = build_orders(plan["merged_rules"])
            _check_contiguous(plan, orders)
        except LedgerError as error:
            if not _can_fallback(plan):
                raise
            plan = _drop(plan, error)
            continue
        plan["orders"] = orders
        return _affected(plan, orders, {"periods": []}), orders


def with_titles(plan, orders):
    while True:
        try:
            titles = build_titles(plan["merged_titles"], orders)
            bridges = title_transitions(plan)
            owners = defaultdict(set)
            for period in titles["periods"]:
                owners[title_key(period["title"])].add(period["chain"])
            for name, entries in bridges.items():
                owners[name].update(entry["chain"] for entry in entries)
            clash = sorted(name for name, chains in owners.items() if len(chains) > 1)
            if clash:
                raise LedgerError("TITLE_CONFLICT", f"刊名 {clash[0]} 在不同出版说明中归属不同订阅链")
        except LedgerError as error:
            if not _can_fallback(plan):
                raise
            plan = _drop(plan, error)
            plan, orders = with_orders(plan)
            continue
        plan["titles"] = titles
        return _affected(plan, orders, titles), orders, titles


def title_transitions(plan):
    """新说明启用后，旧版说明的刊名在过渡期内继续映射回原订阅链。"""
    adopted = plan["candidates"][-1]
    adopted_titles = {row["title"] for row in adopted["titles"]}
    transitions = {}
    for doc in plan["candidates"][:-1]:
        until = max(filter(None, (doc.get("transition_until"), adopted.get("transition_until"))), default=None)
        if until is None:
            continue
        for period in doc["titles"]:
            if period["title"] in adopted_titles:
                continue
            transitions.setdefault(title_key(period["title"]), []).append(
                {"chain": period["chain"], "title": period["title"], "spec": doc["id"],
                 "from_year": period["from_year"], "to_year": until})
    return transitions


def spec_report(plan, titles=None):
    docs = plan["candidates"]
    adopted = _summary(docs[-1], "adopted")
    retained = [_summary(doc, "retained") for doc in docs[:-1]]
    basis_counts = Counter()
    transition = []
    if titles is not None:
        for row in titles["matched"]:
            basis_counts[row.get("basis", "CURRENT_TITLE")] += 1
            if row.get("basis") == "TRANSITION_TITLE":
                transition.append({"line": row["line"], "accession": row["accession"], "title": row["title"],
                                   "year": row["year"], "chain": row["chain"],
                                   "official_title": row["official_title"], "spec": row.get("spec"),
                                   "expires": row.get("expires")})
    return {
        "mode": plan["mode"],
        "adopted": adopted,
        "retained": retained,
        "rejected": plan["rejected"],
        "fallback": plan["fallback"],
        "specs": [*retained, adopted],
        "governing": [{"year": year, "spec": spec} for year, spec in sorted(plan["governing"].items())],
        "affected": {key: value for key, value in plan["affected"].items() if key != "slots"},
        "basis_counts": dict(basis_counts),
        "basis_labels": BASIS_LABELS,
        "transition": transition,
        "unresolved": [{"line": row["line"], "accession": row["accession"], "code": row["code"]}
                       for row in (titles or {}).get("isolated", [])],
    }
