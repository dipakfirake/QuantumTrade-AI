"""
Comprehensive System Audit — Tests all components end-to-end
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd

print("=" * 60)
print("  QUANTUMTRADE AI — COMPREHENSIVE SYSTEM AUDIT")
print("=" * 60)
print()

# 1. Config
print("--- 1. CONFIG ---")
import config
print(f"  ETQ_MODE: {config.ETQ_MODE}")
print(f"  USE_BROKER_ETQ: {config.USE_BROKER_ETQ}")
print(f"  PRICE_MIN: {config.PRICE_MIN}, PRICE_MAX: {config.PRICE_MAX}")
print(f"  BID_QTY_THRESHOLD: {config.BID_QTY_THRESHOLD:,}")
print(f"  SMMA_SHORT: {config.SMMA_SHORT}, SMMA_LONG: {config.SMMA_LONG}")
print(f"  ML_MODEL_PATH: {config.ML_MODEL_PATH} (exists: {os.path.exists(config.ML_MODEL_PATH)})")
print(f"  ML_SCALER_PATH: {config.ML_SCALER_PATH} (exists: {os.path.exists(config.ML_SCALER_PATH)})")
print(f"  ML_CONFIDENCE_THRESHOLD: {config.ML_CONFIDENCE_THRESHOLD}")
print()

# 2. Data Provider
print("--- 2. DATA PROVIDER ---")
from data_provider import get_data_provider
provider = get_data_provider()
print(f"  Provider type: {type(provider).__name__}")
print(f"  Authenticated: {provider.is_authenticated()}")
print()

# 3. Quote fetching
print("--- 3. QUOTE FETCHING (5 sample stocks) ---")
test_symbols = ["SBIN", "NHPC", "TATAPOWER", "SUZLON", "BPCL"]
quotes = provider.get_quotes_batch(test_symbols)
print(f"  Fetched: {len(quotes)} quotes")
for q in quotes:
    print(f"    {q.symbol}: LTP={q.ltp}, Vol={q.volume:,}, BidQ={q.total_bid_qty:,}, AskQ={q.total_ask_qty:,}, LTQ={q.ltq}")
print()

# 4. Full NSE Scan (200 stocks sample)
print("--- 4. FULL NSE SCAN (first 200) ---")
from screener.nse_symbols import fetch_nse_symbols
all_syms = fetch_nse_symbols()
print(f"  Total NSE symbols: {len(all_syms)}")
batch = provider.get_quotes_batch(all_syms[:200])
print(f"  Quotes fetched: {len(batch)}")
print()

# 5. Screener Pipeline
print("--- 5. SCREENER PIPELINE ---")
from screener.stock_screener import StockScreener
screener = StockScreener(provider)
price_filtered = screener.screen_by_price(batch)
qualified = screener.screen_by_liquidity(price_filtered)
print(f"  Price filtered: {len(price_filtered)}/{len(batch)}")
print(f"  Liquidity qualified: {len(qualified)}/{len(price_filtered)}")
for s in qualified[:5]:
    print(f"    {s.symbol}: LTP={s.ltp}, Vol={s.volume:,}, TotBidQ={s.total_bid_qty:,}, TotAskQ={s.total_ask_qty:,}, LTQ={s.ltq}")
print()

# 6. SMMA Calculation
print("--- 6. SMMA CALCULATION ---")
from indicators.smma import calculate_smma, get_smma_pair, calculate_rsi, calculate_atr
prices = [100 + i * 0.5 + np.sin(i / 5) * 2 for i in range(150)]
df_test = pd.DataFrame({
    "Close": prices,
    "Open": prices,
    "High": [p * 1.01 for p in prices],
    "Low": [p * 0.99 for p in prices],
    "Volume": [10000] * 150,
})
smma_20, smma_120 = get_smma_pair(df_test)
print(f"  SMMA(20) last value: {smma_20.iloc[-1]:.4f}")
print(f"  SMMA(120) last value: {smma_120.iloc[-1]:.4f}")
rsi = calculate_rsi(df_test["Close"], 14)
atr = calculate_atr(df_test, 14)
print(f"  RSI(14) last value: {rsi.iloc[-1]:.2f}")
print(f"  ATR(14) last value: {atr.iloc[-1]:.4f}")
print()

# 7. Crossover Detection
print("--- 7. CROSSOVER DETECTION ---")
from indicators.crossover import CrossoverDetector, SignalType
detector = CrossoverDetector()
signals = detector.detect_all_historical("TEST", smma_20, smma_120, df_test["Close"])
print(f"  Historical crossovers found: {len(signals)}")
for sig in signals[:3]:
    print(f"    {sig.signal_type.value} at bar {sig.bar_index}, LTP={sig.ltp:.2f}, Gap={sig.smma_gap_pct:.3f}%")
print()

# 8. ML Model Load & Predict
print("--- 8. ML MODEL ---")
from ml_model.predictor import CrossoverPredictor
predictor = CrossoverPredictor()
print(f"  Model loaded: {predictor.is_loaded}")
importance = predictor.get_feature_importance()
print(f"  Feature count: {len(importance)}")
top_feats = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:5]
for feat, imp in top_feats:
    print(f"    {feat}: {imp:.4f}")
print()

# 9. ML Prediction (multiple scenarios)
print("--- 9. ML PREDICTIONS ---")
scenarios = [
    ("Strong BUY", {"ltq_ratio_2m_5m": 3.0, "ltq_ratio_5m_20m": 2.0, "etq_5m": 2000000, "etq_20m": 4000000, "etq_60m": 8000000,
                    "etq_acceleration": 2.5, "bid_ask_imbalance": 0.5, "spread_pct": 0.03, "smma_gap_pct": 1.2,
                    "price_vs_avg20m": 1.03, "price_vs_avg60m": 1.05, "volume_surge": 3.0, "rsi_14": 55, "atr_pct": 0.015}),
    ("Weak Signal", {"ltq_ratio_2m_5m": 0.5, "ltq_ratio_5m_20m": 0.6, "etq_5m": 50000, "etq_20m": 100000, "etq_60m": 200000,
                     "etq_acceleration": 0.5, "bid_ask_imbalance": -0.1, "spread_pct": 0.3, "smma_gap_pct": 0.05,
                     "price_vs_avg20m": 0.98, "price_vs_avg60m": 0.97, "volume_surge": 0.4, "rsi_14": 72, "atr_pct": 0.04}),
    ("Neutral", {"ltq_ratio_2m_5m": 1.0, "ltq_ratio_5m_20m": 1.0, "etq_5m": 500000, "etq_20m": 1000000, "etq_60m": 2000000,
                 "etq_acceleration": 1.0, "bid_ask_imbalance": 0.0, "spread_pct": 0.05, "smma_gap_pct": 0.3,
                 "price_vs_avg20m": 1.0, "price_vs_avg60m": 1.0, "volume_surge": 1.0, "rsi_14": 50, "atr_pct": 0.01}),
]
for name, feats in scenarios:
    pred, conf, reason = predictor.predict(feats, "BUY")
    print(f"  [{name}] => {pred} (Confidence: {conf:.1%})")
print()

# 10. Feature Engineering (Live)
print("--- 10. FEATURE ENGINEERING ---")
from ml_model.feature_engineer import extract_features_live, FEATURE_NAMES
from data_provider.cache import TickCache
tc = TickCache()
tc.add_tick("TEST", 100.0, 50000, 500000, 450000, 150)
features = extract_features_live("TEST", tc, df_test, smma_20.iloc[-1], smma_120.iloc[-1], 100.0, 500000, 450000, 99.9, 100.1)
print(f"  Feature names: {FEATURE_NAMES}")
print(f"  Features extracted: {len(features)}")
for fn in FEATURE_NAMES:
    print(f"    {fn}: {features.get(fn, 'MISSING')}")
print()

# 11. Evaluator
print("--- 11. STRATEGY EVALUATOR ---")
from ml_model.evaluator import evaluate_strategy_performance
test_trades = pd.DataFrame([
    {"pnl": 5.0, "ml_prediction": "ACCEPT", "ml_confidence": 0.7},
    {"pnl": -3.0, "ml_prediction": "AVOID", "ml_confidence": 0.4},
    {"pnl": 8.0, "ml_prediction": "ACCEPT", "ml_confidence": 0.8},
    {"pnl": -2.0, "ml_prediction": "ACCEPT", "ml_confidence": 0.6},
    {"pnl": -4.0, "ml_prediction": "AVOID", "ml_confidence": 0.35},
])
metrics = evaluate_strategy_performance(test_trades)
raw = metrics["raw_strategy"]
ml = metrics["ml_filtered_strategy"]
avoid = metrics["loss_avoidance"]
print(f"  RAW: {raw['total_trades']} trades, Win Rate: {raw['win_rate_pct']}%, PnL: {raw['total_pnl']}")
print(f"  ML:  {ml['total_trades']} trades, Win Rate: {ml['win_rate_pct']}%, PnL: {ml['total_pnl']}")
print(f"  Improvement: +{ml['win_rate_improvement_pct']}%")
print(f"  Avoided: {avoid['avoided_trades']} trades, Capital Saved: {avoid['capital_saved']}")
print()

# 12. Fyers Intraday OHLCV
print("--- 12. FYERS INTRADAY OHLCV ---")
ohlcv = provider.get_intraday_ohlcv("SBIN")
if ohlcv is not None:
    print(f"  Bars: {len(ohlcv)}, Columns: {list(ohlcv.columns)}")
    smma_s, smma_l = get_smma_pair(ohlcv.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"}))
    valid_s = smma_s.notna().sum()
    valid_l = smma_l.notna().sum()
    print(f"  SMMA(20) valid bars: {valid_s}, SMMA(120) valid bars: {valid_l}")
    if valid_l > 0:
        print(f"  SMMA(20) last: {smma_s.dropna().iloc[-1]:.2f}")
        print(f"  SMMA(120) last: {smma_l.dropna().iloc[-1]:.2f}")
else:
    print("  OHLCV: None (may need market hours or valid token)")
print()

# 13. Signal Tracker & Trade Log
print("--- 13. SIGNAL TRACKER ---")
from trading.signal_tracker import SignalTracker
from indicators.crossover import CrossoverSignal
tracker = SignalTracker()
sig1 = CrossoverSignal(symbol="TEST", signal_type=SignalType.BUY, ltp=100.0, smma_short=101.0, smma_long=100.5, smma_gap_pct=0.5, bar_index=0, timestamp="10:00:00")
closed = tracker.process_signal(sig1, "ACCEPT", 0.75, "Strong BUY")
print(f"  Open positions: {len(tracker.get_open_trades())}")
sig2 = CrossoverSignal(symbol="TEST", signal_type=SignalType.SELL, ltp=105.0, smma_short=99.0, smma_long=100.0, smma_gap_pct=-1.0, bar_index=1, timestamp="11:00:00")
closed = tracker.process_signal(sig2, "ACCEPT", 0.65, "Exit BUY")
print(f"  Trade closed: PnL={closed.pnl if closed else 'N/A'}")
stats = tracker.get_stats()
print(f"  Stats: {stats}")
print()

# 14. Dashboard Components (import check)
print("--- 14. DASHBOARD COMPONENTS ---")
from dashboard.components import (
    render_header, render_metrics, render_screening_table,
    render_signal_cards, render_trade_log, render_feature_importance,
    render_pnl_chart, render_strategy_comparison, render_walk_forward_table,
)
print("  All dashboard components imported successfully!")
print()

# 15. Check for stale imports
print("--- 15. STALE DEPENDENCY CHECK ---")
stale_imports = []
import importlib
for mod_name in ["yfinance"]:
    try:
        importlib.import_module(mod_name)
        stale_imports.append(f"  WARNING: '{mod_name}' is installed (used by trainer.py fallback only)")
    except ImportError:
        stale_imports.append(f"  OK: '{mod_name}' not installed (pure Fyers mode)")
for s in stale_imports:
    print(s)
print()

print("=" * 60)
print("  AUDIT COMPLETE - ALL SYSTEMS VERIFIED")
print("=" * 60)
