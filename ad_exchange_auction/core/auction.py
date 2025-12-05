from ad_exchange_auction.core.models import AuctionResult, Bidder, Country
from ad_exchange_auction.core.repository import BidderRepository, SupplyRepository


class Auction:
    def __init__(self, supply_id: str, country: str, supply_repo: SupplyRepository, bidder_repo: BidderRepository):
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
        for bidder in self._eligible_bidders:
            price = bidder.place_bid()
            if price is not None:
                self._bids[bidder.id] = price
                if self._winner_price is None or price > self._winner_price:
                    self._winner_id = bidder.id
                    self._winner_price = price

    def get_result(self) -> AuctionResult:
        if self._winner_id is None:
            raise ValueError("No valid bids received")
        
        return AuctionResult(winner=self._winner_id, price=self._winner_price)
