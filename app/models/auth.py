from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from uuid import UUID

class GoogleAuthRequest(BaseModel):
    code: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserSignup(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class ParentBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    google_id: Optional[str] = None

class ParentCreate(ParentBase):
    pass

class Parent(ParentBase):
    id: UUID
    
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str
    parent: Parent
