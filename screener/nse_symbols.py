# =============================================================================
# NSE Symbols — Fetch and cache the list of all NSE equity symbols
# =============================================================================
import os
import logging
import pandas as pd
from typing import List
from datetime import datetime, timedelta

import config

logger = logging.getLogger(__name__)


def fetch_nse_symbols(force_refresh: bool = False) -> List[str]:
    """
    Fetch all NSE equity symbols. Uses local cache with daily refresh.

    Returns:
        List of symbol strings, e.g. ["RELIANCE", "TCS", ...]
    """
    cache_path = config.NSE_SYMBOLS_CACHE_PATH
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)

    # Check if cache exists and is fresh (< 24 hours old)
    if not force_refresh and os.path.exists(cache_path):
        try:
            mod_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
            if datetime.now() - mod_time < timedelta(hours=24):
                df = pd.read_csv(cache_path)
                symbols = df["SYMBOL"].dropna().tolist()
                if len(symbols) > 50:
                    logger.info(f"Loaded {len(symbols)} symbols from cache")
                    return symbols
        except Exception as e:
            logger.warning(f"Cache read failed: {e}")

    # Fetch from NSE archives using requests with timeout
    url = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
    try:
        import requests
        import io
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml",
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        df = pd.read_csv(io.StringIO(response.text))
        symbols = df["SYMBOL"].dropna().tolist()
        df[["SYMBOL", "NAME OF COMPANY"]].to_csv(cache_path, index=False)
        logger.info(f"Fetched and cached {len(symbols)} NSE symbols")
        return symbols
    except Exception as e:
        logger.error(f"NSE symbol fetch failed: {e}")

    # Last resort — try loading stale cache
    if os.path.exists(cache_path):
        try:
            df = pd.read_csv(cache_path)
            return df["SYMBOL"].dropna().tolist()
        except Exception:
            pass

    logger.error("No symbol list available — using fallback list")
    return [
        "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN",
        "BHARTIARTL", "ITC", "KOTAKBANK", "LT", "AXISBANK", "WIPRO",
        "HCLTECH", "MARUTI", "TITAN", "SUNPHARMA", "BAJFINANCE",
        "ASIANPAINT", "ULTRACEMCO", "NESTLEIND", "TATAMOTORS",
        "POWERGRID", "NTPC", "ONGC", "COALINDIA", "TATASTEEL",
        "JSWSTEEL", "HINDALCO", "ADANIENT", "ADANIPORTS", "GRASIM",
        "CIPLA", "DRREDDY", "APOLLOHOSP", "EICHERMOT", "HEROMOTOCO",
        "BAJAJ-AUTO", "M&M", "TECHM", "INDUSINDBK", "BPCL",
        "DIVISLAB", "SBILIFE", "BRITANNIA", "HDFCLIFE", "TATACONSUM",
        "HINDUNILVR", "UPL", "VEDL", "BANKBARODA", "PNB",
    ]

def get_symbol_name_map() -> dict:
    """Return {symbol: company_name} mapping."""
    cache_path = config.NSE_SYMBOLS_CACHE_PATH
    if os.path.exists(cache_path):
        try:
            df = pd.read_csv(cache_path)
            return dict(zip(df["SYMBOL"], df["NAME OF COMPANY"]))
        except Exception:
            pass
    return {}
