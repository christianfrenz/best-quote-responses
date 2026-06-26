-- Enable pgvector. Tables and the vector index are created by the backend
-- on startup and after ingestion. This guarantees the extension exists even
-- before the app connects.
CREATE EXTENSION IF NOT EXISTS vector;
