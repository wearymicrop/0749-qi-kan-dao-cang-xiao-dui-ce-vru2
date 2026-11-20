from fastapi import APIRouter

from app.modules.m7_dispatch.attachment import evidence_file
from app.modules.m7_dispatch.service import dispatch
from app.source import Selection, resolve
from app.store import get_run

router = APIRouter(prefix="/api/runs")


@router.post("")
def run(selection: Selection):
    data, sample = resolve(selection)
    return dispatch(data, sample)


@router.get("/{run_id}")
def run_detail(run_id: str):
    document, _ = get_run(run_id)
    return document


@router.post("/{run_id}/rerun")
def rerun(run_id: str):
    document, source = get_run(run_id)
    return dispatch(source, document["manifest"]["sample"])


@router.get("/{run_id}/export")
def export(run_id: str):
    return evidence_file(*get_run(run_id))
