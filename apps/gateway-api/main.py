import json
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import asyncpg
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s [gateway-api] %(message)s",
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

jobs_created_total = Counter(
    "gateway_jobs_created_total", "Total number of jobs accepted by gateway"
)
jobs_failed_total = Counter(
    "gateway_jobs_failed_total", "Total number of failed job submissions"
)
job_submit_latency_seconds = Histogram(
    "gateway_job_submit_latency_seconds", "Latency for POST /jobs"
)


class AppState:
    redis_client: redis.Redis | None = None
    pg_pool: asyncpg.Pool | None = None


state = AppState()


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


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("starting gateway-api")
    state.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    state.pg_pool = await asyncpg.create_pool(POSTGRES_DSN, min_size=1, max_size=10)
    await ensure_schema(state.pg_pool)
    yield
    logger.info("shutting down gateway-api")
    if state.redis_client:
        await state.redis_client.aclose()
    if state.pg_pool:
        await state.pg_pool.close()


app = FastAPI(title="kubeserve-lab gateway-api", version="0.1.0", lifespan=lifespan)


@app.get("/live")
async def live() -> dict[str, str]:
    return {"status": "alive", "time": datetime.now(timezone.utc).isoformat()}


@app.get("/ready")
async def ready() -> JSONResponse:
    redis_ok = False
    postgres_ok = False

    try:
        if state.redis_client is not None:
            redis_ok = bool(await state.redis_client.ping())
    except Exception as exc:
        logger.exception("redis readiness failed: %s", exc)

    try:
        if state.pg_pool is not None:
            async with state.pg_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            postgres_ok = True
    except Exception as exc:
        logger.exception("postgres readiness failed: %s", exc)

    if redis_ok and postgres_ok:
        return JSONResponse(status_code=200, content={"status": "ready"})

    return JSONResponse(
        status_code=503,
        content={
            "status": "not_ready",
            "dependencies": {
                "redis": redis_ok,
                "postgres": postgres_ok,
            },
        },
    )


@app.post("/jobs")
async def create_job(payload: dict) -> dict[str, str]:
    started = time.perf_counter()
    job_id = str(uuid.uuid4())

    try:
        if state.redis_client is None or state.pg_pool is None:
            raise RuntimeError("dependencies are not initialized")

        async with state.pg_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO jobs(job_id, payload, status) VALUES($1, $2::jsonb, 'queued')",
                job_id,
                json.dumps(payload),
            )

        await state.redis_client.rpush(
            REDIS_QUEUE_KEY,
            json.dumps({"job_id": job_id, "payload": payload}),
        )
        jobs_created_total.inc()
        return {"job_id": job_id}
    except Exception as exc:
        jobs_failed_total.inc()
        logger.exception("failed to create job: %s", exc)
        raise HTTPException(status_code=500, detail="failed to enqueue job") from exc
    finally:
        job_submit_latency_seconds.observe(time.perf_counter() - started)


@app.get("/jobs/{job_id}")
async def get_job(job_id: str) -> dict:
    try:
        if state.pg_pool is None:
            raise RuntimeError("postgres pool not initialized")

        async with state.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT job_id, payload, status, result, error, created_at, updated_at FROM jobs WHERE job_id=$1",
                job_id,
            )

        if row is None:
            raise HTTPException(status_code=404, detail="job not found")

        return {
            "job_id": row["job_id"],
            "payload": row["payload"],
            "status": row["status"],
            "result": row["result"],
            "error": row["error"],
            "created_at": row["created_at"].isoformat(),
            "updated_at": row["updated_at"].isoformat(),
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("failed to fetch job %s: %s", job_id, exc)
        raise HTTPException(status_code=500, detail="failed to fetch job") from exc


@app.get("/metrics")
async def metrics() -> PlainTextResponse:
    return PlainTextResponse(generate_latest().decode("utf-8"), media_type=CONTENT_TYPE_LATEST)
