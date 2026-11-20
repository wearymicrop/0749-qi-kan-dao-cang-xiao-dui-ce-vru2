from contextlib import closing

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import ROOT, RULE_VERSION
from app.errors import LedgerError
from app.modules.m1_orders.handler import router as orders
from app.modules.m2_receipts.handler import router as receipts
from app.modules.m3_numbering.handler import router as numbering
from app.modules.m4_combined.handler import router as combined
from app.modules.m5_titles.handler import router as titles
from app.modules.m6_balance.handler import router as balance
from app.modules.m7_dispatch.handler import router as dispatch
from app.modules.m8_specs.handler import router as specs
from app.store import connect
from app.web import pages

app = FastAPI(title="期刊到藏校对册", version=RULE_VERSION)
app.mount("/static", StaticFiles(directory=ROOT / "app/static"), name="static")
for router in (orders, receipts, numbering, combined, titles, specs, balance, dispatch, pages):
    app.include_router(router)


@app.exception_handler(LedgerError)
def ledger_error(_request: Request, error: LedgerError):
    return JSONResponse(error.payload(), status_code=error.status)


@app.exception_handler(RequestValidationError)
def input_error(_request: Request, error: RequestValidationError):
    fields = [".".join(map(str, err["loc"])) for err in error.errors()]
    return JSONResponse({"code": "INVALID_INPUT", "message": "清册结构有误", "fields": fields}, status_code=422)


@app.get("/api/health")
def health():
    with closing(connect()) as db:
        db.execute("SELECT 1").fetchone()
    return {"status": "ok", "version": RULE_VERSION}
