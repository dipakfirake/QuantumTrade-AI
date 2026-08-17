# =============================================================================
# SMMA (Smoothed Moving Average) Calculator
# =============================================================================
import numpy as np
import pandas as pd
from typing import Tuple, Optional

import config


def calculate_smma(series: pd.Series, length: int) -> pd.Series:
    """
    Calculate Smoothed Moving Average (SMMA).

    The SMMA is similar to an EMA but uses a different smoothing factor:
        SMMA[0..length-1] = SMA of first 'length' values
        SMMA[i] = (SMMA[i-1] * (length - 1) + Close[i]) / length

    Args:
        series: Price series (typically Close prices)
        length: SMMA period (e.g., 20 or 120)

    Returns:
        pandas Series with SMMA values (NaN for insufficient data)
    """
    if len(series) < length:
        return pd.Series(np.nan, index=series.index)

    smma = np.full(len(series), np.nan)

    # First SMMA value = SMA of first 'length' bars
    smma[length - 1] = series.iloc[:length].mean()

    # Recursive calculation
    for i in range(length, len(series)):
        smma[i] = (smma[i - 1] * (length - 1) + series.iloc[i]) / length

    return pd.Series(smma, index=series.index)


def get_smma_pair(ohlcv_df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
    """
    Calculate both SMMA(20) and SMMA(120) from OHLCV data.

    Args:
        ohlcv_df: DataFrame with a 'Close' column

    Returns:
        Tuple of (smma_short, smma_long) Series
    """
    close = ohlcv_df["Close"]
    smma_short = calculate_smma(close, config.SMMA_SHORT)
    smma_long = calculate_smma(close, config.SMMA_LONG)
    return smma_short, smma_long


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index (RSI).

    Used as an additional ML feature for crossover analysis.
    """
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()

    # Use SMMA-style smoothing after initial SMA
    for i in range(period, len(series)):
        avg_gain.iloc[i] = (avg_gain.iloc[i - 1] * (period - 1) + gain.iloc[i]) / period
        avg_loss.iloc[i] = (avg_loss.iloc[i - 1] * (period - 1) + loss.iloc[i]) / period

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_atr(ohlcv_df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Average True Range (ATR).

    Used as a volatility feature for ML.
    """
    high = ohlcv_df["High"]
    low = ohlcv_df["Low"]
    close = ohlcv_df["Close"]

    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period, min_periods=period).mean()

    # Smooth with SMMA-style after initial SMA
    for i in range(period, len(tr)):
        atr.iloc[i] = (atr.iloc[i - 1] * (period - 1) + tr.iloc[i]) / period

    return atr
