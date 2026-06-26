"""Quote search endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Quote
from ..schemas import SearchRequest, SearchResponse
from ..search import search_quotes

router = APIRouter(prefix="/api", tags=["quotes"])


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    count = db.execute(select(func.count(Quote.id))).scalar_one()
    return {"status": "ok", "quotes": count}


@router.post("/search", response_model=SearchResponse)
def search(payload: SearchRequest, db: Session = Depends(get_db)) -> SearchResponse:
    results = search_quotes(db, payload.text, payload.limit)
    return SearchResponse(query=payload.text, results=results)
