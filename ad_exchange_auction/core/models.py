import random
from enum import Enum

from pydantic import BaseModel


class Country(Enum):
    US = "US"
    GB = "GB"


class Bidder(BaseModel):
    id: str
    country: Country

    def place_bid(self) -> float | None:
        if random.random() < 0.3:
            return None
        return round(random.uniform(0.01, 1.00), 2)


class Supply(BaseModel):
    id: str
    bidders: list[Bidder]


class Bid(BaseModel):
    bidder_id: str
    price: float | None


class AuctionResult(BaseModel):
    winner: str
    price: float


class BidRequest(BaseModel):
    supply_id: str


class BidderStatistics(BaseModel):
    wins: int
    total_revenue: float
    no_bids: int


class IdentifiedBidderStatistics(BaseModel):
    bidder_id: str
    statistics: BidderStatistics


class SupplyStatistics(BaseModel):
    total_requests: int
    requests_per_country: dict[str, int]
    bidders: list[IdentifiedBidderStatistics]
