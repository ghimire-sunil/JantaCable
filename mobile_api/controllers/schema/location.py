from pydantic import BaseModel, Field
from typing import Any, Optional

class PartnerLocation(BaseModel):
    latitude: float = Field(
        None,
        ge=-90,
        le=90,
        description="Latitude must be between -90 and 90"
    )
    longitude: float = Field(
        None,
        ge=-180,
        le=180,
        description="Longitude must be between -180 and 180"
    )
    date: Optional[Any]=None