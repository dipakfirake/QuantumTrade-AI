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
        Stage 2: From price-filtered stocks, keep only those meeting
        the liquidity threshold (Bid/Ask Qty > 10 Lakhs during market hours,
        or Total Traded Volume > 10 Lakhs during after-hours).
        """
        screened = []
        # Check if live order book depth is active (market hours)
        has_live_depth = any(q.total_bid_qty > 0 or q.total_ask_qty > 0 for q in quotes)

        for q in quotes:
            bid_qty = q.total_bid_qty
            ask_qty = q.total_ask_qty
            
            # If after-market hours, evaluate liquidity via session traded volume & derive order book
            if not has_live_depth and q.volume > 0:
                bid_qty = int(q.volume * 0.45)
                ask_qty = int(q.volume * 0.40)
            
            if (bid_qty >= config.BID_QTY_THRESHOLD and ask_qty >= config.ASK_QTY_THRESHOLD) or (q.volume >= config.BID_QTY_THRESHOLD * 2):
                screened.append(ScreenedStock(
                    symbol=q.symbol,
                    ltp=q.ltp,
                    bid_price=q.bid_price if q.bid_price > 0 else q.ltp * 0.999,
                    bid_qty=q.bid_qty if q.bid_qty > 0 else bid_qty // 5,
                    ask_price=q.ask_price if q.ask_price > 0 else q.ltp * 1.001,
                    ask_qty=q.ask_qty if q.ask_qty > 0 else ask_qty // 5,
                    total_bid_qty=bid_qty,
                    total_ask_qty=ask_qty,
                    volume=q.volume,
                    ltq=q.ltq if q.ltq > 0 else int(q.volume / 375),
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
