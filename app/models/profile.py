from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import Optional

class ChildBase(BaseModel):
    display_name: str
    age: int
    language: str
    gender: str # 'boy' or 'girl'

class ChildCreate(ChildBase):
    avatar_url: str

class Child(ChildBase):
    id: UUID
    parent_id: UUID
    current_level: int
    respect_score: int
    streak: int = 0
    avatar_url: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class ChildResponse(BaseModel):
    status: str
    data: Child
