import json

from ad_exchange_auction.core.models import Bidder, Country
from ad_exchange_auction.settings import settings


class SupplyRepository:
    def __init__(self):
        self._supplies = None

    def load(self):
        with open(settings.data_file_path, "r") as f:
            data = json.load(f)
        self._supplies = data["supplies"]

    def get(self, supply_id: str) -> list[str] | None:
        return self._supplies.get(supply_id)


class BidderRepository:
    def __init__(self):
        self._bidders = None

    def load(self):
        with open(settings.data_file_path, "r") as f:
            data = json.load(f)
        self._bidders = data["bidders"]

    def get(self, bidder_id: str) -> Bidder | None:
        bidder_data = self._bidders.get(bidder_id)
        if bidder_data is None:
            return None
        return Bidder(id=bidder_id, country=Country(bidder_data["country"]))
