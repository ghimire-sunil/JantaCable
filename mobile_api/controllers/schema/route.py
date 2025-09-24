from pydantic import BaseModel, ConfigDict
from typing import Any, Literal, Optional, List

class Route(BaseModel):
    schedule_type: Literal["today", "scheduled"]
    limit: Optional[int] = None
    page: Optional[int] = None
    user: Any
    search_query: Optional[str] = None
    search_field: Optional[Literal["name", "phone", "PAN", "code", "address"]] = None

    sort_field: Optional[Literal["last_ordered_date"]] = None
    sort_order: Optional[Literal["asc", "desc"]] = None

    filter_field: Optional[List[Literal["category", "private_label", "credit_limit"]]] = None
    category_filter: Optional[List[Literal["HORECA", "GT", "MT"]]] = None
    credit_filter: Optional[List[Literal["ok", "overdue"]]] = None
    private_label_filter: Optional[List[Literal["enabled", "disabled"]]] = None

    model_config = ConfigDict(extra='forbid', strict=True)


class RouteCustomer(BaseModel):
    route_id: int
    user:  Optional[Any] = None
    page:Optional[int] = None
    limit:Optional[int] = None
    search_query:Optional[str] = None
    model_config = ConfigDict(extra='forbid', strict=True)


class Contact(BaseModel):
    contact_id: int
    user: Any

    model_config = ConfigDict(extra='forbid', strict=True)

class OwnerDetails(BaseModel):
    id: str
    name: str
    phone: Optional[str]

class EditContact(BaseModel):
    contact_id: int
    user: Any
    image: Any
    name: str
    owner: Optional[Any] = None
    phone: str
    latitude: str
    longitude: str
    street: str    
    street2: Optional[str] = None
    city: str
    province: str
    email: Optional[str] = None
    pan_no: str
    dealer_reference: Optional[str] = None