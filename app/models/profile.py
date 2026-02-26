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

class ChildProgress(BaseModel):
    scenarios_passed: int
    artifacts_unlocked: int

class ChildDashboard(Child):
    progress: ChildProgress

class ParentDashboardResponse(BaseModel):
    parent_name: Optional[str] = None
    parent_email: str
    subscription_status: str
    children: list[ChildDashboard]
