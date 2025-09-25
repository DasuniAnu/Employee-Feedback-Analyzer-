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
