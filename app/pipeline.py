from app.modules.m1_orders.service import build_orders
from app.modules.m2_receipts.service import read_receipts
from app.modules.m3_numbering.service import normalize_receipts
from app.modules.m4_combined.service import expand_claims
from app.modules.m5_titles.service import resolve_titles
from app.modules.m6_balance.service import balance
from app.modules.m8_specs.service import initial_plan, spec_report, title_transitions, with_orders, with_titles


def calculate(data, through="balance"):
    results = {}
    if through == "orders":
        plan, orders = with_orders(initial_plan(data))
        return {"orders": orders, "specs": spec_report(plan)}
    intake = results["receipts"] = read_receipts(data["receipts"])
    if through == "receipts":
        return results
    numbering = results["numbering"] = normalize_receipts(intake)
    if through == "numbering":
        return results
    plan, orders = with_orders(initial_plan(data))
    results["orders"] = orders
    plan, orders, titles = with_titles(plan, orders)
    resolved = results["titles"] = resolve_titles(numbering, titles, title_transitions(plan))
    report = results["specs"] = spec_report(plan, resolved)
    if through == "titles":
        return results
    combined = results["combined"] = expand_claims(resolved, orders)
    if through != "combined":
        results["balance"] = balance(orders, intake, numbering, resolved, combined, report)
    return results
