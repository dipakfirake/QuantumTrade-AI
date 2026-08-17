# =============================================================================
# Abstract Data Provider Interface
# =============================================================================
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
import pandas as pd


@dataclass
class Quote:
    """Real-time quote for a single stock."""
    symbol: str
    ltp: float                      # Last Traded Price
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0             # Previous close
    volume: int = 0                 # Cumulative volume today
    ltq: int = 0                    # Last Traded Quantity
    bid_price: float = 0.0         # Best bid
    bid_qty: int = 0               # Best bid quantity
    ask_price: float = 0.0         # Best ask
    ask_qty: int = 0               # Best ask quantity
    total_bid_qty: int = 0         # Total bid quantity across all levels
    total_ask_qty: int = 0         # Total ask quantity across all levels
    timestamp: Optional[str] = None


@dataclass
class DepthLevel:
    """Single level of market depth."""
    price: float
    quantity: int
    orders: int = 0


@dataclass
class MarketDepth:
    """Full market depth (up to 5 levels)."""
    symbol: str
    bids: List[DepthLevel] = field(default_factory=list)   # Buy side
    asks: List[DepthLevel] = field(default_factory=list)   # Sell side
    total_bid_qty: int = 0
    total_ask_qty: int = 0


class DataProvider(ABC):
    """Abstract base class for market data providers."""

    @abstractmethod
    def get_all_nse_symbols(self) -> List[str]:
        """Return list of all NSE equity symbols."""
        ...

    @abstractmethod
    def get_quote(self, symbol: str) -> Optional[Quote]:
        """Fetch real-time quote for a single symbol."""
        ...

    @abstractmethod
    def get_quotes_batch(self, symbols: List[str]) -> List[Quote]:
        """Fetch quotes for multiple symbols (with rate limiting)."""
        ...

    @abstractmethod
    def get_market_depth(self, symbol: str) -> Optional[MarketDepth]:
        """Fetch 5-level market depth for a symbol."""
        ...

    @abstractmethod
    def get_intraday_ohlcv(self, symbol: str, interval: str = "1m",
                           period: str = "5d") -> Optional[pd.DataFrame]:
        """Fetch intraday OHLCV data for SMMA calculation.

        Returns DataFrame with columns: Open, High, Low, Close, Volume
        and DatetimeIndex.
        """
        ...

    @abstractmethod
    def get_historical_ohlcv(self, symbol: str, interval: str = "1h",
                             period: str = "6mo") -> Optional[pd.DataFrame]:
        """Fetch historical OHLCV data for ML training.

        Returns DataFrame with columns: Open, High, Low, Close, Volume
        and DatetimeIndex.
        """
        ...
