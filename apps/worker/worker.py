import asyncio
import json
import logging
import os
import random
import time
from typing import Any

import asyncpg
import redis.asyncio as redis
from prometheus_client import Counter, Gauge, Histogram, start_http_server

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s [worker] %(message)s",
)
logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
REDIS_QUEUE_KEY = os.getenv("REDIS_QUEUE_KEY", "jobs:queue")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "kubeserve")
POSTGRES_USER = os.getenv("POSTGRES_USER", "app")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "app")
POSTGRES_DSN = os.getenv(
    "POSTGRES_DSN",
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}",
)
METRICS_PORT = int(os.getenv("METRICS_PORT", "9100"))

jobs_processed_total = Counter("worker_jobs_processed_total", "Total processed jobs")
jobs_failed_total = Counter("worker_jobs_failed_total", "Total failed jobs")
job_processing_seconds = Histogram(
    "worker_job_processing_seconds", "Time spent processing each job"
)
worker_inflight_jobs = Gauge("worker_inflight_jobs", "Number of jobs currently being processed")


async def ensure_schema(pool: asyncpg.Pool) -> None:
    query = """
    CREATE TABLE IF NOT EXISTS jobs (
        job_id TEXT PRIMARY KEY,
        payload JSONB NOT NULL,
        status TEXT NOT NULL,
        result JSONB,
        error TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """
    async with pool.acquire() as conn:
        await conn.execute(query)


async def process_payload(payload: dict[str, Any]) -> dict[str, Any]:
    sleep_seconds = random.randint(1, 3)
    await asyncio.sleep(sleep_seconds)
    return {
        "message": "processed",
        "input_keys": list(payload.keys()),
        "processing_seconds": sleep_seconds,
    }


async def run() -> None:
    logger.info("starting worker")
    start_http_server(METRICS_PORT)

    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    pg_pool = await asyncpg.create_pool(POSTGRES_DSN, min_size=1, max_size=5)
    await ensure_schema(pg_pool)

    try:
        while True:
            item = await redis_client.blpop(REDIS_QUEUE_KEY, timeout=5)
            if item is None:
                continue

            _, raw_data = item
            started = time.perf_counter()
            worker_inflight_jobs.inc()

            try:
                body = json.loads(raw_data)
                job_id = body["job_id"]
                payload = body.get("payload", {})

                result = await process_payload(payload)

                async with pg_pool.acquire() as conn:
                    await conn.execute(
                        """
                        UPDATE jobs
                        SET status='completed', result=$1::jsonb, error=NULL, updated_at=NOW()
                        WHERE job_id=$2
                        """,
                        json.dumps(result),
                        job_id,
                    )

                jobs_processed_total.inc()
                logger.info("job completed: %s", job_id)
            except Exception as exc:
                jobs_failed_total.inc()
                logger.exception("job failed: %s", exc)

                try:
                    body = json.loads(raw_data)
                    job_id = body.get("job_id")
                    if job_id:
                        async with pg_pool.acquire() as conn:
                            await conn.execute(
                                """
                                UPDATE jobs
                                SET status='failed', error=$1, updated_at=NOW()
                                WHERE job_id=$2
                                """,
                                str(exc),
                                job_id,
                            )
                except Exception as update_exc:
                    logger.exception("failed to update failed job status: %s", update_exc)
            finally:
                worker_inflight_jobs.dec()
                job_processing_seconds.observe(time.perf_counter() - started)
    finally:
        await redis_client.aclose()
        await pg_pool.close()


if __name__ == "__main__":
    asyncio.run(run())
