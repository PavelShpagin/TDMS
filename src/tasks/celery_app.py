import os
from celery import Celery
from redis import Redis, ConnectionPool


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Shared connection pool for efficient Redis connections
_redis_pool = ConnectionPool.from_url(
    REDIS_URL,
    decode_responses=True,
    max_connections=10,
    socket_keepalive=True,
    socket_connect_timeout=5,
)


def get_redis_client() -> Redis:
    """Get Redis client from shared connection pool.
    
    This is more efficient than creating new connections each time,
    and makes testing easier by providing a single injection point.
    """
    return Redis(connection_pool=_redis_pool)


celery_app = Celery(
    "tdms",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["src.tasks.sync_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    result_expires=3600,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)



