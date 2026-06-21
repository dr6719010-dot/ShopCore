import redis
from app.config import settings

redis_client = redis.from_url(settings.REDIS_URL)

def blacklist_token(token: str, expiry_seconds: int):
    if expiry_seconds <= 0:
        return False
    
    try:
        token_signature = token.split(".")[-1]
        redis_key = f"jwt:blacklist:{token_signature}"

        redis_client.set(redis_key, "1", ex=expiry_seconds)
        return True
    except (ValueError, AttributeError):
        return False
    

def is_token_blacklisted(token: str) -> bool:
    """
    Checks if a JWT's signature exists in the Redis blacklist.
    Returns True if the token is blocked, False otherwise.
    """
    try:
        token_signature = token.split(".")[-1]
        redis_key = f"jwt:blacklist:{token_signature}"
        return redis_client.exists(redis_key) == 1
        
    except (ValueError, AttributeError):
        return True