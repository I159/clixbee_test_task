import asyncio

from ad_exchange_auction.core.models import AuctionResult, Bidder, Country
from ad_exchange_auction.core.repository import BidderRepository, SupplyRepository
from ad_exchange_auction.core.statistics import record_auction_stats


class Auction:
    def __init__(self, supply_id: str, country: str, supply_repo: SupplyRepository, bidder_repo: BidderRepository, logger=None):
        self.supply_id = supply_id
        self.country = country
        self.logger = logger
        country_filter = Country(country)
        
        bidder_ids = supply_repo.get(supply_id)
        if bidder_ids is None:
            raise ValueError(f"Supply {supply_id} not found")
        
        self._eligible_bidders = [
            bidder for bidder_id in bidder_ids
            if (bidder := bidder_repo.get(bidder_id)) and bidder.country == country_filter
        ]
        self._bids: dict[str, float] = {}
        self._winner_id: str | None = None
        self._winner_price: float | None = None

    def run(self):
        if self.logger:
            self.logger.info("auction_started", eligible_bidder_count=len(self._eligible_bidders))
        
        for bidder in self._eligible_bidders:
            price = bidder.place_bid()
            if price is not None:
                self._bids[bidder.id] = price
                if self.logger:
                    self.logger.info("bid_received", bidder_id=bidder.id, price=price)
                if self._winner_price is None or price > self._winner_price:
                    self._winner_id = bidder.id
                    self._winner_price = price
            else:
                if self.logger:
                    self.logger.info("no_bid", bidder_id=bidder.id)
        
        if self.logger and self._winner_id:
            self.logger.info("auction_completed", winner=self._winner_id, price=self._winner_price)

    def get_result(self) -> AuctionResult:
        if self._winner_id is None:
            raise ValueError("No valid bids received")
        
        return AuctionResult(winner=self._winner_id, price=self._winner_price)

    def record_stats_async(self):
        return asyncio.create_task(
            record_auction_stats(
                supply_id=self.supply_id,
                country=self.country,
                winner_id=self._winner_id,
                winner_price=self._winner_price,
                bids=self._bids,
                eligible_bidders=self._eligible_bidders
            )
        )
