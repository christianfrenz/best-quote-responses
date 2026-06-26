"""Pydantic request / response schemas."""

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000, description="User input.")
    limit: int = Field(5, ge=1, le=25, description="Number of quotes to return.")


class QuoteResult(BaseModel):
    id: int
    text: str
    author: str | None = None
    category: str | None = None
    source_name: str | None = None
    source_url: str | None = None
    similarity: float = Field(..., description="Cosine similarity in [0, 1].")


class SearchResponse(BaseModel):
    query: str
    results: list[QuoteResult]
