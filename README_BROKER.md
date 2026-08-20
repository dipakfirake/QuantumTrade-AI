Broker Integration (Fyers / Angel One)

This project supports using broker APIs to obtain true tick-level ETQ (last traded quantity) and 5-level market depth. When broker integration is not configured, the app uses a "proxy" mode that derives ETQ from Yahoo Finance minute bars.

Environment variables (recommended via .env)
- FYERS_API_KEY
- FYERS_ACCESS_TOKEN
- ANGEL_API_KEY
- ANGEL_ACCESS_TOKEN

How to enable broker mode
1. Install the broker SDK(s) you plan to use, for example:
   - Fyers SDK (if available): `pip install fyers-apiv2` (check official package name)
   - Angel SmartAPI: `pip install smartapi-python`

2. Create a `.env` file in the project root (do not commit it):

```
FYERS_API_KEY=your_fyers_api_key
FYERS_ACCESS_TOKEN=your_fyers_access_token
ANGEL_API_KEY=your_angel_api_key
ANGEL_ACCESS_TOKEN=your_angel_access_token
```

3. Set config flags in `config.py` (or use environment-driven config):

```python
ETQ_MODE = "broker"
USE_BROKER_ETQ = True
```

4. Restart the Streamlit app. The provider factory will attempt to instantiate a broker provider and fall back to the NSE provider if SDKs/keys are missing.

Scheduling retrains and caching
- Use the built-in history cache to reduce repeated Yahoo downloads during training: `data_provider/history_cache.py`.
- To run a scheduled retrain after market close, add a Task Scheduler job or cron entry to run:

```
python scripts/schedule_retrain.py --symbols 80
```

Add `--force-cache-refresh` to the command to force redownloading historical OHLCV for the selected symbols.

Security
- Never paste API keys in chat or commit them to Git.
- Use environment variables or a local `.env` file and add `.env` to `.gitignore`.

If you want, I can finish wiring the exact SDK method calls for Fyers or Angel once you confirm which broker you'll provide and I will not ask for keys in chat. I'll provide exact commands to run locally to validate live connectivity.
