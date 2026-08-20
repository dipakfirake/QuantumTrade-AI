"""
Scheduled Retrain Helper

This script is intended to be run by a scheduler (Windows Task Scheduler or cron)
shortly after market close to regenerate training data and retrain the ML model.

Usage (manual):
    python scripts/schedule_retrain.py --symbols 80

Example Windows Task Scheduler (runs daily at 16:30 IST):
- Create Task -> Trigger: Daily 16:30 -> Action: Program: python, Arguments: "scripts/schedule_retrain.py --symbols 100"

The script will:
- Optionally refresh the historical cache
- Generate training data and retrain the model
- Save artifacts to `ml_model/model.pkl` and `data/historical_crossovers.csv`
"""
import argparse
import logging
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ml_model.trainer import generate_training_data, train_model, TRAINING_SYMBOLS
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Scheduled retrain for ML model")
    parser.add_argument("--symbols", type=int, default=50, help="Number of symbols to train on")
    parser.add_argument("--force-cache-refresh", action="store_true", help="Force refresh of history cache")
    args = parser.parse_args()

    n = min(args.symbols, len(TRAINING_SYMBOLS))
    symbols = TRAINING_SYMBOLS[:n]

    # If requested, clear history cache files for the selected symbols
    if args.force_cache_refresh:
        try:
            from data_provider.history_cache import _cache_path, _meta_path
            removed = 0
            for s in symbols:
                p = _cache_path(s, config.HISTORICAL_INTERVAL, config.HISTORICAL_PERIOD)
                m = _meta_path(s, config.HISTORICAL_INTERVAL, config.HISTORICAL_PERIOD)
                for f in (p, m):
                    if os.path.exists(f):
                        os.remove(f)
                        removed += 1
            logger.info(f"Removed {removed} cached artifacts")
        except Exception as e:
            logger.warning(f"Cache refresh failed: {e}")

    logger.info(f"Generating training data for {len(symbols)} symbols...")
    df = generate_training_data(symbols)
    if df is None or len(df) < 10:
        logger.error("Insufficient training samples generated; aborting retrain.")
        return

    logger.info("Training model...")
    results = train_model(df)
    logger.info(f"Retrain complete. Accuracy: {results['accuracy']:.2%}")


if __name__ == "__main__":
    main()
