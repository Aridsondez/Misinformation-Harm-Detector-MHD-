# app/schemas.py
from pydantic import BaseModel, Field
from typing import List, Any

class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=2, strip_whitespace=True)

class EvidenceItem(BaseModel):
    source: str
    confidence: float
    snippet: str
    url: str | None = None

class ResultOut(BaseModel):
    id: int
    text: str
    harm_score: int
    action: str
    evidence: List[EvidenceItem]
