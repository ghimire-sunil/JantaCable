from pydantic import BaseModel, ConfigDict, field_validator
from typing import Any, List, Literal, Optional
from odoo.http import request


class Product(BaseModel):
    product_id: int
    qty: float

    model_config = ConfigDict(extra="forbid", strict=True)


class Order(BaseModel):
    customer: Optional[str] = None
    products: str
    remarks: Optional[str] = None
    payment_method: Optional[Literal["cash", "fonepay", "cheque"]] = None
    user: Any
    discount: Optional[str] = "0"
    latitude: Optional[str] = "0.0000000"
    longitude: Optional[str] = "0.0000000"
    images: Optional[Any] = None

    model_config = ConfigDict(extra="forbid", strict=True)


class GetOrders(BaseModel):
    status: Literal["pending", "completed", "cancelled"]
    customer: Optional[int] = None
    user: Any

    model_config = ConfigDict(extra="forbid", strict=True)


class GetOrder(BaseModel):
    order_id: int
    user: Any

    model_config = ConfigDict(extra="forbid", strict=True)


class OrderLine(BaseModel):
    # line_id: int
    product_id: int
    qty: float

    model_config = ConfigDict(extra="forbid", strict=True)


class EditOrder(BaseModel):
    order_id: int
    # remarks: str
    # payment_method: Literal["cash", "fonepay", "cheque"]
    lines: List[OrderLine]
    user: Any

    model_config = ConfigDict(extra="forbid", strict=True)


class Payment(BaseModel):
    amount: float
    remarks: str
    payment_method: Literal["cash", "fonepay", "cheque"]


class SavePayment(BaseModel):
    order_id: int
    payments: List[Payment]


class CancelOrder(BaseModel):
    order_id: int
    user: Any
    remarks: str

    model_config = ConfigDict(extra="forbid", strict=True)


class DueOrders(BaseModel):
    customer_id: int


class OrderDetails(BaseModel):
    order_id: int


class PaymentMethods(BaseModel):
    amount: float
    remarks: str
    date: Optional[str] = None
    payment_method: Literal["cash", "fonepay", "cheque"]
    paid: Optional[float] = 0.0


class GetPayment(BaseModel):
    orders: List[OrderDetails]
    payments: List[PaymentMethods]


class GetDueOrders(BaseModel):
    customer_id: Optional[int] = None
