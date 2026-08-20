"""
ML Performance & Walk-Forward Evaluator

This module provides quantitative evaluation comparing:
1. Baseline Raw SMMA Crossover Strategy (No ML filter)
2. ML-Enhanced Strategy (Only ACCEPT signals executed)
3. Loss Avoidance Analysis (Evaluating avoided trades)
4. Day-1 vs Day-2 Walk-Forward Performance Comparison
"""
import os
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

import config

logger = logging.getLogger(__name__)

def evaluate_strategy_performance(trades_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute comprehensive metrics comparing Raw SMMA vs ML-Filtered Strategy.
    
    Args:
        trades_df: DataFrame containing trade logs with columns:
                   ['symbol', 'signal_type', 'entry_ltp', 'exit_ltp', 'pnl',
                    'ml_prediction', 'ml_confidence', 'timestamp']
    
    Returns:
        Dictionary of performance metrics for Raw vs ML-Filtered.
    """
    if trades_df.empty or "pnl" not in trades_df.columns:
        return _empty_metrics()

    completed = trades_df.dropna(subset=["pnl"]).copy()
    if completed.empty:
        return _empty_metrics()

    # 1. Baseline: All Raw Signals
    raw_trades = len(completed)
    raw_wins = (completed["pnl"] > 0).sum()
    raw_losses = (completed["pnl"] < 0).sum()
    raw_win_rate = (raw_wins / raw_trades * 100) if raw_trades > 0 else 0.0
    raw_total_pnl = completed["pnl"].sum()
    raw_gross_profit = completed[completed["pnl"] > 0]["pnl"].sum()
    raw_gross_loss = abs(completed[completed["pnl"] < 0]["pnl"].sum())
    raw_profit_factor = (raw_gross_profit / raw_gross_loss) if raw_gross_loss > 0 else (99.0 if raw_gross_profit > 0 else 1.0)

    # 2. ML-Filtered: Only ACCEPT trades
    ml_accepted = completed[completed["ml_prediction"] == "ACCEPT"]
    ml_trades = len(ml_accepted)
    ml_wins = (ml_accepted["pnl"] > 0).sum()
    ml_losses = (ml_accepted["pnl"] < 0).sum()
    ml_win_rate = (ml_wins / ml_trades * 100) if ml_trades > 0 else 0.0
    ml_total_pnl = ml_accepted["pnl"].sum()
    ml_gross_profit = ml_accepted[ml_accepted["pnl"] > 0]["pnl"].sum()
    ml_gross_loss = abs(ml_accepted[ml_accepted["pnl"] < 0]["pnl"].sum())
    ml_profit_factor = (ml_gross_profit / ml_gross_loss) if ml_gross_loss > 0 else (99.0 if ml_gross_profit > 0 else 1.0)

    # 3. Loss Avoidance: AVOID trades
    ml_avoided = completed[completed["ml_prediction"] == "AVOID"]
    avoided_count = len(ml_avoided)
    avoided_losses_count = (ml_avoided["pnl"] <= 0).sum()
    avoided_loss_amount = abs(ml_avoided[ml_avoided["pnl"] < 0]["pnl"].sum())
    avoidance_accuracy = (avoided_losses_count / avoided_count * 100) if avoided_count > 0 else 0.0

    # Win rate delta
    win_rate_improvement = ml_win_rate - raw_win_rate

    return {
        "raw_strategy": {
            "total_trades": int(raw_trades),
            "winning_trades": int(raw_wins),
            "losing_trades": int(raw_losses),
            "win_rate_pct": round(raw_win_rate, 1),
            "total_pnl": round(raw_total_pnl, 2),
            "profit_factor": round(raw_profit_factor, 2),
            "avg_trade_pnl": round(raw_total_pnl / raw_trades, 2) if raw_trades > 0 else 0.0,
        },
        "ml_filtered_strategy": {
            "total_trades": int(ml_trades),
            "winning_trades": int(ml_wins),
            "losing_trades": int(ml_losses),
            "win_rate_pct": round(ml_win_rate, 1),
            "total_pnl": round(ml_total_pnl, 2),
            "profit_factor": round(ml_profit_factor, 2),
            "avg_trade_pnl": round(ml_total_pnl / ml_trades, 2) if ml_trades > 0 else 0.0,
            "win_rate_improvement_pct": round(win_rate_improvement, 1),
        },
        "loss_avoidance": {
            "avoided_trades": int(avoided_count),
            "correctly_avoided_losses": int(avoided_losses_count),
            "capital_saved": round(avoided_loss_amount, 2),
            "avoidance_precision_pct": round(avoidance_accuracy, 1),
        }
    }

def generate_walk_forward_evaluation(trade_history_path: str = config.TRADE_HISTORY_PATH) -> pd.DataFrame:
    """
    Generate a day-by-day evaluation table comparing Raw vs ML performance across sessions.
    """
    if not os.path.exists(trade_history_path):
        return pd.DataFrame()

    try:
        df = pd.read_csv(trade_history_path)
        if df.empty or "pnl" not in df.columns:
            return pd.DataFrame()

        # Group by date if timestamp exists
        if "timestamp" in df.columns:
            df["date"] = pd.to_datetime(df["timestamp"], errors="coerce").dt.date
        else:
            df["date"] = "Session 1"

        summary_rows = []
        for date, group in df.groupby("date"):
            metrics = evaluate_strategy_performance(group)
            raw = metrics["raw_strategy"]
            ml = metrics["ml_filtered_strategy"]
            avoid = metrics["loss_avoidance"]
            
            summary_rows.append({
                "Date": str(date),
                "Raw Trades": raw["total_trades"],
                "Raw Win Rate": f"{raw['win_rate_pct']}%",
                "Raw P&L (₹)": f"₹{raw['total_pnl']:+,.2f}",
                "ML Trades": ml["total_trades"],
                "ML Win Rate": f"{ml['win_rate_pct']}%",
                "ML P&L (₹)": f"₹{ml['total_pnl']:+,.2f}",
                "Alpha (+Δ%)": f"+{ml['win_rate_improvement_pct']}%",
                "Capital Saved": f"₹{avoid['capital_saved']:,.2f}",
            })

        return pd.DataFrame(summary_rows)
    except Exception as e:
        logger.warning(f"Walk-forward evaluation error: {e}")
        return pd.DataFrame()

def _empty_metrics() -> Dict[str, Any]:
    return {
        "raw_strategy": {"total_trades": 0, "winning_trades": 0, "losing_trades": 0, "win_rate_pct": 0.0, "total_pnl": 0.0, "profit_factor": 0.0, "avg_trade_pnl": 0.0},
        "ml_filtered_strategy": {"total_trades": 0, "winning_trades": 0, "losing_trades": 0, "win_rate_pct": 0.0, "total_pnl": 0.0, "profit_factor": 0.0, "avg_trade_pnl": 0.0, "win_rate_improvement_pct": 0.0},
        "loss_avoidance": {"avoided_trades": 0, "correctly_avoided_losses": 0, "capital_saved": 0.0, "avoidance_precision_pct": 0.0}
    }
