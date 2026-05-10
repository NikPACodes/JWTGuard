import redis
from django.conf import settings

def get_redis_client() -> redis.Redis:
    if settings.REDIS_URL:
        return redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )
    else:
        return redis.Redis(
            username=settings.REDIS_USERNAME,
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
        )

