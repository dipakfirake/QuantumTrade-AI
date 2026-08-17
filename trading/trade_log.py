# =============================================================================
# Trade Log — Persistent CSV storage for trade history
# =============================================================================
import os
import csv
import logging
from typing import List, Optional

import pandas as pd

from trading.signal_tracker import Trade
import config

logger = logging.getLogger(__name__)

TRADE_LOG_COLUMNS = [
    "timestamp", "symbol", "signal", "entry_price", "exit_price",
    "pnl", "status", "ml_prediction", "ml_confidence", "ml_reason",
]


def init_trade_log():
    """Create the trade history CSV with headers if it doesn't exist."""
    os.makedirs(os.path.dirname(config.TRADE_HISTORY_PATH), exist_ok=True)
    if not os.path.exists(config.TRADE_HISTORY_PATH):
        with open(config.TRADE_HISTORY_PATH, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(TRADE_LOG_COLUMNS)
        logger.info(f"Created trade log: {config.TRADE_HISTORY_PATH}")


def append_trade(trade: Trade):
    """Append a completed trade to the CSV log."""
    init_trade_log()
    with open(config.TRADE_HISTORY_PATH, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            trade.exit_time or trade.entry_time,
            trade.symbol,
            trade.signal_type.value,
            f"{trade.entry_ltp:.2f}",
            f"{trade.exit_ltp:.2f}" if trade.exit_ltp else "",
            f"{trade.pnl:.2f}" if trade.pnl is not None else "",
            trade.status,
            trade.ml_prediction,
            f"{trade.ml_confidence:.4f}",
            trade.ml_reason,
        ])


def read_trade_log() -> pd.DataFrame:
    """Read the full trade history as a DataFrame."""
    if not os.path.exists(config.TRADE_HISTORY_PATH):
        return pd.DataFrame(columns=TRADE_LOG_COLUMNS)
    try:
        return pd.read_csv(config.TRADE_HISTORY_PATH)
    except Exception as e:
        logger.warning(f"Could not read trade log: {e}")
        return pd.DataFrame(columns=TRADE_LOG_COLUMNS)


def get_trade_summary() -> dict:
    """Quick summary of the trade log."""
    df = read_trade_log()
    if df.empty:
        return {"total": 0, "profitable": 0, "loss": 0, "total_pnl": 0}

    df["pnl"] = pd.to_numeric(df["pnl"], errors="coerce")
    profitable = df[df["pnl"] > 0]
    loss = df[df["pnl"] <= 0]

    return {
        "total": len(df),
        "profitable": len(profitable),
        "loss": len(loss),
        "total_pnl": df["pnl"].sum(),
        "win_rate": len(profitable) / len(df) * 100 if len(df) > 0 else 0,
    }
