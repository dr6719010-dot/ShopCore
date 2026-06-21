from upstash_redis import Redis
from app.config import settings

redis_client = Redis(url=settings.UPSTASH_REDIS_URL, token=settings.UPSTASH_REDIS_TOKEN)

def blacklist_token(token: str, expiry_seconds: int):
    if expiry_seconds <= 0:
        return False
    try:
        token_signature = token.split(".")[-1]
        redis_key = f"jwt:blacklist:{token_signature}"
        redis_client.set(redis_key, "1", ex=expiry_seconds)
        return True
    except Exception as e:
        return False

def is_token_blacklisted(token: str) -> bool:
    try:
        token_signature = token.split(".")[-1]
        redis_key = f"jwt:blacklist:{token_signature}"
        return redis_client.exists(redis_key) == 1
    except Exception:
        return True