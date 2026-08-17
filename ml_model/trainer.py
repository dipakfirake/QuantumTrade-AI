# =============================================================================
# ML Model Trainer — Generates training data and trains XGBoost classifier
# =============================================================================
import os
import logging
import pickle
import numpy as np
import pandas as pd
from typing import List, Tuple

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score
import xgboost as xgb

from indicators.smma import calculate_smma, get_smma_pair
from indicators.crossover import CrossoverDetector, SignalType
from ml_model.feature_engineer import extract_features_historical, FEATURE_NAMES
import config

logger = logging.getLogger(__name__)


def generate_training_data(symbols: List[str],
                           provider=None) -> pd.DataFrame:
    """
    Generate labeled training data from historical OHLCV data.

    For each symbol:
    1. Download historical OHLCV (6mo, 1h candles)
    2. Compute SMMA(20) and SMMA(120)
    3. Detect all crossovers
    4. Label each crossover: 1=profitable, 0=unprofitable
    5. Extract features at each crossover
    """
    import yfinance as yf

    all_rows = []
    detector = CrossoverDetector()

    for i, symbol in enumerate(symbols):
        logger.info(f"Processing {symbol} ({i + 1}/{len(symbols)})...")
        try:
            ticker = yf.Ticker(f"{symbol}.NS")
            df = ticker.history(
                period=config.YFINANCE_HISTORY_PERIOD,
                interval=config.YFINANCE_HISTORY_INTERVAL,
            )
            if df is None or len(df) < config.SMMA_LONG + 10:
                continue

            df = df.rename(columns={
                "Open": "Open", "High": "High", "Low": "Low",
                "Close": "Close", "Volume": "Volume",
            })
            df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()

            if len(df) < config.SMMA_LONG + 10:
                continue

            # Calculate SMMA
            smma_short, smma_long = get_smma_pair(df)

            # Detect all historical crossovers
            crossovers = detector.detect_all_historical(
                symbol, smma_short, smma_long, df["Close"]
            )
            detector.reset()

            if len(crossovers) < 2:
                continue

            # Label each crossover with profitability
            for j in range(len(crossovers) - 1):
                cross = crossovers[j]
                next_cross = crossovers[j + 1]

                entry_price = cross.ltp
                exit_price = next_cross.ltp

                if cross.signal_type == SignalType.BUY:
                    pnl = exit_price - entry_price
                else:
                    pnl = entry_price - exit_price

                label = 1 if pnl > 0 else 0

                # Extract features at the crossover point
                features = extract_features_historical(
                    df, cross.bar_index, smma_short, smma_long
                )

                row = {
                    "symbol": symbol,
                    "signal_type": cross.signal_type.value,
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "pnl": pnl,
                    "label": label,
                    "timestamp": cross.timestamp,
                }
                row.update(features)
                all_rows.append(row)

        except Exception as e:
            logger.warning(f"Failed for {symbol}: {e}")
            continue

    df_training = pd.DataFrame(all_rows)
    logger.info(f"Generated {len(df_training)} training samples from {len(symbols)} symbols")

    # Save training data
    os.makedirs(os.path.dirname(config.TRAINING_DATA_PATH), exist_ok=True)
    df_training.to_csv(config.TRAINING_DATA_PATH, index=False)
    logger.info(f"Training data saved to {config.TRAINING_DATA_PATH}")

    return df_training


def train_model(df_training: pd.DataFrame = None) -> dict:
    """
    Train the XGBoost classifier on crossover data.

    Returns:
        Dictionary with model metrics and paths.
    """
    if df_training is None:
        if not os.path.exists(config.TRAINING_DATA_PATH):
            raise FileNotFoundError(
                f"Training data not found at {config.TRAINING_DATA_PATH}. "
                "Run generate_training_data() first."
            )
        df_training = pd.read_csv(config.TRAINING_DATA_PATH)

    logger.info(f"Training on {len(df_training)} samples")

    # Prepare features and labels
    available_features = [f for f in FEATURE_NAMES if f in df_training.columns]
    X = df_training[available_features].fillna(0).replace([np.inf, -np.inf], 0)
    y = df_training["label"].values

    # Check class balance
    pos_count = y.sum()
    neg_count = len(y) - pos_count
    logger.info(f"Class balance: {pos_count} profitable, {neg_count} unprofitable")

    # Time-based split (no future leakage)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Train XGBoost
    scale_pos_weight = neg_count / pos_count if pos_count > 0 else 1.0
    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        eval_metric="logloss",
        use_label_encoder=False,
        random_state=42,
    )

    model.fit(
        X_train_scaled, y_train,
        eval_set=[(X_test_scaled, y_test)],
        verbose=False,
    )

    # Evaluate
    y_pred = model.predict(X_test_scaled)
    y_prob = model.predict_proba(X_test_scaled)[:, 1]

    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, output_dict=True)

    logger.info(f"Test Accuracy: {accuracy:.4f}")
    logger.info(f"\n{classification_report(y_test, y_pred)}")

    # Feature importance
    importance = dict(zip(available_features, model.feature_importances_))
    sorted_importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
    logger.info(f"Top features: {list(sorted_importance.items())[:5]}")

    # Save model and scaler
    os.makedirs(os.path.dirname(config.ML_MODEL_PATH), exist_ok=True)
    with open(config.ML_MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    with open(config.ML_SCALER_PATH, "wb") as f:
        pickle.dump(scaler, f)

    # Save feature names used
    feature_path = config.ML_MODEL_PATH.replace("model.pkl", "features.pkl")
    with open(feature_path, "wb") as f:
        pickle.dump(available_features, f)

    logger.info(f"Model saved to {config.ML_MODEL_PATH}")

    return {
        "accuracy": accuracy,
        "report": report,
        "feature_importance": sorted_importance,
        "train_size": len(X_train),
        "test_size": len(X_test),
        "model_path": config.ML_MODEL_PATH,
    }


# =============================================================================
# Training symbols — liquid NSE stocks for diverse training data
# =============================================================================
TRAINING_SYMBOLS = [
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN",
    "BHARTIARTL", "ITC", "KOTAKBANK", "LT", "AXISBANK", "WIPRO",
    "HCLTECH", "MARUTI", "TITAN", "SUNPHARMA", "BAJFINANCE",
    "ASIANPAINT", "ULTRACEMCO", "TATAMOTORS", "POWERGRID", "NTPC",
    "ONGC", "COALINDIA", "TATASTEEL", "JSWSTEEL", "HINDALCO",
    "CIPLA", "DRREDDY", "EICHERMOT", "HEROMOTOCO", "M&M", "TECHM",
    "INDUSINDBK", "BPCL", "DIVISLAB", "BRITANNIA", "TATACONSUM",
    "HINDUNILVR", "VEDL", "BANKBARODA", "PNB", "IDFCFIRSTB",
    "FEDERALBNK", "IRCTC", "ZOMATO", "TATAELXSI", "PERSISTENT",
    "MPHASIS", "COFORGE", "LAURUSLABS", "AUROPHARMA", "BIOCON",
    "LUPIN", "CANBK", "UNIONBANK", "SAIL", "NMDC", "GAIL", "IGL",
    "PETRONET", "RECLTD", "PFC", "NHPC", "IRFC", "TATAPOWER",
    "SUZLON", "BEL", "HAL", "BHEL", "VOLTAS", "HAVELLS",
    "CROMPTON", "BATAINDIA", "GODREJCP", "MARICO", "DABUR",
    "COLPAL", "PIDILITIND", "BERGEPAINT", "INDIGO", "CONCOR",
    "DLF", "OBEROIRLTY", "GODREJPROP", "PRESTIGE", "PHOENIXLTD",
    "ESCORTS", "ASHOKLEY", "TVSMOTOR", "BALKRISIND", "MRF",
    "APOLLOTYRE", "CEATLTD", "MOTHERSON", "BOSCHLTD", "EXIDEIND",
    "AMBUJACEM", "SHREECEM", "ACC", "RAMCOCEM", "JKCEMENT",
]
