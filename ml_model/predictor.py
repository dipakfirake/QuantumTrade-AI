# =============================================================================
# ML Predictor — Live inference with SHAP-based explanations
# =============================================================================
import os
import logging
import pickle
import numpy as np
from typing import Tuple, Optional, Dict

import config
from ml_model.feature_engineer import FEATURE_NAMES

logger = logging.getLogger(__name__)

# Human-readable explanations for each feature
FEATURE_EXPLANATIONS = {
    "ltq_ratio_2m_5m": {
        "high": "Strong LTQ surge in last 2 min vs 5 min — indicates sudden institutional activity",
        "low": "Declining LTQ activity — weakening momentum",
        "neutral": "Stable LTQ activity",
    },
    "ltq_ratio_5m_20m": {
        "high": "Increasing trading intensity over medium term",
        "low": "Fading volume interest — potential false signal",
        "neutral": "Normal volume profile",
    },
    "etq_acceleration": {
        "high": "Accelerating exchange activity — confirms signal direction",
        "low": "Decelerating exchange activity — signal may lack follow-through",
        "neutral": "Steady exchange traded quantity",
    },
    "bid_ask_imbalance": {
        "high": "Strong buying pressure — bid side dominant",
        "low": "Strong selling pressure — ask side dominant",
        "neutral": "Balanced order book",
    },
    "spread_pct": {
        "high": "Wide spread — low liquidity, higher execution risk",
        "low": "Tight spread — good liquidity, favorable execution",
        "neutral": "Normal spread",
    },
    "smma_gap_pct": {
        "high": "Strong SMMA separation — momentum behind crossover",
        "low": "Weak crossover — SMMA lines barely crossing, prone to whipsaw",
        "neutral": "Moderate crossover strength",
    },
    "price_vs_avg20m": {
        "high": "Price above recent average — bullish momentum",
        "low": "Price below recent average — bearish pressure",
        "neutral": "Price near recent average",
    },
    "volume_surge": {
        "high": "Volume spike — strong conviction behind move",
        "low": "Low volume — weak conviction, signal unreliable",
        "neutral": "Average volume",
    },
    "rsi_14": {
        "high": "RSI overbought (>70) — BUY signal risky, SELL signal stronger",
        "low": "RSI oversold (<30) — SELL signal risky, BUY signal stronger",
        "neutral": "RSI in neutral zone",
    },
    "atr_pct": {
        "high": "High volatility — larger potential moves but more risk",
        "low": "Low volatility — smaller moves, tighter risk",
        "neutral": "Normal volatility",
    },
}


class CrossoverPredictor:
    """
    Predicts whether an SMMA crossover signal should be accepted or avoided.

    Uses a trained XGBoost model with SHAP-based feature explanations.
    """

    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_names = FEATURE_NAMES
        self._loaded = False
        self.load_model()

    def load_model(self) -> bool:
        """Load the trained model and scaler from disk."""
        try:
            if not os.path.exists(config.ML_MODEL_PATH):
                logger.warning(f"Model not found at {config.ML_MODEL_PATH}")
                return False

            with open(config.ML_MODEL_PATH, "rb") as f:
                self.model = pickle.load(f)
            with open(config.ML_SCALER_PATH, "rb") as f:
                self.scaler = pickle.load(f)

            # Load feature names if saved
            feature_path = config.ML_MODEL_PATH.replace("model.pkl", "features.pkl")
            if os.path.exists(feature_path):
                with open(feature_path, "rb") as f:
                    self.feature_names = pickle.load(f)

            self._loaded = True
            logger.info("ML model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def predict(self, features: Dict[str, float],
                signal_type: str = "BUY") -> Tuple[str, float, str]:
        """
        Predict whether a crossover should be accepted or avoided.

        Args:
            features: Dictionary of feature name → value
            signal_type: "BUY" or "SELL"

        Returns:
            Tuple of (prediction, confidence, explanation):
            - prediction: "ACCEPT" or "AVOID"
            - confidence: probability 0.0 to 1.0
            - explanation: human-readable reasoning
        """
        if not self._loaded:
            return self._rule_based_prediction(features, signal_type)

        try:
            # Prepare feature vector with column names
            import pandas as pd
            X_df = pd.DataFrame([[features.get(f, 0.0) for f in self.feature_names]], columns=self.feature_names)
            X_df = X_df.fillna(0.0).replace([np.inf, -np.inf], 0.0)
            X_scaled = self.scaler.transform(X_df)

            # Predict
            prob = float(self.model.predict_proba(X_scaled)[0][1])  # P(profitable)
            prediction = "ACCEPT" if prob >= config.ML_CONFIDENCE_THRESHOLD else "AVOID"

            # Generate explanation using feature importance
            explanation = self._generate_explanation(features, prob, signal_type)

            return prediction, prob, explanation

        except Exception as e:
            logger.warning(f"Prediction failed, using rule-based fallback: {e}")
            return self._rule_based_prediction(features, signal_type)

    def _generate_explanation(self, features: Dict[str, float],
                              probability: float,
                              signal_type: str) -> str:
        """Generate human-readable explanation of the prediction."""
        reasons = []

        # Get feature importances from model
        if hasattr(self.model, 'feature_importances_'):
            importances = dict(zip(self.feature_names, self.model.feature_importances_))
            sorted_features = sorted(importances.items(), key=lambda x: x[1], reverse=True)
        else:
            sorted_features = [(f, 1.0) for f in self.feature_names]

        # Top 3 most important features with their values
        for feat_name, importance in sorted_features[:3]:
            val = features.get(feat_name, 0.0)
            templates = FEATURE_EXPLANATIONS.get(feat_name, {})

            if feat_name == "rsi_14":
                if val > 70:
                    reasons.append(f"RSI={val:.1f}: {templates.get('high', 'Overbought')}")
                elif val < 30:
                    reasons.append(f"RSI={val:.1f}: {templates.get('low', 'Oversold')}")
                else:
                    reasons.append(f"RSI={val:.1f}: {templates.get('neutral', 'Neutral')}")
            elif feat_name in ("ltq_ratio_2m_5m", "ltq_ratio_5m_20m", "etq_acceleration", "volume_surge"):
                if val > 1.5:
                    reasons.append(f"{feat_name}={val:.2f}: {templates.get('high', 'Elevated')}")
                elif val < 0.7:
                    reasons.append(f"{feat_name}={val:.2f}: {templates.get('low', 'Declining')}")
                else:
                    reasons.append(f"{feat_name}={val:.2f}: {templates.get('neutral', 'Normal')}")
            elif feat_name == "bid_ask_imbalance":
                if val > 0.2:
                    reasons.append(f"Bid-Ask Imbalance={val:+.2f}: {templates.get('high', 'Buy pressure')}")
                elif val < -0.2:
                    reasons.append(f"Bid-Ask Imbalance={val:+.2f}: {templates.get('low', 'Sell pressure')}")
                else:
                    reasons.append(f"Bid-Ask Imbalance={val:+.2f}: {templates.get('neutral', 'Balanced')}")
            elif feat_name == "smma_gap_pct":
                if abs(val) > 0.5:
                    reasons.append(f"SMMA Gap={val:+.2f}%: {templates.get('high', 'Strong crossover')}")
                else:
                    reasons.append(f"SMMA Gap={val:+.2f}%: {templates.get('low', 'Weak crossover')}")
            else:
                reasons.append(f"{feat_name}={val:.3f}")

        action = "ACCEPT" if probability >= config.ML_CONFIDENCE_THRESHOLD else "AVOID"
        intro = f"{signal_type} signal → {action} (Confidence: {probability:.0%})"
        return f"{intro}\n" + "\n".join(f"  • {r}" for r in reasons)

    def _rule_based_prediction(self, features: Dict[str, float],
                               signal_type: str) -> Tuple[str, float, str]:
        """
        Fallback rule-based prediction when ML model is not available.
        Uses simple heuristics based on the features.
        """
        score = 0.5  # Start neutral
        reasons = []

        # LTQ surge — most important per assignment
        ltq_ratio = features.get("ltq_ratio_2m_5m", 1.0)
        if ltq_ratio > 1.5:
            score += 0.1
            reasons.append(f"LTQ surge (2m/5m={ltq_ratio:.2f}x) — strong institutional activity")
        elif ltq_ratio < 0.7:
            score -= 0.1
            reasons.append(f"LTQ declining (2m/5m={ltq_ratio:.2f}x) — weakening momentum")

        # Volume confirmation
        vol_surge = features.get("volume_surge", 1.0)
        if vol_surge > 2.0:
            score += 0.1
            reasons.append(f"Volume spike ({vol_surge:.1f}x avg) — strong conviction")
        elif vol_surge < 0.5:
            score -= 0.1
            reasons.append(f"Low volume ({vol_surge:.1f}x avg) — weak conviction")

        # Bid-ask alignment with signal
        imbalance = features.get("bid_ask_imbalance", 0.0)
        if signal_type == "BUY" and imbalance > 0.2:
            score += 0.05
            reasons.append(f"Order book supports BUY (imbalance={imbalance:+.2f})")
        elif signal_type == "SELL" and imbalance < -0.2:
            score += 0.05
            reasons.append(f"Order book supports SELL (imbalance={imbalance:+.2f})")
        elif (signal_type == "BUY" and imbalance < -0.3) or \
             (signal_type == "SELL" and imbalance > 0.3):
            score -= 0.1
            reasons.append(f"Order book contradicts signal (imbalance={imbalance:+.2f})")

        # RSI confirmation
        rsi = features.get("rsi_14", 50.0)
        if signal_type == "BUY" and rsi > 75:
            score -= 0.1
            reasons.append(f"RSI overbought ({rsi:.0f}) — BUY risky")
        elif signal_type == "SELL" and rsi < 25:
            score -= 0.1
            reasons.append(f"RSI oversold ({rsi:.0f}) — SELL risky")

        # SMMA gap strength
        gap = abs(features.get("smma_gap_pct", 0.0))
        if gap < 0.1:
            score -= 0.05
            reasons.append(f"Weak crossover (SMMA gap={gap:.2f}%) — whipsaw risk")

        score = max(0.0, min(1.0, score))
        prediction = "ACCEPT" if score >= config.ML_CONFIDENCE_THRESHOLD else "AVOID"

        explanation = f"{signal_type} signal → {prediction} (Rule-based confidence: {score:.0%})\n"
        explanation += "\n".join(f"  • {r}" for r in reasons)

        return prediction, score, explanation

    def get_feature_importance(self) -> Dict[str, float]:
        """Return feature importance from the loaded model."""
        if not self._loaded or not hasattr(self.model, 'feature_importances_'):
            return {}
        return dict(zip(self.feature_names, self.model.feature_importances_))
