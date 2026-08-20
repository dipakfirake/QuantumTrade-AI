"""
Fyers Data Provider (scaffold)

This module provides a scaffold for integrating the Fyers API to fetch true
tick-level LTQ/ETQ and 5-level market depth. It intentionally does NOT contain
API keys. Fill in the methods below using the official Fyers Python SDK when
you have account credentials.

Usage:
 - Place API keys in an environment file or `config.py` (do NOT commit keys).
 - Set `config.USE_BROKER_ETQ = True` and `config.ETQ_MODE = "broker"`.
 - Then instantiate `FyersProvider()` and call the DataProvider methods.
"""
from typing import List, Optional
import pandas as pd
from data_provider.base import DataProvider, Quote, MarketDepth, DepthLevel


class FyersProvider(DataProvider):
    """Fyers integration wrapper.

    This wrapper attempts to use the `fyers_api` SDK if installed. If the
    SDK is not available, methods will raise NotImplementedError with
    instructions for installing the SDK and configuring environment variables.

    Environment variables supported:
    - FYERS_API_KEY
    - FYERS_ACCESS_TOKEN
    """

    def __init__(self, api_key: Optional[str] = None, access_token: Optional[str] = None):
        from utils.secrets import get_env

        self.api_key = api_key or get_env("FYERS_API_KEY")
        self.access_token = access_token or get_env("FYERS_ACCESS_TOKEN")
        self._client = None
        try:
            # Try to import SDK
            from fyers_api import fyersModel
            if not self.api_key or not self.access_token:
                raise EnvironmentError("FYERS_API_KEY or FYERS_ACCESS_TOKEN not set in env")
            config = {"client_id": self.api_key, "secret_key": None, "response_type": "json", "grant_type": "authorization_code"}
            self._client = fyersModel.FyersModel(client_id=self.api_key, token=self.access_token)
        except Exception:
            self._client = None

    def _ensure_sdk(self):
        if self._client is None:
            raise NotImplementedError(
                "Fyers SDK not initialized. Install `fyers_api` and set FYERS_API_KEY and FYERS_ACCESS_TOKEN environment variables."
            )

    def get_all_nse_symbols(self) -> List[str]:
        self._ensure_sdk()
        # Fyers does not provide a simple symbol list endpoint; recommend using NSE CSV
        raise NotImplementedError("Use NSEProvider.get_all_nse_symbols() to fetch symbol list")

    def get_quote(self, symbol: str) -> Optional[Quote]:
        self._ensure_sdk()
        # Attempt common SDK methods and map to Quote
        # Common SDK surfaces may expose `quotes`, `market_quotes`, or `get_quotes`
        for method_name in ("market_quotes", "quotes", "get_quotes", "quotes_data"):
            fn = getattr(self._client, method_name, None)
            if fn:
                resp = fn(symbol)
                return self._map_sdk_quote(symbol, resp)
        # Some SDKs expose a `get_ltp`-style helper
        for method_name in ("get_ltp", "ltp", "getLTP"):
            fn = getattr(self._client, method_name, None)
            if fn:
                resp = fn(symbol)
                return self._map_sdk_quote(symbol, resp)
        raise NotImplementedError("Implement Fyers single quote retrieval using fyersModel.market_quotes() or equivalent SDK method")

    def get_quotes_batch(self, symbols: List[str]) -> List[Quote]:
        self._ensure_sdk()
        # Many SDKs accept comma-separated symbols or list payloads
        # Try a few common method names
        for method_name in ("market_quotes", "quotes", "get_quotes"):
            fn = getattr(self._client, method_name, None)
            if fn:
                resp = fn(symbols)
                quotes = []
                # resp may be dict of symbol->data or list
                if isinstance(resp, dict):
                    for sym, data in resp.items():
                        quotes.append(self._map_sdk_quote(sym, data))
                elif isinstance(resp, list):
                    for item in resp:
                        # item may contain symbol key
                        sym = item.get("symbol") if isinstance(item, dict) else None
                        quotes.append(self._map_sdk_quote(sym or "", item))
                return quotes
        raise NotImplementedError("Implement Fyers batch quote retrieval using SDK market endpoints")

    def get_market_depth(self, symbol: str) -> Optional[MarketDepth]:
        self._ensure_sdk()
        # Fyers may provide market depth via a dedicated endpoint. Try common method names.
        for method_name in ("market_depth", "get_market_depth", "depth", "order_book"):
            fn = getattr(self._client, method_name, None)
            if fn:
                resp = fn(symbol)
                return self._map_market_depth(symbol, resp)
        raise NotImplementedError("Implement Fyers market depth retrieval (if supported) via your account's market data endpoints")

    def get_intraday_ohlcv(self, symbol: str, interval: str = "1m",
                           period: str = "5d") -> Optional[pd.DataFrame]:
        self._ensure_sdk()
        # Try SDK historical methods: `historical`, `get_historical`, `history`
        for method_name in ("historical", "get_historical", "history"):
            fn = getattr(self._client, method_name, None)
            if fn:
                resp = fn(symbol, interval=interval, period=period)
                return self._map_to_ohlcv(resp)
        raise NotImplementedError("Implement Fyers intraday OHLCV retrieval using historical data endpoints")

    def get_historical_ohlcv(self, symbol: str, interval: str = "1h",
                             period: str = "6mo") -> Optional[pd.DataFrame]:
        self._ensure_sdk()
        for method_name in ("historical", "get_historical", "history"):
            fn = getattr(self._client, method_name, None)
            if fn:
                resp = fn(symbol, interval=interval, period=period)
                return self._map_to_ohlcv(resp)
        raise NotImplementedError("Implement Fyers historical OHLCV retrieval using fyers historical API")

    def _map_sdk_quote(self, symbol: str, data) -> Quote:
        # Map common SDK response shapes to Quote
        try:
            if isinstance(data, dict):
                ltp = float(data.get("ltp") or data.get("lastPrice") or data.get("last_price") or 0)
                volume = int(data.get("volume") or data.get("totalTradedVolume") or 0)
                ltq = int(data.get("ltq") or data.get("lastQuantity") or data.get("last_qty") or 0)
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
        # Expect resp to contain bids/asks lists
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
            # Fallback: empty depth
            pass
        # Build MarketDepth conservatively
        md = MarketDepth(symbol=symbol, bids=bids, asks=asks,
                         total_bid_qty=sum(d.quantity for d in bids),
                         total_ask_qty=sum(d.quantity for d in asks))
        return md

    def _map_to_ohlcv(self, resp) -> Optional[pd.DataFrame]:
        # Expect resp to be a list of records or dict with 'candles'
        import pandas as pd
        try:
            records = None
            if isinstance(resp, dict):
                records = resp.get("candles") or resp.get("data") or resp.get("history")
            elif isinstance(resp, list):
                records = resp
            if records is None:
                return None
            df = pd.DataFrame(records)
            # Normalize common field names
            rename_map = {}
            for col in df.columns:
                if col.lower() in ("open", "o"):
                    rename_map[col] = "Open"
                if col.lower() in ("high", "h"):
                    rename_map[col] = "High"
                if col.lower() in ("low", "l"):
                    rename_map[col] = "Low"
                if col.lower() in ("close", "c", "close_price"):
                    rename_map[col] = "Close"
                if col.lower() in ("volume", "v"):
                    rename_map[col] = "Volume"
            df = df.rename(columns=rename_map)
            # Ensure required columns
            for req in ("Open", "High", "Low", "Close", "Volume"):
                if req not in df.columns:
                    df[req] = 0
            df.index = pd.to_datetime(df[df.columns[0]]) if df.columns[0].lower() in ("time", "datetime", "date") else pd.RangeIndex(len(df))
            return df[["Open", "High", "Low", "Close", "Volume"]]
        except Exception:
            return None
