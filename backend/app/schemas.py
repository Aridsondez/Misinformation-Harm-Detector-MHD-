# app/schemas.py
from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Any, Dict

class AnalyzeRequest(BaseModel):
    text: Optional[str] = None
    url: Optional[HttpUrl] = None
    media_type: Optional[str] = Field(None, description="html|youtube|pdf|auto")

class EvidenceItem(BaseModel):
    source: str
    title: Optional[str] = None
    url: Optional[HttpUrl] = None
    snippet: str
    confidence: Optional[float] = None

class ResultOut(BaseModel):
    id: int
    text: str
    harm_score: int
    action: str
    evidence: List[EvidenceItem] = []
    verifier_rationale: Optional[str] = None
    factual_confidence: Optional[float] = None
    category: Optional[str] = None
    harm_breakdown: Optional[Dict[str, Any]] = None
