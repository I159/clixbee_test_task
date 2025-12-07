import asyncio

from fastapi import Depends, FastAPI, Header, HTTPException, Request

from ad_exchange_auction.core.auction import Auction
from ad_exchange_auction.core.models import (
    AuctionResult,
    BidderStatistics,
    BidRequest,
    IdentifiedBidderStatistics,
    SupplyStatistics,
)
from ad_exchange_auction.core.rate_limiter import check_rate_limit, record_request
from ad_exchange_auction.core.repository import BidderRepository, SupplyRepository
from ad_exchange_auction.core.statistics import get_all_statistics
from ad_exchange_auction.logging_config import configure_logging, get_logger

app = FastAPI()


@app.on_event("startup")
def startup_event():
    configure_logging()
    app.state.supply_repository = SupplyRepository()
    app.state.bidder_repository = BidderRepository()
    app.state.supply_repository.load()
    app.state.bidder_repository.load()
    app.state.pending_stats_tasks = set()


async def rate_limit_dependency(request: Request):
    if request.client is None:
        raise HTTPException(status_code=400, detail="Unable to determine client IP")

    client_ip = request.client.host

    if not await check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    await record_request(client_ip)


@app.post("/bid")
async def bid(
    request: Request,
    bid_request: BidRequest,
    x_country: str = Header(...),
    _: None = Depends(rate_limit_dependency),
) -> AuctionResult:
    try:
        log = get_logger().bind(supply_id=bid_request.supply_id, country=x_country)

        auction = Auction(
            supply_id=bid_request.supply_id,
            country=x_country,
            supply_repo=request.app.state.supply_repository,
            bidder_repo=request.app.state.bidder_repository,
            logger=log,
        )
        auction.run()
        result = auction.get_result()

        task = auction.record_stats_async()
        request.app.state.pending_stats_tasks.add(task)
        task.add_done_callback(lambda t: request.app.state.pending_stats_tasks.discard(t))

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/stat")
async def stat(request: Request) -> dict[str, SupplyStatistics]:
    if request.app.state.pending_stats_tasks:
        await asyncio.gather(*request.app.state.pending_stats_tasks, return_exceptions=True)

    return await get_all_statistics(request.app.state.supply_repository)
