"""Semantic search over stored quotes using pgvector cosine distance."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from .embeddings import embed
from .models import Quote
from .schemas import QuoteResult


def search_quotes(db: Session, text: str, limit: int = 5) -> list[QuoteResult]:
    query_vector = embed(text)

    # cosine_distance is in [0, 2]; similarity = 1 - distance for normalized vectors.
    distance = Quote.embedding.cosine_distance(query_vector).label("distance")
    stmt = select(Quote, distance).order_by(distance.asc()).limit(limit)

    results: list[QuoteResult] = []
    for quote, dist in db.execute(stmt).all():
        results.append(
            QuoteResult(
                id=quote.id,
                text=quote.text,
                author=quote.author,
                category=quote.category,
                source_name=quote.source_name,
                source_url=quote.source_url,
                similarity=max(0.0, 1.0 - float(dist)),
            )
        )
    return results
