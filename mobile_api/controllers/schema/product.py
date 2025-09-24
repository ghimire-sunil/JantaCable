from pydantic import BaseModel, ConfigDict
from typing import Any, Optional


class Product(BaseModel):
    query: Optional[str] = None
    limit: Optional[int] = 100
    page: Optional[int] = 0
    category: Optional[int] = None
    user: Any
    customer_id: Optional[Any] = None

    model_config = ConfigDict(extra='forbid', strict=True)
