import re
from pydantic import BaseModel, ConfigDict, Field, field_validator, EmailStr
from typing import Any
from ..validators.phone_number import PhoneNumber


class ChangePassword(BaseModel):
    old_password : str
    password: str = Field(..., min_length=6, max_length=255)
    user: Any

    model_config = ConfigDict(extra='forbid', strict=True)

    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not re.search(r"[A-Z]", value):
            raise ValueError(
                "Password must contain at least one uppercase letter")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise ValueError(
                "Password must contain at least one special character")
        return value


class UserProfile(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    email: EmailStr
    phone: PhoneNumber
    address: str
    user: Any

class UserImage(BaseModel):
    image: Any