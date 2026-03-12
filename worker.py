"""RQ worker entrypoint for ingestion tasks."""

from redis import Redis
from rq import Worker

from ingestion.config import settings


def main() -> None:
    redis = Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
    )
    worker = Worker([settings.ingest_queue_name], connection=redis)
    worker.work(with_scheduler=True)


if __name__ == "__main__":
    main()
