"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .config import get_settings
from .db import Base, engine
from .routers import quotes

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure the pgvector extension and tables exist on startup.
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.create_all(bind=engine)
    # HNSW index for fast cosine nearest-neighbor search.
    with engine.connect() as conn:
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_quotes_embedding "
                "ON quotes USING hnsw (embedding vector_cosine_ops)"
            )
        )
        conn.commit()
    yield


app = FastAPI(title="Best Quote Responses API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(quotes.router)


@app.get("/")
def root() -> dict:
    return {"name": "Best Quote Responses API", "docs": "/docs"}
