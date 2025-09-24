from pydantic import BaseModel, EmailStr, ConfigDict


class Login(BaseModel):
    email: EmailStr
    password: str

    model_config = ConfigDict(extra='forbid', strict=True)
        
class ForgetPassword(BaseModel):
    email: EmailStr
    
    model_config = ConfigDict(extra='forbid', strict=True)   

