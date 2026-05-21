from datetime import datetime
from pydantic import BaseModel, Field
from ai.schemas import Source, AnswerWithCitations

class CachedResult(BaseModel):
    source_type: str = Field(..., description="The platform label: wiki, arxiv, or web")
    canonical_query: str = Field(..., description="Lowercase, stripped search term")
    data: list[Source] = Field(..., description="List of source objects provided by AI layer")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    def is_expired(self, ttl_seconds: int) -> bool:
        delta = (datetime.utcnow() - self.timestamp).total_seconds()
        return delta > ttl_seconds

class ResearchSession(BaseModel):
    session_id: str
    question: str
    allowed_sources: list[str]
    retrieved_sources: list[Source]
    final_answer: AnswerWithCitations | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    execution_duration_seconds: float = 0.0

