"""
Retrain ML model using Fyers historical data — with class balancing
"""
import sys, os, logging
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

from ml_model.trainer import generate_training_data, train_model, TRAINING_SYMBOLS

# Train on ALL 100 liquid NSE stocks for maximum data diversity
num_symbols = len(TRAINING_SYMBOLS)
print(f"Generating training data from Fyers API ({num_symbols} stocks, 6mo history)...")
df_train = generate_training_data(TRAINING_SYMBOLS)

pos_count = (df_train["label"] == 1).sum() if "label" in df_train.columns else 0
neg_count = (df_train["label"] == 0).sum() if "label" in df_train.columns else 0
print(f"Training samples: {len(df_train)} (Profitable: {pos_count}, Unprofitable: {neg_count})")

if len(df_train) > 10:
    print("Training XGBoost model...")
    results = train_model(df_train)
    acc = results["accuracy"]
    train_sz = results["train_size"]
    test_sz = results["test_size"]
    print(f"Accuracy: {acc:.4f}")
    print(f"Train size: {train_sz}, Test size: {test_sz}")
    top5 = list(results["feature_importance"].items())[:5]
    for feat, imp in top5:
        print(f"  {feat}: {imp:.4f}")
    print("Model saved successfully!")
    
    # Verify predictions
    print("\n--- Verification ---")
    from ml_model.predictor import CrossoverPredictor
    predictor = CrossoverPredictor()
    print(f"Model reloaded: {predictor.is_loaded}")
    
    scenarios = [
        ("Strong BUY (institutional surge)", "BUY", {
            "ltq_ratio_2m_5m": 3.0, "ltq_ratio_5m_20m": 2.0,
            "etq_5m": 2000000, "etq_20m": 4000000, "etq_60m": 8000000,
            "etq_acceleration": 2.5, "bid_ask_imbalance": 0.5,
            "spread_pct": 0.03, "smma_gap_pct": 1.2,
            "price_vs_avg20m": 1.03, "price_vs_avg60m": 1.05,
            "volume_surge": 3.0, "rsi_14": 55, "atr_pct": 0.015,
        }),
        ("Weak SELL (no conviction)", "SELL", {
            "ltq_ratio_2m_5m": 0.5, "ltq_ratio_5m_20m": 0.6,
            "etq_5m": 50000, "etq_20m": 100000, "etq_60m": 200000,
            "etq_acceleration": 0.5, "bid_ask_imbalance": -0.1,
            "spread_pct": 0.3, "smma_gap_pct": 0.05,
            "price_vs_avg20m": 0.98, "price_vs_avg60m": 0.97,
            "volume_surge": 0.4, "rsi_14": 72, "atr_pct": 0.04,
        }),
        ("Neutral / average", "BUY", {
            "ltq_ratio_2m_5m": 1.2, "ltq_ratio_5m_20m": 1.1,
            "etq_5m": 500000, "etq_20m": 1000000, "etq_60m": 2000000,
            "etq_acceleration": 1.2, "bid_ask_imbalance": 0.1,
            "spread_pct": 0.05, "smma_gap_pct": 0.4,
            "price_vs_avg20m": 1.005, "price_vs_avg60m": 1.01,
            "volume_surge": 1.3, "rsi_14": 52, "atr_pct": 0.012,
        }),
        ("Strong SELL (bearish breakdown)", "SELL", {
            "ltq_ratio_2m_5m": 2.5, "ltq_ratio_5m_20m": 1.9,
            "etq_5m": 1800000, "etq_20m": 3500000, "etq_60m": 7000000,
            "etq_acceleration": 2.2, "bid_ask_imbalance": -0.4,
            "spread_pct": 0.04, "smma_gap_pct": -0.8,
            "price_vs_avg20m": 0.97, "price_vs_avg60m": 0.95,
            "volume_surge": 2.8, "rsi_14": 35, "atr_pct": 0.02,
        }),
    ]
    for name, sig_type, feats in scenarios:
        pred, conf, reason = predictor.predict(feats, sig_type)
        print(f"  [{name}] => {pred} (Confidence: {conf:.1%})")
else:
    print(f"ERROR: Only {len(df_train)} samples - insufficient for training")
