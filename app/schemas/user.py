from pydantic import BaseModel , Field, EmailStr, model_validator, field_validator
from typing import Union
import uuid
class UserRegistrationSchema(BaseModel):
    first_name:str = Field(..., description="First name of the user")
    last_name:str = Field(..., description = "Last name of the user")
    email: EmailStr = Field(..., description="Email of the user")
    username:str = Field(..., description="Username of the user")
    password:str = Field(..., description="Password of the user")
    confirm_password:str = Field(..., description="Confirm password of the user")

    @model_validator(mode = "after")
    def match_password(self):
        if self.password!= self.confirm_password:
            raise ValueError("Passwords dont match")
        return self
    
    @field_validator("password")
    @classmethod
    def check_password_length(cls , p:str):
        if len(p)<8:
            raise ValueError("Length of password must be greater than 8 characters")
        return p
    
class UserLoginSchema(BaseModel):
    email:EmailStr = Field(..., description="Email of the user")
    password: str  = Field(..., description="Password of the user")

class UserOutput(BaseModel):
    id : uuid.UUID
    first_name: str
    last_name : str
    email : EmailStr

class UserUpdateSchema(BaseModel):
    first_name:Union[str, None] = None
    last_name:Union[str, None] = None
    password:Union[str, None] = None

class UserToken(BaseModel):
    token:str = Field(description="Access Token of the user")