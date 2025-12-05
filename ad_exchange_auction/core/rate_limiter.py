"""Sliding window rate limiter using Redis sorted sets.

Fixed window counters reset at fixed intervals, allowing burst traffic across boundaries.
For example, with a 3 req/min limit and fixed windows:
- 3 requests at 12:59:58, 12:59:59, 13:00:00
- Counter resets at 13:00:00
- 3 more requests immediately allowed at 13:00:01
- Result: 6 requests in 3 seconds

Sliding window prevents this by looking back exactly N seconds from the current time.
Each request timestamp is stored in a Redis sorted set with the timestamp as the score.
Before counting, we remove all timestamps older than the window, ensuring accurate
rate limiting over any rolling time period.
"""
import time

from ad_exchange_auction.redis_client import redis_client
from ad_exchange_auction.settings import settings


async def check_rate_limit(ip_address: str) -> bool:
    key = f"rate_limit:{ip_address}"
    current_time = time.time()
    window_start = current_time - settings.rate_limit_window_seconds

    await redis_client.zremrangebyscore(key, 0, window_start)
    request_count = await redis_client.zcard(key)

    return request_count < settings.rate_limit_max_requests


async def record_request(ip_address: str):
    key = f"rate_limit:{ip_address}"
    current_time = time.time()

    await redis_client.zadd(key, {str(current_time): current_time})
    await redis_client.expire(key, settings.rate_limit_window_seconds)
