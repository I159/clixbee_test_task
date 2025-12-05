from ad_exchange_auction.core.models import Bidder, Country
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
