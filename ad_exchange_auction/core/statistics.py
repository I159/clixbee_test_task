from ad_exchange_auction.core.models import Bidder
from ad_exchange_auction.redis_client import redis_client


async def record_auction_stats(
    supply_id: str,
    country: str,
    winner_id: str,
    winner_price: float,
    bids: dict[str, float],
    eligible_bidders: list[Bidder]
):
    await redis_client.incr(f"stats:{supply_id}:total_reqs")
    await redis_client.incr(f"stats:{supply_id}:country:{country}")
    
    await redis_client.incr(f"stats:{supply_id}:bidder:{winner_id}:wins")
    await redis_client.incrbyfloat(f"stats:{supply_id}:bidder:{winner_id}:revenue", winner_price)
    
    for bidder in eligible_bidders:
        if bidder.id not in bids:
            await redis_client.incr(f"stats:{supply_id}:bidder:{bidder.id}:no_bids")
