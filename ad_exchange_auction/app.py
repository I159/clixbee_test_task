from fastapi import Depends, FastAPI, HTTPException, Request

from ad_exchange_auction.core.models import (
    AuctionResult,
    BidderStatistics,
    IdentifiedBidderStatistics,
    SupplyStatistics,
)
from ad_exchange_auction.core.rate_limiter import check_rate_limit, record_request

app = FastAPI()


def rate_limit_dependency(request: Request):
    client_ip = request.client.host

    if not check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    record_request(client_ip)


@app.post("/bid")
async def bid(supply_id: str, _: None = Depends(rate_limit_dependency)) -> AuctionResult:
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
