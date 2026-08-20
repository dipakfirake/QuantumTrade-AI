"""
Check Broker Provider Connectivity (dry-run)

This script attempts to instantiate the Fyers and Angel providers and
invoke `get_quote` and `get_market_depth` for a sample symbol. It is
safe to run without credentials — the providers will raise descriptive
errors when SDKs or keys are missing.

Usage:
    python scripts/check_providers.py

"""
import os
import sys
from pprint import pprint

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from data_provider.fyers_provider import FyersProvider
from data_provider.angel_provider import AngelProvider

SAMPLE = os.environ.get("CHECK_SYMBOL", "RELIANCE")


def safe_check(provider_cls, name):
    print(f"\n--- Checking {name} provider ---")
    try:
        prov = provider_cls()
    except Exception as e:
        print("Instantiation failed:", e)
        return

    # Try get_quote
    try:
        q = prov.get_quote(SAMPLE)
        print("get_quote result:")
        pprint(q)
    except NotImplementedError as nie:
        print("get_quote not implemented / SDK missing:", nie)
    except Exception as e:
        print("get_quote raised:", e)

    # Try market depth
    try:
        md = prov.get_market_depth(SAMPLE)
        print("get_market_depth result:")
        pprint(md)
    except NotImplementedError as nie:
        print("get_market_depth not implemented / SDK missing:", nie)
    except Exception as e:
        print("get_market_depth raised:", e)


if __name__ == "__main__":
    safe_check(FyersProvider, "Fyers")
    safe_check(AngelProvider, "Angel One")
    print("\nDone. If you plan to test live, set environment variables as described in README_BROKER.md and restart the app.")
