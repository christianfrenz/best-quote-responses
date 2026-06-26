"""Ingest real quotes from public web sources into the database.

Sources:
  * Quotable API (https://github.com/lukePeavey/quotable) — quotes with authors,
    spanning politicians, writers, athletes, philosophers, etc. Each quote is
    linked to the author's Wikiquote page as its source.
  * Public-domain KJV Bible JSON — wisdom and gospel books by default. Each verse
    links to its BibleGateway passage.

Run inside the backend container or a local venv:

    python -m scripts.ingest

Re-running is safe: duplicate (text, author) pairs are skipped.
"""

from __future__ import annotations

import sys
from urllib.parse import quote_plus

import httpx
from sqlalchemy.dialects.postgresql import insert as pg_insert
from tenacity import retry, stop_after_attempt, wait_exponential

# Allow running as `python -m scripts.ingest` or `python scripts/ingest.py`.
sys.path.append(".")

from app.config import get_settings  # noqa: E402
from app.db import Base, SessionLocal, engine  # noqa: E402
from app.embeddings import embed_batch  # noqa: E402
from app.models import Quote  # noqa: E402

settings = get_settings()

QUOTABLE_BASE = "https://api.quotable.io"
BIBLE_JSON_URL = (
    "https://raw.githubusercontent.com/thiagobodruk/bible/master/json/en_kjv.json"
)
# Most "quotable" books; keeps CPU embedding time reasonable.
BIBLE_BOOKS = {"Psalms", "Proverbs", "Ecclesiastes", "Matthew", "John"}


@retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1, max=20))
def _get_json(client: httpx.Client, url: str, **params):
    resp = client.get(url, params=params, timeout=30.0)
    resp.raise_for_status()
    return resp.json()


def fetch_quotable(client: httpx.Client, limit: int) -> list[dict]:
    """Fetch quotes from the Quotable API, paginated."""
    collected: list[dict] = []
    page = 1
    while True:
        data = _get_json(client, f"{QUOTABLE_BASE}/quotes", page=page, limit=150)
        for q in data.get("results", []):
            author = (q.get("author") or "").strip()
            tags = q.get("tags") or []
            source_url = (
                f"https://en.wikiquote.org/wiki/{quote_plus(author.replace(' ', '_'))}"
                if author
                else "https://en.wikiquote.org"
            )
            collected.append(
                {
                    "text": q["content"].strip(),
                    "author": author or None,
                    "category": tags[0] if tags else None,
                    "source_name": "Wikiquote",
                    "source_url": source_url,
                }
            )
            if limit and len(collected) >= limit:
                return collected
        if page >= data.get("totalPages", page):
            break
        page += 1
    return collected


def fetch_bible(client: httpx.Client) -> list[dict]:
    """Fetch selected public-domain KJV books."""
    data = _get_json(client, BIBLE_JSON_URL)
    rows: list[dict] = []
    for book in data:
        name = book.get("name", "")
        if name not in BIBLE_BOOKS:
            continue
        for c_idx, chapter in enumerate(book.get("chapters", []), start=1):
            for v_idx, verse in enumerate(chapter, start=1):
                ref = f"{name} {c_idx}:{v_idx}"
                search = quote_plus(f"{name} {c_idx}:{v_idx}")
                rows.append(
                    {
                        "text": verse.strip(),
                        "author": ref,
                        "category": "bible",
                        "source_name": f"Bible (KJV) — {ref}",
                        "source_url": (
                            f"https://www.biblegateway.com/passage/?search={search}"
                            "&version=KJV"
                        ),
                    }
                )
    return rows


def store(rows: list[dict]) -> int:
    """Embed and upsert rows, skipping duplicates. Returns inserted count."""
    if not rows:
        return 0
    vectors = embed_batch([r["text"] for r in rows])
    for row, vec in zip(rows, vectors):
        row["embedding"] = vec

    inserted = 0
    with SessionLocal() as db:
        for i in range(0, len(rows), 500):
            batch = rows[i : i + 500]
            stmt = (
                pg_insert(Quote)
                .values(batch)
                .on_conflict_do_nothing(constraint="uq_quote_text_author")
            )
            result = db.execute(stmt)
            inserted += result.rowcount or 0
            db.commit()
    return inserted


def main() -> None:
    Base.metadata.create_all(bind=engine)
    with httpx.Client(headers={"User-Agent": "best-quote-responses/0.1"}) as client:
        print("Fetching quotes from Quotable...")
        rows = fetch_quotable(client, settings.ingest_quotable_limit)
        print(f"  fetched {len(rows)} quotes")

        if settings.ingest_bible_enabled:
            print("Fetching Bible verses (KJV)...")
            try:
                bible_rows = fetch_bible(client)
                print(f"  fetched {len(bible_rows)} verses")
                rows.extend(bible_rows)
            except Exception as exc:  # noqa: BLE001
                print(f"  Bible fetch failed, skipping: {exc}")

    print(f"Embedding and storing {len(rows)} entries...")
    inserted = store(rows)
    print(f"Done. Inserted {inserted} new quotes (duplicates skipped).")


if __name__ == "__main__":
    main()
