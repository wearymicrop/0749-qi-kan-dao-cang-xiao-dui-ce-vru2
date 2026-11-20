from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import ROOT, RULE_VERSION, SAMPLES
from app.reasons import LABELS

pages = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory=ROOT / "app/templates")
INDEX = {
    "balance": "缺刊勾稽", "orders": "订购规则", "receipts": "来刊采信",
    "numbering": "卷期解析", "combined": "合期展期", "titles": "刊名沿革", "runs": "证据寄送",
}


@pages.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={
        "sections": INDEX, "samples": SAMPLES, "labels": LABELS, "version": RULE_VERSION,
    })
