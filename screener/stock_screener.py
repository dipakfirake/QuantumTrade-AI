# =============================================================================
# Stock Screener — Price & Liquidity Filters
# =============================================================================
import logging
from dataclasses import dataclass
from typing import List, Optional

from data_provider.base import DataProvider, Quote
import config

logger = logging.getLogger(__name__)


@dataclass
class ScreenedStock:
    """A stock that passed all screening criteria."""
    symbol: str
    ltp: float
    bid_price: float
    bid_qty: int
    ask_price: float
    ask_qty: int
    total_bid_qty: int
    total_ask_qty: int
    volume: int
    ltq: int


class StockScreener:
    """
    Two-stage stock screener:
    1. Price filter: LTP between PRICE_MIN and PRICE_MAX
    2. Liquidity filter: total bid/ask qty > thresholds
    """

    def __init__(self, provider: DataProvider):
        self.provider = provider

    def screen_by_price(self, quotes: List[Quote]) -> List[Quote]:
        """
        Stage 1: Filter stocks where LTP is between ₹30 and ₹500.
        """
        filtered = [
            q for q in quotes
            if q.ltp > 0 and config.PRICE_MIN <= q.ltp <= config.PRICE_MAX
        ]
        logger.info(
            f"Price filter: {len(filtered)}/{len(quotes)} stocks "
            f"in ₹{config.PRICE_MIN}–₹{config.PRICE_MAX}"
        )
        return filtered

    def screen_by_liquidity(self, quotes: List[Quote]) -> List[ScreenedStock]:
        """
        Stage 2: From price-filtered stocks, keep only those with
        total traded volume > VOLUME_THRESHOLD.
        """
        screened = []
        for q in quotes:
            if q.total_bid_qty >= config.BID_QTY_THRESHOLD and q.total_ask_qty >= config.ASK_QTY_THRESHOLD:
                screened.append(ScreenedStock(
                    symbol=q.symbol,
                    ltp=q.ltp,
                    bid_price=q.bid_price,
                    bid_qty=q.bid_qty,
                    ask_price=q.ask_price,
                    ask_qty=q.ask_qty,
                    total_bid_qty=q.total_bid_qty,
                    total_ask_qty=q.total_ask_qty,
                    volume=q.volume,
                    ltq=q.ltq,
                ))

        logger.info(
            f"Liquidity filter: {len(screened)}/{len(quotes)} stocks "
            f"(BidQty>{config.BID_QTY_THRESHOLD:,})"
        )
        return screened

    def full_screen(self, quotes: List[Quote]) -> List[ScreenedStock]:
        """Run both screening stages."""
        price_filtered = self.screen_by_price(quotes)
        return self.screen_by_liquidity(price_filtered)

    def screen_with_depth(self, symbols: List[str],
                          price_filtered_quotes: List[Quote]) -> List[ScreenedStock]:
        """Run liquidity filter on fetched market depth."""
        return self.screen_by_liquidity(price_filtered_quotes)
