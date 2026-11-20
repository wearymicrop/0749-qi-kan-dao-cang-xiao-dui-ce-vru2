from fastapi import APIRouter

from app.pipeline import calculate
from app.source import Selection, load_sample, resolve

router = APIRouter(prefix="/api/titles")


@router.get("/{sample}")
def sample_stage(sample: str):
    return calculate(load_sample(sample), "titles")["titles"]


@router.post("")
def input_stage(selection: Selection):
    data, _ = resolve(selection)
    return calculate(data, "titles")["titles"]
