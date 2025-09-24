from pydantic import BaseModel
from typing import Optional

class Account(BaseModel):
    customer_id: Optional[int] = None