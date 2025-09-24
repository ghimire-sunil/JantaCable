from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from typing import Any, Optional
from ..validators.phone_number import PhoneNumber
from odoo.http import request


class Location(BaseModel):
    latitude: Optional[float] = Field(
        None,
        ge=-90,
        le=90,
        description="Latitude must be between -90 and 90"
    )
    longitude: Optional[float] = Field(
        None,
        ge=-180,
        le=180,
        description="Longitude must be between -180 and 180"
    )


class Contact(BaseModel):
    # name: str
    # street: str
    # street2: Optional[str] = None
    # phone: Optional[str] = None
    # city: Optional[str] = None
    # credit_limit: Optional[str] = None
    # pan_no: Optional[str] = None
    # image: Optional[Any] = None
    # location: Optional[str] = None
    # user: Any
    # search_query:Optional[str] = None

    name: str
    street: str
    street2: Optional[str] = None
    phone: str
    city: str
    province: str
    credit_limit_value: str  
    credit_limit_days: str  
    pan_no: str
    image: Any
    location: str
    user: Any
    outlet_type: str
    email: Optional[str] = None
    secondary_contact_name: Optional[str] = None
    secondary_contact_phone: Optional[str] = None
    secondary_contact_email: Optional[str] = None
    registration_number: Optional[str] = None
    dealer_reference: Optional[str] = None
    search_query: Optional[str] = None
    private_label: Optional[str] = None
    artwork_reference: Optional[Any]= None
    lead_time_note: Optional[str] = None
    min_order_qty_check: Optional[str] = None
    packaging_notes: Optional[str] = None

    model_config = ConfigDict(extra='forbid', strict=True)

    # @field_validator("vat", mode="before")
    # @classmethod
    # def check_existing_customer(cls, value, field):
    #     if value:       
    #         partner = request.env['res.partner'].sudo().search([
    #             (field.field_name, '=', value)
    #         ], limit=1)
    #         if partner:
    #             raise ValueError(       
    #                 f"Customer with {field.field_name.capitalize()} - {value} already exists")
    #     return value
