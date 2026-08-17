# =============================================================================
# Standalone ML Model Training Script
# =============================================================================
"""
Train the XGBoost model on historical SMMA crossover data.

Usage:
    python scripts/train_model.py [--symbols N] [--verbose]

Options:
    --symbols N     Number of symbols to use for training (default: 50)
    --verbose       Enable verbose logging

This will:
1. Download 6 months of hourly OHLCV data for N liquid NSE stocks
2. Calculate SMMA(20) and SMMA(120) for each
3. Detect all historical crossovers
4. Label them as profitable (1) or unprofitable (0)
5. Extract 14 quantitative features at each crossover
6. Train an XGBoost classifier
7. Save the model to ml_model/model.pkl
"""
import os
import sys
import argparse
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_model.trainer import generate_training_data, train_model, TRAINING_SYMBOLS


def main():
    parser = argparse.ArgumentParser(description="Train the SMMA crossover ML model")
    parser.add_argument("--symbols", type=int, default=50,
                        help="Number of symbols to train on (default: 50)")
    parser.add_argument("--verbose", action="store_true",
                        help="Enable verbose logging")
    args = parser.parse_args()

    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger(__name__)

    n_symbols = min(args.symbols, len(TRAINING_SYMBOLS))
    symbols = TRAINING_SYMBOLS[:n_symbols]

    logger.info(f"Training with {n_symbols} symbols")
    logger.info("=" * 60)

    # Step 1: Generate training data
    logger.info("Step 1: Generating training data from historical crossovers...")
    df_training = generate_training_data(symbols)

    if df_training is None or len(df_training) < 10:
        logger.error("Insufficient training data generated. Need at least 10 crossovers.")
        sys.exit(1)

    logger.info(f"Generated {len(df_training)} labeled crossover samples")

    # Step 2: Train the model
    logger.info("Step 2: Training XGBoost classifier...")
    results = train_model(df_training)

    # Step 3: Report results
    logger.info("=" * 60)
    logger.info("✅ Training Complete!")
    logger.info(f"   Test Accuracy: {results['accuracy']:.1%}")
    logger.info(f"   Train Samples: {results['train_size']}")
    logger.info(f"   Test Samples:  {results['test_size']}")
    logger.info(f"   Model saved:   {results['model_path']}")
    logger.info("")
    logger.info("Top 5 Features:")
    for feat, imp in list(results['feature_importance'].items())[:5]:
        logger.info(f"   {feat}: {imp:.4f}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
