# best-quote-responses

Type how you feel or what's on your mind, and get the **best matching real quote**
— from politicians, writers, athletes, philosophers, the Bible and more — each
with a link to its source.

Matching uses **semantic similarity** (embeddings + vector search), so quotes are
matched by *meaning*, not just keywords, and every result is a real, attributable
quote (no AI-invented quotes).

## Tech stack

| Layer | Tech | Why |
| --- | --- | --- |
| App (web + iOS + Android) | **Flutter** | One codebase, real native apps + web build |
| Backend API | **FastAPI** (Python) | Fast, minimal embedding + search service |
| Database / search | **Postgres + pgvector** | Relational store + vector similarity in one |
| Embeddings | **all-MiniLM-L6-v2** | Small, accurate, CPU-friendly (no GPU needed) |
| Offline | **shared_preferences** | Past requests saved on-device for offline viewing |

Search is **online only**; past requests are **stored offline** for later viewing.

## Project structure

```
doc/                 Architecture & setup documentation
docker/              Docker Compose, backend Dockerfile, Postgres init
src/
  backend/           FastAPI app + ingestion scripts
    app/             API, models, embeddings, vector search
    scripts/         Web + Bible quote ingestion
  app/               Flutter app (web / iOS / Android)
    lib/             UI, services, models
```

## Quick start

```bash
# 1. Backend + DB
docker compose -f docker/docker-compose.yml up --build

# 2. Load real quotes (Quotable API + KJV Bible)
docker compose -f docker/docker-compose.yml exec backend python -m scripts.ingest

# 3. App
cd src/app && flutter pub get
flutter run -d chrome --dart-define=API_BASE_URL=http://localhost:8000
```

See [doc/setup.md](doc/setup.md) for full instructions and
[doc/architecture.md](doc/architecture.md) for the design, the macOS/Docker GPU
note, and how to add more quote sources.