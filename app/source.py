import json
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.config import MAX_RECORDS, ROOT, SAMPLES
from app.errors import LedgerError


class LedgerInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rules: list[dict]
    titles: list[dict]
    receipts: list[Any]
    specs: list[dict] | None = None


class Selection(BaseModel):
    sample: str | None = None
    data: LedgerInput | None = None


def load_sample(sample):
    if sample not in SAMPLES:
        raise LedgerError("SAMPLE_NOT_FOUND", "样例不存在", 404)
    return json.loads((ROOT / "sample_data" / f"{sample}.json").read_text(encoding="utf-8-sig"))


def resolve(source):
    if (source.sample is None) == (source.data is None):
        raise LedgerError("CHOOSE_SOURCE", "请选择样例或提交一份订购清册")
    if source.sample is not None:
        return load_sample(source.sample), source.sample
    data = source.data.model_dump(exclude_none=True)
    if any(len(rows) > MAX_RECORDS for rows in data.values()):
        raise LedgerError("TOO_MANY_ROWS", f"单表最多 {MAX_RECORDS} 行", 413)
    try:
        json.dumps(data, allow_nan=False)
    except ValueError as error:
        raise LedgerError("INVALID_JSON", "清册数字须为有限值") from error
    return data, None
