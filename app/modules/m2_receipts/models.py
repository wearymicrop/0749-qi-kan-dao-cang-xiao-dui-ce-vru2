from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.modules.m1_orders.models import Year

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class Receipt(BaseModel):
    model_config = ConfigDict(extra="forbid")
    accession: Text
    title: Text
    year: Year
    volume: Text
    issue: Text
    kind: Literal["regular", "supplement"] = "regular"
