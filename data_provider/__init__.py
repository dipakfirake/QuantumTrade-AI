"""
Data Provider Package Helpers

Provides a small factory to select the appropriate data provider at runtime
based on `config.ETQ_MODE` and available broker SDKs / environment variables.
"""
from typing import Optional

import config


def get_data_provider(prefer_broker: Optional[str] = None):
	"""Return a `DataProvider` instance.

	- If `config.ETQ_MODE == 'broker'` or `config.USE_BROKER_ETQ` is True,
	  attempt to instantiate a broker provider (`fyers` then `angel`) and
	  fall back to `NSEProvider` if none are available.
	- `prefer_broker` can be 'fyers', 'angel', or None for automatic.
	"""
	# Local import to avoid import-time SDK errors
	from data_provider.nse_provider import NSEProvider

	broker_mode = getattr(config, "ETQ_MODE", "proxy") == "broker" or getattr(config, "USE_BROKER_ETQ", False)

	if not broker_mode:
		return NSEProvider()

	# Broker mode requested: try preferred broker first
	prefer = (prefer_broker or "auto").lower()
	tried = []
	if prefer in ("fyers", "auto"):
		tried.append("fyers")
		try:
			from data_provider.fyers_provider import FyersProvider

			prov = FyersProvider()
			return prov
		except Exception:
			pass

	if prefer in ("angel", "auto"):
		tried.append("angel")
		try:
			from data_provider.angel_provider import AngelProvider

			prov = AngelProvider()
			return prov
		except Exception:
			pass

	# Nothing available — fall back to NSEProvider (proxy mode behavior)
	return NSEProvider()

