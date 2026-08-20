# =============================================================================
# SMMA Crossover Detection
# =============================================================================
import logging
from dataclasses import dataclass
from typing import Optional, Dict
from enum import Enum

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class SignalType(Enum):
    BUY = "BUY"     # SMMA(20) crosses above SMMA(120)
    SELL = "SELL"    # SMMA(20) crosses below SMMA(120)


@dataclass
class CrossoverSignal:
    """Represents a detected SMMA crossover."""
    symbol: str
    signal_type: SignalType
    ltp: float                      # LTP at crossover
    smma_short: float               # SMMA(20) value
    smma_long: float                # SMMA(120) value
    smma_gap_pct: float = 0.0       # Gap as percentage
    bar_index: int = 0              # Index in the series where crossover happened
    timestamp: Optional[str] = None


class CrossoverDetector:
    """
    Detects SMMA(20) / SMMA(120) crossovers.

    Buy Signal:  SMMA(20) crosses ABOVE SMMA(120)
    Sell Signal: SMMA(20) crosses BELOW SMMA(120)
    """

    def __init__(self):
        # Track previous SMMA relationship per symbol to detect crossing
        self._prev_state: Dict[str, str] = {}  # symbol -> "above" | "below" | None

    def detect(self, symbol: str, smma_short: pd.Series,
               smma_long: pd.Series, ltp: float) -> Optional[CrossoverSignal]:
        """
        Check if a crossover just occurred.

        Args:
            symbol: Stock symbol
            smma_short: SMMA(20) Series
            smma_long: SMMA(120) Series
            ltp: Current LTP

        Returns:
            CrossoverSignal if crossover detected, else None
        """
        # Need at least 2 valid data points to detect a crossing
        valid_mask = smma_short.notna() & smma_long.notna()
        valid_indices = smma_short.index[valid_mask]

        if len(valid_indices) < 2:
            return None

        # Current and previous relationship
        curr_short = smma_short.iloc[-1]
        curr_long = smma_long.iloc[-1]
        prev_short = smma_short.iloc[-2]
        prev_long = smma_long.iloc[-2]

        if np.isnan(curr_short) or np.isnan(curr_long):
            return None
        if np.isnan(prev_short) or np.isnan(prev_long):
            return None

        curr_above = curr_short > curr_long
        prev_above = prev_short > prev_long

        # Determine current state
        curr_state = "above" if curr_above else "below"
        prev_state = self._prev_state.get(symbol)

        # Update state
        self._prev_state[symbol] = curr_state

        # Detect crossover
        signal = None
        if prev_above is False and curr_above is True:
            # SMMA(20) just crossed above SMMA(120) → BUY
            smma_gap = ((curr_short - curr_long) / curr_long) * 100
            signal = CrossoverSignal(
                symbol=symbol,
                signal_type=SignalType.BUY,
                ltp=ltp,
                smma_short=curr_short,
                smma_long=curr_long,
                smma_gap_pct=smma_gap,
                bar_index=len(smma_short) - 1,
            )
            logger.info(f"🟢 BUY crossover detected for {symbol} at ₹{ltp:.2f}")

        elif prev_above is True and curr_above is False:
            # SMMA(20) just crossed below SMMA(120) → SELL
            smma_gap = ((curr_short - curr_long) / curr_long) * 100
            signal = CrossoverSignal(
                symbol=symbol,
                signal_type=SignalType.SELL,
                ltp=ltp,
                smma_short=curr_short,
                smma_long=curr_long,
                smma_gap_pct=smma_gap,
                bar_index=len(smma_short) - 1,
            )
            logger.info(f"🔴 SELL crossover detected for {symbol} at ₹{ltp:.2f}")

        return signal

    def detect_all_historical(self, symbol: str, smma_short: pd.Series,
                              smma_long: pd.Series,
                              close: pd.Series) -> list:
        """
        Detect ALL crossovers in a historical series (for ML training).

        Returns list of CrossoverSignal objects.
        """
        valid_mask = smma_short.notna() & smma_long.notna()
        signals = []

        prev_above = None
        for i in range(len(smma_short)):
            if not valid_mask.iloc[i]:
                continue

            curr_short = smma_short.iloc[i]
            curr_long = smma_long.iloc[i]
            curr_above = curr_short > curr_long

            if prev_above is not None and prev_above != curr_above:
                signal_type = SignalType.BUY if curr_above else SignalType.SELL
                smma_gap = ((curr_short - curr_long) / curr_long) * 100
                ltp = close.iloc[i]

                signals.append(CrossoverSignal(
                    symbol=symbol,
                    signal_type=signal_type,
                    ltp=ltp,
                    smma_short=curr_short,
                    smma_long=curr_long,
                    smma_gap_pct=smma_gap,
                    bar_index=i,
                    timestamp=str(smma_short.index[i]),
                ))

            prev_above = curr_above

        return signals

    def get_current_state(self, symbol: str) -> Optional[str]:
        """Get whether SMMA(20) is currently above or below SMMA(120)."""
        return self._prev_state.get(symbol)

    def reset(self, symbol: Optional[str] = None):
        """Reset tracked state."""
        if symbol:
            self._prev_state.pop(symbol, None)
        else:
            self._prev_state.clear()
