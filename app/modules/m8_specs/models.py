from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StrictInt

from app.modules.m1_orders.models import Key, Year


class SpecDocument(BaseModel):
    """一份出版说明：独立编号、版本、生效年度及该版订购与刊名。"""

    model_config = ConfigDict(extra="forbid")
    id: Key
    revision: Annotated[StrictInt, Field(ge=1)]
    effective_from: Year
    rules: list[dict]
    titles: list[dict]
    transition_until: Year | None = None
