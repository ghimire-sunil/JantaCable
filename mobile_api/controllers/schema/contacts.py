from pydantic import BaseModel, ConfigDict
from typing import Any, Optional, Literal

class Contacts(BaseModel):
    customer_id: Optional[Any] = None
    user:  Optional[Any] = None
    page:Optional[int] = None
    limit:Optional[int] = None
    search_query:Optional[str] = None
    model_config = ConfigDict(extra='forbid', strict=True)

class ContactDetail(BaseModel):
    customer_id: int
    user:  Optional[Any] = None
    model_config = ConfigDict(extra='forbid', strict=True)

class OrderHistory(BaseModel):
    status: Literal["pending", "completed", "cancelled"]
    user_id: int
    user: Any

    model_config = ConfigDict(extra="forbid", strict=True)

class OrderHistoryDaily(BaseModel):
    status: Literal["pending", "completed", "cancelled"]
    user: Any

    model_config = ConfigDict(extra="forbid", strict=True)