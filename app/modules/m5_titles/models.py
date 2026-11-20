from pydantic import BaseModel, ConfigDict

from app.modules.m1_orders.models import Key, Year


class TitlePeriod(BaseModel):
    model_config = ConfigDict(extra="forbid")
    chain: Key
    title: Key
    from_year: Year
    to_year: Year
