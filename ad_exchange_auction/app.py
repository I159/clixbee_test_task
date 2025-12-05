from fastapi import Depends, FastAPI, Header, HTTPException, Request

from ad_exchange_auction.core.models import (
    AuctionResult,
    BidRequest,
    BidderStatistics,
    IdentifiedBidderStatistics,
    SupplyStatistics,
)
from ad_exchange_auction.core.auction import Auction
from ad_exchange_auction.core.rate_limiter import check_rate_limit, record_request
from ad_exchange_auction.core.repository import BidderRepository, SupplyRepository

app = FastAPI()


@app.on_event("startup")
def startup_event():
    app.state.supply_repository = SupplyRepository()
    app.state.bidder_repository = BidderRepository()
    app.state.supply_repository.load()
    app.state.bidder_repository.load()


async def rate_limit_dependency(request: Request):
    client_ip = request.client.host

    if not await check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    await record_request(client_ip)


@app.post("/bid")
async def bid(
    request: Request,
    bid_request: BidRequest,
    x_country: str = Header(...),
    _: None = Depends(rate_limit_dependency)
) -> AuctionResult:
    try:
        auction = Auction(
            supply_id=bid_request.supply_id,
            country=x_country,
            supply_repo=request.app.state.supply_repository,
            bidder_repo=request.app.state.bidder_repository
        )
        auction.run()
        return auction.get_result()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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
