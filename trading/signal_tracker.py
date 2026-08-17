# =============================================================================
# Signal Tracker — Manages open trades, entry/exit, P&L
# =============================================================================
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime

from indicators.crossover import CrossoverSignal, SignalType

logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """Represents a single trade from entry to exit."""
    symbol: str
    signal_type: SignalType         # BUY or SELL
    entry_ltp: float
    entry_time: str
    exit_ltp: Optional[float] = None
    exit_time: Optional[str] = None
    pnl: Optional[float] = None
    status: str = "OPEN"            # OPEN | CLOSED
    ml_prediction: str = ""         # ACCEPT | AVOID
    ml_confidence: float = 0.0
    ml_reason: str = ""

    @property
    def is_open(self) -> bool:
        return self.status == "OPEN"

    @property
    def is_profitable(self) -> Optional[bool]:
        if self.pnl is None:
            return None
        return self.pnl > 0


class SignalTracker:
    """
    Tracks open positions and computes P&L.

    Trading Logic (from assignment):
    - BUY trade: Entry at LTP when SMMA(20) crosses above SMMA(120).
                 Exit when SMMA(20) crosses below SMMA(120).
                 P&L = Exit LTP - Entry LTP
    - SELL trade: Entry at LTP when SMMA(20) crosses below SMMA(120).
                  Exit when SMMA(20) crosses above SMMA(120).
                  P&L = Entry LTP - Exit LTP
    """

    def __init__(self):
        self._open_trades: Dict[str, Trade] = {}   # symbol -> open Trade
        self._trade_history: List[Trade] = []       # all completed trades

    def process_signal(self, signal: CrossoverSignal,
                       ml_prediction: str = "",
                       ml_confidence: float = 0.0,
                       ml_reason: str = "") -> Optional[Trade]:
        """
        Process a new crossover signal.

        - If there's an open trade for this symbol, close it first
        - Open a new trade based on the signal

        Returns the closed trade (if any) for P&L reporting.
        """
        closed_trade = None

        # Check if there's an open trade to close
        if signal.symbol in self._open_trades:
            open_trade = self._open_trades[signal.symbol]

            # Close the existing trade
            open_trade.exit_ltp = signal.ltp
            open_trade.exit_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            open_trade.status = "CLOSED"

            # Calculate P&L
            if open_trade.signal_type == SignalType.BUY:
                # Buy trade: P&L = Sell LTP − Buy LTP
                open_trade.pnl = open_trade.exit_ltp - open_trade.entry_ltp
            else:
                # Sell trade: P&L = Entry LTP − Exit LTP (i.e., Sell − Buy)
                open_trade.pnl = open_trade.entry_ltp - open_trade.exit_ltp

            self._trade_history.append(open_trade)
            closed_trade = open_trade
            del self._open_trades[signal.symbol]

            profit_str = f"₹{open_trade.pnl:+.2f}"
            emoji = "✅" if open_trade.pnl > 0 else "❌"
            logger.info(
                f"{emoji} Closed {open_trade.signal_type.value} trade on "
                f"{signal.symbol}: {profit_str}"
            )

        # Open a new trade
        new_trade = Trade(
            symbol=signal.symbol,
            signal_type=signal.signal_type,
            entry_ltp=signal.ltp,
            entry_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ml_prediction=ml_prediction,
            ml_confidence=ml_confidence,
            ml_reason=ml_reason,
        )
        self._open_trades[signal.symbol] = new_trade

        logger.info(
            f"Opened {signal.signal_type.value} trade on {signal.symbol} "
            f"at ₹{signal.ltp:.2f} | ML: {ml_prediction} ({ml_confidence:.0%})"
        )

        return closed_trade

    def get_open_trades(self) -> Dict[str, Trade]:
        """Return all currently open trades."""
        return self._open_trades.copy()

    def get_trade_history(self) -> List[Trade]:
        """Return all completed trades."""
        return self._trade_history.copy()

    def get_stats(self) -> dict:
        """Compute aggregate trading statistics."""
        if not self._trade_history:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "avg_profit": 0.0,
                "avg_loss": 0.0,
                "total_pnl": 0.0,
                "ml_accepted_wins": 0,
                "ml_avoided_losses": 0,
            }

        winners = [t for t in self._trade_history if t.pnl and t.pnl > 0]
        losers = [t for t in self._trade_history if t.pnl and t.pnl <= 0]

        ml_accepted = [t for t in self._trade_history if t.ml_prediction == "ACCEPT"]
        ml_avoided = [t for t in self._trade_history if t.ml_prediction == "AVOID"]

        return {
            "total_trades": len(self._trade_history),
            "winning_trades": len(winners),
            "losing_trades": len(losers),
            "win_rate": len(winners) / len(self._trade_history) * 100 if self._trade_history else 0,
            "avg_profit": sum(t.pnl for t in winners) / len(winners) if winners else 0,
            "avg_loss": sum(t.pnl for t in losers) / len(losers) if losers else 0,
            "total_pnl": sum(t.pnl for t in self._trade_history if t.pnl),
            "ml_accepted_wins": len([t for t in ml_accepted if t.pnl and t.pnl > 0]),
            "ml_avoided_losses": len([t for t in ml_avoided if t.pnl and t.pnl <= 0]),
            "open_positions": len(self._open_trades),
        }

    def has_open_trade(self, symbol: str) -> bool:
        """Check if there's an open trade for a symbol."""
        return symbol in self._open_trades
