"""
History Cache for OHLCV data

Stores per-symbol OHLCV as parquet files under `data/historical_cache/` to
avoid repeated downloads from Yahoo Finance during training and development.

Usage:
    from data_provider.history_cache import get_historical
    df = get_historical("RELIANCE", interval="1h", period="6mo")
"""
import os
import json
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

CACHE_DIR = os.path.join("data", "historical_cache")
os.makedirs(CACHE_DIR, exist_ok=True)


def _cache_path(symbol: str, interval: str, period: str) -> str:
    safe = f"{symbol}.{interval}.{period}".replace("/", "-")
    return os.path.join(CACHE_DIR, f"{safe}.parquet")


def _meta_path(symbol: str, interval: str, period: str) -> str:
    safe = f"{symbol}.{interval}.{period}".replace("/", "-")
    return os.path.join(CACHE_DIR, f"{safe}.meta.json")


def get_historical(symbol: str, interval: str = "1h", period: str = "6mo", ttl_hours: int = 24, force_refresh: bool = False) -> Optional[pd.DataFrame]:
    """Return cached OHLCV DataFrame if fresh; otherwise download via yfinance and cache it.

    - `ttl_hours` controls how long the cache is considered fresh.
    - `force_refresh=True` forces re-download.
    """
    import yfinance as yf

    path = _cache_path(symbol, interval, period)
    meta = _meta_path(symbol, interval, period)

    if not force_refresh and os.path.exists(path) and os.path.exists(meta):
        try:
            with open(meta, "r") as f:
                info = json.load(f)
            ts = datetime.fromisoformat(info.get("fetched_at"))
            if datetime.utcnow() - ts < timedelta(hours=ttl_hours):
                # Load cached parquet
                df = pd.read_parquet(path)
                return df
        except Exception:
            # If metadata is corrupt, fall through to re-download
            pass

    # Download via yfinance
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        df = ticker.history(period=period, interval=interval)
        if df is None or df.empty:
            return None
        df = df.rename(columns={
            "Open": "Open", "High": "High", "Low": "Low",
            "Close": "Close", "Volume": "Volume",
        })
        df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()

        # Save parquet and meta
        try:
            df.to_parquet(path)
            with open(meta, "w") as f:
                json.dump({"fetched_at": datetime.utcnow().isoformat()}, f)
        except Exception:
            # Ignore caching errors
            pass

        return df
    except Exception:
        return None
