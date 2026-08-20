"""Debug scaler transformations to understand why live features get low probabilities."""
import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import pandas as pd
import config
from ml_model.feature_engineer import FEATURE_NAMES

# Load model artifacts
with open(config.ML_MODEL_PATH, "rb") as f:
    model = pickle.load(f)
with open(config.ML_SCALER_PATH, "rb") as f:
    scaler = pickle.load(f)

# Load training data
df = pd.read_csv(config.TRAINING_DATA_PATH)
avail = [f for f in FEATURE_NAMES if f in df.columns]
X = df[avail].fillna(0).replace([np.inf, -np.inf], 0)
y = df["label"].values

# Check model performance on training data
X_s = scaler.transform(X)
probs = model.predict_proba(X_s)[:, 1]

print("=== MODEL ON TRAINING DATA ===")
print(f"Accept rate at 0.29: {(probs >= 0.29).mean():.1%}")
print(f"Positives accepted: {(probs[y == 1] >= 0.29).sum()}/{(y == 1).sum()}")
print(f"Negatives rejected: {(probs[y == 0] < 0.29).sum()}/{(y == 0).sum()}")
print()

# Print scaler parameters
print("=== SCALER PARAMETERS (mean, scale) ===")
for i, feat in enumerate(avail):
    print(f"  {feat}: mean={scaler.mean_[i]:.4f}, std={scaler.scale_[i]:.4f}")
print()

# Test a "Strong BUY" scenario with training-aligned features
strong_buy = {
    "ltq_ratio_2m_5m": 1.8, "ltq_ratio_5m_20m": 1.6,
    "etq_5m": 8000000, "etq_20m": 20000000, "etq_60m": 50000000,
    "etq_acceleration": 1.8, "bid_ask_imbalance": 0.5,
    "spread_pct": 0.05, "smma_gap_pct": 0.12,
    "price_vs_avg20m": 1.02, "price_vs_avg60m": 1.04,
    "volume_surge": 2.5, "rsi_14": 55, "atr_pct": 0.8,
}
X_test = pd.DataFrame([[strong_buy.get(f, 0) for f in avail]], columns=avail)
X_test_s = scaler.transform(X_test)
prob = model.predict_proba(X_test_s)[0][1]

print("=== STRONG BUY: Scaled Feature Values ===")
for i, feat in enumerate(avail):
    raw = strong_buy.get(feat, 0)
    scaled = X_test_s[0][i]
    print(f"  {feat}: raw={raw:.4f} -> scaled={scaled:.4f}")
print(f"  P(profitable) = {prob:.4f}")
print()

# Now check: what does a TYPICAL positive (profitable) sample look like?
pos_indices = np.where(y == 1)[0]
if len(pos_indices) > 0:
    print("=== TYPICAL POSITIVE (PROFITABLE) SAMPLE ===")
    sample_idx = pos_indices[0]
    sample = X.iloc[sample_idx]
    for feat in avail:
        print(f"  {feat}: {sample[feat]:.4f}")
    sample_prob = probs[sample_idx]
    print(f"  P(profitable) = {sample_prob:.4f}")
    print()
    
    # Average of all positive samples
    print("=== AVERAGE POSITIVE SAMPLE ===")
    pos_mean = X.iloc[pos_indices].mean()
    for feat in avail:
        print(f"  {feat}: {pos_mean[feat]:.4f}")
    X_pos_mean = pd.DataFrame([pos_mean[avail].values], columns=avail)
    prob_avg = model.predict_proba(scaler.transform(X_pos_mean))[0][1]
    print(f"  P(profitable) = {prob_avg:.4f}")
    print()

# Check: what features distinguish positive from negative?
print("=== FEATURE DIFFERENCES (Positive mean - Negative mean) ===")
pos_mean = X.iloc[np.where(y == 1)[0]].mean()
neg_mean = X.iloc[np.where(y == 0)[0]].mean()
for feat in avail:
    diff = pos_mean[feat] - neg_mean[feat]
    pct = (diff / neg_mean[feat] * 100) if neg_mean[feat] != 0 else 0
    direction = "+" if diff > 0 else ""
    print(f"  {feat}: pos={pos_mean[feat]:.4f} vs neg={neg_mean[feat]:.4f} ({direction}{pct:.1f}%)")
