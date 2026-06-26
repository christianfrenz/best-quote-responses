# Setup

## Prerequisites

- Docker + Docker Compose
- Flutter SDK 3.4+ (for the app) — https://docs.flutter.dev/get-started/install
- Python 3.12 (only if running the backend or ingestion outside Docker)

## 1. Start the backend + database

From the repo root:

```bash
docker compose -f docker/docker-compose.yml up --build
```

This starts:

- **db** — Postgres 16 with pgvector on `localhost:5432`
- **backend** — FastAPI on `http://localhost:8000` (docs at `/docs`)

The backend creates the `vector` extension and tables automatically on startup.

## 2. Load real quotes (ingestion)

The database starts empty. Populate it by running the ingestion script inside the
backend container:

```bash
docker compose -f docker/docker-compose.yml exec backend python -m scripts.ingest
```

This fetches quotes from the Quotable API (with Wikiquote source links) and KJV
Bible verses (with BibleGateway links), embeds them on CPU, and stores them.
Re-running is safe — duplicates are skipped.

Verify:

```bash
curl http://localhost:8000/api/health
# {"status":"ok","quotes":1623}
```

Try a search:

```bash
curl -X POST http://localhost:8000/api/search \
  -H 'Content-Type: application/json' \
  -d '{"text":"I am afraid to fail","limit":3}'
```

## 3. Run the app

```bash
cd src/app
flutter pub get

# Web
flutter run -d chrome --dart-define=API_BASE_URL=http://localhost:8000

# iOS simulator / Android emulator
flutter run --dart-define=API_BASE_URL=http://localhost:8000
```

> On the **Android emulator**, use `http://10.0.2.2:8000` instead of
> `localhost` to reach the host machine.

### Build for release

```bash
flutter build web      # -> build/web (static, host anywhere)
flutter build apk      # Android
flutter build ios      # iOS (needs Xcode)
```

## Running the backend without Docker (optional)

```bash
cd src/backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # point DATABASE_URL at your Postgres
uvicorn app.main:app --reload
python -m scripts.ingest
```

## Configuration

Backend settings live in `src/backend/.env` (see `.env.example`):

- `DATABASE_URL` — Postgres connection
- `EMBEDDING_MODEL` / `EMBEDDING_DIM` — embedding model (keep dim in sync)
- `CORS_ORIGINS` — allowed frontend origins
- `INGEST_QUOTABLE_LIMIT` / `INGEST_BIBLE_ENABLED` — ingestion controls
