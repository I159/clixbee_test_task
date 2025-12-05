from fastapi import FastAPI

from ad_exchange_auction.core.models import (
    AuctionResult,
    BidderStatistics,
    IdentifiedBidderStatistics,
    SupplyStatistics,
)

app = FastAPI()


@app.post("/bid")
async def bid(supply_id: str) -> AuctionResult:
    return AuctionResult(winner="bidder1", price=0.50)


@app.get("/stat")
async def stat() -> dict[str, SupplyStatistics]:
    return {
        "supply1": SupplyStatistics(
            total_requests=10,
            requests_per_country={"US": 6, "GB": 4},
            bidders=[
                IdentifiedBidderStatistics(
                    bidder_id="bidder1",
                    statistics=BidderStatistics(
                        wins=3, total_revenue=1.50, no_bids=2
                    ),
                ),
                IdentifiedBidderStatistics(
                    bidder_id="bidder2",
                    statistics=BidderStatistics(
                        wins=2, total_revenue=0.80, no_bids=3
                    ),
                ),
            ],
        )
    }
