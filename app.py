# =============================================================================
# SSG Infotech — AI/ML Stock Market Screening & Analysis System
# Main Streamlit Application
# =============================================================================
import os
import sys
import logging
import asyncio
from datetime import datetime

# Suppress Windows asyncio 'Event loop is closed' warning
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import streamlit as st
import pandas as pd
import numpy as np

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from streamlit_autorefresh import st_autorefresh

import config
from dashboard.styles import inject_css
from dashboard.components import (
    render_header, render_metrics, render_screening_table,
    render_signal_cards, render_trade_log, render_feature_importance,
    render_pnl_chart,
)
from data_provider.nse_provider import NSEProvider
from data_provider.cache import TickCache
from screener.stock_screener import StockScreener
from screener.nse_symbols import fetch_nse_symbols
from indicators.smma import get_smma_pair
from indicators.crossover import CrossoverDetector, SignalType
from trading.signal_tracker import SignalTracker, Trade
from trading.trade_log import append_trade, init_trade_log
from ml_model.predictor import CrossoverPredictor
from ml_model.feature_engineer import extract_features_live

# =============================================================================
# Logging
# =============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# =============================================================================
# Streamlit Page Config
# =============================================================================
st.set_page_config(
    page_title="QuantumTrade AI — Algorithmic Market Screener",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject custom CSS
inject_css()


# =============================================================================
# Session State Initialization
# =============================================================================
def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        "provider": NSEProvider(),
        "tick_cache": TickCache(),
        "screener": None,
        "crossover_detector": CrossoverDetector(),
        "signal_tracker": SignalTracker(),
        "predictor": CrossoverPredictor(),
        "scan_count": 0,
        "qualified_stocks": [],
        "active_signals": [],
        "all_signals_history": [],
        "screening_df": pd.DataFrame(),
        "last_scan_time": "—",
        "total_scanned": 0,
        "is_initialized": False,
        "refresh_interval": config.REFRESH_INTERVAL_MS,
        "price_min": config.PRICE_MIN,
        "price_max": config.PRICE_MAX,
        "bid_threshold": config.BID_QTY_THRESHOLD,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

    if st.session_state.screener is None:
        st.session_state.screener = StockScreener(st.session_state.provider)

    # Load ML model
    if not st.session_state.predictor.is_loaded:
        st.session_state.predictor.load_model()

    init_trade_log()
    st.session_state.is_initialized = True


init_session_state()


# =============================================================================
# Auto-Refresh
# =============================================================================
st_autorefresh(
    interval=st.session_state.refresh_interval,
    key="market_data_refresh",
)


# =============================================================================
# Sidebar — Configuration
# =============================================================================
with st.sidebar:
    st.markdown("## ⚙️ Configuration")

    st.session_state.refresh_interval = st.slider(
        "Refresh Interval (sec)", 10, 120,
        st.session_state.refresh_interval // 1000,
    ) * 1000

    st.markdown("---")
    st.markdown("### 📏 Price Filter")
    st.session_state.price_min = st.number_input(
        "Min LTP (₹)", value=config.PRICE_MIN, step=5
    )
    st.session_state.price_max = st.number_input(
        "Max LTP (₹)", value=config.PRICE_MAX, step=50
    )
    st.markdown("##### 💧 Liquidity Threshold")
    threshold_lakh = st.number_input(
        "Min Bid/Ask Qty (Lakh)",
        min_value=0, max_value=1000, value=int(config.BID_QTY_THRESHOLD / 100000), step=1
    )
    config.BID_QTY_THRESHOLD = threshold_lakh * 100_000
    config.ASK_QTY_THRESHOLD = threshold_lakh * 100_000
    st.markdown("### 🧠 ML Model")
    if st.session_state.predictor.is_loaded:
        st.success("✅ Model loaded")
    else:
        st.warning("⚠️ Model not trained yet")
        if st.button("🔄 Train Model", key="train_btn"):
            with st.spinner("Training ML model... This may take 5-10 minutes."):
                try:
                    from ml_model.trainer import generate_training_data, train_model, TRAINING_SYMBOLS
                    df_train = generate_training_data(TRAINING_SYMBOLS[:30])
                    if len(df_train) > 10:
                        results = train_model(df_train)
                        st.session_state.predictor.load_model()
                        st.success(f"✅ Model trained! Accuracy: {results['accuracy']:.1%}")
                    else:
                        st.error("Insufficient training data generated.")
                except Exception as e:
                    st.error(f"Training failed: {e}")

    st.markdown("---")
    st.markdown("##### 📊 About")
    st.info("""
    **QuantumTrade AI**
    Institutional Market Screening & ML Analysis System.
    Real-time execution screening of NSE stocks with SMMA crossover prediction.
    """)


# =============================================================================
# Main Data Processing Pipeline
# =============================================================================
@st.cache_data(ttl=60)
def get_nse_symbols():
    """Fetch and cache NSE symbols (refreshes every 60 seconds in cache)."""
    return fetch_nse_symbols()


def run_screening_pipeline():
    """Execute the full screening and analysis pipeline."""
    provider = st.session_state.provider
    tick_cache = st.session_state.tick_cache
    screener = st.session_state.screener
    detector = st.session_state.crossover_detector
    tracker = st.session_state.signal_tracker
    predictor = st.session_state.predictor

    # Update config from sidebar
    config.PRICE_MIN = st.session_state.price_min
    config.PRICE_MAX = st.session_state.price_max
    config.BID_QTY_THRESHOLD = st.session_state.bid_threshold
    config.ASK_QTY_THRESHOLD = st.session_state.bid_threshold

    # Step 1: Load Symbols
    symbols = get_nse_symbols()
    
    if not symbols:
        st.error("Failed to fetch NSE symbols. Check internet connection.")
        return

    st.session_state.total_scanned = len(symbols)

    # Step 2: Batch download quotes for price filtering
    with st.spinner(f"🔍 Scanning {len(symbols)} NSE stocks..."):
        # Fetch real-time quotes via batch download
        quotes = provider.get_quotes_batch(symbols)

    # Step 3: Price filter
    price_filtered = screener.screen_by_price(quotes)

    # Step 4: Fetch market depth for price-filtered stocks & liquidity filter
    qualified = screener.screen_with_depth(
        [q.symbol for q in price_filtered], price_filtered
    )

    st.session_state.qualified_stocks = qualified
    st.session_state.scan_count += 1
    st.session_state.last_scan_time = datetime.now().strftime("%H:%M:%S")

    # Step 5: Process each qualified stock
    screening_rows = []
    active_signals = []

    # Pre-fetch intraday OHLCV for all qualified stocks concurrently
    ohlcv_dict = {}
    if qualified:
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            future_to_symbol = {
                executor.submit(provider.get_intraday_ohlcv, stock.symbol): stock.symbol 
                for stock in qualified
            }
            for future in concurrent.futures.as_completed(future_to_symbol):
                sym = future_to_symbol[future]
                try:
                    ohlcv_dict[sym] = future.result()
                except Exception:
                    ohlcv_dict[sym] = None

    for stock in qualified:
        symbol = stock.symbol

        # Update tick cache
        tick_cache.add_tick(
            symbol, stock.ltp, stock.volume,
            stock.total_bid_qty, stock.total_ask_qty, stock.ltq,
        )

        # Fetch intraday data for SMMA
        ohlcv = ohlcv_dict.get(symbol)

        smma_20_val, smma_120_val = 0.0, 0.0
        signal_type = "—"
        ml_prediction = ""
        ml_confidence = 0.0
        ml_reason = ""

        if ohlcv is not None and len(ohlcv) > config.SMMA_LONG:
            smma_short, smma_long = get_smma_pair(ohlcv)
            smma_20_val = smma_short.iloc[-1] if not pd.isna(smma_short.iloc[-1]) else 0.0
            smma_120_val = smma_long.iloc[-1] if not pd.isna(smma_long.iloc[-1]) else 0.0

            # Detect crossover
            crossover = detector.detect(symbol, smma_short, smma_long, stock.ltp)

            if crossover:
                signal_type = crossover.signal_type.value

                # Extract ML features
                features = extract_features_live(
                    symbol, tick_cache, ohlcv,
                    smma_20_val, smma_120_val, stock.ltp,
                    stock.total_bid_qty, stock.total_ask_qty,
                    stock.bid_price, stock.ask_price,
                )

                # ML prediction
                ml_prediction, ml_confidence, ml_reason = predictor.predict(
                    features, signal_type
                )

                # Track the trade
                closed_trade = tracker.process_signal(
                    crossover, ml_prediction, ml_confidence, ml_reason
                )

                if closed_trade:
                    append_trade(closed_trade)

                active_signals.append({
                    "symbol": symbol,
                    "signal_type": signal_type,
                    "ltp": stock.ltp,
                    "smma_short": smma_20_val,
                    "smma_long": smma_120_val,
                    "ml_prediction": ml_prediction,
                    "ml_confidence": ml_confidence,
                    "ml_reason": ml_reason,
                })
            else:
                # Check current SMMA relationship (no crossover)
                state = detector.get_current_state(symbol)
                if state == "above":
                    signal_type = "BULLISH"
                elif state == "below":
                    signal_type = "BEARISH"

        # ETQ & Average LTP from tick cache
        etq_5m = tick_cache.get_etq(symbol, 5)
        etq_20m = tick_cache.get_etq(symbol, 20)
        etq_60m = tick_cache.get_etq(symbol, 60)
        avg_ltp_20m = tick_cache.get_avg_ltp(symbol, 20) or stock.ltp
        avg_ltp_60m = tick_cache.get_avg_ltp(symbol, 60) or stock.ltp

        screening_rows.append({
            "Symbol": symbol,
            "LTP": stock.ltp,
            "SMMA_20": smma_20_val,
            "SMMA_120": smma_120_val,
            "Signal": signal_type,
            "Bid_Price": stock.bid_price,
            "Bid_Qty": stock.bid_qty,
            "Ask_Price": stock.ask_price,
            "Ask_Qty": stock.ask_qty,
            "Total_Bid_Qty": stock.total_bid_qty,
            "Total_Ask_Qty": stock.total_ask_qty,
            "ETQ_5m": etq_5m,
            "ETQ_20m": etq_20m,
            "ETQ_60m": etq_60m,
            "Avg_LTP_20m": avg_ltp_20m,
            "Avg_LTP_60m": avg_ltp_60m,
            "ML_Prediction": ml_prediction,
            "ML_Confidence": ml_confidence,
            "ML_Reason": ml_reason,
        })

    st.session_state.screening_df = pd.DataFrame(screening_rows)
    st.session_state.active_signals = active_signals
    if active_signals:
        st.session_state.all_signals_history.extend(active_signals)


# =============================================================================
# Run the pipeline
# =============================================================================
run_screening_pipeline()


# =============================================================================
# Render Dashboard
# =============================================================================

# Header
render_header(
    last_updated=st.session_state.last_scan_time,
    stocks_scanned=st.session_state.total_scanned,
    qualified=len(st.session_state.qualified_stocks),
    active_signals=len(st.session_state.active_signals),
)

# Trading Stats
stats = st.session_state.signal_tracker.get_stats()
render_metrics(stats)

# Main Content — Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Live Screening Dashboard",
    "🤖 AI/ML Signal Analysis",
    "📋 Trade Log",
    "🧠 Model Performance",
])

with tab1:
    st.markdown("""
    <div class="section-header">
        <h2>🔴 Live Stock Screening</h2>
        <span class="badge">Auto-Refresh</span>
    </div>
    """, unsafe_allow_html=True)
    render_screening_table(st.session_state.screening_df)

with tab2:
    st.markdown("""
    <div class="section-header">
        <h2>🤖 AI/ML Crossover Analysis</h2>
        <span class="badge">SMMA Crossover Prediction</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    The AI/ML model analyzes each SMMA crossover to determine whether the signal
    should be **accepted** or **avoided** based on:
    - **LTQ (Last Traded Quantity) patterns** — sudden surges indicate institutional activity
    - **Bid-Ask imbalance** — order book alignment with signal direction
    - **Volume confirmation** — trading conviction strength
    - **RSI & volatility context** — overbought/oversold + risk assessment
    """)

    # Show current active signals
    if st.session_state.active_signals:
        render_signal_cards(st.session_state.active_signals)
    else:
        st.info("🔍 No new crossover signals in this scan cycle. Monitoring...")

    # Show recent signal history
    if st.session_state.all_signals_history:
        st.markdown("### 📜 Recent Signal History")
        render_signal_cards(st.session_state.all_signals_history[-10:])

with tab3:
    st.markdown("""
    <div class="section-header">
        <h2>📋 Trade History & P&L</h2>
        <span class="badge">Entry → Exit Tracking</span>
    </div>
    """, unsafe_allow_html=True)

    trades = st.session_state.signal_tracker.get_trade_history()
    trade_dicts = [
        {
            "symbol": t.symbol,
            "signal_type": t.signal_type.value,
            "entry_ltp": t.entry_ltp,
            "entry_time": t.entry_time,
            "exit_ltp": t.exit_ltp or 0,
            "exit_time": t.exit_time or "",
            "pnl": t.pnl or 0,
            "ml_prediction": t.ml_prediction,
            "ml_confidence": t.ml_confidence,
        }
        for t in trades
    ]

    if trade_dicts:
        render_pnl_chart(trade_dicts)
        render_trade_log(trade_dicts)
    else:
        st.info("No completed trades yet. Trades are closed when an opposite crossover occurs.")

    # Show open positions
    open_trades = st.session_state.signal_tracker.get_open_trades()
    if open_trades:
        st.markdown("### 🔓 Open Positions")
        for sym, trade in open_trades.items():
            emoji = "🟢" if trade.signal_type == SignalType.BUY else "🔴"
            st.markdown(
                f"{emoji} **{sym}** — {trade.signal_type.value} @ ₹{trade.entry_ltp:.2f} "
                f"(Opened: {trade.entry_time})"
            )

with tab4:
    st.markdown("""
    <div class="section-header">
        <h2>🧠 ML Model Performance</h2>
        <span class="badge">XGBoost Classifier</span>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Feature Importance")
        importance = st.session_state.predictor.get_feature_importance()
        render_feature_importance(importance)

    with col2:
        st.markdown("### Model Info")
        if st.session_state.predictor.is_loaded:
            st.success("Model Status: **Loaded & Active**")
            st.markdown(f"""
            - **Algorithm**: XGBoost (Gradient Boosted Trees)
            - **Features**: {len(importance)} quantitative features
            - **Key Features**: LTQ ratios, ETQ acceleration, bid-ask imbalance
            - **Confidence Threshold**: {config.ML_CONFIDENCE_THRESHOLD:.0%}

            **Why XGBoost?**
            - Excellent for tabular financial data
            - Handles feature interactions naturally
            - Fast inference for real-time predictions
            - Built-in feature importance for explainability
            """)
        else:
            st.warning("Model not trained. Click 'Train Model' in the sidebar.")
            st.markdown("""
            **Using Rule-Based Fallback:**
            The system uses a rule-based prediction engine until the ML model is trained.
            Rules are based on:
            - LTQ surge patterns (2min vs 5min)
            - Volume confirmation
            - Bid-ask alignment with signal direction
            - RSI overbought/oversold conditions
            """)

    # SMMA Crossover Logic explanation
    st.markdown("---")
    st.markdown("### 📖 SMMA Crossover Logic")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **🟢 Buy Signal**
        - SMMA(20) crosses **above** SMMA(120)
        - Entry: Record LTP at crossover
        - Exit: When SMMA(20) crosses below SMMA(120)
        - P&L = Exit LTP − Entry LTP
        """)
    with col2:
        st.markdown("""
        **🔴 Sell Signal**
        - SMMA(20) crosses **below** SMMA(120)
        - Entry: Record LTP at crossover
        - Exit: When SMMA(20) crosses above SMMA(120)
        - P&L = Entry LTP − Exit LTP
        """)
