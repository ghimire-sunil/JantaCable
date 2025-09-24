from pydantic import BaseModel
from typing import List, Optional, Literal


class DistributorOrderLine(BaseModel):
    product_id: int
    qty: float


class DistributorOrder(BaseModel):
    partner_id: int
    order_date: Optional[str] = None
    products: List[DistributorOrderLine]
    private_label: Literal["True", "False"]
    discount_type: Optional[Literal["Percent", "Fixed"]] = None
    discount_amount: Optional[float] = None


class DOFilter(BaseModel):
    state: Optional[str] = None
    page: Optional[int] = None
    limit: Optional[int] = None
    order_date: Optional[str] = None
    salesperson_id: Optional[int] = None


class CompleteLinePayload(BaseModel):
    line_id: int
    qty: int


class CompleteOrderPayload(BaseModel):
    order_id: int
    lines: List[CompleteLinePayload]
