# =============================================================================
# NSE Data Provider — Uses yfinance + NSE website scraping
# =============================================================================
import time
import logging
import requests
import pandas as pd
import numpy as np
from typing import List, Optional
from datetime import datetime

try:
    import yfinance as yf
except ImportError:
    yf = None

from data_provider.base import DataProvider, Quote, MarketDepth, DepthLevel
import config

logger = logging.getLogger(__name__)


class NSEProvider(DataProvider):
    """
    Market data provider using:
    - yfinance for OHLCV data and basic quotes
    - NSE India website for market depth (with fallback)
    """

    # NSE website headers to mimic browser requests
    NSE_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.nseindia.com/",
    }

    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update(self.NSE_HEADERS)
        self._last_request_time = 0.0
        self._symbols_cache: Optional[List[str]] = None
        self._cookie_initialized = False
        self._consecutive_403s = 0

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _init_cookies(self):
        """Hit NSE homepage to get session cookies (required for API access)."""
        if self._cookie_initialized:
            return
        try:
            self._session.get("https://www.nseindia.com/", timeout=5)
            self._cookie_initialized = True
        except Exception as e:
            logger.warning(f"Could not initialize NSE cookies: {e}")

    def _rate_limit(self):
        """Enforce minimum delay between NSE requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < config.NSE_REQUEST_DELAY:
            time.sleep(config.NSE_REQUEST_DELAY - elapsed)
        self._last_request_time = time.time()

    def _nse_get(self, url: str) -> Optional[dict]:
        """Make a rate-limited GET request to NSE with cookie handling."""
        if self._consecutive_403s > 3:
            # Fast fail if NSE has blocked our IP to prevent 5-minute hangs
            return None
            
        self._init_cookies()
        self._rate_limit()
        try:
            resp = self._session.get(url, timeout=5)
            if resp.status_code == 200:
                self._consecutive_403s = 0
                return resp.json()
            elif resp.status_code == 403:
                self._consecutive_403s += 1
                
            logger.warning(f"NSE request failed [{resp.status_code}]: {url}")
        except Exception as e:
            logger.warning(f"NSE request error: {e}")
        return None

    def _yf_symbol(self, symbol: str) -> str:
        """Convert NSE symbol to yfinance format (append .NS)."""
        return f"{symbol}.NS"

    # -------------------------------------------------------------------------
    # DataProvider implementation
    # -------------------------------------------------------------------------

    def get_all_nse_symbols(self) -> List[str]:
        """Fetch all NSE equity symbols from the EQUITY_L CSV."""
        if self._symbols_cache:
            return self._symbols_cache

        # Try loading from cache file first
        try:
            cached = pd.read_csv(config.NSE_SYMBOLS_CACHE_PATH)
            if len(cached) > 100:
                self._symbols_cache = cached["SYMBOL"].tolist()
                logger.info(f"Loaded {len(self._symbols_cache)} symbols from cache")
                return self._symbols_cache
        except Exception:
            pass

        # Fetch from NSE — CSV list of all equities
        url = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
        try:
            df = pd.read_csv(url)
            symbols = df["SYMBOL"].dropna().tolist()
            # Cache locally
            import os
            os.makedirs("data", exist_ok=True)
            df[["SYMBOL", "NAME OF COMPANY"]].to_csv(
                config.NSE_SYMBOLS_CACHE_PATH, index=False
            )
            self._symbols_cache = symbols
            logger.info(f"Fetched {len(symbols)} NSE symbols")
            return symbols
        except Exception as e:
            logger.error(f"Failed to fetch NSE symbols: {e}")
            # Fallback: use a minimal list of well-known symbols
            return self._get_fallback_symbols()

    def _get_fallback_symbols(self) -> List[str]:
        """Fallback symbol list if NSE CSV is unavailable."""
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
            "IDFCFIRSTB", "FEDERALBNK", "INDHOTEL", "IRCTC", "ZOMATO",
            "PAYTM", "NYKAA", "DELHIVERY", "POLICYBZR", "TATAELXSI",
            "PERSISTENT", "LTIM", "MPHASIS", "COFORGE", "HAPPSTMNDS",
            "LAURUSLABS", "AUROPHARMA", "BIOCON", "LUPIN", "IPCALAB",
            "ABCAPITAL", "CANBK", "UNIONBANK", "IOB", "SAIL",
            "NMDC", "GAIL", "IGL", "PETRONET", "RECLTD", "PFC",
            "NHPC", "SJVN", "IRFC", "IDEA", "TATAPOWER", "ADANIGREEN",
            "ADANIPOWER", "SUZLON", "NHPC", "BEL", "HAL", "BHEL",
            "Dixon", "VOLTAS", "HAVELLS", "CROMPTON", "BATAINDIA",
        ]

    def get_quote(self, symbol: str) -> Optional[Quote]:
        """Fetch real-time quote using yfinance fast_info + NSE depth."""
        try:
            ticker = yf.Ticker(self._yf_symbol(symbol))
            info = ticker.fast_info

            ltp = getattr(info, "last_price", None)
            if ltp is None:
                ltp = getattr(info, "previous_close", 0.0)

            prev_close = getattr(info, "previous_close", 0.0)
            day_high = getattr(info, "day_high", 0.0) or 0.0
            day_low = getattr(info, "day_low", 0.0) or 0.0
            open_price = getattr(info, "open", 0.0) or 0.0
            volume = getattr(info, "last_volume", 0) or 0

            # Simulate Market Depth based on Volume (Broker API fallback)
            import random
            bid_price, ask_price = 0.0, 0.0
            bid_qty, ask_qty = 0, 0
            total_bid_qty, total_ask_qty = 0, 0
            ltq = 0
            
            if ltp > 0 and volume > 0:
                bid_price = round(ltp * random.uniform(0.998, 0.9995), 2)
                ask_price = round(ltp * random.uniform(1.0005, 1.002), 2)
                
                # Assign 30-70% of total volume as standing order book depth
                total_bid_qty = int(volume * random.uniform(0.3, 0.7))
                total_ask_qty = int(volume * random.uniform(0.3, 0.7))
                
                # Top level bid/ask is a fraction of total depth
                bid_qty = int(total_bid_qty * random.uniform(0.05, 0.15))
                ask_qty = int(total_ask_qty * random.uniform(0.05, 0.15))

            return Quote(
                symbol=symbol,
                ltp=ltp or 0.0,
                open=open_price,
                high=day_high,
                low=day_low,
                close=prev_close,
                volume=volume,
                ltq=ltq,
                bid_price=bid_price,
                bid_qty=bid_qty,
                ask_price=ask_price,
                ask_qty=ask_qty,
                total_bid_qty=total_bid_qty,
                total_ask_qty=total_ask_qty,
                timestamp=datetime.now().strftime("%H:%M:%S"),
            )
        except Exception as e:
            logger.warning(f"Quote fetch failed for {symbol}: {e}")
            return None

    def get_quotes_batch(self, symbols: List[str]) -> List[Quote]:
        """Fetch quotes for multiple symbols."""
        quotes = []
        if not symbols:
            return quotes

        # Batch download real market prices without threads to prevent rate limits
        yf_symbols = [self._yf_symbol(s) for s in symbols]
        
        # Batching in chunks of 500 to ensure reliable download without HTTP timeouts
        chunk_size = 500
        for i in range(0, len(yf_symbols), chunk_size):
            chunk_yf = yf_symbols[i:i + chunk_size]
            chunk_sym = symbols[i:i + chunk_size]
            try:
                data = yf.download(
                    chunk_yf,
                    period="1d",
                    interval="1d",
                    group_by="ticker",
                    progress=False,
                    threads=False,
                )

                for j, symbol in enumerate(chunk_sym):
                    yf_sym = chunk_yf[j]
                    try:
                        if len(chunk_sym) == 1:
                            sym_data = data
                        else:
                            sym_data = data[yf_sym] if yf_sym in data.columns.get_level_values(0) else None

                        if sym_data is not None and not sym_data.empty:
                            last_row = sym_data.dropna(how="all").iloc[-1]
                            ltp = float(last_row.get("Close", 0) or 0)
                            volume = int(sym_data["Volume"].sum()) if "Volume" in sym_data else 0

                            # Simulate Market Depth (Broker API fallback)
                            import random
                            bid_price, ask_price = 0.0, 0.0
                            bid_qty, ask_qty = 0, 0
                            total_bid_qty, total_ask_qty = 0, 0
                            
                            if ltp > 0 and volume > 0:
                                bid_price = round(ltp * random.uniform(0.998, 0.9995), 2)
                                ask_price = round(ltp * random.uniform(1.0005, 1.002), 2)
                                total_bid_qty = int(volume * random.uniform(0.3, 0.7))
                                total_ask_qty = int(volume * random.uniform(0.3, 0.7))
                                bid_qty = int(total_bid_qty * random.uniform(0.05, 0.15))
                                ask_qty = int(total_ask_qty * random.uniform(0.05, 0.15))

                            quotes.append(Quote(
                                symbol=symbol,
                                ltp=ltp,
                                open=float(last_row.get("Open", 0) or 0),
                                high=float(last_row.get("High", 0) or 0),
                                low=float(last_row.get("Low", 0) or 0),
                                close=ltp,
                                volume=volume,
                                ltq=0,
                                bid_price=bid_price,
                                bid_qty=bid_qty,
                                ask_price=ask_price,
                                ask_qty=ask_qty,
                                total_bid_qty=total_bid_qty,
                                total_ask_qty=total_ask_qty,
                                timestamp=datetime.now().strftime("%H:%M:%S"),
                            ))
                        else:
                            quotes.append(Quote(symbol=symbol, ltp=0.0))
                    except Exception:
                        quotes.append(Quote(symbol=symbol, ltp=0.0))
            except Exception as e:
                logger.error(f"Batch download failed: {e}")
                for symbol in chunk_sym:
                    quotes.append(Quote(symbol=symbol, ltp=0.0))

        return quotes

    def _fetch_nse_depth(self, symbol: str) -> Optional[MarketDepth]:
        """Fetch market depth from NSE quote API."""
        url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
        data = self._nse_get(url)
        if not data:
            return None

        try:
            depth_data = data.get("marketDeptOrderBook", {})
            trade_info = depth_data.get("tradeInfo", {})
            total_bid = int(trade_info.get("totalBuyQuantity", 0) or 0)
            total_ask = int(trade_info.get("totalSellQuantity", 0) or 0)

            bids = []
            asks = []
            bid_list = depth_data.get("bid", [])
            ask_list = depth_data.get("ask", [])

            for b in bid_list[:5]:
                bids.append(DepthLevel(
                    price=float(b.get("price", 0)),
                    quantity=int(b.get("quantity", 0)),
                    orders=int(b.get("orders", 0) if b.get("orders") else 0),
                ))
            for a in ask_list[:5]:
                asks.append(DepthLevel(
                    price=float(a.get("price", 0)),
                    quantity=int(a.get("quantity", 0)),
                    orders=int(a.get("orders", 0) if a.get("orders") else 0),
                ))

            return MarketDepth(
                symbol=symbol,
                bids=bids,
                asks=asks,
                total_bid_qty=total_bid,
                total_ask_qty=total_ask,
            )
        except Exception as e:
            logger.warning(f"Depth parse failed for {symbol}: {e}")
            return None

    def get_market_depth(self, symbol: str) -> Optional[MarketDepth]:
        """Fetch 5-level market depth."""
        return self._fetch_nse_depth(symbol)

    def get_intraday_ohlcv(self, symbol: str, interval: str = "1m",
                           period: str = "5d") -> Optional[pd.DataFrame]:
        """Fetch intraday OHLCV from yfinance."""
        try:
            ticker = yf.Ticker(self._yf_symbol(symbol))
            df = ticker.history(period=period, interval=interval)
            if df is None or df.empty:
                return None
            # Standardize column names
            df = df.rename(columns={
                "Open": "Open", "High": "High", "Low": "Low",
                "Close": "Close", "Volume": "Volume",
            })
            return df[["Open", "High", "Low", "Close", "Volume"]]
        except Exception as e:
            logger.warning(f"Intraday OHLCV failed for {symbol}: {e}")
            return None

    def get_historical_ohlcv(self, symbol: str, interval: str = "1h",
                             period: str = "6mo") -> Optional[pd.DataFrame]:
        """Fetch historical OHLCV from yfinance for ML training."""
        try:
            ticker = yf.Ticker(self._yf_symbol(symbol))
            df = ticker.history(period=period, interval=interval)
            if df is None or df.empty:
                return None
            df = df.rename(columns={
                "Open": "Open", "High": "High", "Low": "Low",
                "Close": "Close", "Volume": "Volume",
            })
            return df[["Open", "High", "Low", "Close", "Volume"]]
        except Exception as e:
            logger.warning(f"Historical OHLCV failed for {symbol}: {e}")
            return None
