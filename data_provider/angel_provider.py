"""
Angel One Data Provider (scaffold)

Scaffold to integrate Angel One's market data APIs for real LTQ/ETQ and depth.
Fill the implementation using Angel One's developer APIs and your account keys.

Security: do not store API secrets in source. Use environment variables or
`config.py` with proper `.gitignore`/`.env` handling.
"""
from typing import List, Optional
import pandas as pd
from data_provider.base import DataProvider, Quote, MarketDepth, DepthLevel


class AngelProvider(DataProvider):
    def __init__(self, api_key: Optional[str] = None, access_token: Optional[str] = None):
        from utils.secrets import get_env

        self.api_key = api_key or get_env("ANGEL_API_KEY")
        self.access_token = access_token or get_env("ANGEL_ACCESS_TOKEN")
        self._client = None
        try:
            # SmartAPI (Angel Broking) SDK
            from SmartApi import SmartConnect
            if not self.api_key:
                raise EnvironmentError("ANGEL_API_KEY not set in env")
            # Note: actual login flow requires username/password → generate session
            # Here we leave initialization for the user
            self._client = SmartConnect(api_key=self.api_key)
        except Exception:
            self._client = None

    def _ensure_sdk(self):
        if self._client is None:
            raise NotImplementedError(
                "Angel One SmartAPI not initialized. Install SmartApi and set ANGEL_API_KEY/ANGEL_ACCESS_TOKEN env vars."
            )

    def get_all_nse_symbols(self) -> List[str]:
        raise NotImplementedError("Use NSEProvider.get_all_nse_symbols() to fetch symbol list")

    def get_quote(self, symbol: str) -> Optional[Quote]:
        self._ensure_sdk()
        # Try common SDK methods for LTP
        for method_name in ("getLTP", "get_ltp", "ltp", "get_ltp_data"): 
            fn = getattr(self._client, method_name, None)
            if fn:
                resp = fn(symbol)
                return self._map_sdk_quote(symbol, resp)
        # SmartAPI sometimes exposes `ltt` or `get_quote`
        for method_name in ("get_quote", "quote", "getQuote"):
            fn = getattr(self._client, method_name, None)
            if fn:
                resp = fn(symbol)
                return self._map_sdk_quote(symbol, resp)
        raise NotImplementedError("Implement Angel One single quote retrieval using SmartConnect.getLTP() or equivalent")

    def get_quotes_batch(self, symbols: List[str]) -> List[Quote]:
        self._ensure_sdk()
        for method_name in ("getLTPMultiple", "get_ltp_multiple", "getLTPS", "getLTPBatch"):
            fn = getattr(self._client, method_name, None)
            if fn:
                resp = fn(symbols)
                quotes = []
                if isinstance(resp, dict):
                    for sym, data in resp.items():
                        quotes.append(self._map_sdk_quote(sym, data))
                elif isinstance(resp, list):
                    for item in resp:
                        sym = item.get("symbol") if isinstance(item, dict) else None
                        quotes.append(self._map_sdk_quote(sym or "", item))
                return quotes
        # Fallback: call single quote in a loop (rate-limited)
        quotes = []
        for s in symbols:
            try:
                q = self.get_quote(s)
                if q:
                    quotes.append(q)
            except NotImplementedError:
                raise
        return quotes

    def get_market_depth(self, symbol: str) -> Optional[MarketDepth]:
        self._ensure_sdk()
        for method_name in ("get_market_depth", "market_depth", "depth", "get_depth"):
            fn = getattr(self._client, method_name, None)
            if fn:
                resp = fn(symbol)
                return self._map_market_depth(symbol, resp)
        raise NotImplementedError("Implement Angel One market depth retrieval using SmartAPI market depth endpoint")

    def get_intraday_ohlcv(self, symbol: str, interval: str = "1m",
                           period: str = "5d") -> Optional[pd.DataFrame]:
        self._ensure_sdk()
        # SmartAPI historically exposes historical data via `get_historical_data` or `get_candle_data`
        for method_name in ("get_candle_data", "get_historical_data", "historical"):
            fn = getattr(self._client, method_name, None)
            if fn:
                resp = fn(symbol, interval=interval, period=period)
                return self._map_to_ohlcv(resp)
        raise NotImplementedError("Implement Angel One intraday OHLCV retrieval using historical endpoints or data service")

    def get_historical_ohlcv(self, symbol: str, interval: str = "1h",
                             period: str = "6mo") -> Optional[pd.DataFrame]:
        self._ensure_sdk()
        for method_name in ("get_candle_data", "get_historical_data", "historical"):
            fn = getattr(self._client, method_name, None)
            if fn:
                resp = fn(symbol, interval=interval, period=period)
                return self._map_to_ohlcv(resp)
        raise NotImplementedError("Implement Angel One historical OHLCV retrieval using SDK")

    def _map_sdk_quote(self, symbol: str, data) -> Quote:
        try:
            if isinstance(data, dict):
                ltp = float(data.get("ltp") or data.get("lastPrice") or 0)
                volume = int(data.get("volume") or data.get("totalTradedVolume") or 0)
                ltq = int(data.get("ltq") or data.get("lastQuantity") or 0)
                bid_price = float(data.get("bidPrice") or data.get("bestBid") or 0)
                ask_price = float(data.get("askPrice") or data.get("bestAsk") or 0)
                bid_qty = int(data.get("bidQty") or data.get("bestBidQty") or 0)
                ask_qty = int(data.get("askQty") or data.get("bestAskQty") or 0)
                return Quote(symbol=symbol, ltp=ltp, volume=volume, ltq=ltq,
                             bid_price=bid_price, bid_qty=bid_qty, ask_price=ask_price, ask_qty=ask_qty)
        except Exception:
            pass
        return Quote(symbol=symbol, ltp=0.0)

    def _map_market_depth(self, symbol: str, resp) -> MarketDepth:
        bids = []
        asks = []
        try:
            b = resp.get("bids") or resp.get("buy") or resp.get("bid") or []
            a = resp.get("asks") or resp.get("sell") or resp.get("ask") or []
            for item in (b or [])[:5]:
                if isinstance(item, dict):
                    price = float(item.get("price") or item.get("p") or 0)
                    qty = int(item.get("quantity") or item.get("q") or 0)
                else:
                    price = float(item[0])
                    qty = int(item[1])
                bids.append(DepthLevel(price=price, quantity=qty))
            for item in (a or [])[:5]:
                if isinstance(item, dict):
                    price = float(item.get("price") or item.get("p") or 0)
                    qty = int(item.get("quantity") or item.get("q") or 0)
                else:
                    price = float(item[0])
                    qty = int(item[1])
                asks.append(DepthLevel(price=price, quantity=qty))
        except Exception:
            pass
        md = MarketDepth(symbol=symbol, bids=bids, asks=asks,
                         total_bid_qty=sum(d.quantity for d in bids),
                         total_ask_qty=sum(d.quantity for d in asks))
        return md

    def _map_to_ohlcv(self, resp) -> Optional[pd.DataFrame]:
        try:
            records = None
            if isinstance(resp, dict):
                records = resp.get("candles") or resp.get("data") or resp.get("history")
            elif isinstance(resp, list):
                records = resp
            if records is None:
                return None
            df = pd.DataFrame(records)
            rename_map = {}
            for col in df.columns:
                if col.lower() in ("open", "o"):
                    rename_map[col] = "Open"
                if col.lower() in ("high", "h"):
                    rename_map[col] = "High"
                if col.lower() in ("low", "l"):
                    rename_map[col] = "Low"
                if col.lower() in ("close", "c"):
                    rename_map[col] = "Close"
                if col.lower() in ("volume", "v"):
                    rename_map[col] = "Volume"
            df = df.rename(columns=rename_map)
            for req in ("Open", "High", "Low", "Close", "Volume"):
                if req not in df.columns:
                    df[req] = 0
            df.index = pd.to_datetime(df[df.columns[0]]) if df.columns[0].lower() in ("time", "datetime", "date") else pd.RangeIndex(len(df))
            return df[["Open", "High", "Low", "Close", "Volume"]]
        except Exception:
            return None
