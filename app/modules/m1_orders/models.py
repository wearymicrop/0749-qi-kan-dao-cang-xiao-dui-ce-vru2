from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StringConstraints

Key = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=70)]
Year = Annotated[StrictInt, Field(ge=1900, le=2200)]
Positive = Annotated[StrictInt, Field(ge=1, le=9999)]


class Order(BaseModel):
    model_config = ConfigDict(extra="forbid")
    chain: Key
    from_year: Year
    to_year: Year
    first_volume: Positive
    issues_per_year: Annotated[StrictInt, Field(ge=1, le=60)]
    numbering: Literal["yearly", "continuous"]
    first_issue: Positive = 1
