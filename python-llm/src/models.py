from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict

Style = Literal["simple", "expanded", "ege"]
Intent = Literal["explain", "practice", "solve", "hint", "exam_prep"]

class NormalizeInput(BaseModel):
    subject: Optional[str] = None
    grade: Optional[int] = None
    style: Optional[str] = None
    query: str

class NormalizedPayload(BaseModel):
    subject: str
    grade: int
    style: Style
    intent: Intent
    topic_id: Optional[str]
    concepts: List[str] = []
    language: str = "ru"
    query_raw: str
    confidence: Dict[str, float] = Field(default_factory=dict)
    flags: List[str] = []

class TutorOutput(BaseModel):
    explanation: str
    examples: List[str]
    pitfalls: List[str]
    checks: List[Dict[str, str]]  # {"q":..., "a":...}
    homework: List[str]
    citations: List[str]
