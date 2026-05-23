"""
Data schemas for cache storage and research session tracking.
"""
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from ai.schemas import Source, AnswerWithCitations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel


class CachedResult(BaseModel):
    source_type: str
    canonical_query: str
    data: list[Source]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def is_expired(self, ttl_seconds: int) -> bool:
        timestamp = self.timestamp

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        elapsed_seconds = (datetime.now(timezone.utc) - timestamp).total_seconds()
        return elapsed_seconds > ttl_seconds


class ResearchSession(BaseModel):
    """Represents an active or completed research inquiry."""
    session_id: str = Field(..., description="Unique identifier for the research session")
    question: str = Field(..., description="The original question asked by the user")
    allowed_sources: list[str] = Field(..., description="List of authorized search providers")
    retrieved_sources: list[Source] = Field(..., description="Aggregate list of sources found")
    final_answer: AnswerWithCitations | None = Field(default=None, description="The final synthesized response")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    execution_duration_seconds: float = Field(default=0.0, description="Total time taken to complete the research")
