from collections import defaultdict

from pydantic import ValidationError

from app.config import MAX_YEAR_SPAN
from app.errors import LedgerError
from app.modules.m1_orders.models import Order


def build_orders(rows):
    groups = defaultdict(list)
    if not rows:
        raise LedgerError("NO_ORDERS", "请提供至少一个订购段")
    for line, row in enumerate(rows, 1):
        try:
            order = Order.model_validate(row)
        except ValidationError as error:
            raise LedgerError("INVALID_ORDER", f"订购规则第 {line} 条无效") from error
        years = order.to_year - order.from_year + 1
        if not 1 <= years <= MAX_YEAR_SPAN:
            raise LedgerError("ORDER_SPAN", f"订购规则第 {line} 条年限须为 1 至 {MAX_YEAR_SPAN} 年")
        if order.numbering == "yearly" and order.first_issue != 1:
            raise LedgerError("YEARLY_RESET", "逐年复位的期号须从第 1 期开始")
        last_issue = order.first_issue + order.issues_per_year * years - 1
        if order.first_volume + years - 1 > 9999 or (order.numbering == "continuous" and last_issue > 9999):
            raise LedgerError("NUMBER_LIMIT", "推算出的卷号或期号超过四位")
        groups[order.chain].append(order)

    slots = []
    years_by_chain = []
    for chain, versions in sorted(groups.items()):
        previous = None
        for order in sorted(versions, key=lambda item: item.from_year):
            if previous and order.from_year <= previous.to_year:
                raise LedgerError("ORDER_OVERLAP", f"订阅链 {chain} 的订购规则有效期重叠")
            if previous and order.from_year == previous.to_year + 1:
                elapsed = previous.to_year - previous.from_year + 1
                if order.first_volume != previous.first_volume + elapsed:
                    raise LedgerError("VOLUME_DISCONTINUITY", f"订阅链 {chain} 的相邻订购段卷号断开")
                if previous.numbering == order.numbering == "continuous":
                    if order.first_issue != previous.first_issue + elapsed * previous.issues_per_year:
                        raise LedgerError("ISSUE_DISCONTINUITY", f"订阅链 {chain} 的连排期号断开")
            for offset, year in enumerate(range(order.from_year, order.to_year + 1)):
                volume = order.first_volume + offset
                first = 1 if order.numbering == "yearly" else order.first_issue + offset * order.issues_per_year
                last = first + order.issues_per_year - 1
                years_by_chain.append({"chain": chain, "year": year, "volume": volume, "first": first,
                                       "last": last, "numbering": order.numbering,
                                       "issues_per_year": order.issues_per_year, "spec": order.spec})
                slots.extend({"chain": chain, "year": year, "volume": volume, "issue": issue, "spec": order.spec}
                             for issue in range(first, last + 1))
            if len(slots) > 10000:
                raise LedgerError("TOO_MANY_SLOTS", "应到期位超过 10000")
            previous = order
    return {"expected": len(slots), "years": years_by_chain, "slots": slots}
