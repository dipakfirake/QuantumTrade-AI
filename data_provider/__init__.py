"""
Data Provider Package Helpers

Provides a factory to select the appropriate data provider at runtime
based on `config.ETQ_MODE` and available broker credentials.
"""
from typing import Optional
import logging
import config

logger = logging.getLogger(__name__)

def get_data_provider(prefer_broker: Optional[str] = None):
    """
    Return a `DataProvider` instance.
    - If `config.ETQ_MODE in ('broker', 'fyers', 'angel')` or `config.USE_BROKER_ETQ` is True,
      attempts to instantiate the authenticated broker provider.
    - Falls back to `NSEProvider` if credentials are not present.
    """
    from data_provider.nse_provider import NSEProvider

    broker_mode = getattr(config, "ETQ_MODE", "proxy") in ("broker", "fyers", "angel") or getattr(config, "USE_BROKER_ETQ", False)

    if broker_mode:
        prefer = (prefer_broker or getattr(config, "ETQ_MODE", "auto")).lower()
        
        if prefer in ("fyers", "broker", "auto"):
            try:
                from data_provider.fyers_provider import FyersProvider
                prov = FyersProvider()
                if prov.is_authenticated():
                    logger.info("Using authenticated Fyers API v3 Data Provider")
                    return prov
            except Exception as e:
                logger.warning(f"Could not initialize FyersProvider: {e}")

        if prefer in ("angel", "broker", "auto"):
            try:
                from data_provider.angel_provider import AngelProvider
                prov = AngelProvider()
                logger.info("Using Angel One Data Provider")
                return prov
            except Exception as e:
                logger.warning(f"Could not initialize AngelProvider: {e}")

    # Default to NSEProvider with fast parallel downloads
    return NSEProvider()
