# =============================================================================
# Feature Engineering — Extract ML features at crossover points
# =============================================================================
import numpy as np
import pandas as pd
from typing import Dict, Optional

from data_provider.cache import TickCache
from indicators.smma import calculate_rsi, calculate_atr
import config


def extract_features_live(symbol: str, tick_cache: TickCache,
                          ohlcv_df: pd.DataFrame,
                          smma_short_val: float, smma_long_val: float,
                          ltp: float,
                          total_bid_qty: int = 0,
                          total_ask_qty: int = 0,
                          bid_price: float = 0.0,
                          ask_price: float = 0.0) -> Dict[str, float]:
    """
    Extract features for a live crossover event.

    Features are designed to capture:
    1. LTQ-based activity surges (primary interest per assignment)
    2. Order book imbalance (bid/ask)
    3. SMMA crossover strength
    4. Price momentum
    5. Volatility context (ATR)
    6. Trend strength (RSI)

    Args:
        symbol: Stock symbol
        tick_cache: TickCache with recent tick data
        ohlcv_df: Recent OHLCV DataFrame
        smma_short_val: Current SMMA(20) value
        smma_long_val: Current SMMA(120) value
        ltp: Current LTP
        total_bid_qty: Total bid quantity
        total_ask_qty: Total ask quantity
        bid_price: Best bid price
        ask_price: Best ask price

    Returns:
        Dictionary of feature name → value
    """
    features = {}

    # --- LTQ-based features (primary per assignment) ---
    avg_ltq_2m = tick_cache.get_avg_ltq(symbol, 2)
    avg_ltq_5m = tick_cache.get_avg_ltq(symbol, 5)
    avg_ltq_20m = tick_cache.get_avg_ltq(symbol, 20)

    features["ltq_ratio_2m_5m"] = (avg_ltq_2m / avg_ltq_5m) if avg_ltq_5m > 0 else 1.0
    features["ltq_ratio_5m_20m"] = (avg_ltq_5m / avg_ltq_20m) if avg_ltq_20m > 0 else 1.0

    # --- ETQ features ---
    etq_5m = tick_cache.get_etq(symbol, 5)
    etq_20m = tick_cache.get_etq(symbol, 20)
    etq_60m = tick_cache.get_etq(symbol, 60)

    features["etq_5m"] = float(etq_5m)
    features["etq_20m"] = float(etq_20m)
    features["etq_60m"] = float(etq_60m)
    features["etq_acceleration"] = (etq_5m / (etq_20m / 4)) if etq_20m > 0 else 1.0

    # --- Bid-Ask features ---
    total_qty = total_bid_qty + total_ask_qty
    features["bid_ask_imbalance"] = (
        (total_bid_qty - total_ask_qty) / total_qty if total_qty > 0 else 0.0
    )
    features["spread_pct"] = (
        ((ask_price - bid_price) / ltp * 100) if ltp > 0 and ask_price > 0 and bid_price > 0 else 0.0
    )

    # --- SMMA features ---
    features["smma_gap_pct"] = (
        ((smma_short_val - smma_long_val) / smma_long_val * 100)
        if smma_long_val > 0 else 0.0
    )

    # --- Price momentum ---
    avg_ltp_20m = tick_cache.get_avg_ltp(symbol, 20)
    avg_ltp_60m = tick_cache.get_avg_ltp(symbol, 60)
    features["price_vs_avg20m"] = (ltp / avg_ltp_20m) if avg_ltp_20m > 0 else 1.0
    features["price_vs_avg60m"] = (ltp / avg_ltp_60m) if avg_ltp_60m > 0 else 1.0

    # --- Volume surge ---
    if ohlcv_df is not None and len(ohlcv_df) > 20:
        vol = ohlcv_df["Volume"]
        avg_vol_20 = vol.iloc[-20:].mean()
        curr_vol = vol.iloc[-1]
        features["volume_surge"] = (curr_vol / avg_vol_20) if avg_vol_20 > 0 else 1.0
    else:
        features["volume_surge"] = 1.0

    # --- RSI ---
    if ohlcv_df is not None and len(ohlcv_df) > config.RSI_PERIOD + 1:
        rsi = calculate_rsi(ohlcv_df["Close"], config.RSI_PERIOD)
        features["rsi_14"] = rsi.iloc[-1] if not np.isnan(rsi.iloc[-1]) else 50.0
    else:
        features["rsi_14"] = 50.0

    # --- ATR (volatility) ---
    if ohlcv_df is not None and len(ohlcv_df) > config.ATR_PERIOD + 1:
        atr = calculate_atr(ohlcv_df, config.ATR_PERIOD)
        atr_val = atr.iloc[-1]
        features["atr_pct"] = (atr_val / ltp * 100) if ltp > 0 and not np.isnan(atr_val) else 0.0
    else:
        features["atr_pct"] = 0.0

    return features


def extract_features_historical(ohlcv_df: pd.DataFrame,
                                crossover_idx: int,
                                smma_short: pd.Series,
                                smma_long: pd.Series) -> Dict[str, float]:
    """
    Extract features from historical OHLCV data at a specific crossover index.
    Used for ML training data generation.

    Since we don't have tick-level data for history, we approximate
    LTQ and ETQ features from volume patterns.
    """
    features = {}
    close = ohlcv_df["Close"]
    volume = ohlcv_df["Volume"]
    ltp = close.iloc[crossover_idx]
    idx = crossover_idx

    # --- LTQ approximation from volume ---
    # Approximate "LTQ ratio" using per-bar volume changes
    if idx >= 5:
        vol_2 = volume.iloc[idx - 1:idx + 1].mean()  # ~2 bars
        vol_5 = volume.iloc[idx - 4:idx + 1].mean()   # ~5 bars
        vol_20 = volume.iloc[max(0, idx - 19):idx + 1].mean()

        features["ltq_ratio_2m_5m"] = (vol_2 / vol_5) if vol_5 > 0 else 1.0
        features["ltq_ratio_5m_20m"] = (vol_5 / vol_20) if vol_20 > 0 else 1.0
    else:
        features["ltq_ratio_2m_5m"] = 1.0
        features["ltq_ratio_5m_20m"] = 1.0

    # --- ETQ approximation ---
    etq_5 = volume.iloc[max(0, idx - 4):idx + 1].sum()
    etq_20 = volume.iloc[max(0, idx - 19):idx + 1].sum()
    etq_60 = volume.iloc[max(0, idx - 59):idx + 1].sum()

    features["etq_5m"] = float(etq_5)
    features["etq_20m"] = float(etq_20)
    features["etq_60m"] = float(etq_60)
    features["etq_acceleration"] = (etq_5 / (etq_20 / 4)) if etq_20 > 0 else 1.0

    # --- Bid-Ask features (unavailable in historical → use volume proxy) ---
    vol_change = volume.iloc[idx] - volume.iloc[idx - 1] if idx > 0 else 0
    price_change = close.iloc[idx] - close.iloc[idx - 1] if idx > 0 else 0
    # Positive vol + positive price → buying pressure (proxy for bid > ask)
    features["bid_ask_imbalance"] = np.sign(price_change) * min(abs(vol_change) / (volume.iloc[idx] + 1), 1.0)
    features["spread_pct"] = 0.05  # Placeholder — typical spread

    # --- SMMA features ---
    s_short = smma_short.iloc[idx]
    s_long = smma_long.iloc[idx]
    features["smma_gap_pct"] = ((s_short - s_long) / s_long * 100) if s_long > 0 else 0.0

    # --- Price momentum ---
    avg_20 = close.iloc[max(0, idx - 19):idx + 1].mean()
    avg_60 = close.iloc[max(0, idx - 59):idx + 1].mean()
    features["price_vs_avg20m"] = (ltp / avg_20) if avg_20 > 0 else 1.0
    features["price_vs_avg60m"] = (ltp / avg_60) if avg_60 > 0 else 1.0

    # --- Volume surge ---
    if idx >= 20:
        avg_vol_20 = volume.iloc[idx - 20:idx].mean()
        features["volume_surge"] = (volume.iloc[idx] / avg_vol_20) if avg_vol_20 > 0 else 1.0
    else:
        features["volume_surge"] = 1.0

    # --- RSI ---
    if idx > config.RSI_PERIOD:
        rsi = calculate_rsi(close.iloc[:idx + 1], config.RSI_PERIOD)
        features["rsi_14"] = rsi.iloc[-1] if not np.isnan(rsi.iloc[-1]) else 50.0
    else:
        features["rsi_14"] = 50.0

    # --- ATR ---
    if idx > config.ATR_PERIOD:
        atr = calculate_atr(ohlcv_df.iloc[:idx + 1], config.ATR_PERIOD)
        atr_val = atr.iloc[-1]
        features["atr_pct"] = (atr_val / ltp * 100) if ltp > 0 and not np.isnan(atr_val) else 0.0
    else:
        features["atr_pct"] = 0.0

    return features


# Feature names in fixed order for model training/inference
FEATURE_NAMES = [
    "ltq_ratio_2m_5m",
    "ltq_ratio_5m_20m",
    "etq_5m",
    "etq_20m",
    "etq_60m",
    "etq_acceleration",
    "bid_ask_imbalance",
    "spread_pct",
    "smma_gap_pct",
    "price_vs_avg20m",
    "price_vs_avg60m",
    "volume_surge",
    "rsi_14",
    "atr_pct",
]
