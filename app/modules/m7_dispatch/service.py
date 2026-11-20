from time import perf_counter

from app.manifest import make_manifest
from app.pipeline import calculate
from app.store import archive


def dispatch(data, sample=None):
    started = perf_counter()
    stages = calculate(data)
    manifest = make_manifest(data, sample, round((perf_counter() - started) * 1000, 2))
    document = {"id": manifest["digest"], "manifest": manifest,
                "result": {"balance": stages["balance"], "supplements": stages["combined"]["supplements"],
                           "duplicates": stages["receipts"]["duplicates"], "titles": stages["titles"]["periods"]}}
    return archive(document, data)
