from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import List, Optional, Literal

# --- Base Models ---

class ModuleBase(BaseModel):
    title: str
    description: Optional[str] = None
    language: str
    order_index: int

class LevelBase(BaseModel):
    title: str
    description: Optional[str] = None
    order_index: int
    pass_threshold_points: int
    status: str = "locked" # locked, available, completed

class ScenarioBase(BaseModel):
    title: str
    description: Optional[str] = None
    type: Literal['standard', 'boss']
    order_index: int

class PersonaBase(BaseModel):
    name: str
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    language: str

class DialogueNodeBase(BaseModel):
    text: str
    audio_url: Optional[str] = None
    speaker_type: Literal['persona', 'user', 'narrator']
    expected_response: Optional[str] = None
    points_max: int = 1
    order_index: int

# --- Response Models ---

class Persona(PersonaBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)

class DialogueNode(DialogueNodeBase):
    id: UUID
    persona_id: Optional[UUID] = None
    model_config = ConfigDict(from_attributes=True)

class Scenario(ScenarioBase):
    id: UUID
    level_id: UUID
    model_config = ConfigDict(from_attributes=True)

class ScenarioDetail(Scenario):
    nodes: List[DialogueNode] = []

class Level(LevelBase):
    id: UUID
    module_id: UUID
    scenarios: List[Scenario] = []
    model_config = ConfigDict(from_attributes=True)

class Module(ModuleBase):
    id: UUID
    levels: List[Level] = []
    model_config = ConfigDict(from_attributes=True)
