from fastapi import APIRouter

from app.pipeline import calculate
from app.source import Selection, load_sample, resolve

router = APIRouter(prefix="/api/combined")


@router.get("/{sample}")
def sample_stage(sample: str):
    return calculate(load_sample(sample), "combined")["combined"]


@router.post("")
def input_stage(selection: Selection):
    data, _ = resolve(selection)
    return calculate(data, "combined")["combined"]
