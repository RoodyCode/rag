"""Queue helpers for enqueueing ingestion tasks into Redis/RQ."""

import hashlib
from pathlib import Path

from redis import Redis
from rq import Queue, Retry
from rq.job import Job

from ingestion.config import settings
from ingestion.pipeline import list_pdf_files
from ingestion.tasks import process_pdf_task


def build_redis_client() -> Redis:
    return Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
    )


def build_queue() -> Queue:
    return Queue(
        name=settings.ingest_queue_name,
        connection=build_redis_client(),
    )


def _job_id_for_pdf(pdf_path: Path) -> str:
    normalized = str(pdf_path.resolve())
    digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()
    return f"ingest-{digest}"


def enqueue_pdf_ingestion(pdf_path: Path) -> bool:
    queue = build_queue()
    job_id = _job_id_for_pdf(pdf_path)

    existing = queue.fetch_job(job_id)
    if isinstance(existing, Job):
        return False

    queue.enqueue(
        process_pdf_task,
        str(pdf_path.resolve()),
        job_id=job_id,
        job_timeout=settings.ingest_job_timeout_seconds,
        result_ttl=settings.ingest_result_ttl_seconds,
        failure_ttl=settings.ingest_failure_ttl_seconds,
        retry=Retry(max=settings.ingest_retry_max),
    )
    return True


def enqueue_directory(data_dir: Path) -> tuple[int, int]:
    queue = build_queue()
    prepared_jobs = []
    skipped_existing = 0

    for pdf_path in list_pdf_files(data_dir):
        job_id = _job_id_for_pdf(pdf_path)
        existing = queue.fetch_job(job_id)
        if isinstance(existing, Job):
            skipped_existing += 1
            continue

        prepared_jobs.append(
            Queue.prepare_data(
                process_pdf_task,
                (str(pdf_path.resolve()),),
                job_id=job_id,
                timeout=settings.ingest_job_timeout_seconds,
                result_ttl=settings.ingest_result_ttl_seconds,
                failure_ttl=settings.ingest_failure_ttl_seconds,
                retry=Retry(max=settings.ingest_retry_max),
            )
        )

    if prepared_jobs:
        with queue.connection.pipeline() as pipeline:
            queue.enqueue_many(prepared_jobs, pipeline=pipeline)
            pipeline.execute()

    return len(prepared_jobs), skipped_existing
