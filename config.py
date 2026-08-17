# =============================================================================
# SSG Infotech — AI/ML Stock Market Screening & Analysis System
# Configuration Constants
# =============================================================================

# --- Screening Thresholds ---
PRICE_MIN = 30          # Minimum LTP (₹)
PRICE_MAX = 500         # Maximum LTP (₹)
BID_QTY_THRESHOLD = 1_000_000   # Min Bid Qty (10 Lakhs)
ASK_QTY_THRESHOLD = 1_000_000   # Min Ask Qty (10 Lakhs)

# --- SMMA Parameters ---
SMMA_SHORT = 20         # Fast SMMA period
SMMA_LONG = 120         # Slow SMMA period

# --- Dashboard ---
REFRESH_INTERVAL_MS = 60000    # Auto-refresh interval (milliseconds)

# --- Time Windows (minutes) ---
ETQ_WINDOWS = [5, 20, 60]          # ETQ aggregation windows
AVG_LTP_WINDOWS = [20, 60]         # Average LTP windows
LTQ_WINDOWS = [2, 5, 20]           # LTQ averaging windows for ML features

# --- Data Source ---
YFINANCE_INTERVAL = "1m"           # Intraday candle interval
YFINANCE_PERIOD = "5d"             # Lookback period for intraday data
YFINANCE_HISTORY_PERIOD = "6mo"    # Historical period for ML training
YFINANCE_HISTORY_INTERVAL = "1h"   # Historical candle interval for ML training

NSE_REQUEST_DELAY = 1.0            # Seconds between NSE API calls (rate limiting)
NSE_BATCH_SIZE = 50                # Number of symbols per scan batch

# --- ML Model ---
ML_MODEL_PATH = "ml_model/model.pkl"
ML_SCALER_PATH = "ml_model/scaler.pkl"
ML_CONFIDENCE_THRESHOLD = 0.55     # Minimum confidence to ACCEPT a trade
TRAINING_DATA_PATH = "data/historical_crossovers.csv"

# --- Trade Log ---
TRADE_HISTORY_PATH = "data/trade_history.csv"
NSE_SYMBOLS_CACHE_PATH = "data/nse_symbols.csv"

# --- RSI ---
RSI_PERIOD = 14

# --- ATR ---
ATR_PERIOD = 14
