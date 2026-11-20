import re
from unicodedata import normalize

from app.errors import LedgerError

RANGE = re.compile(r"([0-9]{1,4})(?:\s*[-–—~至]\s*([0-9]{1,4}))?")


def parse_numbering(volume, issue, kind="regular"):
    volume_text = normalize("NFKC", volume).strip().removeprefix("第").removesuffix("卷").strip()
    text = normalize("NFKC", issue).strip()
    text = text.removeprefix("增刊" if kind == "supplement" else "第").removesuffix("期").strip()
    if not re.fullmatch(r"[0-9]{1,4}", volume_text) or int(volume_text) == 0:
        raise LedgerError("BAD_VOLUME", "卷号须为 1 至 9999")
    match = RANGE.fullmatch(text)
    if not match:
        raise LedgerError("BAD_ISSUE", "期号须为正整数或同卷连续范围")
    first = int(match[1])
    last = int(match[2]) if match[2] is not None else first
    if first < 1 or last < first:
        raise LedgerError("ISSUE_ORDER", "期号须为正数且范围递增")
    if kind == "supplement" and match[2] is not None:
        raise LedgerError("SUPPLEMENT_RANGE", "每行增刊仅登记一个期号")
    return {"volume": int(volume_text), "first": first, "last": last, "kind": kind}
