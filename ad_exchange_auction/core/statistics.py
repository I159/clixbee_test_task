from ad_exchange_auction.core.models import (
    Bidder,
    BidderStatistics,
    IdentifiedBidderStatistics,
    SupplyStatistics,
)
from ad_exchange_auction.redis_client import redis_client


async def record_auction_stats(
    supply_id: str,
    country: str,
    winner_id: str,
    winner_price: float,
    bids: dict[str, float],
    eligible_bidders: list[Bidder],
):
    await redis_client.incr(f"stats:{supply_id}:total_reqs")
    await redis_client.incr(f"stats:{supply_id}:country:{country}")

    await redis_client.incr(f"stats:{supply_id}:bidder:{winner_id}:wins")
    await redis_client.incrbyfloat(
        f"stats:{supply_id}:bidder:{winner_id}:revenue", winner_price
    )

    for bidder in eligible_bidders:
        if bidder.id not in bids:
            await redis_client.incr(f"stats:{supply_id}:bidder:{bidder.id}:no_bids")


async def get_all_statistics(supply_repo) -> dict[str, SupplyStatistics]:
    stats = {}

    for supply_id in supply_repo._supplies.keys():
        total_reqs = await redis_client.get(f"stats:{supply_id}:total_reqs") or 0
        total_reqs = int(total_reqs)

        reqs_per_country = {}
        country_keys = await redis_client.keys(f"stats:{supply_id}:country:*")
        for key in country_keys:
            country = key.split(":")[-1]
            count = await redis_client.get(key) or 0
            reqs_per_country[country] = int(count)

        bidder_stats = []
        bidder_keys = await redis_client.keys(f"stats:{supply_id}:bidder:*:wins")
        bidder_ids = set(key.split(":")[3] for key in bidder_keys)

        for bidder_id in bidder_ids:
            wins = (
                await redis_client.get(f"stats:{supply_id}:bidder:{bidder_id}:wins")
                or 0
            )
            revenue = (
                await redis_client.get(f"stats:{supply_id}:bidder:{bidder_id}:revenue")
                or 0.0
            )
            no_bids = (
                await redis_client.get(f"stats:{supply_id}:bidder:{bidder_id}:no_bids")
                or 0
            )

            bidder_stats.append(
                IdentifiedBidderStatistics(
                    bidder_id=bidder_id,
                    statistics=BidderStatistics(
                        wins=int(wins),
                        total_revenue=float(revenue),
                        no_bids=int(no_bids),
                    ),
                )
            )

        stats[supply_id] = SupplyStatistics(
            total_requests=total_reqs,
            requests_per_country=reqs_per_country,
            bidders=bidder_stats,
        )

    return stats
