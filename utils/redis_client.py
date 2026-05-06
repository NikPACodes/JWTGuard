import redis
from django.conf import settings

def get_redis_client() -> redis.Redis:
    # return redis.Redis(
    #     host=settings.REDIS_HOST,
    #     port=settings.REDIS_PORT,
    #     db=settings.REDIS_DB,
    #     decode_responses=True,
    # )
    return redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
    )

