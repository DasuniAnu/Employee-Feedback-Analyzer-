from pydantic import BaseModel, Field
from typing import List, Optional

#Defines how user feedback is received
class FeedbackIn(BaseModel):
    text: str = Field(..., min_length=3, max_length=5000)
    metadata: Optional[dict] = None

#Stores sentiment analysis result of feedback
class SentimentOut(BaseModel):
    label: str
    score: float

#Summarizes main themes and extracts key entities from feedback.
class ThemesOut(BaseModel):
    summary: str
    entities: List[str]

class SuggestionOut(BaseModel):
    suggestions: List[str]
    rationale: str

class IRDoc(BaseModel):
    doc_id: str
    title: str
    snippet: str
    score: float
    url: Optional[str] = None

class IRResult(BaseModel):
    query: str
    results: List[IRDoc]

class AnalyzeResponse(BaseModel):
    sentiment: SentimentOut
    themes: ThemesOut
    suggestions: SuggestionOut
    evidence: IRResult
