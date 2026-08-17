# =============================================================================
# Tick Cache — Time-windowed aggregations for ETQ, Avg LTP, Avg LTQ
# =============================================================================
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class TickSnapshot:
    """A single tick data point."""
    timestamp: float        # Unix timestamp
    ltp: float              # Last Traded Price
    ltq: int                # Last Traded Quantity (estimated from volume delta)
    volume: int             # Cumulative volume at this tick
    bid_qty: int = 0
    ask_qty: int = 0


class TickCache:
    """
    In-memory cache for per-symbol tick data.
    Supports time-windowed aggregations for:
    - ETQ (Exchange Traded Quantity): total LTQ over N minutes
    - Average LTP over N minutes
    - Average LTQ over N minutes (for ML features)
    """

    MAX_TICKS_PER_SYMBOL = 7200  # ~2 hours at 1 tick/sec

    def __init__(self):
        self._ticks: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=self.MAX_TICKS_PER_SYMBOL)
        )
        self._prev_volume: Dict[str, int] = {}

    def add_tick(self, symbol: str, ltp: float, volume: int,
                 bid_qty: int = 0, ask_qty: int = 0, ltq: int = 0):
        """
        Record a new tick. If ltq is 0, estimate it from volume delta.
        """
        now = time.time()

        # Estimate LTQ from volume change if not provided directly
        if ltq == 0 and symbol in self._prev_volume:
            delta = volume - self._prev_volume[symbol]
            ltq = max(delta, 0)

        self._prev_volume[symbol] = volume

        snap = TickSnapshot(
            timestamp=now,
            ltp=ltp,
            ltq=ltq,
            volume=volume,
            bid_qty=bid_qty,
            ask_qty=ask_qty,
        )
        self._ticks[symbol].append(snap)

    def _get_window(self, symbol: str, minutes: int):
        """Get ticks within the last N minutes."""
        if symbol not in self._ticks:
            return []
        cutoff = time.time() - (minutes * 60)
        return [t for t in self._ticks[symbol] if t.timestamp >= cutoff]

    def get_etq(self, symbol: str, minutes: int) -> int:
        """Total Exchange Traded Quantity (sum of LTQ) in last N minutes."""
        window = self._get_window(symbol, minutes)
        return sum(t.ltq for t in window)

    def get_avg_ltp(self, symbol: str, minutes: int) -> float:
        """Average LTP over the last N minutes."""
        window = self._get_window(symbol, minutes)
        if not window:
            return 0.0
        return sum(t.ltp for t in window) / len(window)

    def get_avg_ltq(self, symbol: str, minutes: int) -> float:
        """Average LTQ over the last N minutes."""
        window = self._get_window(symbol, minutes)
        if not window:
            return 0.0
        ltqs = [t.ltq for t in window if t.ltq > 0]
        if not ltqs:
            return 0.0
        return sum(ltqs) / len(ltqs)

    def get_tick_count(self, symbol: str) -> int:
        """Number of ticks stored for a symbol."""
        return len(self._ticks.get(symbol, []))

    def get_latest_tick(self, symbol: str) -> Optional[TickSnapshot]:
        """Get the most recent tick for a symbol."""
        ticks = self._ticks.get(symbol)
        if ticks:
            return ticks[-1]
        return None

    def clear(self, symbol: Optional[str] = None):
        """Clear cache for a specific symbol or all symbols."""
        if symbol:
            self._ticks.pop(symbol, None)
            self._prev_volume.pop(symbol, None)
        else:
            self._ticks.clear()
            self._prev_volume.clear()
